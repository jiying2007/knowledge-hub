import collections
import hashlib
import pathlib
from typing import Any, Dict, List, Sequence, Tuple

REVIEW_CONTENT_BOUND_DECISIONS = {"accept-as-review-record", "archive-only", "reject"}


def _is_blank(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip()
    if isinstance(value, (list, dict)):
        return not value
    return False


def _as_list(value: Any) -> List[Any]:
    return value if isinstance(value, list) else []


def _repository_file_sha256(root: pathlib.Path, relative_path: Any) -> str:
    path_text = str(relative_path or "")
    if not path_text:
        return ""
    candidate = pathlib.Path(path_text)
    if candidate.is_absolute():
        return ""
    resolved = (root / candidate).resolve()
    try:
        resolved.relative_to(root)
    except ValueError:
        return ""
    if not resolved.is_file():
        return ""
    digest = hashlib.sha256()
    with resolved.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _review_priority(item: Dict[str, Any]) -> str:
    status_value = str(item.get("status", ""))
    path_text = str(item.get("path", ""))
    tags = {str(tag) for tag in _as_list(item.get("tags", []))}
    promotion_like = (
        status_value == "active"
        or path_text == "AGENTS.md"
        or path_text.startswith("domains/embedded/standards/")
        or path_text.startswith("src/codex-home/vendor/skills/")
        or "promoted" in tags
        or "team-standard" in tags
    )
    if promotion_like:
        return "P0"
    if status_value == "reviewing":
        return "P1"
    if status_value in {"archived", "personal"}:
        return "P3"
    return "P2"


def _make_item_row(
    root: pathlib.Path,
    item: Dict[str, Any],
    queue_type: str,
    reasons: List[str],
    missing_fields: List[str],
) -> Dict[str, Any]:
    item_id = str(item.get("id", ""))
    source = item.get("source", {}) if isinstance(item.get("source", {}), dict) else {}
    content_sha256 = _repository_file_sha256(root, item.get("path", ""))
    return {
        "queue_id": "item:{}:{}".format(item_id, queue_type),
        "queue_type": queue_type,
        "object_type": "registry-item",
        "id": item_id,
        "title": str(item.get("title", "")),
        "kind": str(item.get("kind", "")),
        "domain": str(item.get("domain", "")),
        "path": str(item.get("path", "")),
        "content_hash_required": True,
        "content_hash_status": "bound" if content_sha256 else "unavailable",
        "content_sha256": content_sha256,
        "owner": str(item.get("owner", "")),
        "status": str(item.get("status", "")),
        "review_after": str(item.get("review_after", "")),
        "priority": _review_priority(item),
        "reasons": reasons,
        "missing_fields": missing_fields,
        "source_id": str(source.get("source_id", "")),
        "evidence_refs": _as_list(item.get("validation_refs", [])) + _as_list(item.get("evidence_refs", [])),
        "generated_by_ai": bool(item.get("generated_by_ai", False)),
        "ai_role": str(item.get("ai_role", "")),
        "ai_model_or_tool": str(item.get("ai_model_or_tool", "")),
        "ai_generated_at": str(item.get("ai_generated_at", "")),
        "human_reviewed_by": str(item.get("human_reviewed_by", "")),
        "human_reviewed_at": str(item.get("human_reviewed_at", "")),
        "review_basis": str(item.get("review_basis", "")),
        "read_status": str(item.get("read_status", "")),
        "source_license": str(item.get("source_license", "")),
        "retrieved_at": str(item.get("retrieved_at", "")),
        "promotion_decision": str(item.get("promotion_decision", "none") or "none"),
        "read_only": True,
        "report_only": True,
        "owner_gate_mutation": False,
        "memory_write": False,
        "source_project_write": False,
        "next_commands": ["rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics --explain {}".format(item_id)],
        "must_not": ["不生成 owner decision", "不关闭 owner gate", "不写 memory", "不自动提升 active"],
    }


def _source_looks_external(source: Dict[str, Any]) -> bool:
    path_text = str(source.get("path", ""))
    fields = ["retrieved_at", "read_status", "source_license", "source_url", "url"]
    return path_text.startswith(("http://", "https://")) or any(not _is_blank(source.get(field)) for field in fields)


def _make_source_row(source: Dict[str, Any]) -> Dict[str, Any]:
    source_id = str(source.get("id", ""))
    missing = [field for field in ["retrieved_at", "read_status", "source_license", "review_status"] if _is_blank(source.get(field))]
    return {
        "queue_id": "source:{}:external-source-review".format(source_id),
        "queue_type": "external-source-review",
        "object_type": "registered-source",
        "id": source_id,
        "title": str(source.get("name", source_id)),
        "kind": "registered-source",
        "domain": "",
        "path": str(source.get("path", "")),
        "content_hash_required": False,
        "content_hash_status": "not-applicable",
        "content_sha256": "",
        "owner": str(source.get("owner", "")),
        "status": str(source.get("status", "")),
        "review_after": str(source.get("review_after", "")),
        "priority": "P2" if missing else "P3",
        "reasons": ["external-source-fields-incomplete"] if missing else ["external-source-review-tracked"],
        "missing_fields": missing,
        "source_id": source_id,
        "evidence_refs": [],
        "generated_by_ai": False,
        "read_status": str(source.get("read_status", "")),
        "source_license": str(source.get("source_license", "")),
        "retrieved_at": str(source.get("retrieved_at", "")),
        "promotion_decision": str(source.get("promotion_decision", "none") or "none"),
        "read_only": True,
        "report_only": True,
        "owner_gate_mutation": False,
        "memory_write": False,
        "source_project_write": False,
        "next_commands": ["rtk bash ~/knowledge-hub/tools/knowledge-index-plan.sh --section source --json"],
        "must_not": ["不生成 owner decision", "不关闭 owner gate", "不写 memory", "不自动提升 active"],
    }


def _collect_item_rows(root: pathlib.Path, items: Sequence[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    ai_rows: List[Dict[str, Any]] = []
    external_rows: List[Dict[str, Any]] = []
    external_fields = ["retrieved_at", "read_status", "source_license", "source_url", "url"]
    for item in items:
        if item.get("generated_by_ai") is True:
            missing = [field for field in ["human_reviewed_by", "human_reviewed_at", "review_basis"] if _is_blank(item.get(field))]
            current_sha = _repository_file_sha256(root, item.get("path", ""))
            stored_sha = str(item.get("human_review_content_sha256", ""))
            decision = str(item.get("human_review_decision", ""))
            drifted = decision in REVIEW_CONTENT_BOUND_DECISIONS and bool(stored_sha) and stored_sha != current_sha
            if missing:
                ai_rows.append(_make_item_row(root, item, "ai-human-review", ["missing-{}".format(field.replace("_", "-")) for field in missing], missing))
            elif decision in {"needs-edits", "defer"}:
                ai_rows.append(_make_item_row(root, item, "ai-human-review", ["unresolved-{}".format(decision)], ["review_resolution"]))
            elif drifted:
                ai_rows.append(_make_item_row(root, item, "ai-human-review", ["unresolved-content-sha256-drift"], ["review_resolution"]))
        if str(item.get("kind", "")) == "external-source-note" or any(not _is_blank(item.get(field)) for field in external_fields):
            missing = [field for field in ["retrieved_at", "read_status", "source_license", "review_basis"] if _is_blank(item.get(field))]
            if missing:
                external_rows.append(_make_item_row(root, item, "external-source-review", ["missing-{}".format(field.replace("_", "-")) for field in missing], missing))
    return ai_rows, external_rows


def _queue_command(row: Dict[str, Any], limit: int, json_mode: bool = False, forms_jsonl: bool = False, validate_path: str = "") -> str:
    parts = ["rtk", "bash", "~/knowledge-hub/tools/knowledge-index-plan.sh", "--section", "review-queue"]
    if row.get("queue_type"):
        parts.extend(["--queue-type", str(row["queue_type"])])
    if row.get("owner"):
        parts.extend(["--queue-owner", str(row["owner"])])
    parts.extend(["--queue-limit", str(limit)])
    if json_mode:
        parts.append("--json")
    if forms_jsonl:
        parts.append("--queue-forms-jsonl")
    if validate_path:
        parts.extend(["--validate-queue-forms", validate_path])
    return " ".join(parts)


def build_review_queues(
    root: pathlib.Path,
    items: Sequence[Dict[str, Any]],
    sources: Sequence[Dict[str, Any]],
    today: Any,
    final_profile: str,
    limit: int,
) -> Dict[str, Any]:
    ai_rows, external_rows = _collect_item_rows(root, items)
    for source in sources:
        if _source_looks_external(source):
            row = _make_source_row(source)
            if row.get("missing_fields"):
                external_rows.append(row)
    def key(row: Dict[str, Any]) -> Any:
        return (
            str(row.get("priority", "P9")),
            str(row.get("review_after", "") or "9999-12-31"),
            str(row.get("owner", "")),
            str(row.get("id", "")),
        )
    ai_rows = sorted(ai_rows, key=key)
    external_rows = sorted(external_rows, key=key)
    all_rows = ai_rows + external_rows
    recommended = ai_rows[0] if ai_rows else (external_rows[0] if external_rows else {})
    priorities = collections.Counter(str(row.get("priority", "")) for row in all_rows)
    owners = collections.Counter(str(row.get("owner", "") or "<missing-owner>") for row in all_rows)
    active_rows = [row for row in all_rows if row.get("priority") == "P0"]
    return {
        "status": "needs-human-review" if all_rows else "clear", "read_only": True, "report_only": True,
        "final_profile": final_profile, "active_blocking_final_gate": bool(active_rows), "product_blocking_final_gate": bool(all_rows),
        "blocking_final_gate": bool(all_rows), "queue_source": "registry/items.jsonl + registry/sources.json", "sample_limit": limit,
        "summary": {"total_pending_count": len(all_rows), "ai_generated_pending_count": len(ai_rows), "external_source_pending_count": len(external_rows), "active_or_promotion_blocker_count": len(active_rows), "by_priority": dict(sorted(priorities.items())), "by_owner": dict(sorted(owners.items()))},
        "ai_generated_pending": ai_rows[:limit], "external_source_pending": external_rows[:limit],
        "commands": {"status_json": "rtk bash ~/knowledge-hub/tools/knowledge-status.sh --as-of {} --json".format(today.isoformat()), "index_plan": "rtk bash ~/knowledge-hub/tools/knowledge-index-plan.sh --section review-queue --json", "recommended_batch_json": _queue_command(recommended, limit, json_mode=True), "recommended_forms_jsonl": _queue_command(recommended, limit, forms_jsonl=True), "recommended_validate_queue_forms": _queue_command(recommended, limit, json_mode=True, validate_path="'<review-queue-forms.jsonl>'")},
        "must_not": ["队列是 report-only 派生视图，不写 registry", "不得把 AI 草稿或外部资料队列当 owner decision", "不得自动提升 active 或关闭 owner gate", "不得写 ~/.codex/memories"],
    }
