# Source hard migration 2026-06-25

本报告记录 Knowledge Hub 硬迁移的当前执行结果。长期知识正文以 Hub target 为准，外部 origin 只保留 tombstone/provenance。

本批次将 `embedded-knowledge` 的过渡快照正文完整归位到 `domains/embedded/*`，旧快照目录已删除；`sources/embedded-knowledge` 只保留 source 控制面。

- registered_sources: 18
- migration_rows: 960
- planned_copy_or_artifact: 553
- copied: 0
- existing_verified: 553
- retired_origin_missing: 10
- retired_manifest_reused: 942
- decommission_rows: 18

## 验证

- 后续必须运行 `rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics`。
- 删除外部 source 前必须复核 `source-hard-decommission-*.jsonl` 和 `registry/source-tombstones.jsonl`。
