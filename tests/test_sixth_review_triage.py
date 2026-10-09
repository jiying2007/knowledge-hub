import ast
import datetime as dt
import hashlib
import json
import os
import pathlib
import subprocess
import sys

import pytest

from tools.codex_assets.knowledge_hub import review_triage

AS_OF = dt.date(2026, 10, 7)
ROOT = pathlib.Path(__file__).resolve().parents[1]


def _action_functions():
    path = ROOT / 'tools/codex_assets/knowledge_hub/reviewing_triage_cli.py'
    names = {'_current_review', '_verified_evidence', 'action_for'}
    nodes = [node for node in ast.parse(path.read_text()).body
             if isinstance(node, ast.FunctionDef) and node.name in names]
    namespace = {'dt':dt, '_body_evidence':review_triage._body_evidence, '_reference':review_triage._reference}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(path), 'exec'), namespace)
    return namespace['action_for']


def _item(root):
    body = '---\nid: candidate\npath: candidate.md\nstatus: reviewing\nowner: declared-owner\nreview_after: 2026-11-01\n---\nbody\n'
    (root / 'candidate.md').write_text(body)
    (root / 'evidence.json').write_text('{"status":"pass"}')
    return dict(id='candidate', path='candidate.md', status='reviewing', owner='declared-owner',
        review_after='2026-11-01', decision_status='candidate', human_reviewed_by='explicit-reviewer',
        human_review_decision='approved-reviewing', content_review_status='accepted',
        human_review_content_sha256=hashlib.sha256(body.encode()).hexdigest(),
        evidence_validation_status='verified', evidence_refs=['evidence.json'], validation_refs=[])


@pytest.mark.parametrize('changes', [
    {'human_review_decision':'rejected'}, {'content_review_status':'rejected'},
    {'evidence_validation_status':'unverified'}, {'evidence_refs':[]},
    {'human_review_decision':'accept-as-review-record'}, {'evidence_refs':['missing.json']},
    {'human_review_content_sha256':'a'*64}, {'review_after':'2026-10-01'},
    {'evidence_refs':['rtk arbitrary command']},
])
def test_rejected_unverified_stale_or_record_only_review_cannot_be_owner_ready(tmp_path, changes):
    row = dict(_item(tmp_path), **changes)
    before = (tmp_path / 'candidate.md').read_bytes()
    assert _action_functions()(row, review_triage._EvidenceReader(tmp_path), AS_OF) == 'owner-review-and-validation'
    assert (tmp_path / 'candidate.md').read_bytes() == before and row['status'] == 'reviewing'


def test_explicit_current_review_and_local_evidence_only_prepare_owner_packet(tmp_path):
    row = _item(tmp_path)
    before = dict(row)
    assert _action_functions()(row, review_triage._EvidenceReader(tmp_path), AS_OF) == 'owner-ready-validation-pending'
    assert row == before and row['status'] == 'reviewing'


def test_body_confirmation_uses_shared_total_budget(tmp_path, monkeypatch):
    row = _item(tmp_path)
    size = (tmp_path / 'candidate.md').stat().st_size
    monkeypatch.setattr(review_triage, 'MAX_TOTAL_BYTES', size)
    actual = []
    original = review_triage.read_repository_bytes_bounded
    def measured(*args, **kwargs):
        raw = original(*args, **kwargs)
        actual.append(len(raw))
        return raw
    monkeypatch.setattr(review_triage, 'read_repository_bytes_bounded', measured)
    row.update(evidence_refs=[], validation_refs=[])
    result = review_triage.prepare_review_triage(tmp_path, [dict(item_id='candidate', days_until_review=25)],
        [row], [], [], AS_OF)
    assert result['evidence_bytes_read'] == sum(actual) == size
    assert result['evidence_byte_overflow'] and result['metadata_ready_count'] == 0


def test_successful_confirmation_and_reference_reads_are_fully_counted(tmp_path):
    row = _item(tmp_path)
    result = review_triage.prepare_review_triage(tmp_path, [dict(item_id='candidate', days_until_review=25)],
        [row], [], [], AS_OF)
    expected = 2 * (tmp_path / 'candidate.md').stat().st_size + (tmp_path / 'evidence.json').stat().st_size
    assert result['evidence_bytes_read'] == expected and not result['evidence_byte_overflow']
    assert result['metadata_ready_count'] == 1 and not result['owner_decision_generated']


@pytest.mark.parametrize('decision,expected', [
    ('rejected', 'owner-review-and-validation'), ('approved-reviewing', 'owner-ready-validation-pending')])
def test_real_readonly_cli_uses_same_prepared_classification(tmp_path, decision, expected):
    item = _item(tmp_path)
    item['human_review_decision'] = decision
    registry = tmp_path / 'registry'
    registry.mkdir()
    path = registry / 'items.jsonl'
    path.write_text(json.dumps(item) + '\n')
    before = path.read_bytes()
    result = subprocess.run(['rtk', sys.executable, '-m',
        'tools.codex_assets.knowledge_hub.reviewing_triage_cli', str(tmp_path),
        '--json', '--as-of', AS_OF.isoformat()], cwd=str(ROOT),
        env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1'), capture_output=True, text=True, timeout=10)
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload['items'][0]['recommended_action'] == expected
    assert payload['by_recommended_action'] == {expected:1}
    assert payload['read_only'] and payload['report_only']
    assert path.read_bytes() == before and not (tmp_path / '.tmp').exists()
