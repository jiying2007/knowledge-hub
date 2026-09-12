"""P6 retrieval v4: ACL-first hierarchical multi-lane retrieval.

Canonical Markdown/registry remain authoritative. Chunks, vectors, lane scores, and
fusion are derived and may be deleted/rebuilt without changing canonical state.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import math
import pathlib
import re
from typing import Any, Callable, Dict, List, Mapping, Optional, Sequence, Tuple

from .common import KnowledgeHubError, registry_items, resolve_today
from .runtime_p5_security import authorize_item, principal_context, trust_class
from .runtime_v3_contracts import DEFAULT_AGENT, agent_profile
from .search import search_tokens

MAX_CORPUS_ITEMS = 5000
MAX_FILE_BYTES = 4 * 1024 * 1024
MAX_CHUNKS_PER_ITEM = 128
MAX_CHUNK_CHARS = 4000
MAX_EMBEDDING_DIMS = 4096
DEFAULT_DIMS = 256
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
IDENTIFIER_RE = re.compile(r"(?:[A-Za-z]+[_./:-]\w+|\bv?\d+\.\d+(?:\.\d+)?\b)")
TEMPORAL_TERMS = {"when", "timeline", "history", "historical", "当前", "历史", "何时", "版本"}
GRAPH_TERMS = {"related", "depends", "relation", "关联", "依赖", "关系"}
EmbeddingFn = Callable[[str], Sequence[float]]
RerankFn = Callable[[str, Sequence[Mapping[str, Any]]], Sequence[Mapping[str, Any]]]


def _date(value: Any, label: str) -> Optional[dt.date]:
    if value in (None, ""):
        return None
    try:
        return dt.date.fromisoformat(str(value))
    except ValueError as exc:
        raise KnowledgeHubError("{} must use YYYY-MM-DD".format(label)) from exc


def _temporal_eligible(item: Mapping[str, Any], today: dt.date) -> bool:
    valid_from = _date(item.get("valid_from"), "valid_from")
    valid_to = _date(item.get("valid_to"), "valid_to")
    if valid_from and valid_to and valid_from > valid_to:
        raise KnowledgeHubError("valid_from must not exceed valid_to")
    if valid_from and today < valid_from:
        return False
    if valid_to and today > valid_to:
        return False
    return str(item.get("status", "")) in {"active", "reviewing", "draft"}


def _read_text(root: pathlib.Path, relative: str) -> str:
    path = root / relative
    try:
        stat = path.lstat()
    except OSError:
        return ""
    if path.is_symlink() or not path.is_file() or stat.st_size > MAX_FILE_BYTES:
        return ""
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return ""


def _chunk_id(item_id: str, heading: str, start: int, text: str) -> str:
    digest = hashlib.sha256(
        "{}\0{}\0{}\0{}".format(item_id, heading, start, text).encode("utf-8")
    ).hexdigest()
    return "{}:{}".format(item_id, digest[:20])


def hierarchical_chunks(
    root: pathlib.Path,
    item: Mapping[str, Any],
) -> List[Dict[str, Any]]:
    item_id = str(item.get("id", ""))
    relative = str(item.get("path", ""))
    body = _read_text(root, relative)
    if not body:
        metadata = " ".join(
            [
                str(item.get("title", "")),
                str(item.get("summary_zh", "")),
                " ".join(str(value) for value in item.get("tags", [])),
            ]
        ).strip()
        if not metadata:
            return []
        return [
            {
                "chunk_id": _chunk_id(item_id, "metadata", 1, metadata),
                "item_id": item_id,
                "heading_path": ["metadata"],
                "line_start": 1,
                "line_end": 1,
                "text": metadata[:MAX_CHUNK_CHARS],
                "content_sha256": hashlib.sha256(metadata.encode("utf-8")).hexdigest(),
            }
        ]
    lines = body.splitlines()
    heading_stack: List[Tuple[int, str]] = []
    chunks: List[Dict[str, Any]] = []
    buffer: List[str] = []
    start_line = 1

    def flush(end_line: int) -> None:
        nonlocal buffer, start_line
        text = "\n".join(buffer).strip()
        if text:
            heading_path = [value for _, value in heading_stack] or ["document"]
            clipped = text[:MAX_CHUNK_CHARS]
            chunks.append(
                {
                    "chunk_id": _chunk_id(item_id, "/".join(heading_path), start_line, clipped),
                    "item_id": item_id,
                    "heading_path": heading_path,
                    "line_start": start_line,
                    "line_end": max(start_line, end_line),
                    "text": clipped,
                    "content_sha256": hashlib.sha256(clipped.encode("utf-8")).hexdigest(),
                }
            )
        buffer = []

    for index, line in enumerate(lines, 1):
        match = HEADING_RE.match(line)
        if match:
            flush(index - 1)
            level = len(match.group(1))
            heading_stack[:] = [row for row in heading_stack if row[0] < level]
            heading_stack.append((level, match.group(2).strip()))
            start_line = index
            buffer = [line]
        else:
            if not buffer:
                start_line = index
            buffer.append(line)
            if sum(len(value) + 1 for value in buffer) >= MAX_CHUNK_CHARS:
                flush(index)
                start_line = index + 1
        if len(chunks) >= MAX_CHUNKS_PER_ITEM:
            break
    if len(chunks) < MAX_CHUNKS_PER_ITEM:
        flush(len(lines))
    return chunks[:MAX_CHUNKS_PER_ITEM]


def _feature_vector(text: str, dims: int = DEFAULT_DIMS) -> Tuple[float, ...]:
    values = [0.0] * dims
    for token in search_tokens(text):
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        index = int.from_bytes(digest[:4], "big") % dims
        values[index] += 1.0 if digest[4] & 1 else -1.0
    norm = math.sqrt(sum(value * value for value in values))
    return tuple(value / norm for value in values) if norm else tuple(values)


def _vector(text: str, embedding_fn: Optional[EmbeddingFn]) -> Tuple[float, ...]:
    raw = embedding_fn(text) if embedding_fn is not None else _feature_vector(text)
    if isinstance(raw, (str, bytes)) or not isinstance(raw, Sequence):
        raise KnowledgeHubError("embedding provider must return a numeric sequence")
    if not raw or len(raw) > MAX_EMBEDDING_DIMS:
        raise KnowledgeHubError("embedding provider returned invalid dimensions")
    try:
        values = tuple(float(value) for value in raw)
    except (TypeError, ValueError) as exc:
        raise KnowledgeHubError("embedding provider returned non-numeric value") from exc
    if any(not math.isfinite(value) for value in values):
        raise KnowledgeHubError("embedding provider returned non-finite value")
    norm = math.sqrt(sum(value * value for value in values))
    return tuple(value / norm for value in values) if norm else values


def _cosine(left: Sequence[float], right: Sequence[float]) -> float:
    if len(left) != len(right):
        raise KnowledgeHubError("embedding dimensions do not match")
    return sum(a * b for a, b in zip(left, right))


def _lexical_score(query: str, item: Mapping[str, Any], chunks: Sequence[Mapping[str, Any]]) -> float:
    query_tokens = set(search_tokens(query))
    if not query_tokens:
        return 0.0
    text = " ".join(
        [
            str(item.get("id", "")),
            str(item.get("title", "")),
            str(item.get("summary_zh", "")),
            " ".join(str(value) for value in item.get("tags", [])),
            " ".join(str(row.get("text", "")) for row in chunks[:8]),
        ]
    )
    item_tokens = set(search_tokens(text))
    overlap = len(query_tokens.intersection(item_tokens))
    return overlap / max(1, len(query_tokens))


def _authority(item: Mapping[str, Any]) -> float:
    status = str(item.get("status", ""))
    if status == "active" and not item.get("manual_validation_pending", False):
        return 1.0
    return {"active": 0.8, "reviewing": 0.55, "draft": 0.3}.get(status, 0.0)


def _freshness(item: Mapping[str, Any], today: dt.date) -> float:
    updated = _date(item.get("updated_at"), "updated_at")
    if updated is None:
        return 0.5
    age = max(0, (today - updated).days)
    return max(0.25, 1.0 - min(age, 730) / 1000.0)


def route_query(query: str) -> str:
    lowered = query.lower()
    tokens = set(search_tokens(query))
    if IDENTIFIER_RE.search(query):
        return "exact-first"
    if tokens.intersection(TEMPORAL_TERMS) or any(term in lowered for term in TEMPORAL_TERMS):
        return "temporal"
    if tokens.intersection(GRAPH_TERMS) or any(term in lowered for term in GRAPH_TERMS):
        return "graph"
    return "hybrid"


def _dense_scores(
    query: str,
    chunks_by_item: Mapping[str, Sequence[Mapping[str, Any]]],
    embedding_fn: Optional[EmbeddingFn],
) -> Tuple[Dict[str, float], Dict[str, Dict[str, Any]]]:
    query_vector = _vector(query, embedding_fn)
    item_scores: Dict[str, float] = {}
    best_chunks: Dict[str, Dict[str, Any]] = {}
    for item_id, chunks in chunks_by_item.items():
        best_score = 0.0
        best: Optional[Mapping[str, Any]] = None
        for chunk in chunks:
            score = max(0.0, _cosine(query_vector, _vector(str(chunk["text"]), embedding_fn)))
            if score > best_score:
                best_score = score
                best = chunk
        item_scores[item_id] = best_score
        if best is not None:
            best_chunks[item_id] = {key: value for key, value in best.items() if key != "text"}
    return item_scores, best_chunks


def _rank(scores: Mapping[str, float]) -> Dict[str, int]:
    ordered = sorted(scores.items(), key=lambda pair: (-pair[1], pair[0]))
    return {item_id: index for index, (item_id, _) in enumerate(ordered, 1)}


def _rrf(ranks: Sequence[Mapping[str, int]], item_id: str, k: int = 60) -> float:
    return sum(1.0 / (k + rank[item_id]) for rank in ranks if item_id in rank)


def _authorized_items(
    root: pathlib.Path,
    principal: Mapping[str, Any],
    agent_id: str,
    today: dt.date,
) -> Tuple[Dict[str, Any], List[Mapping[str, Any]], int, int]:
    principal_value = principal_context(principal)
    profile = agent_profile(root, agent_id)
    scopes = [str(value) for value in profile.get("knowledge_scopes", [])]
    authorized: List[Mapping[str, Any]] = []
    denied_count = 0
    legacy_acl_count = 0
    for item in registry_items(root):
        if not _temporal_eligible(item, today):
            continue
        decision = authorize_item(item, principal_value, operation="search", agent_scopes=scopes)
        if decision["authorized"]:
            authorized.append(item)
            if not bool(decision.get("acl_explicit", False)):
                legacy_acl_count += 1
        else:
            denied_count += 1
    if len(authorized) > MAX_CORPUS_ITEMS:
        raise KnowledgeHubError("authorized retrieval corpus exceeds explicit budget")
    return principal_value, authorized, denied_count, legacy_acl_count


def _score_lanes(
    root: pathlib.Path,
    query: str,
    authorized: Sequence[Mapping[str, Any]],
    today: dt.date,
    embedding_fn: Optional[EmbeddingFn],
) -> Tuple[
    Dict[str, Sequence[Mapping[str, Any]]],
    Dict[str, float],
    Dict[str, float],
    Dict[str, float],
    Dict[str, float],
    Dict[str, Dict[str, Any]],
]:
    chunks_by_item = {
        str(item["id"]): hierarchical_chunks(root, item)
        for item in authorized
        if item.get("id")
    }
    lexical_scores = {
        str(item["id"]): _lexical_score(query, item, chunks_by_item.get(str(item["id"]), []))
        for item in authorized
        if item.get("id")
    }
    dense_scores, best_chunks = _dense_scores(query, chunks_by_item, embedding_fn)
    authority_scores = {
        str(item["id"]): _authority(item)
        for item in authorized
        if item.get("id")
    }
    freshness_scores = {
        str(item["id"]): _freshness(item, today)
        for item in authorized
        if item.get("id")
    }
    return chunks_by_item, lexical_scores, dense_scores, authority_scores, freshness_scores, best_chunks


def _ranked_rows(
    query: str,
    route: str,
    authorized: Sequence[Mapping[str, Any]],
    lexical_scores: Mapping[str, float],
    dense_scores: Mapping[str, float],
    authority_scores: Mapping[str, float],
    freshness_scores: Mapping[str, float],
    best_chunks: Mapping[str, Mapping[str, Any]],
) -> List[Dict[str, Any]]:
    ranks = [_rank(lexical_scores), _rank(dense_scores), _rank(authority_scores)]
    rows: List[Dict[str, Any]] = []
    for item in authorized:
        item_id = str(item.get("id", ""))
        if not item_id:
            continue
        exact_bonus = 0.2 if route == "exact-first" and item_id.lower() in query.lower() else 0.0
        score = _rrf(ranks, item_id) + 0.12 * authority_scores[item_id] + 0.05 * freshness_scores[item_id] + exact_bonus
        rows.append(
            {
                "id": item_id,
                "title": str(item.get("title", "")),
                "path": str(item.get("path", "")),
                "domain": str(item.get("domain", "")),
                "status": str(item.get("status", "")),
                "trust_class": trust_class(item),
                "score": round(score, 8),
                "score_components": {
                    "lexical": round(lexical_scores.get(item_id, 0.0), 6),
                    "dense": round(dense_scores.get(item_id, 0.0), 6),
                    "authority": round(authority_scores[item_id], 6),
                    "freshness": round(freshness_scores[item_id], 6),
                },
                "best_chunk": dict(best_chunks.get(item_id, {})),
                "derived": True,
                "authoritative": authority_scores[item_id] == 1.0,
            }
        )
    rows.sort(key=lambda row: (-float(row["score"]), str(row["id"])))
    return rows


def _secure_rerank(
    query: str,
    candidates: Sequence[Mapping[str, Any]],
    rerank_fn: RerankFn,
) -> List[Dict[str, Any]]:
    by_id = {str(row.get("id", "")): dict(row) for row in candidates if row.get("id")}
    returned = rerank_fn(query, [dict(row) for row in candidates])
    if isinstance(returned, (str, bytes)) or not isinstance(returned, Sequence):
        raise KnowledgeHubError("reranker must return a sequence")
    result: List[Dict[str, Any]] = []
    seen = set()
    for row in returned:
        if not isinstance(row, Mapping):
            raise KnowledgeHubError("reranker result must contain objects")
        item_id = str(row.get("id", ""))
        if item_id not in by_id:
            raise KnowledgeHubError("reranker attempted to inject unauthorized candidate")
        if item_id in seen:
            continue
        result.append(by_id[item_id])
        seen.add(item_id)
    result.extend(by_id[item_id] for item_id in by_id if item_id not in seen)
    return result


def retrieve_v4(
    root: pathlib.Path,
    query: str,
    principal: Mapping[str, Any],
    *,
    agent_id: str = DEFAULT_AGENT,
    limit: int = 10,
    as_of: str = "",
    embedding_fn: Optional[EmbeddingFn] = None,
    rerank_fn: Optional[RerankFn] = None,
) -> Dict[str, Any]:
    query = str(query or "").strip()
    if not query or len(query) > 4096:
        raise KnowledgeHubError("query must be non-empty and bounded")
    if not 1 <= int(limit) <= 100:
        raise KnowledgeHubError("limit must be between 1 and 100")
    today, source = resolve_today(as_of)
    principal_value, authorized, denied_count, legacy_acl_count = _authorized_items(root, principal, agent_id, today)
    chunks, lexical, dense, authority, freshness, best_chunks = _score_lanes(root, query, authorized, today, embedding_fn)
    route = route_query(query)
    rows = _ranked_rows(query, route, authorized, lexical, dense, authority, freshness, best_chunks)
    selected = rows[: max(limit * 3, limit)]
    if rerank_fn is not None:
        selected = _secure_rerank(query, selected, rerank_fn)
    return {
        "schema_version": "knowledge-hub.retrieval-v4.v1",
        "status": "pass",
        "query_route": route,
        "as_of": today.isoformat(),
        "as_of_source": source,
        "agent_id": agent_id,
        "principal_id": principal_value["principal_id"],
        "results": [dict(row) for row in selected[:limit]],
        "authorized_item_count": len(authorized),
        "denied_item_count": denied_count,
        "legacy_acl_item_count": legacy_acl_count,
        "lane_health": {
            "lexical_nonzero": sum(value > 0 for value in lexical.values()),
            "dense_nonzero": sum(value > 0 for value in dense.values()),
            "chunk_count": sum(len(value) for value in chunks.values()),
            "reranker_enabled": rerank_fn is not None,
            "dense_provider": "external-provider" if embedding_fn is not None else "deterministic-feature-hash-fallback",
        },
        "authority_contract": {
            "ranking_is_authority": False,
            "acl_applied_before_ranking": True,
            "canonical_markdown_registry_remain_authoritative": True,
        },
    }
