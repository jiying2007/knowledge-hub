import argparse
import json
import os
import pathlib
import subprocess
import sys
import time
import datetime as dt

import pytest

from test_provider_archive import setup
from test_activity_v2 import _hub, _item
from tools.codex_assets.knowledge_hub import obsidian_view, governed_provider_cli, observability_runtime
from tools.codex_assets.knowledge_hub.activity import capture_receipt
from tools.codex_assets.knowledge_hub.common import KnowledgeHubError, registry_items
from tools.codex_assets.knowledge_hub.provider_archive import archive
from tools.codex_assets.knowledge_hub.schemas import validate_instance
from tools.codex_assets.knowledge_hub.store import audit_transactions, WriteConflict
from tools.codex_assets.knowledge_hub.private_io import atomic_private_write
from tools.codex_assets.knowledge_hub.bounded_process import run_bounded
from tools.codex_assets.knowledge_hub.product_gate_parallel import _unit_result
from tools.codex_assets.knowledge_hub.natural_query import normalize_question
from tools.codex_assets.knowledge_hub.candidate_duplicates import duplicate_hints, content_fingerprint
from tools.codex_assets.knowledge_hub.review_batches import build_review_batches, prepare_review_batches, record_consumption
from tools.codex_assets.knowledge_hub.check_dependencies import dependency_fingerprints, check_identity, store_check, cached_check


def test_obsidian_rejects_interleaved_archive_and_keeps_new_navigation(tmp_path, monkeypatch):
    root, _, args = setup(tmp_path)
    archive(root, args)
    second = tmp_path / 'second.md'
    second.write_text('# 第二个候选\n\n另一项结论。\n')
    other_args = argparse.Namespace(**vars(args))
    other_args.source = str(second)
    original = obsidian_view.registry_items
    added = {}

    def interleaved(value):
        old = original(value)
        monkeypatch.setattr(obsidian_view, 'registry_items', original)
        added.update(archive(root, other_args))
        return old

    monkeypatch.setattr(obsidian_view, 'registry_items', interleaved)
    with pytest.raises(WriteConflict):
        obsidian_view.build_obsidian_views(root, apply=True)
    assert added['item_id'] in (root / 'indexes/obsidian/catalog.md').read_text()
    assert len(registry_items(root)) == 2


def _receipt(path, item_id, receipt_id=None):
    payload = dict(schema_version=2, kind='activity-session-receipt', session_date='2026-08-21',
                   work_items=[_item(item_id=item_id)], raw_content_stored=False)
    if receipt_id:
        payload['receipt_id'] = receipt_id
    path.write_text(json.dumps(payload))


def test_same_basename_receipts_preserve_both_and_retry_is_idempotent(tmp_path):
    root = _hub(tmp_path / 'hub')
    path = tmp_path / 'receipt.json'
    _receipt(path, 'first')
    first = capture_receipt(root, path, apply=True)
    assert capture_receipt(root, path, apply=True)['target'] == first['target']
    _receipt(path, 'second')
    second = capture_receipt(root, path, apply=True)
    assert first['target'] != second['target']
    assert json.loads(pathlib.Path(first['target']).read_text())['work_items'][0]['item_id'] == 'first'


def test_explicit_receipt_identity_conflict_and_compare_swap_revision(tmp_path):
    root = _hub(tmp_path / 'hub')
    path = tmp_path / 'receipt.json'
    _receipt(path, 'first', 'session-a')
    first = capture_receipt(root, path, apply=True)
    _receipt(path, 'second', 'session-a')
    with pytest.raises(KnowledgeHubError, match='identity conflict'):
        capture_receipt(root, path, apply=True)
    second = capture_receipt(root, path, apply=True, expected_sha256=first['sha256'])
    assert first['target'] == second['target']
    with pytest.raises(KnowledgeHubError, match='expected hash'):
        capture_receipt(root, path, apply=True, expected_sha256=first['sha256'])


