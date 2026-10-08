import datetime as dt
import json

import pytest

from tools.codex_assets.knowledge_hub.common import KnowledgeHubError
from tools.codex_assets.knowledge_hub.activity_versions import resolve_facts, fact_sha256
from tools.codex_assets.knowledge_hub.activity import collect_work_items, normalize_item
from tools.codex_assets.knowledge_hub.operation_journal import record_stage
from tools.codex_assets.knowledge_hub.runtime_catalog import runtime_catalog
from tools.codex_assets.knowledge_hub.runtime_maintenance import runtime_maintenance_summary
from test_activity_v2 import _hub, _item


def test_orphan_revision_has_explicit_unknown_lineage():
    row = {'item_id':'item', 'revision':9, 'supersedes_sha256':'a' * 64, 'activity_date':'2026-10-06'}
    selected, conflicts, _ = resolve_facts({('subject', 'project', 'item'):[row]})
    assert not selected and conflicts[0]['reason'] == 'lineage-unknown'


def test_cross_day_revision_is_resolved_before_period_projection(tmp_path):
    root = _hub(tmp_path / 'hub')
    directory = root / '.tmp/activity/receipts'
    directory.mkdir(parents=True)
    old = _item(revision=1, observed_at='2026-08-21T01:00:00+00:00')
    normalized = normalize_item(old, source_kind='session-wrap', source_ref='old')
    new = _item(activity_date='2026-08-22', revision=2, supersedes_sha256=fact_sha256(normalized),
                observed_at='2026-08-22T01:00:00+00:00', title='完成修订')
    for name, item in [('old', old), ('new', new)]:
        (directory / (name + '.json')).write_text(json.dumps({'schema_version':2,
            'kind':'activity-session-receipt', 'raw_content_stored':False, 'work_items':[item]}))
    rows, info = collect_work_items(root, dt.date(2026, 8, 22), dt.date(2026, 8, 22))
    assert info['conflict_count'] == 0 and len(rows) == 1 and rows[0]['revision'] == 2


def test_operation_states_cannot_skip_or_regress_and_retries_are_idempotent(tmp_path):
    digest, identity = 'a' * 64, {'operation_id':'b' * 64}
    with pytest.raises(KnowledgeHubError, match='transition'):
        record_stage(tmp_path, digest, 'verified', identity)
    for stage in ['planned', 'gated', 'applied', 'verified']:
        assert record_stage(tmp_path, digest, stage, identity)
        assert record_stage(tmp_path, digest, stage, identity) is False
    with pytest.raises(KnowledgeHubError, match='transition'):
        record_stage(tmp_path, digest, 'planned', identity)
    value = json.loads((tmp_path / '.tmp/governed-provider' / (digest + '.state.json')).read_text())
    assert len(value['events']) == 4 and value['attempt_generation'] == 1


def test_catalog_prioritizes_unknown_operations_and_summary_exposes_overflow(tmp_path):
    for directory in ['.tmp/activity/receipts', '.tmp/governed-provider']:
        (tmp_path / directory).mkdir(parents=True)
    for i in range(3):
        (tmp_path / '.tmp/activity/receipts' / (str(i) + '.json')).write_text('{}')
    (tmp_path / '.tmp/governed-provider/pending.json').write_text('{}')
    report = runtime_catalog(tmp_path, dt.date.today(), maximum_files=2)
    assert report['rows'][0]['category'] == 'governed-provider'
    assert report['overflow'] and not report['deletion_authorized']
    summary = runtime_maintenance_summary({'status':'ready', 'artifact_catalog':report})
    assert summary['artifact_catalog']['overflow']
    assert not summary['artifact_catalog']['categories']['activity-receipts']['scan_complete']


def test_review_state_rejects_large_integer_without_overflow(tmp_path):
    from tools.codex_assets.knowledge_hub.review_state import load_state
    path = tmp_path / 'state.json'
    path.write_text(json.dumps({'item':{'decision':'accepted', 'review_seconds':10 ** 400}}))
    with pytest.raises(KnowledgeHubError):
        load_state(path)


def _failure_fixture(tmp_path):
    from tools.codex_assets.knowledge_hub.common import run_rtk
    from tools.codex_assets.knowledge_hub.engineering_snapshot import capture_snapshot
    from tools.codex_assets.knowledge_hub.snapshot_retention import retain_failure
    root = tmp_path / 'repo'
    root.mkdir()
    run_rtk(root, ['git', 'init'])
    (root / '.gitignore').write_text('.tmp/\nlocal/\n')
    (root / 'source.py').write_text('original\n')
    run_rtk(root, ['git', 'add', '.'])
    run_rtk(root, ['git', '-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid', 'commit', '-m', 'fixture'])
    (root / 'source.py').write_text('dirty\n')
    (root / 'local').mkdir()
    (root / 'local/activity-report.json').write_text('{"fixture":true}\n')
    snapshot = tmp_path / 'snapshot'
    identity = capture_snapshot(root, snapshot)
    retained = retain_failure(root, snapshot, identity, {'status':'fail'})
    return root, snapshot, identity, retained


