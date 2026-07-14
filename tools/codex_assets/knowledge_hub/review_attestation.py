"""Human review attestation packets and mechanically generated local forms."""

from __future__ import annotations

import datetime as dt
import pathlib
from typing import Any, Dict, Mapping, Sequence

from .common import (
    KnowledgeHubError,
    bytes_sha256,
    encode_jsonl,
    file_sha256,
    normalize_relpath,
    registry_items,
    resolve_inside,
)
from .model import assert_transition
from .store import RepositoryTransaction


FORM_KIND = "content-review-attestation"
ATTESTATION_MODES = ("human-reviewed", "human-directed-delegation")
TARGET_DECISIONS = {
    "active": "accept-active",
    "archived": "retire",
    "superseded": "supersede",
    "rejected": "reject",
}
MACHINE_IDENTITIES = {"ai", "automation", "codex", "script", "system", "unassigned", "unknown"}


def _item_context(root: pathlib.Path, item_id: str, target_status: str) -> Dict[str, str]:
    matches = [row for row in registry_items(root) if str(row.get("id", "")) == item_id]
    if len(matches) != 1:
        raise KnowledgeHubError("item id must resolve to exactly one registry row: {}".format(item_id))
    item = matches[0]
    before_status = str(item.get("status", ""))
    assert_transition(before_status, target_status)
    item_path = resolve_inside(root, str(item.get("path", "")))
    if not item_path.is_file():
        raise KnowledgeHubError("item body is missing: {}".format(item.get("path", "")))
    return {
        "item_id": item_id,
        "item_path": str(item["path"]),
        "before_status": before_status,
        "target_status": target_status,
        "content_sha256": file_sha256(item_path),
        "review_decision": TARGET_DECISIONS[target_status],
    }


def confirmation_token(context: Mapping[str, str]) -> str:
    payload = "|".join(
        str(context[field])
        for field in ("item_id", "item_path", "before_status", "target_status", "content_sha256")
    )
    return "KH-ATTEST-{}".format(bytes_sha256(payload.encode("utf-8"))[:20])


def suggested_output_path(context: Mapping[str, str], as_of: dt.date) -> str:
    return "artifacts/manifests/{}-{}-review-{}.local.jsonl".format(
        context["item_id"], context["target_status"], as_of.strftime("%Y%m%d")
    )


def _response_template(context: Mapping[str, str], token: str, delegated: bool) -> str:
    if delegated:
        return (
            "我已看到条目 {item_id} 当前正文身份（SHA256 {content_sha256}）及从 "
            "{before_status} 变更为 {target_status} 的影响，明确作出该生命周期决定；"
            "委托 Codex 仅机械生成表单，reviewed_by=<reviewer>-via-codex-delegation；"
            "这不代表直接内容复核，也不授权 active promotion。确认码 {token}"
        ).format(token=token, **context)
    return (
        "我已复核条目 {item_id} 的当前正文（SHA256 {content_sha256}），确认其生命周期从 "
        "{before_status} 变更为 {target_status}；reviewed_by=<reviewer>；"
        "允许 Codex 仅机械生成 content-review attestation 表单。确认码 {token}"
    ).format(token=token, **context)


