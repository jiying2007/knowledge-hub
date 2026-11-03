import argparse
import hashlib
import json
import pathlib
import subprocess

import pytest

from tools.codex_assets.knowledge_hub import project_migration as migration
from tools.codex_assets.knowledge_hub.common import KnowledgeHubError


def put(root, path, value):
    target = root / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(value if isinstance(value, str) else json.dumps(value))


@pytest.fixture
def sample(tmp_path, monkeypatch):
    root = tmp_path / 'hub'
    root.mkdir()
    subprocess.run(['git', 'init', '-q', str(root)], check=True)
    put(root, '.gitignore', '.tmp/\n')
    put(root, 'registry/projects.json', {'projects': [
        {'id': 'legacy-app', 'name': 'Legacy App', 'evidence_profile': 'embedded-target', 'groups': ['device']},
        {'id': 'new-app', 'name': 'New App', 'evidence_profile': 'knowledge-project', 'groups': []}]})
    put(root, 'registry/project-routes.json', {'routes': [
        {'project_id': 'legacy-app', 'group_id': 'device', 'repo_refs': ['legacy-app']},
        {'project_id': 'new-app', 'group_id': '', 'repo_refs': []}]})
    put(root, 'registry/repositories.json', {'repositories': [
        {'repo_id': 'legacy-app', 'project_id': 'legacy-app', 'aliases': ['new-app']}]})
    put(root, 'registry/provider-grants.jsonl', json.dumps({'id': 'grant-one', 'subject_ref': {'type': 'project', 'id': 'legacy-app'}, 'status': 'active'}) + '\n')
    put(root, 'registry/provider-operations.jsonl', '')
    put(root, 'registry/authorizations.jsonl', '')
    items = []
    for project in ('legacy-app', 'new-app'):
        put(root, f'projects/{project}/README.md', '# ' + project + '\n\n' + project + ' knowledge.\n')
        path = f'projects/{project}/validation/project-readiness.md'
        ident = project + '-project-readiness'
        items.append({'id': ident, 'path': path, 'domain': 'projects/' + project, 'status': 'reviewing'})
        put(root, path, f'---\nid: {ident}\npath: {path}\n---\n# Contract\n\n{project} evidence.\n')
    put(root, 'projects/legacy-app/archive/knowledge.md', '# Field knowledge\n\ncommit abcdef and measured 13 ms.\n')
    items.append({'id': 'stable-record', 'path': 'projects/legacy-app/archive/knowledge.md', 'status': 'archived'})
    put(root, 'registry/items.jsonl', ''.join(json.dumps(r) + '\n' for r in items))
    put(root, 'indexes/by-project.md', 'projects/legacy-app/README.md\n')
    monkeypatch.setattr(migration, 'principal', lambda root: 'test-principal')
    monkeypatch.setattr(migration, 'authorize', lambda *a, **k: None)
    from tools.codex_assets.knowledge_hub import provider_subjects
    monkeypatch.setattr(provider_subjects, 'policy', lambda root: {'actions': ['read', 'assign']})
    from tools.codex_assets.knowledge_hub import provider_grants
    monkeypatch.setattr(provider_grants, 'attested_request', lambda raw, path: ('a' * 64, 'b' * 64))
    return root


def plan(root):
    return migration.build_plan(root, 'project:legacy-app', 'new-app', 'ssh://git@example.test/team/new-app.git')


def args(tmp_path, expected='', apply=False, text='全面迁移，全部闭环落地完成'):
    request = tmp_path / 'request.md'
    request.write_text(text)
    return argparse.Namespace(from_subject='project:legacy-app', project='new-app',
                              remote_url='ssh://git@example.test/team/new-app.git',
                              declaration_file=str(request), expected_content_sha256=expected, apply=apply,
                              authorization_id='migration-test')


