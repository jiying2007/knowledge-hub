"""Probe only the permissions needed by local HTTP tests and dependency lookup."""

from __future__ import annotations

import json
import socket
from typing import Any, Dict


def probe_environment():
    checks: Dict[str, Dict[str, Any]] = {}
    for name, probe in (('loopback_socket', _loopback), ('dependency_dns', _dns)):
        try:
            probe()
            checks[name] = {'status':'pass'}
        except OSError as error:
            checks[name] = {'status':'blocked', 'error_type':type(error).__name__,
                            'errno':error.errno}
    return {'schema_version':'knowledge-hub.environment-capabilities/v1',
            'status':'pass' if all(row['status'] == 'pass' for row in checks.values()) else 'blocked',
            'checks':checks, 'validation_only':True, 'dependency_http_request_performed':False,
            'dependency_dns_lookup_performed':True}


def _loopback():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as channel:
        channel.settimeout(1)
        channel.bind(('127.0.0.1', 0))


def _dns():
    if not socket.getaddrinfo('pypi.org', 443, type=socket.SOCK_STREAM):
        raise OSError('dependency DNS returned no addresses')


def main():
    report = probe_environment()
    print(json.dumps(report, ensure_ascii=False))
    return 0 if report['status'] == 'pass' else 1


if __name__ == '__main__':
    raise SystemExit(main())
