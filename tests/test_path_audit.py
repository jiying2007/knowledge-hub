from tools.codex_assets.knowledge_hub.common import (
    parse_json_output,
    repository_root,
    run_rtk,
)


def test_hub_path_audit_classifies_negative_retrieval_terms_as_detector_config():
    root = repository_root()
    result = run_rtk(
        root,
        [
            "bash",
            "tools/knowledge-path-audit.sh",
            "--scope",
            "hub",
            "--strict",
            "--json",
        ],
        accepted_exit_codes=(0, 1),
    )
    payload = parse_json_output(result)
    detector_paths = {
        row["path"]
        for row in payload["matches"]
        if row["classification"] == "detector-config"
    }

    assert result["exit_code"] == 0
    assert payload["summary"]["runtime_route_candidate_count"] == 0
    assert "tests/fixtures/retrieval_cases.json" in detector_paths
    assert "tools/codex_assets/knowledge_hub/retrieval.py" in detector_paths
