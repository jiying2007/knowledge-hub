# Knowledge Hub structured search filters 2026-06-20

## 结论

本批推进把 `knowledge-search.sh` 从纯全文扫描增强为“全文搜索 + registry-backed 结构化过滤”入口。旧参数保持兼容，新增参数只读过滤本仓已登记条目，便于中文开发人员按 owner、状态、类型、知识域和来源 source 恢复长期资产。

当前终态仍不是完全完成：PCR02 7 个 owner decision worksheets 继续保持 open，只能由 owner 人工签收。本批未生成 owner decision，未关闭 owner gate，未修改 PCR02 源项目 docs，未提升 PCR02 project-specific 内容到 `domains/embedded/standards/`，未启用自动化，未写 memory。

## 本批变更

| Area | Change | Boundary |
|---|---|---|
| Search CLI | 新增 `--owner`、`--status`、`--kind`、`--domain`、`--source-id` | 只过滤本仓可关联到 `registry/items.jsonl` 的登记条目 |
| Compatibility | 保留 `--source` 为物理扫描源过滤 | 不改变旧命令语义 |
| JSON contract | 保留 `query/count/results`，新增 `filters` 和 item metadata | 自动化可读但不生成索引、不写文件 |
| Docs | README 和 tools README 补结构化搜索示例、5 条最短路径和最小落盘文件 | 复核过期项移到辅助路径，不再混入 5 条必经路径 |
| Regression | 新增结构化过滤和非法枚举过滤回归 | 回归场景从 43 扩展到 45 |

## 参数语义

- `--source`：物理扫描源，例如 `knowledge-hub` 或 `pcr02-project-docs`。
- `--source-id`：registry item 的 `source.source_id`，用于查询“已终态归位或已登记、来源为某 source 的本仓知识条目”。
- `--owner`、`--status`、`--kind`、`--domain`：按 `registry/items.jsonl` 字段过滤；`--domain` 使用前缀匹配。
- 结构化过滤只对本仓登记条目生效；未登记普通文件在使用结构化过滤时会被排除，避免把原始外部文件误当治理条目。

## Evidence Index

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
|---|---:|---|---|---|---|
| `rtk bash tools/knowledge-search.sh "Knowledge Hub" --owner leiwenjun --status active --json --limit 5` | 0 | 返回 active 且 owner 为 `leiwenjun` 的 registry item 命中，包含 `item_id`、`kind`、`domain`、`status`、`owner`、`source_id` | `tools/knowledge-search.sh` | Tool | `knowledge-hub-structured-search-filters-20260620` |
| `rtk bash tools/knowledge-regression.sh --json` | 0 | 通过；45 个场景全部 pass，包含 `knowledge-search-structured-filters` 和 `knowledge-search-invalid-filters` | `tools/knowledge-regression.sh` | Tool | `knowledge-hub-structured-search-filters-20260620` |
| `rtk bash tools/knowledge-check.sh --dry-run --json --diagnostics` | 0 | 通过；0 errors、0 warnings，确认新增 manifest、registry、migration 和索引登记一致 | `tools/knowledge-check.sh` | Tool | `knowledge-hub-structured-search-filters-20260620` |

## 边界

- 不修改 PCR02 源项目 docs。
- 不关闭任何 PCR02 owner gate。
- 不生成 owner decision。
- 不启用自动化，不写 `~/.codex/memories`。
- 不把 PCR02 project-specific 内容提升到 `domains/embedded/standards/`。
