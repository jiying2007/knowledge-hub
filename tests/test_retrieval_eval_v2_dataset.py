from tools.codex_assets.knowledge_hub.common import repository_root
from tools.codex_assets.knowledge_hub.eval_v2 import load_dataset


def test_retrieval_eval_v2_shadow_dataset_is_versioned_and_valid():
    payload = load_dataset(repository_root() / "tests/fixtures/retrieval_cases_v2.jsonl")
    assert payload["schema_version"] == "knowledge-hub.eval-dataset.v2"
    assert payload["case_count"] >= 10
    assert len(payload["dataset_sha256"]) == 64
