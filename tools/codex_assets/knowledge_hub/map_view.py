"""Bounded, rebuildable navigation map for Agent session start."""

from __future__ import annotations

import base64
import hashlib
import json
import pathlib
from collections import Counter
from typing import Any, Dict, Iterable, List, Mapping, Sequence, Tuple

from .common import KnowledgeHubError, compact_json, registry_items
from .model import ITEM_KINDS, ITEM_STATUSES


MAP_SCHEMA = "knowledge-hub.map.v1"
MAP_CURSOR_VERSION = 1
MAP_DEFAULT_LIMIT = 20
MAP_MAX_LIMIT = 100
MAP_DEFAULT_MAX_BYTES = 8192
MAP_MIN_MAX_BYTES = 2048
MAP_MAX_MAX_BYTES = 1024 * 1024
DEFAULT_STATUSES = ("active", "reviewing", "draft")
STATUS_ORDER = {
    "active": 0,
    "reviewing": 1,
    "draft": 2,
    "personal": 3,
    "archived": 4,
    "superseded": 5,
    "rejected": 6,
}


def _digest(value: Any) -> str:
    return hashlib.sha256(compact_json(value).encode("utf-8")).hexdigest()


def _source_fingerprint(items: Sequence[Mapping[str, Any]]) -> str:
    return _digest(
        [
            {
                "id": str(item.get("id", "")),
                "title": str(item.get("title", "")),
                "kind": str(item.get("kind", "")),
                "domain": str(item.get("domain", "")),
                "owner": str(item.get("owner", "")),
                "path": str(item.get("path", "")),
                "status": str(item.get("status", "")),
                "summary_zh": str(item.get("summary_zh", "")),
                "manual_validation_pending": bool(
                    item.get("manual_validation_pending", False)
                ),
                "updated_at": str(item.get("updated_at", "")),
            }
            for item in sorted(items, key=lambda row: str(row.get("id", "")))
        ]
    )


def _cursor_token(payload: Mapping[str, Any]) -> str:
    body = compact_json(payload).encode("utf-8")
    checksum = hashlib.sha256(MAP_SCHEMA.encode("ascii") + b":" + body).hexdigest()[:16]
    raw = body + b"." + checksum.encode("ascii")
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _decode_cursor(token: str) -> Dict[str, Any]:
    try:
        padded = token + "=" * (-len(token) % 4)
        raw = base64.urlsafe_b64decode(padded.encode("ascii"))
        body, checksum = raw.rsplit(b".", 1)
        expected = hashlib.sha256(MAP_SCHEMA.encode("ascii") + b":" + body).hexdigest()[:16]
        if checksum.decode("ascii") != expected:
            raise ValueError("checksum")
        payload = json.loads(body.decode("utf-8"))
    except (ValueError, UnicodeError, json.JSONDecodeError) as exc:
        raise KnowledgeHubError("invalid map cursor") from exc
    if not isinstance(payload, dict) or payload.get("v") != MAP_CURSOR_VERSION:
        raise KnowledgeHubError("invalid map cursor version")
    return payload


def _bounded_counts(values: Iterable[str], limit: int) -> Dict[str, Any]:
    counts = Counter(value for value in values if value)
    ordered = sorted(counts.items(), key=lambda row: (-row[1], row[0]))
    return {
        "values": [{"value": key, "count": count} for key, count in ordered[:limit]],
        "total_values": len(ordered),
        "truncated": len(ordered) > limit,
    }


def _item_projection(item: Mapping[str, Any]) -> Dict[str, Any]:
    summary = " ".join(str(item.get("summary_zh", "")).split())
    return {
        "id": str(item.get("id", "")),
        "title": str(item.get("title", "")),
        "kind": str(item.get("kind", "")),
        "status": str(item.get("status", "")),
        "domain": str(item.get("domain", "")),
        "owner": str(item.get("owner", "")),
        "path": str(item.get("path", "")),
        "summary_zh": summary[:160],
        "authority_lane": _authority_lane(item),
    }


