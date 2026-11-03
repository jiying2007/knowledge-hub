"""Owner landing identity can navigate proved history without new write rights."""
import hashlib
import json
import pathlib
import runpy
import sys

import pytest


OLD = 'projects/gros/current/runbooks/asan-debug-guide.md'
HISTORY = 'projects/gros/archive/historical-current/runbooks/asan-debug-guide.md'
ITEM = 'pcr02-asan-debug-guide-project-local-20260624'


def fixture(repo):
    (repo / 'registry').mkdir()
    (repo / 'artifacts/manifests').mkdir(parents=True)
    (repo / 'registry/items.jsonl').write_text(json.dumps({'id': ITEM, 'path': HISTORY}) + '\n')
    history = repo / HISTORY
    history.parent.mkdir(parents=True)
    history.write_text('synthetic archived evidence\n')
    expected = hashlib.sha256(b'original synthetic source').hexdigest()
    manifest = {
        'inputs': {OLD: expected}, 'deletes': {OLD: expected},
        'active_promoted': False, 'owner_review_performed': False,
        'request': {'items': [{'item_id': ITEM, 'target_path': HISTORY, 'expected_sha256': expected}]},
        'result_writes': {HISTORY: hashlib.sha256(history.read_bytes()).hexdigest()},
    }
    path = repo / 'artifacts/manifests/content-maintenance-fixture.json'
    path.write_text(json.dumps(manifest))
    for target in ('plans/2026-06-15-dvr-record-proto-sensor-decoupling-plan.md',
                   'reports/2026-05-29-motor-mcu-debug-record.md',
                   'reports/2026-06-16-dvr-record-replay-session-archive.md'):
        file = repo / 'projects/gros/archive' / target
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text('synthetic other archived evidence\n')
    landing = repo / 'artifacts/manifests/pcr02-project-docs-owner-decision-landing-20260623.jsonl'
    landing.write_text(json.dumps({'worksheet_id': 'pcr02-owner-decision-worksheet-003',
                                   'source_sha256': expected, 'source_size': 25}) + '\n')
    return manifest, path


def invoke(repo, monkeypatch, capsys, apply=False):
    home = repo / 'synthetic-home'
    monkeypatch.setattr(pathlib.Path, 'home', lambda: home)
    monkeypatch.setattr(sys, 'argv', ['owner-targets', str(repo), '--json'] + (['--apply'] if apply else []))
    code = 0
    try:
        runpy.run_module('tools.codex_assets.knowledge_hub.pcr02_owner_targets_cli', run_name='__main__')
    except SystemExit as error:
        code = error.code
    return code, json.loads(capsys.readouterr().out)


def source_canary(repo, monkeypatch):
    source = repo / 'synthetic-home/work/sigmastar/pcr02_ssc305/SourceCode/sdk/verify/gros/docs/runbooks/asan-debug-guide.md'
    source.parent.mkdir(parents=True)
    source.write_text('retired-source-canary\n')
    original = pathlib.Path.read_bytes

    def guarded(path):
        assert path != source, 'retired source body must not be read'
        return original(path)

    monkeypatch.setattr(pathlib.Path, 'read_bytes', guarded)


def test_readonly_follows_only_proved_history_and_preserves_landing(tmp_path, monkeypatch, capsys):
    fixture(tmp_path)
    source_canary(tmp_path, monkeypatch)
    code, payload = invoke(tmp_path, monkeypatch, capsys)
    assert code == 0 and payload['read_only'] is True
    assert payload['target_present_count'] == 4 and payload['written_count'] == 0
    row = payload['results'][0]
    assert row['target_path'] == OLD and row['resolved_target_path'] == HISTORY
    assert row['target_resolution_source'] == 'maintenance-manifest'
    assert row['source_identity_source'] == 'owner-decision-landing-manifest'
    assert not (tmp_path / OLD).exists()


