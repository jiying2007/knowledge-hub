"""Ranking and result-shaping helpers for Knowledge Hub search."""

from __future__ import annotations

import base64
import hashlib
import json
import pathlib
import re
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple
from .common import KnowledgeHubError, compact_json, read_repository_bytes_bounded, source_id
from .schema_subset import validate_contract_subset
from .query_concepts import ConceptQuery, FIELD_VALUES, exact_concept_match
from .query_scope import candidate_concepts
from .query_matching import ConceptMatcher, Match, document_matcher
from .query_focus import focus_bonus
from .search_score_evidence import concept_evidence_score, distinctive_evidence_score, select_distinctive_terms
from .search_ranking import is_historical_result as _historical_result, path_priority as _path_priority, redact_internal_endpoints as _redact_internal_endpoints, status_priority as _status_priority
from .search_core import (
    ARCHIVE_INTENT_TERMS,
    ASCII_TOKEN_PATTERN,
    CJK_PATTERN,
    GENERIC_QUERY_TERMS,
    SEARCH_MAX_CURSOR_CHARS,
    SEARCH_MAX_FILE_BYTES,
    SEARCH_MAX_TOTAL_BYTES,
    SearchBoundaryError,
    SearchFilters,
    _cjk_ngrams,
    _domain_matches,
    _governed_items_by_path,
    _indexed_title,
    _metadata_haystack,
    _physical_sources,
    _registered_text_file_records,
    _source_roots,
    _term_variants,
)

def _term_matches(term: str, haystack: str) -> bool:
    variants = _term_variants(term)
    if any(variant in haystack for variant in variants):
        return True
    for variant in variants:
        cjk = "".join(CJK_PATTERN.findall(variant))
        if len(cjk) < 2:
            continue
        grams = _cjk_ngrams(cjk)
        short = [value for value in grams if len(value) == 2]
        if short and sum(1 for value in short if value in haystack) / float(len(short)) >= 0.5:
            return True
    return False


def _matched_query_terms(
    terms: Sequence[str],
    body: str,
    item: Mapping[str, Any],
    exact: bool = False,
    matcher: Optional[Match] = None,
) -> List[str]:
    """Return query terms matched by a row without exposing matched body text."""

    body = _topic_body(body)
    combined = (_metadata_haystack(item) if item else "") + "\n" + body.lower()
    topical = '\n'.join((str(item.get('title', '')), str(item.get('summary_zh', '')),
                         ' '.join(str(tag) for tag in item.get('tags', [])), body)).lower()
    matcher = matcher or (_concept_matches if exact else _term_matches)
    return [term for term in terms if matcher(term, topical if term in FIELD_VALUES else combined)]


def _concept_matches(term: str, text: str) -> bool:
    return any(exact_concept_match(variant, text, normalized=True) for variant in _term_variants(term))


def _topic_body(body: str) -> str:
    """Exclude YAML property mirrors, preserving physical line numbers for previews."""
    opening = re.match(r'\A(?:\ufeff)?---\r?\n', body)
    if not opening:
        return body
    closing = re.search(r'(?m)^---[ \t]*\r?$(?:\n|\Z)', body[opening.end():])
    if not closing:
        return ''
    end = opening.end() + closing.end()
    return '\n' * body[:end].count('\n') + body[end:]


def _archive_intent(query: str) -> bool:
    lowered = query.lower()
    return any(_term_matches(term, lowered) for term in ARCHIVE_INTENT_TERMS)


def _cursor_fingerprint(query: str, filters: SearchFilters, concept_plan: Optional[ConceptQuery] = None) -> str:
    payload = {
        "query": query,
        'query_policy':'curated-metadata-concepts-v3',
        'concept_plan':concept_plan.__dict__ if concept_plan and (concept_plan.enabled or concept_plan.enforce_constraints) else None,
        "filters": {
            "source": list(filters.sources),
            "owner": list(filters.owners),
            "status": list(filters.statuses),
            "kind": list(filters.kinds),
            "domain": list(filters.domains),
            "source_id": list(filters.source_ids),
        },
    }
    return hashlib.sha256(compact_json(payload).encode("utf-8")).hexdigest()


