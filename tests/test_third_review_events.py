import datetime as dt
import json

import pytest

from test_provider_archive import setup
from tools.codex_assets.knowledge_hub import review_events
from tools.codex_assets.knowledge_hub import private_io, review_batches, review_consumption_cli
from tools.codex_assets.knowledge_hub.common import KnowledgeHubError, registry_items
from tools.codex_assets.knowledge_hub.private_io import PrivateWriteUncertain
from tools.codex_assets.knowledge_hub.provider_archive import archive
from tools.codex_assets.knowledge_hub.review_batches import record_consumption, prepare_review_batches
from tools.codex_assets.knowledge_hub.review_state import load_state


def _consumption(**changes):
    result = dict(decision='accepted', body_sha256='a' * 64, cycle_sha256='b' * 64,
                  review_seconds=12, reviewed_at='2026-10-06', next_review_at='',
                  valid_until='2026-11-05', reviewer='explicit-reviewer', evidence_ref='proof')
    result.update(changes)
    return result


def _path(root):
    return root / '.tmp/review-consumption/events.json'


def test_events_are_metadata_only_and_retries_are_idempotent(tmp_path):
    assert review_events.append_event(tmp_path, 'item', _consumption()) == 'recorded'
    assert review_events.append_event(tmp_path, 'item', _consumption()) == 'already-recorded'
    raw = _path(tmp_path).read_text()
    assert 'explicit-reviewer' not in raw and 'proof' not in raw
    assert len(json.loads(raw)['events']) == 1


def test_independent_explicit_events_preserve_real_durations(tmp_path):
    review_events.append_event(tmp_path, 'item', _consumption(), 'first-review')
    review_events.append_event(tmp_path, 'item', _consumption(review_seconds=None), 'second-review')
    metrics = review_events.event_metrics(tmp_path, dt.date(2026, 10, 6))
    assert metrics['event_count'] == 2 and metrics['distinct_items'] == 1
    assert metrics['review_seconds_total'] == 12
    assert metrics['timed_review_count'] == metrics['untimed_review_count'] == 1
    assert metrics['owner_approval'] is False


def test_explicit_event_conflict_is_not_a_retry(tmp_path):
    review_events.append_event(tmp_path, 'item', _consumption(), 'first-review')
    with pytest.raises(KnowledgeHubError, match='conflicting metadata'):
        review_events.append_event(tmp_path, 'item', _consumption(review_seconds=13), 'first-review')
    assert len(json.loads(_path(tmp_path).read_text())['events']) == 1


@pytest.mark.parametrize('field,value', [
    ('review_seconds', True), ('review_seconds', float('nan')), ('review_seconds', float('inf')),
    ('review_seconds', -1), ('review_seconds', 86401), ('review_seconds', 10 ** 400),
    ('reviewed_at', '20261006'),
    ('reviewed_at', '2026-02-30'), ('recorded_at', '2026-10-06'),
    ('recorded_at', '2026-10-06T25:00:00Z'), ('body_sha256', 7),
    ('event_id', 'bad'), ('item_id', []), ('decision', []), ('unexpected', 'raw'),
])
def test_invalid_events_fail_closed(tmp_path, field, value):
    review_events.append_event(tmp_path, 'item', _consumption())
    document = json.loads(_path(tmp_path).read_text())
    document['events'][0][field] = value
    _path(tmp_path).write_text(json.dumps(document))
    metrics = review_events.event_metrics(tmp_path, dt.date(2026, 10, 6))
    assert metrics['status'] == 'needs-review' and metrics['event_count'] is None
    with pytest.raises((KnowledgeHubError, ValueError)):
        review_events.append_event(tmp_path, 'item', _consumption(), 'another')


@pytest.mark.parametrize('value', [True, '1', 2])
def test_event_schema_version_has_strict_type(tmp_path, value):
    _path(tmp_path).parent.mkdir(parents=True)
    _path(tmp_path).write_text(json.dumps({'schema_version':value, 'events':[]}))
    assert review_events.event_metrics(tmp_path, dt.date(2026, 10, 6))['status'] == 'needs-review'


def test_duplicate_json_fields_and_excessive_nesting_fail_closed(tmp_path):
    _path(tmp_path).parent.mkdir(parents=True)
    for raw in ('{"schema_version":1,"schema_version":1,"events":[]}', '[' * 2000 + ']' * 2000):
        _path(tmp_path).write_text(raw)
        assert review_events.event_metrics(tmp_path, dt.date(2026, 10, 6))['status'] == 'needs-review'
        with pytest.raises(KnowledgeHubError):
            review_events.append_event(tmp_path, 'item', _consumption())


