# Knowledge Hub owner dispatch filter 2026-06-20

## 结论

`tools/knowledge-owner-gates.sh` 新增只读 `--owner <owner>` 精确筛选，用于把 open owner gate 按责任人分派、排期和复核。`tools/knowledge-status.sh` 同步输出 `owner_gates.owner_summary_commands`，在 final gate blocker 中也暴露按 owner 的可执行 summary 命令。

该能力只降低人工签收瓶颈，不生成 owner decision，不关闭 owner gate。

## 终态差距地图

| gap_id | gap_type | source_id | evidence | 当前影响 | 自动完成 | owner decision | 本轮动作 | 状态 |
|---|---|---|---|---|---|---|---|---|
| ODF-001 | manual-maintenance | pcr02-project-docs | 7 条 open gate 分属 6 个 owner，其中 `project-owner` 有 2 条 | 人工分派必须从全量 summary 中手工筛选 | yes | no | `knowledge-owner-gates.sh --owner <owner> --summary` | applied |
| ODF-002 | tooling | pcr02-project-docs | `knowledge-status.sh --json` 原本只有全量 summary 和 next-open | status 看板不能直接给出 owner 分派命令 | yes | no | 新增 `owner_gates.owner_summary_commands` 和 next action | applied |
| ODF-003 | regression | pcr02-project-docs | owner 分派入口若无回归会漂移 | 后续工具改动可能丢失 owner 过滤 | yes | no | 新增 `owner-summary-by-owner`，扩展 `status-next-owner-gate` | applied |

## 行为边界

- `--owner` 是精确字符串过滤，不是权限控制。
- `--owner` 可与 `--source-id`、`--summary`、`--forms`、`--forms-jsonl`、`--checklist`、`--worksheet-id`、`--next-open` 组合使用。
- `--owner` 不填 owner 决策字段，不自动填 `reviewed_by`、`reviewed_at`、`source_sha256` 或 `source_size`。
- final gate 仍然会在 7 条 owner gate 未签收时返回 `needs-owner-review`。

## Evidence Index

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
|---|---:|---|---|---|---|
| `rtk bash tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --owner project-owner --summary --json` | 0 | 只读输出 project-owner 名下 2 条 open gate，owner-ready coverage 为 2/2 | `tools/knowledge-owner-gates.sh` | Tool | `knowledge-hub-owner-dispatch-filter-20260620` |
| `rtk bash tools/knowledge-status.sh --json` | 0 | `owner_gates.owner_summary_commands` 输出 6 条按 owner 分派命令 | `tools/knowledge-status.sh` | Tool | `knowledge-hub-owner-dispatch-filter-20260620` |
| `rtk bash tools/knowledge-regression.sh --json` | 0 | 29 个回归场景通过，包含 `owner-summary-by-owner` 和 status owner summary commands 检查 | `tools/knowledge-regression.sh` | Regression | `knowledge-hub-owner-dispatch-filter-20260620` |
| `rtk bash tools/knowledge-final-gate.sh --json` | expected 1 | 仍返回 `needs-owner-review`，严格 blocker 中包含 owner 分派 summary commands | `tools/knowledge-final-gate.sh` | Final Gate | `knowledge-hub-owner-dispatch-filter-20260620` |

## 维护

- owner：`leiwenjun`
- review_after：`2026-09-20`
- review_status：`owner-dispatch-filter-applied`
- 下一次复核内容：若 owner 字段命名、status dashboard command contract 或 owner gate 分派策略变化，需同步 README、tools README、回归和本 manifest。
