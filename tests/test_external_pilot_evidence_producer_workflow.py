from pathlib import Path


def _workflow() -> str:
    root = Path(__file__).resolve().parents[1]
    return (root / ".github/workflows/external-pilot-evidence-producer.yml").read_text(
        encoding="utf-8"
    )


def test_external_pilot_producer_is_manual_master_only_and_read_only():
    text = _workflow()
    assert "workflow_dispatch:" in text
    assert "github.ref == 'refs/heads/master'" in text
    assert "actions: read" in text
    assert "contents: read" in text
    assert "contents: write" not in text
    assert "pull-requests: write" not in text


def test_external_pilot_producer_binds_successful_same_repo_source_artifact():
    text = _workflow()
    assert "source workflow run must" not in text
    assert "observation source run must be completed/success" in text
    assert "observation source run must belong to the current repository" in text
    assert "expected exactly one observation artifact" in text
    assert "observation artifact must expose a sha256 digest" in text
    assert "gh run download" in text


def test_external_pilot_producer_projects_strict_evidence_and_keeps_raw_observation_out():
    text = _workflow()
    assert "pilot_evidence_cli" in text
    assert '--expected-gap "${EXPECTED_GAP}"' in text
    assert "external-evidence.json" in text
    assert "raw_observation_uploaded': False" in text
    upload_block = text.split("- name: Upload bounded strict evidence artifact", 1)[1]
    assert "pilot-observation.json" not in upload_block
    assert ".tmp/external-pilot-observation" not in upload_block


def test_external_pilot_producer_binds_revision_and_connector_adapter_commit():
    text = _workflow()
    assert "evidence source_revision must equal observation source run head" in text
    assert "connector adapter_commit must equal observation source run head" in text
    assert "source_run_head_sha" in text
    assert "producer_revision" in text


def test_external_pilot_producer_cannot_mutate_canonical_registry():
    text = _workflow()
    assert "git diff --exit-code -- registry/knowledge-platform-p5-p10.json" in text
    assert "canonical_write_performed': False" in text
    assert "registry/knowledge-platform-p5-p10.json" not in text.split("path: |", 1)[-1]


def test_external_pilot_producer_uses_runtime_dependency_surface():
    text = _workflow()
    assert "requirements-runtime.lock" in text
    assert "requirements-dev.lock" not in text


def test_external_pilot_producer_supports_all_operational_real_evidence_gaps():
    text = _workflow()
    for gap in (
        "connector-provider-pilot",
        "production-retrieval-eval",
        "memory-lifecycle-pilot",
        "real-adoption-evidence",
    ):
        assert gap in text


def test_external_pilot_producer_requires_trusted_master_observation_run():
    text = _workflow()
    assert "observation source run must execute from master" in text
    assert "observation source run event is not trusted" in text
    assert "{'workflow_dispatch', 'schedule'}" in text
    assert "observation source workflow path is invalid" in text
    assert "'source_run_head_branch':" in text
    assert "'source_workflow_path':" in text


def test_external_pilot_producer_retains_attempt_and_validates_root_provenance():
    text = _workflow()
    assert "'source_run_attempt': int(run.get('run_attempt', 0) or 0)" in text
    assert "external-evidence-source-provenance-v1" in text
    assert "observation source provenance contract failed" in text


def test_external_pilot_producer_validates_producer_receipt_contract():
    text = _workflow()
    assert "external-pilot-evidence-producer-receipt-v1" in text
    assert "producer receipt contract validation failed" in text


def test_external_pilot_producer_binds_code_to_workflow_sha():
    text = _workflow()
    assert 'PRODUCER_REVISION: ${{ github.workflow_sha }}' in text
    assert 'ref: ${{ env.PRODUCER_REVISION }}' in text
    assert "'producer_revision': os.environ['PRODUCER_REVISION']" in text
    assert "'producer_revision': os.environ['GITHUB_SHA']" not in text
    assert text.count(
        "Checkout immutable producer revision"
    ) == 1


def test_external_pilot_producer_checkout_has_single_with_mapping():
    text = _workflow()
    block = text.split(
        "- name: Checkout immutable producer revision",
        1,
    )[1].split("- name: Set up governed Python", 1)[0]
    assert block.count("\n        with:\n") == 1
