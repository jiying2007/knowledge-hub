"""Cheap input contracts precede expensive immutable-tree verification."""

from __future__ import annotations

import subprocess
import os

from .common import run_rtk, KnowledgeHubError, parse_json_output
from .schemas import validate_schema_catalog


def preflight(root, *, verify_capabilities=False):
    from .engineering import evaluate_engineering_contract, _current_python_executable
    contract = evaluate_engineering_contract(root)
    schema = validate_schema_catalog(root)
    try:
        result = run_rtk(root, [_current_python_executable(), '-c', 'print("ci-transport-ready")'], timeout=30,
                         extra_env={'PATH':str(root / 'tools/ci') + os.pathsep + os.environ.get('PATH', '')})
        transport = {'status':'pass', 'exit_code':result['exit_code']}
    except (KnowledgeHubError, OSError, subprocess.TimeoutExpired) as error:
        transport = {'status':'fail', 'error':str(error)}
    capabilities = {'status':'not-run', 'reason':'prerequisite-failed' if verify_capabilities else 'not-requested'}
    if verify_capabilities and all(value['status'] == 'pass' for value in (contract, schema, transport)):
        capabilities = environment_capabilities(root, _current_python_executable())
    required = [contract, schema, transport] + ([capabilities] if verify_capabilities else [])
    return {'schema_version':1, 'status':'pass' if all(value['status'] == 'pass' for value in required) else 'fail',
            'contract':contract, 'schema':{'status':schema['status'], 'errors':schema['errors'][:20]},
            'transport':transport, 'environment':capabilities, 'expensive_checks_started':False,
            'errors':[] if all(value['status'] == 'pass' for value in required) else ['engineering preflight requirements failed']}


def environment_capabilities(root, python):
    try:
        result = run_rtk(root, [python, '-m', 'tools.codex_assets.knowledge_hub.environment_capabilities'],
                         timeout=8, accepted_exit_codes=(0, 1),
                         extra_env={'PATH':str(root / 'tools/ci') + os.pathsep + os.environ.get('PATH', '')})
        if type(result.get('exit_code')) is not int or result['exit_code'] not in (0, 1) or not isinstance(result.get('stdout'), str):
            raise KnowledgeHubError('invalid capability transport result')
        if len(result['stdout'].encode('utf-8')) > 16384:
            raise KnowledgeHubError('capability report exceeds byte budget')
        report = parse_json_output(result)
        checks = report.get('checks', {})
        if (report.get('schema_version') != 'knowledge-hub.environment-capabilities/v1'
                or not isinstance(checks, dict) or set(checks) != {'loopback_socket', 'dependency_dns'}
                or any(not isinstance(row, dict) or row.get('status') not in {'pass', 'blocked'} for row in checks.values())
                or report.get('validation_only') is not True or report.get('dependency_http_request_performed') is not False
                or report.get('dependency_dns_lookup_performed') is not True):
            raise KnowledgeHubError('invalid capability report')
        successful = result['exit_code'] == 0 and all(row['status'] == 'pass' for row in checks.values())
        if report.get('status') != ('pass' if successful else 'blocked'):
            raise KnowledgeHubError('capability status contradicts its checks or exit code')
        return dict(report, status='pass' if successful else 'fail', exit_code=result['exit_code'])
    except (KnowledgeHubError, OSError, subprocess.TimeoutExpired, ValueError, TypeError, RecursionError) as error:
        return {'status':'fail', 'error_type':type(error).__name__, 'reason':'capability-probe-unavailable',
                'automatic_retry_performed':False}
