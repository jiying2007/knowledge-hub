"""ACL-first multi-lane retrieval; relevance never grants authority."""

from __future__ import annotations

import copy
import datetime as dt
import hashlib
import math
import pathlib
import re
from typing import Any, Callable, Dict, List, Mapping, Optional, Sequence, Tuple

from .common import KnowledgeHubError, registry_items, resolve_today
from .retrieval_cache import DerivedCache, fingerprint
from .retrieval_candidates import lexical_candidate_set
from .retrieval_chunks import hierarchical_chunks
from .runtime_p5_security import authorize_item, principal_context, trust_class
from .runtime_v3_contracts import DEFAULT_AGENT, agent_profile
from .search_core import _item_is_default_searchable, search_tokens

MAX_CORPUS_ITEMS = 5000
MAX_CORPUS_CHARS = 32 * 1024 * 1024
MAX_TOTAL_CHUNKS = 8192
MAX_EMBEDDING_DIMS = 4096
DEFAULT_DIMS = 256
IDENTIFIER_RE = re.compile(r"(?:[A-Za-z]+[_./:-]\w+|\bv?\d+\.\d+(?:\.\d+)?\b)")
TEMPORAL_TERMS = {"when", "timeline", "history", "historical", "当前", "历史", "何时", "版本"}
GRAPH_TERMS = {"related", "depends", "relation", "关联", "依赖", "关系"}
EmbeddingFn = Callable[[str], Sequence[float]]
RerankFn = Callable[[str, Sequence[Mapping[str, Any]]], Any]


def _date(value: Any, label: str) -> Optional[dt.date]:
    if value in (None, ""):
        return None
    try:
        return dt.date.fromisoformat(str(value))
    except ValueError as exc:
        raise KnowledgeHubError("{} must use YYYY-MM-DD".format(label)) from exc


def _temporal_eligible(item: Mapping[str, Any], today: dt.date) -> bool:
    if not _item_is_default_searchable(item):
        return False
    valid_from = _date(item.get("valid_from"), "valid_from")
    valid_to = _date(item.get("valid_to"), "valid_to")
    if valid_from and valid_to and valid_from > valid_to:
        raise KnowledgeHubError("valid_from must not exceed valid_to")
    if valid_from and today < valid_from:
        return False
    if valid_to and today > valid_to:
        return False
    return str(item.get("status", "")) in {"active", "reviewing", "draft"}


def _feature_vector(text: str, dims: int = DEFAULT_DIMS) -> Tuple[float, ...]:
    values = [0.0] * dims
    for token in search_tokens(text):
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        index = int.from_bytes(digest[:4], "big") % dims
        values[index] += 1.0 if digest[4] & 1 else -1.0
    norm = math.sqrt(sum(value * value for value in values))
    return tuple(value / norm for value in values) if norm else tuple(values)


def _vector(text: str, embedding_fn: Optional[EmbeddingFn]) -> Tuple[float, ...]:
    raw: Any = embedding_fn(text) if embedding_fn is not None else _feature_vector(text)
    if isinstance(raw, (str, bytes)) or not isinstance(raw, Sequence):
        raise KnowledgeHubError("embedding provider must return a numeric sequence")
    if not raw or len(raw) > MAX_EMBEDDING_DIMS:
        raise KnowledgeHubError("embedding provider returned invalid dimensions")
    try:
        values = tuple(float(value) for value in raw)
    except (TypeError, ValueError, OverflowError) as exc:
        raise KnowledgeHubError("embedding provider returned non-numeric value") from exc
    if any(not math.isfinite(value) for value in values):
        raise KnowledgeHubError("embedding provider returned non-finite value")
    scale = max(abs(value) for value in values)
    scaled = tuple(value / scale for value in values) if scale else values
    norm = math.sqrt(sum(value * value for value in scaled))
    return tuple(value / norm for value in scaled) if norm else scaled


def _embedding_binding(embedding_fn: Optional[EmbeddingFn], identity: Any) -> Tuple[str, int]:
    if embedding_fn is None:
        if identity is not None:
            raise KnowledgeHubError("embedding identity requires an external provider")
        return fingerprint(["feature-hash-v1", "search-tokens-v1", DEFAULT_DIMS]), DEFAULT_DIMS
    if identity is None:
        return "", 0  # An anonymous callable cannot be persistently identified.
    if not isinstance(identity, Mapping):
        raise KnowledgeHubError("embedding identity must be an object")
    fields = ("provider", "model", "revision", "preprocessing")
    if any(not isinstance(identity.get(k), str) or not identity[k].strip() or len(identity[k]) > 256 for k in fields):
        raise KnowledgeHubError("embedding identity requires provider/model/revision/preprocessing")
    dims = identity.get("dimensions")
    if type(dims) is not int or not 1 <= dims <= MAX_EMBEDDING_DIMS:
        raise KnowledgeHubError("embedding identity requires bounded dimensions")
    return fingerprint(["normalized-vector-v1", [identity[k] for k in fields], dims]), dims