def _authority_lane(item: Mapping[str, Any]) -> str:
    status = str(item.get("status", ""))
    if status == "active" and not bool(item.get("manual_validation_pending", False)):
        return "active"
    if status in {"active", "reviewing", "draft"}:
        return "provisional"
    if status == "personal":
        return "personal"
    return "terminal"


def _apply_page_metadata(
    payload: Dict[str, Any],
    page: Sequence[Mapping[str, Any]],
    *,
    offset: int,
    total: int,
    source_fingerprint: str,
    filter_digest: str,
) -> int:
    next_offset = offset + len(page)
    truncated = next_offset < total
    next_cursor = ""
    if truncated:
        next_cursor = _cursor_token(
            {
                "v": MAP_CURSOR_VERSION,
                "offset": next_offset,
                "source": source_fingerprint,
                "filters": filter_digest,
            }
        )
    payload.update(
        {
            "items": list(page),
            "returned_items": len(page),
            "truncated": truncated,
            "next_cursor": next_cursor,
            "encoded_bytes": 0,
        }
    )
    while True:
        encoded_size = len(compact_json(payload).encode("utf-8"))
        if payload["encoded_bytes"] == encoded_size:
            return encoded_size
        payload["encoded_bytes"] = encoded_size


def _module_projection(items: Sequence[Mapping[str, Any]], limit: int = 24) -> Dict[str, Any]:
    grouped: Dict[str, Counter] = {}
    for item in items:
        domain = str(item.get("domain", "")) or "unclassified"
        counter = grouped.setdefault(domain, Counter())
        counter["total"] += 1
        counter[str(item.get("status", ""))] += 1
    rows = [
        {
            "module": domain,
            "total": counter["total"],
            "active": counter["active"],
            "provisional": counter["reviewing"] + counter["draft"],
            "terminal": counter["archived"] + counter["superseded"] + counter["rejected"],
        }
        for domain, counter in grouped.items()
    ]
    rows.sort(key=lambda row: (-int(row["total"]), str(row["module"])))
    return {
        "items": rows[:limit],
        "total_modules": len(rows),
        "truncated": len(rows) > limit,
    }


