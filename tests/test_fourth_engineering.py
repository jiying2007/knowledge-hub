"""Coverage recovery and recursion guards must not invent successful evidence."""

import ast
import json
import os
import pathlib
import subprocess
import sys

import pytest

from tools.codex_assets.knowledge_hub import engineering
from tools.codex_assets.knowledge_hub.engineering_results import coverage_failure_class

ROOT = pathlib.Path(__file__).resolve().parents[1]
PASSED = {'coverage':{'status':'pass'}, 'full_regression':{'status':'pass'}}


@pytest.mark.parametrize('message', [
    'Coverage failure: total of 70 is less than fail-under=75',
    'coverage threshold failed', 'unclassified report failure',
    'Coverage failure: total of 70 is less than fail-under=75; No data to report',
])
def test_low_or_unknown_coverage_does_not_repeat_tests(tmp_path, monkeypatch, message):
    def forbidden(*args, **kwargs):
        pytest.fail('deterministic or unknown failures cannot start recovery commands')
    monkeypatch.setattr(engineering, '_run_quality_command', forbidden)
    result = engineering._recover_coverage_report(tmp_path, 'python',
        {'status':'fail', 'attempts':[{'stderr_tail':[message]}]}, PASSED)
    assert result['status'] == 'fail' and not result['recollection']
    assert not result['recovered_after_recollection']


@pytest.mark.parametrize('prior', [None, {}, {'coverage':{'status':'pass'}},
    {'coverage':{'status':'fail'}, 'full_regression':{'status':'pass'}}])
def test_data_recovery_requires_both_completed_test_runs(tmp_path, monkeypatch, prior):
    monkeypatch.setattr(engineering, '_run_quality_command', lambda *a, **k:pytest.fail('not eligible'))
    result = engineering._recover_coverage_report(tmp_path, 'python',
        {'status':'fail', 'error':'No data to report.'}, prior)
    assert result['status'] == 'fail' and not result['recollection']


def test_recognized_data_recovery_has_no_implicit_exit_one_retry(tmp_path, monkeypatch):
    calls = []
    def run(root, command, timeout, **kwargs):
        calls.append((tuple(command), kwargs))
        if 'tools.codex_assets.knowledge_hub.regression_cli' in command:
            return {'status':'fail', 'attempt_count':1, 'attempts':[{'exit_code':1}]}
        return {'status':'pass'}
    monkeypatch.setattr(engineering, '_run_quality_command', run)
    result = engineering._recover_coverage_report(tmp_path, 'python',
        {'status':'fail', 'error':'database disk image is malformed'}, PASSED)
    assert result['status'] == 'fail' and not result['recovered_after_recollection']
    assert len(calls) == 4 and all(not kwargs for _, kwargs in calls)


def test_real_inner_selected_case_is_delegated_without_pass():
    env = dict(os.environ, KNOWLEDGE_FINAL_GATE_INNER_REGRESSION='1', PYTHONDONTWRITEBYTECODE='1')
    result = subprocess.run(['rtk', sys.executable, '-m',
        'tools.codex_assets.knowledge_hub.regression_cli', str(ROOT), '--test',
        'test_final_gate_owner_review_blocker', '--summary-json'],
        cwd=str(ROOT), env=env, text=True, capture_output=True, timeout=10)
    payload = json.loads(result.stdout)
    assert result.returncode == 1 and payload['status'] == 'fail'
    assert payload['delegated_result_count'] == 1 and payload['executed_result_count'] == 0
    assert payload['passed_result_count'] == payload['failed_result_count'] == 0
    assert payload['delegated_ids'] == ['final-gate-owner-review-blocker']
    assert payload['full_regression_completed'] is False


