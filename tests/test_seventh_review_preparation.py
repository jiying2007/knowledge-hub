import copy
import datetime as dt
import json

import pytest

from tools.codex_assets.knowledge_hub import review_triage
from tools.codex_assets.knowledge_hub.common import KnowledgeHubError
from tools.codex_assets.knowledge_hub.review_preparation import prepare_owner_preparation


def _row(key, owner='routing-owner', kind='item', retired=False):
    return dict(entity_id=key, entity_type=kind, owner=owner, warning_equivalent=True,
        status='reviewing', review_after='2026-09-01', classifications=['owner-semantic-review-due'],
        body_path='projects/example/current/' + key + '.md',
        body_evidence={'status':'metadata-ready', 'sha256':'a'*64, 'human_review_renewed':False},
        source_evidence=dict(retired_provenance_only=retired, source_check_executed=False, authority_verified=False),
        references=[dict(status='replay-command-not-executed', reference_sha256='b'*64,
                         raw_command='must not execute', body='must not export')])


def test_owner_packets_reuse_metadata_without_reads_or_assignments():
    rows = [_row('item'), _row('source', kind='source'), _row('retired', kind='source', retired=True)]
    before = copy.deepcopy(rows)
    result = prepare_owner_preparation(rows)
    assert result['eligible_count'] == result['selected_count'] == 3
    assert result['remaining_count'] == 0 and not result['overflow']
    packet = result['packets'][0]
    assert packet['declared_owner'] == 'routing-owner' and not result['owners'][0]['real_signer_confirmed']
    assert {result['decision_kinds'][row['lane']] for row in packet['rows']} == {
        'candidate-scope-and-evidence', 'current-source-authority', 'retired-provenance-boundary'}
    assert rows == before and not result['owner_approval_performed'] and not result['review_dates_changed']
    assert 'must not' not in json.dumps(result)


def test_type_and_owner_round_robin_preserve_remaining_counts():
    rows = [_row('item-'+str(n), 'owner-a') for n in range(20)]
    rows += [_row('source', 'owner-a', 'source'), _row('retired', 'owner-a', 'source', True),
             _row('second', 'owner-b')]
    result = prepare_owner_preparation(rows, packet_size=3, total_limit=4)
    assert result['selected_count'] == 4 and result['remaining_count'] == 19 and result['overflow']
    first, second = result['packets']
    assert {row['lane'] for row in first['rows']} == {'item-candidate', 'source-current', 'source-retired'}
    assert len(second['rows']) == 1
    assert sum(owner['remaining_count'] for owner in result['owners']) == result['remaining_count']


def test_byte_budget_reports_partial_packet_without_claiming_full_coverage():
    rows = [_row(str(n)) for n in range(20)]
    result = prepare_owner_preparation(rows, maximum_bytes=4000)
    assert len(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()) <= 4000
    assert result['selected_count'] < 20 and result['remaining_count'] > 0 and result['overflow']


@pytest.mark.parametrize('kwargs', [{'owner_limit':True}, {'packet_size':0}, {'total_limit':501},
                                  {'maximum_bytes':0}])
def test_invalid_packet_budget_fails_closed(kwargs):
    with pytest.raises(KnowledgeHubError, match='budget'):
        prepare_owner_preparation([], **kwargs)


def test_private_rows_and_reference_material_are_not_exposed():
    private = dict(_row('private'), visibility='personal-local')
    public = _row('public')
    public['references'] = [dict(status='external-evidence-required', reference_sha256='c'*64,
        path='/home/operator/.ssh/id_rsa', raw_url='https://secret.invalid/token', body='RAW PRIVATE BODY')]
    result = prepare_owner_preparation([private, public])
    assert result['privacy_excluded_count'] == 1 and result['eligible_count'] == 1
    serialized = json.dumps(result)
    assert 'private' not in serialized and '.ssh' not in serialized and 'secret.invalid' not in serialized
    assert 'RAW PRIVATE BODY' not in serialized
    assert result['packets'][0]['rows'][0]['reference_status_counts'] == {'external-evidence-required':1}


def test_large_owner_is_split_without_silent_ten_row_truncation():
    result = prepare_owner_preparation([_row(str(n)) for n in range(109)], total_limit=500)
    assert result['selected_count'] == 109 and result['remaining_count'] == 0
    assert [len(packet['rows']) for packet in result['packets']] == [10]*10 + [9]
    assert result['owners'][0]['packet_count'] == 11


def test_hidden_owners_and_packet_cap_keep_honest_remaining_counts():
    rows = [_row(str(n), 'owner-'+str(n)) for n in range(15)]
    result = prepare_owner_preparation(rows, owner_limit=12, total_limit=500)
    assert result['owner_count'] == 15 and result['selected_count'] == 12
    assert result['remaining_count'] == 3 and result['overflow']
    result = prepare_owner_preparation([_row(str(n)) for n in range(100)], packet_size=1, total_limit=500)
    assert len(result['packets']) == result['selected_count'] == 50
    assert result['remaining_count'] == 50 and result['overflow']


def test_triage_projection_does_not_touch_stock_body_or_retired_origin(tmp_path, monkeypatch):
    body = '---\nid: item\npath: item.md\nowner: declared\nstatus: reviewing\nreview_after: 2026-09-01\n---\nbody\n'
    (tmp_path / 'item.md').write_text(body)
    stock = tmp_path / '.tmp/review-consumption/state.json'
    stock.parent.mkdir(parents=True)
    stock.write_text('{"schema_version":2,"entries":{},"pending_events":[]}')
    before = {path:path.read_bytes() for path in (tmp_path / 'item.md', stock)}
    item = dict(id='item', path='item.md', owner='declared', status='reviewing', review_after='2026-09-01')
    source = dict(id='retired', path='sources/retired', status='retired', owner='declared',
        review_after='2026-09-01', origin_path='~/retired-origin-must-not-probe', evidence_refs=[])
    original = review_triage.pathlib.Path.expanduser
    def deny_origin(path):
        if 'retired-origin' in str(path):
            pytest.fail('retired origin was probed')
        return original(path)
    monkeypatch.setattr(review_triage.pathlib.Path, 'expanduser', deny_origin)
    result = review_triage.prepare_review_triage(tmp_path, [dict(item_id='item', days_until_review=-36)],
        [item], [source], [], dt.date(2026, 10, 7), detail_limit=1)
    projection = result['owner_preparation']
    assert projection['eligible_count'] == 2 and projection['selected_count'] == 1
    assert projection['remaining_count'] == 1 and projection['overflow']
    assert result['detail_overflow'] and all(path.read_bytes() == raw for path,raw in before.items())