def build_attestation_packet(
    root: pathlib.Path,
    item_id: str,
    target_status: str,
    as_of: dt.date,
) -> Dict[str, Any]:
    context = _item_context(root, item_id, target_status)
    token = confirmation_token(context)
    output = suggested_output_path(context, as_of)
    modes = ["human-reviewed"]
    response_templates = {"human-reviewed": _response_template(context, token, False)}
    if target_status != "active":
        modes.append("human-directed-delegation")
        response_templates["human-directed-delegation"] = _response_template(context, token, True)
    transition_tool = "knowledge-promote.sh" if target_status == "active" else "knowledge-retire.sh"
    return {
        "schema_version": 1,
        "action": "review-attestation-packet",
        "status": "awaiting-human-decision",
        "read_only": True,
        "item": context,
        "execution_authorization": {
            "required_for_transition": True,
            "required_for_form_generation": False,
            "separate_gate": True,
            "statement": "Execution authorization permits the write; it does not assert content review.",
        },
        "content_review_attestation": {
            "human_decision_required": True,
            "manual_json_editing_required": False,
            "confirmation_token": token,
            "allowed_modes": modes,
            "response_templates": response_templates,
            "required_statement_bindings": [
                "item_id",
                "before_status",
                "target_status",
                "full content_sha256",
                "confirmation_token",
            ],
        },
        "mechanical_generation": {
            "output": output,
            "command_template": (
                "rtk bash ~/knowledge-hub/tools/knowledge-review-attest.sh generate "
                "--id {item_id} --target {target_status} --expected-sha256 {content_sha256} "
                "--attestation-mode <mode> --attested-by <reviewer> "
                "--attestation-source-ref <human-decision-source> "
                "--attestation-text '<exact-human-response>' --confirm-attestation "
                "--output {output} --apply --json"
            ).format(output=output, **context),
        },
        "transition": {
            "command_template": (
                "rtk bash ~/knowledge-hub/tools/{tool} --id {item_id} --target {target_status} "
                "--authorization-id <execution-authorization-id> --forms {output} "
                "--expected-sha256 {content_sha256} --apply --json"
            ).format(tool=transition_tool, output=output, **context),
        },
        "boundaries": [
            "packet generation is read-only",
            "form generation does not create execution authorization",
            "Codex must not invent the attestation text or reviewer identity",
            "human-directed-delegation is forbidden for active promotion",
            "no memory write, source-project write, or remote publish",
        ],
    }


def _validate_identity(attested_by: str) -> str:
    identity = attested_by.strip()
    if not identity:
        raise KnowledgeHubError("--attested-by is required")
    if identity.lower() in MACHINE_IDENTITIES or identity.startswith("<") or identity.endswith(">"):
        raise KnowledgeHubError("attested_by must identify the human who made the decision")
    if identity.endswith("-via-codex-delegation"):
        raise KnowledgeHubError("attested_by must be the human identity without delegation suffix")
    if len(identity) > 128 or any(character in identity for character in "\r\n\t"):
        raise KnowledgeHubError("attested_by contains unsupported control characters or is too long")
    return identity


def _validate_statement(
    statement: str,
    context: Mapping[str, str],
    token: str,
    reviewer: str,
    attestation_mode: str,
) -> str:
    value = statement.strip()
    if not value:
        raise KnowledgeHubError("--attestation-text is required")
    if len(value) > 4096:
        raise KnowledgeHubError("attestation text exceeds 4096 characters")
    required_fragments = [
        context["item_id"],
        context["before_status"],
        context["target_status"],
        context["content_sha256"],
        token,
        "reviewed_by={}".format(
            reviewer
            if attestation_mode == "human-reviewed"
            else "{}-via-codex-delegation".format(reviewer)
        ),
    ]
    missing = [fragment for fragment in required_fragments if fragment not in value]
    if missing:
        raise KnowledgeHubError(
            "attestation text is not bound to the exact review packet; missing: {}".format(", ".join(missing))
        )
    return value


def _output_relative(output: str) -> str:
    if pathlib.Path(output).is_absolute():
        raise KnowledgeHubError("review attestation output must be a repository-relative path")
    relative = normalize_relpath(output)
    if not relative.startswith("artifacts/manifests/") or not relative.endswith(".local.jsonl"):
        raise KnowledgeHubError("review attestation output must match artifacts/manifests/*.local.jsonl")
    return relative


def attestation_review_basis(attestation_mode: str, token: str, source_ref: str) -> str:
    if attestation_mode == "human-reviewed":
        return "explicit human content review; token={}; source={}".format(token, source_ref)
    return (
        "explicit human lifecycle decision delegated to Codex; direct content review not asserted; "
        "token={}; source={}".format(token, source_ref)
    )