def approve(root, expected):
    import datetime as dt
    scope = {'actor': 'test-principal', 'action': 'migrate-project',
             'source_subject_sha256': migration.digest({'type': 'project', 'id': 'legacy-app'}),
             'subject_ref': {'type': 'project', 'id': 'new-app'},
             'remote_key': migration.parse_remote('ssh://git@example.test/team/new-app.git'),
             'expected_hash': expected, 'visibility_change': False}
    put(root, 'registry/authorizations.jsonl', json.dumps({'authorization_id': 'migration-test',
        'authorized_by': 'test-user', 'authorized_at': dt.date.today().isoformat(),
        'expires_at': dt.date.today().isoformat(), 'allowed_actions': ['automation-apply-with-review'],
        'status': 'active', 'scope': json.dumps(scope)}) + '\n')


def test_plan_is_readonly_preserves_every_record_and_resolves_collisions(sample):
    before = {p: p.read_bytes() for p in sample.rglob('*') if p.is_file()}
    result, inputs, writes, deletes, virtual = plan(sample)
    assert result['source_file_count'] == 3 and result['source_item_count'] == 2
    assert all(p.read_bytes() == raw for p, raw in before.items())
    assert 'projects/new-app/validation/knowledge-project-readiness.md' in writes
    assert b'legacy-app' not in b''.join(virtual.values())
    items = [json.loads(line) for line in virtual['registry/items.jsonl'].splitlines()]
    assert len(items) == 3 and len({r['id'] for r in items}) == 3
    assert next(r for r in items if r['id'] == 'stable-record')['status'] == 'archived'
    assert b'commit abcdef and measured 13 ms.' in virtual['projects/new-app/archive/knowledge.md']
    grants = [json.loads(line) for line in virtual['registry/provider-grants.jsonl'].splitlines()]
    assert grants[0]['status'] == 'revoked'


def test_exact_apply_receipt_and_manifest_prove_all_outputs(sample, tmp_path):
    result = plan(sample)[0]
    approve(sample, result['expected_hash'])
    receipt = migration.migrate(sample, args(tmp_path, result['expected_hash'], True))
    assert receipt['status'] == 'MIGRATED' and receipt['persisted'] is True
    assert not (sample / 'projects/legacy-app').exists()
    report = json.loads((sample / receipt['manifest_ref']).read_text())
    assert 'legacy-app' not in json.dumps(report)
    for name, expected in report['result_writes'].items():
        assert hashlib.sha256((sample / name).read_bytes()).hexdigest() == expected
    again = migration.migrate(sample, args(tmp_path, result['expected_hash'], True))
    assert again['status'] == 'ALREADY_MIGRATED' and again['write_performed'] is False


@pytest.mark.parametrize('change', ['wrong-hash', 'changed-input', 'unrelated-request'])
def test_no_write_on_invalid_plan_or_request(sample, tmp_path, change):
    result = plan(sample)[0]
    expected = result['expected_hash']
    approve(sample, expected)
    text = '全面迁移'
    if change == 'wrong-hash':
        expected = '0' * 64
    elif change == 'changed-input':
        put(sample, 'projects/legacy-app/archive/knowledge.md', 'changed user content')
    else:
        text = '只读查看状态'
    before = (sample / 'registry/items.jsonl').read_bytes()
    with pytest.raises(KnowledgeHubError):
        migration.migrate(sample, args(tmp_path, expected, True, text))
    assert (sample / 'registry/items.jsonl').read_bytes() == before
    assert (sample / 'projects/legacy-app').exists()


def test_unknown_collision_fails_without_overwriting(sample):
    put(sample, 'projects/new-app/archive/knowledge.md', 'different existing content')
    with pytest.raises(KnowledgeHubError, match='ROUTE_CONFLICT'):
        plan(sample)
    assert (sample / 'projects/new-app/archive/knowledge.md').read_text() == 'different existing content'


def test_runtime_source_cannot_change_during_provider_call(sample):
    put(sample, 'tools/runtime.py', "PROJECT = 'legacy-app'\n")
    with pytest.raises(KnowledgeHubError, match='RUNTIME_MAINTENANCE_REQUIRED'):
        plan(sample)


