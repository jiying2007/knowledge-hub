"""Synthetic headers: never load real private material to test its exclusion."""
import hashlib
import io
import json
import os

import pytest

from tools.codex_assets.knowledge_hub import body_privacy as privacy
from tools.codex_assets.knowledge_hub import content_convergence as convergence
from tools.codex_assets.knowledge_hub.common import KnowledgeHubError


@pytest.mark.parametrize("header", [
    b"visibility: private\n", b"visibility: personal-local\n", b"status: personal\n",
    b"visibility: 'private' # comment\n", b'"visibility": "PRIVATE"\n',
    b"visibility: team-internal\nstatus: personal\n",
])
def test_private_header_stops_before_body(header):
    class HeaderOnly(io.BytesIO):
        def read(self, *args, **kwargs):
            pytest.fail("a body read is forbidden for this header")

        def readline(self, size=-1):
            line = super().readline(size)
            assert b"SECRET_BODY" not in line
            return line

    private, prefix = privacy._header(HeaderOnly(b"---\n" + header + b"---\nSECRET_BODY\n"))
    assert private is True
    assert prefix == b""


@pytest.mark.parametrize("data", [
    b"Public legacy body.\n", b"", b"---\nvisibility: public\n---\ntext\n",
    b"---\nvisibility: team-internal\nstatus: superseded\n---\ntext\n",
    b"\xef\xbb\xbf---\r\nvisibility: public\r\n---\r\ntext\r\n",
    b"---\nstatus: archived\nrelated:\n  - a.md\n  - b.md\n---\nbody\n",
    b"---\nsummary: >\n  This is a folded summary.\nvisibility: public\n---\nbody\n",
    b"---\nrelated:\n- a.md\n- b.md\nvisibility: public\n---\nbody\n",
])
def test_public_and_authorized_legacy_digest_is_unchanged(tmp_path, data):
    (tmp_path / "body.md").write_bytes(data)
    assert privacy.declared_private(tmp_path, "body.md") is False
    assert privacy.digest_public_body(tmp_path, "body.md", len(data)) == (
        hashlib.sha256(data).hexdigest(), len(data),
    )


@pytest.mark.parametrize("header", [
    b"visibility: public\nvisibility: private\n", b"visibility: [public]\n",
    b"visibility:\n  private\n", b"<<: *defaults\nvisibility: public\n",
    b'"visibil\\u0069ty": private\n', b"? visibility\n: private\n",
    b"{visibility: private}\n", b"visibility: future-policy\n", b"status: future-policy\n",
    b"visibility: |\n  private\n", b"visibility: *alias\n", b"status: !x active\n",
    b"  visibility: private\n", b"status: public\x00\n",
])
def test_ambiguous_metadata_never_reaches_hashing(tmp_path, monkeypatch, header):
    (tmp_path / "body.md").write_bytes(b"---\n" + header + b"---\nbody\n")
    monkeypatch.setattr(privacy.hashlib, "sha256", lambda: pytest.fail("must classify first"))
    with pytest.raises(privacy.BodyPrivacyError):
        privacy.digest_public_body(tmp_path, "body.md", 100000)


def test_indented_delimiter_cannot_end_header_and_hide_private_field(tmp_path):
    data = b"---\nsummary: |\n  ---\nvisibility: private\n---\nSECRET_BODY\n"
    (tmp_path / "body.md").write_bytes(data)
    assert privacy.declared_private(tmp_path, "body.md") is True
    with pytest.raises(privacy.BodyPrivacyError):
        privacy.digest_public_body(tmp_path, "body.md", 100000)


@pytest.mark.parametrize("data", [
    b" ---\nvisibility: private\n---\nbody\n",
    b"---\nvisibility: public\n", b"x" * 4097,
    b"---\nvisibility: public\n" + b"# pad\n" * 12000 + b"---\nbody\n",
    b"---\nvisibility: \xff\n---\nbody\n",
])
def test_bad_or_unbounded_header_is_rejected(tmp_path, data):
    (tmp_path / "body.md").write_bytes(data)
    with pytest.raises(privacy.BodyPrivacyError):
        privacy.digest_public_body(tmp_path, "body.md", len(data) + 1)


@pytest.mark.parametrize("relative", ["../x.md", "./x.md", "a//x.md", "/x.md", "a\\x.md", "x\n.md", ".", ""])
def test_noncanonical_paths_fail_without_opening(tmp_path, monkeypatch, relative):
    monkeypatch.setattr(privacy.os, "open", lambda *a, **k: pytest.fail("invalid path opened"))
    with pytest.raises(privacy.BodyPrivacyError):
        privacy.declared_private(tmp_path, relative)


