# Codex Archive Reference Boundary

## 摘要

`codex-archive` 是已登记的 Codex workflow history source。Knowledge Hub 对它采用 reference-first：默认通过 Codex archive tools 和原始归档路径读取，不复制历史 archive 正文，不把历史记录直接提升为 active governance。

## Source Identity

- source_id：`codex-archive`
- source_root：`/home/leiwenjun/codex/docs/archive`
- role：`codex-governance-source`
- authority：`codex-workflow-history`
- write_policy：`use-codex-archive-tools`
- check：`rtk bash /home/leiwenjun/codex/scripts/archive-check.sh`

## 使用边界

- 可用于追溯 Codex 工作流、归档记录、历史决策和治理演进。
- 不 duplicate wholesale，不把 archive 正文整批复制到 Knowledge Hub。
- 不把历史 archive 直接当作当前有效规则；提升为 active governance 前必须新增 manifest、owner review、promotion_decision、rollback 和验证证据。
- 不处理 `~/codex` 当前工作区脏变更；Codex 资产链路仍由 `~/codex` 自己的 build/doctor/check 管理。

## 验证

```bash
rtk bash /home/leiwenjun/codex/scripts/archive-check.sh
rtk bash tools/knowledge-check.sh --dry-run --json
```

## Review

- owner：`leiwenjun`
- review_after：`2026-09-19`
- 下一次复核内容：是否有具体 Codex archive 条目需要提升为独立治理资产。
