import json
import pathlib
import subprocess

import pytest

from tools.codex_assets.knowledge_hub import product_gate_parallel as parallel
from tools.codex_assets.knowledge_hub import product_gate, final_gate_cli
from tools.codex_assets.knowledge_hub.bounded_process import BoundedTimeoutExpired
from tools.codex_assets.knowledge_hub.schemas import validate_instance


def _quiet_noncommands(monkeypatch):
    for name in ('audit_links', 'build_obsidian_views', 'validate_schema_catalog', 'evaluate_engineering_contract',
                 'local_metrics', '_project_readiness', 'plan_team_export', '_restore_state'):
        monkeypatch.setattr(parallel, name, lambda *args, **kwargs:{})
    monkeypatch.setattr(parallel, 'incomplete_transactions', lambda *args:[])


@pytest.mark.parametrize('selected,fragment,deadline', [
    ('check_result', 'knowledge-check.sh', 45), ('status_result', 'knowledge-status.sh', 60),
    ('source_check_result', 'knowledge-source-check.sh', 60), ('unit_result', 'pytest', 180),
    ('diff_result', 'diff', 20),
])
def test_command_future_timeout_becomes_failed_evidence_without_raising(tmp_path, monkeypatch, selected, fragment, deadline):
    monkeypatch.delenv('KNOWLEDGE_FINAL_GATE_INNER_REGRESSION', raising=False)
    _quiet_noncommands(monkeypatch)
    calls = []
    def transport(root, command, **kwargs):
        calls.append((command, kwargs['timeout']))
        if any(fragment in value for value in command):
            raise BoundedTimeoutExpired(command, kwargs['timeout'], output=b'x'*10000, stderr=b'partial error')
        return dict(exit_code=0, command='synthetic', stdout='{}', stderr='', duration_sec=0)
    monkeypatch.setattr(parallel, 'run_rtk', transport)
    results = parallel.collect_parallel_results(tmp_path, '2026-06-01', 'fixture', {'head_revision':'fixture'},
                                               False, {}, unit_test_timeout_seconds=180)
    failed = results[selected]
    assert failed['exit_code'] == 124 and failed['evidence_status'] == 'failed-timeout'
    assert failed['timed_out'] and failed['timeout_sec'] == deadline and failed['output_incomplete']
    assert failed['output_truncated'] and len(failed['stdout']) == 4096
    assert failed['stderr'] == 'partial error' and not failed['automatic_retry_performed']
    projection = parallel.command_timeout_projection(failed)
    assert projection['status'] == 'fail' and projection['command_timeout']['timeout_sec'] == deadline
    assert len(calls) == 5


def test_noncommand_programming_error_is_not_silently_failed_evidence(tmp_path, monkeypatch):
    _quiet_noncommands(monkeypatch)
    monkeypatch.setattr(parallel, 'run_rtk', lambda *args, **kwargs:dict(exit_code=0))
    def invalid_schema(*args):
        raise TypeError('programming contract failure')
    monkeypatch.setattr(parallel, 'validate_schema_catalog', invalid_schema)
    with pytest.raises(TypeError, match='programming contract'):
        parallel.collect_parallel_results(tmp_path, '2026-06-01', 'fixture', {'head_revision':'fixture'},
                                          False, {}, unit_test_timeout_seconds=180)


def test_non_timeout_command_errors_still_escape(tmp_path, monkeypatch):
    def invalid_call(*args, **kwargs):
        raise ValueError('invalid programming argument')
    monkeypatch.setattr(parallel, 'run_rtk', invalid_call)
    with pytest.raises(ValueError, match='programming'):
        parallel._check_result(tmp_path, '2026-06-01')


def test_unit_timeout_keeps_real_product_cli_json_failed_and_schema_valid(monkeypatch, capsys):
    root = pathlib.Path(__file__).resolve().parents[1]
    monkeypatch.delenv('KNOWLEDGE_FINAL_GATE_INNER_REGRESSION', raising=False)
    signature = 'a'*64
    monkeypatch.setattr(product_gate, 'working_tree_signature', lambda *args:signature)
    monkeypatch.setattr(product_gate, '_candidate_integrity', lambda *args:dict(status='pass', unchanged=True,
                                                                             before_signature=signature, after_signature=signature))
    monkeypatch.setattr(product_gate, '_git_delivery_state', lambda *args:dict(head_revision='fixture', worktree_clean=False,
                                                                            dependency_manifests_tracked=True))
    monkeypatch.setattr(product_gate, '_engineering_quality_state', lambda *args:dict(status='missing', fresh=False, check_statuses={}))
    monkeypatch.setattr(product_gate, '_write_snapshot', lambda *args:'synthetic-only-no-write')
    monkeypatch.setattr(parallel, '_restore_state', lambda *args:dict(fresh=False, status='not-run'))
    monkeypatch.setattr(product_gate, 'run_retrieval_benchmark_serialized', lambda *args, **kwargs:dict(status='pass', cases=[]))
    def transport(root, command, **kwargs):
        if 'pytest' in command:
            raise subprocess.TimeoutExpired(command, kwargs['timeout'], output=b'partial pytest', stderr=b'deadline proof')
        value = dict(status='pass', errors=[])
        return dict(exit_code=0, command='synthetic', stdout=json.dumps(value), stderr='', duration_sec=0)
    monkeypatch.setattr(parallel, 'run_rtk', transport)
    assert final_gate_cli.main(['--root', str(root), '--json', '--as-of', '2026-06-01']) == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload['as_of'] == '2026-06-01'
    assert payload['checks']['knowledge_check']['status'] == 'pass'
    unit = payload['checks']['shared_unit_tests']
    assert unit['status'] == 'fail' and unit['exit_code'] == 124
    assert unit['command_timeout']['timeout_sec'] == 180
    assert unit['stderr_tail'] == ['deadline proof']
    assert payload['platform_status']['hard_checks']['shared_unit_tests'] is False
    assert payload['platform_status']['unit_evidence_status'] == 'failed-timeout'
    assert validate_instance(root, 'final-gate-product-v5', payload)['status'] == 'pass'
