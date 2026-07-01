# Knowledge Hub review_after 运营计划 2026-07-01

## 结论

本计划用于把 2026-07-01 的 review_after 近期待复核队列转成可执行运营批次。它是 report-only 运营计划，不自动修改 `review_after`，不关闭 owner gate，不生成 owner decision，不提升 active，不写 memory，不修改源项目。

## 基线

| 字段 | 值 |
|---|---:|
| as_of | 2026-07-01 |
| window_days | 30 |
| stale_items | 0 |
| near_due_items | 27 |
| owner_gate_open_count | 0 |
| source_near_due | 0 |

## 批次

| 批次 | owner | 数量 | review_after | 动作 |
|---|---|---:|---|---|
| P1-current-reviewing | team-core | 13 | 2026-07-16 | 复核 current / decision / runbook 是否仍准确，owner 复核后再延后日期或改状态 |
| P2-archive-boundary | team-core | 10 | 2026-07-16 | 确认 archive-only 边界、validation_refs 和不得提升 active 的说明 |
| P3-owner-artifacts | leiwenjun | 4 | 2026-07-17..2026-07-18 | 确认历史 owner-review artifact 仍是人工提示或审计材料 |

## P1-current-reviewing

- `pcr02-build-and-deploy-guide`
- `pcr02-core-module-design`
- `pcr02-debug-tools-guide`
- `pcr02-diag-command-architecture-final`
- `pcr02-diag-usage-guide`
- `pcr02-diag-v4-hybrid-refcount-discovery-spec`
- `pcr02-hdi-api-app-functional-overview`
- `pcr02-irlight-sw-threshold-calibration`
- `pcr02-module-catalog`
- `pcr02-prog-tool-usage-guide`
- `pcr02-project-detailed-design`
- `pcr02-project-overview-design`
- `pcr02-third-party-libraries-reference`

## P2-archive-boundary

- `pcr02-aov-lightsensor-analysis-validation-report-20260508`
- `pcr02-diag-ut-hard-switch-progress-archive-20260513`
- `pcr02-diag-v4-hybrid-refcount-discovery-plan-archive-20260510`
- `pcr02-irlight-optimization-plan-archive-20260508`
- `pcr02-prog-tool-terminal-release-validation-report-20260514`
- `pcr02-session-archive-report-20260517`
- `pcr02-v1-deep-analysis-plan-archive-20260506`
- `pcr02-v1-deep-analysis-validation-report-20260506`
- `pcr02-v1-migration-execution-plan-archive-20260506`
- `pcr02-v1-migration-final-validation-report-20260507`

## P3-owner-artifacts

- `pcr02-review-required-resolution-20260617`
- `pcr02-owner-decision-worksheets-20260618`
- `pcr02-owner-review-follow-up-20260618`
- `pcr02-owner-review-package-20260618`

## 执行规则

1. 先人工或 owner 复核，再更新 `review_after`、`review_status`、`review_basis` 或状态。
2. archive-only 条目只能确认归档边界、证据引用和不得提升 active 的说明；不得把历史计划写成已完成事实。
3. 缺失 `source_id` 的历史 artifact 只做人工提示，不自动推断来源，不反推出 owner approval。
4. 每批处理后运行：

```bash
rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics --as-of 2026-07-01
rtk bash ~/knowledge-hub/tools/knowledge-status.sh --strict --json --as-of 2026-07-01 --final-profile mature
```

## 禁止动作

- 不自动修改 `review_after`。
- 不关闭 owner gate。
- 不生成或代签 owner decision。
- 不提升 active。
- 不写 `~/.codex/memories`。
- 不修改源项目或远端仓库。

## 证据索引

- `governance/status/knowledge-hub-operational-maturity.md`
- `artifacts/manifests/knowledge-hub-review-after-operation-plan-20260701.jsonl`
- `rtk bash ~/knowledge-hub/tools/knowledge-review-after.sh --as-of 2026-07-01 --window-days 30 --json`
- `rtk bash ~/knowledge-hub/tools/knowledge-status.sh --strict --json --as-of 2026-07-01 --final-profile mature`
