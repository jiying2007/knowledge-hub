# Knowledge Hub Source Coverage Gate 2026-06-19

## 目标

把 registered source 的终态覆盖矩阵纳入 `knowledge-check` 默认门禁，避免只更新 `registry/sources.json` 和 `indexes/by-source.md`，却忘记说明新 source 的迁移、引用、owner-gated 或 auxiliary-only 终态边界。

## 问题地图

| ID | 问题 | 风险 | 处理 |
| --- | --- | --- | --- |
| SCG-001 | `indexes/by-source.md` 已有 source id 覆盖门禁，但不检查每个 source 是否有终态分类。 | 新增 source 后可能只有导航入口，没有迁移/引用/不迁移决策。 | `knowledge-check` 读取最新 `knowledge-hub-source-coverage-closeout-*.jsonl`，要求覆盖所有 registered source。 |
| SCG-002 | source coverage 行如果缺少 decision 或 risk，就无法支撑终态审计。 | 后续维护者不知道该复制、引用、等待 owner，还是保持 auxiliary-only。 | 每行要求 `source_id`、`status`、`classification`、`decision`、`risk`、`owner`、`checked_at`。 |
| SCG-003 | 自动修复 coverage 会扩大复杂度。 | 工具可能生成错误分类或覆盖人工判断。 | 本轮只做只读检查，不生成、不修复、不迁移 source。 |

## 决策

- 默认只从 `artifacts/manifests/knowledge-hub-source-coverage-closeout-YYYYMMDD.jsonl` 日期候选中选择最新 closeout；非日期候选会被忽略并在 selection metadata 中暴露。
- coverage source 集合必须与 `registry/sources.json` source id 集合一致。
- coverage 行必须包含可读的终态分类、决策和风险字段。
- `checked_at` 必须是 ISO 日期。

## 非目标

- 不检查外部 source 目录内容是否变化。
- 不自动重新生成 source coverage manifest。
- 不把 owner-gated source 自动迁移。
- 不启用自动化。

## Evidence Index

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
| --- | --- | --- | --- | --- | --- |
| `rtk bash tools/knowledge-check.sh --dry-run --json --diagnostics` | 0 | source coverage gate 默认启用，全仓通过，0 errors，0 warnings。 | `tools/knowledge-check.sh` | Knowledge Hub | source-coverage-gate |
| `/tmp source coverage missing-source fixture` | 1 | 临时副本删除 coverage 中一个 source 后，`knowledge-check` 报 `source-coverage:* missing source`。 | `/tmp` | Negative fixture | source-coverage-gate |
| `rtk bash tools/knowledge-search.sh source-coverage-gate-applied --json` | 0 | 可检索到本门禁登记项。 | `registry/items.jsonl`、`indexes/by-status.md` | Knowledge Hub | source-coverage-gate |

## Review

- owner：`leiwenjun`
- review_after：`2026-09-19`
- 下一次复核内容：如新增 source，应先补 source coverage closeout 行，再通过本门禁。
