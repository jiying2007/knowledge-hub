"""Cold index construction avoids a discarded scan without bypassing validation."""

import contextlib
import json

from tools.codex_assets.knowledge_hub import search_index


def corpus(tmp_path):
    (tmp_path / 'registry').mkdir()
    (tmp_path / 'README.md').write_text('# Example\n\nSearchable body.\n')
    item = {'id': 'example', 'title': 'Example', 'path': 'README.md',
            'kind': 'standard', 'domain': 'root', 'status': 'reviewing',
            'owner': 'fixture', 'tags': ['example']}
    (tmp_path / 'registry/items.jsonl').write_text(json.dumps(item) + '\n')
    (tmp_path / 'registry/sources.json').write_text('{"sources": []}\n')
    (tmp_path / 'registry/retired-sources.jsonl').write_text('')
    return tmp_path


def test_cold_index_scans_once_under_exclusive_lock_then_warm_validates(tmp_path, monkeypatch):
    root = corpus(tmp_path)
    index = search_index.SearchIndex(root)
    original = search_index._signature
    signatures = []

    def signature(*args, **kwargs):
        result = original(*args, **kwargs)
        signatures.append(result[0])
        return result

    monkeypatch.setattr(search_index, '_signature', signature)
    cold = index.ensure()
    assert cold['state'] == 'rebuilt' and cold['lock_mode'] == 'exclusive'
    assert signatures == [cold['signature']]
    warm = index.ensure()
    assert warm['state'] == 'warm' and warm['lock_mode'] == 'shared'
    assert signatures == [cold['signature'], cold['signature']]
    (root / 'README.md').write_text('# Example\n\nChanged searchable body.\n')
    changed = index.ensure()
    assert changed['signature'] != cold['signature']
    assert changed['updated'] or changed['rebuilt']


def test_creator_before_exclusive_lock_is_validated_and_reused(tmp_path, monkeypatch):
    root = corpus(tmp_path)
    index = search_index.SearchIndex(root)
    original_lock = index._lock
    created = []

    @contextlib.contextmanager
    def lock(exclusive=True):
        if exclusive and not created:
            created.append(search_index.SearchIndex(root).ensure())
        with original_lock(exclusive=exclusive):
            yield

    def forbidden_rebuild(*args, **kwargs):
        raise AssertionError('the concurrent creator index should be validated and reused')

    monkeypatch.setattr(index, '_lock', lock)
    monkeypatch.setattr(index, '_rebuild', forbidden_rebuild)
    result = index.ensure()
    assert result['state'] == 'warm' and result['lock_mode'] == 'exclusive'
    assert result['signature'] == created[0]['signature']


def test_force_keeps_exclusive_rebuild_and_complete_signature(tmp_path, monkeypatch):
    root = corpus(tmp_path)
    index = search_index.SearchIndex(root)
    original = index.ensure()
    signature = search_index._signature
    calls = []

    def observed(*args, **kwargs):
        result = signature(*args, **kwargs)
        calls.append(result[0])
        return result

    monkeypatch.setattr(search_index, '_signature', observed)
    result = index.ensure(force=True)
    assert result['rebuilt'] and result['lock_mode'] == 'exclusive'
    assert result['signature'] == original['signature']
    assert calls == [original['signature']]