def test_source_symlink_is_rejected(sample):
    (sample / 'projects/legacy-app/linked.md').symlink_to('/etc/hosts')
    with pytest.raises(KnowledgeHubError, match='SOURCE_INVENTORY_INCOMPLETE'):
        plan(sample)


def test_proof_chain_is_extended_without_forging_historical_hash(sample):
    path = 'projects/legacy-app/archive/knowledge.md'
    before = hashlib.sha256((sample / path).read_bytes()).hexdigest()
    row = {'schema_version': 4, 'item_id': 'stable-record', 'operation_id': '1' * 64,
           'request_sha256': '1' * 64, 'action': 'archive', 'content_sha256': before,
           'subject_ref': {'type': 'project', 'id': 'legacy-app'},
           'created_subject_ref': {'type': 'project', 'id': 'legacy-app'}}
    put(sample, 'registry/provider-operations.jsonl', json.dumps(row) + '\n')
    # Include the old identity in content so normalization changes its bytes.
    put(sample, path, '# legacy-app knowledge\n')
    row['content_sha256'] = hashlib.sha256((sample / path).read_bytes()).hexdigest()
    put(sample, 'registry/provider-operations.jsonl', json.dumps(row) + '\n')
    result, _, _, _, virtual = plan(sample)
    proofs = [json.loads(line) for line in virtual['registry/provider-operations.jsonl'].splitlines()]
    assert result['provider_proofs'] == 1 and len(proofs) == 2
    assert proofs[0]['content_sha256'] == row['content_sha256']
    assert proofs[-1]['before_content_sha256'] == row['content_sha256']
    assert proofs[-1]['content_sha256'] == hashlib.sha256(virtual['projects/new-app/archive/knowledge.md']).hexdigest()


def test_transaction_failure_restores_original_files(sample, tmp_path, monkeypatch):
    result = plan(sample)[0]
    approve(sample, result['expected_hash'])
    before = {str(p.relative_to(sample)): p.read_bytes() for p in sample.rglob('*')
              if p.is_file() and '.git' not in p.parts and '.tmp' not in p.parts}
    from tools.codex_assets.knowledge_hub import store
    original = store.os.replace
    failed = False
    def interrupted(src, dst):
        nonlocal failed
        if not failed and pathlib.Path(dst) == sample / 'registry/items.jsonl':
            failed = True
            raise OSError('injected write failure')
        return original(src, dst)
    monkeypatch.setattr(store.os, 'replace', interrupted)
    with pytest.raises(KnowledgeHubError):
        migration.migrate(sample, args(tmp_path, result['expected_hash'], True))
    assert failed
    assert all((sample / name).read_bytes() == content for name, content in before.items())


def test_ignored_knowledge_is_detected_before_writes(sample):
    put(sample, '.gitignore', '.tmp/\nprojects/legacy-app/private.md\n')
    put(sample, 'projects/legacy-app/private.md', 'must never be omitted')
    with pytest.raises(KnowledgeHubError, match='SOURCE_INVENTORY_INCOMPLETE'):
        plan(sample)


def test_executable_path_rename_is_rejected(sample):
    put(sample, 'tools/legacy-app.py', 'print(1)\n')
    with pytest.raises(KnowledgeHubError, match='RUNTIME_MAINTENANCE_REQUIRED'):
        plan(sample)


def test_readonly_host_cannot_migrate(sample, tmp_path, monkeypatch):
    from tools.codex_assets.knowledge_hub import provider_subjects
    monkeypatch.setattr(provider_subjects, 'policy', lambda root: {'actions': ['read']})
    expected = plan(sample)[0]['expected_hash']
    approve(sample, expected)
    with pytest.raises(KnowledgeHubError, match='POLICY_DENIED'):
        migration.migrate(sample, args(tmp_path, expected, True))


