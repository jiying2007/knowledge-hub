# Knowledge Hub review_after near-due snapshot 2026-06-22

## 结论

本轮新增一个只读 `review_after` 预警快照，用于人工提前复核即将到期的知识条目。

- `as_of`: `2026-06-22`
- 默认窗口：30 天
- 窗口截止日：`2026-07-22`
- 过期 item：0
- 30 天内到期 item：32
- 过期 source：0
- 30 天内到期 source：0
- 当前 owner gate open：7

该快照只提供人工维护提醒，不是 blocking gate，不自动修改 `review_after`，不关闭 owner gate，不生成 owner decision。

## 到期批次

| review_after | item 数 | 说明 |
|---|---:|---|
| `2026-07-16` | 27 | 首批 PCR02 copy-first 迁移正文和早期迁移 manifest 进入人工复核窗口。 |
| `2026-07-17` | 1 | PCR02 review-required resolution plan 进入人工复核窗口。 |
| `2026-07-18` | 4 | PCR02 reference/artifact-ref、owner-review package、follow-up 和 worksheet 进入人工复核窗口。 |

## 人工复核重点

1. 确认条目的 `owner`、`status`、`domain` 和 `path` 仍然有效。
2. 复核 `validation_refs` 是否仍可执行或仍能作为证据引用。
3. 对 `archived` 条目确认 archive-only 边界，不要误提升为 active。
4. 对 PCR02 owner-gated 相关条目，只能提示 owner 人工处理，不得由 Codex 代签或关闭 gate。
5. 若需要调整 `review_after`，必须由人工按 registry/index 正常维护流程落地，并重新运行门禁。

## 30 天窗口明细

| review_after | days | id | owner | status | path |
|---|---:|---|---|---|---|
| `2026-07-16` | 24 | `migrated-pcr02-docs-copyfirst-001` | `team-core` | `reviewing` | `domains/projects/pcr02/decisions/diag-command-architecture-final.md` |
| `2026-07-16` | 24 | `migrated-pcr02-docs-copyfirst-002` | `team-core` | `reviewing` | `domains/projects/pcr02/current/architecture/hdi-api-app-functional-overview.md` |
| `2026-07-16` | 24 | `migrated-pcr02-docs-copyfirst-003` | `team-core` | `reviewing` | `domains/projects/pcr02/current/architecture/module-catalog.md` |
| `2026-07-16` | 24 | `migrated-pcr02-docs-copyfirst-004` | `team-core` | `reviewing` | `domains/projects/pcr02/current/architecture/project-core-module-design.md` |
| `2026-07-16` | 24 | `migrated-pcr02-docs-copyfirst-005` | `team-core` | `reviewing` | `domains/projects/pcr02/decisions/project-detailed-design.md` |
| `2026-07-16` | 24 | `migrated-pcr02-docs-copyfirst-006` | `team-core` | `reviewing` | `domains/projects/pcr02/current/architecture/project-overview-design.md` |
| `2026-07-16` | 24 | `migrated-pcr02-docs-copyfirst-007` | `team-core` | `reviewing` | `domains/projects/pcr02/decisions/diag-v4-hybrid-refcount-discovery-spec.md` |
| `2026-07-16` | 24 | `migrated-pcr02-docs-copyfirst-008` | `team-core` | `reviewing` | `domains/projects/pcr02/current/third-party-libraries-reference.md` |
| `2026-07-16` | 24 | `migrated-pcr02-docs-copyfirst-009` | `team-core` | `reviewing` | `domains/projects/pcr02/current/runbooks/diag-usage-guide.md` |
| `2026-07-16` | 24 | `migrated-pcr02-docs-copyfirst-010` | `team-core` | `reviewing` | `domains/projects/pcr02/current/runbooks/irlight-sw-threshold-calibration.md` |
| `2026-07-16` | 24 | `migrated-pcr02-docs-copyfirst-011` | `team-core` | `reviewing` | `domains/projects/pcr02/current/runbooks/prog-tool-usage-guide.md` |
| `2026-07-16` | 24 | `migrated-pcr02-docs-copyfirst-012` | `team-core` | `reviewing` | `domains/projects/pcr02/current/runbooks/project-build-and-deploy-guide.md` |
| `2026-07-16` | 24 | `migrated-pcr02-docs-copyfirst-013` | `team-core` | `reviewing` | `domains/projects/pcr02/current/runbooks/project-debug-tools-guide.md` |
| `2026-07-16` | 24 | `migrated-pcr02-docs-copyfirst-014` | `team-core` | `archived` | `domains/projects/pcr02/archive/plans/2026-05-06-v1-deep-analysis-plan.md` |
| `2026-07-16` | 24 | `migrated-pcr02-docs-copyfirst-015` | `team-core` | `archived` | `domains/projects/pcr02/archive/plans/2026-05-06-v1-migration-execution-plan.md` |
| `2026-07-16` | 24 | `migrated-pcr02-docs-copyfirst-016` | `team-core` | `archived` | `domains/projects/pcr02/archive/plans/2026-05-08-irlight-optimization-plan.md` |
| `2026-07-16` | 24 | `migrated-pcr02-docs-copyfirst-017` | `team-core` | `archived` | `domains/projects/pcr02/archive/plans/2026-05-10-diag-v4-hybrid-refcount-discovery-implementation-plan.md` |
| `2026-07-16` | 24 | `migrated-pcr02-docs-copyfirst-018` | `team-core` | `archived` | `domains/projects/pcr02/archive/plans/2026-05-13-diag-ut-hard-switch-progress-plan.md` |
| `2026-07-16` | 24 | `migrated-pcr02-docs-copyfirst-019` | `team-core` | `reviewing` | `domains/projects/pcr02/validation/reports/2026-05-06-v1-deep-analysis-report.md` |
| `2026-07-16` | 24 | `migrated-pcr02-docs-copyfirst-020` | `team-core` | `reviewing` | `domains/projects/pcr02/validation/reports/2026-05-07-v1-migration-final-report.md` |
| `2026-07-16` | 24 | `migrated-pcr02-docs-copyfirst-021` | `team-core` | `reviewing` | `domains/projects/pcr02/validation/reports/2026-05-08-sigmastar-aov-lightsensor-analysis-report.md` |
| `2026-07-16` | 24 | `migrated-pcr02-docs-copyfirst-022` | `team-core` | `reviewing` | `domains/projects/pcr02/validation/reports/2026-05-14-prog-tool-terminal-release-report.md` |
| `2026-07-16` | 24 | `migrated-pcr02-docs-copyfirst-023` | `team-core` | `archived` | `domains/projects/pcr02/archive/reports/2026-05-17-session-archive-report.md` |
| `2026-07-16` | 24 | `pcr02-copy-first-applied-20260616` | `leiwenjun` | `reviewing` | `artifacts/manifests/pcr02-copy-first-applied-20260616.md` |
| `2026-07-16` | 24 | `pcr02-copy-first-dry-run-20260616` | `leiwenjun` | `reviewing` | `artifacts/manifests/pcr02-copy-first-dry-run-20260616.md` |
| `2026-07-16` | 24 | `pcr02-project-docs-classification-20260616` | `leiwenjun` | `reviewing` | `artifacts/manifests/pcr02-project-docs-classification-20260616.md` |
| `2026-07-16` | 24 | `source-inventory-20260616` | `leiwenjun` | `reviewing` | `artifacts/manifests/source-inventory-20260616.md` |
| `2026-07-17` | 25 | `pcr02-review-required-resolution-20260617` | `leiwenjun` | `reviewing` | `artifacts/manifests/pcr02-review-required-resolution-20260617.md` |
| `2026-07-18` | 26 | `pcr02-owner-decision-worksheets-20260618` | `leiwenjun` | `reviewing` | `artifacts/manifests/pcr02-owner-decision-worksheets-20260618.md` |
| `2026-07-18` | 26 | `pcr02-owner-review-follow-up-20260618` | `leiwenjun` | `reviewing` | `artifacts/manifests/pcr02-owner-review-follow-up-20260618.md` |
| `2026-07-18` | 26 | `pcr02-owner-review-package-20260618` | `leiwenjun` | `reviewing` | `artifacts/manifests/pcr02-owner-review-package-20260618.md` |
| `2026-07-18` | 26 | `pcr02-reference-artifact-ref-applied-20260618` | `leiwenjun` | `reviewing` | `artifacts/manifests/pcr02-reference-artifact-ref-applied-20260618.md` |

