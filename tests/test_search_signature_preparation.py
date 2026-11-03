"""Instance preparation reuses parsing, never the bounded input read or its proof."""

import json
import os

import pytest

from test_search_index_cold import corpus
from tools.codex_assets.knowledge_hub import common, search_core, search_index


def test_same_captured_bytes_are_parsed_once_per_instance(tmp_path, monkeypatch):
    root = corpus(tmp_path)
    index = search_index.SearchIndex(root)
    parse = search_index._governed_paths_from_bytes
    read = search_index.read_repository_bytes_bounded
    parsed, reads = [], []

    def capture(root, raw):
        parsed.append(raw)
        return parse(root, raw)

    def fresh(*args):
        raw = read(*args)
        reads.append(raw)
        return raw

    monkeypatch.setattr(search_index, '_governed_paths_from_bytes', capture)
    monkeypatch.setattr(search_index, 'read_repository_bytes_bounded', fresh)
    first = index._signature_for_index()
    assert index._signature_for_index(previous_states=first[2]) == first
    assert len(reads) == 2 and parsed == reads[:1]
    assert search_index.SearchIndex(root)._signature_for_index() == first
    assert len(parsed) == 2
    mapping = index._governed_preparation[1]
    assert mapping['README.md'] == ()
    with pytest.raises(TypeError):
        mapping['other.md'] = ()


@pytest.mark.parametrize('raw', [b'', b'\n {"id":"x"}\r\n\n', b'{}\n{', b'\n[]\n', b'\xff'])
def test_captured_jsonl_matches_existing_parser(tmp_path, raw):
    root = corpus(tmp_path)
    path = root / 'registry/items.jsonl'
    path.write_bytes(raw)

    def outcome(call):
        try:
            return call()
        except common.KnowledgeHubError as exc:
            return type(exc), str(exc)

    assert outcome(lambda: search_core._registry_rows_from_bytes(root, raw)) == outcome(lambda: common.registry_items(root))


def test_prepared_and_default_complete_signature_match(tmp_path, monkeypatch):
    root = corpus(tmp_path)
    raw = (root / 'registry/items.jsonl').read_bytes()
    mapping = search_core._governed_paths_from_bytes(root, raw)
    expected = search_core._signature(root)
    assert search_core._signature(root, prepared_items_by_path=mapping,
                                  prepared_registry_sha256=common.bytes_sha256(raw)) == expected
    (root / 'registry/items.jsonl').write_text('')
    monkeypatch.setattr(search_core, '_governed_items_by_path', lambda root: pytest.fail('empty prepared map must not reread'))
    assert search_core._signature(root, prepared_items_by_path={},
                                  prepared_registry_sha256=common.bytes_sha256(b''))[1] == []


@pytest.mark.parametrize('reuse', [False, True])
def test_final_dependency_digest_rejects_mixed_registry_generation(tmp_path, reuse):
    root = corpus(tmp_path)
    _, _, states = search_core._signature(root)
    with pytest.raises(search_core.SearchBoundaryError, match='changed during signature preparation'):
        search_core._signature(root, previous_states=states if reuse else None,
                               prepared_items_by_path={'README.md': ()}, prepared_registry_sha256='0' * 64)


def test_mutation_after_capture_cannot_bind_old_map_to_new_dependency(tmp_path, monkeypatch):
    root = corpus(tmp_path)
    index = search_index.SearchIndex(root)
    parse = search_index._governed_paths_from_bytes

    def mutate(root, raw):
        mapping = parse(root, raw)
        row = json.loads(raw)
        row['searchable'] = False
        (root / 'registry/items.jsonl').write_text(json.dumps(row) + '\n')
        return mapping

    monkeypatch.setattr(search_index, '_governed_paths_from_bytes', mutate)
    with pytest.raises(search_core.SearchBoundaryError, match='changed during signature preparation'):
        index._signature_for_index()
    assert index._governed_preparation is None