def test_snapshot_objects_and_retained_dirty_overlay_are_independent(tmp_path):
    from tools.codex_assets.knowledge_hub.common import run_rtk
    root, snapshot, identity, retained = _failure_fixture(tmp_path)
    assert not (snapshot / '.git/objects/info/alternates').exists()
    source_objects = root / '.git/objects'
    source_objects.rename(root / '.git/objects-hidden')
    assert run_rtk(snapshot, ['git', 'cat-file', '-t', identity['head']])['stdout'].strip() == 'commit'
    replay = root / retained['path']
    assert run_rtk(replay, ['git', 'cat-file', '-t', identity['head']])['stdout'].strip() == 'commit'
    assert (replay / 'source.py').read_text() == 'dirty\n'
    assert not (replay / 'local/activity-report.json').exists()


def test_failure_replay_uses_temporary_host_and_preserves_retained_fixture(tmp_path, monkeypatch):
    from tools.codex_assets.knowledge_hub import engineering, snapshot_routing
    from tools.codex_assets.knowledge_hub.snapshot_retention import replay_failure
    root, _, identity, retained = _failure_fixture(tmp_path)
    observed = []
    def execute(execution):
        observed.append(execution)
        assert (execution / 'local/activity-report.json').read_text() == '{"fixture":true}\n'
        assert (execution / 'source.py').read_text() == 'dirty\n'
        return {'status':'pass'}
    monkeypatch.setattr(engineering, 'run_engineering_quality', execute)
    monkeypatch.setattr(snapshot_routing, 'bind_snapshot_route', lambda *args:identity['snapshot_routing'])
    result = replay_failure(root, retained['path'])
    assert result['replayed_source_signature'] == identity['source_signature']
    assert result['live_source_certified'] is False and not observed[0].exists()
    assert not (root / retained['path'] / 'local/activity-report.json').exists()
    (root / 'local/activity-report.json').write_text('{"fixture":false}\n')
    with pytest.raises(KnowledgeHubError, match='original host'):
        replay_failure(root, retained['path'])
    assert len(observed) == 1


@pytest.mark.parametrize('mutation', ['source', 'head', 'inputs', 'host'])
def test_failure_replay_rejects_tampered_identity(tmp_path, mutation):
    from tools.codex_assets.knowledge_hub.snapshot_retention import replay_failure
    root, _, _, retained = _failure_fixture(tmp_path)
    replay = root / retained['path']
    path = replay / '.tmp/replay-manifest.json'
    manifest = json.loads(path.read_text())
    if mutation == 'source':
        (replay / 'source.py').write_text('tampered\n')
    elif mutation == 'head':
        manifest['head'] = 'a' * 40
    elif mutation == 'inputs':
        manifest['inputs'][0]['sha256'] = 'a' * 64
    else:
        manifest['host_inputs'][0]['path'] = 'source.py'
    path.write_text(json.dumps(manifest))
    with pytest.raises(KnowledgeHubError, match='replay'):
        replay_failure(root, retained['path'])


def test_unknown_operation_cannot_be_retried_without_reconciliation(tmp_path):
    digest, identity = 'a' * 64, {'operation_id':'b' * 64}
    for stage in ['planned', 'gated', 'unknown']:
        record_stage(tmp_path, digest, stage, identity)
    assert record_stage(tmp_path, digest, 'unknown', identity) is False
    for stage in ['planned', 'gated', 'applied', 'verified']:
        with pytest.raises(KnowledgeHubError, match='transition'):
            record_stage(tmp_path, digest, stage, identity)


@pytest.mark.parametrize('failure', ['denied', 'missing', 'timeout'])
def test_quality_command_does_not_retry_unknown_or_deterministic_failure(tmp_path, monkeypatch, failure):
    import subprocess
    from tools.codex_assets.knowledge_hub import engineering
    calls = []
    errors = {'denied':KnowledgeHubError('denied command: env'), 'missing':FileNotFoundError('missing executable'),
              'timeout':subprocess.TimeoutExpired(['fixture'], 1)}
    def execute(*args, **kwargs):
        calls.append(1)
        raise errors[failure]
    monkeypatch.setattr(engineering, 'run_rtk', execute)
    result = engineering._run_quality_command(tmp_path, ['fixture'], 1, max_attempts=2, retry_exit_codes=(1,))
    assert len(calls) == result['attempt_count'] == 1 and result['status'] == 'fail'
    assert result['attempts'][0]['retry_eligible'] is False