@pytest.mark.parametrize('key,value', [('content_sha256', 7), ('source_sha256', 'invalid'),
                                      ('candidate_status', 'active'), ('write_performed', False)])
def test_archive_receipt_negative_contracts(tmp_path, key, value):
    root, _, args = setup(tmp_path)
    receipt = archive(root, args)
    assert validate_instance(root, 'provider-archive-receipt-v1', receipt)['status'] == 'pass'
    receipt[key] = value
    assert validate_instance(root, 'provider-archive-receipt-v1', receipt)['status'] != 'pass'


@pytest.mark.parametrize('journal', [[], {'status':'applying','writes':['invalid']},
    {'status':'applying','writes':[{'path':'../escape'}]},
    {'status':'applying','writes':[], 'applied_paths':['unknown']}])
def test_malformed_journal_is_readonly_attention_not_exception(tmp_path, journal):
    path = tmp_path / '.tmp/transactions/broken/journal.json'
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(journal))
    before = path.read_bytes()
    result = audit_transactions(tmp_path)
    assert result['status'] == 'needs-recovery-review'
    assert result['rows'][0]['status'] == 'invalid-journal'
    assert not result['rows'][0]['recoverable'] and path.read_bytes() == before


@pytest.mark.parametrize('key', ['status', 'pending_path'])
@pytest.mark.parametrize('value', [[], {}, None, False])
def test_unhashable_journal_fields_are_standard_invalid_journals(tmp_path, key, value):
    path = tmp_path / '.tmp/transactions/broken/journal.json'
    path.parent.mkdir(parents=True)
    row = {'status':'applying', 'writes':[]}
    row[key] = value
    path.write_text(json.dumps(row))
    assert audit_transactions(tmp_path)['rows'][0]['status'] == 'invalid-journal'


def test_private_writer_permissions_idempotence_and_conflicts(tmp_path):
    previous = os.umask(0o002)
    target = tmp_path / 'new/receipts/item.json'
    try:
        assert atomic_private_write(target, '{}\n', immutable=True)
        assert target.parent.stat().st_mode & 0o777 == 0o700
        assert target.stat().st_mode & 0o777 == 0o600
        assert not atomic_private_write(target, '{}\n', immutable=True)
        with pytest.raises(KnowledgeHubError):
            atomic_private_write(target, 'different', immutable=True)
    finally:
        os.umask(previous)


def test_private_writer_rejects_symlink_ancestor_before_creating_directories(tmp_path):
    outside = tmp_path / 'outside/existing'
    outside.mkdir(parents=True)
    (tmp_path / 'link').symlink_to(tmp_path / 'outside', target_is_directory=True)
    with pytest.raises(KnowledgeHubError, match='ancestors'):
        atomic_private_write(tmp_path / 'link/existing/new/item.json', '{}')
    assert not (outside / 'new').exists()


def test_timeout_reaps_owned_grandchild(tmp_path):
    pid_path = tmp_path / 'pid'
    script = "import subprocess,sys,time,pathlib; p=subprocess.Popen([sys.executable,'-c','import time;time.sleep(5)']); pathlib.Path(sys.argv[1]).write_text(str(p.pid)); time.sleep(5)"
    with pytest.raises(subprocess.TimeoutExpired):
        run_bounded([sys.executable, '-c', script, str(pid_path)], cwd=str(tmp_path), env=os.environ.copy(), timeout=.3)
    pid = int(pid_path.read_text())
    status = pathlib.Path('/proc') / str(pid) / 'status'
    for _ in range(20):
        if not status.exists() or 'State:\tZ' in status.read_text():
            break
        time.sleep(.05)
    assert not status.exists() or 'State:\tZ' in status.read_text()


def test_output_budget_drains_without_unbounded_capture(tmp_path):
    result, overflow = run_bounded([sys.executable, '-c', 'print("x"*10000)'], cwd=str(tmp_path),
                                   env=os.environ.copy(), timeout=5, output_limit=100)
    assert result.returncode == 0 and overflow and len(result.stdout.encode()) <= 100