## Evidence Index

| 命令 | 退出码 | 结果摘要 | 证据路径 |
|---|---:|---|---|
| `rtk bash tools/knowledge-index-plan.sh --section review-date --json` | 0 | 通过；registry item 共 205 条，30 天窗口覆盖 32 条，最早到期日为 `2026-07-16`。 | `tools/knowledge-index-plan.sh` |
| `rtk bash tools/knowledge-status.sh --json --as-of 2026-06-22` | 0 | 通过；`stale_review_after_count=0`，source stale 也为 0，owner gate open 仍为 7。 | `tools/knowledge-status.sh` |
| `rtk bash tools/knowledge-check.sh --dry-run --json --diagnostics --as-of 2026-06-22` | 0 | 通过；本轮落盘后复核，`status=pass`，errors=0，warnings=0。 | `tools/knowledge-check.sh` |
| `rtk bash tools/knowledge-regression.sh --json --as-of 2026-06-22` | 0 | 通过；`status=pass`，result_count=87，未写真实仓库。 | `tools/knowledge-regression.sh` |
| `rtk bash tools/knowledge-final-gate.sh --json --as-of 2026-06-22` | 1 | 预期停在 owner-review；`final_status=needs-owner-review`，automatic governance 已完成到 owner-review 前，唯一 blocker 为 7 个 `owner-gates-open`。 | `tools/knowledge-final-gate.sh` |

## 边界

- 不自动修改 `review_after`。
- 不关闭 owner gate。
- 不生成 owner decision。
- 不把 near-due warning 当作 blocking error。
- 不修改 PCR02 源项目文件。
- 不启用自动化写操作。
- 不写 `~/.codex/memories`。
