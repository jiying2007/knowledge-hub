import json
import pytest

from tools.codex_assets.knowledge_hub import provider_cli
from tools.codex_assets.knowledge_hub.context_support import TASK_TYPES
from tools.codex_assets.knowledge_hub.schemas import validate_instance


@pytest.mark.parametrize("option,value,issue", [
    ("--task-type", "private-secret-sentinel", "invalid-choice"),
    ("--context-budget", "private-secret-sentinel", "invalid-choice"),
    ("--limit", "private-secret-sentinel", "invalid-type"),
    ("--unknown-option", "private-secret-sentinel", "invalid-arguments"),
])
def test_invalid_arguments_are_diagnostic_and_do_not_echo_input(capsys, option, value, issue):
    assert provider_cli.main(["context", option, value]) == 2
    raw = capsys.readouterr().out
    result = json.loads(raw)
    assert value not in raw
    assert result["status"] == "BLOCKED" and result["reason_codes"] == ["SCHEMA_INVALID"]
    assert result["persisted"] is False and result["write_performed"] is False
    assert result["diagnostics"][0]["issue"] == issue
    if option != "--unknown-option":
        assert result["diagnostics"][0]["field"] == option
    assert validate_instance(provider_cli.repository_root(""), "provider-operation-receipt-v4", result)["status"] == "pass"


def test_help_is_structured_readonly_and_does_not_resolve_repository(capsys, monkeypatch):
    monkeypatch.setattr(provider_cli, "repository_root", lambda root: pytest.fail("help resolved repository"))
    with pytest.raises(SystemExit) as exited:
        provider_cli.main(["context", "--help"])
    assert exited.value.code == 0
    result = json.loads(capsys.readouterr().out)
    assert result["schema_version"] == "knowledge-provider.help/v4"
    assert result["operation"] == "context" and result["read_only"] is True
    assert result["persisted"] is False and result["write_performed"] is False
    options = {flag: row for row in result["options"] for flag in row["flags"]}
    assert options["--task-type"]["allowed_values"] == sorted(TASK_TYPES)
    assert "--project" not in options and "--root" not in options and "--apply" not in options
    assert "--execution-project" in options


def test_analysis_is_not_an_alias_and_capability_matches_parser():
    from tools.codex_assets.knowledge_hub.provider_capabilities import capabilities
    with pytest.raises(provider_cli.ProviderArgumentError):
        provider_cli.parser().parse_args(["context", "--task-type", "analysis"])
    result = capabilities(provider_cli.repository_root(""))
    assert result["operations"]["context"]["task_types"] == sorted(TASK_TYPES)


@pytest.mark.parametrize("args,field", [(["--project", "private-secret-sentinel"], "--project"), (["--apply"], "--apply")])
def test_foreign_operation_arguments_identify_only_known_field(capsys, args, field):
    assert provider_cli.main(["context", "--query", "private-secret-sentinel"] + args) == 2
    raw = capsys.readouterr().out
    result = json.loads(raw)
    assert "private-secret-sentinel" not in raw
    assert result["persisted"] is False and result["write_performed"] is False
    assert result["diagnostics"] == [{"field": field, "issue": "unsupported-for-operation", "allowed_values": []}]
