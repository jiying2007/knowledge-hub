# PCR02 Owner Decision Intake Execution - 2026-06-20

## 结论

本包把 PCR02 剩余 7 个 owner gate 的人工签收入口固定成一个可转交、可引用、可索引的执行包。它不生成 owner decision，不关闭 gate，不迁移 source 正文，不修改源项目 docs，不启用自动化，不写 `~/.codex/memories`。

当前终态仍是 `needs-owner-review`：

- row_count: 7
- open_count: 7
- resolved_count: 0
- active_exposure_count: 0
- source_identity: 7/7 match
- owner_ready_package_coverage: 7/7

## 使用顺序

1. 先看全量 owner gate 总览：

```bash
rtk bash tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --summary
```

2. 按 `review_after, worksheet_id` 顺序处理下一条：

```bash
rtk bash tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --next-open --checklist --forms
```

3. Owner 填写 JSONL 后，先只读验证，不直接落地：

```bash
rtk bash tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --validate-forms '<owner-decisions.jsonl>' --json
rtk bash tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --validate-forms '<owner-decisions.jsonl>' --landing-plan --json
```

4. 只有验证通过后，才按 landing plan 手工更新正文、registry、migration 和索引；仍不得修改源项目 docs。

## 不变量

- PCR02 project-specific 内容不得提升到 `domains/embedded/standards/`。
- `.session`、handoff、memory candidates 只能作为 archive/artifact/candidate，不能进入 active facts。
- `source_sha256` 和 `source_size` 必须由 owner 显式填写，脚本显示的 observed source identity 不能自动替代签收。
- `reviewing` 是 registry canonical status；owner overlay 状态只能写入 `review_status` 或 manifest 字段。
- 本包不新增 worksheet row，因此 `owner_gates.open_count` 应继续为 7，直到 owner decision 正式落地。

## Owner 分派

| owner | rows | source paths |
| --- | ---: | --- |
| `project-owner` | 2 | `plans/2026-06-15-dvr-record-proto-sensor-decoupling-plan.md`; `reports/2026-06-16-dvr-record-replay-session-archive.md` |
| `team-core-or-pcr02-docs-owner` | 1 | `AGENTS.md` |
| `pcr02-diag-owner-or-team-core` | 1 | `standards/diag-command-metadata-standard.md` |
| `team-core` | 1 | `runbooks/asan-debug-guide.md` |
| `personal-owner-and-team-review-if-teamized` | 1 | `runbooks/memory-auto-curation-guide.md` |
| `motor-mcu-or-soc-owner` | 1 | `reports/2026-05-29-motor-mcu-debug-record.md` |

## Owner-ready Package 覆盖

7 条 owner gate 均已有单项 owner-ready 签收包。下表是人工分派时的唯一入口索引；这些包都只是签收材料，不代表 owner decision 已落地。

| worksheet | owner-ready package | review_status | focus command |
| --- | --- | --- | --- |
| `pcr02-owner-decision-worksheet-001` | `artifacts/manifests/pcr02-agents-owner-ready-package-20260620.md` | `owner-ready-no-decision` | `rtk bash tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --worksheet-id pcr02-owner-decision-worksheet-001 --checklist --forms` |
| `pcr02-owner-decision-worksheet-002` | `artifacts/manifests/pcr02-diag-owner-ready-package-20260620.md` | `owner-ready-no-decision` | `rtk bash tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --worksheet-id pcr02-owner-decision-worksheet-002 --checklist --forms` |
| `pcr02-owner-decision-worksheet-003` | `artifacts/manifests/pcr02-asan-owner-ready-package-20260620.md` | `owner-ready-no-decision` | `rtk bash tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --worksheet-id pcr02-owner-decision-worksheet-003 --checklist --forms` |
| `pcr02-owner-decision-worksheet-004` | `artifacts/manifests/pcr02-memory-auto-curation-owner-ready-package-20260620.md` | `owner-ready-no-decision` | `rtk bash tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --worksheet-id pcr02-owner-decision-worksheet-004 --checklist --forms` |
| `pcr02-owner-decision-worksheet-005` | `artifacts/manifests/pcr02-dvr-plan-owner-ready-package-20260620.md` | `owner-ready-no-decision` | `rtk bash tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --worksheet-id pcr02-owner-decision-worksheet-005 --checklist --forms` |
| `pcr02-owner-decision-worksheet-006` | `artifacts/manifests/pcr02-motor-mcu-owner-ready-package-20260620.md` | `owner-ready-no-decision` | `rtk bash tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --worksheet-id pcr02-owner-decision-worksheet-006 --checklist --forms` |
| `pcr02-owner-decision-worksheet-007` | `artifacts/manifests/pcr02-dvr-session-archive-owner-ready-package-20260620.md` | `owner-ready-no-decision` | `rtk bash tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --worksheet-id pcr02-owner-decision-worksheet-007 --checklist --forms` |

## 执行队列

