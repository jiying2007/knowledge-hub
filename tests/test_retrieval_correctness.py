"""#109 F02/F03 regressions against real retrieval entrypoints."""

import hashlib
import json
import shutil

import pytest

from tools.codex_assets.knowledge_hub.common import KnowledgeHubError, repository_root
from tools.codex_assets.knowledge_hub import retrieval_v4 as retrieval
from tools.codex_assets.knowledge_hub.retrieval_chunks import (
    MAX_CHUNK_CHARS, MAX_CHUNKS_PER_ITEM, _split_body, hierarchical_chunks,
)


def _item(item_id="public-note", status="active", **changes):
    row = {
        "id": item_id, "title": item_id, "path": "projects/pcr02/{}.md".format(item_id),
        "domain": "projects/pcr02", "status": status, "updated_at": "2026-09-10",
        "visibility": "team-internal", "owner": "alice", "acl": ["alice"],
    }
    row.update(changes)
    return row


def _root(tmp_path, documents):
    (tmp_path / "registry").mkdir()
    shutil.copyfile(repository_root() / "registry/knowledge-runtime-v3.json", tmp_path / "registry/knowledge-runtime-v3.json")
    (tmp_path / "registry/items.jsonl").write_text(
        "".join(json.dumps(item) + "\n" for item, _ in documents), encoding="utf-8",
    )
    for item, body in documents:
        path = tmp_path / item["path"]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")
    return tmp_path


def _retrieve(root, query, **kwargs):
    return retrieval.retrieve_v4(
        root, query,
        {"principal_id": "alice", "organization_id": "engineering", "groups": ["team:embedded"], "scopes": ["projects/pcr02"]},
        agent_id="embedded-expert", as_of="2026-09-12", **kwargs,
    )


def test_zero_and_negative_scores_do_not_get_rrf_ranks():
    assert retrieval._rank({"zero": 0.0, "negative": -1.0, "hit": 0.1}) == {"hit": 1}


def test_unrelated_active_cannot_outrank_a_relevant_provisional_candidate():
    rows = retrieval._ranked_rows(
        "quasar", "hybrid", [_item("unrelated"), _item("relevant", "draft")],
        {"unrelated": 0.0, "relevant": 1.0}, {"unrelated": 0.0, "relevant": 1.0},
        {"unrelated": 1.0, "relevant": 0.3}, {"unrelated": 1.0, "relevant": 1.0}, {},
    )
    assert [row["id"] for row in rows] == ["relevant"]
    assert rows[0]["authoritative"] is False


@pytest.mark.parametrize("body", [
    "x" * (MAX_CHUNK_CHARS + 1) + "TAIL_EVIDENCE",
    "## Section\r\n中文证据🙂\r\n" * 20,
    "identical " * 2000,
    "\n" * 20 + "  preserve whitespace  \n",
])
def test_lossless_spans_reconstruct_the_exact_original(body):
    chunks = _split_body("doc", body)
    assert "".join(row["text"] for row in chunks) == body
    assert len({row["chunk_id"] for row in chunks}) == len(chunks)
    previous_end = 0
    for row in chunks:
        assert row["source_char_start"] == previous_end
        previous_end = row["source_char_end"]
        assert body[row["source_char_start"]:previous_end] == row["text"]
        assert row["source_content_sha256"] == hashlib.sha256(body.encode("utf-8")).hexdigest()
        assert row["coverage_complete"] is True
        assert row["next_char_offset"] is None
        assert 0 < len(row["text"]) <= MAX_CHUNK_CHARS


def test_mid_line_repeated_content_has_distinct_chunk_ids_and_correct_lines():
    chunks = _split_body("doc", "z" * (MAX_CHUNK_CHARS * 3))
    assert len(chunks) == 3
    assert len({row["chunk_id"] for row in chunks}) == 3
    assert all(row["line_start"] == row["line_end"] == 1 for row in chunks)


def test_heading_inside_a_code_fence_is_not_document_structure():
    body = "# Real\n```python\n# Not a heading\nprint(1)\n```\n## Next\nproof\n"
    chunks = _split_body("doc", body)
    assert "".join(row["text"] for row in chunks) == body
    assert all("Not a heading" not in row["heading_path"] for row in chunks)
    assert any(row["heading_path"] == ["Real", "Next"] for row in chunks)


def test_chunk_budget_reports_incomplete_coverage_and_resume_offset():
    body = "x" * (MAX_CHUNK_CHARS * MAX_CHUNKS_PER_ITEM + 1)
    chunks = _split_body("doc", body)
    assert len(chunks) == MAX_CHUNKS_PER_ITEM
    assert all(row["coverage_complete"] is False for row in chunks)
    assert chunks[-1]["next_char_offset"] == MAX_CHUNK_CHARS * MAX_CHUNKS_PER_ITEM
    assert chunks[-1]["source_char_count"] == len(body)


