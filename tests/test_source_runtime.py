import datetime as dt
import json

import pytest

from tools.codex_assets.knowledge_hub.common import KnowledgeHubError
from tools.codex_assets.knowledge_hub.common import repository_root
from tools.codex_assets.knowledge_hub.source_runtime import run_source_checks


def _write_sources(root, current, retired):
    (root / "registry").mkdir()
    (root / "registry/sources.json").write_text(
        json.dumps({"sources": current}) + "\n"
    )
    (root / "registry/retired-sources.jsonl").write_text(
        "".join(json.dumps(row) + "\n" for row in retired)
    )


def test_all_scope_is_registry_driven_and_executes_current_and_retired(tmp_path):
    (tmp_path / "sources/current").mkdir(parents=True)
    (tmp_path / "sources/retired").mkdir(parents=True)
    _write_sources(
        tmp_path,
        [
            {
                "id": "current-source",
                "path": "sources/current",
                "check": "rtk test -d sources/current",
            }
        ],
        [
            {
                "id": "retired-source",
                "path": "sources/retired",
                "status": "retired",
                "check": "rtk test -d sources/retired",
            }
        ],
    )

    payload = run_source_checks(tmp_path, dt.date(2026, 7, 18), scope="all")

    assert payload["status"] == "pass"
    assert payload["registry_source_count"] == 2
    assert payload["current_source_count"] == 1
    assert payload["retired_source_count"] == 1
    assert payload["selected_source_ids"] == ["current-source", "retired-source"]
    assert payload["executed_count"] == 2
    assert {row["registry_bucket"] for row in payload["rows"]} == {"current", "retired"}


def test_all_scope_rejects_shell_payload_in_registry_check(tmp_path):
    (tmp_path / "sources/current").mkdir(parents=True)
    _write_sources(
        tmp_path,
        [
            {
                "id": "unsafe-source",
                "path": "sources/current",
                "check": "rtk test -d sources/current; touch /tmp/unsafe",
            }
        ],
        [],
    )

    payload = run_source_checks(tmp_path, dt.date(2026, 7, 18), scope="all")

    assert payload["status"] == "fail"
    assert payload["executed_count"] == 0
    assert payload["rejected_count"] == 1
    assert payload["rows"][0]["result"] == "rejected-runtime-check"


def test_source_check_rejects_removed_shell_form_and_external_paths(tmp_path):
    (tmp_path / "sources/current").mkdir(parents=True)
    _write_sources(
        tmp_path,
        [
            {
                "id": "removed-shell-form",
                "path": "sources/current",
                "check": "rtk bash -lc 'test -d sources/current'",
            },
            {
                "id": "external-path",
                "path": "/tmp",
                "check": "rtk test -d /tmp",
            },
        ],
        [],
    )

    payload = run_source_checks(tmp_path, dt.date(2026, 7, 18), scope="all")

    assert payload["status"] == "fail"
    assert payload["executed_count"] == 0
    assert payload["rejected_count"] == 2


def test_source_check_rejects_removed_profile_scope(tmp_path):
    _write_sources(tmp_path, [], [])

    with pytest.raises(KnowledgeHubError, match="all or current"):
        run_source_checks(tmp_path, dt.date(2026, 7, 18), scope="pcr02-level2")


def test_repository_all_scope_covers_every_registered_source():
    payload = run_source_checks(
        repository_root(), dt.date(2026, 7, 18), scope="all", plan=True
    )

    assert payload["status"] == "planned"
    assert payload["registry_source_count"] == 18
    assert payload["current_source_count"] == 5
    assert payload["retired_source_count"] == 13
    assert payload["row_count"] == payload["registry_source_count"]
    assert payload["expected_source_ids"] == payload["selected_source_ids"]
