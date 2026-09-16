"""Read-only Operator projection for observed governed binding lifecycle artifacts."""

from __future__ import annotations

import hashlib
import json
import pathlib
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from .common import KnowledgeHubError
from .operator_binding_apply_receipt import build_governed_apply_receipt
from .operator_binding_rollback_receipt import build_governed_rollback_receipt

LIFECYCLE_PROJECTION = "knowledge-operator-binding-lifecycle-v1"
PROPOSAL_PROJECTION = "knowledge-operator-binding-proposal-v1"
PATCH_PLAN_PROJECTION = "knowledge-operator-binding-patch-plan-v1"
REVIEW_PROJECTION = "knowledge-operator-binding-review-bundle-v1"
AUTHORIZATION_PROJECTION = "knowledge-operator-binding-authorization-v1"
APPLY_PROJECTION = "knowledge-operator-binding-governed-apply-v1"
ROLLBACK_PROJECTION = "knowledge-operator-binding-governed-rollback-v1"

_INPUT_ORDER = (
    "proposal",
    "patch_plan",
    "review_bundle",
    "authorization",
    "apply",
    "rollback",
)
_EXPECTED_PROJECTIONS = {
    "proposal": PROPOSAL_PROJECTION,
    "patch_plan": PATCH_PLAN_PROJECTION,
    "review_bundle": REVIEW_PROJECTION,
    "authorization": AUTHORIZATION_PROJECTION,
    "apply": APPLY_PROJECTION,
    "rollback": ROLLBACK_PROJECTION,
}
_READ_ONLY_STAGES = {"proposal", "patch_plan", "review_bundle", "authorization"}


def _fingerprint(value: Any) -> str:
    raw = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return "sha256:{}".format(hashlib.sha256(raw).hexdigest())


def _load_json_object(root: pathlib.Path, value: str, label: str) -> Mapping[str, Any]:
    path = pathlib.Path(value).expanduser()
    if not path.is_absolute():
        path = root / path
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise KnowledgeHubError(
            "cannot load {} lifecycle JSON {}: {}".format(label, path, exc)
        ) from exc
    if not isinstance(payload, dict):
        raise KnowledgeHubError("{} lifecycle JSON must be an object".format(label))
    return payload


def _observed_contract_reasons(stage: str, payload: Mapping[str, Any]) -> List[str]:
    reasons: List[str] = []
    if payload.get("schema_version") != 1:
        reasons.append("{}-schema-version-invalid".format(stage))
    if str(payload.get("projection", "")) != _EXPECTED_PROJECTIONS[stage]:
        reasons.append("{}-projection-invalid".format(stage))
    if payload.get("automatic_execution_enabled") is not False:
        reasons.append("{}-automatic-execution-boundary-invalid".format(stage))
    if stage in _READ_ONLY_STAGES:
        if payload.get("read_only") is not True:
            reasons.append("{}-read-only-boundary-invalid".format(stage))
        if payload.get("canonical_write_performed") is not False:
            reasons.append("{}-canonical-write-boundary-invalid".format(stage))
        if payload.get("automatic_binding_enabled") is not False:
            reasons.append("{}-automatic-binding-boundary-invalid".format(stage))
    return reasons


def _stage_row(
    stage: str,
    payload: Mapping[str, Any],
    *,
    trust_state: str,
    status_override: str = "",
    reason_codes: Optional[Sequence[str]] = None,
) -> Dict[str, Any]:
    source_reasons = payload.get("reason_codes", [])
    if not isinstance(source_reasons, list):
        source_reasons = []
    reasons = list(reason_codes) if reason_codes is not None else source_reasons[:10]
    return {
        "stage": stage,
        "observed": True,
        "projection": str(payload.get("projection", "")),
        "source_status": str(payload.get("status", "")),
        "status": status_override or str(payload.get("status", "")),
        "trust_state": trust_state,
        "reason_codes": [str(value) for value in reasons if str(value)][:10],
    }


