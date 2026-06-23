# PCR02 项目 docs owner decision landing（2026-06-23）

## 结论

本制品记录 PCR02 项目 docs 剩余 7 条 owner gate 的人工授权决策落地结果。7 条 worksheet 均已补齐必填 owner 字段，`knowledge-owner-gates.sh` 当前显示 `open_count=0`、`resolved_count=7`。

本次只关闭 owner decision gate，不复制源项目正文，不修改源项目 docs，不提升 PCR02 project-specific 内容到 `domains/embedded/standards/`，不启用自动化，不写 `~/.codex/memories`。

## 决策清单

| Worksheet | Source Path | Owner Decision | Target Decision | 边界 |
| --- | --- | --- | --- | --- |
| `pcr02-owner-decision-worksheet-001` | `AGENTS.md` | `reference-only` | `reference-only` | 仅作为 PCR02 项目本地规则参考，不覆盖 Knowledge Hub 根规则。 |
| `pcr02-owner-decision-worksheet-002` | `standards/diag-command-metadata-standard.md` | `reference-only` | `reference-only` | 缺运行态 gate evidence，不提升为团队级标准或 project current。 |
| `pcr02-owner-decision-worksheet-003` | `runbooks/asan-debug-guide.md` | `split-approved` | `domains/projects/pcr02/current/runbooks/asan-debug-guide.md` | PCR02-specific 内容留项目内；团队层 ASAN 仅 candidate-only，另审。 |
| `pcr02-owner-decision-worksheet-004` | `runbooks/memory-auto-curation-guide.md` | `teamized-report-only` | `report-only-governance-candidate` | `enabled=false`、`writes_memory=false`、`writes_team_active_index=false`。 |
| `pcr02-owner-decision-worksheet-005` | `plans/2026-06-15-dvr-record-proto-sensor-decoupling-plan.md` | `archive-only` | `domains/projects/pcr02/archive/plans/2026-06-15-dvr-record-proto-sensor-decoupling-plan.md` | 缺完成证据，不声明 completed。 |
| `pcr02-owner-decision-worksheet-006` | `reports/2026-05-29-motor-mcu-debug-record.md` | `archive-only` | `domains/projects/pcr02/archive/reports/2026-05-29-motor-mcu-debug-record.md` | 事实、反馈、推断、建议和 open items 未拆分前不进入 validation/current。 |
| `pcr02-owner-decision-worksheet-007` | `reports/2026-06-16-dvr-record-replay-session-archive.md` | `archive-only` | `domains/projects/pcr02/archive/reports/2026-06-16-dvr-record-replay-session-archive.md` | session handoff、dirty-state、memory candidates 不进入 active facts。 |

## 证据

- 机器可校验决策：`artifacts/manifests/pcr02-project-docs-owner-decision-landing-20260623.jsonl`
- 已更新 worksheet：`artifacts/manifests/pcr02-owner-decision-worksheets-20260618.jsonl`
- 原 owner-review 包：`artifacts/manifests/pcr02-owner-review-package-20260618.md`
- owner-ready 包：`artifacts/manifests/pcr02-*-owner-ready-package-20260620.md`

## 复审日期口径

- worksheet 级 `review_after=2026-09-17` 来自 7 条原始 owner gate 行，用于复核对应 source 的 owner decision 是否仍适用。
- registry item 级 `review_after=2026-09-23` 属于本 landing 制品自身的维护窗口，用于复核本次落地记录、索引和证据链是否仍可恢复。
- 消费方不得用 landing 制品的复审日期覆盖 worksheet 级复审日期；需要按 source/worksheet 处理语义有效性时，应优先读取 `pcr02-owner-decision-worksheets-20260618.jsonl`。

## 验证命令

```bash
rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --status all --json
rtk bash ~/knowledge-hub/tools/knowledge-status.sh --strict --json
rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics --as-of 2026-06-23
```

## 后续边界

- ASAN 项目内 runbook 若要正式生成正文，应另行按 split-approved 边界落地，不能整篇复制到团队层。
- memory auto-curation 只能保持 disabled/report-only，任何启用、写 memory 或写 team active index 都需要新的人工审批。
- DVR plan、motor MCU debug record 和 DVR session archive 后续若要抽 validation/decision/current 内容，必须另行 owner review，并保留证据引用。
