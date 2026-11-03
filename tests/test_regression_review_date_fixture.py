"""Calendar fixtures change only their actual temporary scalar and SSOT mirrors."""
import json
from pathlib import Path

import pytest

from tools.codex_assets.knowledge_hub.common import split_frontmatter
from tools.codex_assets.knowledge_hub.regression import support_review_dates


@pytest.mark.parametrize('previous', ['2026-11-07', '2029-12-31'])
def test_dynamic_date_updates_actual_path_and_preserves_every_other_field(tmp_path, previous):
    (tmp_path / 'registry').mkdir()
    (tmp_path / 'indexes').mkdir()
    document = tmp_path / 'projects/renamed/archive/actual.md'
    document.parent.mkdir(parents=True)
    body = '# technical body\nreview_after: untouched narrative\n'
    document.write_text('---\nowner: synthetic-owner\nstatus: reviewing\nreview_after: "' + previous + '"\n---\n' + body)
    row = {'id': 'target', 'path': document.relative_to(tmp_path).as_posix(),
           'owner': 'synthetic-owner', 'status': 'reviewing', 'review_after': previous}
    other = json.dumps({'id': 'other', 'review_after': previous})
    registry = tmp_path / 'registry/items.jsonl'
    registry.write_text(json.dumps(row) + '\n' + other + '\n')
    index = tmp_path / 'indexes/by-review-date.md'
    index.write_text('- ' + previous + ': `target`\n- ' + previous + ': `other`\n')
    support_review_dates.set_fixture_review_after(tmp_path, 'target', '2026-01-01')
    meta, after = split_frontmatter(document.read_text())
    assert meta == {'owner': 'synthetic-owner', 'status': 'reviewing', 'review_after': '2026-01-01'}
    assert after == body
    updated = json.loads(registry.read_text().splitlines()[0])
    assert updated == {**row, 'review_after': '2026-01-01'}
    assert registry.read_text().splitlines()[1] == other
    assert index.read_text() == '- 2026-01-01: `target`\n- ' + previous + ': `other`\n'


def test_missing_or_duplicate_registry_item_never_silently_mutates(tmp_path):
    (tmp_path / 'registry').mkdir()
    path = tmp_path / 'registry/items.jsonl'
    function = support_review_dates.fixture_item
    for rows in ([], [{'id': 'target'}, {'id': 'target'}]):
        original = ''.join(json.dumps(row) + '\n' for row in rows)
        path.write_text(original)
        with pytest.raises(AssertionError, match='one registered item'):
            function(tmp_path, 'target')
        assert path.read_text() == original


@pytest.mark.parametrize('kind', ['absolute', 'parent', 'parent-symlink', 'leaf-symlink'])
def test_unsafe_document_path_rejected_before_read_or_write(tmp_path, monkeypatch, kind):
    repo = tmp_path / 'repo'
    (repo / 'registry').mkdir(parents=True)
    (repo / 'indexes').mkdir()
    outside = tmp_path / 'outside'
    outside.mkdir()
    canary = outside / 'canary.md'
    canary.write_text('---\nreview_after: "2026-11-07"\n---\nexternal canary\n')
    if kind == 'absolute':
        relative = str(canary)
    elif kind == 'parent':
        relative = '../outside/canary.md'
    elif kind == 'parent-symlink':
        (repo / 'linked').symlink_to(outside, target_is_directory=True)
        relative = 'linked/canary.md'
    else:
        (repo / 'linked.md').symlink_to(canary)
        relative = 'linked.md'
    registry = repo / 'registry/items.jsonl'
    registry.write_text(json.dumps({'id': 'target', 'path': relative, 'review_after': '2026-11-07'}) + '\n')
    index = repo / 'indexes/by-review-date.md'
    index.write_text('- 2026-11-07: `target`\n')
    before = {path: path.read_bytes() for path in (canary, registry, index)}
    original = Path.read_bytes

    def guarded(path):
        assert path.resolve() != canary, 'outside canary must not be read'
        return original(path)

    with monkeypatch.context() as guard:
        guard.setattr(Path, 'read_bytes', guarded)
        with pytest.raises(AssertionError, match='unsafe fixture'):
            support_review_dates.set_fixture_review_after(repo, 'target', '2026-01-01')
    assert {path: path.read_bytes() for path in before} == before
