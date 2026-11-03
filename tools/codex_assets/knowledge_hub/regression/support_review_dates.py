"""Temporary calendar fixture support, outside generated case shards."""

import json
import re


def fixture_path(repo, relative):
    """Reject fixture paths outside the temporary root or through symlinks."""
    relative = type(repo)(relative)
    assert not relative.is_absolute() and '..' not in relative.parts, 'unsafe fixture path'
    base = repo.resolve()
    candidate = base
    for part in relative.parts:
        candidate = candidate / part
        assert not candidate.is_symlink(), 'unsafe fixture symlink'
    assert candidate.resolve().is_relative_to(base), 'unsafe fixture path'
    return candidate


def fixture_item(repo, item_id):
    rows = [json.loads(line) for line in fixture_path(repo, 'registry/items.jsonl').read_text().splitlines() if line.strip()]
    matches = [row for row in rows if row.get('id') == item_id]
    assert len(matches) == 1, 'fixture must select one registered item'
    return matches[0]


def set_fixture_review_after(repo, item_id, value):
    """Mutate only the temporary item's actual scalar and matching registry/index."""
    from ..common import split_frontmatter
    row = fixture_item(repo, item_id)
    body_path = fixture_path(repo, row['path'])
    registry = fixture_path(repo, 'registry/items.jsonl')
    index = fixture_path(repo, 'indexes/by-review-date.md')
    text = body_path.read_bytes().decode('utf-8')
    metadata, body = split_frontmatter(text)
    assert str(metadata['review_after']) == row['review_after']
    marker = text.index('\n---\n', 4)
    header, count = re.subn(r'(?m)^review_after:[^\n]*$',
                            'review_after: ' + json.dumps(value), text[:marker])
    assert count == 1, 'fixture review_after must have one actual frontmatter scalar'
    updated = header + text[marker:]
    changed_metadata, changed_body = split_frontmatter(updated)
    assert changed_metadata['review_after'] == value and changed_body == body
    assert {key: item for key, item in metadata.items() if key != 'review_after'} == {
        key: item for key, item in changed_metadata.items() if key != 'review_after'}
    body_path.write_text(updated)
    lines = []
    for line in registry.read_text().splitlines():
        item = json.loads(line) if line.strip() else {}
        if item.get('id') == item_id:
            item['review_after'] = value
            line = json.dumps(item, ensure_ascii=False, separators=(',', ':'))
        lines.append(line)
    registry.write_text('\n'.join(lines) + '\n')
    index_text, count = re.subn(r'(?m)^- \d{4}-\d{2}-\d{2}: `' + re.escape(item_id) + r'`$',
                               '- ' + value + ': `' + item_id + '`', index.read_text())
    assert count == 1, 'fixture review index must contain one matching item'
    index.write_text(index_text)
    assert fixture_item(repo, item_id)['review_after'] == changed_metadata['review_after']
