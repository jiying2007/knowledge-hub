"""The sixth strategy cannot inherit fifth-strategy qualification."""

from tools.codex_assets.knowledge_hub import metrics
from tools.codex_assets.knowledge_hub.common import repository_root
from tools.codex_assets.knowledge_hub.retrieval_telemetry import IMPLEMENTATION_GENERATION, PERFORMANCE_CONTRACT
from tools.codex_assets.knowledge_hub.schemas import validate_instance


def test_fifth_generation_remains_history_without_sixth_performance_credit():
    previous = {'performance_contract': PERFORMANCE_CONTRACT,
                'implementation_generation': 'knowledge-retrieval-implementation-20261007-v2'}
    current = dict(previous, implementation_generation=IMPLEMENTATION_GENERATION)
    assert metrics._current_performance_rows([previous, current]) == [current]
    assert previous['implementation_generation'].endswith('v2')


def test_current_metrics_schema_rejects_fifth_generation():
    root = repository_root()
    report = metrics.local_metrics(root)
    assert validate_instance(root, 'local-metrics-v5', report)['status'] == 'pass'
    report['measurement_contract']['implementation_generation'] = 'knowledge-retrieval-implementation-20261007-v2'
    assert validate_instance(root, 'local-metrics-v5', report)['status'] == 'fail'