def generate_review_form(
    root: pathlib.Path,
    item_id: str,
    target_status: str,
    as_of: dt.date,
    expected_item_sha256: str,
    attestation_mode: str,
    attested_by: str,
    attestation_source_ref: str,
    attestation_text: str,
    output: str,
    apply: bool,
    confirm_attestation: bool,
    attested_at: str = "",
    validation_refs: Sequence[str] = (),
) -> Dict[str, Any]:
    if not confirm_attestation:
        raise KnowledgeHubError("--confirm-attestation is required after an explicit human decision")
    context = _item_context(root, item_id, target_status)
    if not expected_item_sha256:
        raise KnowledgeHubError("--expected-sha256 is required")
    if expected_item_sha256 != context["content_sha256"]:
        raise KnowledgeHubError("expected item SHA256 does not match current body")
    if attestation_mode not in ATTESTATION_MODES:
        raise KnowledgeHubError("unsupported attestation mode: {}".format(attestation_mode))
    if target_status == "active" and attestation_mode != "human-reviewed":
        raise KnowledgeHubError("active promotion requires direct human-reviewed attestation")
    reviewer = _validate_identity(attested_by)
    source_ref = attestation_source_ref.strip()
    if not source_ref:
        raise KnowledgeHubError("--attestation-source-ref is required")
    if len(source_ref) > 500 or any(character in source_ref for character in "\r\n\t"):
        raise KnowledgeHubError("attestation source ref contains unsupported control characters or is too long")
    token = confirmation_token(context)
    statement = _validate_statement(attestation_text, context, token, reviewer, attestation_mode)
    review_date = attested_at or as_of.isoformat()
    try:
        parsed_review_date = dt.date.fromisoformat(review_date)
    except ValueError as exc:
        raise KnowledgeHubError("--attested-at must use YYYY-MM-DD") from exc
    if parsed_review_date > as_of:
        raise KnowledgeHubError("--attested-at cannot be later than --as-of")
    reviewed_by = (
        reviewer
        if attestation_mode == "human-reviewed"
        else "{}-via-codex-delegation".format(reviewer)
    )
    refs = []
    for ref in (
        context["item_path"],
        source_ref,
        "rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics",
        *validation_refs,
    ):
        value = str(ref).strip()
        if value and value not in refs:
            refs.append(value)
    review_basis = attestation_review_basis(attestation_mode, token, source_ref)
    form = {
        "schema_version": 1,
        "form_kind": FORM_KIND,
        "attestation_id": "attestation-{}-{}-{}".format(item_id, target_status, token.rsplit("-", 1)[-1]),
        "item_id": item_id,
        "reviewed_by": reviewed_by,
        "reviewed_at": review_date,
        "review_decision": context["review_decision"],
        "review_basis": review_basis,
        "validation_refs": refs,
        "attestation_mode": attestation_mode,
        "attested_by": reviewer,
        "attested_at": review_date,
        "attestation_source_ref": source_ref,
        "attestation_statement": statement,
        "attestation_statement_sha256": bytes_sha256(statement.encode("utf-8")),
        "confirmation_token": token,
        "content_sha256": context["content_sha256"],
        "expected_before_status": context["before_status"],
        "target_status": context["target_status"],
        "generated_mechanically": True,
        "generated_by": "knowledge-review-attest",
        "execution_authorization_embedded": False,
        "boundaries": [
            "content review attestation only",
            "does not authorize lifecycle execution",
            "does not authorize active promotion unless mode is human-reviewed",
            "no memory write, source-project write, or remote publish",
        ],
    }
    relative = _output_relative(output)
    target = resolve_inside(root, relative)
    encoded = encode_jsonl([form])
    if target.exists() and target.read_text(encoding="utf-8") != encoded:
        raise KnowledgeHubError("review attestation output already exists with different content: {}".format(relative))
    transaction = RepositoryTransaction(root)
    transaction.add_text(relative, encoded, expected_sha256=file_sha256(target) if target.exists() else "")
    result: Dict[str, Any] = {
        "schema_version": 1,
        "action": "generate-review-attestation",
        "status": "planned",
        "read_only": not apply,
        "output": relative,
        "item": context,
        "attestation": {
            "attestation_id": form["attestation_id"],
            "attestation_mode": attestation_mode,
            "attested_by": reviewer,
            "reviewed_by": reviewed_by,
            "content_sha256": context["content_sha256"],
            "execution_authorization_embedded": False,
        },
        "transaction": transaction.plan(),
        "next_command": (
            "rtk bash ~/knowledge-hub/tools/{} --id {} --target {} "
            "--authorization-id <execution-authorization-id> --forms {} "
            "--expected-sha256 {} --apply --json"
        ).format(
            "knowledge-promote.sh" if target_status == "active" else "knowledge-retire.sh",
            item_id,
            target_status,
            relative,
            context["content_sha256"],
        ),
    }
    if apply:
        result["transaction"] = transaction.apply().to_dict()
        result["status"] = "applied" if result["transaction"]["status"] == "applied" else "no-change"
        result["read_only"] = False
    return result
