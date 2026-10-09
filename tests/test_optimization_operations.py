import datetime as dt
import json

from tools.codex_assets.knowledge_hub.metrics import local_metrics, local_metrics_summary
from tools.codex_assets.knowledge_hub.review_batches import build_review_batches
from tools.codex_assets.knowledge_hub.provider_capabilities import capabilities
from test_metrics import _interaction
from test_provider_archive import setup


def test_recent_health_does_not_inherit_stale_lifetime_samples(tmp_path):
    cache = tmp_path / '.cache/knowledge-hub'
    cache.mkdir(parents=True)
    for kind in ('search', 'context'):
        rows = [_interaction('old-' + str(i), kind=kind) for i in range(30)]
        (cache / (kind + '-telemetry.jsonl')).write_text(''.join(json.dumps(row) + '\n' for row in rows))
    payload = local_metrics(tmp_path, dt.date(2026, 10, 6))
    assert payload['adoption']['qualification_scope'] == 'lifetime-local-observation'
    recent = local_metrics_summary(payload)['recent_health']
    assert recent['current_status'] == 'insufficient-data'
    assert recent['windows']['30']['context_count'] == 0
    assert recent['windows']['30']['feedback_count'] == 0
    assert recent['production_qualification'] is False


def test_review_packets_separate_responsibilities_and_bound_selection():
    rows = [dict(item_id='item-' + str(i), path='governance/a.md', owner='owner',
                 status=status, days_until_review=-i, review_class='ordinary')
            for i, status in enumerate(['archived', 'reviewing', 'active'])]
    packet = build_review_batches(rows, 2)
    batch = packet['batches'][0]
    assert batch['selected_count'] == 2 and batch['remaining_count'] == 1
    assert [row['lane'] for row in batch['rows']] == ['current-validity', 'candidate-decision']
    assert packet['selection_is_authorization'] is False


def test_disabling_archive_does_not_disable_readonly_capabilities(tmp_path):
    root, _, _ = setup(tmp_path)
    policy_path = root / 'registry/provider-archive-policy.json'
    policy = json.loads(policy_path.read_text())
    policy['enabled'] = False
    policy_path.write_text(json.dumps(policy))
    result = capabilities(root)['operations']
    assert result['context']['available'] and not result['context']['write_allowed']
    assert not result['archive']['write_allowed']
    assert not result['archive']['active_promotion_allowed']
