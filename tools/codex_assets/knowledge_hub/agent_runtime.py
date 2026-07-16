"""Derived EvidencePack and deterministic Agent action preflight."""

from __future__ import annotations

import pathlib
import re
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set

from .common import KnowledgeHubError, registry_items
from .model import guard_regex_safety_error
from .search import SearchFilters, SearchIndex, search


EVIDENCE_PACK_SCHEMA = "knowledge-hub.evidence-pack.v1"
ACTION_CHECK_SCHEMA = "knowledge-hub.action-check.v1"
ACTIVE_STATUS = "active"
PROVISIONAL_STATUSES = {"reviewing", "draft"}
TERMINAL_STATUSES = {"archived", "superseded", "rejected"}
EVIDENCE_PACK_MAX_LIMIT = 100
ACTION_TEXT_MAX_CHARS = 8192
ACTION_MAX_LIST_VALUES = 32
ACTION_MAX_SCOPE_CHARS = 200
ACTION_MAX_EXCEPTION_CHARS = 500


def _contract(item: Mapping[str, Any]) -> Mapping[str, Any]:
    value = item.get("agent_contract")
    return value if isinstance(value, Mapping) else {}


def _is_active_authority(item: Mapping[str, Any]) -> bool:
    return (
        item.get("status") == ACTIVE_STATUS
        and not bool(item.get("manual_validation_pending", False))
    )


def _scope_matches(contract: Mapping[str, Any], scope_refs: Sequence[str]) -> bool:
    declared = {
        str(value) for value in contract.get("scope_refs", []) if str(value)
    }
    if not declared or "global" in declared:
        return True
    return bool(declared.intersection(str(value) for value in scope_refs))


