"""Explain withheld scope without disclosing any withheld path or body."""
import hashlib
import json
import subprocess

import pytest

from tools.codex_assets.knowledge_hub import repository_text_inventory as inventory
from tools.codex_assets.knowledge_hub.body_privacy import BodyPrivacyError


def _git(root, *args):
    return subprocess.check_output(
        ["git", "-c", "core.hooksPath=/dev/null", "-C", str(root), *args],
        stderr=subprocess.DEVNULL,
    ).decode().strip()


def _repo(root, files):
    _git(root, "init", "-q")
    for name, data in files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    _git(root, "add", "--all")
    _git(root, "-c", "user.name=Synthetic Test", "-c",
         "user.email=test@example.invalid", "commit", "-qm", "fixture")


@pytest.mark.parametrize("header,reason", [
    (b"visibility: future\n", "unknown-privacy-classification"),
    (b"visibility: public\nvisibility: private\n", "duplicate-header-key"),
    (b"visibility: [public]\n", "ambiguous-privacy-value"),
    (b"metadata: &a {same: *a}\n", "header-event-or-alias-budget"),
    (b"- public\n", "header-must-be-a-mapping"),
    (b"visibility: \xff\n", "invalid-header-encoding"),
    (b"a: [unterminated\n", "invalid-header-yaml"),
])
def test_real_gate_failure_has_only_aggregate_fixed_reason(tmp_path, header, reason):
    hidden = "SYNTHETIC_SENSITIVE_FILENAME.md"
    _repo(tmp_path, {hidden: b"---\n" + header + b"---\nSYNTHETIC_PRIVATE_BODY\n",
                     "public.md": b"public\n"})
    report = inventory.build_repository_text_inventory(tmp_path, set(), {})
    assert report["withheld_reason_counts"] == {reason: 1}
    assert report["status"] == "needs-review"
    assert report["withheld_count"] == 1
    assert report["observed_count"] == 1
    assert report["terminal"] is report["semantic_review_performed"] is False
    rendered = json.dumps(report)
    assert hidden not in rendered and "SYNTHETIC_PRIVATE_BODY" not in rendered


def test_mixed_counts_conserve_scope_without_private_identity(tmp_path):
    _repo(tmp_path, {
        "kept.md": b"public\n", "dirty.md": b"old\n", "gone.md": b"old\n",
        "hidden.md": b"---\nvisibility: private\n---\nCANARY\n",
        "unknown.md": b"---\nvisibility: future\n---\nCANARY\n",
    })
    (tmp_path / "dirty.md").write_bytes(b"new\n")
    (tmp_path / "gone.md").unlink()
    report = inventory.build_repository_text_inventory(tmp_path, set(), {})
    assert report["withheld_reason_counts"] == {
        "body-io-unavailable": 1, "body-not-at-expected-git-blob": 1,
        "unknown-privacy-classification": 1,
    }
    assert sum(report["withheld_reason_counts"].values()) == report["withheld_count"] == 3
    assert report["tracked_text_count"] == 5
    assert report["private_excluded_count"] == report["observed_count"] == 1
    assert [row["path"] for row in report["body_records"]] == ["kept.md"]
    for name in ("dirty.md", "gone.md", "hidden.md", "unknown.md", "CANARY"):
        assert name not in json.dumps(report)
    fingerprint = report.pop("report_sha256")
    encoded = json.dumps(report, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    assert fingerprint == hashlib.sha256(encoded).hexdigest()


def test_declared_private_is_excluded_not_withheld(tmp_path, monkeypatch):
    _repo(tmp_path, {"hidden.md": b"---\nvisibility: private\n---\nCANARY\n"})
    monkeypatch.setattr(inventory, "digest_public_body", lambda *a, **k: pytest.fail("private hashed"))
    report = inventory.build_repository_text_inventory(tmp_path, set(), {})
    assert report["private_excluded_count"] == 1
    assert report["withheld_reason_counts"] == {} and report["withheld_count"] == 0


def test_nonregular_git_entry_is_explained_without_opening(tmp_path, monkeypatch):
    _repo(tmp_path, {"real.txt": b"public\n"})
    (tmp_path / "sensitive-link.md").symlink_to("real.txt")
    _git(tmp_path, "add", "--all")
    _git(tmp_path, "-c", "user.name=Test", "-c", "user.email=t@example.invalid", "commit", "-qm", "link")
    original = inventory.declared_private

    def guard(root, relative):
        assert relative != "sensitive-link.md"
        return original(root, relative)

    monkeypatch.setattr(inventory, "declared_private", guard)
    report = inventory.build_repository_text_inventory(tmp_path, set(), {})
    assert report["withheld_reason_counts"] == {"unsupported-git-entry": 1}
    assert "sensitive-link.md" not in json.dumps(report)


@pytest.mark.parametrize("detail", [
    "SYNTHETIC_PRIVATE_DETAIL", "duplicate-header-key: private/path", "",
    ["duplicate-header-key"], {"private": "value"}, None,
])
def test_arbitrary_details_never_become_reason_keys(detail):
    assert inventory._withheld_reason(BodyPrivacyError(detail)) == "unclassified-body-failure"


def test_exception_context_cycle_is_bounded():
    error = BodyPrivacyError("PRIVATE_DETAIL")
    error.__context__ = error
    assert inventory._withheld_reason(error) == "unclassified-body-failure"


def test_suppressed_wrapper_keeps_only_fixed_inner_code():
    inner = BodyPrivacyError("body-byte-budget")
    outer = BodyPrivacyError("unsafe-or-changing-public-body")
    outer.__context__ = inner
    outer.__suppress_context__ = True
    assert inventory._withheld_reason(outer) == "body-byte-budget"


def test_non_git_does_not_forge_a_zero_withheld_complete_report(tmp_path):
    report = inventory.build_repository_text_inventory(tmp_path, set(), {})
    assert report["status"] == "unavailable"
    assert report["head_inventory_complete"] is False
    assert "withheld_reason_counts" not in report