def _valid_vector(value: Any, dims: int) -> bool:
    if not isinstance(value, (list, tuple)) or len(value) != dims:
        return False
    if any(type(v) not in (int, float) or not math.isfinite(v) or abs(v) > 1 for v in value):
        return False
    norm = sum(v * v for v in value)
    return norm == 0 or abs(norm - 1) < 1e-8


def _cosine(left: Sequence[float], right: Sequence[float]) -> float:
    if len(left) != len(right):
        raise KnowledgeHubError("embedding dimensions do not match")
    return sum(a * b for a, b in zip(left, right))


def _lexical_lane(
    query: str, item: Mapping[str, Any], chunks: Sequence[Mapping[str, Any]],
) -> Tuple[float, Dict[str, Any]]:
    tokens = set(search_tokens(query))
    if not tokens:
        return 0.0, {}
    metadata = " ".join([
        str(item.get("id", "")), str(item.get("title", "")),
        str(item.get("summary_zh", "")), " ".join(map(str, item.get("tags", []))),
    ])
    matched = tokens.intersection(search_tokens(metadata))
    best: Dict[str, Any] = {}
    best_count = 0
    for chunk in chunks:
        hits = tokens.intersection(search_tokens(str(chunk["text"])))
        matched.update(hits)
        if len(hits) > best_count:
            best_count = len(hits)
            best = {key: value for key, value in chunk.items() if key != "text"}
    return len(matched) / len(tokens), best


def _authority(item: Mapping[str, Any]) -> float:
    status = str(item.get("status", ""))
    if status == "active" and not item.get("manual_validation_pending", False):
        return 1.0
    return {"active": 0.8, "reviewing": 0.55, "draft": 0.3}.get(status, 0.0)


def _freshness(item: Mapping[str, Any], today: dt.date) -> float:
    updated = _date(item.get("updated_at"), "updated_at")
    if updated is None:
        return 0.5
    return max(0.25, 1.0 - min(max(0, (today - updated).days), 730) / 1000.0)


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
    query: str, chunks_by_item: Mapping[str, Sequence[Mapping[str, Any]]],
    embedding_fn: Optional[EmbeddingFn], *, cache: Optional[DerivedCache] = None,
    binding: Tuple[str, int] = ("", 0), query_vector: Optional[Sequence[float]] = None,
) -> Tuple[Dict[str, float], Dict[str, Dict[str, Any]]]:
    if not chunks_by_item:
        return {}, {}
    if query_vector is None:
        query_vector = _vector(query, embedding_fn)
    if binding[1] and len(query_vector) != binding[1]:
        raise KnowledgeHubError("embedding identity dimensions do not match provider")
    scores: Dict[str, float] = {}
    best_chunks: Dict[str, Dict[str, Any]] = {}
    for item_id, chunks in chunks_by_item.items():
        best_score = 0.0
        best: Optional[Mapping[str, Any]] = None
        for chunk in chunks:
            text = str(chunk["text"])
            if cache is not None and binding[0]:
                vector = cache.resolve(
                    "vectors", fingerprint([binding[0], hashlib.sha256(text.encode("utf-8")).hexdigest()]),
                    binding[0], lambda text=text: _vector(text, embedding_fn),
                    lambda value: _valid_vector(value, binding[1]),
                )
            else:
                vector = _vector(text, embedding_fn)
            score = max(0.0, _cosine(query_vector, vector))
            if score > best_score:
                best_score, best = score, chunk
        scores[item_id] = best_score
        if best is not None:
            best_chunks[item_id] = {key: value for key, value in best.items() if key != "text"}
    return scores, best_chunks


def _rank(scores: Mapping[str, float]) -> Dict[str, int]:
    # These are normalized positive overlap/cosine lanes, not raw BM25 scores.
    ordered = sorted(
        ((key, value) for key, value in scores.items() if math.isfinite(value) and value > 0),
        key=lambda pair: (-pair[1], pair[0]),
    )
    return {item_id: index for index, (item_id, _) in enumerate(ordered, 1)}


def _rrf(ranks: Sequence[Mapping[str, int]], item_id: str, k: int = 60) -> float:
    return sum(1.0 / (k + row[item_id]) for row in ranks if item_id in row)