@pytest.mark.parametrize('damage', ['missing', 'changed-bytes', 'wrong-proof', 'ambiguous'])
def test_invalid_or_ambiguous_history_never_reports_present(tmp_path, monkeypatch, capsys, damage):
    manifest, path = fixture(tmp_path)
    if damage == 'missing':
        (tmp_path / HISTORY).unlink()
    elif damage == 'changed-bytes':
        (tmp_path / HISTORY).write_text('different evidence\n')
    elif damage == 'wrong-proof':
        manifest['result_writes'][HISTORY] = '0' * 64
        path.write_text(json.dumps(manifest))
    else:
        second = 'projects/gros/archive/second.md'
        (tmp_path / second).write_text('second evidence\n')
        registry = tmp_path / 'registry/items.jsonl'
        registry.write_text(registry.read_text() + json.dumps({'id': 'second', 'path': second}) + '\n')
        manifest['request']['items'] = [{'item_id': 'second', 'target_path': second,
                                         'expected_sha256': manifest['deletes'][OLD]}]
        manifest['result_writes'] = {second: hashlib.sha256((tmp_path / second).read_bytes()).hexdigest()}
        (path.parent / 'content-maintenance-second.json').write_text(json.dumps(manifest))
    code, payload = invoke(tmp_path, monkeypatch, capsys)
    assert code == 0 and payload['target_present_count'] == 3
    assert payload['results'][0]['target_exists'] is False
    assert payload['results'][0]['resolved_target_path'] == ''
    assert not (tmp_path / OLD).exists()


@pytest.mark.parametrize('invalid_proof', [False, True])
def test_apply_never_recreates_current_or_overwrites_history(tmp_path, monkeypatch, capsys, invalid_proof):
    manifest, path = fixture(tmp_path)
    before = (tmp_path / HISTORY).read_bytes()
    if invalid_proof:
        manifest['result_writes'][HISTORY] = '0' * 64
        path.write_text(json.dumps(manifest))
    source_canary(tmp_path, monkeypatch)
    code, payload = invoke(tmp_path, monkeypatch, capsys, apply=True)
    assert code == 1 and payload['status'] == 'blocked' and payload['written_count'] == 0
    assert 're-materialization is forbidden' in payload['blocked'][0]['reason']
    assert (tmp_path / HISTORY).read_bytes() == before
    assert not (tmp_path / OLD).exists()


def test_apply_without_retired_source_stays_blocked(tmp_path, monkeypatch, capsys):
    fixture(tmp_path)
    code, payload = invoke(tmp_path, monkeypatch, capsys, apply=True)
    assert code == 1 and payload['status'] == 'blocked'
    assert payload['source_available_count'] == payload['written_count'] == 0
    assert not (tmp_path / OLD).exists()


@pytest.mark.parametrize('apply', [False, True])
def test_unique_valid_wrong_item_proof_cannot_replace_known_identity(tmp_path, monkeypatch, capsys, apply):
    manifest, path = fixture(tmp_path)
    other = 'projects/gros/archive/other-item.md'
    other_file = tmp_path / other
    other_file.write_text('different item with valid lineage\n')
    registry = tmp_path / 'registry/items.jsonl'
    registry.write_text(registry.read_text() + json.dumps({'id': 'other-item', 'path': other}) + '\n')
    manifest['request']['items'] = [{'item_id': 'other-item', 'target_path': other,
                                     'expected_sha256': manifest['deletes'][OLD]}]
    manifest['result_writes'] = {other: hashlib.sha256(other_file.read_bytes()).hexdigest()}
    path.write_text(json.dumps(manifest))
    source_canary(tmp_path, monkeypatch)
    before = other_file.read_bytes()
    code, payload = invoke(tmp_path, monkeypatch, capsys, apply=apply)
    assert code == (1 if apply else 0)
    assert payload['target_present_count'] == 3 and payload['written_count'] == 0
    assert payload['results'][0]['resolved_target_path'] == ''
    assert payload['results'][0]['target_exists'] is False
    assert other_file.read_bytes() == before
    assert not (tmp_path / OLD).exists()
