import datetime as dt
import hashlib
import json
import pathlib
import subprocess
import sys

import pytest

from tools.codex_assets.knowledge_hub.common import KnowledgeHubError
from tools.codex_assets.knowledge_hub.review_triage import prepare_review_triage


AS_OF = dt.date(2026, 10, 7)


def _fixture(root, **changes):
    item = dict(id='candidate', path='candidate.md', status='reviewing', owner='declared-owner',
                review_after='2026-09-01', evidence_refs=[], validation_refs=[])
    item.update(changes)
    body = '---\n' + '\n'.join('{}: {}'.format(field, item[field])
                              for field in ('id', 'path', 'status', 'owner', 'review_after')) + '\n---\n正文\n'
    (root / item['path']).write_text(body)
    row = dict(item_id=item['id'], days_until_review=-36)
    return item, row


def test_identical_prior_human_hash_prepares_metadata_but_never_renews_review(tmp_path):
    item, row = _fixture(tmp_path)
    item['human_review_content_sha256'] = hashlib.sha256((tmp_path / item['path']).read_bytes()).hexdigest()
    before = (tmp_path / item['path']).read_bytes()
    report = prepare_review_triage(tmp_path, [row], [item], [], [], AS_OF)
    assert report['metadata_ready_count'] == report['warning_equivalent_count'] == 1
    prepared = report['rows'][0]
    assert prepared['body_evidence']['prior_human_content_hash_matches']
    assert prepared['semantic_revalidation_required'] and not prepared['automatic_closure_allowed']
    assert not prepared['owner_approval_performed']
    assert report['automatically_closed_warning_count'] == 0
    assert item['review_after'] == '2026-09-01' and (tmp_path / item['path']).read_bytes() == before


def test_body_metadata_and_hash_share_one_snapshot_under_aba(tmp_path, monkeypatch):
    from tools.codex_assets.knowledge_hub import review_triage
    from tools.codex_assets.knowledge_hub.common import load_markdown
    item, row = _fixture(tmp_path)
    path = tmp_path / item['path']
    matching_b = path.read_bytes()
    mismatching_a = matching_b.replace(b'owner: declared-owner', b'owner: different-owner')
    path.write_bytes(mismatching_a)
    calls = []
    def swapping_load(target):
        calls.append(1)
        target.write_bytes(matching_b)
        try:
            return load_markdown(target)
        finally:
            target.write_bytes(mismatching_a)
    # The old disk parser would certify B metadata with A's hash after ABA.
    monkeypatch.setattr(review_triage, 'load_markdown', swapping_load, raising=False)
    report = prepare_review_triage(tmp_path, [row], [item], [], [], AS_OF)
    evidence = report['rows'][0]['body_evidence']
    assert evidence['status'] == 'metadata-mismatch'
    assert evidence['sha256'] == hashlib.sha256(mismatching_a).hexdigest()
    assert not calls and path.read_bytes() == mismatching_a


def test_body_one_mib_limit_cannot_be_bypassed_by_another_parser(tmp_path, monkeypatch):
    from tools.codex_assets.knowledge_hub import review_triage
    item, row = _fixture(tmp_path)
    path = tmp_path / item['path']
    head = path.read_bytes()
    monkeypatch.setattr(review_triage, 'load_markdown', lambda *args:pytest.fail('must parse the bounded snapshot'), raising=False)
    path.write_bytes(head + b'x' * (review_triage.MAX_FILE_BYTES - len(head)))
    report = prepare_review_triage(tmp_path, [row], [item], [], [], AS_OF)
    assert report['metadata_ready_count'] == 1
    assert report['evidence_bytes_read'] == 2 * review_triage.MAX_FILE_BYTES
    path.write_bytes(path.read_bytes() + b'x')
    report = prepare_review_triage(tmp_path, [row], [item], [], [], AS_OF)
    assert report['metadata_ready_count'] == 0
    assert report['rows'][0]['body_evidence']['status'] == 'body-unavailable-or-over-budget'


def test_local_hash_reuse_external_pointer_and_replay_are_separate(tmp_path):
    local = tmp_path / 'evidence.json'
    local.write_text('{"status":"pass"}')
    item, row = _fixture(tmp_path, evidence_refs=['evidence.json', 'https://external.invalid/owner-proof', 'rtk arbitrary command'])
    report = prepare_review_triage(tmp_path, [row], [item], [], [], AS_OF)
    refs = report['rows'][0]['references']
    assert [ref['status'] for ref in refs] == ['local-hash-confirmed', 'external-evidence-required', 'replay-command-not-executed']
    assert refs[0]['sha256'] == hashlib.sha256(local.read_bytes()).hexdigest()
    assert all(ref['reuse_scope'] == 'provenance-only' and not ref['semantic_verified'] for ref in refs)
    assert 'external.invalid' not in json.dumps(report)
    assert 'external-evidence-required' in report['rows'][0]['classifications']