def _pack_item(
    item: Mapping[str, Any],
    result: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    contract = _contract(item)
    evidence_refs = item.get("evidence_refs", [])
    if not isinstance(evidence_refs, list):
        evidence_refs = []
    output = {
        "id": str(item.get("id", "")),
        "title": str(item.get("title", "")),
        "kind": str(item.get("kind", "")),
        "status": str(item.get("status", "")),
        "runtime_role": str(contract.get("role", "untyped")),
        "force": str(contract.get("force", "advisory")),
        "subject": str(contract.get("subject", "")),
        "scope_refs": list(contract.get("scope_refs", [])),
        "summary_zh": str(item.get("summary_zh", "")),
        "path": str(item.get("path", "")),
        "evidence_refs": evidence_refs,
        "authority": "active" if _is_active_authority(item) else "provisional",
    }
    if result:
        output["score"] = result.get("score", 0)
        output["why_selected"] = list(result.get("why_selected", []))
        output["query_coverage"] = result.get("query_coverage", 0)
    return output


def _append_unique(target: List[Dict[str, Any]], row: Dict[str, Any]) -> None:
    if not any(item.get("id") == row.get("id") for item in target):
        target.append(row)


def _active_search_filters(filters: SearchFilters) -> Optional[SearchFilters]:
    if filters.statuses and ACTIVE_STATUS not in filters.statuses:
        return None
    return SearchFilters(
        sources=filters.sources,
        owners=filters.owners,
        statuses=(ACTIVE_STATUS,),
        kinds=filters.kinds,
        domains=filters.domains,
        source_ids=filters.source_ids,
    )


def build_evidence_pack(
    root: pathlib.Path,
    query: str,
    *,
    limit: int = 20,
    filters: Optional[SearchFilters] = None,
    scope_refs: Sequence[str] = (),
) -> Dict[str, Any]:
    if not 1 <= limit <= EVIDENCE_PACK_MAX_LIMIT:
        raise KnowledgeHubError(
            "EvidencePack limit must be between 1 and {}".format(
                EVIDENCE_PACK_MAX_LIMIT
            )
        )
    _validate_runtime_values("scope_refs", scope_refs, ACTION_MAX_SCOPE_CHARS)
    filters = filters or SearchFilters()
    search_index = SearchIndex(root)
    search_payload = search(
        root,
        query,
        limit=limit,
        filters=filters,
        search_index=search_index,
    )
    active_filters = _active_search_filters(filters)
    active_payload = (
        search(
            root,
            query,
            limit=limit,
            filters=active_filters,
            search_index=search_index,
        )
        if active_filters is not None
        else {"results": []}
    )
    items = registry_items(root)
    by_id = {str(item.get("id", "")): item for item in items if item.get("id")}
    pack: Dict[str, Any] = {
        "schema_version": EVIDENCE_PACK_SCHEMA,
        "read_only": True,
        "query": query,
        "scope_refs": list(scope_refs),
        "must": [],
        "should": [],
        "context": [],
        "provisional": [],
        "conflict": [],
        "missing": [],
        "search_trace": search_payload.get("search_trace", {}),
        "active_search_trace": active_payload.get("search_trace", {}),
        "source_index": search_payload.get("index", {}),
        "authority_contract": {
            "active_only": True,
            "active_supplemental_search": active_filters is not None,
            "candidate_constraints_enforced": False,
            "candidate_hits_consume_active_limit": False,
            "navigation_is_evidence": False,
        },
    }
    lifecycle_excluded: List[Dict[str, str]] = []
    selected_ids: Set[str] = set()
    result_stream = list(active_payload.get("results", [])) + list(
        search_payload.get("results", [])
    )
    for result in result_stream:
        item_id = str(result.get("item_id", result.get("id", "")))
        item = by_id.get(item_id)
        if item is None:
            continue
        status = str(item.get("status", ""))
        if status in TERMINAL_STATUSES or status == "personal":
            if len(lifecycle_excluded) < 5:
                lifecycle_excluded.append(
                    {"id": item_id, "status": status, "reason": "non-serviceable-lifecycle"}
                )
            continue
        row = _pack_item(item, result)
        selected_ids.add(item_id)
        if not _is_active_authority(item):
            _append_unique(pack["provisional"], row)
            continue
        contract = _contract(item)
        role = contract.get("role")
        if role == "constraint" and _scope_matches(contract, scope_refs):
            _append_unique(pack["must"], row)
        elif role == "guidance":
            _append_unique(pack["should"], row)
        elif role == "question":
            _append_unique(pack["missing"], row)
        elif role == "symbol":
            continue
        else:
            _append_unique(pack["context"], row)

    # Explicit active constraints are a completeness surface, not a retrieval guess.
    for item in items:
        contract = _contract(item)
        if (
            _is_active_authority(item)
            and contract.get("role") == "constraint"
            and _scope_matches(contract, scope_refs)
        ):
            _append_unique(pack["must"], _pack_item(item))
            selected_ids.add(str(item.get("id", "")))
        elif (
            item.get("status") in PROVISIONAL_STATUSES
            and contract.get("role") == "constraint"
            and _scope_matches(contract, scope_refs)
            and str(item.get("id", "")) in selected_ids
        ):
            _append_unique(pack["provisional"], _pack_item(item))

    selected = {
        row["id"]
        for lane in ("must", "should", "context", "provisional", "missing")
        for row in pack[lane]
    }
    for item_id in sorted(selected):
        item = by_id.get(item_id, {})
        relations = _contract(item).get("relations", {})
        if not isinstance(relations, Mapping):
            continue
        for target in relations.get("conflicts_with", []):
            if target in selected:
                pair = sorted((item_id, str(target)))
                conflict = {"source_id": pair[0], "target_id": pair[1], "relation": "conflicts_with"}
                if conflict not in pack["conflict"]:
                    pack["conflict"].append(conflict)
    if not any(pack[lane] for lane in ("must", "should", "context", "provisional", "missing")):
        pack["missing"].append(
            {
                "reason": "no_match",
                "message_zh": "当前查询没有可服务条目；请根据 search_trace 重试，不能据此断言知识不存在。",
            }
        )
    pack["counts"] = {
        lane: len(pack[lane])
        for lane in ("must", "should", "context", "provisional", "conflict", "missing")
    }
    pack["search_trace"]["lifecycle_excluded"] = lifecycle_excluded
    return pack


def render_evidence_pack(pack: Mapping[str, Any]) -> str:
    labels = (
        ("must", "MUST"),
        ("should", "SHOULD"),
        ("context", "CONTEXT"),
        ("provisional", "PROVISIONAL"),
        ("conflict", "CONFLICT"),
        ("missing", "MISSING"),
    )
    lines: List[str] = []
    for key, label in labels:
        lines.append(label)
        rows = pack.get(key, [])
        if not rows:
            lines.append("- (none)")
        for row in rows:
            if row.get("id"):
                lines.append(
                    "- [{id}] {summary_zh} [status={status}; role={runtime_role}]".format(
                        **row
                    )
                )
            else:
                lines.append("- {}".format(row.get("message_zh", row)))
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _contains_any(text: str, patterns: Iterable[str]) -> List[str]:
    lowered = text.casefold()
    return [pattern for pattern in patterns if str(pattern).casefold() in lowered]


def _validate_runtime_values(
    name: str,
    values: Sequence[str],
    maximum_length: int,
) -> None:
    if isinstance(values, (str, bytes)) or not isinstance(values, Sequence):
        raise KnowledgeHubError("{} must be a sequence of strings".format(name))
    if len(values) > ACTION_MAX_LIST_VALUES:
        raise KnowledgeHubError(
            "{} exceeds {} values".format(name, ACTION_MAX_LIST_VALUES)
        )
    for value in values:
        text = str(value)
        if not text.strip():
            raise KnowledgeHubError("{} must contain non-empty values".format(name))
        if len(text) > maximum_length:
            raise KnowledgeHubError(
                "{} value exceeds {} characters".format(name, maximum_length)
            )


def check_action(
    root: pathlib.Path,
    task: str,
    candidate: str,
    *,
    scope_refs: Sequence[str] = (),
    asserted_exceptions: Sequence[str] = (),
) -> Dict[str, Any]:
    if not task.strip():
        raise KnowledgeHubError("task must not be empty")
    if not candidate.strip():
        raise KnowledgeHubError("candidate must not be empty")
    if len(task) > ACTION_TEXT_MAX_CHARS:
        raise KnowledgeHubError(
            "task exceeds {} characters".format(ACTION_TEXT_MAX_CHARS)
        )
    if len(candidate) > ACTION_TEXT_MAX_CHARS:
        raise KnowledgeHubError(
            "candidate exceeds {} characters".format(ACTION_TEXT_MAX_CHARS)
        )
    _validate_runtime_values("scope_refs", scope_refs, ACTION_MAX_SCOPE_CHARS)
    _validate_runtime_values(
        "asserted_exceptions", asserted_exceptions, ACTION_MAX_EXCEPTION_CHARS
    )
    combined = "{}\n{}".format(task, candidate)
    applicable: List[Dict[str, Any]] = []
    provisional: List[Dict[str, Any]] = []
    violations: List[Dict[str, Any]] = []
    needs_review: List[Dict[str, Any]] = []
    evaluated: List[Dict[str, Any]] = []

    for item in registry_items(root):
        contract = _contract(item)
        if contract.get("role") != "constraint" or not _scope_matches(contract, scope_refs):
            continue
        row = _pack_item(item)
        if not _is_active_authority(item):
            if item.get("status") in PROVISIONAL_STATUSES or item.get("status") == "active":
                provisional.append(row)
            continue
        guard = contract.get("guard")
        if not isinstance(guard, Mapping):
            applicable.append(row)
            needs_review.append({"id": row["id"], "reason": "constraint_has_no_deterministic_guard"})
            continue
        when_matches = _contains_any(combined, guard.get("when_any", []))
        if guard.get("when_any") and not when_matches:
            continue
        applicable.append(row)
        capabilities = set(contract.get("capabilities", []))
        if not {"enforceable", "guardable"}.issubset(capabilities):
            needs_review.append({"id": row["id"], "reason": "constraint_not_enforceable_and_guardable"})
            continue
        asserted = sorted(set(asserted_exceptions).intersection(contract.get("exceptions", [])))
        if asserted:
            needs_review.append(
                {
                    "id": row["id"],
                    "reason": "asserted_exception_requires_host_attestation",
                    "exceptions": asserted,
                }
            )
        deny_matches = _contains_any(candidate, guard.get("deny_any", []))
        regex_matches = []
        for pattern in guard.get("deny_regex", []):
            unsafe_reason = guard_regex_safety_error(str(pattern))
            if unsafe_reason:
                needs_review.append(
                    {
                        "id": row["id"],
                        "reason": "unsafe_guard_regex",
                    }
                )
                continue
            try:
                if re.search(str(pattern), candidate, flags=re.IGNORECASE):
                    regex_matches.append(str(pattern))
            except re.error:
                needs_review.append({"id": row["id"], "reason": "invalid_guard_regex"})
        required = list(guard.get("require_any", []))
        required_matches = _contains_any(candidate, required)
        if deny_matches or regex_matches or (required and not required_matches):
            violations.append(
                {
                    "id": row["id"],
                    "denied_phrases": deny_matches,
                    "denied_regex": regex_matches,
                    "missing_required_any": required if required and not required_matches else [],
                }
            )
        else:
            evaluated.append(
                {
                    "id": row["id"],
                    "when_matches": when_matches,
                    "result": "no_violation",
                }
            )

    if violations:
        verdict = "BLOCK"
        reason = "one or more active deterministic constraints were violated"
    elif needs_review or not applicable:
        verdict = "NEEDS_REVIEW"
        reason = (
            "applicable constraints require human or host-attested review"
            if applicable
            else "no explicit active applicable constraint can authorize this action"
        )
    else:
        verdict = "ALLOW"
        reason = "all explicit active applicable deterministic constraints passed"
    return {
        "schema_version": ACTION_CHECK_SCHEMA,
        "read_only": True,
        "verdict": verdict,
        "reason": reason,
        "task": task,
        "candidate_sha256": __import__("hashlib").sha256(candidate.encode("utf-8")).hexdigest(),
        "scope_refs": list(scope_refs),
        "applicable_must": applicable,
        "violations": violations,
        "needs_review": needs_review,
        "evaluated": evaluated,
        "provisional_constraints": provisional,
        "authority_contract": {
            "active_only": True,
            "candidate_constraints_enforced": False,
            "no_applicable_rule_allows": False,
            "asserted_exception_is_authorization": False,
        },
    }