| worksheet | source path | owner | owner-ready package | default state | allowed owner decisions | required fields | identity | hard gate summary |
| --- | --- | --- | --- | --- | --- | ---: | --- | --- |
| `pcr02-owner-decision-worksheet-001` | `AGENTS.md` | `team-core-or-pcr02-docs-owner` | `pcr02-agents-owner-ready-package-20260620` | `reference-only-pending-owner-gate` | `project-local-rule`, `reference-only`, `no-migration` | 13 | match | 门禁待补证 |
| `pcr02-owner-decision-worksheet-002` | `standards/diag-command-metadata-standard.md` | `pcr02-diag-owner-or-team-core` | `pcr02-diag-owner-ready-package-20260620` | `reference-only-pending-owner-gate` | `pcr02-project-decision-after-owner-gate`, `pcr02-project-current-after-owner-gate`, `reference-only`, `no-migration` | 14 | match | 门禁待补证 |
| `pcr02-owner-decision-worksheet-003` | `runbooks/asan-debug-guide.md` | `team-core` | `pcr02-asan-owner-ready-package-20260620` | `split-required / blocked-pending-owner-review` | `split-approved`, `active-project-local`, `reference-only`, `rejected`, `team-candidate-only` | 15 | match | 门禁待补证 |
| `pcr02-owner-decision-worksheet-004` | `runbooks/memory-auto-curation-guide.md` | `personal-owner-and-team-review-if-teamized` | `pcr02-memory-auto-curation-owner-ready-package-20260620` | `blocked-personal-local` | `personal-local`, `teamized-report-only`, `rejected`, `no-migration` | 18 | match | 门禁待补证 |
| `pcr02-owner-decision-worksheet-005` | `plans/2026-06-15-dvr-record-proto-sensor-decoupling-plan.md` | `project-owner` | `pcr02-dvr-plan-owner-ready-package-20260620` | `completed-after-owner-gate preferred, otherwise blocked-pending-owner-status-decision` | `completed`, `superseded`, `active-if-owner-confirms-current-baseline`, `archive-only` | 20 | match | 门禁待补证 |
| `pcr02-owner-decision-worksheet-006` | `reports/2026-05-29-motor-mcu-debug-record.md` | `motor-mcu-or-soc-owner` | `pcr02-motor-mcu-owner-ready-package-20260620` | `archive-only` | `archive-only`, `validation-report-candidate` | 19 | match | 门禁待补证 |
| `pcr02-owner-decision-worksheet-007` | `reports/2026-06-16-dvr-record-replay-session-archive.md` | `project-owner` | `pcr02-dvr-session-archive-owner-ready-package-20260620` | `archive-only` | `archive-only` | 24 | match | 门禁待补证 |

## 每条必须带回的字段

每条 owner decision 至少必须填写：

- `worksheet_id`
- `owner_decision`
- `target_decision`
- `reviewed_by`
- `reviewed_at`
- `review_after`
- `source_status`
- `source_sha256`
- `source_size`
- 每条 worksheet 的额外必填字段
- `evidence_refs`
- `status_reason`

额外字段以 `tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --worksheet-id <id> --checklist --forms` 输出为准。

## Evidence Index

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
| --- | ---: | --- | --- | --- | --- |
| `rtk bash tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --summary` | 0 | 7 open、0 resolved、0 active exposure；owner distribution 可读。 | `tools/knowledge-owner-gates.sh` | Owner gate | `pcr02-owner-decision-intake-execution-20260620` |
| `rtk bash tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --forms --checklist --json` | 0 | 7 条 checklist 和 decision form skeleton 均可生成，source identity 均为 match。 | `tools/knowledge-owner-gates.sh` | Owner gate | `pcr02-owner-decision-intake-execution-20260620` |
| `rtk bash tools/knowledge-status.sh --strict --json` | 1 expected | 预期仍为 `needs-owner-review`，唯一 blocker 为 `owner-gates-open count=7`。 | `tools/knowledge-status.sh` | Strict status | `pcr02-owner-decision-intake-execution-20260620` |
| `rtk bash tools/knowledge-check.sh --dry-run --json --diagnostics` | 0 | 全仓一致性门禁应通过。 | `tools/knowledge-check.sh` | Knowledge Hub | `pcr02-owner-decision-intake-execution-20260620` |
| `rtk bash tools/knowledge-check.sh --dry-run --json --explain pcr02-owner-decision-intake-execution-20260620` | 0 | registry item 存在，artifact path 存在，owner/review-date/status core indexes 均命中；validation_refs_count=7。 | `tools/knowledge-check.sh` | Knowledge Hub | `pcr02-owner-decision-intake-execution-20260620` |
| `rtk bash tools/knowledge-regression.sh --json` | 0 | 20 个回归场景通过，`kept_temp=false`。 | `tools/knowledge-regression.sh` | Regression | `pcr02-owner-decision-intake-execution-20260620` |
| `rtk bash tools/knowledge-final-gate.sh --json` | 1 | 预期返回 `needs-owner-review`；knowledge-check 与 regression 均 pass；唯一 blocker 为 7 个 open owner gates；owner-ready 包覆盖不等于 owner gate 已签收。 | `tools/knowledge-final-gate.sh` | Final gate | `pcr02-owner-decision-intake-execution-20260620` |

## 非目标

- 不新增 owner decision worksheet row。
- 不写 owner decision 结果。
- 不关闭 `owner-gates-open` blocker。
- 不复制 7 个 source 正文。
- 不修改源项目 docs。
- 不提升 PCR02 内容到团队标准。
- 不写 memory，不启用自动化。

## 后续落地条件

Owner decision JSONL 通过 `--validate-forms` 后，下一步只能按 `--landing-plan` 的文件清单手工落地，并在最终重新运行：

```bash
rtk bash tools/knowledge-check.sh --dry-run --json --diagnostics
rtk bash tools/knowledge-regression.sh --json
rtk bash tools/knowledge-final-gate.sh --json
```
