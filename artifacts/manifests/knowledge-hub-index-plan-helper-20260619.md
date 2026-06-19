# Knowledge Hub Index Plan Helper 2026-06-19

## 目标

降低人工维护核心索引的成本，同时不引入自动写入或复杂生成链路。新增 `tools/knowledge-index-plan.sh`，从 `registry/items.jsonl` 只读打印 `by-owner`、`by-review-date` 和 `by-status` 的应有视图，供维护者对照和复制。

## 问题地图

| ID | 问题 | 风险 | 处理 |
| --- | --- | --- | --- |
| IPH-001 | `indexes/by-status.md` 仍带有 bootstrap/未来生成化提示。 | 维护者可能误判当前索引仍是临时状态。 | 改为说明核心状态 bucket 手工维护且由 `knowledge-check` 门禁兜底，可用 index plan 辅助核对。 |
| IPH-002 | 人工新增 item 需要同步三个核心索引。 | 大行编辑和多文件同步容易漏项、重复或状态错位。 | 新增只读 `knowledge-index-plan.sh` 打印 registry 派生视图。 |
| IPH-003 | 自动生成并覆盖索引会提高风险。 | 工具可能覆盖人工分组、说明行或当前 range 写法。 | 本轮只读输出计划，不写文件、不排序覆盖、不自动修复。 |

## 决策

- `knowledge-index-plan.sh` 只读取 `registry/items.jsonl`，不读取外部 source，不写文件。
- 默认输出 Markdown，`--json` 输出可机读摘要。
- 支持 `--section owner|review-date|status|all`，便于只查看当前维护点。
- `knowledge-check` 仍是提交前权威门禁；index plan 只是人工辅助视图。

## 非目标

- 不自动重写 `indexes/*.md`。
- 不改变 `knowledge-check` 门禁语义。
- 不删除现有 range 写法或说明行。
- 不启用自动化。

## Evidence Index

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
| --- | --- | --- | --- | --- | --- |
| `rtk bash tools/knowledge-index-plan.sh --json` | 0 | 从 registry 生成只读核心索引计划，状态为 `planned`。 | `tools/knowledge-index-plan.sh` | Knowledge Hub | index-plan-helper |
| `rtk bash tools/knowledge-index-plan.sh --section status` | 0 | 输出 active、reviewing、archived 三个状态 bucket 的 registry 派生视图。 | `tools/knowledge-index-plan.sh` | Knowledge Hub | indexes/by-status.md |
| `rtk bash tools/knowledge-check.sh --dry-run --json --diagnostics` | 0 | 全仓门禁通过，0 errors，0 warnings。 | `tools/knowledge-check.sh` | Knowledge Hub | index-plan-helper |

## Review

- owner：`leiwenjun`
- review_after：`2026-09-19`
- 下一次复核内容：是否需要把 by-owner/by-review-date 的人工维护提示也改为引用 `knowledge-index-plan.sh`。
