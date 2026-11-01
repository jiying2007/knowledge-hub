"""Validated body reuse never bypasses a fresh bounded Markdown read."""
import os

import pytest

from tools.codex_assets.knowledge_hub import content_quality as quality
from tools.codex_assets.knowledge_hub.common import load_markdown


def outcome(call):
    try:
        return ('ok', call())
    except Exception as exc:
        return (type(exc), str(exc))


@pytest.mark.parametrize('text', [
    '', '正文\n', '---\ntitle: 测试\n---\n\n正文\n',
    '---\r\ntitle: yes\r\n---\r\n正文\r\n', '\ufeff---\nx: y\n---\n正文',
    '---\nx: [\n---\nbody', '---\nx: y', '---\n- value\n---\nbody',
    '---\nx: !!python/object:unknown {}\n---\nbody',
    '---\nx: &a [one]\ny: [' + ','.join(['*a'] * 65) + ']\n---\nbody',
    '---\nx: ' + '[' * 66 + '0' + ']' * 66 + '\n---\nbody',
    '---\nx: [' + ','.join(['0'] * 10001) + ']\n---\nbody',
])
def test_complete_parse_and_error_parity(tmp_path, text):
    path = tmp_path / 'record.md'
    path.write_bytes(text.encode('utf-8'))
    batch = quality.ValidatedBodyBatch()
    expected = outcome(lambda: load_markdown(path))
    assert outcome(lambda: batch.load(path)) == expected
    body_expected = expected if expected[0] != 'ok' else ('ok', expected[1][1])
    assert outcome(lambda: batch.body(path)) == body_expected


def test_hit_reads_again_but_does_not_parse_or_expose_metadata(tmp_path, monkeypatch):
    path = tmp_path / 'record.md'
    path.write_text('---\nx: [one]\n---\nbody')
    batch = quality.ValidatedBodyBatch()
    meta, body = batch.load(path)
    meta['x'].append('mutated')
    original = quality.read_utf8_bounded
    reads = []

    def read(*args):
        reads.append(args[0])
        return original(*args)

    monkeypatch.setattr(quality, 'read_utf8_bounded', read)
    monkeypatch.setattr(quality, 'split_frontmatter', lambda _: pytest.fail('cache hit parsed'))
    assert batch.body(path) == body
    assert reads == [path]
    assert isinstance(batch._bodies[path][1], str)


@pytest.mark.parametrize('replacement', [b'other', b'---\nx: [\n---\nbody', b'\xff'])
def test_same_stat_changes_never_reuse_old_body(tmp_path, replacement):
    path = tmp_path / 'record.md'
    path.write_bytes(b'first')
    batch = quality.ValidatedBodyBatch()
    batch.load(path)
    before = path.stat()
    path.write_bytes(replacement)
    os.utime(path, ns=(before.st_atime_ns, before.st_mtime_ns))
    expected = outcome(lambda: load_markdown(path))
    assert outcome(lambda: batch.body(path)) == (
        expected if expected[0] != 'ok' else ('ok', expected[1][1]))


@pytest.mark.parametrize('change', ['missing', 'symlink', 'permission', 'oversize'])
def test_fresh_read_failure_boundaries(tmp_path, monkeypatch, change):
    path = tmp_path / 'record.md'
    path.write_text('body')
    batch = quality.ValidatedBodyBatch()
    batch.load(path)
    if change == 'missing':
        path.unlink()
    elif change == 'symlink':
        other = tmp_path / 'other.md'
        other.write_text('other')
        path.unlink()
        path.symlink_to(other)
    elif change == 'permission':
        path.chmod(0)
    else:
        from tools.codex_assets.knowledge_hub import common
        monkeypatch.setattr(quality, 'DEFAULT_MARKDOWN_MAX_BYTES', 3)
        monkeypatch.setattr(common, 'DEFAULT_MARKDOWN_MAX_BYTES', 3)
    expected = outcome(lambda: load_markdown(path))
    assert outcome(lambda: batch.body(path)) == (
        expected if expected[0] != 'ok' else ('ok', expected[1][1]))


