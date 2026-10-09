"""The eighth retrieval strategy cannot inherit v4 qualification."""

from tools.codex_assets.knowledge_hub import metrics
from tools.codex_assets.knowledge_hub.common import repository_root
from tools.codex_assets.knowledge_hub.retrieval_telemetry import IMPLEMENTATION_GENERATION, PERFORMANCE_CONTRACT
from tools.codex_assets.knowledge_hub.schemas import validate_instance


def test_v5_qualification_excludes_v4_without_rewriting_usage():
    assert IMPLEMENTATION_GENERATION == 'knowledge-retrieval-implementation-20261008-v5'
    previous = {'performance_contract': PERFORMANCE_CONTRACT,
                'implementation_generation': 'knowledge-retrieval-implementation-20261007-v4'}
    current = dict(previous, implementation_generation=IMPLEMENTATION_GENERATION)
    assert metrics._current_performance_rows([previous, current]) == [current]
    assert previous['implementation_generation'].endswith('v4')


def test_current_schema_accepts_v5_and_rejects_v4():
    root = repository_root()
    report = metrics.local_metrics(root)
    assert validate_instance(root, 'local-metrics-v5', report)['status'] == 'pass'
    report['measurement_contract']['implementation_generation'] = 'knowledge-retrieval-implementation-20261007-v4'
    rejected = validate_instance(root, 'local-metrics-v5', report)
    assert rejected['status'] == 'fail'
    assert any(error['path'] == '$.measurement_contract.implementation_generation' for error in rejected['errors'])