def test_symlink_and_fifo_are_rejected(tmp_path):
    (tmp_path / "target.md").write_text("public\n", encoding="utf-8")
    (tmp_path / "alias.md").symlink_to(tmp_path / "target.md")
    os.mkfifo(tmp_path / "fifo.md")
    for name in ("alias.md", "fifo.md"):
        with pytest.raises(privacy.BodyPrivacyError):
            privacy.digest_public_body(tmp_path, name, 1000)


@pytest.mark.parametrize("budget", [-1, True, 1.0, 2])
def test_invalid_or_insufficient_budget_fails(tmp_path, budget):
    (tmp_path / "body.md").write_bytes(b"public\n")
    with pytest.raises(privacy.BodyPrivacyError):
        privacy.digest_public_body(tmp_path, "body.md", budget)


def test_change_during_hashing_fails(tmp_path, monkeypatch):
    path = tmp_path / "body.md"
    path.write_bytes(b"header\nbody\n")
    original_header = privacy._header

    def mutate(handle):
        outcome = original_header(handle)
        with path.open("ab") as writer:
            writer.write(b"changed")
        return outcome

    monkeypatch.setattr(privacy, "_header", mutate)
    with pytest.raises(privacy.BodyPrivacyError):
        privacy.digest_public_body(tmp_path, "body.md", 1000)


def _fixture(root):
    (root / "registry").mkdir()
    (root / "registry/items.jsonl").write_text("", encoding="utf-8")
    (root / "registry/sources.json").write_text('{"sources":[]}', encoding="utf-8")
    (root / "registry/retired-sources.jsonl").write_text("", encoding="utf-8")
    return root


def test_unregistered_private_header_never_enters_report(tmp_path):
    _fixture(tmp_path)
    hidden = "hidden-canary.md"
    public = "public.md"
    (tmp_path / hidden).write_bytes(b"---\nvisibility: private\n---\nSECRET_BODY\n")
    (tmp_path / public).write_bytes(b"public\n")
    report = convergence.build_content_convergence(tmp_path, [hidden, public], {}, {})
    assert report["body_count"] == report["uncovered_count"] == 1
    assert report["private_excluded_count"] == 1
    assert report["scope_body_count"] == 2
    assert report["body_records"][0]["path"] == public
    assert report["full_content_review_proven"] is False
    rendered = json.dumps(report)
    assert hidden not in rendered and "SECRET_BODY" not in rendered


def test_registered_public_does_not_override_private_header(tmp_path):
    _fixture(tmp_path)
    path = "conflict.md"
    row = {"id": "canary-id", "path": path, "status": "reviewing", "visibility": "team-internal"}
    (tmp_path / "registry/items.jsonl").write_text(json.dumps(row) + "\n", encoding="utf-8")
    (tmp_path / path).write_bytes(b"---\nvisibility: private\n---\nSECRET_BODY\n")
    report = convergence.build_content_convergence(tmp_path, [path], {path: [row["id"]]}, {})
    assert report["body_count"] == 0 and report["private_excluded_count"] == 1
    assert path not in json.dumps(report) and row["id"] not in json.dumps(report)


def test_metadata_changes_between_summary_and_digest_fail_closed(tmp_path, monkeypatch):
    _fixture(tmp_path)
    target = tmp_path / "body.md"
    target.write_bytes(b"public\n")
    original = convergence.private_body_paths

    def classification_then_change(root, paths):
        result = original(root, paths)
        target.write_bytes(b"---\nvisibility: private\n---\nSECRET_BODY\n")
        return result

    monkeypatch.setattr(convergence, "private_body_paths", classification_then_change)
    with pytest.raises(KnowledgeHubError, match="unsafe or changing"):
        convergence.build_content_convergence(tmp_path, ["body.md"], {}, {})


def test_registry_and_reserved_exclusion_precedes_open(tmp_path, monkeypatch):
    _fixture(tmp_path)
    monkeypatch.setattr(convergence, "declared_private", lambda *a: pytest.fail("private path opened"))
    report = convergence.build_content_convergence(tmp_path, ["notes/personal/absent.md"], {}, {})
    assert report["private_excluded_count"] == 1 and report["body_count"] == 0


def test_segment_negative_controls_stay_non_private(tmp_path):
    _fixture(tmp_path)
    assert convergence.private_body_paths(tmp_path, ["notes/personality/a.md"]) == set()


@pytest.mark.parametrize("status,visibility", [
    ("personal", "team-internal"), ("reviewing", "personal-local"),
])
def test_registry_private_body_never_opens(tmp_path, monkeypatch, status, visibility):
    _fixture(tmp_path)
    row = {"id": "private-id", "path": "restricted/missing.md",
           "status": status, "visibility": visibility}
    (tmp_path / "registry/items.jsonl").write_text(json.dumps(row) + "\n", encoding="utf-8")
    monkeypatch.setattr(convergence, "declared_private", lambda *a: pytest.fail("private opened"))
    result = convergence.build_content_convergence(tmp_path, [row["path"]], {row["path"]: [row["id"]]}, {})
    assert result["private_excluded_count"] == 1
    assert row["path"] not in json.dumps(result) and row["id"] not in json.dumps(result)


