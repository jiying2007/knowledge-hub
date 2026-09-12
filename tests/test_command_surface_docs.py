import pathlib

from tools.codex_assets.knowledge_hub import command_surface


def _catalog():
    return {
        "schema_version": 1,
        "wrapper_baseline": len(command_surface.DAILY_COMMANDS),
        "commands": [
            {
                "name": name,
                "plane": "experience",
                "tier": "daily",
                "summary_json": True,
            }
            for name in command_surface.DAILY_COMMANDS
        ],
    }


def _stub_surface(monkeypatch, tmp_path):
    wrappers = {
        name: tmp_path / "tools" / "{}.sh".format(name)
        for name in command_surface.DAILY_COMMANDS
    }
    monkeypatch.setattr(command_surface, "_load_catalog", lambda root: _catalog())
    monkeypatch.setattr(command_surface, "_wrapper_names", lambda root: wrappers)
    monkeypatch.setattr(
        command_surface,
        "_supports_summary_json",
        lambda root, wrapper: True,
    )


def _write_readme(tmp_path: pathlib.Path, count: int) -> None:
    (tmp_path / "README.md").write_text(
        "命令面的机器权威是 `registry/command-surface.json`：当前 {} 个稳定 wrapper。\n".format(count),
        encoding="utf-8",
    )


def test_command_surface_accepts_readme_count_bound_to_canonical_registry(monkeypatch, tmp_path):
    _stub_surface(monkeypatch, tmp_path)
    expected = len(command_surface.DAILY_COMMANDS)
    _write_readme(tmp_path, expected)

    report = command_surface.evaluate_command_surface(tmp_path)

    assert report["status"] == "pass"
    assert report["wrapper_count"] == expected
    assert report["readme_wrapper_count"] == expected
    assert report["errors"] == []


def test_command_surface_rejects_readme_count_drift(monkeypatch, tmp_path):
    _stub_surface(monkeypatch, tmp_path)
    expected = len(command_surface.DAILY_COMMANDS)
    _write_readme(tmp_path, expected - 1)

    report = command_surface.evaluate_command_surface(tmp_path)

    assert report["status"] == "fail"
    assert report["wrapper_count"] == expected
    assert report["readme_wrapper_count"] == expected - 1
    assert "README command-surface count differs from executable wrapper surface" in report["errors"]