def test_environment_flag_without_parent_is_not_passing_evidence(tmp_path, monkeypatch):
    monkeypatch.setenv('KNOWLEDGE_FINAL_GATE_INNER_REGRESSION', '1')
    result = _unit_result(tmp_path, False, {}, 1)
    assert result['exit_code'] != 0 and result['evidence_status'] == 'delegated-unverified'


def test_parent_unit_evidence_is_invalidated_by_source_or_result_changes(tmp_path, monkeypatch):
    from tools.codex_assets.knowledge_hub.unit_evidence import record_parent_unit, verified_parent_unit, UNIT_RECEIPT
    from tools.codex_assets.knowledge_hub.common import working_tree_signature
    subprocess.run(['git', 'init', '-q', str(tmp_path)], check=True)
    (tmp_path / '.gitignore').write_text('.tmp/\n.cache/\n')
    code = tmp_path / 'tools/a.py'
    code.parent.mkdir()
    code.write_text('value = 1\n')
    proof = {'status':'pass', 'command':'python -m coverage run --parallel-mode -m pytest -q',
             'attempts':[{'exit_code':0}], 'stdout_tail':'all tests passed'}
    record_parent_unit(tmp_path, working_tree_signature(tmp_path), dependency_fingerprints(tmp_path)['kernel'], proof)
    assert verified_parent_unit(tmp_path)
    monkeypatch.setenv('KNOWLEDGE_FINAL_GATE_INNER_REGRESSION', '1')
    assert _unit_result(tmp_path, False, {}, 1)['evidence_status'] == 'passed-reused'
    path = tmp_path / UNIT_RECEIPT
    row = json.loads(path.read_text())
    row['result']['stdout_tail'] = 'tampered'
    path.write_text(json.dumps(row))
    assert verified_parent_unit(tmp_path) is None
    record_parent_unit(tmp_path, working_tree_signature(tmp_path), dependency_fingerprints(tmp_path)['kernel'], proof)
    code.write_text('value = 2\n')
    assert verified_parent_unit(tmp_path) is None


@pytest.mark.parametrize('query', ['歌唱的和声分析', '知识的价值与治理', 'without_reference API',
                                   '不要修改 active 规则', 'GD32L235 v1.1.38 PA12',
                                   '请假流程', '请示审批规则', '请柬和请帖的区别'])
def test_normalization_preserves_nouns_tokens_and_negation(query):
    assert normalize_question(query) == query


def test_duplicate_self_excluded_before_topk_and_scope_body_signal():
    rows = [dict(id=str(i), title='title', summary_zh='summary', domain='test', status='reviewing') for i in range(4)]
    hints = duplicate_hints(rows, 'title', 'summary', 'test', exclude_id='0')
    assert [row['item_id'] for row in hints] == ['1', '2', '3']
    rows[0].update(content_fingerprint=content_fingerprint('正文  内容'), scope='project', version='v1')
    assert duplicate_hints(rows, 'title', 'summary', 'test', body='正文 内容', scope='project', version='v1')[0]['reason'] == 'same-content-scope-version'


def test_review_lane_quota_prevents_history_starvation():
    rows = [dict(item_id=str(i), path='a.md', owner='a', status='active', review_class='ordinary') for i in range(20)]
    rows += [dict(item_id='r', path='r.md', owner='a', status='reviewing', review_class='ordinary'),
             dict(item_id='h', path='h.md', owner='a', status='archived', review_class='ordinary')]
    result = build_review_batches(rows, 3)['batches'][0]
    assert {row['lane'] for row in result['rows']} == {'current-validity', 'candidate-decision', 'historical-integrity'}


