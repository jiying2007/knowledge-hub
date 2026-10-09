"""Sixth-generation usage cannot qualify the seventh retrieval strategy."""

from tools.codex_assets.knowledge_hub import metrics
from tools.codex_assets.knowledge_hub.common import repository_root
from tools.codex_assets.knowledge_hub.retrieval_telemetry import IMPLEMENTATION_GENERATION, PERFORMANCE_CONTRACT
from tools.codex_assets.knowledge_hub.schemas import validate_instance


def test_previous_usage_keeps_its_identity_without_current_performance_credit():
    assert IMPLEMENTATION_GENERATION != 'knowledge-retrieval-implementation-20261007-v3'
    previous = {'performance_contract': PERFORMANCE_CONTRACT,
                'implementation_generation': 'knowledge-retrieval-implementation-20261007-v3'}
    current = dict(previous, implementation_generation=IMPLEMENTATION_GENERATION)
    assert metrics._current_performance_rows([previous, current]) == [current]
    assert previous['implementation_generation'].endswith('v3')


def test_schema_accepts_current_report_and_rejects_v3_qualification():
    root = repository_root()
    report = metrics.local_metrics(root)
    assert validate_instance(root, 'local-metrics-v5', report)['status'] == 'pass'
    report['measurement_contract']['implementation_generation'] = 'knowledge-retrieval-implementation-20261007-v3'
    rejected = validate_instance(root, 'local-metrics-v5', report)
    assert rejected['status'] == 'fail'
    assert any(error['path'] == '$.measurement_contract.implementation_generation' for error in rejected['errors'])
