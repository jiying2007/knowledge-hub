from tools.codex_assets.knowledge_hub.common import repository_root


def test_mcp_evidence_uses_checked_out_revision_not_event_sha():
    root = repository_root()
    script = (root / "tools/ci/run-mcp-conformance.sh").read_text(encoding="utf-8")
    workflow = (root / ".github/workflows/mcp-conformance.yml").read_text(encoding="utf-8")

    assert 'git rev-parse --verify HEAD' in script
    assert 'export KNOWLEDGE_HUB_SOURCE_REVISION="$source_revision"' in script
    assert "'source_revision': os.environ.get('KNOWLEDGE_HUB_SOURCE_REVISION', '')" in script
    assert "'source_revision': os.environ.get('GITHUB_SHA', '')" not in script
    assert "knowledge-hub-mcp-conformance-${{ github.event.pull_request.head.sha || github.sha }}" in workflow
    assert "knowledge-hub-mcp-conformance-${{ github.sha }}" not in workflow
