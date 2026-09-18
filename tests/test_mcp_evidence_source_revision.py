from tools.codex_assets.knowledge_hub.common import repository_root


def test_mcp_evidence_uses_checked_out_revision_not_event_sha():
    root = repository_root()
    script = (root / "tools/ci/run-mcp-conformance.sh").read_text(encoding="utf-8")
    quality = (root / ".github/workflows/quality.yml").read_text(encoding="utf-8")
    manual = (root / ".github/workflows/mcp-conformance.yml").read_text(encoding="utf-8")

    assert 'git rev-parse --verify HEAD' in script
    assert 'export KNOWLEDGE_HUB_SOURCE_REVISION="$source_revision"' in script
    assert "'source_revision': os.environ.get('KNOWLEDGE_HUB_SOURCE_REVISION', '')" in script
    assert "'source_revision': os.environ.get('GITHUB_SHA', '')" not in script
    assert "'runner_environment': os.environ.get('RUNNER_ENVIRONMENT', '')" in script

    assert 'ref: ${{ github.event.pull_request.head.sha || github.sha }}' in quality
    assert "knowledge-hub-mcp-conformance" in quality
    assert "workflow_dispatch:" in manual
