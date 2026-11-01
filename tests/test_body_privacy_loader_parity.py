"""Security parity for the optional C parser; no real private corpus is read."""

import hashlib

import pytest
import yaml

from tools.codex_assets.knowledge_hub import body_privacy as privacy


HEADERS = [
    b'', b'visibility: public\nstatus: active\n',
    'title: 中文与é\ndate: 2026-11-01\nflag: true\nvisibility: public\n'.encode(),
    b'a: &a [one, two]\nb: [*a, *a]\n',
    b'a: &a {visibility: private}\nb: *a\n',
    b'status: personal\n', b'visibility: !!str public\n',
    b'visibility: public\nVisibility: private\n',
    b'a: &a {visibility: private}\n<<: *a\nvisibility: public\n',
    b'a: &a [*a]\n', b'a: &a {self: *a}\n',
    b'a: *unknown\n', b'a: &same one\nb: &same two\n',
    b'visibility: !!python/name:os.system public\n',
    b'a: !!python/object/apply:os.system ["false"]\n',
    b'a: !custom {visibility: public}\n',
    b'visibility: [public]\n', b'visibility: !!bool true\n',
    b'visibility: future-policy\n', b'a: [unclosed\n',
    b'status: active\x00\n', b'\xef\xbb\xbfvisibility: public\n',
]


def classify(header):
    try:
        return ('result', privacy._classify_header(header))
    except privacy.BodyPrivacyError as error:
        return ('privacy-error', str(error))
    except yaml.YAMLError:
        # Public wrappers deliberately replace all parser diagnostics.
        return ('yaml-error',)


@pytest.mark.parametrize('header', HEADERS)
def test_optional_c_and_missing_c_have_identical_classification(header, monkeypatch):
    actual = classify(header)
    monkeypatch.delattr(yaml, 'CSafeLoader', raising=False)
    assert classify(header) == actual


@pytest.mark.parametrize('missing_c', [False, True])
def test_parse_and_compose_share_the_selected_safe_loader(monkeypatch, missing_c):
    if missing_c:
        monkeypatch.delattr(yaml, 'CSafeLoader', raising=False)
    selected = getattr(yaml, 'CSafeLoader', yaml.SafeLoader)
    calls = []
    parse, compose = yaml.parse, yaml.compose

    def checked_parse(text, Loader):
        calls.append(('parse', Loader))
        return parse(text, Loader=Loader)

    def checked_compose(text, Loader):
        calls.append(('compose', Loader))
        return compose(text, Loader=Loader)

    monkeypatch.setattr(yaml, 'parse', checked_parse)
    monkeypatch.setattr(yaml, 'compose', checked_compose)
    assert privacy._classify_header(b'visibility: public\n') is False
    assert calls == [('parse', selected), ('compose', selected)]


def boundary_header(budget, number):
    if budget == 'events':
        return ('a: [' + ','.join('0' for _ in range(number)) + ']').encode()
    if budget == 'aliases':
        return ('a: &a value\nb: [' + ','.join('*a' for _ in range(number)) + ']').encode()
    return ('a: ' + '[' * number + '0' + ']' * number).encode()


@pytest.mark.parametrize('missing_c', [False, True])
@pytest.mark.parametrize('budget', ['events', 'aliases', 'depth'])
def test_exact_existing_budget_boundaries(monkeypatch, missing_c, budget):
    if missing_c:
        monkeypatch.delattr(yaml, 'CSafeLoader', raising=False)
    if budget == 'events':
        scaffold = len(list(yaml.parse('a: []', Loader=yaml.SafeLoader)))
        count = privacy.MAX_HEADER_EVENTS - scaffold
    elif budget == 'aliases':
        count = privacy.MAX_HEADER_ALIASES
    else:
        count = privacy.MAX_HEADER_DEPTH - 1  # The root mapping is a collection.
    assert privacy._classify_header(boundary_header(budget, count)) is False
    with pytest.raises(privacy.BodyPrivacyError):
        privacy._classify_header(boundary_header(budget, count + 1))


@pytest.mark.parametrize('missing_c', [False, True])
def test_recursive_alias_graph_depth_still_fails_closed(monkeypatch, missing_c):
    if missing_c:
        monkeypatch.delattr(yaml, 'CSafeLoader', raising=False)
    monkeypatch.setattr(privacy, 'MAX_HEADER_DEPTH', 4)
    header = b'a: &a [value]\nb: &b [*a]\nc: &c [*b]\nd: &d [*c]\ne: [*d]\n'
    with pytest.raises(privacy.BodyPrivacyError, match='header-depth-budget'):
        privacy._classify_header(header)


@pytest.mark.parametrize('missing_c', [False, True])
@pytest.mark.parametrize('header', HEADERS)
def test_anonymous_public_errors_and_exact_public_hashes(tmp_path, monkeypatch, missing_c, header):
    if missing_c:
        monkeypatch.delattr(yaml, 'CSafeLoader', raising=False)
    data = b'---\n' + header + b'---\nSYNTHETIC_BODY\n'
    path = tmp_path / 'identifying-canary.md'
    path.write_bytes(data)
    try:
        private = privacy.declared_private(tmp_path, path.name)
    except privacy.BodyPrivacyError as error:
        assert str(error) == 'unavailable-or-ambiguous-body-metadata'
        with pytest.raises(privacy.BodyPrivacyError, match='^unsafe-or-changing-public-body$'):
            privacy.digest_public_body(tmp_path, path.name, len(data))
    else:
        if private:
            with pytest.raises(privacy.BodyPrivacyError, match='^unsafe-or-changing-public-body$'):
                privacy.digest_public_body(tmp_path, path.name, len(data))
        else:
            assert privacy.digest_public_body(tmp_path, path.name, len(data)) == (hashlib.sha256(data).hexdigest(), len(data))
    assert path.read_bytes() == data


@pytest.mark.parametrize('missing_c', [False, True])
def test_tagged_objects_never_invoke_construction_or_commands(monkeypatch, missing_c):
    if missing_c:
        monkeypatch.delattr(yaml, 'CSafeLoader', raising=False)
    monkeypatch.setattr(yaml, 'load', lambda *a, **kw: pytest.fail('YAML construction forbidden'))
    monkeypatch.setattr(privacy.os, 'system', lambda *a: pytest.fail('command execution forbidden'))
    with pytest.raises(privacy.BodyPrivacyError):
        privacy._classify_header(b'a: !!python/object/apply:os.system ["false"]\n')