def test_duplicate_and_oversized_events_fail_closed(tmp_path):
    review_events.append_event(tmp_path, 'item', _consumption())
    document = json.loads(_path(tmp_path).read_text())
    document['events'] *= 2
    _path(tmp_path).write_text(json.dumps(document))
    assert review_events.event_metrics(tmp_path, dt.date(2026, 10, 6))['status'] == 'needs-review'
    document['events'] *= 2501
    _path(tmp_path).write_text(json.dumps(document))
    assert review_events.event_metrics(tmp_path, dt.date(2026, 10, 6))['status'] == 'needs-review'


def test_window_includes_boundaries_and_excludes_future(tmp_path):
    for index, date in enumerate(('2026-09-06', '2026-09-07', '2026-10-06', '2026-10-07')):
        review_events.append_event(tmp_path, 'item', _consumption(reviewed_at=date), str(index))
    metrics = review_events.event_metrics(tmp_path, dt.date(2026, 10, 6))
    assert metrics['event_count'] == 2 and metrics['window_start'] == '2026-09-07'


def test_cas_retry_preserves_competing_event(tmp_path, monkeypatch):
    original = review_events.atomic_private_write
    calls = []
    def compete(path, content, **kwargs):
        if not calls:
            calls.append(True)
            monkeypatch.setattr(review_events, 'atomic_private_write', original)
            review_events.append_event(tmp_path, 'competitor', _consumption(), 'other-review')
        return original(path, content, **kwargs)
    monkeypatch.setattr(review_events, 'atomic_private_write', compete)
    assert review_events.append_event(tmp_path, 'item', _consumption(), 'our-review') == 'recorded'
    assert {row['item_id'] for row in json.loads(_path(tmp_path).read_text())['events']} == {'item', 'competitor'}


def test_cas_conflicts_are_bounded(tmp_path, monkeypatch):
    calls = []
    def conflict(*args, **kwargs):
        calls.append(True)
        raise KnowledgeHubError('private write expected hash conflict')
    monkeypatch.setattr(review_events, 'atomic_private_write', conflict)
    with pytest.raises(KnowledgeHubError, match='hash conflict'):
        review_events.append_event(tmp_path, 'item', _consumption())
    assert len(calls) == 3


def test_visible_uncertain_event_retry_repairs_durability(tmp_path, monkeypatch):
    review_events.append_event(tmp_path, 'baseline', _consumption())
    original = private_io._sync_directory
    calls = []
    def fail_once(directory):
        calls.append(directory)
        if len(calls) == 1:
            raise OSError('injected directory sync failure')
        original(directory)
    monkeypatch.setattr(private_io, '_sync_directory', fail_once)
    with pytest.raises(PrivateWriteUncertain):
        review_events.append_event(tmp_path, 'item', _consumption(), 'our-review')
    assert len(json.loads(_path(tmp_path).read_text())['events']) == 2
    assert review_events.append_event(tmp_path, 'item', _consumption(), 'our-review') == 'already-recorded'
    assert len(calls) == 2


def test_consumption_stock_and_throughput_are_distinct(tmp_path):
    root, _, args = setup(tmp_path)
    receipt = archive(root, args)
    inputs = (root, receipt['item_id'], 'accepted', 'explicit-reviewer', 'proof', receipt['content_sha256'])
    first = record_consumption(*inputs, review_seconds=11, review_event_id='first', apply=True)
    repeat = record_consumption(*inputs, review_seconds=11, review_event_id='first', apply=True)
    assert first['event_id'] == repeat['event_id'] and repeat['history_status'] == 'already-recorded'
    record_consumption(*inputs, review_seconds=7, review_event_id='second', apply=True)
    packet = prepare_review_batches(root, [], registry_items(root))
    metrics = packet['consumption_metrics']
    assert metrics['measurement_scope'] == 'current-state-stock' and metrics['recorded_count'] == 1
    assert metrics['review_seconds_total'] == 7
    assert metrics['throughput']['event_count'] == 2 and metrics['throughput']['review_seconds_total'] == 18
    with pytest.raises(KnowledgeHubError, match='conflicting metadata'):
        record_consumption(*inputs, review_seconds=99, review_event_id='second', apply=True)
    assert load_state(root / '.tmp/review-consumption/state.json')[0][receipt['item_id']]['review_seconds'] == 7
    assert registry_items(root)[0]['status'] == 'reviewing'


def test_history_failure_does_not_mask_written_consumption(tmp_path, monkeypatch):
    root, _, args = setup(tmp_path)
    receipt = archive(root, args)
    def fail(*args, **kwargs):
        raise PrivateWriteUncertain('injected uncertain history durability')
    monkeypatch.setattr(review_events, 'append_prepared_event', fail)
    result = record_consumption(root, receipt['item_id'], 'accepted', 'explicit-reviewer',
                                'proof', receipt['content_sha256'], apply=True)
    assert result['status'] == 'recorded' and result['history_status'] == 'needs-review'
    assert receipt['item_id'] in load_state(root / '.tmp/review-consumption/state.json')[0]
    assert result['semantic_owner_approval'] is False