def _encode_cursor(signature: str, fingerprint: str, offset: int) -> str:
    raw = compact_json(
        {
            "schema_version": 1,
            "signature": signature,
            "fingerprint": fingerprint,
            "offset": offset,
        }
    ).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _decode_cursor(value: str, signature: str, fingerprint: str) -> int:
    if len(value) > SEARCH_MAX_CURSOR_CHARS:
        raise KnowledgeHubError(
            "cursor exceeds {} characters".format(SEARCH_MAX_CURSOR_CHARS)
        )
    try:
        padding = "=" * (-len(value) % 4)
        payload = json.loads(
            base64.b64decode(value + padding, altchars=b"-_", validate=True)
        )
    except (ValueError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise KnowledgeHubError("cursor is invalid") from exc
    if not isinstance(payload, dict) or payload.get("schema_version") != 1:
        raise KnowledgeHubError("cursor is invalid")
    if payload.get("signature") != signature:
        raise KnowledgeHubError("cursor is stale for the current search corpus")
    if payload.get("fingerprint") != fingerprint:
        raise KnowledgeHubError("cursor does not match the query and filters")
    offset = payload.get("offset")
    if isinstance(offset, bool) or not isinstance(offset, int) or offset < 0:
        raise KnowledgeHubError("cursor offset is invalid")
    return offset


def _filters_match(item: Mapping[str, Any], physical_sources: Sequence[str], filters: SearchFilters) -> bool:
    if filters.sources and not set(filters.sources).intersection(physical_sources):
        return False
    if filters.structured and not item:
        return False
    if filters.owners and item.get("owner", "") not in filters.owners:
        return False
    if filters.statuses and item.get("status", "") not in filters.statuses:
        return False
    if filters.normalized_kinds and item.get("kind", "") not in filters.normalized_kinds:
        return False
    if filters.domains and not any(_domain_matches(item.get("domain", ""), prefix) for prefix in filters.domains):
        return False
    if filters.source_ids and source_id(item) not in filters.source_ids:
        return False
    return True


def _filter_reason(item: Mapping[str, Any], physical_sources: Sequence[str], filters: SearchFilters) -> str:
    if filters.sources and not set(filters.sources).intersection(physical_sources):
        return "physical-source"
    if filters.structured and not item:
        return "unregistered-structured-result"
    if filters.owners and item.get("owner", "") not in filters.owners:
        return "owner"
    if filters.statuses and item.get("status", "") not in filters.statuses:
        return "status"
    if filters.normalized_kinds and item.get("kind", "") not in filters.normalized_kinds:
        return "kind"
    if filters.domains and not any(_domain_matches(item.get("domain", ""), prefix) for prefix in filters.domains):
        return "domain"
    if filters.source_ids and source_id(item) not in filters.source_ids:
        return "source-id"
    return ""


def _scan_candidates(root: pathlib.Path) -> List[Dict[str, Any]]:
    items_by_path = _governed_items_by_path(root)
    source_roots = _source_roots(root)
    rows: List[Dict[str, Any]] = []
    total_bytes = 0
    for path, relative, file_stat in _registered_text_file_records(
        root, items_by_path
    ):
        try:
            file_size = file_stat.st_size
            if file_size > SEARCH_MAX_FILE_BYTES:
                raise SearchBoundaryError(
                    "search text file exceeds {} bytes: {}".format(
                        SEARCH_MAX_FILE_BYTES, relative
                    )
                )
            total_bytes += file_size
            if total_bytes > SEARCH_MAX_TOTAL_BYTES:
                raise SearchBoundaryError(
                    "search text corpus exceeds {} bytes".format(
                        SEARCH_MAX_TOTAL_BYTES
                    )
                )
            raw = read_repository_bytes_bounded(
                root,
                relative,
                SEARCH_MAX_FILE_BYTES,
                "search text file",
            )
            body = raw.decode("utf-8", errors="ignore")
        except SearchBoundaryError:
            raise
        except KnowledgeHubError as exc:
            raise SearchBoundaryError(str(exc)) from exc
        except (OSError, ValueError):
            continue
        for item in items_by_path.get(relative, []):
            rows.append(
                {
                    "path": relative,
                    "suffix": path.suffix.lower(),
                    "physical_sources": compact_json(_physical_sources(path, source_roots)),
                    "item_json": compact_json(item),
                    "indexed_title": _indexed_title(relative, body, item),
                    "body": body,
                    "fts_rank": 0.0,
                }
            )
    return rows


def _validate_retrieval_contract(
    root: pathlib.Path,
    payload: Mapping[str, Any],
) -> Dict[str, Any]:
    """Validate the public search contract before a successful return."""

    catalog_path = root / "schemas" / "catalog.json"
    if catalog_path.is_file():
        validation = validate_contract_subset(root, "retrieval-result-v3", payload)
        if validation.get("status") != "pass":
            details = "; ".join(
                "{path}: {message}".format(**row)
                for row in validation.get("errors", [])[:5]
            )
            raise KnowledgeHubError(
                "retrieval result violates retrieval-result-v3: {}".format(details)
            )
        return {
            "status": "pass",
            "contract_id": "retrieval-result-v3",
            "error_count": 0,
        }

    required_payload = {
        "schema_version",
        "status",
        "query",
        "index",
        "results",
        "pagination",
        "search_trace",
        "zero_hit",
        "timing",
    }
    missing_payload = sorted(required_payload - set(payload))
    result_errors: List[str] = []
    for index, result in enumerate(payload.get("results", [])):
        required_result = {"id", "path", "status", "score", "why_selected"}
        missing = sorted(required_result - set(result))
        if missing:
            result_errors.append(
                "results[{}] missing {}".format(index, ", ".join(missing))
            )
    if missing_payload or result_errors:
        fallback_details: List[str] = []
        if missing_payload:
            fallback_details.append(
                "payload missing {}".format(", ".join(missing_payload))
            )
        fallback_details.extend(result_errors[:5])
        raise KnowledgeHubError(
            "retrieval result violates fallback contract: {}".format(
                "; ".join(fallback_details)
            )
        )
    return {
        "status": "pass",
        "contract_id": "retrieval-result-v3-essential-fields",
        "error_count": 0,
    }


def _preview(
    body: str,
    terms: Sequence[str],
    item: Mapping[str, Any],
) -> Tuple[int, str, bool, bool]:
    body = _topic_body(body)
    lower = body.lower()
    positions = [(lower.find(term), term) for term in terms if lower.find(term) >= 0]
    if not positions:
        grams = [gram for term in terms for gram in _cjk_ngrams(term) if len(gram) >= 2]
        positions = [(lower.find(gram), gram) for gram in grams if lower.find(gram) >= 0]
    if not positions:
        summary = item.get("summary_zh") or item.get("title") or item.get("id", "")
        preview, redacted = _redact_internal_endpoints(
            "registry metadata: {}".format(summary)[:240]
        )
        return 1, preview, False, redacted
    index, _ = min(positions, key=lambda value: value[0])
    line_no = lower[:index].count("\n") + 1
    lines = body.splitlines()
    line = lines[line_no - 1].strip()[:240] if lines and line_no <= len(lines) else ""
    preview, redacted = _redact_internal_endpoints(line)
    return line_no, preview, True, redacted


def _score(
    relative: str,
    suffix: str,
    body: str,
    item: Mapping[str, Any],
    indexed_title: str,
    terms: Sequence[str],
    query: str,
    concept_plan: Optional[ConceptQuery] = None,
    query_matcher: Optional[Match] = None,
) -> Optional[Tuple[int, List[str], float]]:
    shared_context = False
    if concept_plan and (concept_plan.enabled or concept_plan.enforce_constraints):
        scoped = candidate_concepts(concept_plan, item)
        if scoped is None:
            return None
        shared_context = bool(concept_plan.project_domains and not scoped.project_domains)
        concept_plan, terms = scoped, scoped.terms
    body = _topic_body(body)
    body_haystack = body.lower()
    natural = bool(concept_plan and concept_plan.enabled)
    matches = document_matcher((query_matcher or ConceptMatcher(terms)) if natural else _term_matches)
    matched_terms = _matched_query_terms(terms, body, item, exact=natural, matcher=matches)
    if not matched_terms:
        return None
    coverage = len(matched_terms) / float(max(1, len(terms)))
    score, path_reason = _path_priority(relative)
    reasons = [path_reason, "query-coverage:{:.2f}".format(coverage)]
    if shared_context:
        reasons.append('shared-policy-comparison')
    score += int(coverage * 180)
    if item:
        status = str(item.get("status", ""))
        score += 300 + _status_priority(status)
        reasons.extend(["registry-backed", "status:{}".format(status)])
    title = (str(item.get("title", "")) if item else indexed_title).lower()
    item_id = str(item.get("id", "")).lower() if item else ""
    path_text = str(item.get("path", relative)).lower() if item else relative.lower()
    summary = str(item.get("summary_zh", "")).lower() if item else ""
    tags = " ".join(str(value).lower() for value in item.get("tags", [])) if item and isinstance(item.get("tags"), list) else ""
    normalized_query = query.lower().strip()
    if normalized_query and normalized_query in title:
        score += 190
        reasons.append("exact-title")
    elif title:
        title_hits = sum(1 for term in terms if matches(term, title))
        score += title_hits * 70
        if title_hits:
            reasons.append("title-tokens")
    if normalized_query and normalized_query in item_id:
        score += 150
        reasons.append("exact-id")
    elif item_id:
        id_hits = sum(1 for term in terms if term not in FIELD_VALUES and matches(term, item_id))
        score += id_hits * 55
        if id_hits:
            reasons.append("id-tokens")
    for field_text, weight, reason in ((tags, 45, "tag-tokens"), (summary, 40, "summary-tokens"), (path_text, 30, "path-tokens")):
        hits = sum(1 for term in terms if (reason != 'path-tokens' or term not in FIELD_VALUES) and matches(term, field_text))
        if hits:
            score += hits * weight
            reasons.append(reason)
    distinctive_terms = select_distinctive_terms(terms)
    if distinctive_terms and normalized_query and normalized_query in summary:
        # A complete question in a curated summary is stronger evidence than
        # a title sharing only CJK ngrams. Generic-only queries gain no bonus.
        summary_token_score = 40 * sum(matches(term, summary) for term in terms)
        score += max(0, min(120, 180 - summary_token_score))
        reasons.append('exact-summary')
    metadata_fields = "\n".join((title, item_id, tags, summary, path_text))
    topic_fields = '\n'.join((title, tags, summary))
    full_document = metadata_fields + '\n' + body_haystack
    topic_document = topic_fields + '\n' + body_haystack
    def evidence_text(term: str) -> str:
        return topic_fields if term in FIELD_VALUES else metadata_fields
    concept_score = concept_evidence_score(concept_plan, natural, terms, matches, full_document,
                                           topic_document, metadata_fields, evidence_text, item)
    if concept_score is None:
        return None
    score += concept_score[0]
    reasons.extend(concept_score[1])
    distinctive_score = distinctive_evidence_score(distinctive_terms, matches, evidence_text, body_haystack,
                                                   normalized_query, topic_fields)
    if distinctive_score is None:
        return None
    score += distinctive_score[0]
    reasons.extend(distinctive_score[1])
    metadata_term_match = any(
        matches(term, evidence_text(term)) for term in terms
    )
    if relative == "README.md" and not metadata_term_match:
        score -= 160
        reasons.append("root-body-only-penalty")
    ascii_distinctive = [
        term
        for term in distinctive_terms
        if ASCII_TOKEN_PATTERN.fullmatch(term) and term not in GENERIC_QUERY_TERMS
        and term not in FIELD_VALUES
    ]
    if len(ascii_distinctive) >= 2 and all(term in path_text for term in ascii_distinctive):
        score += 220
        reasons.append("exact-path-term-set")
    if normalized_query and normalized_query in body_haystack:
        score += 55
        reasons.append("exact-body")
    elif any(matches(term, body_haystack) for term in terms):
        score += 20
        reasons.append("body-tokens")
    if suffix in {".json", ".jsonl"}:
        score -= 55
        reasons.append("structured-ledger-penalty")
    if relative.startswith("artifacts/manifests/"):
        score -= 75
        reasons.append("historical-penalty")
    if relative.startswith("registry/"):
        score -= 110
        reasons.append("registry-noise-penalty")
    source_type = str((item.get("source") or {}).get("type", "")) if item and isinstance(item.get("source"), dict) else ""
    if source_type in {"retired-source-provenance", "artifact-ref"}:
        score -= 35
        reasons.append("provenance-penalty")
    if "project-readiness" in tags or "template-projection" in tags:
        score -= 180
        reasons.append("template-projection-penalty")
    if _historical_result(item, relative) and not _archive_intent(query):
        reasons.append("historical-fallback-lane")
    focus_score, focus_reasons = focus_bonus(query, concept_plan, title)
    return int(score + focus_score), reasons + focus_reasons, coverage
