"""Synthetic committed repositories; no production private bodies in tests."""
import hashlib
import json
import subprocess
from pathlib import Path

import pytest

from tools.codex_assets.knowledge_hub import tracked_text_inventory as census


def _git(root, *args):
    return subprocess.run(["git", "-C", str(root), *args], check=True,
                          capture_output=True).stdout.decode().strip()


def _repo(tmp_path, files=None, rows=None):
    root = tmp_path / "hub"
    (root / "registry").mkdir(parents=True)
    (root / "registry/items.jsonl").write_text(
        "".join(json.dumps(row) + "\n" for row in rows or []), encoding="utf-8")
    for path, data in (files or {"README.md": b"# Public index\n"}).items():
        target = root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    _git(root, "init")
    _git(root, "config", "user.email", "test@example.invalid")
    _git(root, "config", "user.name", "Synthetic Test")
    _commit(root)
    return root


def _commit(root):
    _git(root, "add", ".")
    _git(root, "commit", "-m", "synthetic fixture")


def _row(path, **overrides):
    return dict({"id": "fixture", "path": path, "status": "reviewing",
                 "visibility": "team-internal"}, **overrides)


def test_census_includes_readme_sources_templates_indexes_and_mdx(tmp_path):
    files = {p: ("# " + p + "\n").encode() for p in (
        "README.md", "docs/design.mdx", "sources/example/coverage.md",
        "sources/example/source-policy.md", "templates/example.md",
        "indexes/by-topic.md", "projects/example/README.md")}
    root = _repo(tmp_path, files)
    before = _git(root, "status", "--porcelain")
    result = census.build_tracked_text_inventory(root)
    assert result["status"] == "observed"
    assert result["source_revision"] == _git(root, "rev-parse", "HEAD")
    assert result["counts"]["tracked_text"] == len(files)
    assert result["counts"]["unregistered_public"] == len(files)
    assert {r["path"] for r in result["records"]} == set(files)
    for row in result["records"]:
        assert row["sha256"] == hashlib.sha256(files[row["path"]]).hexdigest()
        assert row["git_blob_sha1"] == _git(root, "rev-parse", "HEAD:" + row["path"])
        assert row["semantic_review_performed"] is False
    assert not result["full_content_review_proven"]
    assert not result["owner_approval_performed"]
    assert not result["canonical_write_performed"]
    assert _git(root, "status", "--porcelain") == before


@pytest.mark.parametrize("header", [b"visibility: private\n", b"status: personal\n",
    b"metadata: {visibility: private}\n", b"a: &a {visibility: private}\nb: *a\n"])
def test_private_header_is_excluded_without_body_hash_or_identity_export(tmp_path, monkeypatch, header):
    root = _repo(tmp_path, {"docs/hidden.md": b"---\n" + header + b"---\nSYNTHETIC_PRIVATE_BODY\n"})
    original = census._blob_sha

    def guarded(data):
        assert b"SYNTHETIC_PRIVATE_BODY" not in data
        return original(data)

    monkeypatch.setattr(census, "_blob_sha", guarded)
    result = census.build_tracked_text_inventory(root)
    assert result["counts"]["private_excluded"] == 1
    assert result["records"] == []
    assert "hidden.md" not in json.dumps(result)
    assert "SYNTHETIC_PRIVATE_BODY" not in json.dumps(result)


@pytest.mark.parametrize("path", ["notes/personal/x.md", "personal/x.md", ".private/x.md"])
def test_reserved_path_never_opens(tmp_path, monkeypatch, path):
    root = _repo(tmp_path, {path: b"SYNTHETIC_PRIVATE_BODY\n"})
    original = census._open_body

    def guarded(root, relative):
        assert relative != path
        return original(root, relative)

    monkeypatch.setattr(census, "_open_body", guarded)
    result = census.build_tracked_text_inventory(root)
    assert result["counts"]["private_excluded"] == 1
    assert path not in json.dumps(result)


def test_registry_private_directory_is_segment_bound(tmp_path):
    root = _repo(tmp_path, {"docs/private/x.md": b"hidden\n", "docs/private-extra/x.md": b"public\n"},
                 [_row("docs/private", visibility="personal-local")])
    result = census.build_tracked_text_inventory(root)
    assert result["counts"]["private_excluded"] == 1
    assert [r["path"] for r in result["records"]] == ["docs/private-extra/x.md"]


@pytest.mark.parametrize("data", [b"---\nvisibility: future-policy\n---\nx\n",
    b"---\nvisibility: public\nvisibility: private\n---\nx\n",
    b"---\nvisibility: public\n", b"---\n[bad\n---\nx\n"])
def test_ambiguous_header_is_counted_without_identity(tmp_path, data):
    root = _repo(tmp_path, {"docs/unknown.md": data})
    result = census.build_tracked_text_inventory(root)
    assert result["status"] == "needs-review"
    assert result["counts"]["classification_or_read_deferred"] == 1
    assert result["unresolved_count"] == 1
    assert "unknown.md" not in json.dumps(result)