def test_consumption_filters_only_matching_body_and_never_promotes(tmp_path):
    root, _, args = setup(tmp_path)
    item = archive(root, args)
    rows = [dict(item_id=item['item_id'], path=item['target'], owner='owner', status='reviewing', review_class='ordinary')]
    record_consumption(root, item['item_id'], 'accepted', 'explicit-reviewer', 'proof', item['content_sha256'], apply=True)
    packet = prepare_review_batches(root, rows, registry_items(root))
    assert packet['owner_count'] == 0 and packet['consumed_or_deferred_count'] == 1
    assert registry_items(root)[0]['status'] == 'reviewing'
    path = root / item['target']
    path.write_text(path.read_text() + '\n正文发生变化。\n')
    assert prepare_review_batches(root, rows, registry_items(root))['owner_count'] == 1


def test_dependency_identity_reuses_code_checks_but_not_content_tests(tmp_path):
    subprocess.run(['git', 'init', '-q', str(tmp_path)], check=True)
    (tmp_path / 'tools').mkdir()
    (tmp_path / 'tools/a.py').write_text('value = 1\n')
    (tmp_path / 'projects').mkdir()
    body = tmp_path / 'projects/a.md'
    body.write_text('first')
    before = dependency_fingerprints(tmp_path)
    body.write_text('second')
    after = dependency_fingerprints(tmp_path)
    assert before['kernel'] == after['kernel'] and before['delivery'] != after['delivery']
    _, identity = check_identity('mypy', ['python', '-m', 'mypy'], after)
    store_check(tmp_path, 'mypy', identity, {'status':'pass'})
    assert cached_check(tmp_path, 'mypy', identity)['cache_reused']
    (tmp_path / 'tools/a.py').write_text('value = 2\n')
    _, changed = check_identity('mypy', ['python', '-m', 'mypy'], dependency_fingerprints(tmp_path))
    assert cached_check(tmp_path, 'mypy', changed) is None
    cache = tmp_path / '.cache/knowledge-hub/checks/mypy.json'
    cache.write_text('{invalid')
    assert cached_check(tmp_path, 'mypy', identity) is None


@pytest.mark.parametrize('name', ['.ruff.toml', 'ruff.toml', 'mypy.ini', '.mypy.ini', 'setup.cfg', '.bandit'])
def test_discovered_configuration_creation_change_and_removal_invalidate_cache(tmp_path, name):
    subprocess.run(['git', 'init', '-q', str(tmp_path)], check=True)
    before = dependency_fingerprints(tmp_path)['kernel']
    path = tmp_path / name
    path.write_text('first')
    first = dependency_fingerprints(tmp_path)['kernel']
    path.write_text('second')
    second = dependency_fingerprints(tmp_path)['kernel']
    path.unlink()
    assert before != first != second and dependency_fingerprints(tmp_path)['kernel'] == before


def test_trace_overflow_is_bounded_and_nonblocking(tmp_path, monkeypatch):
    monkeypatch.setenv('KNOWLEDGE_TELEMETRY', '1')
    monkeypatch.setattr(observability_runtime, 'MAX_TRACE_LEDGER_BYTES', 1)
    result = observability_runtime.append_optional_span(tmp_path, {'status':'ok'})
    assert result['status'] == 'budget-exceeded' and result['non_blocking'] and not result['recorded']


def test_gate_denial_never_invokes_provider_apply(tmp_path, monkeypatch):
    source = tmp_path / 'input.json'
    source.write_text('{}')
    monkeypatch.setenv('CODEX_THREAD_ID', 'actual-thread')
    calls = []

    def run(root, args, **kwargs):
        calls.append(args)
        if 'gate' in args:
            raise KnowledgeHubError('denied gate exit3')
        return {'stdout':json.dumps({'status':'pass', 'sha256':'a'*64, 'receipt_id':'test'}), 'command':'test'}

    monkeypatch.setattr(governed_provider_cli, 'run_rtk', run)
    with pytest.raises(KnowledgeHubError, match='denied gate'):
        governed_provider_cli.execute_provider(tmp_path, tmp_path, 'actual-thread', 'activity-capture', source, apply=True)
    assert not any('--apply' in args for args in calls)


