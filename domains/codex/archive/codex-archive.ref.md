# Codex Archive Hard-Migration Boundary

## 摘要

`codex-archive` 是已登记且已硬迁移的 Codex workflow history source。Knowledge Hub 现在以 Hub 内 `sources/codex-archive` 和 `domains/codex/archive/source-docs/codex-archive` 为控制入口；旧 `~/codex/docs/archive` 只保留在 `origin_path`、tombstone 和迁移 manifest 中作 provenance，不再作为新增归档、默认读取或 active source 入口。

## Source Identity

- source_id：`codex-archive`
- hub_source_path：`sources/codex-archive`
- canonical_target：`domains/codex/archive/source-docs/codex-archive`
- origin_path：`~/codex/docs/archive`（retired provenance only）
- role：`hub-migrated-source`
- authority：`knowledge-hub-canonical`
- write_policy：`knowledge-hub-only`
- check：`rtk test -d sources/codex-archive`
- canonical_manifest：`artifacts/manifests/source-hard-migration-20260624.jsonl`
- decommission_manifest：`artifacts/manifests/source-hard-decommission-20260624.jsonl`

## 使用边界

- 可用于追溯 Codex 工作流、归档记录、历史决策和治理演进。
- 新增 Codex 归档必须进入 Knowledge Hub 的 `domains/codex/`、`artifacts/manifests/` 或 `sources/` 控制面，不得默认写回旧 archive 路径。
- 不把历史 archive 直接当作当前有效规则；提升为 active governance 前必须新增 manifest、owner review、promotion_decision、rollback 和验证证据。
- 不处理 `~/codex` 当前工作区脏变更；Codex 资产链路删除旧入口前需要在 `~/codex` 单独做权限、dirty worktree 和 apply 链路门禁。

## 验证

```bash
rtk test -d sources/codex-archive
rtk bash tools/knowledge-check.sh --dry-run --json
```

## Review

- owner：`leiwenjun`
- review_after：`2026-09-19`
- 下一次复核内容：旧 `origin_path` 删除前确认 tombstone、Hub canonical 和 Codex 自动化新归档入口是否闭环。
