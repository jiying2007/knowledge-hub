import json
import shutil

import pytest

from tools.codex_assets.knowledge_hub.common import KnowledgeHubError, repository_root
from tools.codex_assets.knowledge_hub.eval_v2 import (
    compare_baseline,
    migrate_v1_cases,
    validate_case,
)
from tools.codex_assets.knowledge_hub.retrieval_v4 import (
    hierarchical_chunks,
    retrieve_v4,
    route_query,
)


def _root(tmp_path):
    source_root = repository_root()
    (tmp_path / "registry").mkdir(parents=True)
    shutil.copyfile(
        source_root / "registry/knowledge-runtime-v3.json",
        tmp_path / "registry/knowledge-runtime-v3.json",
    )
    items = [
        {
            "id": "allowed-power-loss",
            "title": "Unexpected power loss recovery",
            "summary_zh": "断电后恢复与文件系统重建方法。",
            "tags": ["power-loss", "recovery", "filesystem"],
            "domain": "projects/pcr02",
            "path": "projects/pcr02/power-loss.md",
            "status": "active",
            "updated_at": "2026-09-10",
            "visibility": "team-internal",
            "owner": "alice",
            "acl": ["alice"],
        },
        {
            "id": "denied-secret",
            "title": "Power loss secret recovery",
            "summary_zh": "不应被 alice 看见。",
            "tags": ["power-loss", "secret"],
            "domain": "projects/pcr02",
            "path": "projects/pcr02/secret.md",
            "status": "active",
            "updated_at": "2026-09-10",
            "visibility": "team-internal",
            "owner": "bob",
            "acl": ["bob"],
        },
    ]
    (tmp_path / "registry/items.jsonl").write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in items),
        encoding="utf-8",
    )
    (tmp_path / "registry/sources.json").write_text('{"sources":[]}\n', encoding="utf-8")
    (tmp_path / "registry/retired-sources.jsonl").write_text("", encoding="utf-8")
    project = tmp_path / "projects/pcr02"
    project.mkdir(parents=True)
    (project / "power-loss.md").write_text(
        "# Recovery\n\nUnexpected power loss recovery procedure.\n\n## Filesystem\n\nRebuild metadata after sudden power loss.\n",
        encoding="utf-8",
    )
    (project / "secret.md").write_text(
        "# Secret\n\nPower loss hidden details.\n",
        encoding="utf-8",
    )
    return tmp_path


def _alice():
    return {
        "principal_id": "alice",
        "organization_id": "engineering",
        "groups": ["team:embedded"],
        "scopes": ["projects/pcr02"],
    }


def test_retrieval_v4_filters_acl_before_ranking(tmp_path):
    root = _root(tmp_path)
    result = retrieve_v4(
        root,
        "power loss recovery filesystem",
        _alice(),
        agent_id="embedded-expert",
        as_of="2026-09-12",
        limit=10,
    )
    ids = [row["id"] for row in result["results"]]
    assert ids == ["allowed-power-loss"]
    assert result["denied_item_count"] == 1
    assert result["authority_contract"]["acl_applied_before_ranking"] is True
    assert result["lane_health"]["chunk_count"] >= 1


def test_hierarchical_chunks_keep_heading_and_line_provenance(tmp_path):
    root = _root(tmp_path)
    item = json.loads((root / "registry/items.jsonl").read_text(encoding="utf-8").splitlines()[0])
    chunks = hierarchical_chunks(root, item)
    assert chunks
    assert all(row["line_start"] >= 1 for row in chunks)
    assert all(row["line_end"] >= row["line_start"] for row in chunks)
    assert any("Filesystem" in row["heading_path"] for row in chunks)
    assert all(len(row["content_sha256"]) == 64 for row in chunks)


def test_reranker_cannot_inject_unauthorized_candidate(tmp_path):
    root = _root(tmp_path)

    def malicious_reranker(query, candidates):
        assert candidates
        return [{"id": "denied-secret", "score": 999.0}]

    with pytest.raises(KnowledgeHubError, match="unauthorized"):
        retrieve_v4(
            root,
            "power loss",
            _alice(),
            agent_id="embedded-expert",
            as_of="2026-09-12",
            rerank_fn=malicious_reranker,
        )


def test_embedding_provider_is_bounded_and_finite(tmp_path):
    root = _root(tmp_path)

    def bad_embedding(text):
        return [float("nan"), 1.0]

    with pytest.raises(KnowledgeHubError, match="non-finite"):
        retrieve_v4(
            root,
            "power loss",
            _alice(),
            agent_id="embedded-expert",
            as_of="2026-09-12",
            embedding_fn=bad_embedding,
        )


def test_invalid_temporal_metadata_fails_closed(tmp_path):
    root = _root(tmp_path)
    rows = [json.loads(line) for line in (root / "registry/items.jsonl").read_text(encoding="utf-8").splitlines()]
    rows[0]["valid_from"] = "not-a-date"
    (root / "registry/items.jsonl").write_text(
        "".join(json.dumps(row) + "\n" for row in rows),
        encoding="utf-8",
    )
    with pytest.raises(KnowledgeHubError, match="valid_from"):
        retrieve_v4(
            root,
            "power loss",
            _alice(),
            agent_id="embedded-expert",
            as_of="2026-09-12",
        )


def test_query_router_prefers_exact_temporal_and_graph_modes():
    assert route_query("GD32L235 v1.1.38") == "exact-first"
    assert route_query("历史版本什么时候生效") == "temporal"
    assert route_query("关联依赖关系") == "graph"
    assert route_query("low speed torque optimization") == "hybrid"


def test_eval_v2_migration_and_baseline_regression_contract():
    migrated = migrate_v1_cases(
        {
            "cases": [
                {
                    "id": "case-a",
                    "query": "断电恢复",
                    "expected_ids": ["allowed-power-loss"],
                    "forbidden_ids": ["denied-secret"],
                }
            ]
        }
    )
    assert validate_case(migrated[0]) == []
    assert migrated[0]["language"] == "mixed"
    assert migrated[0]["principal"]["principal_id"] == "eval-user"

    passed = compare_baseline(
        {"pass_rate": 0.98, "p95_ms": 100.0},
        {"pass_rate": 0.99, "p95_ms": 110.0, "critical_failure_ids": []},
    )
    failed = compare_baseline(
        {"pass_rate": 0.98, "p95_ms": 100.0},
        {"pass_rate": 0.90, "p95_ms": 150.0, "critical_failure_ids": ["critical-a"]},
    )
    assert passed["status"] == "pass"
    assert failed["status"] == "fail"
    assert "critical-case-failure" in failed["failures"]