def _next_responsibility(stage: str, status: str) -> Tuple[str, str]:
    if stage == "proposal":
        if status == "needs-governed-review":
            return (
                "governance-review",
                "审核 proposal 与 canonical target，并显式选择 proposal fingerprint；选择不是授权。",
            )
        if status in {"blocked", "upstream-error"}:
            return "governance-review", "审计 proposal 上游 contract/冲突后再继续。"
    if stage == "patch_plan":
        if status == "needs-governed-pr":
            return (
                "machine-after-prerequisite",
                "基于 exact patch plan 生成确定性 review bundle；不得把 plan 或 selection 当成授权。",
            )
        if status in {"blocked", "upstream-error"}:
            return "governance-review", "审计 patch plan 与 proposal/registry precondition 后再继续。"
    if stage == "review_bundle":
        if status == "needs-governed-authorization":
            return "human-authorization", "由真实 owner 提供显式 binding authorization；UI 不生成授权。"
        if status in {"blocked", "upstream-error"}:
            return "governance-review", "审计 review bundle/patch plan 一致性后再继续。"
    if stage == "authorization":
        if status == "ready-for-governed-apply":
            return (
                "human-authorization",
                "通过独立 apply CLI 重新验证完整链并显式确认 fingerprint、registry SHA 与身份边界。",
            )
        if status in {"blocked", "upstream-error"}:
            return "governance-review", "审计 authorization contract/owner coverage 后再继续。"
    if stage == "apply":
        if status in {"post-apply-state-drift", "blocked"}:
            return "governance-review", "审计 apply receipt 或当前 registry drift；不得覆盖现状。"
    if stage == "rollback":
        if status == "ready-for-governed-rollback":
            return (
                "human-authorization",
                "通过独立 rollback CLI 显式确认 receipt、authorization fingerprint、当前 SHA 与身份边界。",
            )
        if status in {"post-rollback-state-drift", "blocked"}:
            return "governance-review", "审计 rollback receipt 或当前 registry drift；不得自动 reapply。"
    return "", ""


def _observation_error(
    stages: Sequence[Mapping[str, Any]],
    reasons: Sequence[str],
) -> Dict[str, Any]:
    return {
        "schema_version": 1,
        "projection": LIFECYCLE_PROJECTION,
        "status": "observation-error",
        "read_only": True,
        "network_performed": False,
        "canonical_write_performed": False,
        "automatic_binding_enabled": False,
        "automatic_execution_enabled": False,
        "observed_stage_count": len(stages),
        "current_stage": str(stages[-1].get("stage", "")) if stages else "",
        "trust_state": "fail-closed-observation",
        "next_execution_class": "governance-review",
        "next_summary_zh": "生命周期观测输入无法安全解释；先审计保存的 JSON/链路，不执行 apply 或 rollback。",
        "stages": [dict(row) for row in stages],
        "reason_codes": list(dict.fromkeys(str(value) for value in reasons if str(value)))[:20],
    }


def _not_observed() -> Dict[str, Any]:
    return {
        "schema_version": 1,
        "projection": LIFECYCLE_PROJECTION,
        "status": "not-observed",
        "read_only": True,
        "network_performed": False,
        "canonical_write_performed": False,
        "automatic_binding_enabled": False,
        "automatic_execution_enabled": False,
        "observed_stage_count": 0,
        "current_stage": "",
        "trust_state": "not-observed",
        "next_execution_class": "",
        "next_summary_zh": "",
        "stages": [],
        "reason_codes": ["no-explicit-lifecycle-observation-input"],
    }


