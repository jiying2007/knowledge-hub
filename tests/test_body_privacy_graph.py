"""Bounded YAML graph checks use synthetic headers, never real private bodies."""
import hashlib
import io

import pytest

from tools.codex_assets.knowledge_hub import body_privacy as privacy


@pytest.mark.parametrize("header", [
    b"metadata:\n  visibility: private\n",
    b"provenance:\n  status: personal\n",
    b"visibility: public\nmetadata: {visibility: personal-local}\n",
    b"entries:\n- metadata: {visibility: PRIVATE}\n",
    b"flags: &flags {visibility: private}\nmetadata: *flags\n",
    b"private_value: &value private\nmetadata: {visibility: *value}\n",
    b"v: &value personal\nmetadata: {status: *value}\n",
    b"a: &a [{visibility: private}]\nb: [*a, *a]\n",
])
def test_nested_private_header_stops_before_body(header, tmp_path, monkeypatch):
    class HeaderOnly(io.BytesIO):
        def readline(self, size=-1):
            line = super().readline(size)
            assert b"SYNTHETIC_BODY" not in line
            return line

        def read(self, *args, **kwargs):
            pytest.fail("private body was read")

    data = b"---\n" + header + b"---\nSYNTHETIC_BODY\n"
    assert privacy._header(HeaderOnly(data)) == (True, b"")
    (tmp_path / "test.md").write_bytes(data)
    monkeypatch.setattr(privacy.hashlib, "sha256", lambda: pytest.fail("private body was hashed"))
    assert privacy.declared_private(tmp_path, "test.md") is True
    with pytest.raises(privacy.BodyPrivacyError):
        privacy.digest_public_body(tmp_path, "test.md", len(data))


@pytest.mark.parametrize("header", [
    b"visibility: public\nrelated: &refs [a.md, b.md]\nvalidation_refs: *refs\n",
    b"metadata: &meta {status: completed, visibility: team-internal}\ncopy: *meta\n",
    b"v: &v public\nvisibility: *v\n",
    b"status: archived\nresult: {status: passed}\n",
    b"summary: >\n  Example with words.\n  ---\nvisibility: public\n",
    b"a: &a [one, two]\nb: &b [*a, *a]\nc: [*b, *b]\n",
])
def test_safe_acyclic_aliases_preserve_exact_bytes(tmp_path, header):
    data = b"---\n" + header + b"---\nPublic body.\n"
    (tmp_path / "test.md").write_bytes(data)
    assert privacy.declared_private(tmp_path, "test.md") is False
    assert privacy.digest_public_body(tmp_path, "test.md", len(data)) == (
        hashlib.sha256(data).hexdigest(), len(data),
    )


@pytest.mark.parametrize("header", [
    b"a: &a [*a]\n",
    b"a: &a {child: *a}\n",
    b"a: &a {visibility: private}\n<<: *a\nvisibility: public\n",
    b"a: &a {visibility: private}\nmetadata: {<<: *a, visibility: public}\n",
    b"metadata: {visibility: public, Visibility: private}\n",
    b"metadata: {visibility: future-policy}\n",
    b"metadata: {visibility: [public]}\n",
    b"metadata: {status: [personal]}\n",
    b"a: *not_defined\n",
    b"a: &a value\nb: &a other\n",
    b"metadata: !custom {visibility: public}\n",
    b"metadata: !custom [public]\n",
    b"status: future-policy\n",
])
def test_ambiguous_graph_is_not_hashed(tmp_path, header, monkeypatch):
    data = b"---\n" + header + b"---\nSYNTHETIC_BODY\n"
    (tmp_path / "test.md").write_bytes(data)
    monkeypatch.setattr(privacy.hashlib, "sha256", lambda: pytest.fail("unsafe body hashed"))
    with pytest.raises(privacy.BodyPrivacyError):
        privacy.digest_public_body(tmp_path, "test.md", len(data))


def test_alias_budget_is_bounded(tmp_path, monkeypatch):
    monkeypatch.setattr(privacy, "MAX_HEADER_ALIASES", 3)
    path = tmp_path / "test.md"
    path.write_bytes(b"---\na: &a value\nb: [*a, *a, *a]\n---\nbody\n")
    assert privacy.declared_private(tmp_path, path.name) is False
    path.write_bytes(b"---\na: &a value\nb: [*a, *a, *a, *a]\n---\nbody\n")
    with pytest.raises(privacy.BodyPrivacyError):
        privacy.declared_private(tmp_path, path.name)


def test_event_budget_remains_enforced(tmp_path, monkeypatch):
    monkeypatch.setattr(privacy, "MAX_HEADER_EVENTS", 5)
    path = tmp_path / "test.md"
    path.write_bytes(b"---\na: one\nb: two\n---\nbody\n")
    with pytest.raises(privacy.BodyPrivacyError):
        privacy.declared_private(tmp_path, path.name)


def test_alias_graph_depth_is_checked_not_only_syntax(tmp_path, monkeypatch):
    monkeypatch.setattr(privacy, "MAX_HEADER_DEPTH", 4)
    data = b"---\na: &a [value]\nb: &b [*a]\nc: &c [*b]\nd: &d [*c]\ne: [*d]\n---\nbody\n"
    path = tmp_path / "test.md"
    path.write_bytes(data)
    with pytest.raises(privacy.BodyPrivacyError):
        privacy.declared_private(tmp_path, path.name)
