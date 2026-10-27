"""Real temporary Git checkouts; private canaries must never reach projections."""
import hashlib
import json
import os
import subprocess

import pytest

from tools.codex_assets.knowledge_hub import body_privacy as privacy
from tools.codex_assets.knowledge_hub import repository_text_inventory as inventory


def _git(root, *args):
    return subprocess.check_output([
        "git", "-c", "core.hooksPath=/dev/null", "-C", str(root), *args,
    ], stderr=subprocess.DEVNULL).decode().strip()


def _repo(root, files):
    root.mkdir(exist_ok=True)
    _git(root, "init", "-q")
    for name, content in files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
    _git(root, "add", "--all")
    _git(root, "-c", "user.name=Synthetic Inventory Test", "-c",
         "user.email=inventory-test@example.invalid", "commit", "-qm", "fixture")
    return _git(root, "rev-parse", "HEAD")


def test_full_scope_extends_beyond_old_body_prefixes(tmp_path):
    files = {"README.md": b"# public\n", "sources/test/coverage.md": b"coverage\n",
             "templates/item.mdx": b"template\n", "requirements-runtime.txt": b"PyYAML==6.0.3\n",
             "docs/test.MD": b"Upper extension\n", "script.py": b"pass\n"}
    head = _repo(tmp_path, files)
    report = inventory.build_repository_text_inventory(tmp_path, set(), {"README.md": ["root"]})
    assert report["status"] == "observed"
    assert report["source_revision"] == head
    assert report["head_inventory_complete"] is True
    assert report["tracked_text_count"] == report["observed_count"] == 5
    assert report["registered_count"] == 1
    assert report["unregistered_count"] == 4
    assert report["withheld_count"] == report["private_excluded_count"] == 0
    assert report["semantic_review_performed"] is report["terminal"] is False
    for row in report["body_records"]:
        assert row["sha256"] == hashlib.sha256(files[row["path"]]).hexdigest()
        assert row["git_blob"] == _git(tmp_path, "rev-parse", head + ":" + row["path"])
        assert row["size_bytes"] == len(files[row["path"]])
    fingerprint = report.pop("report_sha256")
    raw = json.dumps(report, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    assert fingerprint == hashlib.sha256(raw).hexdigest()


@pytest.mark.parametrize("private_path", [
    "notes/personal/canary.md", "personal/canary.md", ".private/canary.md", "restricted/canary.md",
])
def test_reserved_and_registry_private_paths_are_not_opened(tmp_path, monkeypatch, private_path):
    _repo(tmp_path, {private_path: b"SYNTHETIC_PRIVATE_BODY\n", "public.md": b"public\n"})
    original = inventory.declared_private

    def guard(root, relative):
        assert relative != private_path
        return original(root, relative)

    monkeypatch.setattr(inventory, "declared_private", guard)
    report = inventory.build_repository_text_inventory(tmp_path, {"restricted"}, {})
    assert report["private_excluded_count"] == 1
    assert report["observed_count"] == 1
    assert private_path not in json.dumps(report)
    assert "SYNTHETIC_PRIVATE_BODY" not in json.dumps(report)


@pytest.mark.parametrize("header", [
    b"visibility: private\n", b"status: personal\n", b"metadata: {visibility: private}\n",
    b"metadata: {status: personal}\n",
])
def test_private_header_precedes_hash_and_identity_export(tmp_path, monkeypatch, header):
    hidden = "synthetic-sensitive-name.md"
    _repo(tmp_path, {hidden: b"---\n" + header + b"---\nSYNTHETIC_CANARY\n"})
    monkeypatch.setattr(inventory, "digest_public_body", lambda *a, **k: pytest.fail("private hashed"))
    report = inventory.build_repository_text_inventory(tmp_path, set(), {})
    assert report["tracked_text_count"] == report["private_excluded_count"] == 1
    assert report["body_records"] == []
    assert hidden not in json.dumps(report)
    assert "SYNTHETIC_CANARY" not in json.dumps(report)


@pytest.mark.parametrize("body", [
    b"---\nvisibility: not-defined\n---\nbody\n",
    b"---\nvisibility: public\nvisibility: private\n---\nbody\n",
    b"---\nvisibility: [public]\n---\nbody\n",
    b"---\nmetadata: &a {same: *a}\n---\nbody\n",
    b"---\nvisibility: public\n", b"x" * 4097,
])
def test_ambiguous_header_is_counted_but_never_named(tmp_path, body):
    hidden = "unknown-policy-canary.md"
    _repo(tmp_path, {hidden: body, "public.md": b"public\n"})
    report = inventory.build_repository_text_inventory(tmp_path, set(), {})
    assert report["status"] == "needs-review"
    assert report["withheld_count"] == 1
    assert report["observed_count"] == 1
    assert hidden not in json.dumps(report)


def test_dirty_deleted_and_untracked_texts_are_not_current_claims(tmp_path):
    _repo(tmp_path, {"dirty.md": b"old\n", "gone.md": b"gone\n", "kept.md": b"kept\n"})
    (tmp_path / "dirty.md").write_bytes(b"new\n")
    (tmp_path / "gone.md").unlink()
    (tmp_path / "new.md").write_bytes(b"not committed\n")
    report = inventory.build_repository_text_inventory(tmp_path, set(), {})
    assert report["tracked_text_count"] == 3
    assert report["withheld_count"] == 2
    assert [r["path"] for r in report["body_records"]] == ["kept.md"]
    assert "new.md" not in json.dumps(report)


def test_symlink_text_is_withheld_without_following(tmp_path):
    _repo(tmp_path, {"public.md": b"public\n"})
    (tmp_path / "alias.md").symlink_to("public.md")
    _git(tmp_path, "add", "alias.md")
    _git(tmp_path, "-c", "user.name=Test", "-c", "user.email=t@example.invalid", "commit", "-qm", "link")
    report = inventory.build_repository_text_inventory(tmp_path, set(), {})
    assert report["tracked_text_count"] == 2
    assert report["observed_count"] == report["withheld_count"] == 1
    assert "alias.md" not in json.dumps(report)


def test_checkout_fifo_substitution_cannot_block_or_hash(tmp_path):
    _repo(tmp_path, {"test.md": b"original\n"})
    (tmp_path / "test.md").unlink()
    os.mkfifo(tmp_path / "test.md")
    report = inventory.build_repository_text_inventory(tmp_path, set(), {})
    assert report["withheld_count"] == 1 and report["body_records"] == []


def test_non_git_or_nested_checkout_is_not_complete(tmp_path):
    assert inventory.build_repository_text_inventory(tmp_path, set(), {})["status"] == "unavailable"
    _repo(tmp_path, {"nested/file.md": b"text\n"})
    report = inventory.build_repository_text_inventory(tmp_path / "nested", set(), {})
    assert report["head_inventory_complete"] is False
    assert report["tracked_text_count"] is None and report["body_records"] == []


@pytest.mark.parametrize("constant,value", [
    ("MAX_TEXT_FILES", 0), ("MAX_TREE_ENTRIES", 0), ("MAX_METADATA_BYTES", 10),
])
def test_scope_budget_overflow_is_not_a_complete_report(tmp_path, monkeypatch, constant, value):
    _repo(tmp_path, {"test.md": b"text\n"})
    monkeypatch.setattr(inventory, constant, value)
    report = inventory.build_repository_text_inventory(tmp_path, set(), {})
    assert report["status"] == "unavailable" and report["head_inventory_complete"] is False


def test_body_budget_is_not_silently_treated_as_reviewed(tmp_path, monkeypatch):
    _repo(tmp_path, {"test.md": b"text\n"})
    monkeypatch.setattr(inventory, "MAX_TOTAL_BODY_BYTES", 1)
    report = inventory.build_repository_text_inventory(tmp_path, set(), {})
    assert report["status"] == "needs-review" and report["withheld_count"] == 1


def test_head_drift_discards_projection(tmp_path, monkeypatch):
    head = _repo(tmp_path, {"test.md": b"text\n"})
    original = inventory._git
    observations = 0

    def change(root, args):
        nonlocal observations
        data = original(root, args)
        if args == ["rev-parse", "--verify", "HEAD^{commit}"]:
            observations += 1
            if observations == 2:
                return (("0" if head[0] != "0" else "1") + head[1:] + "\n").encode()
        return data

    monkeypatch.setattr(inventory, "_git", change)
    report = inventory.build_repository_text_inventory(tmp_path, set(), {})
    assert report["status"] == "unavailable" and report["body_records"] == []


def test_nested_private_after_summary_still_does_not_hash(tmp_path, monkeypatch):
    _repo(tmp_path, {"test.md": b"public\n"})
    original = inventory.declared_private

    def mutate(root, path):
        result = original(root, path)
        (root / path).write_bytes(b"---\nmetadata: {visibility: private}\n---\nCANARY\n")
        return result

    monkeypatch.setattr(inventory, "declared_private", mutate)
    report = inventory.build_repository_text_inventory(tmp_path, set(), {})
    assert report["body_records"] == [] and report["withheld_count"] == 1
    assert "test.md" not in json.dumps(report)


@pytest.mark.parametrize("value", ["g" * 40, "0" * 39, "0" * 41, True, 2])
def test_expected_git_identity_shape_is_checked_before_open(tmp_path, monkeypatch, value):
    monkeypatch.setattr(privacy, "_open_body", lambda *a: pytest.fail("invalid identity opened"))
    with pytest.raises(privacy.BodyPrivacyError):
        privacy.digest_public_body(tmp_path, "test.md", 100, expected_git_blob=value)


def test_wrong_git_blob_cannot_issue_current_sha(tmp_path):
    data = b"public body\n"
    (tmp_path / "test.md").write_bytes(data)
    with pytest.raises(privacy.BodyPrivacyError):
        privacy.digest_public_body(tmp_path, "test.md", len(data), expected_git_blob="0" * 40)
    assert privacy.digest_public_body(tmp_path, "test.md", len(data)) == (
        hashlib.sha256(data).hexdigest(), len(data),
    )


def test_existing_convergence_invokes_whole_repository_observer(tmp_path):
    from tools.codex_assets.knowledge_hub.content_convergence import build_content_convergence

    files = {"projects/public.md": b"public\n", "docs/extra.md": b"extra\n",
             "registry/items.jsonl": b"", "registry/sources.json": b'{"sources":[]}',
             "registry/retired-sources.jsonl": b""}
    _repo(tmp_path, files)
    report = build_content_convergence(tmp_path, ["projects/public.md"], {}, {})
    assert report["scope_body_count"] == report["body_count"] == 1
    whole = report["repository_text_inventory"]
    assert whole["tracked_text_count"] == whole["observed_count"] == 2
    assert report["full_content_review_proven"] is False
    assert whole["semantic_review_performed"] is False


def test_registered_nontext_and_missing_asset_metadata_is_counted_without_content(tmp_path):
    _repo(tmp_path, {"docs/public.md": b"public\\n", "registry/config.json": b'{"x":1}',
                     "tools/sample.sh": b"#!/bin/sh\\n", "history/chunk.md": b"history\\n"})
    registered = {"docs/public.md": ["public"], "registry/config.json": ["config"],
                  "tools/sample.sh": ["shell"], "history": ["archive-dir"],
                  "missing/not-here.json": ["missing"], "restricted/sensitive.json": ["private"]}
    report = inventory.build_repository_text_inventory(tmp_path, {"restricted"}, registered)
    counts = report["registered_asset_counts"]
    assert counts["registered_nontext_regular_count"] == 2
    assert counts["registered_nontext_unsafe_count"] == 0
    assert counts["registered_missing_path_count"] == 1
    assert counts["registered_directory_root_count"] == 1
    assert report["registered_nontext_metadata_only"] is True
    assert report["registered_nontext_content_verified"] is False
    assert report["status"] == "needs-review"
    assert "restricted/sensitive.json" not in json.dumps(report)
    assert "missing/not-here.json" not in json.dumps(report)
    assert '"x":1' not in json.dumps(report)


def test_invalid_registered_path_does_not_export_identity(tmp_path):
    _repo(tmp_path, {"safe.md": b"safe\\n"})
    report = inventory.build_repository_text_inventory(tmp_path, set(),
                                                        {"../outside/private.json": ["secret"]})
    assert report["status"] == "unavailable"
    assert report["body_records"] == []
    assert "../outside" not in json.dumps(report)


def test_registered_nontext_symlink_is_counted_as_unsafe_not_read(tmp_path):
    _repo(tmp_path, {"public.md": b"safe\\n", "private.json": b"private data"})
    (tmp_path / "private.json").unlink()
    (tmp_path / "private.json").symlink_to("public.md")
    _git(tmp_path, "add", "private.json")
    _git(tmp_path, "-c", "user.name=Test", "-c", "user.email=t@example.invalid",
         "commit", "-qm", "link nontext")
    report = inventory.build_repository_text_inventory(tmp_path, set(),
                                                        {"private.json": ["protected"]})
    counts = report["registered_asset_counts"]
    assert counts["registered_nontext_unsafe_count"] == 1
    assert report["status"] == "needs-review"
    assert "private.json" not in json.dumps(report)
