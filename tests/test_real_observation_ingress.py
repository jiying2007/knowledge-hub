import base64
import json
import pytest

from tools.codex_assets.knowledge_hub.common import KnowledgeHubError, repository_root
from tools.codex_assets.knowledge_hub.observation_source_readiness import (
    build_observation_source_readiness,
)
from tools.codex_assets.knowledge_hub import real_observation_ingress_cli as ingress


GIT_SHA = "e" * 40


def _encoded(payload):
    return base64.b64encode(
        json.dumps(payload, sort_keys=True).encode("utf-8")
    ).decode("ascii")


def test_ingress_preserves_exact_observation_and_binds_policy(monkeypatch, tmp_path):
    registry = tmp_path / "registry"
    workflow = tmp_path / ".github/workflows"
    registry.mkdir(parents=True)
    workflow.mkdir(parents=True)
    registered = ".github/workflows/real-observation-test.yml"
    (tmp_path / registered).write_text("name: test\n", encoding="utf-8")
    (registry / "ai-operations-policy.json").write_text(
        json.dumps(
            {
                "external_evidence": {
                    "supported_gaps": ["production-retrieval-eval"],
                    "observation_contracts": {
                        "production-retrieval-eval": "production-retrieval-observation-v1"
                    },
                    "observation_source_workflow_prefix": ".github/workflows/real-observation-",
                    "observation_source_workflow_allowlist": {
                        "production-retrieval-eval": [registered]
                    },
                }
            }
        ),
        encoding="utf-8",
    )
    payload = {
        "schema_version": "example",
        "gap_id": "production-retrieval-eval",
        "source_revision": GIT_SHA,
        "observed_at": "2026-09-26T00:00:00Z",
    }
    calls = []

    def validate(root, contract_id, value):
        calls.append(("schema", contract_id, dict(value)))
        return {"status": "pass", "errors": []}

    def project(value, *, expected_gap):
        calls.append(("semantic", expected_gap, dict(value)))
        return {"gap_id": expected_gap}

    monkeypatch.setattr(ingress, "validate_instance", validate)
    monkeypatch.setattr(ingress, "build_pilot_evidence", project)

    observed, receipt = ingress.prepare_real_observation(
        tmp_path,
        encoded=_encoded(payload),
        expected_gap="production-retrieval-eval",
        source_revision=GIT_SHA,
    )

    assert observed == payload
    assert receipt["status"] == "pass"
    assert receipt["contract_id"] == "production-retrieval-observation-v1"
    assert receipt["source_workflow_path"] == registered
    assert receipt["canonical_write_performed"] is False
    assert receipt["raw_observation_logged"] is False
    assert calls[0][0] == "schema"
    assert calls[1][0] == "semantic"


@pytest.mark.parametrize(
    "encoded,error",
    [
        ("", "not configured"),
        ("not-base64", "invalid base64"),
        (_encoded([]), "must be an object"),
    ],
)
def test_ingress_rejects_missing_or_malformed_secret(encoded, error):
    with pytest.raises(KnowledgeHubError, match=error):
        ingress._decode_observation(encoded)


def test_ingress_rejects_gap_or_revision_relabel(monkeypatch, tmp_path):
    registry = tmp_path / "registry"
    workflow = tmp_path / ".github/workflows"
    registry.mkdir(parents=True)
    workflow.mkdir(parents=True)
    registered = ".github/workflows/real-observation-test.yml"
    (tmp_path / registered).write_text("name: test\n", encoding="utf-8")
    (registry / "ai-operations-policy.json").write_text(
        json.dumps(
            {
                "external_evidence": {
                    "supported_gaps": ["memory-lifecycle-pilot"],
                    "observation_contracts": {
                        "memory-lifecycle-pilot": "production-memory-observation-v1"
                    },
                    "observation_source_workflow_prefix": ".github/workflows/real-observation-",
                    "observation_source_workflow_allowlist": {
                        "memory-lifecycle-pilot": [registered]
                    },
                }
            }
        ),
        encoding="utf-8",
    )
    wrong_gap = {
        "gap_id": "real-adoption-evidence",
        "source_revision": GIT_SHA,
    }
    with pytest.raises(KnowledgeHubError, match="gap does not match"):
        ingress.prepare_real_observation(
            tmp_path,
            encoded=_encoded(wrong_gap),
            expected_gap="memory-lifecycle-pilot",
            source_revision=GIT_SHA,
        )

    wrong_revision = {
        "gap_id": "memory-lifecycle-pilot",
        "source_revision": "a" * 40,
    }
    with pytest.raises(KnowledgeHubError, match="source revision does not match"):
        ingress.prepare_real_observation(
            tmp_path,
            encoded=_encoded(wrong_revision),
            expected_gap="memory-lifecycle-pilot",
            source_revision=GIT_SHA,
        )


def test_ingress_rejects_invalid_or_unregistered_policy(tmp_path):
    registry = tmp_path / "registry"
    registry.mkdir()
    (registry / "ai-operations-policy.json").write_text(
        json.dumps(
            {
                "external_evidence": {
                    "supported_gaps": ["real-adoption-evidence"],
                    "observation_contracts": {
                        "real-adoption-evidence": "production-adoption-observation-v1"
                    },
                    "observation_source_workflow_prefix": ".github/workflows/real-observation-",
                    "observation_source_workflow_allowlist": {
                        "real-adoption-evidence": []
                    },
                }
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(KnowledgeHubError, match="exactly one registered workflow"):
        ingress._contract_for_gap(tmp_path, "real-adoption-evidence")


def test_current_policy_registers_every_open_real_observation_source():
    report = build_observation_source_readiness(repository_root())

    assert report["status"] == "ready-for-observation"
    assert report["unregistered_count"] == 0
    assert report["registered_open_count"] == 4
    assert all(row["status"] == "registered" for row in report["rows"])
    assert all(
        row["next_action"] == "produce-real-observation"
        for row in report["rows"]
    )


def test_registered_workflows_are_dispatch_only_secret_bound_and_fail_closed():
    root = repository_root()
    policy = json.loads(
        (root / "registry/ai-operations-policy.json").read_text(encoding="utf-8")
    )
    allowlists = policy["external_evidence"]["observation_source_workflow_allowlist"]
    expected_secrets = {
        "connector-provider-pilot": "KNOWLEDGE_REAL_OBSERVATION_CONNECTOR_B64",
        "production-retrieval-eval": "KNOWLEDGE_REAL_OBSERVATION_RETRIEVAL_B64",
        "memory-lifecycle-pilot": "KNOWLEDGE_REAL_OBSERVATION_MEMORY_B64",
        "real-adoption-evidence": "KNOWLEDGE_REAL_OBSERVATION_ADOPTION_B64",
    }

    for gap, expected_secret in expected_secrets.items():
        paths = allowlists[gap]
        assert len(paths) == 1
        path = root / paths[0]
        assert path.is_file()
        text = path.read_text(encoding="utf-8")
        assert "workflow_dispatch:" in text
        assert "\n  schedule:" not in text
        assert "\n  push:" not in text
        assert "\n  pull_request:" not in text
        assert 'test "${GITHUB_REF}" = "refs/heads/master"' in text
        assert "ref: ${{ github.sha }}" in text
        assert "persist-credentials: false" in text
        assert "real_observation_ingress_cli" in text
        assert expected_secret in text
        assert text.count("secrets.") == 1
        assert "git diff --exit-code -- registry/knowledge-platform-p5-p10.json registry/items.jsonl" in text
        assert "actions/upload-artifact@043fb46d1a93c77aae656e7c1c64a875d1fc6a0a" in text
