import datetime as dt
import hashlib
import json

import pytest

from test_activity_v2 import _hub
from test_optimization_closure import _receipt
from tools.codex_assets.knowledge_hub.common import KnowledgeHubError, run_rtk, working_tree_signature
from tools.codex_assets.knowledge_hub.activity import capture_receipt
from tools.codex_assets.knowledge_hub.activity_versions import resolve_facts, fact_sha256, version_fields
from tools.codex_assets.knowledge_hub.check_dependencies import dependency_fingerprints, cache_safe, cached_check
from tools.codex_assets.knowledge_hub.review_state import load_state
from tools.codex_assets.knowledge_hub.review_batches import build_review_batches
from tools.codex_assets.knowledge_hub.private_io import atomic_private_write, PrivateWriteUncertain
from tools.codex_assets.knowledge_hub import private_io
from tools.codex_assets.knowledge_hub.engineering_snapshot import capture_snapshot
from tools.codex_assets.knowledge_hub.runtime_catalog import runtime_catalog
from tools.codex_assets.knowledge_hub.retrieval_diagnostics import development_diagnostics
from test_provider_archive import setup
from tools.codex_assets.knowledge_hub.provider_archive import archive
from tools.codex_assets.knowledge_hub.common import registry_items
from tools.codex_assets.knowledge_hub.review_batches import record_consumption, prepare_review_batches
from tools.codex_assets.knowledge_hub import retrieval_cli, retrieval_holdout
from tools.codex_assets.knowledge_hub.provider_reconcile import reconcile_archive, reconcile_activity


def test_root_python_is_a_cache_dependency(tmp_path):
    run_rtk(tmp_path, ['git', 'init'])
    path = tmp_path / 'root_input.py'
    path.write_text('x = 1\n')
    before = dependency_fingerprints(tmp_path)['kernel']
    path.write_text('x = "wrong"\n')
    assert dependency_fingerprints(tmp_path)['kernel'] != before
    (tmp_path / 'mypy.ini').write_text('[mypy]\nplugins = external_plugin\n')
    assert not cache_safe(tmp_path, 'mypy')


@pytest.mark.parametrize('key', ['files', 'modules', 'packages', 'mypy_path', 'plugins'])
def test_explicit_mypy_dependencies_disable_cache(tmp_path, key):
    (tmp_path / 'mypy.ini').write_text('[mypy]\n' + key + ' = .tmp/input.py\n')
    assert not cache_safe(tmp_path, 'mypy')


@pytest.mark.parametrize('value', [[], 7, None, {'schema_version':2}])
def test_operation_journal_rejects_invalid_schema(tmp_path, value):
    from tools.codex_assets.knowledge_hub.operation_journal import record_stage
    digest = 'a' * 64
    path = tmp_path / '.tmp/governed-provider' / (digest + '.state.json')
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(value))
    with pytest.raises(KnowledgeHubError):
        record_stage(tmp_path, digest, 'unknown', {})


def test_unordered_activity_conflict_does_not_choose_filename_order():
    key = ('subject', 'project', 'item')
    old = {'status':'in_progress', 'item_id':'item'}
    new = dict(old, status='done')
    selected, conflicts, _ = resolve_facts({key:[new, old]})
    assert selected == [] and len(conflicts) == 1
    old.update(version_fields({'revision':1, 'observed_at':'2026-10-01T00:00:00Z'}))
    new.update(version_fields({'revision':2, 'supersedes_sha256':fact_sha256(old), 'observed_at':'2026-10-02T00:00:00Z'}))
    assert resolve_facts({key:[new, old]})[0] == [new]
    assert resolve_facts({key:[new, old]}, '2026-10-01T12:00:00Z')[0] == [old]


@pytest.mark.parametrize('value', [[], 7, None, {'entries':[]}])
def test_malformed_review_state_is_rejected(tmp_path, value):
    path = tmp_path / 'state.json'
    path.write_text(json.dumps(value))
    with pytest.raises(KnowledgeHubError):
        load_state(path)


def test_invalid_cache_timestamp_is_a_miss(tmp_path):
    path = tmp_path / '.cache/knowledge-hub/checks/mypy.json'
    path.parent.mkdir(parents=True)
    result = {'status':'pass'}
    path.write_text(json.dumps({'identity':'id', 'generated_at':7, 'result':result,
                               'result_sha256':hashlib.sha256(json.dumps(result, sort_keys=True).encode()).hexdigest()}))
    assert cached_check(tmp_path, 'mypy', 'id') is None


def test_same_content_retry_repairs_directory_sync(tmp_path, monkeypatch):
    path = tmp_path / 'private/value.json'
    original = private_io._sync_directory
    calls = []
    def fail_once(directory):
        calls.append(directory)
        if len(calls) == 1:
            raise OSError('injected directory sync failure')
        original(directory)
    monkeypatch.setattr(private_io, '_sync_directory', fail_once)
    with pytest.raises(PrivateWriteUncertain):
        atomic_private_write(path, 'value', immutable=True)
    assert path.read_text() == 'value'
    atomic_private_write(path, 'value', immutable=True)
    assert len(calls) == 2


