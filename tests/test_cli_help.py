import importlib

import pytest

from tools.codex_assets.knowledge_hub.common import repository_root


CLI_MODULES = (
    "action_check_cli",
    "artifact_restore_cli",
    "compliance_eval_cli",
    "context_cli",
    "doctor_cli",
    "engineering_cli",
    "evidence_pack_cli",
    "export_cli",
    "feedback_cli",
    "final_gate_cli",
    "health_cli",
    "link_audit_cli",
    "map_cli",
    "metrics_cli",
    "new_cli",
    "obsidian_view_cli",
    "pcr02_validation_cli",
    "project_readiness_cli",
    "proposal_routing_cli",
    "proposal_shadow_stats_cli",
    "raw_evidence_cli",
    "recovery_cli",
    "restore_cli",
    "retrieval_cli",
    "review_attestation_cli",
    "runtime_maintenance_cli",
    "search_cli",
    "source_check_cli",
    "workspace_discovery_cli",
)
ROOT_FIRST_MODULES = {"doctor_cli", "new_cli"}


@pytest.mark.parametrize("module_name", CLI_MODULES)
def test_public_cli_exposes_zero_exit_help(module_name, capsys):
    module = importlib.import_module(
        "tools.codex_assets.knowledge_hub.{}".format(module_name)
    )

    argv = (
        [str(repository_root()), "--help"]
        if module_name in ROOT_FIRST_MODULES
        else ["--help"]
    )
    with pytest.raises(SystemExit) as raised:
        module.main(argv)

    output = capsys.readouterr().out
    assert raised.value.code == 0
    assert "usage:" in output
