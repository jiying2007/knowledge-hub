from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "external-evidence-intake.yml"
CLI = ROOT / "tools" / "codex_assets" / "knowledge_hub" / "external_evidence_cli.py"


def _workflow():
    payload = yaml.load(WORKFLOW.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)
    assert isinstance(payload, dict)
    return payload


def test_external_evidence_intake_supports_trusted_auto_and_manual_paths():
    payload = _workflow()
    assert set(payload["on"]) == {"workflow_run", "workflow_dispatch"}
    trigger = payload["on"]["workflow_run"]
    assert trigger["workflows"] == ["external-pilot-evidence-producer"]
    assert trigger["types"] == ["completed"]
    assert payload["permissions"] == {"actions": "read", "contents": "read"}

    job = payload["jobs"]["intake"]
    condition = job["if"]
    assert "github.ref == 'refs/heads/master'" in condition
    assert "workflow_run.conclusion == 'success'" in condition
    assert "workflow_run.head_branch == 'master'" in condition
    assert job["env"]["INTAKE_REVISION"] == "${{ github.workflow_sha }}"


def test_external_evidence_intake_auto_path_requires_exact_producer_identity():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "automatic intake source must be external-pilot-evidence-producer" in text
    assert ".github/workflows/external-pilot-evidence-producer.yml" in text
    assert "automatic producer run must be master workflow_dispatch" in text
    assert "automatic intake requires exactly one strict producer artifact" in text
    assert "knowledge-hub-external-pilot-evidence-" in text
    assert (
        "connector-provider-pilot|production-retrieval-eval|"
        "memory-lifecycle-pilot|real-adoption-evidence"
        in text
    )
    assert 'evidence_file = "external-evidence.json"' in text


def test_external_evidence_intake_manual_fallback_keeps_exact_selectors():
    payload = _workflow()
    inputs = payload["on"]["workflow_dispatch"]["inputs"]
    assert "real-adoption-evidence" in inputs["expected_gap"]["options"]
    assert inputs["source_run_id"]["required"] == "true"
    assert inputs["artifact_name"]["required"] == "true"
    assert inputs["evidence_file"]["default"] == "external-evidence.json"

    text = WORKFLOW.read_text(encoding="utf-8")
    assert "artifact_name contains unsupported characters" in text
    assert "evidence_file must be a root JSON filename" in text
    assert "expected exactly one source artifact with the requested name" in text


def test_external_evidence_intake_binds_successful_source_run_and_digest():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "source workflow run must be completed/success" in text
    assert "source workflow run must belong to the current repository" in text
    assert "source workflow run must expose an exact git revision" in text
    assert "source artifact must expose a sha256 digest" in text
    assert "gh run download" in text
    assert "source-provenance.json" in text


def test_external_evidence_intake_never_auto_promotes_canonical_state():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "closure_candidate_only" in text
    assert "canonical_write_performed" in text
    assert "intake must never perform a canonical write" in text
    assert "registry/knowledge-platform-p5-p10.json" not in text
    assert "registry/terminal-closure.json" not in text
    assert ".tmp/external-evidence-source" not in text.split(
        "Upload bounded intake receipts", 1
    )[1]
    assert "if-no-files-found: error" in text


def test_external_evidence_intake_uses_runtime_dependency_surface():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "requirements-runtime.lock" in text
    assert "requirements-dev.lock" not in text


def test_external_evidence_cli_keeps_input_output_inside_repository_and_private():
    text = CLI.read_text(encoding="utf-8")
    assert "resolve_inside(root, args.input)" in text
    assert "resolve_inside(root, args.output)" in text
    assert "ensure_private_directory_tree(root, output.parent)" in text
    assert "ensure_private_file(output)" in text
    assert (
        'parser.add_argument("--expected-gap", choices=sorted(SUPPORTED_GAPS), required=True)'
        in text
    )


def test_external_evidence_intake_auto_path_supports_adoption():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "real-adoption-evidence" in text
    assert "automatic intake requires exactly one strict producer artifact" in text


def test_external_evidence_manual_fallback_keeps_trusted_master_source_boundary():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "source workflow run must execute from master" in text
    assert "manual intake source run event is not trusted" in text
    assert '{"workflow_dispatch", "schedule"}' in text
    assert "manual intake source workflow path is invalid" in text


def test_external_evidence_intake_retains_source_attempt_and_workflow_identity():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert '"source_run_attempt": int(run.get("run_attempt", 0) or 0)' in text
    assert '"source_run_head_branch": str(run.get("head_branch") or "")' in text
    assert '"source_workflow_path": str(run.get("path") or "")' in text


def test_external_evidence_intake_revalidates_producer_receipt_contract():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "external-pilot-evidence-producer-receipt-v1" in text
    assert "producer receipt contract validation failed" in text
    assert '"root_observation_provenance": root_provenance' in text