def test_receipt_dry_run_rejects_stale_cas_and_retains_history(tmp_path):
    root = _hub(tmp_path / 'hub')
    source = tmp_path / 'receipt.json'
    _receipt(source, 'first', 'explicit-session')
    first = capture_receipt(root, source, apply=True)
    _receipt(source, 'second', 'explicit-session')
    with pytest.raises(KnowledgeHubError, match='expected hash'):
        capture_receipt(root, source, apply=False, expected_sha256='0' * 64)
    capture_receipt(root, source, apply=True, expected_sha256=first['sha256'])
    history = list((root / '.tmp/activity/receipt-history').rglob('*.json'))
    assert len(history) == 1 and hashlib.sha256(history[0].read_bytes()).hexdigest() == first['sha256']


def test_snapshot_captures_dirty_untracked_deleted_without_long_lock(tmp_path):
    root = tmp_path / 'repo'
    root.mkdir()
    run_rtk(root, ['git', 'init'])
    (root / 'a.py').write_text('before\n')
    (root / 'deleted.py').write_text('deleted\n')
    run_rtk(root, ['git', 'add', '.'])
    run_rtk(root, ['git', '-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid', 'commit', '-m', 'fixture'])
    (root / 'a.py').write_text('dirty\n')
    (root / 'deleted.py').unlink()
    (root / 'new.py').write_text('new\n')
    snapshot = tmp_path / 'snapshot'
    identity = capture_snapshot(root, snapshot)
    assert working_tree_signature(root) == working_tree_signature(snapshot) == identity['source_signature']
    assert identity['writer_lock_released_before_tests']
    assert snapshot.stat().st_mode & 0o777 == 0o700
    assert (snapshot / 'a.py').read_text() == 'dirty\n'
    assert not (snapshot / 'deleted.py').exists()


@pytest.mark.parametrize('credential', [False, True])
def test_snapshot_preserves_registered_routing_without_credentials(tmp_path, credential):
    root = tmp_path / 'repo'
    root.mkdir()
    run_rtk(root, ['git', 'init'])
    (root / 'registry').mkdir()
    row = {'remote_key':'team/hub', 'repo_id':'hub', 'project_id':'hub', 'workspace_ref':'~/hub'}
    (root / 'registry/repositories.json').write_text(json.dumps({'repositories':[row]}))
    (root / '.gitignore').write_text('local/workspaces.json\n.tmp/\n')
    run_rtk(root, ['git', 'add', '.'])
    run_rtk(root, ['git', '-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid', 'commit', '-m', 'fixture'])
    url = 'https://user:secret@example.invalid/team/hub.git' if credential else 'https://example.invalid/team/hub.git'
    run_rtk(root, ['git', 'remote', 'add', 'origin', url])
    snapshot = tmp_path / 'snapshot'
    if credential:
        with pytest.raises(KnowledgeHubError, match='credential'):
            capture_snapshot(root, snapshot)
    else:
        identity = capture_snapshot(root, snapshot)
        assert identity['snapshot_routing']['repo_id'] == 'hub'
        assert working_tree_signature(root) == working_tree_signature(snapshot)
        binding = json.loads((snapshot / 'local/workspaces.json').read_text())['workspaces'][0]
        assert binding['repo_id'] == 'hub' and binding['snapshot_view_only']
        from tools.codex_assets.knowledge_hub.schemas import validate_instance
        from pathlib import Path
        assert validate_instance(Path(__file__).resolve().parents[1], 'local-workspaces-v1',
                                 json.loads((snapshot / 'local/workspaces.json').read_text()))['status'] == 'pass'


def test_snapshot_artifact_rejects_existing_leaf_symlink(tmp_path, monkeypatch):
    from tools.codex_assets.knowledge_hub import engineering_snapshot
    from tools.codex_assets.knowledge_hub import engineering_preflight
    monkeypatch.setattr(engineering_preflight, 'preflight', lambda root, **kwargs:{'status':'pass'})
    root = tmp_path / 'live'
    dist = root / '.tmp/engineering/dist'
    dist.mkdir(parents=True)
    outside = tmp_path / 'outside.whl'
    outside.write_bytes(b'preserve')
    (dist / 'artifact.whl').symlink_to(outside)
    def capture(source, snapshot):
        source_dist = snapshot / '.tmp/engineering/dist'
        source_dist.mkdir(parents=True)
        (source_dist / 'artifact.whl').write_bytes(b'new-build')
        return {'source_signature':'sig', 'inputs':[], 'host_inputs':[]}
    monkeypatch.setattr(engineering_snapshot, 'capture_snapshot', capture)
    monkeypatch.setattr(engineering_snapshot, 'run_rtk', lambda *a, **k:{'stdout':json.dumps({'status':'pass', 'candidate_integrity':{'after_signature':'sig'}})})
    with pytest.raises(KnowledgeHubError, match='symlink'):
        engineering_snapshot.run_snapshot_engineering(root)
    assert outside.read_bytes() == b'preserve'


