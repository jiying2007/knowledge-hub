"""P7 derived temporal context graph from governed registry facts.

No LLM extraction is performed here. The graph uses explicit relations, lifecycle
fields, tags, and validity windows, and is always non-authoritative.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import pathlib
from typing import Any, Dict, List, Mapping, Sequence, Set, Tuple

from .common import KnowledgeHubError, registry_items, resolve_today


def validate_temporal_fields(
    item: Mapping[str, Any],
    *,
    require_superseded_link: bool = False,
) -> List[str]:
    errors: List[str] = []
    parsed: Dict[str, dt.date] = {}
    for field in ("valid_from", "valid_to"):
        value = item.get(field)
        if value in (None, ""):
            continue
        try:
            parsed[field] = dt.date.fromisoformat(str(value))
        except ValueError:
            errors.append("{} must use YYYY-MM-DD".format(field))
    if (
        "valid_from" in parsed
        and "valid_to" in parsed
        and parsed["valid_from"] > parsed["valid_to"]
    ):
        errors.append("valid_from must not exceed valid_to")
    if (
        require_superseded_link
        and str(item.get("status", "")) == "superseded"
        and not item.get("superseded_by")
    ):
        errors.append("superseded item requires superseded_by")
    return errors


def _date(value: Any, field: str) -> dt.date:
    try:
        return dt.date.fromisoformat(str(value))
    except ValueError as exc:
        raise KnowledgeHubError("{} must use YYYY-MM-DD".format(field)) from exc


def _eligible(item: Mapping[str, Any], today: dt.date) -> bool:
    errors = validate_temporal_fields(item)
    if errors:
        raise KnowledgeHubError("; ".join(errors))
    valid_from = item.get("valid_from")
    valid_to = item.get("valid_to")
    if valid_from and today < _date(valid_from, "valid_from"):
        return False
    if valid_to and today > _date(valid_to, "valid_to"):
        return False
    return str(item.get("status", "")) not in {"rejected"}


def _episode_id(item: Mapping[str, Any]) -> str:
    payload = "{}\0{}\0{}\0{}".format(
        item.get("id", ""),
        item.get("created_at", ""),
        item.get("updated_at", ""),
        item.get("source", ""),
    )
    return "episode-" + hashlib.sha256(payload.encode("utf-8")).hexdigest()[:20]


def _explicit_edges(item: Mapping[str, Any]) -> List[Tuple[str, str]]:
    edges: List[Tuple[str, str]] = []
    contract = item.get("agent_contract", {})
    relations = contract.get("relations", {}) if isinstance(contract, Mapping) else {}
    if isinstance(relations, Mapping):
        for relation, targets in relations.items():
            if isinstance(targets, list):
                edges.extend((str(relation), str(target)) for target in targets)
    superseded_by = item.get("superseded_by")
    if superseded_by:
        edges.append(("superseded_by", str(superseded_by)))
    return edges


def temporal_context_graph(
    root: pathlib.Path,
    *,
    seed_ids: Sequence[str] = (),
    as_of: str = "",
    maximum_nodes: int = 1000,
) -> Dict[str, Any]:
    today, source = resolve_today(as_of)
    rows = [row for row in registry_items(root) if row.get("id") and _eligible(row, today)]
    by_id = {str(row["id"]): row for row in rows}
    if seed_ids:
        requested = {str(value) for value in seed_ids}
        frontier: Set[str] = requested.intersection(by_id)
    else:
        frontier = set(by_id)
    visited: Set[str] = set()
    edges: List[Dict[str, Any]] = []
    while frontier and len(visited) < maximum_nodes:
        item_id = sorted(frontier)[0]
        frontier.remove(item_id)
        if item_id in visited:
            continue
        visited.add(item_id)
        item = by_id[item_id]
        for relation, target in _explicit_edges(item):
            if target not in by_id:
                continue
            edges.append(
                {
                    "source_id": item_id,
                    "relation": relation,
                    "target_id": target,
                    "valid_from": item.get("valid_from", ""),
                    "valid_to": item.get("valid_to", ""),
                    "source_item_id": item_id,
                }
            )
            if target not in visited and seed_ids:
                frontier.add(target)
    nodes = []
    episodes = []
    for item_id in sorted(visited):
        item = by_id[item_id]
        nodes.append(
            {
                "id": item_id,
                "kind": "knowledge-item",
                "title": str(item.get("title", "")),
                "status": str(item.get("status", "")),
                "domain": str(item.get("domain", "")),
                "valid_from": str(item.get("valid_from", "")),
                "valid_to": str(item.get("valid_to", "")),
                "tags": [str(value) for value in item.get("tags", [])][:32],
            }
        )
        episodes.append(
            {
                "id": _episode_id(item),
                "item_id": item_id,
                "observed_at": str(item.get("updated_at", item.get("created_at", ""))),
                "provenance": item.get("source", {}),
            }
        )
    return {
        "schema_version": "knowledge-hub.temporal-context-graph.v1",
        "status": "pass",
        "derived": True,
        "authoritative": False,
        "as_of": today.isoformat(),
        "as_of_source": source,
        "nodes": nodes,
        "edges": edges,
        "episodes": episodes,
        "node_count": len(nodes),
        "edge_count": len(edges),
        "canonical_graph_mutated": False,
    }