@pytest.mark.parametrize('corrupt', [False, True])
def test_governed_provider_success_requires_bound_identity_and_readback(tmp_path, monkeypatch, corrupt):
    source = tmp_path / 'input.json'
    source.write_text('{}')
    target = tmp_path / '.tmp/activity/receipt.json'
    target.parent.mkdir(parents=True)
    import hashlib
    encoded = '{"validated":true}\n'
    digest = hashlib.sha256(encoded.encode()).hexdigest()
    monkeypatch.setenv('CODEX_THREAD_ID', 'actual-thread')
    calls = []

    def run(root, args, **kwargs):
        calls.append(args)
        payload = {'status':'pass', 'sha256':digest, 'receipt_id':'test'}
        if 'gate' in args:
            payload.update(gate_allowed=True)
        if '--apply' in args:
            target.write_text('wrong' if corrupt else encoded)
            payload.update(applied=True, target=str(target))
        return {'stdout':json.dumps(payload), 'command':'test'}

    monkeypatch.setattr(governed_provider_cli, 'run_rtk', run)
    if corrupt:
        with pytest.raises(governed_provider_cli.PersistenceUnverified, match='readback mismatch'):
            governed_provider_cli.execute_provider(tmp_path, tmp_path, 'actual-thread', 'activity-capture', source, apply=True)
    else:
        result = governed_provider_cli.execute_provider(tmp_path, tmp_path, 'actual-thread', 'activity-capture', source, apply=True)
        assert result['readback_verified'] and result['applied']
        plan = tmp_path / '.tmp/governed-provider' / (result['plan_sha256'] + '.json')
        assert hashlib.sha256(plan.read_bytes()).hexdigest() == result['plan_sha256']
    assert next(i for i, args in enumerate(calls) if 'gate' in args) < next(i for i, args in enumerate(calls) if '--apply' in args)


@pytest.mark.parametrize('phase', ['dry-run', 'apply'])
def test_provider_timeout_cli_distinguishes_not_started_and_unknown(tmp_path, monkeypatch, capsys, phase):
    source = tmp_path / 'input.json'
    source.write_text('{}')
    monkeypatch.setenv('CODEX_THREAD_ID', 'actual-thread')

    def run(root, args, **kwargs):
        is_provider = 'activity-capture' in args
        if is_provider and (phase == 'dry-run' or '--apply' in args):
            raise subprocess.TimeoutExpired('provider', 1)
        return {'stdout':json.dumps({'status':'pass', 'gate_allowed':True, 'receipt_id':'test', 'sha256':'a'*64}), 'command':'test'}

    monkeypatch.setattr(governed_provider_cli, 'run_rtk', run)
    assert governed_provider_cli.main(['--root', str(tmp_path), '--policy-root', str(tmp_path),
                                      '--operation', 'activity-capture', '--source', str(source), '--apply']) == 3
    result = json.loads(capsys.readouterr().out)
    assert result['applied'] is (None if phase == 'apply' else False)
    assert result['status'] == ('needs-recovery-review' if phase == 'apply' else 'blocked')


@pytest.mark.parametrize('key,value', [('target', 7), ('target', None), ('status', []), ('status', {}), ('sha256', 7)])
def test_malformed_success_after_apply_reports_unknown(tmp_path, monkeypatch, capsys, key, value):
    source = tmp_path / 'input.json'
    source.write_text('{}')
    monkeypatch.setenv('CODEX_THREAD_ID', 'actual-thread')

    def run(root, args, **kwargs):
        payload = {'status':'pass', 'gate_allowed':True, 'receipt_id':'test', 'sha256':'a'*64}
        if '--apply' in args:
            payload.update(applied=True, target=str(tmp_path / 'output.json'))
            payload[key] = value
        return {'stdout':json.dumps(payload), 'command':'test'}

    monkeypatch.setattr(governed_provider_cli, 'run_rtk', run)
    assert governed_provider_cli.main(['--root', str(tmp_path), '--policy-root', str(tmp_path),
                                      '--operation', 'activity-capture', '--source', str(source), '--apply']) == 3
    result = json.loads(capsys.readouterr().out)
    assert result['applied'] is None and result['status'] == 'needs-recovery-review'


