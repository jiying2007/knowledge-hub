"""Previous lexical observations cannot qualify the new concept implementation."""

from tools.codex_assets.knowledge_hub import metrics
from tools.codex_assets.knowledge_hub.retrieval_telemetry import IMPLEMENTATION_GENERATION, PERFORMANCE_CONTRACT
from tools.codex_assets.knowledge_hub.common import repository_root
from tools.codex_assets.knowledge_hub.schemas import validate_instance


def test_new_generation_does_not_relabel_previous_observations():
    assert IMPLEMENTATION_GENERATION != 'knowledge-retrieval-implementation-20260731-v1'
    previous = {'performance_contract':PERFORMANCE_CONTRACT,
                'implementation_generation':'knowledge-retrieval-implementation-20260731-v1'}
    current = dict(previous, implementation_generation=IMPLEMENTATION_GENERATION)
    assert metrics._current_performance_rows([previous, current]) == [current]
    assert previous['implementation_generation'].endswith('20260731-v1')


def test_metrics_schema_accepts_current_generation_and_rejects_legacy():
    root = repository_root()
    report = metrics.local_metrics(root)
    assert validate_instance(root, 'local-metrics-v5', report)['status'] == 'pass'
    report['measurement_contract']['implementation_generation'] = 'knowledge-retrieval-implementation-20260731-v1'
    rejected = validate_instance(root, 'local-metrics-v5', report)
    assert rejected['status'] == 'fail'
    assert any(error['path'] == '$.measurement_contract.implementation_generation' for error in rejected['errors'])