def test_quality_command_retries_only_explicit_transient_os_error(tmp_path, monkeypatch):
    import errno
    from tools.codex_assets.knowledge_hub import engineering
    calls = []
    def execute(*args, **kwargs):
        calls.append(1)
        if len(calls) == 1:
            raise OSError(errno.EAGAIN, 'fixture temporary resource pressure')
        return {'exit_code':0, 'command':['fixture'], 'duration_sec':0, 'stdout':'', 'stderr':''}
    monkeypatch.setattr(engineering, 'run_rtk', execute)
    result = engineering._run_quality_command(tmp_path, ['fixture'], 1, max_attempts=2)
    assert len(calls) == 2 and result['status'] == 'pass' and result['recovered_after_retry']
    assert result['attempts'][0]['failure_class'] == 'transient-os-error'


@pytest.mark.parametrize('failure', ['invalid-json', 'timeout', 'missing'])
def test_snapshot_retains_source_for_transport_or_output_failure(tmp_path, monkeypatch, failure):
    import shutil
    import subprocess
    from tools.codex_assets.knowledge_hub import engineering_snapshot, engineering_preflight
    root, captured, identity, _ = _failure_fixture(tmp_path)
    def capture(source, destination):
        shutil.copytree(captured, destination)
        return identity
    def execute(*args, **kwargs):
        if failure == 'timeout':
            raise subprocess.TimeoutExpired(['fixture'], 1)
        if failure == 'missing':
            raise FileNotFoundError('fixture missing executable')
        return {'stdout':'invalid-json', 'stderr':'', 'exit_code':1}
    monkeypatch.setattr(engineering_preflight, 'preflight', lambda root, **kwargs:{'status':'pass'})
    monkeypatch.setattr(engineering_snapshot, 'capture_snapshot', capture)
    monkeypatch.setattr(engineering_snapshot, 'run_rtk', execute)
    result = engineering_snapshot.run_snapshot_engineering(root)
    assert result['status'] == 'fail' and result['failure_class'] == 'transport-or-invalid-output'
    assert not result['automatic_retry_performed']
    retained = root / result['failure_replay']['path']
    assert retained.is_dir() and (retained / 'source.py').read_text() == 'dirty\n'
    assert not (retained / 'local/activity-report.json').exists()


def test_preflight_transport_timeout_returns_structured_failure(tmp_path, monkeypatch):
    import subprocess
    from tools.codex_assets.knowledge_hub import engineering_preflight, engineering
    monkeypatch.setattr(engineering, 'evaluate_engineering_contract', lambda root:{'status':'pass'})
    monkeypatch.setattr(engineering_preflight, 'validate_schema_catalog', lambda root:{'status':'pass', 'errors':[]})
    def execute(*args, **kwargs):
        raise subprocess.TimeoutExpired(['fixture'], 30)
    monkeypatch.setattr(engineering_preflight, 'run_rtk', execute)
    result = engineering_preflight.preflight(tmp_path)
    assert result['status'] == result['transport']['status'] == 'fail'
    assert result['expensive_checks_started'] is False


def test_preflight_selects_ci_transport_without_nested_wrapper(tmp_path, monkeypatch):
    from tools.codex_assets.knowledge_hub import engineering_preflight, engineering
    monkeypatch.setattr(engineering, 'evaluate_engineering_contract', lambda root:{'status':'pass'})
    monkeypatch.setattr(engineering_preflight, 'validate_schema_catalog', lambda root:{'status':'pass', 'errors':[]})
    def execute(root, command, **kwargs):
        assert command[0] == engineering._current_python_executable()
        assert 'bash' not in command and 'tools/ci/rtk' not in command
        assert kwargs['extra_env']['PATH'].split(':')[0] == str(root / 'tools/ci')
        return {'exit_code':0}
    monkeypatch.setattr(engineering_preflight, 'run_rtk', execute)
    assert engineering_preflight.preflight(tmp_path)['status'] == 'pass'


def test_quality_nonzero_keeps_failure_predicates_without_retry(tmp_path, monkeypatch):
    from tools.codex_assets.knowledge_hub import engineering
    calls = []
    def execute(root, command, **kwargs):
        calls.append(1)
        assert 1 in kwargs['accepted_exit_codes']
        return {'exit_code':1, 'command':'fixture regression_cli', 'duration_sec':0,
                'stdout':json.dumps({'status':'fail', 'failure_ids':['specific-contract'], 'failures':[]}), 'stderr':''}
    monkeypatch.setattr(engineering, 'run_rtk', execute)
    result = engineering._run_quality_command(tmp_path, ['tools.codex_assets.knowledge_hub.regression_cli'], 1, max_attempts=2)
    assert result['status'] == 'fail' and result['attempt_count'] == len(calls) == 1
    assert result['attempts'][0]['failure_summary']['failure_ids'] == ['specific-contract']
    assert result['attempts'][0]['stdout_tail'] and not result['attempts'][0]['retry_eligible']
