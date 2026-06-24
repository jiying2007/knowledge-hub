# Source hard migration 2026-06-24

本报告记录 Knowledge Hub 硬迁移的当前执行结果。长期知识正文以 Hub target 为准，外部 origin 只保留 tombstone/provenance。

- registered_sources: 18
- migration_rows: 973
- planned_copy_or_artifact: 566
- copied: 29
- existing_verified: 537
- decommission_rows: 18

## 验证

- 后续必须运行 `rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics`。
- 删除外部 source 前必须复核 `source-hard-decommission-*.jsonl` 和 `registry/source-tombstones.jsonl`。