def test_legacy_replay_notes_and_unknown_ids_are_not_missing_files(tmp_path):
    tools = tmp_path / 'tools'
    tools.mkdir()
    (tools / 'knowledge-check.sh').write_text('must never execute')
    refs = ['tools/knowledge-check.sh --dry-run --json', 'field-capture-sha256:' + 'a'*64,
            '说明：后续需要真人补充现场证据', 'opaque-evidence-reference']
    item, row = _fixture(tmp_path, evidence_refs=refs)
    report = prepare_review_triage(tmp_path, [row], [item], [], [], AS_OF)
    statuses = [ref['status'] for ref in report['rows'][0]['references']]
    assert statuses == ['legacy-replay-not-executed', 'metadata-note', 'metadata-note', 'unknown-pointer']
    assert 'local-evidence-unavailable' not in report['rows'][0]['classifications']
    assert 'evidence-pointer-unresolved' in report['rows'][0]['classifications']
    assert not report['rows'][0]['automatic_closure_allowed']


def test_literal_file_names_with_spaces_remain_valid_evidence(tmp_path):
    notes = tmp_path / 'notes'
    notes.mkdir()
    target = notes / 'real evidence notes.md'
    target.write_text('existing evidence')
    item, row = _fixture(tmp_path, evidence_refs=['notes/real evidence notes.md', 'docs/missing evidence.md'])
    report = prepare_review_triage(tmp_path, [row], [item], [], [], AS_OF)
    references = report['rows'][0]['references']
    assert references[0]['status'] == 'local-hash-confirmed'
    assert references[0]['sha256'] == hashlib.sha256(target.read_bytes()).hexdigest()
    assert references[1]['status'] == 'local-unavailable-or-over-budget'


def test_missing_origin_and_retired_provenance_do_not_restore_or_probe_source(tmp_path):
    source_dir = tmp_path / 'sources/current'
    source_dir.mkdir(parents=True)
    sources = [dict(id='current', path='sources/current', origin_path=str(tmp_path / 'missing-original'), review_after='2026-09-01'),
               dict(id='retired', path='sources/missing', status='retired', origin_path='~/retired-missing-origin', review_after='2026-09-01')]
    report = prepare_review_triage(tmp_path, [], [], sources, [], AS_OF)
    current, retired = report['rows']
    assert current['source_evidence']['hub_path_present']
    assert current['source_evidence']['origin_status'] == 'unavailable'
    assert retired['source_evidence']['origin_status'] == 'retired-provenance-not-probed'
    assert 'source-path-unavailable' in current['classifications']
    assert report['warning_counts']['stale_sources'] == 2
    assert not report['active_promoted'] and not (tmp_path / 'sources/missing').exists()


def test_expired_stock_cache_cannot_suppress_semantic_review(tmp_path):
    item, row = _fixture(tmp_path)
    state = tmp_path / '.tmp/review-consumption/state.json'
    state.parent.mkdir(parents=True)
    state.write_text(json.dumps({item['id']:{'decision':'accepted', 'valid_until':'2026-10-01'}}))
    report = prepare_review_triage(tmp_path, [row], [item], [], [], AS_OF)
    assert 'expired-review-cache' in report['rows'][0]['classifications']
    assert report['rows'][0]['semantic_revalidation_required']