def test_exact_approval_is_required_and_cannot_cover_another_plan(sample, tmp_path):
    expected = plan(sample)[0]['expected_hash']
    with pytest.raises(KnowledgeHubError):
        migration.migrate(sample, args(tmp_path, expected, True))
    approve(sample, '0' * 64)
    with pytest.raises(KnowledgeHubError, match='POLICY_DENIED'):
        migration.migrate(sample, args(tmp_path, expected, True))


def test_historical_human_proof_is_retained_but_not_reapproved(sample):
    path = sample / 'registry/items.jsonl'
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    rows[0].update(human_review_content_sha256='a' * 64,
                   human_review_decision='accept-as-review-record', content_review_status='accepted')
    path.write_text(''.join(json.dumps(row) + '\n' for row in rows))
    result, _, _, _, virtual = plan(sample)
    after = next(row for row in map(json.loads, virtual['registry/items.jsonl'].splitlines())
                 if row.get('human_review_content_sha256'))
    assert after['human_review_content_sha256'] == 'a' * 64
    assert after['human_review_decision'] == 'defer' and after['content_review_status'] == 'pending'
    assert result['prior_review_evidence'][0]['kind'] == 'prior-content-review'


def test_no_collision_readiness_link_uses_actual_destination(sample):
    (sample / 'projects/new-app/validation/project-readiness.md').unlink()
    path = sample / 'registry/items.jsonl'
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    path.write_text(''.join(json.dumps(row) + '\n' for row in rows if row['path'] != 'projects/new-app/validation/project-readiness.md'))
    _, _, _, _, virtual = plan(sample)
    assert b'](validation/project-readiness.md)' in virtual['projects/new-app/README.md']


def test_changed_ai_authority_is_sealed_and_current_credential_detached(sample):
    authority = {'authorization_id': 'review-one', 'scope': 'legacy-app content',
                 'authorization_statement': 'legacy-app historical review'}
    raw = json.dumps(authority)
    put(sample, 'registry/ai-content-review-authorizations.jsonl', raw + '\n')
    path = sample / 'registry/items.jsonl'
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    rows[0]['ai_delegated_content_review'] = {'authorization_id': 'review-one'}
    path.write_text(''.join(json.dumps(row) + '\n' for row in rows))
    result, _, _, _, virtual = plan(sample)
    assert virtual['registry/ai-content-review-authorizations.jsonl'] == b''
    after = [json.loads(line) for line in virtual['registry/items.jsonl'].splitlines()]
    assert all('ai_delegated_content_review' not in row for row in after)
    historical = next(row for row in result['prior_review_evidence'] if row['kind'] == 'prior-delegated-authority')
    assert historical['original_sha256'] == hashlib.sha256(raw.encode()).hexdigest()
    assert historical['historical_validation_verified'] is False


def test_migration_cannot_detach_active_review(sample):
    path = sample / 'registry/items.jsonl'
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    rows[0].update(status='active', human_review_content_sha256='a' * 64,
                   human_review_decision='accept-as-review-record', content_review_status='accepted')
    path.write_text(''.join(json.dumps(row) + '\n' for row in rows))
    with pytest.raises(KnowledgeHubError, match='ACTIVE_REVIEW_REVALIDATION_REQUIRED'):
        plan(sample)


def test_uppercase_workspace_variable_is_normalized(sample):
    put(sample, 'registry/workspaces.example.json', {'env': 'LEGACY_APP_HOME', 'path_example': '$LEGACY_APP_HOME'})
    _, _, _, _, virtual = plan(sample)
    value = json.loads(virtual['registry/workspaces.example.json'])
    assert value == {'env': 'NEW_APP_HOME', 'path_example': '$NEW_APP_HOME'}


def test_unrecognized_mixed_case_identity_cannot_silently_survive(sample):
    put(sample, 'registry/workspaces.example.json', {'env': 'LeGaCy_App_HOME'})
    with pytest.raises(KnowledgeHubError, match='CONTENT_DRIFT'):
        plan(sample)
