from __future__ import annotations

import json

import pytest

from tools.codex_assets.knowledge_hub.common import KnowledgeHubError
from tools.codex_assets.knowledge_hub.quality_evidence_binding import (
    QUALITY_EVIDENCE_PATHS,
    build_quality_evidence_binding,
    verify_quality_evidence_binding,
)


def _write_evidence(tmp_path):
    for index, relative in enumerate(QUALITY_EVIDENCE_PATHS, 1):
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"index": index}) + "\n", encoding="utf-8")


def test_quality_evidence_binding_round_trip(tmp_path):
    _write_evidence(tmp_path)
    binding = build_quality_evidence_binding(
        tmp_path,
        source_revision="a" * 40,
    )

    verified = verify_quality_evidence_binding(
        tmp_path,
        binding,
        source_revision="a" * 40,
    )

    assert binding["status"] == "pass"
    assert binding["source_revision"] == "a" * 40
    assert [row["path"] for row in binding["evidence"]] == list(
        QUALITY_EVIDENCE_PATHS
    )
    assert verified["status"] == "pass"
    assert verified["evidence_count"] == len(QUALITY_EVIDENCE_PATHS)


def test_quality_evidence_binding_rejects_source_revision_drift(tmp_path):
    _write_evidence(tmp_path)
    binding = build_quality_evidence_binding(
        tmp_path,
        source_revision="a" * 40,
    )

    with pytest.raises(KnowledgeHubError, match="source revision mismatch"):
        verify_quality_evidence_binding(
            tmp_path,
            binding,
            source_revision="b" * 40,
        )


def test_quality_evidence_binding_rejects_evidence_mutation(tmp_path):
    _write_evidence(tmp_path)
    binding = build_quality_evidence_binding(
        tmp_path,
        source_revision="a" * 40,
    )
    target = tmp_path / QUALITY_EVIDENCE_PATHS[0]
    target.write_text('{"mutated": true}\n', encoding="utf-8")

    with pytest.raises(KnowledgeHubError, match="digest/size mismatch"):
        verify_quality_evidence_binding(
            tmp_path,
            binding,
            source_revision="a" * 40,
        )


def test_quality_evidence_binding_rejects_symlink(tmp_path):
    _write_evidence(tmp_path)
    target = tmp_path / QUALITY_EVIDENCE_PATHS[0]
    real = tmp_path / "real-evidence.json"
    real.write_text("{}\n", encoding="utf-8")
    target.unlink()
    target.symlink_to(real)

    with pytest.raises(KnowledgeHubError, match="unavailable"):
        build_quality_evidence_binding(
            tmp_path,
            source_revision="a" * 40,
        )
