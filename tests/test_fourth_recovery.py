import concurrent.futures
import datetime as dt
import hashlib
import json
import threading

import pytest

from tools.codex_assets.knowledge_hub import governed_provider_cli as provider
from tools.codex_assets.knowledge_hub import private_io, review_batches
from tools.codex_assets.knowledge_hub.common import KnowledgeHubError
from tools.codex_assets.knowledge_hub.operation_journal import record_stage
from tools.codex_assets.knowledge_hub.review_state import load_state, cycle_sha256


def _provider_fixture(tmp_path, monkeypatch):
    monkeypatch.setenv('CODEX_THREAD_ID', 'fixture-thread')
    source = tmp_path / 'source.md'
    source.write_text('sanitized candidate')
    planned = {'status':'PLANNED', 'operation_id':'b' * 64,
               'content_sha256':'c' * 64, 'target':'candidate.md'}
    def transport(root, args, **kwargs):
        payload = planned if 'archive' in args else {'status':'pass', 'gate_allowed':True}
        return {'stdout':json.dumps(payload), 'stderr':'', 'exit_code':0}
    monkeypatch.setattr(provider, 'run_rtk', transport)
    def execute():
        return provider.execute_provider(tmp_path, tmp_path, 'fixture-thread', 'archive',
                                         source, project='fixture', apply=True)
    return execute, planned


def test_same_plan_concurrent_execution_invokes_apply_once(tmp_path, monkeypatch, capsys):
    execute, planned = _provider_fixture(tmp_path, monkeypatch)
    entered, release = threading.Event(), threading.Event()
    calls = []
    def apply(*args):
        calls.append(1)
        entered.set()
        assert release.wait(timeout=5)
        return dict(planned, status='ARCHIVED', persisted=True)
    monkeypatch.setattr(provider, '_apply_and_verify', apply)
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        first = pool.submit(execute)
        try:
            assert entered.wait(timeout=5)
            with pytest.raises(KnowledgeHubError, match='already in progress'):
                execute()
            assert provider.main(['--root', str(tmp_path), '--policy-root', str(tmp_path),
                                  '--source', str(tmp_path / 'source.md'), '--project', 'fixture', '--apply']) == 3
            competitor = json.loads(capsys.readouterr().out)
            assert competitor['status'] == 'blocked' and competitor['applied'] is False
        finally:
            release.set()
        assert first.result(timeout=5)['status'] == 'pass'
    assert len(calls) == 1


def test_unknown_execution_releases_lock_but_cannot_apply_again(tmp_path, monkeypatch):
    execute, _ = _provider_fixture(tmp_path, monkeypatch)
    calls = []
    def uncertain(*args):
        calls.append(1)
        raise provider.PersistenceUnverified('injected Provider outcome unknown')
    monkeypatch.setattr(provider, '_apply_and_verify', uncertain)
    monkeypatch.setattr(provider, 'reconcile_plan', lambda *args:{'status':'NOT_FOUND', 'read_only':True})
    with pytest.raises(provider.PersistenceUnverified):
        execute()
    with pytest.raises(KnowledgeHubError, match='transition'):
        execute()
    assert len(calls) == 1
    state = next((tmp_path / '.tmp/governed-provider').glob('*.state.json'))
    assert json.loads(state.read_text())['stage'] == 'unknown'


def test_execution_lock_does_not_follow_symlink(tmp_path):
    outside = tmp_path / 'outside'
    outside.mkdir()
    link = tmp_path / 'link'
    link.symlink_to(outside, target_is_directory=True)
    with pytest.raises(KnowledgeHubError, match='symlinks'):
        with private_io.private_execution_lock(link / 'operation.lock'):
            pytest.fail('must not claim external directory')
    assert not list(outside.iterdir())


def test_same_stage_retry_confirms_durability_without_new_event(tmp_path, monkeypatch):
    digest, identity = 'a' * 64, {'operation_id':'b' * 64}
    record_stage(tmp_path, digest, 'planned', identity)
    original = private_io._sync_directory
    calls = []
    def once(path):
        calls.append(path)
        if len(calls) == 1:
            raise OSError('injected directory sync failure')
        original(path)
    monkeypatch.setattr(private_io, '_sync_directory', once)
    with pytest.raises(private_io.PrivateWriteUncertain):
        record_stage(tmp_path, digest, 'gated', identity)
    path = tmp_path / '.tmp/governed-provider' / (digest + '.state.json')
    before = path.read_bytes()
    assert record_stage(tmp_path, digest, 'gated', identity) is False
    assert len(calls) == 2 and path.read_bytes() == before
    assert len(json.loads(before)['events']) == 2