def test_tampered_unseen_gold_cannot_be_reported_as_frozen_validation(tmp_path):
    from tools.codex_assets.knowledge_hub.retrieval_holdout import evaluate_holdout
    subprocess.run(['git', 'init', '-q', str(tmp_path)], check=True)
    path = tmp_path / 'cases.json'
    path.write_text(json.dumps({'dataset_role':'frozen-validation', 'used_for_tuning':False,
                               'frozen_cases_sha256':'0'*64,
                               'cases':[{'id':'changed-gold', 'query':'changed', 'expected_ids':['answer']}]}))
    with pytest.raises(KnowledgeHubError, match='integrity'):
        evaluate_holdout(tmp_path, path)


@pytest.mark.parametrize('mutate_source', [False, True])
def test_holdout_benchmarks_consume_frozen_bytes_and_bind_source_before_after(tmp_path, monkeypatch, mutate_source):
    import hashlib
    from tools.codex_assets.knowledge_hub import retrieval_holdout as module
    root = tmp_path / 'repo'
    root.mkdir()
    subprocess.run(['git', 'init', '-q', str(root)], check=True)
    path = tmp_path / 'cases.json'
    cases = [{'id':'case-1', 'query':'old', 'expected_ids':['answer']}]
    digest = hashlib.sha256(json.dumps(cases, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    path.write_text(json.dumps({'dataset_role':'frozen-validation', 'used_for_tuning':False,
                               'frozen_cases_sha256':digest, 'cases':cases}))
    original_digest = hashlib.sha256(path.read_bytes()).hexdigest()
    seen = []

    def benchmark(value, cases_path, **kwargs):
        seen.append(json.loads(cases_path.read_text())['cases'][0]['query'])
        if len(seen) == 1:
            path.write_text('{}')
            if mutate_source:
                (root / 'new-source.md').write_text('changed')
        return {'status':'pass', 'cases':[{'id':'case-1', 'hit':True, 'reciprocal_rank':1,
                 'ndcg_at_10':1, 'forbidden_hits':[]}], 'hit_rate':1, 'mrr':1, 'ndcg_at_10':1,
                'authority_recall_at_3':1, 'integrity':{'status':'pass'}}

    monkeypatch.setattr(module, 'run_retrieval_benchmark_serialized', benchmark)
    monkeypatch.setattr(module, 'retrieval_benchmark_summary', lambda value:value)
    result = module.evaluate_holdout(root, path)
    assert seen == ['old', 'old'] and result['dataset_sha256'] == original_digest
    assert result['candidate_integrity']['unchanged'] is not mutate_source
    assert result['status'] == ('fail' if mutate_source else 'pass')


def test_deferred_review_reappears_when_due_without_touching_registry(tmp_path):
    root, _, args = setup(tmp_path)
    item = archive(root, args)
    today = dt.date.today()
    rows = [dict(item_id=item['item_id'], path=item['target'], owner='owner', status='reviewing', review_class='ordinary')]
    future = today + dt.timedelta(days=2)
    record_consumption(root, item['item_id'], 'deferred', 'explicit-reviewer', 'proof', item['content_sha256'],
                       next_review_at=future.isoformat(), review_seconds=12, apply=True)
    assert prepare_review_batches(root, rows, registry_items(root), as_of=today)['owner_count'] == 0
    packet = prepare_review_batches(root, rows, registry_items(root), as_of=future)
    assert packet['owner_count'] == 1 and packet['consumption_metrics']['review_seconds_total'] == 12
