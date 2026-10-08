"""Bounded failed-attempt projections and structured regression predicates."""

from __future__ import annotations

import errno
import subprocess

from .common import KnowledgeHubError, parse_json_output


def failed_attempts(attempts, error):
    return {'status':'fail', 'attempt_count':len(attempts), 'recovered_after_retry':False,
            'attempts':attempts, 'error':error}


def coverage_failure_class(result):
    attempts = result.get('attempts', [])
    if not isinstance(attempts, list) or len(attempts) > 100:
        return 'unknown-coverage-failure'
    rows = [result] + attempts
    if any(isinstance(row, dict) and row.get('timed_out') for row in rows):
        return 'non-recoverable-timeout'
    if any(isinstance(row, dict) and (row.get('output_truncated') or row.get('failure_class') in
            ('deterministic-or-unknown', 'transient-os-error', 'transport-or-invalid-output')
            or (type(row.get('exit_code')) is int and row['exit_code'] < 0)) for row in rows):
        return 'non-recoverable-execution'
    text = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        for key in ('error', 'stdout_tail', 'stderr_tail'):
            value = row.get(key, '')
            if isinstance(value, list):
                value = '\n'.join(str(part)[:1000] for part in value[-20:])
            if isinstance(value, str):
                text.append(value[-12000:].lower())
    message = '\n'.join(text)
    if 'less than fail-under' in message or 'coverage threshold' in message:
        return 'deterministic-low-coverage'
    if any(marker in message for marker in ('database disk image is malformed',
            'file is not a database', 'no data to report', 'no usable data files')):
        return 'recoverable-coverage-data'
    return 'unknown-coverage-failure'


def exception_attempt(number, error):
    transient = isinstance(error, OSError) and error.errno in (errno.EAGAIN, errno.EINTR)
    result = {'attempt':number, 'status':'fail', 'error':str(error),
              'failure_class':'transient-os-error' if transient else 'deterministic-or-unknown',
              'retry_eligible':transient}
    if isinstance(error, subprocess.TimeoutExpired):
        for key, value in (('stdout_tail', error.output), ('stderr_tail', error.stderr)):
            if isinstance(value, bytes):
                value = value.decode('utf-8', errors='replace')
            result[key] = value[-12000:].splitlines()[-20:] if isinstance(value, str) else []
        result.update(timed_out=True, timeout_sec=error.timeout,
                      output_truncated=bool(getattr(error, 'output_truncated', False)))
    return result


def retain_regression_failure(command, result, attempt):
    if 'tools.codex_assets.knowledge_hub.regression_cli' in command and result['exit_code'] != 0:
        try:
            report = parse_json_output(result)
            attempt['failure_summary'] = {key:report.get(key) for key in
                ('status', 'selected_test_count', 'result_count', 'failure_ids', 'failures', 'failures_truncated',
                 'executed_result_count', 'delegated_result_count', 'delegated_ids',
                 'delegated_truncated', 'full_regression_completed')}
        except KnowledgeHubError:
            attempt['failure_summary'] = {'status':'unparseable'}