def test_same_stage_continued_sync_failure_remains_uncertain(tmp_path, monkeypatch):
    digest = 'a' * 64
    record_stage(tmp_path, digest, 'planned', {})
    def fail(path):
        raise OSError('persistent directory sync failure')
    monkeypatch.setattr(private_io, '_sync_directory', fail)
    with pytest.raises(private_io.PrivateWriteUncertain):
        record_stage(tmp_path, digest, 'planned', {})


@pytest.mark.parametrize('pending', ['corrupted', {}, [None]])
def test_invalid_outbox_has_identical_read_write_rejection(tmp_path, monkeypatch, pending):
    monkeypatch.setattr('tools.codex_assets.knowledge_hub.candidate_duplicates.duplicate_inventory', lambda *args:[])
    path = tmp_path / '.tmp/review-consumption/state.json'
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps({'schema_version':2, 'entries':{}, 'pending_events':pending}))
    before = path.read_bytes()
    packet = review_batches.prepare_review_batches(tmp_path, [], [], as_of=dt.date(2026, 10, 6))
    assert packet['consumption_state_status'] == 'needs-review'
    assert packet['consumption_metrics']['throughput']['status'] == 'needs-review'
    with pytest.raises(KnowledgeHubError):
        review_batches._load_consumption(path)
    assert path.read_bytes() == before


def test_legacy_and_v2_review_states_keep_valid_suppression(tmp_path, monkeypatch):
    monkeypatch.setattr('tools.codex_assets.knowledge_hub.candidate_duplicates.duplicate_inventory', lambda *args:[])
    target = tmp_path / 'candidate.md'
    target.write_text('candidate body')
    item = {'id':'candidate', 'path':'candidate.md', 'owner':'explicit-owner', 'status':'reviewing'}
    row = dict(item, item_id='candidate')
    entry = {'decision':'accepted', 'body_sha256':hashlib.sha256(target.read_bytes()).hexdigest(),
             'cycle_sha256':cycle_sha256(tmp_path, item), 'valid_until':'2026-11-05'}
    state = tmp_path / '.tmp/review-consumption/state.json'
    state.parent.mkdir(parents=True)
    for document in ({'candidate':entry}, {'schema_version':2, 'entries':{'candidate':entry}},
                     {'schema_version':2, 'entries':{'candidate':entry}, 'pending_events':[]}):
        state.write_text(json.dumps(document))
        packet = review_batches.prepare_review_batches(tmp_path, [row], [item], as_of=dt.date(2026, 10, 6))
        assert packet['consumption_state_status'] == 'pass'
        assert packet['consumed_or_deferred_count'] == 1
        assert load_state(state)[0] == {'candidate':entry}


def test_valid_pending_outbox_is_visible_to_read_only_packet(tmp_path, monkeypatch):
    from tools.codex_assets.knowledge_hub.review_events import _make_event
    monkeypatch.setattr('tools.codex_assets.knowledge_hub.candidate_duplicates.duplicate_inventory', lambda *args:[])
    state = tmp_path / '.tmp/review-consumption/state.json'
    state.parent.mkdir(parents=True)
    consumption = dict(decision='accepted', body_sha256='a' * 64, cycle_sha256='b' * 64,
                       review_seconds=12, reviewed_at='2026-10-06', next_review_at='',
                       valid_until='2026-11-05', reviewer='explicit-reviewer', evidence_ref='proof')
    event = _make_event('candidate', consumption, 'pending-review')
    state.write_text(json.dumps({'schema_version':2, 'entries':{}, 'pending_events':[event]}))
    before = state.read_bytes()
    packet = review_batches.prepare_review_batches(tmp_path, [], [], as_of=dt.date(2026, 10, 6))
    assert packet['consumption_state_status'] == 'needs-review'
    assert packet['pending_event_count'] == 1
    assert packet['consumption_metrics']['throughput']['status'] == 'needs-review'
    assert review_batches._load_consumption(state)[1] == [event]
    assert state.read_bytes() == before


def test_duplicate_state_json_and_deep_nesting_fail_closed(tmp_path, monkeypatch):
    monkeypatch.setattr('tools.codex_assets.knowledge_hub.candidate_duplicates.duplicate_inventory', lambda *args:[])
    state = tmp_path / '.tmp/review-consumption/state.json'
    state.parent.mkdir(parents=True)
    for raw in ('{"schema_version":2,"entries":{},"pending_events":[],"pending_events":[]}', '[' * 2000 + ']' * 2000):
        state.write_text(raw)
        packet = review_batches.prepare_review_batches(tmp_path, [], [])
        assert packet['consumption_state_status'] == 'needs-review'
        with pytest.raises(KnowledgeHubError):
            review_batches._load_consumption(state)
