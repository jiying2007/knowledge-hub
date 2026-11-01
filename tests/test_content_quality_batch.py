"""Batch template reuse preserves findings and single-call parsing boundaries."""

from collections import Counter

import pytest

from tools.codex_assets.knowledge_hub import content_quality
from tools.codex_assets.knowledge_hub.common import KnowledgeHubError


def corpus(tmp_path):
    templates = tmp_path / 'templates'
    templates.mkdir()
    (templates / 'README.md').write_text('---\ninvalid: [\n---\n\nignored\n')
    (templates / 'one.md').write_text('---\ntitle: One\n---\n\nTemplate one\n')
    (templates / 'two.md').write_text('---\ntitle: Two\n---\n\nTemplate two\n')
    project = tmp_path / 'projects/one/current'
    project.mkdir(parents=True)
    items = []
    for index, body in enumerate(('Template one', 'Evidence body', 'Template two', 'Template one')):
        path = project / ('item-{}.md'.format(index))
        path.write_text('# ' + body + '\n' if index == 1 else body + '\n')
        items.append({'id': str(index), 'path': str(path.relative_to(tmp_path)),
                      'status': 'archived' if index == 2 else 'reviewing',
                      'searchable': False if index == 3 else True})
    return items


def legacy_findings(root, items):
    result = []
    for item in items:
        path = root / item.get('path', '')
        if not str(item.get('path', '')).startswith('projects/') or not path.is_file() or path.suffix != '.md':
            continue
        _, body = content_quality.load_markdown(path)
        if content_quality.template_body(root, body) and item.get('searchable') is not False:
            result.append('template-body:' + item['path'])
        if '/current/' in item['path'] and item.get('status') in {'archived', 'superseded', 'rejected'}:
            result.append('terminal-in-current:' + item['path'])
    return result


def test_batch_results_match_legacy_and_templates_load_once(tmp_path, monkeypatch):
    items = corpus(tmp_path)
    expected = legacy_findings(tmp_path, items)
    counts = Counter()
    load = content_quality.load_markdown

    def counted(path):
        counts[path] += 1
        return load(path)

    monkeypatch.setattr(content_quality, 'load_markdown', counted)
    assert content_quality.findings(tmp_path, items) == expected
    assert counts[tmp_path / 'templates/one.md'] == 1
    assert counts[tmp_path / 'templates/two.md'] == 1
    assert counts[tmp_path / 'templates/README.md'] == 0


def test_next_batch_and_public_call_read_changed_template(tmp_path):
    items = corpus(tmp_path)
    before = content_quality.findings(tmp_path, items)
    (tmp_path / 'templates/one.md').write_text('Updated template\n')
    assert not content_quality.template_body(tmp_path, 'Template one')
    after = content_quality.findings(tmp_path, items)
    assert after == legacy_findings(tmp_path, items)
    assert after != before


def test_no_eligible_items_does_not_parse_templates(tmp_path, monkeypatch):
    corpus(tmp_path)

    def forbidden(path):
        raise AssertionError('no Markdown should be read')

    monkeypatch.setattr(content_quality, 'load_markdown', forbidden)
    assert content_quality.findings(tmp_path, [{'path': 'missing.md'}]) == []


def test_lazy_short_circuit_preserves_template_error_boundary(tmp_path, monkeypatch):
    items = corpus(tmp_path)
    first = tmp_path / 'templates/one.md'
    bad = tmp_path / 'templates/bad.md'
    bad.write_text('---\nbroken: [\n---\n')
    glob = type(tmp_path).glob

    def ordered(path, pattern):
        return iter([first, bad]) if path == tmp_path / 'templates' else glob(path, pattern)

    monkeypatch.setattr(type(tmp_path), 'glob', ordered)
    assert content_quality.findings(tmp_path, items[:1]) == legacy_findings(tmp_path, items[:1])
    with pytest.raises(KnowledgeHubError, match='invalid YAML frontmatter'):
        content_quality.findings(tmp_path, items[:2])