def test_runtime_catalog_protects_unknown_and_reports_overflow(tmp_path):
    directory = tmp_path / '.tmp/governed-provider'
    directory.mkdir(parents=True)
    (directory / 'operation.json').write_text('{}')
    (directory / 'other.json').write_text('{}')
    report = runtime_catalog(tmp_path, dt.date.today(), maximum_files=1)
    assert report['overflow'] and report['report_only'] and not report['deletion_authorized']
    assert report['rows'][0]['protected_reason'] == 'unknown-operation-state'


def test_review_wip_is_bounded_and_next_action_is_explicit():
    rows = [dict(item_id=str(i), path='a.md', owner='owner', status='reviewing', days_until_review=-60)
            for i in range(5)]
    batch = build_review_batches(rows, 5, owner_wip_limit=2)['batches'][0]
    assert batch['selected_count'] == 2 and batch['cold_count'] == 5
    assert all(row['next_action'] and row['responsible_owner'] == 'owner' for row in batch['rows'])


def test_diagnostic_rejects_frozen_validation():
    with pytest.raises(KnowledgeHubError, match='development'):
        development_diagnostics({'dataset_role':'frozen-validation'}, {})


def test_regression_failure_retains_predicates_beyond_stdout_tail():
    from tools.codex_assets.knowledge_hub.engineering import _retain_regression_failure
    failure = {'id':'date-selection', 'details':{'final_exit_code':1, 'parse_errors':[],
                                              'final_selection':{}, 'warnings':['warning'] * 100}}
    result = {'exit_code':1, 'stdout':json.dumps({'status':'fail', 'failure_ids':['date-selection'],
                                               'failures':[failure], 'failures_truncated':False})}
    attempt = {}
    _retain_regression_failure(['tools.codex_assets.knowledge_hub.regression_cli'], result, attempt)
    assert attempt['failure_summary']['failures'][0]['details']['final_selection'] == {}
    assert attempt['failure_summary']['failure_ids'] == ['date-selection']


def test_diagnostic_preserves_actual_retrieved_identity():
    dataset = {'cases':[{'id':'case'}]}
    measured = {'cases':[{'id':'case', 'query':'Obsidian', 'forbidden_hits':[], 'hit':True,
                         'rank':1, 'ranked':[{'item_id':'actual-item'}]}]}
    report = development_diagnostics(dataset, measured)
    assert report['rows'][0]['returned_ids'] == ['actual-item']


def test_accepted_consumption_expires_and_cycle_changes_reopen(tmp_path):
    root, _, args = setup(tmp_path)
    receipt = archive(root, args)
    rows = [dict(item_id=receipt['item_id'], path=receipt['target'], owner='owner', status='reviewing')]
    record_consumption(root, receipt['item_id'], 'accepted', 'explicit-reviewer', 'proof', receipt['content_sha256'], apply=True)
    items = registry_items(root)
    assert prepare_review_batches(root, rows, items)['owner_count'] == 0
    assert prepare_review_batches(root, rows, items, as_of=dt.date(2030, 1, 1))['reopened_count'] == 1
    items[0]['evidence_validation_status'] = 'changed'
    assert prepare_review_batches(root, rows, items)['reopened_count'] == 1
    state = root / '.tmp/review-consumption/state.json'
    state.write_text(json.dumps({receipt['item_id']:{'decision':'deferred', 'next_review_at':[]}}))
    packet = prepare_review_batches(root, rows, items)
    assert packet['consumption_state_status'] == 'needs-review' and packet['owner_count'] == 1


def test_holdout_cli_respects_flags_and_quality_gate(tmp_path, monkeypatch, capsys):
    called = {}
    monkeypatch.setattr(retrieval_cli, 'repository_root', lambda:tmp_path)
    def evaluate(root, path, **kwargs):
        called.update(kwargs)
        return {'status':'fail', 'verbose':'should-be-hidden'}
    monkeypatch.setattr(retrieval_holdout, 'evaluate_holdout', evaluate)
    monkeypatch.setattr(retrieval_holdout, 'holdout_summary', lambda value:{'status':value['status']})
    assert retrieval_cli.main(['--holdout', '--quality-gate', '--top-k', '1', '--min-hit-rate', '0.5', '--summary-json']) == 1
    assert called['top_k'] == 1 and called['minimum_hit_rate'] == 0.5
    assert json.loads(capsys.readouterr().out) == {'status':'fail'}
    assert retrieval_cli.main(['--holdout']) == 0


def test_public_reconcile_is_readonly_and_requires_exact_hash(tmp_path):
    root, _, args = setup(tmp_path)
    receipt = archive(root, args)
    result = reconcile_archive(root, args.project, receipt['operation_id'], receipt['content_sha256'])
    assert result['status'] == 'VERIFIED' and result['read_only'] and not result['durable_acknowledgement']
    assert reconcile_archive(root, args.project, receipt['operation_id'], '0' * 64)['status'] != 'VERIFIED'
    activity_root = _hub(tmp_path / 'activity')
    source = tmp_path / 'receipt.json'
    _receipt(source, 'item', 'session-reconcile')
    first = capture_receipt(activity_root, source, apply=True)
    result = reconcile_activity(activity_root, 'session-reconcile', '2026-08-21', first['sha256'])
    assert result['status'] == 'VERIFIED' and result['read_only']
