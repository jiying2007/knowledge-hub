"""Private bodies must be excluded before hashing or exporting identities."""

import hashlib
import json
import pathlib
import runpy
import sys

import pytest

from tools.codex_assets.knowledge_hub import content_convergence as convergence
from tools.codex_assets.knowledge_hub.common import KnowledgeHubError


def _json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value) + "\n", encoding="utf-8")


def _root(root, *, status="personal", visibility="team-internal"):
    public = "projects/demo/current/public.md"
    private = "projects/demo/current/private-canary.md"
    rows = [
        {"id": "public-item", "path": public,
         "status": "reviewing", "visibility": "team-internal"},
        {"id": "private-item-canary", "path": private,
         "status": status, "visibility": visibility},
    ]
    _json(root / "registry/sources.json", {"schema_version": 1, "sources": []})
    _json(root / "registry/owners.json", {"owners": []})
    _json(root / "registry/body-coverage.json", {"schema_version": 2, "collections": []})
    (root / "registry/retired-sources.jsonl").write_text("", encoding="utf-8")
    (root / "registry/items.jsonl").write_text(
        "".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8",
    )
    for name, body in ((public, "Public body.\n"), (private, "PRIVATE_BODY_CANARY\n")):
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")
    return public, private, rows


def _forbid_private_open(monkeypatch, paths):
    original = pathlib.Path.open

    def guarded(path, *args, **kwargs):
        if path in paths:
            pytest.fail("private body must never be opened")
        return original(path, *args, **kwargs)

    monkeypatch.setattr(pathlib.Path, "open", guarded)


@pytest.mark.parametrize("status,visibility", [
    ("personal", "team-internal"), ("reviewing", "personal-local"),
])
def test_registry_private_classification_precedes_reads(tmp_path, monkeypatch, status, visibility):
    public, private, _ = _root(tmp_path, status=status, visibility=visibility)
    _forbid_private_open(monkeypatch, {tmp_path / private})
    result = convergence.build_content_convergence(
        tmp_path, [private, public],
        {public: ["public-item"], private: ["private-item-canary"]}, {},
    )
    assert result["scope_body_count"] == 2
    assert result["private_excluded_count"] == 1
    assert result["body_count"] == result["exact_registry_count"] == 1
    assert result["hashed_bytes"] == len(b"Public body.\n")
    assert result["private_bodies_hashed"] is False
    assert result["exact_duplicate_candidates"] == []
    rendered = json.dumps(result)
    for value in (private, "private-item-canary", "PRIVATE_BODY_CANARY",
                  hashlib.sha256(b"PRIVATE_BODY_CANARY\n").hexdigest()):
        assert value not in rendered


def test_private_duplicate_never_becomes_a_duplicate_candidate(tmp_path, monkeypatch):
    public, private, _ = _root(tmp_path)
    (tmp_path / private).write_bytes(b"Public body.\n")
    _forbid_private_open(monkeypatch, {tmp_path / private})
    result = convergence.build_content_convergence(tmp_path, [public, private], {}, {})
    assert result["body_count"] == 1
    assert result["exact_duplicate_candidate_count"] == 0


def test_private_directory_and_default_personal_scope_are_segment_bound(tmp_path, monkeypatch):
    public, _, rows = _root(tmp_path)
    rows[1]["path"] = "projects/demo/private-tree"
    (tmp_path / "registry/items.jsonl").write_text(
        "".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8",
    )
    child = "projects/demo/private-tree/never-opened.md"
    note = "notes/personal/unregistered-canary.md"
    # Even absent personal bodies must not be opened, hashed, or identified.
    result = convergence.build_content_convergence(tmp_path, [public, child, note], {}, {})
    assert result["body_count"] == 1
    assert result["private_excluded_count"] == 2
    assert convergence.private_body_paths(tmp_path, [
        "projects/demo/private-tree-extra/a.md", "notes/personality/a.md",
    ]) == set()
    assert child not in json.dumps(result)
    assert note not in json.dumps(result)


@pytest.mark.parametrize("field,value", [
    ("visibility", None), ("visibility", "future-policy"), ("visibility", []),
    ("status", None), ("status", []), ("status", "future-status"),
    ("path", "../PRIVATE_PATH_CANARY"), ("path", "./PRIVATE_PATH_CANARY"),
    ("path", "projects//PRIVATE_PATH_CANARY"), ("path", None),
])
def test_invalid_classification_fails_before_any_body_read(tmp_path, monkeypatch, field, value):
    public, private, rows = _root(tmp_path)
    rows[1][field] = value
    (tmp_path / "registry/items.jsonl").write_text(
        "".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8",
    )
    _forbid_private_open(monkeypatch, {tmp_path / public, tmp_path / private})
    with pytest.raises(KnowledgeHubError, match="registry privacy") as error:
        convergence.build_content_convergence(tmp_path, [public, private], {}, {})
    assert "PRIVATE_PATH_CANARY" not in str(error.value)
    assert "private-item-canary" not in str(error.value)