@pytest.mark.parametrize("path", ["sources/raw-session/body.md", "notes/unclassified.md", "artifacts/vault/log.txt"])
def test_outside_authorized_hub_scope_never_opens(tmp_path, monkeypatch, path):
    root = _repo(tmp_path, {path: b"MUST_NOT_OPEN\n"})
    original = census._open_body

    def guarded(root, relative):
        assert relative != path
        return original(root, relative)

    monkeypatch.setattr(census, "_open_body", guarded)
    result = census.build_tracked_text_inventory(root)
    assert result["counts"]["policy_deferred"] == 1
    assert result["unresolved_count"] == 1
    assert path not in json.dumps(result)


@pytest.mark.parametrize("change", ["replace", "remove", "fifo", "symlink"])
def test_worktree_content_cannot_borrow_committed_blob_identity(tmp_path, change):
    root = _repo(tmp_path, {"docs/x.md": b"original\n"})
    path = root / "docs/x.md"
    path.unlink()
    if change == "replace":
        path.write_bytes(b"different\n")
    elif change == "fifo":
        import os
        os.mkfifo(path)
    elif change == "symlink":
        path.symlink_to(root / "registry/items.jsonl")
    result = census.build_tracked_text_inventory(root)
    assert result["status"] == "needs-review"
    assert result["unresolved_count"] == 1
    assert result["records"] == []


def test_registered_code_directory_and_missing_are_distinct(tmp_path):
    rows = [_row("tools/entry.sh"), _row("projects/archive", id="dir"),
            _row("docs/missing.md", id="missing")]
    root = _repo(tmp_path, {"tools/entry.sh": b"#!/bin/sh\nexit 0\n", "projects/archive/child.md": b"# Historical\n"}, rows)
    result = census.build_tracked_text_inventory(root)
    assert result["counts"]["registered_nontext"] == 1
    assert result["counts"]["registered_public"] == 1
    assert result["counts"]["registered_directory_roots"] == 1
    assert result["counts"]["registered_missing"] == 1
    assert result["unresolved_count"] == 1
    assert result["status"] == "needs-review"


@pytest.mark.parametrize("path", ["requirements-runtime.txt", "requirements-dev.txt"])
def test_dependency_input_is_not_called_semantically_reviewed(tmp_path, path):
    root = _repo(tmp_path, {path: b"PyYAML==6.0.3\n"})
    result = census.build_tracked_text_inventory(root)
    assert result["records"][0]["asset_role"] == "dependency-input"
    assert result["records"][0]["semantic_review_performed"] is False


@pytest.mark.parametrize("problem", ["dirty", "unknown", "duplicate"])
def test_registry_integrity_block_clears_all_rows(tmp_path, problem):
    root = _repo(tmp_path)
    path = root / "registry/items.jsonl"
    if problem == "dirty":
        path.write_text(json.dumps(_row("README.md")) + "\n")
    elif problem == "unknown":
        path.write_text(json.dumps(_row("README.md", visibility="future-policy")) + "\n")
        _commit(root)
    else:
        path.write_text('{"id":"a","path":"README.md","status":"personal","status":"active","visibility":"public"}\n')
        _commit(root)
    result = census.build_tracked_text_inventory(root)
    assert result["status"] == "blocked"
    assert not result["head_enumeration_complete"]
    assert result["records"] == []
    assert "README.md" not in json.dumps(result)


def test_head_change_during_observation_clears_rows(tmp_path, monkeypatch):
    root = _repo(tmp_path)
    original = census._scan

    def mutate(*args):
        result = original(*args)
        (root / "added.md").write_bytes(b"new\n")
        _commit(root)
        return result

    monkeypatch.setattr(census, "_scan", mutate)
    assert census.build_tracked_text_inventory(root)["status"] == "blocked"


def test_registered_secret_cannot_be_reclassified_by_public_header(tmp_path):
    root = _repo(tmp_path, {"docs/x.md": b"---\nvisibility: public\n---\nbody\n"},
                 [_row("docs/x.md", status="personal")])
    result = census.build_tracked_text_inventory(root)
    assert result["counts"]["private_excluded"] == 1
    assert result["records"] == []


def test_current_header_can_make_a_tracked_public_file_private(tmp_path):
    root = _repo(tmp_path, {"docs/x.md": b"public\n"})
    (root / "docs/x.md").write_bytes(b"---\nvisibility: private\n---\nSYNTHETIC_PRIVATE_BODY\n")
    result = census.build_tracked_text_inventory(root)
    assert result["counts"]["private_excluded"] == 1
    assert result["records"] == []