def test_check_cache_expiry_and_result_hash_are_report_only(tmp_path):
    base = tmp_path / '.cache/knowledge-hub/checks'
    base.mkdir(parents=True)
    result = {'status':'pass'}
    digest = hashlib.sha256(json.dumps(result, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    (base / 'expired.json').write_text(json.dumps(dict(generated_at='2026-09-01T00:00:00Z', result=result, result_sha256=digest)))
    (base / 'invalid.json').write_text(json.dumps(dict(generated_at='2026-10-07T00:00:00Z', result=result, result_sha256='0'*64)))
    report = prepare_review_triage(tmp_path, [], [], [], [], AS_OF)
    caches = report['runtime_check_cache']
    assert caches['expired_count'] == 1
    assert {row['status'] for row in caches['rows']} == {'expired', 'invalid-result-hash'}
    assert not caches['reuse_authorized'] and all(not row['reuse_allowed'] for row in caches['rows'])


def test_symlink_body_and_missing_owner_are_not_metadata_ready(tmp_path):
    outside = tmp_path / 'external'
    outside.write_text('not a governed body')
    (tmp_path / 'candidate.md').symlink_to(outside)
    item = dict(id='candidate', path='candidate.md', owner='', status='reviewing')
    row = dict(item_id='candidate', days_until_review=-1)
    report = prepare_review_triage(tmp_path, [row], [item], [], [], AS_OF)
    assert report['metadata_ready_count'] == 0
    assert 'real-owner-assignment-required' in report['rows'][0]['classifications']


def test_detail_limit_preserves_all_counts_without_closing_owner_gate(tmp_path):
    gates = [dict(worksheet_id='gate-'+str(i)) for i in range(3)]
    report = prepare_review_triage(tmp_path, [], [], [], gates, AS_OF, detail_limit=1)
    assert report['entity_count'] == 3 and report['detail_overflow'] and len(report['rows']) == 1
    assert report['classifications']['owner-gate-open'] == 3
    assert not report['rows'][0]['automatic_closure_allowed']
    with pytest.raises(KnowledgeHubError, match='budget'):
        prepare_review_triage(tmp_path, [], [], [], [{}] * 5001, AS_OF)


def test_cache_enumeration_and_evidence_bytes_are_bounded(tmp_path, monkeypatch):
    from tools.codex_assets.knowledge_hub import review_triage
    base = tmp_path / '.cache/knowledge-hub/checks'
    base.mkdir(parents=True)
    for i in range(34):
        (base / (str(i) + '.json')).write_text('{}')
    report = prepare_review_triage(tmp_path, [], [], [], [], AS_OF)
    assert report['runtime_check_cache']['overflow']
    assert len(report['runtime_check_cache']['rows']) == 32
    monkeypatch.setattr(review_triage, 'MAX_TOTAL_BYTES', 16)
    item, row = _fixture(tmp_path)
    report = prepare_review_triage(tmp_path, [row], [item], [], [], AS_OF)
    assert report['metadata_ready_count'] == 0
    assert report['evidence_bytes_read'] <= 16


def test_cache_symlink_cannot_read_external_inventory(tmp_path):
    outside = tmp_path / 'outside'
    outside.mkdir()
    (outside / 'private.json').write_text('{}')
    base = tmp_path / '.cache/knowledge-hub'
    base.mkdir(parents=True)
    (base / 'checks').symlink_to(outside, target_is_directory=True)
    report = prepare_review_triage(tmp_path, [], [], [], [], AS_OF)
    assert report['runtime_check_cache']['status'] == 'needs-review'
    assert not report['runtime_check_cache']['rows']


def test_cli_disallows_report_apply_before_any_registry_write(tmp_path):
    script = pathlib.Path(__file__).resolve().parents[1] / 'tools/codex_assets/knowledge_hub/review_after_cli.py'
    result = subprocess.run(['rtk', sys.executable, str(script), str(tmp_path), '--json', '--apply'], capture_output=True, text=True)
    assert result.returncode != 0 and '--apply requires --consume-item' in result.stderr
    assert not list(tmp_path.iterdir())


def test_cli_includes_retired_due_provenance_without_reactivating_source(tmp_path):
    item, _ = _fixture(tmp_path)
    registry = tmp_path / 'registry'
    registry.mkdir()
    (registry / 'items.jsonl').write_text(json.dumps(item) + '\n')
    (registry / 'sources.json').write_text('{"sources":[]}')
    source = dict(id='retired', path='sources/retired', status='retired', review_after='2026-09-01')
    ledger = registry / 'retired-sources.jsonl'
    ledger.write_text(json.dumps(source) + '\n')
    policy = dict(default_class='ordinary', classes={'ordinary':dict(stale_severity='warning', ai_first_action='auto-triage')}, rules=[])
    (registry / 'review-risk-policy.json').write_text(json.dumps(policy))
    manifests = tmp_path / 'artifacts/manifests'
    manifests.mkdir(parents=True)
    (manifests / 'test-owner-decision-worksheets-1.jsonl').write_text('')
    before = ledger.read_bytes()
    script = pathlib.Path(__file__).resolve().parents[1] / 'tools/codex_assets/knowledge_hub/review_after_cli.py'
    result = subprocess.run(['rtk', sys.executable, str(script), str(tmp_path), '--json', '--as-of', AS_OF.isoformat()], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report['counts']['sources_total'] == report['counts']['stale_sources'] == 1
    assert report['evidence_triage']['warning_equivalent_count'] == 2
    assert report['evidence_triage']['classifications']['retired-provenance-review'] == 1
    assert ledger.read_bytes() == before and not (tmp_path / source['path']).exists()