def test_registry_private_directory_remains_segment_bound(tmp_path):
    _fixture(tmp_path)
    row = {"id": "private-root", "path": "restricted/private",
           "status": "personal", "visibility": "team-internal"}
    (tmp_path / "registry/items.jsonl").write_text(json.dumps(row) + "\n", encoding="utf-8")
    assert convergence.private_body_paths(tmp_path, ["restricted/private/x.md", "restricted/private-extra/x.md"]) == {"restricted/private/x.md"}


def test_public_duplicate_and_coverage_semantics_stay_unchanged(tmp_path):
    _fixture(tmp_path)
    for name in ("a.md", "b.md", "c.md"):
        (tmp_path / name).write_bytes(b"public duplicate\n")
    result = convergence.build_content_convergence(tmp_path, ["c.md", "a.md", "b.md"], {"a.md": ["a"]}, {"b.md": "frozen"})
    assert result["body_count"] == 3
    assert result["exact_registry_count"] == result["frozen_collection_count"] == result["uncovered_count"] == 1
    assert result["exact_duplicate_candidate_count"] == 1
    assert result["exact_duplicate_candidates"][0]["paths"] == ["a.md", "b.md", "c.md"]
    assert result["canonical_mutations"] == 0
    assert result["full_external_migration_proven"] is False
    assert result == convergence.build_content_convergence(tmp_path, ["b.md", "c.md", "a.md"], {"a.md": ["a"]}, {"b.md": "frozen"})


def test_existing_aggregate_budget_still_rejects(tmp_path, monkeypatch):
    _fixture(tmp_path)
    (tmp_path / "a.md").write_bytes(b"longer than budget\n")
    monkeypatch.setattr(convergence, "MAX_HASH_BYTES", 5)
    with pytest.raises(KnowledgeHubError, match="byte budget"):
        convergence.build_content_convergence(tmp_path, ["a.md"], {}, {})


def test_unknown_registry_privacy_fails_before_any_metadata_open(tmp_path, monkeypatch):
    _fixture(tmp_path)
    (tmp_path / "registry/items.jsonl").write_text('{"path":"x.md","status":"active","visibility":"future"}\n', encoding="utf-8")
    monkeypatch.setattr(convergence, "declared_private", lambda *a: pytest.fail("opened"))
    with pytest.raises(KnowledgeHubError, match="registry privacy"):
        convergence.build_content_convergence(tmp_path, ["x.md"], {}, {})


def test_missing_public_body_remains_an_error(tmp_path):
    _fixture(tmp_path)
    with pytest.raises(KnowledgeHubError, match="canonical body missing"):
        convergence.build_content_convergence(tmp_path, ["absent.md"], {}, {})


def test_duplicate_registry_json_keys_remain_rejected(tmp_path):
    _fixture(tmp_path)
    (tmp_path / "registry/items.jsonl").write_text('{"status":"personal","status":"active"}\n', encoding="utf-8")
    with pytest.raises(KnowledgeHubError, match="duplicate key"):
        convergence.build_content_convergence(tmp_path, [], {}, {})


@pytest.mark.parametrize("line_break", ["\r", "\u0085", "\u2028", "\u2029"])
def test_yaml_line_breaks_do_not_hide_private_field(tmp_path, line_break):
    data = ("---\ntitle: example" + line_break + "visibility: private\n---\nSECRET_BODY\n").encode("utf-8")
    (tmp_path / "body.md").write_bytes(data)
    assert privacy.declared_private(tmp_path, "body.md") is True
    with pytest.raises(privacy.BodyPrivacyError):
        privacy.digest_public_body(tmp_path, "body.md", 10000)


def test_embedded_bom_fails_closed(tmp_path):
    (tmp_path / "body.md").write_text("---\n\ufeffvisibility: private\n---\nSECRET_BODY\n", encoding="utf-8")
    with pytest.raises(privacy.BodyPrivacyError):
        privacy.digest_public_body(tmp_path, "body.md", 10000)


def test_direct_digest_never_opens_reserved_private_path(tmp_path, monkeypatch):
    monkeypatch.setattr(privacy.os, "open", lambda *a, **k: pytest.fail("private path opened"))
    with pytest.raises(privacy.BodyPrivacyError):
        privacy.digest_public_body(tmp_path, "notes/personal/canary.md", 1000)


def test_plain_scalar_continuation_is_not_a_header_delimiter(tmp_path):
    data = b"---\nvisibility: public\nsummary: example\n  ---\nstatus: personal\n---\nSYNTHETIC_CANARY\n"
    (tmp_path / "body.md").write_bytes(data)
    assert privacy.declared_private(tmp_path, "body.md") is True
    with pytest.raises(privacy.BodyPrivacyError):
        privacy.digest_public_body(tmp_path, "body.md", 10000)
