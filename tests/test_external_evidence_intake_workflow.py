from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "external-evidence-intake.yml"
CLI = ROOT / "tools" / "codex_assets" / "knowledge_hub" / "external_evidence_cli.py"


def test_external_evidence_intake_is_manual_master_only_and_read_only():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "workflow_dispatch:" in text
    assert "github.ref == 'refs/heads/master'" in text
    assert "actions: read" in text
    assert "contents: read" in text
    assert "contents: write" not in text
    assert "pull-requests: write" not in text


def test_external_evidence_intake_binds_successful_source_run_and_digest():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "source workflow run must be completed/success" in text
    assert "source workflow run must belong to the current repository" in text
    assert "source workflow run must expose an exact git revision" in text
    assert "expected exactly one source artifact with the requested name" in text
    assert "source artifact must expose a sha256 digest" in text
    assert "gh run download" in text


def test_external_evidence_intake_never_auto_promotes_canonical_state():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "closure_candidate_only" in text
    assert "canonical_write_performed" in text
    assert "intake must never perform a canonical write" in text
    assert "registry/knowledge-platform-p5-p10.json" not in text
    assert "registry/terminal-closure.json" not in text
    assert ".tmp/external-evidence-source" not in text.split("Upload bounded intake receipts", 1)[1]
    assert "if-no-files-found: error" in text


def test_external_evidence_cli_keeps_input_output_inside_repository_and_private():
    text = CLI.read_text(encoding="utf-8")
    assert "resolve_inside(root, args.input)" in text
    assert "resolve_inside(root, args.output)" in text
    assert "ensure_private_directory_tree(root, output.parent)" in text
    assert "ensure_private_file(output)" in text
    assert 'parser.add_argument("--expected-gap", choices=sorted(SUPPORTED_GAPS), required=True)' in text