def test_outer_case_is_not_skipped_by_inner_guard(monkeypatch):
    path = ROOT / 'tools/codex_assets/knowledge_hub/regression/product_gates.py'
    source = ast.parse(path.read_text())
    function = next(node for node in source.body if isinstance(node, ast.FunctionDef)
                    and node.name == '_skip_inside_product_gate')
    calls, namespace = [], {'os':os, 'record':lambda *args:calls.append(args)}
    exec(compile(ast.Module(body=[function], type_ignores=[]), str(path), 'exec'), namespace)
    monkeypatch.delenv('KNOWLEDGE_FINAL_GATE_INNER_REGRESSION', raising=False)
    assert namespace['_skip_inside_product_gate']('outer', 'outer') is False and not calls


def test_failure_class_reads_bounded_attempt_metadata():
    result = {'attempts':[{'stderr_tail':['No data to report.']}]}
    assert coverage_failure_class(result) == 'recoverable-coverage-data'


def test_delegated_projection_is_bounded_and_not_completed():
    from tools.codex_assets.knowledge_hub.product_gate_support import _regression_execution_summary
    result = _regression_execution_summary({'delegated_result_count':30,
        'delegated_ids':['delegated'] * 30, 'executed_result_count':3}, 'full', False)
    assert result['full_regression_completed'] is False
    assert result['delegated_result_count'] == 30 and len(result['delegated_ids']) == 20


def test_failure_summary_retains_delegated_predicate():
    from tools.codex_assets.knowledge_hub.engineering_results import retain_regression_failure
    attempt = {}
    retain_regression_failure(['tools.codex_assets.knowledge_hub.regression_cli'],
        {'exit_code':1, 'stdout':json.dumps({'status':'fail', 'delegated_ids':['inner'],
            'delegated_result_count':1, 'full_regression_completed':False})}, attempt)
    assert attempt['failure_summary']['delegated_ids'] == ['inner']
    assert attempt['failure_summary']['full_regression_completed'] is False


@pytest.mark.parametrize('change', [
    {'full_regression_completed':None}, {'full_regression_completed':False},
    {'delegated_result_count':1}, {'delegated_result_count':'0'},
    {'delegated_result_count':False}, {'delegated_result_count':None},
])
def test_product_full_requires_explicit_execution_facts(change):
    from tools.codex_assets.knowledge_hub.product_gate_support import _full_regression_verified
    valid = {'status':'pass', 'full_regression_completed':True, 'delegated_result_count':0}
    assert _full_regression_verified({'exit_code':0}, valid)
    assert not _full_regression_verified({'exit_code':0}, dict(valid, **change))
    assert not _full_regression_verified({'exit_code':0}, {'status':'pass'})
    assert not _full_regression_verified({'exit_code':1}, valid)


@pytest.mark.parametrize('location', ['top', 'attempt', 'earlier-attempt'])
def test_timeout_metadata_precedes_recoverable_coverage_text(tmp_path, monkeypatch, location):
    row = {'timed_out':True, 'stderr_tail':['No data to report.']}
    initial = dict(status='fail', **row) if location == 'top' else {'status':'fail', 'attempts':[row]}
    if location == 'earlier-attempt':
        initial['attempts'] += [{'stderr_tail':['No data to report.']}] * 3
    monkeypatch.setattr(engineering, '_run_quality_command', lambda *a, **k:pytest.fail('timeout cannot recollect'))
    result = engineering._recover_coverage_report(tmp_path, 'python', initial, PASSED)
    assert result['failure_class'] == 'non-recoverable-timeout'
    assert result['status'] == 'fail' and not result['recollection']


@pytest.mark.parametrize('metadata', [{'exit_code':-15}, {'output_truncated':True},
    {'failure_class':'deterministic-or-unknown'}, {'failure_class':'transient-os-error'}])
def test_execution_failure_metadata_precedes_data_marker(tmp_path, monkeypatch, metadata):
    row = dict(metadata, stderr_tail=['No data to report.'])
    monkeypatch.setattr(engineering, '_run_quality_command', lambda *a, **k:pytest.fail('cannot recollect'))
    result = engineering._recover_coverage_report(tmp_path, 'python',
        {'status':'fail', 'attempts':[row] + [{'stderr_tail':['No data to report.']}] * 3}, PASSED)
    assert result['failure_class'] == 'non-recoverable-execution'
    assert result['status'] == 'fail' and not result['recollection']