def test_untracked_text_is_not_silently_added_to_head_scope(tmp_path):
    root = _repo(tmp_path)
    (root / "untracked.md").write_text("untracked\n")
    result = census.build_tracked_text_inventory(root)
    assert result["counts"]["tracked_text"] == 1
    assert "untracked.md" not in json.dumps(result)


def test_global_budget_counts_changed_reads_not_only_successes(tmp_path, monkeypatch):
    root = _repo(tmp_path, {"docs/a.md": b"a\n", "docs/b.md": b"b\n"})
    (root / "docs/a.md").write_bytes(b"a\n" + b"x" * 70000)
    monkeypatch.setattr(census, "MAX_TOTAL", 100000)
    result = census.build_tracked_text_inventory(root)
    assert result["counts"]["worktree_drift"] == 1
    assert result["counts"]["classification_or_read_deferred"] == 1
    assert result["counts"]["read_bytes_including_deferred"] == 70002


def test_subdirectory_and_nonrepository_are_not_full_head_inventory(tmp_path):
    root = _repo(tmp_path)
    for target in [root / "registry", tmp_path]:
        result = census.build_tracked_text_inventory(target)
        assert result["status"] == "blocked"
        assert result["head_enumeration_complete"] is False


def test_body_count_is_an_exact_disjoint_partition(tmp_path):
    files = {"docs/public.md": b"public\n", "notes/personal/hidden.md": b"hidden\n",
             "notes/unclassified.md": b"unclassified\n", "docs/unknown.md": b"---\nvisibility: future\n---\nx\n"}
    root = _repo(tmp_path, files)
    result = census.build_tracked_text_inventory(root)
    c = result["counts"]
    assert c["tracked_text"] + c["registered_nontext"] == sum(c[k] for k in (
        "private_excluded", "policy_deferred", "unsupported_entry", "classification_or_read_deferred",
        "worktree_drift", "public_exact_head"))


def test_binary_disguised_as_text_stays_deferred(tmp_path):
    root = _repo(tmp_path, {"docs/not-text.md": b"legacy\n\xff\xfe"})
    result = census.build_tracked_text_inventory(root)
    assert result["counts"]["classification_or_read_deferred"] == 1
    assert result["records"] == []


def test_registry_change_during_scan_discards_projection(tmp_path, monkeypatch):
    root = _repo(tmp_path)
    original = census._scan

    def mutate(*args):
        result = original(*args)
        (root / "registry/items.jsonl").write_text(json.dumps(_row("README.md")))
        return result

    monkeypatch.setattr(census, "_scan", mutate)
    result = census.build_tracked_text_inventory(root)
    assert result["status"] == "blocked"
    assert result["records"] == []


def test_registered_binary_remains_counted_but_not_read(tmp_path, monkeypatch):
    path = "artifacts/vault/example.pdf"
    root = _repo(tmp_path, {path: b"BINARY_DO_NOT_READ"}, [_row(path)])
    original = census._open_body

    def guarded(root, relative):
        assert relative != path
        return original(root, relative)

    monkeypatch.setattr(census, "_open_body", guarded)
    result = census.build_tracked_text_inventory(root)
    assert result["counts"]["registered_nontext"] == 1
    assert result["counts"]["policy_deferred"] == 1
    assert path not in json.dumps(result)


def test_tracked_symlink_and_unsafe_names_cannot_export_identity(tmp_path):
    root = _repo(tmp_path)
    (root / "docs").mkdir()
    (root / "docs/link.md").symlink_to(root / "README.md")
    _commit(root)
    result = census.build_tracked_text_inventory(root)
    assert result["counts"]["unsupported_entry"] == 1
    assert "link.md" not in json.dumps(result)
    (root / "docs/bad\nname.md").write_text("unsafe path\n")
    _commit(root)
    result = census.build_tracked_text_inventory(root)
    assert result["status"] == "blocked"
    assert result["records"] == []


def test_census_module_is_an_exact_security_critical_rule():
    root = Path(__file__).resolve().parents[1]
    policy = json.loads((root / "registry/review-risk-policy.json").read_text())
    matches = [r for r in policy["rules"] if r.get("path") ==
               "tools/codex_assets/knowledge_hub/tracked_text_inventory.py"]
    assert matches == [{"path": "tools/codex_assets/knowledge_hub/tracked_text_inventory.py",
                        "review_class": "security-critical"}]
    assert policy["classes"]["security-critical"]["ai_first_action"] == "human-review-required"


def test_cli_preserves_selected_gate_and_observes_global_scope_separately():
    root = Path(__file__).resolve().parents[1]
    source = (root / "tools/codex_assets/knowledge_hub/orphan_files_cli.py").read_text()
    assert 'output["tracked_text_inventory"] = build_tracked_text_inventory(root)' in source
    assert 'needs_fix = bool(missing or coverage_errors)' in source
    assert 'if args.strict and needs_fix:' in source
    assert 'output["convergence"] = build_content_convergence(' in source
