import json
from types import SimpleNamespace

from tools.codex_assets.knowledge_hub import provider_grants as grants


def test_request_renewal_is_only_forwarded_when_explicit(tmp_path, monkeypatch):
    thread = '01a18d5d-eb3d-77c2-a480-6ae362e0336c'
    monkeypatch.setenv('CODEX_THREAD_ID', thread)
    import subprocess
    commands = []
    raw = '全部优化落地\n'
    def run(command, **kwargs):
        commands.append(command)
        return SimpleNamespace(returncode=0, stdout=json.dumps({
            'schema_version': 'codex-request-verification/v1', 'status': 'VERIFIED', 'read_only': True,
            'user_message_verified': True, 'thread_id': thread, 'request_sha256': grants.hashlib.sha256(raw.encode()).hexdigest(),
            'attestation_sha256': 'a' * 64}))
    monkeypatch.setattr(subprocess, 'run', run)
    declaration = tmp_path / 'request.md'
    renewal = tmp_path / 'renewal.md'
    grants.attested_request(raw, declaration)
    assert '--renewal-request-file' not in commands[-1]
    grants.attested_request(raw, declaration, renewal)
    assert commands[-1][-2:] == ['--renewal-request-file', str(renewal)]