def test_preparation_never_reopens_registry_for_parsing(tmp_path, monkeypatch):
    root = corpus(tmp_path)
    expected = search_core._signature(root)
    monkeypatch.setattr(search_core, 'registry_items', lambda root: pytest.fail('parse must consume captured bytes'))
    assert search_index.SearchIndex(root)._signature_for_index() == expected


def test_same_size_mtime_tamper_is_detected_by_fresh_content_key(tmp_path):
    root = corpus(tmp_path)
    index = search_index.SearchIndex(root)
    before = index._signature_for_index()
    path = root / 'registry/items.jsonl'
    file_stat = path.stat()
    path.write_bytes(path.read_bytes().replace(b'Example', b'Changed'))
    os.utime(path, ns=(file_stat.st_atime_ns, file_stat.st_mtime_ns))
    assert path.stat().st_size == file_stat.st_size
    # Some filesystems can preserve all identity fields within one clock tick.
    # An old dependency digest must then fail closed, never return stale input.
    try:
        after = index._signature_for_index(previous_states=before[2])
    except search_core.SearchBoundaryError as exc:
        assert 'changed during signature preparation' in str(exc)
        after = index._signature_for_index()
    assert after == search_core._signature(root)
    assert after[0] != before[0]


def test_parent_symlink_is_rejected_even_with_cached_registry(tmp_path):
    root = corpus(tmp_path)
    index = search_index.SearchIndex(root)
    index._signature_for_index()
    (root / 'registry').rename(root / 'other-registry')
    (root / 'registry').symlink_to(root / 'other-registry', target_is_directory=True)
    with pytest.raises(search_core.SearchBoundaryError):
        index._signature_for_index()


@pytest.mark.parametrize('mutation', ['invalid', 'duplicate', 'private', 'hidden', 'replace', 'oversize', 'symlink'])
def test_fresh_registry_changes_are_never_hidden_by_cache(tmp_path, mutation):
    root = corpus(tmp_path)
    index = search_index.SearchIndex(root)
    original = index._signature_for_index()
    path = root / 'registry/items.jsonl'
    raw = path.read_bytes()
    row = json.loads(raw)
    if mutation == 'invalid':
        path.write_bytes(b'{')
    elif mutation == 'duplicate':
        path.write_bytes(raw + raw)
    elif mutation == 'oversize':
        path.write_bytes(b' ' * (search_core.SEARCH_MAX_FILE_BYTES + 1))
    elif mutation == 'symlink':
        target = root / 'other.jsonl'
        path.rename(target)
        path.symlink_to(target)
    elif mutation == 'replace':
        replacement = root / 'new.jsonl'
        replacement.write_bytes(raw)
        replacement.replace(path)
    else:
        row.update({'visibility': 'personal-local'} if mutation == 'private' else {'searchable': False})
        path.write_text(json.dumps(row) + '\n')
    if mutation in {'invalid', 'duplicate', 'oversize', 'symlink'}:
        with pytest.raises(search_core.SearchBoundaryError):
            index._signature_for_index(previous_states=original[2])
    else:
        result = index._signature_for_index(previous_states=original[2])
        assert result == search_core._signature(root, previous_states=original[2])
        if mutation != 'replace':
            assert result[1] == [] and result[0] != original[0]


def test_force_and_permission_failure_do_not_reuse_preparation(tmp_path, monkeypatch):
    root = corpus(tmp_path)
    index = search_index.SearchIndex(root)
    expected = index._signature_for_index()
    monkeypatch.setattr(search_index, '_governed_paths_from_bytes', lambda *args: pytest.fail('force uses original path'))
    assert index._signature_for_index(force=True) == expected

    def denied(*args):
        raise PermissionError('denied')

    monkeypatch.setattr(search_index, 'read_repository_bytes_bounded', denied)
    with pytest.raises(search_core.SearchBoundaryError, match='denied'):
        index._signature_for_index(previous_states=expected[2])
