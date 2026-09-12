from tools.codex_assets.knowledge_hub.common import registry_items, repository_root
from tools.codex_assets.knowledge_hub.temporal_graph import validate_temporal_fields


def test_all_tracked_registry_temporal_metadata_is_strictly_valid():
    failures = []
    for item in registry_items(repository_root()):
        errors = validate_temporal_fields(item)
        if errors:
            failures.append(
                {
                    "id": str(item.get("id", "")),
                    "errors": errors,
                }
            )
    assert failures == []
