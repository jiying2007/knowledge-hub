"""Environment denial must stop before tests, build or vulnerability lookup."""

import json
import pathlib
import socket
import subprocess

import pytest

from tools.codex_assets.knowledge_hub import environment_capabilities, engineering_preflight, engineering_snapshot


def _report(loopback='pass', dns='pass'):
    return {'schema_version':'knowledge-hub.environment-capabilities/v1',
            'status':'pass' if loopback == dns == 'pass' else 'blocked',
            'checks':{'loopback_socket':{'status':loopback}, 'dependency_dns':{'status':dns}},
            'validation_only':True, 'dependency_http_request_performed':False,
            'dependency_dns_lookup_performed':True}


def test_probe_preserves_dns_and_socket_denials_without_addresses(monkeypatch):
    def denied():
        raise PermissionError(1, 'private diagnostic that must not appear')
    monkeypatch.setattr(environment_capabilities, '_loopback', denied)
    monkeypatch.setattr(environment_capabilities, '_dns', denied)
    result = environment_capabilities.probe_environment()
    assert result['status'] == 'blocked'
    assert result['checks']['loopback_socket']['errno'] == 1
    assert result['checks']['dependency_dns']['error_type'] == 'PermissionError'
    assert 'private diagnostic' not in json.dumps(result)


def test_loopback_probe_closes_its_ephemeral_socket(monkeypatch):
    operations = []
    class Channel:
        def __enter__(self):
            return self
        def __exit__(self, *args):
            operations.append('closed')
        def settimeout(self, value):
            operations.append(('timeout', value))
        def bind(self, address):
            operations.append(('bind', address))
    monkeypatch.setattr(socket, 'socket', lambda *args:Channel())
    environment_capabilities._loopback()
    assert operations == [('timeout', 1), ('bind', ('127.0.0.1', 0)), 'closed']


def test_capability_subprocess_is_bounded_and_uses_real_ci_path(tmp_path, monkeypatch):
    def execute(root, command, **options):
        assert command == ['/selected/python', '-m', 'tools.codex_assets.knowledge_hub.environment_capabilities']
        assert options['timeout'] == 8 and options['accepted_exit_codes'] == (0, 1)
        assert options['extra_env']['PATH'].startswith(str(root / 'tools/ci'))
        return {'exit_code':1, 'stdout':json.dumps(_report(dns='blocked'))}
    monkeypatch.setattr(engineering_preflight, 'run_rtk', execute)
    result = engineering_preflight.environment_capabilities(tmp_path, '/selected/python')
    assert result['status'] == 'fail' and result['checks']['dependency_dns']['status'] == 'blocked'


@pytest.mark.parametrize('kind', ['timeout', 'invalid-json', 'oversized', 'contradictory-status'])
def test_capability_uncertainty_never_becomes_success(tmp_path, monkeypatch, kind):
    def execute(*args, **kwargs):
        if kind == 'timeout':
            raise subprocess.TimeoutExpired('probe', 8)
        report = _report()
        report['status'] = 'blocked'
        raw = {'invalid-json':'not-json', 'oversized':'x' * 16385,
               'contradictory-status':json.dumps(report)}[kind]
        return {'exit_code':0, 'stdout':raw}
    monkeypatch.setattr(engineering_preflight, 'run_rtk', execute)
    result = engineering_preflight.environment_capabilities(tmp_path, '/selected/python')
    assert result['status'] == 'fail' and result['automatic_retry_performed'] is False


def test_environment_failure_prevents_snapshot_capture_and_full(tmp_path, monkeypatch):
    checked = {'status':'fail', 'contract':{'status':'pass'}, 'schema':{'status':'pass'},
               'transport':{'status':'pass'}, 'environment':{'status':'fail'}, 'expensive_checks_started':False}
    monkeypatch.setattr(engineering_preflight, 'preflight', lambda root, **kwargs:checked)
    monkeypatch.setattr(engineering_snapshot, 'capture_snapshot',
                        lambda *args:pytest.fail('snapshot capture started despite failed environment'))
    result = engineering_snapshot.run_snapshot_engineering(pathlib.Path(tmp_path))
    assert result['phase'] == 'preflight' and result['checks'] == {}
    assert result['expensive_checks_started'] is False


def test_in_place_cli_does_not_start_full_when_capability_blocked(tmp_path, monkeypatch, capsys):
    from tools.codex_assets.knowledge_hub import engineering_cli
    checked = {'status':'fail', 'contract':{'status':'pass'}, 'schema':{'status':'pass'},
               'environment':{'status':'fail'}, 'expensive_checks_started':False}
    monkeypatch.setattr(engineering_cli, 'repository_root', lambda *args:tmp_path)
    monkeypatch.setattr(engineering_preflight, 'preflight', lambda *args, **kwargs:checked)
    monkeypatch.setattr(engineering_cli, 'run_engineering_quality',
                        lambda *args, **kwargs:pytest.fail('full started despite blocked capability'))
    assert engineering_cli.main(['--mode', 'full', '--in-place', '--summary-json']) == 1
    result = json.loads(capsys.readouterr().out)
    assert result['preflight'] is True and result['check_statuses'] == {}
    assert result['expensive_checks_started'] is False


def test_boolean_transport_exit_code_is_not_accepted(tmp_path, monkeypatch):
    monkeypatch.setattr(engineering_preflight, 'run_rtk',
                        lambda *args, **kwargs:{'exit_code':False, 'stdout':json.dumps(_report())})
    assert engineering_preflight.environment_capabilities(tmp_path, '/selected/python')['status'] == 'fail'


def test_replay_cli_checks_environment_before_touching_retained_inputs(tmp_path, monkeypatch, capsys):
    from tools.codex_assets.knowledge_hub import engineering_cli, snapshot_retention
    checked = {'status':'fail', 'contract':{'status':'pass'}, 'environment':{'status':'fail'},
               'expensive_checks_started':False}
    monkeypatch.setattr(engineering_cli, 'repository_root', lambda *args:tmp_path)
    monkeypatch.setattr(engineering_preflight, 'preflight', lambda *args, **kwargs:checked)
    monkeypatch.setattr(snapshot_retention, 'replay_failure',
                        lambda *args:pytest.fail('replay started despite blocked environment'))
    assert engineering_cli.main(['--mode', 'full', '--replay', 'retained', '--json']) == 1
    result = json.loads(capsys.readouterr().out)
    assert result['phase'] == 'preflight' and result['expensive_checks_started'] is False


def test_multibyte_capability_report_cannot_bypass_byte_budget(tmp_path, monkeypatch):
    report = dict(_report(), note='汉' * 6000)
    raw = json.dumps(report, ensure_ascii=False)
    assert len(raw) < 16384 < len(raw.encode('utf-8'))
    monkeypatch.setattr(engineering_preflight, 'run_rtk',
                        lambda *args, **kwargs:{'exit_code':0, 'stdout':raw})
    result = engineering_preflight.environment_capabilities(tmp_path, '/selected/python')
    assert result['status'] == 'fail' and result['automatic_retry_performed'] is False