def _authorized_items(
    root: pathlib.Path, principal: Mapping[str, Any], agent_id: str, today: dt.date,
) -> Tuple[Dict[str, Any], List[Mapping[str, Any]], int, int]:
    principal_value = principal_context(principal)
    scopes = [str(value) for value in agent_profile(root, agent_id).get("knowledge_scopes", [])]
    authorized: List[Mapping[str, Any]] = []
    denied = legacy = 0
    for item in registry_items(root):
        if not _temporal_eligible(item, today):
            continue
        decision = authorize_item(item, principal_value, operation="search", agent_scopes=scopes)
        if not decision["authorized"]:
            denied += 1
            continue
        authorized.append(item)
        legacy += 0 if decision.get("acl_explicit", False) else 1
        if len(authorized) > MAX_CORPUS_ITEMS:
            raise KnowledgeHubError("authorized retrieval corpus exceeds explicit budget")
    return principal_value, authorized, denied, legacy


def _score_lanes(
    root: pathlib.Path, query: str, authorized: Sequence[Mapping[str, Any]],
    today: dt.date, embedding_fn: Optional[EmbeddingFn], *,
    cache: Optional[DerivedCache] = None, binding: Tuple[str, int] = ("", 0),
    lexical_candidate_ids: Optional[Set[str]] = None,
) -> Tuple[
    Dict[str, List[Dict[str, Any]]], Dict[str, float], Dict[str, float],
    Dict[str, float], Dict[str, float], Dict[str, Dict[str, Any]],
]:
    chunks: Dict[str, List[Dict[str, Any]]] = {}
    lexical: Dict[str, float] = {}
    dense: Dict[str, float] = {}
    best: Dict[str, Dict[str, Any]] = {}
    total_chars = total_chunks = 0
    query_vector = None
    for item in authorized:
        item_id = str(item.get("id", ""))
        if not item_id or item_id in chunks:
            raise KnowledgeHubError("retrieval corpus must have unique non-empty item IDs")
        lexical_candidate = (
            lexical_candidate_ids is None or item_id in lexical_candidate_ids
        )
        if embedding_fn is None and not lexical_candidate:
            chunks[item_id] = []
            lexical[item_id] = 0.0
            dense[item_id] = 0.0
            best[item_id] = {}
            continue
        item_chunks = hierarchical_chunks(root, item, cache=cache)
        total_chars += sum(len(row["text"]) for row in item_chunks)
        total_chunks += len(item_chunks)
        if total_chars > MAX_CORPUS_CHARS or total_chunks > MAX_TOTAL_CHUNKS:
            raise KnowledgeHubError("retrieval corpus exceeds chunk/character budget")
        if lexical_candidate:
            lexical[item_id], best[item_id] = _lexical_lane(query, item, item_chunks)
        else:
            lexical[item_id], best[item_id] = 0.0, {}
        # Keep independent external semantic recall; feature hashes only refine
        # lexical hits. Retain span metadata, not the entire corpus body.
        if embedding_fn is not None or lexical[item_id] > 0:
            if query_vector is None:
                query_vector = _vector(query, embedding_fn)
            item_scores, dense_best = _dense_scores(
                query, {item_id: item_chunks}, embedding_fn, cache=cache,
                binding=binding, query_vector=query_vector,
            )
            dense.update(item_scores)
            if item_id in dense_best and (embedding_fn is not None or not best[item_id]):
                best[item_id] = dense_best[item_id]
        chunks[item_id] = [{k: v for k, v in row.items() if k != "text"} for row in item_chunks]
    authority = {str(item["id"]): _authority(item) for item in authorized}
    freshness = {str(item["id"]): _freshness(item, today) for item in authorized}
    return chunks, lexical, dense, authority, freshness, best


def _ranked_rows(
    query: str, route: str, authorized: Sequence[Mapping[str, Any]],
    lexical: Mapping[str, float], dense: Mapping[str, float],
    authority: Mapping[str, float], freshness: Mapping[str, float],
    best_chunks: Mapping[str, Mapping[str, Any]],
) -> List[Dict[str, Any]]:
    ranks = [_rank(lexical), _rank(dense)]
    candidates = set(ranks[0]) | set(ranks[1])
    rows: List[Dict[str, Any]] = []
    for item in authorized:
        item_id = str(item.get("id", ""))
        if item_id not in candidates:
            continue
        exact_match = re.search(r"(?<!\w)" + re.escape(item_id) + r"(?!\w)", query, re.IGNORECASE)
        exact = 0.2 if route == "exact-first" and exact_match else 0.0
        relevance = _rrf(ranks, item_id)
        score = relevance * (1 + 0.12 * authority[item_id] + 0.05 * freshness[item_id]) + exact
        rows.append({
            "id": item_id, "title": str(item.get("title", "")), "path": str(item.get("path", "")),
            "domain": str(item.get("domain", "")), "status": str(item.get("status", "")),
            "trust_class": trust_class(item), "score": round(score, 8),
            "score_components": {
                "lexical": round(lexical.get(item_id, 0.0), 6), "dense": round(dense.get(item_id, 0.0), 6),
                "authority": round(authority[item_id], 6), "freshness": round(freshness[item_id], 6),
            },
            "best_chunk": dict(best_chunks.get(item_id, {})), "derived": True,
            "authoritative": authority[item_id] == 1.0,
        })
    rows.sort(key=lambda row: (-float(row["score"]), str(row["id"])))
    return rows


