"""Result projection extracted without changing selection, preview or fields."""

from typing import Any, Dict, List, Set

from .common import source_id
from .query_scope import candidate_concepts
from .search_query_support import _preview


def deduplicate_paths(candidates):
    deduplicated: List[Dict[str, Any]] = []
    seen_paths: Set[str] = set()
    for candidate in candidates:
        candidate_path = str(candidate.get("path", ""))
        if candidate_path in seen_paths:
            continue
        seen_paths.add(candidate_path)
        deduplicated.append(candidate)
    return deduplicated


def search_result(row, item, scored, concept_plan, filters, physical_sources):
    score, reasons, coverage = scored
    line_no, preview, body_match, preview_redacted = _preview(
        str(row["body"]),
        list((candidate_concepts(concept_plan, item) or concept_plan).terms),
        item,
    )
    selected_source = "knowledge-hub"
    if filters.sources:
        selected_source = next((value for value in filters.sources if value in physical_sources), "knowledge-hub")
    result: Dict[str, Any] = {
        "source": selected_source,
        "path": str(row["path"]),
        "line": line_no,
        "preview": preview,
        "preview_redacted": preview_redacted,
        "score": score,
        "match": "body-and-metadata" if body_match and item else "body" if body_match else "registry-metadata",
        "match_kind": reasons[0],
        "why_selected": reasons,
        "query_coverage": round(coverage, 3),
        "evidence_strength": item.get("evidence_strength", ""),
        "manual_validation_pending": bool(item.get("manual_validation_pending", False)),
        "item_id": item.get("id", ""),
        "id": item.get("id", ""),
        "title": item.get("title", ""),
        "kind": item.get("kind", ""),
        "domain": item.get("domain", ""),
        "status": item.get("status", ""),
        "owner": item.get("owner", ""),
        "source_id": source_id(item),
        "review_after": item.get("review_after", ""),
        "tags": item.get("tags", []),
    }
    return result