def test_lexical_lane_reads_evidence_after_the_eighth_chunk():
    body = "".join("# Part {}\nordinary filler\n".format(i) for i in range(10)) + "# Tail\nquasar-proof\n"
    chunks = _split_body("doc", body)
    assert len(chunks) > 8
    score, best = retrieval._lexical_lane("quasar-proof", _item(), chunks)
    assert score == 1.0
    assert best["heading_path"] == ["Tail"]


def test_reranker_cannot_mutate_nested_source_evidence():
    original = [{"id": "doc", "best_chunk": {"content_sha256": "a" * 64}}]
    def malicious(query, rows):
        rows[0]["best_chunk"]["content_sha256"] = "forged"
        return rows
    result = retrieval._secure_rerank("proof", original, malicious)
    assert result == original
    assert result[0]["best_chunk"]["content_sha256"] == "a" * 64


def test_no_answer_is_empty_even_when_feature_hashes_collide(tmp_path):
    token = "knownword"
    digest = hashlib.sha256(token.encode()).digest()
    key = (int.from_bytes(digest[:4], "big") % retrieval.DEFAULT_DIMS, digest[4] & 1)
    collision = next(
        "absent{}".format(i) for i in range(20000)
        if (lambda d: (int.from_bytes(d[:4], "big") % retrieval.DEFAULT_DIMS, d[4] & 1))(
            hashlib.sha256("absent{}".format(i).encode()).digest()
        ) == key
    )
    root = _root(tmp_path, [(_item(), token)])
    result = _retrieve(root, collision)
    assert result["results"] == []
    assert result["answerability"] == "no-match"
    assert result["lane_health"]["independent_semantic_recall"] is False


def test_real_provider_retains_independent_semantic_recall(tmp_path):
    root = _root(tmp_path, [(_item(), "knownword")])
    result = _retrieve(root, "unmatchedquery", embedding_fn=lambda text: [1.0, 0.0])
    assert result["lane_health"]["lexical_nonzero"] == 0
    assert result["lane_health"]["independent_semantic_recall"] is True
    assert [row["id"] for row in result["results"]] == ["public-note"]


def test_only_provisional_evidence_is_not_presented_as_active(tmp_path):
    root = _root(tmp_path, [(_item(status="draft"), "quasar-proof")])
    result = _retrieve(root, "quasar-proof")
    assert result["answerability"] == "provisional-only"
    assert result["results"][0]["authoritative"] is False


def test_incomplete_corpus_cannot_claim_a_complete_no_answer(tmp_path):
    body = "x" * (MAX_CHUNK_CHARS * MAX_CHUNKS_PER_ITEM + 1)
    root = _root(tmp_path, [(_item(), body)])
    result = _retrieve(root, "unmatchedquery")
    assert result["status"] == "needs-review"
    assert result["answerability"] == "incomplete-corpus"
    assert result["retrieval_coverage"] == {"complete": False, "truncated_item_count": 1}


def test_global_chunk_budget_fails_closed(tmp_path, monkeypatch):
    root = _root(tmp_path, [(_item(), "# First\none\n# Second\ntwo\n")])
    monkeypatch.setattr(retrieval, "MAX_TOTAL_CHUNKS", 1)
    with pytest.raises(KnowledgeHubError, match="budget"):
        _retrieve(root, "one")


def test_denied_body_is_not_read_or_sent_to_embedding(tmp_path):
    denied = _item("denied", owner="bob", acl=["bob"])
    root = _root(tmp_path, [(_item(), "public proof"), (denied, "private proof")])
    (root / denied["path"]).unlink()
    observed = []
    def embedding(text):
        observed.append(text)
        return [1.0, 0.0]
    result = _retrieve(root, "proof", embedding_fn=embedding)
    assert result["denied_item_count"] == 1
    assert not any("private" in text for text in observed)


def test_source_path_cannot_escape_through_a_symlink(tmp_path):
    target = tmp_path / "target.md"
    target.write_text("private", encoding="utf-8")
    (tmp_path / "link.md").symlink_to(target)
    with pytest.raises(KnowledgeHubError):
        hierarchical_chunks(tmp_path, _item(path="link.md"))


def test_huge_finite_embedding_is_normalized_without_overflow():
    vector = retrieval._vector("proof", lambda text: [1e308, 1e308])
    assert sum(value * value for value in vector) == pytest.approx(1.0)
