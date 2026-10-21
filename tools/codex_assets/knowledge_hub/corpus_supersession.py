"""Read-only supersession lineage derived from exact Markdown frontmatter.

An explicit supersedes_candidate link proves historical candidate lineage, not
owner approval, product truth, safe deletion, or a lifecycle transition.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any, Dict, List, Mapping

from .common import KnowledgeHubError

PROJECTION = "knowledge-hub.corpus-supersession/v1"
MAX_ITEMS = 5000
BLOCKING_SIGNALS = frozenset({
    "supersession-declaration-invalid", "supersession-predecessor-missing",
    "supersession-cross-scope", "supersession-cycle",
    "supersession-fork", "supersession-active-requires-owner",
})


def _signal(row: Dict[str, Any], value: str) -> None:
    signals = row.get("signals")
    if not isinstance(signals, list):
        raise KnowledgeHubError("supersession requires canonical corpus signals")
    row["signals"] = sorted(set(signals) | {value})


def _cycles(edges: Mapping[str, str]) -> set:
    """Find every cycle in a single-outgoing-edge graph, in linear time."""
    visited, cycle_nodes = set(), set()
    for start in sorted(edges):
        if start in visited:
            continue
        trail, local = [], {}
        node = start
        while node in edges and node not in visited and node not in local:
            local[node] = len(trail)
            trail.append(node)
            node = edges[node]
        if node in local:
            cycle_nodes.update(trail[local[node]:])
        visited.update(trail)
    return cycle_nodes


def _validated_edges(by_id: Mapping[str, Dict[str, Any]]) -> Dict[str, str]:
    edges = {}
    for identity, row in sorted(by_id.items()):
        body = row.get("body")
        if not isinstance(body, Mapping):
            raise KnowledgeHubError("supersession body observation must be an object")
        if body.get("supersedes_invalid") is True:
            _signal(row, "supersession-declaration-invalid")
            continue
        predecessor = body.get("supersedes_candidate", "")
        if not predecessor:
            continue
        if not isinstance(predecessor, str):
            _signal(row, "supersession-declaration-invalid")
            continue
        previous = by_id.get(predecessor)
        if previous is None:
            _signal(row, "supersession-predecessor-missing")
        elif previous.get("domain") != row.get("domain") or previous.get("kind") != row.get("kind"):
            _signal(row, "supersession-cross-scope")
        else:
            edges[identity] = predecessor
    return edges


def annotate_supersession(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Annotate existing redacted corpus rows, without reading or writing files."""
    if not isinstance(rows, list) or len(rows) > MAX_ITEMS:
        raise KnowledgeHubError("supersession inventory exceeds budget")
    by_id = {}
    for row in rows:
        if not isinstance(row, dict):
            raise KnowledgeHubError("supersession inventory row must be an object")
        if row.get("lane") == "personal-excluded":
            continue
        identity = row.get("id")
        if not isinstance(identity, str) or not identity or identity in by_id:
            raise KnowledgeHubError("supersession corpus identity invalid or duplicated")
        by_id[identity] = row

    edges = _validated_edges(by_id)
    cycles = _cycles(edges)
    for identity in cycles:
        _signal(by_id[identity], "supersession-cycle")

    successors: Dict[str, List[str]] = defaultdict(list)
    for successor, predecessor in edges.items():
        if successor not in cycles and predecessor not in cycles:
            successors[predecessor].append(successor)
            by_id[successor]["supersession"] = {
                "predecessor_id": predecessor, "candidate_only": True,
            }
    for predecessor, child_ids in sorted(successors.items()):
        children = sorted(child_ids)
        old = by_id[predecessor]
        old["supersession"] = {"candidate_successors": children,
                                "candidate_only": True}
        if len(children) > 1:
            _signal(old, "supersession-fork")
            for child in children:
                _signal(by_id[child], "supersession-fork")
        elif old.get("status") == "active":
            _signal(old, "supersession-active-requires-owner")
        elif old.get("status") in {"reviewing", "draft"}:
            _signal(old, "superseded-candidate-provenance")

    blockers = Counter(
        signal for row in by_id.values() for signal in row["signals"]
        if signal in BLOCKING_SIGNALS
    )
    historical_candidates = sum(
        "superseded-candidate-provenance" in row["signals"]
        for row in by_id.values()
    )
    return {
        "projection": PROJECTION,
        "status": "needs-review" if blockers else "report-only",
        "visible_count": len(by_id), "declared_link_count": len(edges),
        "candidate_history_count": historical_candidates,
        "cycle_item_count": len(cycles),
        "blocking_signal_counts": dict(sorted(blockers.items())),
        "candidate_only": True, "read_only": True,
        "automatic_delete_enabled": False,
        "automatic_status_change_enabled": False,
        "owner_approval_performed": False,
        "semantic_review_performed": False,
    }
