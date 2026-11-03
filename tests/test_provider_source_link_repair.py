import copy
import argparse
import json

import pytest

from tools.codex_assets.knowledge_hub import provider_maintenance as maintenance
from tools.codex_assets.knowledge_hub.common import KnowledgeHubError, load_markdown, render_markdown
from test_provider_maintenance import sample as _sample_fixture

sample = _sample_fixture


def test_exact_missing_source_link_becomes_explicit_unmapped_pointer(sample):
    root, request, item = sample
    source = root / item['path']
    metadata, body = load_markdown(source)
    literal = '[来源方案](source-plan.md)'
    body += '\n' + literal + '\n'
    source.write_text(render_markdown(metadata, body))
    entry = request['items'][0]
    entry.pop('target_path')
    entry['expected_sha256'] = maintenance.sha(source.read_bytes())
    entry['link_repairs'] = [{'start': body.index(literal), 'end': body.index(literal) + len(literal),
                              'sha256': maintenance.sha(literal.encode())}]
    plan, _, writes, _ = maintenance.build_plan(root, request)
    assert '来源方案（来源内引用：`source-plan.md`；尚未映射为 Hub 链接）'.encode() in writes[item['path']]
    assert plan['body_redactions'][-1]['kind'] == 'unresolved-source-links'
    assert plan['owner_review_performed'] is False


@pytest.mark.parametrize('literal', ['plain text', '[x](https://example.test/x)', '[x](/private/path)', '[x](#anchor)',
                                    '[x](../../../outside.md)', '[x](existing.md)', '[x](bad`target.md)'])
def test_cannot_repair_arbitrary_text_or_existing_external_targets(tmp_path, literal):
    (tmp_path / 'projects/p').mkdir(parents=True)
    (tmp_path / 'projects/p/existing.md').write_text('existing')
    repair = {'start': 0, 'end': len(literal), 'sha256': maintenance.sha(literal.encode())}
    with pytest.raises(KnowledgeHubError):
        maintenance.repair_unresolved_source_links(tmp_path, 'projects/p/note.md', literal, [repair])


def test_hash_drift_duplicate_span_and_conflicting_body_edits_fail_closed(sample):
    root, request, item = sample
    literal = '[x](missing.md)'
    repair = {'start': 0, 'end': len(literal), 'sha256': '0' * 64}
    with pytest.raises(KnowledgeHubError, match='CONTENT_DRIFT'):
        maintenance.repair_unresolved_source_links(root, item['path'], literal, [repair])
    repair['sha256'] = maintenance.sha(literal.encode())
    with pytest.raises(KnowledgeHubError, match='CONTENT_DRIFT'):
        maintenance.repair_unresolved_source_links(root, item['path'], literal, [repair, copy.deepcopy(repair)])


@pytest.mark.parametrize('body', [
    '`[x](missing.md)`', '``[x](missing.md)``',
    '```text\n[x](missing.md)\n```\n', '~~~\n[x](missing.md)\n~~~\n',
    '> ```text\n> [x](missing.md)\n> ```\n',
    '- ```text\n  [x](missing.md)\n  ```\n',
    '- > ~~~text\n  > [x](missing.md)\n  > ~~~\n',
    '> - > ```text\n>   > [x](missing.md)\n>   > ```\n',
    '1. > ~~~text\n   > [x](missing.md)\n   > ~~~\n',
    '\\[x](missing.md)', '![x](missing.md)',
    '    [x](missing.md)\n', '\t[x](missing.md)\n',
    '>     [x](missing.md)\n', '-     [x](missing.md)\n',
    '`unclosed\n[x](missing.md)', '```text\n[x](missing.md)\n',
    '<!-- [x](missing.md) -->', '<!--\n[x](missing.md)\n',
    '<pre>[x](missing.md)</pre>', '<code>[x](missing.md)</code>',
    '<SCRIPT>\n[x](missing.md)\n</SCRIPT>',
    '<style>[x](missing.md)</style>', '<textarea>[x](missing.md)</textarea>',
])
def test_non_link_markdown_contexts_cannot_be_rewritten(tmp_path, body):
    (tmp_path / 'projects/p').mkdir(parents=True)
    literal = '[x](missing.md)'
    start = body.index(literal)
    repair = {'start': start, 'end': start + len(literal), 'sha256': maintenance.sha(literal.encode())}
    with pytest.raises(KnowledgeHubError, match='POLICY_DENIED'):
        maintenance.repair_unresolved_source_links(tmp_path, 'projects/p/note.md', body, [repair])