def _load_inputs(
    root: pathlib.Path,
    inputs: Mapping[str, str],
) -> Tuple[Dict[str, Mapping[str, Any]], List[Dict[str, Any]], List[str]]:
    payloads: Dict[str, Mapping[str, Any]] = {}
    stages: List[Dict[str, Any]] = []
    reasons: List[str] = []
    for stage in _INPUT_ORDER:
        value = str(inputs.get(stage, "")).strip()
        if not value:
            continue
        try:
            payload = _load_json_object(root, value, stage)
        except KnowledgeHubError as exc:
            reasons.append("{}-input-unavailable:{}".format(stage, exc))
            continue
        payloads[stage] = payload
        contract_reasons = _observed_contract_reasons(stage, payload)
        stages.append(
            _stage_row(
                stage,
                payload,
                trust_state=(
                    "observed-output-not-revalidated"
                    if not contract_reasons
                    else "contract-invalid"
                ),
                reason_codes=contract_reasons or None,
            )
        )
        reasons.extend(contract_reasons)
    return payloads, stages, reasons


def _proposal_fingerprints(payload: Mapping[str, Any]) -> set:
    rows = payload.get("rows", [])
    if not isinstance(rows, list):
        return set()
    return {
        str(row.get("proposal_fingerprint", ""))
        for row in rows
        if isinstance(row, Mapping) and str(row.get("proposal_fingerprint", ""))
    }


def _chain_reasons(payloads: Mapping[str, Mapping[str, Any]]) -> List[str]:
    reasons: List[str] = []
    proposal = payloads.get("proposal")
    patch_plan = payloads.get("patch_plan")
    review = payloads.get("review_bundle")
    authorization = payloads.get("authorization")
    apply_payload = payloads.get("apply")
    rollback = payloads.get("rollback")

    if proposal is not None and patch_plan is not None:
        selected = [str(value) for value in patch_plan.get("selected_proposal_fingerprints", [])]
        if not selected or any(value not in _proposal_fingerprints(proposal) for value in selected):
            reasons.append("proposal-patch-plan-selection-chain-mismatch")
    if patch_plan is not None and review is not None:
        if review.get("selected_proposal_fingerprints") != patch_plan.get(
            "selected_proposal_fingerprints"
        ):
            reasons.append("patch-plan-review-selection-chain-mismatch")
        if str(review.get("patch_plan_fingerprint", "")) != _fingerprint(patch_plan):
            reasons.append("patch-plan-review-fingerprint-chain-mismatch")
        for key in ("registry_before_sha256", "registry_after_sha256"):
            if str(review.get(key, "")) != str(patch_plan.get(key, "")):
                reasons.append("patch-plan-review-{}-chain-mismatch".format(key.replace("_", "-")))
    if review is not None and authorization is not None:
        checks = (
            "review_bundle_fingerprint",
            "patch_plan_fingerprint",
            "registry_before_sha256",
            "registry_after_sha256",
        )
        for key in checks:
            if str(authorization.get(key, "")) != str(review.get(key, "")):
                reasons.append("review-authorization-{}-chain-mismatch".format(key.replace("_", "-")))
    if authorization is not None and apply_payload is not None:
        checks = (
            "authorization_fingerprint",
            "review_bundle_fingerprint",
            "patch_plan_fingerprint",
            "registry_before_sha256",
            "registry_after_sha256",
        )
        for key in checks:
            if str(apply_payload.get(key, "")) != str(authorization.get(key, "")):
                reasons.append("authorization-apply-{}-chain-mismatch".format(key.replace("_", "-")))
    if apply_payload is not None and rollback is not None:
        if str(rollback.get("apply_authorization_fingerprint", "")) and str(
            rollback.get("apply_authorization_fingerprint", "")
        ) != str(apply_payload.get("authorization_fingerprint", "")):
            reasons.append("apply-rollback-authorization-chain-mismatch")
        transaction = apply_payload.get("transaction", {})
        apply_transaction_id = (
            str(transaction.get("transaction_id", ""))
            if isinstance(transaction, Mapping)
            else ""
        )
        if str(rollback.get("apply_transaction_id", "")) and str(
            rollback.get("apply_transaction_id", "")
        ) != apply_transaction_id:
            reasons.append("apply-rollback-transaction-chain-mismatch")
    return list(dict.fromkeys(reasons))