def test_missing_privacy_registry_is_not_an_empty_public_registry(tmp_path, monkeypatch):
    public, private, _ = _root(tmp_path)
    (tmp_path / "registry/items.jsonl").unlink()
    _forbid_private_open(monkeypatch, {tmp_path / public, tmp_path / private})
    with pytest.raises(KnowledgeHubError, match="missing or symlinked"):
        convergence.build_content_convergence(tmp_path, [public, private], {}, {})


def test_internal_directory_symlink_cannot_alias_a_private_body(tmp_path, monkeypatch):
    public, private, _ = _root(tmp_path)
    alias = tmp_path / "projects/alias"
    alias.symlink_to(tmp_path / "projects/demo/current", target_is_directory=True)
    _forbid_private_open(monkeypatch, {tmp_path / private, alias / "private-canary.md"})
    with pytest.raises(KnowledgeHubError, match="symlinked path component"):
        convergence.build_content_convergence(
            tmp_path, ["projects/alias/private-canary.md"], {}, {},
        )


@pytest.mark.parametrize("extra", [[], ["--convergence"]])
def test_real_cli_summary_and_nested_report_both_exclude_private(tmp_path, monkeypatch, capsys, extra):
    public, private, _ = _root(tmp_path, status="reviewing", visibility="personal-local")
    note = tmp_path / "notes/personal/unregistered-canary.md"
    note.parent.mkdir(parents=True)
    note.write_text("UNREGISTERED_PRIVATE_CANARY", encoding="utf-8")
    _forbid_private_open(monkeypatch, {tmp_path / private, note})
    monkeypatch.setattr(sys, "argv", [
        "orphan_files_cli", str(tmp_path), "--all", "--strict", "--json",
        "--limit", "5000", *extra,
    ])
    runpy.run_module("tools.codex_assets.knowledge_hub.orphan_files_cli", run_name="__main__")
    rendered = capsys.readouterr().out
    report = json.loads(rendered)
    assert report["status"] == "ok"
    assert report["checked_count"] == report["registered_count"] == 1
    assert report["scope_checked_count"] == 3
    assert report["private_excluded_count"] == 2
    assert report["missing_registry_count"] == 0
    for value in (private, "private-item-canary", "unregistered-canary", "PRIVATE_CANARY"):
        assert value not in rendered
    if extra:
        assert report["convergence"]["body_count"] == 1
        assert report["convergence"]["private_excluded_count"] == 2


def test_excluding_private_never_hides_an_unregistered_public_body(tmp_path, monkeypatch, capsys):
    _root(tmp_path)
    missing = "projects/demo/current/unregistered-public.md"
    (tmp_path / missing).write_text("Needs registry coverage.", encoding="utf-8")
    monkeypatch.setattr(sys, "argv", [
        "orphan_files_cli", str(tmp_path), "--all", "--strict", "--json", "--convergence",
    ])
    with pytest.raises(SystemExit) as error:
        runpy.run_module("tools.codex_assets.knowledge_hub.orphan_files_cli", run_name="__main__")
    assert error.value.code == 1
    report = json.loads(capsys.readouterr().out)
    assert report["missing_registry"] == [missing]
    assert report["convergence"]["uncovered_count"] == 1
    assert report["convergence"]["full_content_review_proven"] is False


def test_duplicate_privacy_keys_fail_closed_before_body_reads(tmp_path, monkeypatch):
    public, private, _ = _root(tmp_path)
    (tmp_path / "registry/items.jsonl").write_text(
        '{"id":"canary","path":"projects/demo/current/private-canary.md",'
        '"status":"personal","status":"reviewing","visibility":"team-internal"}\n',
        encoding="utf-8",
    )
    _forbid_private_open(monkeypatch, {tmp_path / public, tmp_path / private})
    with pytest.raises(KnowledgeHubError, match="duplicate key in convergence metadata"):
        convergence.build_content_convergence(tmp_path, [public, private], {}, {})


@pytest.mark.parametrize("alias", [
    "./projects/demo/current/private-canary.md",
    "projects//demo/current/private-canary.md",
    "projects/demo/./current/private-canary.md",
])
def test_noncanonical_path_cannot_alias_registered_private_file(tmp_path, monkeypatch, alias):
    _, private, _ = _root(tmp_path)
    _forbid_private_open(monkeypatch, {tmp_path / private})
    with pytest.raises(KnowledgeHubError, match="invalid canonical body path"):
        convergence.build_content_convergence(tmp_path, [alias], {}, {})