def test_valid_link_next_to_code_preserves_every_other_character(tmp_path):
    (tmp_path / 'projects/p').mkdir(parents=True)
    literal = '[来源](missing.md)'
    body = '中文前缀 `code [example](other.md)`，' + literal + '\n```text\n[x](code.md)\n```\n'
    start = body.index(literal)
    repair = {'start': start, 'end': start + len(literal), 'sha256': maintenance.sha(literal.encode())}
    repaired = maintenance.repair_unresolved_source_links(tmp_path, 'projects/p/note.md', body, [repair])
    replacement = '来源（来源内引用：`missing.md`；尚未映射为 Hub 链接）'
    assert repaired == body[:start] + replacement + body[start + len(literal):]


def test_exact_grant_is_separate_and_maintenance_checks_its_scope(sample, tmp_path, monkeypatch):
    from tools.codex_assets.knowledge_hub import provider_maintenance_authorization as grants
    root, request, item = sample
    (root / 'local').mkdir()
    (root / 'local/provider-principal.json').write_text('{}')
    (root / 'registry/provider-subject-policy.json').write_text('{}')
    monkeypatch.setattr(grants, 'principal', lambda *a: 'test-user')
    monkeypatch.setattr(grants, 'policy', lambda *a: {'actions': ['assign']})
    monkeypatch.setattr(grants, 'attested_request', lambda *a: ('a' * 64, 'b' * 64))
    declaration = tmp_path / 'request.md'
    declaration.write_text('全部优化落地')
    original = (root / item['path']).read_bytes()
    grant_request = {'schema_version': grants.SCHEMA, 'request': request}
    args = argparse.Namespace(apply=False, expected_content_sha256='', declaration_file=str(declaration))
    planned = grants.record(root, args, grant_request)
    args.apply, args.expected_content_sha256 = True, planned['expected_hash']
    granted = grants.record(root, args, grant_request)
    assert granted['persisted'] is True and granted['item_count'] == 0
    assert (root / item['path']).read_bytes() == original
    source = tmp_path / 'maintenance.json'
    source.write_text(json.dumps(request))
    args.source, args.authorization_id = str(source), granted['authorization_id']
    args.expected_content_sha256 = granted['application_expected_hash']
    result = maintenance.maintain(root, args)
    assert result['persisted'] is True and result['owner_review_performed'] is False


def test_unattested_grant_cannot_persist(sample, tmp_path, monkeypatch):
    from tools.codex_assets.knowledge_hub import provider_maintenance_authorization as grants
    root, request, _ = sample
    (root / 'local').mkdir()
    (root / 'local/provider-principal.json').write_text('{}')
    (root / 'registry/provider-subject-policy.json').write_text('{}')
    monkeypatch.setattr(grants, 'principal', lambda *a: 'test-user')
    monkeypatch.setattr(grants, 'policy', lambda *a: {'actions': ['assign']})
    def unverified(*a):
        raise KnowledgeHubError('DECLARATION_UNATTESTED')
    monkeypatch.setattr(grants, 'attested_request', unverified)
    declaration = tmp_path / 'request.md'
    declaration.write_text('全部优化落地')
    request = {'schema_version': grants.SCHEMA, 'request': request}
    args = argparse.Namespace(apply=False, expected_content_sha256='', declaration_file=str(declaration))
    plan = grants.record(root, args, request)
    args.apply, args.expected_content_sha256 = True, plan['expected_hash']
    before = (root / 'registry/authorizations.jsonl').read_bytes()
    with pytest.raises(KnowledgeHubError, match='DECLARATION_UNATTESTED'):
        grants.record(root, args, request)
    assert (root / 'registry/authorizations.jsonl').read_bytes() == before