def test_historical_replay_cannot_roll_back_latest_decision(tmp_path):
    root, _, args = setup(tmp_path)
    receipt = archive(root, args)
    inputs = (root, receipt['item_id'], 'accepted', 'explicit-reviewer', 'proof', receipt['content_sha256'])
    record_consumption(*inputs, review_event_id='first', apply=True)
    newer = list(inputs)
    newer[2] = 'changes-requested'
    record_consumption(*newer, review_event_id='second', apply=True)
    before = (root / '.tmp/review-consumption/state.json').read_bytes()
    result = record_consumption(*inputs, review_event_id='first', apply=True)
    assert result['stock_changed'] is False and result['history_status'] == 'already-recorded'
    assert result['consumption']['decision'] == 'changes-requested'
    assert (root / '.tmp/review-consumption/state.json').read_bytes() == before


def test_failed_history_can_recover_after_a_newer_decision(tmp_path, monkeypatch):
    root, _, args = setup(tmp_path)
    receipt = archive(root, args)
    inputs = (root, receipt['item_id'], 'accepted', 'explicit-reviewer', 'proof', receipt['content_sha256'])
    original = review_events.append_prepared_event
    def fail(*args, **kwargs):
        raise OSError('injected history failure')
    monkeypatch.setattr(review_events, 'append_prepared_event', fail)
    first = record_consumption(*inputs, review_seconds=11, review_event_id='first', apply=True)
    assert first['applied'] is True and first['history_status'] == 'needs-review'
    monkeypatch.setattr(review_events, 'append_prepared_event', original)
    newer = list(inputs)
    newer[2] = 'changes-requested'
    record_consumption(*newer, review_seconds=7, review_event_id='second', apply=True)
    assert len(json.loads((root / '.tmp/review-consumption/state.json').read_text())['pending_events']) == 1
    restored = record_consumption(*inputs, review_seconds=11, review_event_id='first', apply=True)
    assert restored['stock_changed'] is False and restored['history_status'] == 'recorded'
    assert restored['consumption']['decision'] == 'changes-requested'
    assert json.loads((root / '.tmp/review-consumption/state.json').read_text())['pending_events'] == []
    metrics = review_events.event_metrics(root, dt.date.today())
    assert metrics['event_count'] == 2 and metrics['review_seconds_total'] == 18


def test_cli_state_uncertainty_is_unknown_and_retry_recovers(tmp_path, monkeypatch, capsys):
    root, _, args = setup(tmp_path)
    receipt = archive(root, args)
    argv = ['--root', str(root), '--item-id', receipt['item_id'], '--decision', 'accepted',
            '--reviewer', 'explicit-reviewer', '--evidence-ref', 'proof',
            '--body-sha256', receipt['content_sha256'], '--review-event-id', 'first', '--apply']
    original = review_batches.atomic_private_write
    def uncertain(*args, **kwargs):
        original(*args, **kwargs)
        raise PrivateWriteUncertain('injected after visible state write')
    monkeypatch.setattr(review_batches, 'atomic_private_write', uncertain)
    assert review_consumption_cli.main(argv) == 3
    result = json.loads(capsys.readouterr().out)
    assert result['applied'] is None and result['status'] == 'needs-recovery-review'
    assert receipt['item_id'] in load_state(root / '.tmp/review-consumption/state.json')[0]
    monkeypatch.setattr(review_batches, 'atomic_private_write', original)
    assert review_consumption_cli.main(argv) == 0
    assert json.loads(capsys.readouterr().out)['stock_changed'] is False
    assert review_events.event_metrics(root, dt.date.today())['event_count'] == 1


def test_cross_day_retry_keeps_original_event_dates(tmp_path, monkeypatch):
    root, _, args = setup(tmp_path)
    receipt = archive(root, args)
    inputs = (root, receipt['item_id'], 'accepted', 'explicit-reviewer', 'proof', receipt['content_sha256'])
    record_consumption(*inputs, review_event_id='first', apply=True)
    before = _path(root).read_bytes()
    real_date = dt.date
    class Tomorrow(real_date):
        @classmethod
        def today(cls):
            return real_date.today() + dt.timedelta(days=1)
    monkeypatch.setattr(review_batches.dt, 'date', Tomorrow)
    result = record_consumption(*inputs, review_event_id='first', apply=True)
    assert result['history_status'] == 'already-recorded' and result['stock_changed'] is False
    assert _path(root).read_bytes() == before
