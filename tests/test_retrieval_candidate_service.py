"""Candidate-service and cross-runtime corpus parity regressions."""

import json
import sqlite3

import pytest

from tools.codex_assets.knowledge_hub.common import KnowledgeHubError
from tools.codex_assets.knowledge_hub import retrieval_candidates as candidates
from tools.codex_assets.knowledge_hub import retrieval_v4 as rv4
from tools.codex_assets.knowledge_hub import runtime_v3 as rv3
from tools.codex_assets.knowledge_hub.search_core import SearchBoundaryError


class FakeIndex:
    CANDIDATE_LIMIT = 4096

    def __init__(self, root):
        self.root = root

    def ensure(self):
        return {"state": "warm", "fresh": True, "signature": "abc"}

    def authority_candidates(self, query):
        return [
            {"item_json": json.dumps({"id": "allowed"})},
            {"item_json": json.dumps({"id": "outside"})},
        ]

    def candidates(self, query, candidate_limit):
        assert candidate_limit == candidates.MAX_LEXICAL_CANDIDATES
        return [
            {"item_json": json.dumps({"id": "allowed"})},
            {"item_json": json.dumps({"id": "second"})},
        ]


def test_fts_candidate_service_never_widens_authorized_set(monkeypatch, tmp_path):
    monkeypatch.setattr(candidates, "SearchIndex", FakeIndex)
    selected, report = candidates.lexical_candidate_set(
        tmp_path, "uart", {"allowed", "second"}
    )
    assert selected == {"allowed", "second"}
    assert report["mode"] == "fts-index"
    assert report["fallback"] is False
    assert report["indexed_candidate_count"] == 4


@pytest.mark.parametrize("error", [OSError("io"), sqlite3.Error("db"), KnowledgeHubError("index")])
def test_normal_index_fault_falls_back_only_to_authorized_ids(monkeypatch, tmp_path, error):
    class Broken(FakeIndex):
        def ensure(self):
            raise error
    monkeypatch.setattr(candidates, "SearchIndex", Broken)
    selected, report = candidates.lexical_candidate_set(tmp_path, "uart", {"a", "b"})
    assert selected == {"a", "b"}
    assert report["mode"] == "authorized-scan-fallback"
    assert report["fallback"] is True


def test_security_resource_boundary_does_not_degrade_to_scan(monkeypatch, tmp_path):
    class Broken(FakeIndex):
        def ensure(self):
            raise SearchBoundaryError("budget")
    monkeypatch.setattr(candidates, "SearchIndex", Broken)
    with pytest.raises(SearchBoundaryError):
        candidates.lexical_candidate_set(tmp_path, "uart", {"a"})


@pytest.mark.parametrize(
    "item, expected",
    [
        ({"path": "projects/a/current/x.md", "status": "active"}, True),
        ({"path": "projects/a/current/x.md", "status": "active", "searchable": False}, False),
        ({"path": "registry/schema.md", "status": "active"}, False),
        ({"path": "registry/schema.md", "status": "active", "searchable": True}, True),
        ({"path": "notes/personal/x.md", "status": "active", "visibility": "personal-local"}, False),
    ],
)
def test_v4_and_runtime_share_default_corpus_eligibility(item, expected):
    today = rv4.dt.date(2026, 9, 25)
    assert rv4._temporal_eligible(item, today) is expected
    assert rv3._eligible(item, today, ()) is expected


def test_feature_hash_path_skips_non_fts_body_reads(monkeypatch, tmp_path):
    seen = []
    def chunks(root, item, cache=None):
        seen.append(item["id"])
        return [{"text": "uart proof", "coverage_complete": True}]
    monkeypatch.setattr(rv4, "hierarchical_chunks", chunks)
    authorized = [
        {"id": "hit", "status": "active"},
        {"id": "miss", "status": "active"},
    ]
    rv4._score_lanes(
        tmp_path, "uart", authorized, rv4.dt.date(2026, 9, 25), None,
        lexical_candidate_ids={"hit"},
    )
    assert seen == ["hit"]


def test_external_semantic_provider_keeps_independent_recall(monkeypatch, tmp_path):
    seen = []
    def chunks(root, item, cache=None):
        seen.append(item["id"])
        return [{"text": item["id"], "coverage_complete": True}]
    monkeypatch.setattr(rv4, "hierarchical_chunks", chunks)
    def embedding(text):
        return [1.0, 0.0]
    authorized = [
        {"id": "fts-hit", "status": "active"},
        {"id": "semantic-only", "status": "active"},
    ]
    _, lexical, dense, _, _, _ = rv4._score_lanes(
        tmp_path, "query", authorized, rv4.dt.date(2026, 9, 25), embedding,
        lexical_candidate_ids={"fts-hit"},
    )
    assert seen == ["fts-hit", "semantic-only"]
    assert lexical["semantic-only"] == 0.0
    assert dense["semantic-only"] > 0.0


def test_empty_authorized_corpus_does_not_open_index(monkeypatch, tmp_path):
    class ShouldNotConstruct:
        def __init__(self, root):
            raise AssertionError("index should not be opened")
    monkeypatch.setattr(candidates, "SearchIndex", ShouldNotConstruct)
    selected, report = candidates.lexical_candidate_set(tmp_path, "uart", set())
    assert selected == set()
    assert report["state"] == "empty-authorized-corpus"


def test_allowed_id_input_is_fail_closed_when_not_a_set(tmp_path):
    with pytest.raises(KnowledgeHubError, match="allowed_ids"):
        candidates.lexical_candidate_set(tmp_path, "uart", ["a"])  # type: ignore[arg-type]