def build_knowledge_map(
    root: pathlib.Path,
    *,
    limit: int = MAP_DEFAULT_LIMIT,
    max_bytes: int = MAP_DEFAULT_MAX_BYTES,
    cursor: str = "",
    statuses: Sequence[str] = (),
    kinds: Sequence[str] = (),
    domains: Sequence[str] = (),
    owners: Sequence[str] = (),
    all_statuses: bool = False,
) -> Dict[str, Any]:
    if not 1 <= limit <= MAP_MAX_LIMIT:
        raise KnowledgeHubError("--limit must be between 1 and {}".format(MAP_MAX_LIMIT))
    if not MAP_MIN_MAX_BYTES <= max_bytes <= MAP_MAX_MAX_BYTES:
        raise KnowledgeHubError(
            "--max-bytes must be between {} and {}".format(
                MAP_MIN_MAX_BYTES, MAP_MAX_MAX_BYTES
            )
        )
    if all_statuses and statuses:
        raise KnowledgeHubError("--all-statuses cannot be combined with --status")
    selected_statuses = tuple(statuses) if statuses else (() if all_statuses else DEFAULT_STATUSES)
    invalid_statuses = sorted(set(selected_statuses) - ITEM_STATUSES)
    invalid_kinds = sorted(set(kinds) - ITEM_KINDS)
    if invalid_statuses:
        raise KnowledgeHubError("invalid map status: {}".format(", ".join(invalid_statuses)))
    if invalid_kinds:
        raise KnowledgeHubError("invalid map kind: {}".format(", ".join(invalid_kinds)))

    source_items = registry_items(root)
    source_fingerprint = _source_fingerprint(source_items)
    filters = {
        "status": list(selected_statuses),
        "kind": list(kinds),
        "domain": list(domains),
        "owner": list(owners),
        "all_statuses": bool(all_statuses),
    }
    filter_digest = _digest(filters)
    offset = 0
    if cursor:
        decoded = _decode_cursor(cursor)
        if decoded.get("source") != source_fingerprint:
            raise KnowledgeHubError("map cursor_stale: registry source changed")
        if decoded.get("filters") != filter_digest:
            raise KnowledgeHubError("map cursor_mismatch: filters changed")
        offset = decoded.get("offset")
        if not isinstance(offset, int) or offset < 0:
            raise KnowledgeHubError("invalid map cursor offset")

    filtered = []
    for item in source_items:
        if selected_statuses and item.get("status") not in selected_statuses:
            continue
        if kinds and item.get("kind") not in kinds:
            continue
        if domains and not any(str(item.get("domain", "")).startswith(value) for value in domains):
            continue
        if owners and item.get("owner") not in owners:
            continue
        filtered.append(item)
    filtered.sort(
        key=lambda item: (
            STATUS_ORDER.get(str(item.get("status", "")), 99),
            str(item.get("domain", "")),
            str(item.get("kind", "")),
            str(item.get("id", "")),
        )
    )
    if offset > len(filtered):
        raise KnowledgeHubError("invalid map cursor offset")

    status_counts = Counter(str(item.get("status", "")) for item in source_items)
    authority_counts = Counter(_authority_lane(item) for item in source_items)
    base: Dict[str, Any] = {
        "schema_version": MAP_SCHEMA,
        "read_only": True,
        "navigation_only": True,
        "authority": "registry/items.jsonl",
        "source_fingerprint": source_fingerprint,
        "filters": filters,
        "summary": {
            "total_items": len(source_items),
            "matching_items": len(filtered),
            "active_items": authority_counts["active"],
            "provisional_items": authority_counts["provisional"],
            "terminal_items": status_counts["archived"] + status_counts["superseded"] + status_counts["rejected"],
            "personal_items": status_counts["personal"],
        },
        "modules": _module_projection(source_items),
        "vocabulary": {
            "statuses": _bounded_counts((str(item.get("status", "")) for item in source_items), 12),
            "kinds": _bounded_counts((str(item.get("kind", "")) for item in source_items), 24),
            "domains": _bounded_counts((str(item.get("domain", "")) for item in source_items), 24),
            "owners": _bounded_counts((str(item.get("owner", "")) for item in source_items), 16),
        },
        "items": [],
        "returned_items": 0,
        "truncated": False,
        "next_cursor": "",
        "encoded_bytes": 0,
        "notes_zh": "map 只用于导航，不是事实或引用证据；active/provisional 必须按 authority_lane 区分。",
    }
    page: List[Dict[str, Any]] = []
    while offset + len(page) < len(filtered) and len(page) < limit:
        candidate = _item_projection(filtered[offset + len(page)])
        trial = dict(base)
        trial_page = page + [candidate]
        trial_size = _apply_page_metadata(
            trial,
            trial_page,
            offset=offset,
            total=len(filtered),
            source_fingerprint=source_fingerprint,
            filter_digest=filter_digest,
        )
        if trial_size > max_bytes:
            break
        page.append(candidate)
    if not page and offset < len(filtered):
        raise KnowledgeHubError("map byte budget cannot fit one item; increase --max-bytes")
    encoded_size = _apply_page_metadata(
        base,
        page,
        offset=offset,
        total=len(filtered),
        source_fingerprint=source_fingerprint,
        filter_digest=filter_digest,
    )
    if encoded_size > max_bytes:
        raise KnowledgeHubError("map fixed metadata exceeds --max-bytes")
    return base


def render_knowledge_map(payload: Mapping[str, Any]) -> str:
    summary = payload.get("summary", {})
    lines = [
        "# Knowledge Hub map",
        "",
        "items: total={total_items} matching={matching_items} active={active_items} provisional={provisional_items}".format(
            **summary
        ),
        "",
        "## modules",
    ]
    for row in payload.get("modules", {}).get("items", []):
        lines.append(
            "- {module}: total={total} active={active} provisional={provisional}".format(
                **row
            )
        )
    lines.extend(["", "## items"])
    for item in payload.get("items", []):
        lines.append(
            "- [{status}/{kind}] {id}: {title} ({path})".format(**item)
        )
    if payload.get("truncated"):
        lines.extend(["", "truncated: true; continue with next_cursor"])
    return "\n".join(lines) + "\n"