@pytest.mark.parametrize('max_bytes,max_entries,cached', [(6, 1, True), (5, 1, False), (6, 0, False)])
def test_exact_budgets_and_transparent_fallback(tmp_path, monkeypatch, max_bytes, max_entries, cached):
    path = tmp_path / 'record.md'
    path.write_text('中文')  # six UTF-8 bytes, not two characters
    batch = quality.ValidatedBodyBatch(max_bytes, max_entries)
    batch.load(path)
    original = quality.split_frontmatter
    calls = []

    def split(text):
        calls.append(text)
        return original(text)

    monkeypatch.setattr(quality, 'split_frontmatter', split)
    assert batch.body(path) == '中文'
    assert bool(calls) is not cached
    assert batch._bytes <= max_bytes
    assert len(batch._bodies) <= max_entries


def test_entry_limit_replacement_and_new_batch(tmp_path, monkeypatch):
    first, second = tmp_path / 'one.md', tmp_path / 'two.md'
    first.write_text('one')
    second.write_text('two')
    batch = quality.ValidatedBodyBatch(max_bytes=6, max_entries=1)
    batch.load(first)
    batch.load(second)
    assert set(batch._bodies) == {first}
    first.write_text('longer than budget')
    assert batch.body(first) == 'longer than budget'
    assert not batch._bodies
    assert batch._bytes == 0
    original = quality.split_frontmatter
    calls = []

    def split(text):
        calls.append(text)
        return original(text)

    monkeypatch.setattr(quality, 'split_frontmatter', split)
    assert quality.ValidatedBodyBatch().body(second) == 'two'
    assert calls == ['two']


def test_findings_complete_order_with_injected_reader(tmp_path):
    from test_content_quality_batch import corpus
    items = corpus(tmp_path)
    batch = quality.ValidatedBodyBatch()
    for item in items:
        batch.load(tmp_path / item['path'])
    assert quality.findings(tmp_path, items, body_reader=batch.body) == quality.findings(tmp_path, items)


def test_total_byte_budget_and_replacement_accounting(tmp_path):
    first, second, third = [tmp_path / name for name in ('one.md', 'two.md', 'three.md')]
    first.write_text('中文')
    second.write_text('body')
    third.write_text('x')
    batch = quality.ValidatedBodyBatch(max_bytes=10, max_entries=3)
    for path in (first, second, third):
        batch.load(path)
    assert set(batch._bodies) == {first, second}
    assert batch._bytes == 10
    first.write_text('a')
    batch.load(first)
    assert batch._bytes == 5
    batch.load(third)
    assert batch._bytes == 6
    assert set(batch._bodies) == {first, second, third}


def test_cached_hit_cannot_hide_fresh_oserror(tmp_path, monkeypatch):
    from tools.codex_assets.knowledge_hub import common
    path = tmp_path / 'record.md'
    path.write_text('body')
    batch = quality.ValidatedBodyBatch()
    batch.load(path)

    def failed(*_args):
        raise PermissionError('synthetic denied')

    monkeypatch.setattr(quality, 'read_utf8_bounded', failed)
    monkeypatch.setattr(common, 'read_utf8_bounded', failed)
    assert outcome(lambda: batch.body(path)) == outcome(lambda: load_markdown(path))


def test_noneligible_load_still_validates_without_retaining_body(tmp_path):
    path = tmp_path / 'record.md'
    path.write_text('---\nx: [one]\n---\nbody')
    batch = quality.ValidatedBodyBatch()
    assert batch.load(path, retain_body=False) == load_markdown(path)
    assert batch._bytes == 0 and batch._bodies == {}
    path.write_text('---\nx: [\n---\nbody')
    assert outcome(lambda: batch.load(path, retain_body=False)) == outcome(lambda: load_markdown(path))
