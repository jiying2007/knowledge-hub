from tools.codex_assets.knowledge_hub import (
    product_gate,
    product_gate_parallel,
    product_gate_support,
)


def test_product_gate_split_compatibility_surface():
    assert product_gate._project_readiness is product_gate_support._project_readiness
    assert product_gate._restore_state is product_gate_support._restore_state
    assert product_gate._source_runtime_ready is product_gate_support._source_runtime_ready
    assert callable(product_gate_parallel.collect_parallel_results)
    assert product_gate.UNIT_TEST_TIMEOUT_SECONDS == 180