def _secure_rerank(
    query: str, candidates: Sequence[Mapping[str, Any]], rerank_fn: RerankFn,
) -> List[Dict[str, Any]]:
    by_id = {str(row.get("id", "")): copy.deepcopy(dict(row)) for row in candidates if row.get("id")}
    returned: Any = rerank_fn(query, copy.deepcopy(list(candidates)))
    if isinstance(returned, (str, bytes)) or not isinstance(returned, Sequence):
        raise KnowledgeHubError("reranker must return a sequence")
    if len(returned) > len(candidates):
        raise KnowledgeHubError("reranker exceeded candidate budget")
    result: List[Dict[str, Any]] = []
    seen = set()
    for row in returned:
        if not isinstance(row, Mapping):
            raise KnowledgeHubError("reranker result must contain objects")
        item_id = str(row.get("id", ""))
        if item_id not in by_id:
            raise KnowledgeHubError("reranker attempted to inject unauthorized candidate")
        if item_id not in seen:
            result.append(by_id[item_id])
            seen.add(item_id)
    result.extend(by_id[item_id] for item_id in by_id if item_id not in seen)
    return result


def retrieve_v4(
    root: pathlib.Path, query: str, principal: Mapping[str, Any], *,
    agent_id: str = DEFAULT_AGENT, limit: int = 10, as_of: str = "",
    embedding_fn: Optional[EmbeddingFn] = None, rerank_fn: Optional[RerankFn] = None,
    embedding_identity: Optional[Mapping[str, Any]] = None, cache_enabled: bool = True,
) -> Dict[str, Any]:
    if not isinstance(query, str) or not query.strip() or len(query) > 4096:
        raise KnowledgeHubError("query must be non-empty and bounded")
    query = query.strip()
    if type(limit) is not int or not 1 <= limit <= 100:
        raise KnowledgeHubError("limit must be between 1 and 100")
    if type(cache_enabled) is not bool:
        raise KnowledgeHubError("cache_enabled must be a boolean")
    binding = _embedding_binding(embedding_fn, embedding_identity)
    today, source = resolve_today(as_of)
    principal_value, authorized, denied, legacy = _authorized_items(root, principal, agent_id, today)
    lexical_ids, candidate_service = lexical_candidate_set(
        root,
        query,
        {str(item.get("id", "")) for item in authorized if item.get("id")},
    )
    with DerivedCache(root, enabled=cache_enabled and bool(authorized)) as cache:
        chunks, lexical, dense, authority, freshness, best = _score_lanes(
            root, query, authorized, today, embedding_fn, cache=cache, binding=binding,
            lexical_candidate_ids=lexical_ids,
        )
    route = route_query(query)
    rows = _ranked_rows(query, route, authorized, lexical, dense, authority, freshness, best)
    selected = rows[: max(limit * 3, limit)]
    if rerank_fn is not None and selected:
        selected = _secure_rerank(query, selected, rerank_fn)
    results = [dict(row) for row in selected[:limit]]
    truncated = sum(bool(rows) and not rows[-1]["coverage_complete"] for rows in chunks.values())
    answerability = "no-match" if not results else (
        "evidence-match" if any(row["authoritative"] for row in results) else "provisional-only"
    )
    return {
        "schema_version": "knowledge-hub.retrieval-v4.v1", "status": "needs-review" if truncated else "pass",
        "query_route": route, "answerability": "incomplete-corpus" if truncated else answerability,
        "as_of": today.isoformat(), "as_of_source": source, "agent_id": agent_id,
        "principal_id": principal_value["principal_id"], "results": results,
        "authorized_item_count": len(authorized), "denied_item_count": denied, "legacy_acl_item_count": legacy,
        "retrieval_coverage": {"complete": not truncated, "truncated_item_count": truncated},
        "derived_cache": dict(cache.stats, document_vector_cache_identified=bool(binding[0])),
        "candidate_service": candidate_service,
        "lane_health": {
            "lexical_nonzero": sum(value > 0 for value in lexical.values()),
            "dense_nonzero": sum(value > 0 for value in dense.values()),
            "chunk_count": sum(len(value) for value in chunks.values()),
            "reranker_enabled": rerank_fn is not None,
            "dense_provider": "external-provider" if embedding_fn is not None else "deterministic-feature-hash-fallback",
            "independent_semantic_recall": embedding_fn is not None,
        },
        "authority_contract": {
            "ranking_is_authority": False, "acl_applied_before_ranking": True,
            "canonical_markdown_registry_remain_authoritative": True,
        },
    }