def _insert_after(
    stages: List[Dict[str, Any]],
    after_stage: str,
    row: Dict[str, Any],
) -> None:
    index = max(
        (position for position, value in enumerate(stages) if value.get("stage") == after_stage),
        default=len(stages) - 1,
    )
    stages.insert(index + 1, row)


def _revalidate_latest(
    root: pathlib.Path,
    payloads: Mapping[str, Mapping[str, Any]],
    stages: List[Dict[str, Any]],
) -> Tuple[str, str, List[str]]:
    apply_receipt: Mapping[str, Any] = {}
    apply_payload = payloads.get("apply")
    if apply_payload is not None and apply_payload.get("status") == "applied":
        apply_receipt = build_governed_apply_receipt(root, apply_payload)
        _insert_after(
            stages,
            "apply",
            _stage_row(
                "apply_receipt",
                apply_receipt,
                trust_state="revalidated-by-apply-receipt",
            ),
        )

    rollback = payloads.get("rollback")
    if rollback is not None:
        if apply_payload is None:
            return "rollback", "blocked", ["rollback-observation-requires-apply-result"]
        if rollback.get("status") == "rolled-back":
            receipt = build_governed_rollback_receipt(root, apply_payload, rollback)
            _insert_after(
                stages,
                "rollback",
                _stage_row(
                    "rollback_receipt",
                    receipt,
                    trust_state="revalidated-by-rollback-receipt",
                ),
            )
            reasons = receipt.get("reason_codes", [])
            return (
                "rollback",
                str(receipt.get("status", "blocked")),
                [str(value) for value in reasons] if isinstance(reasons, list) else [],
            )
        return "rollback", str(rollback.get("status", "")), []

    if apply_payload is not None:
        if apply_receipt:
            reasons = apply_receipt.get("reason_codes", [])
            return (
                "apply",
                str(apply_receipt.get("status", "blocked")),
                [str(value) for value in reasons] if isinstance(reasons, list) else [],
            )
        return "apply", str(apply_payload.get("status", "")), []
    for stage in reversed(_INPUT_ORDER[:4]):
        if stage in payloads:
            return stage, str(payloads[stage].get("status", "")), []
    return "", "not-observed", []


def build_binding_lifecycle_projection(
    root: pathlib.Path,
    inputs: Optional[Mapping[str, str]] = None,
) -> Dict[str, Any]:
    """Project explicitly supplied lifecycle outputs without executing any lifecycle action."""

    raw_inputs = inputs or {}
    unknown = sorted(str(key) for key in raw_inputs if str(key) not in _INPUT_ORDER)
    if unknown:
        return _observation_error([], ["unknown-lifecycle-input:{}".format(value) for value in unknown])
    normalized = {
        str(key): str(value)
        for key, value in raw_inputs.items()
        if str(value).strip()
    }
    if not normalized:
        return _not_observed()
    payloads, stages, reasons = _load_inputs(root, normalized)
    reasons.extend(_chain_reasons(payloads))
    if reasons:
        return _observation_error(stages, reasons)
    current_stage, status, verifier_reasons = _revalidate_latest(root, payloads, stages)
    execution_class, summary = _next_responsibility(current_stage, status)
    trust_state = str(stages[-1].get("trust_state", "")) if stages else "not-observed"
    return {
        "schema_version": 1,
        "projection": LIFECYCLE_PROJECTION,
        "status": status,
        "read_only": True,
        "network_performed": False,
        "canonical_write_performed": False,
        "automatic_binding_enabled": False,
        "automatic_execution_enabled": False,
        "observed_stage_count": len(stages),
        "current_stage": current_stage,
        "trust_state": trust_state,
        "next_execution_class": execution_class,
        "next_summary_zh": summary,
        "stages": stages,
        "reason_codes": list(dict.fromkeys(verifier_reasons))[:20],
    }
