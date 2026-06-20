# PCR02 DVR Plan Owner Ready Package - 2026-06-20

## 结论

本包把 `pcr02-owner-decision-worksheet-005` 单独收口成 owner 可签收材料。它只服务 PCR02 docs `plans/2026-06-15-dvr-record-proto-sensor-decoupling-plan.md` 这一条 owner gate：

- 不复制源 plan 正文。
- 不修改源项目 docs。
- 不生成 owner decision。
- 不关闭 owner gate。
- 不把源 plan 的 `active` 语义带入 Knowledge Hub active 状态。
- 不把计划中的命令文本当作已通过验证。
- 不创建 PCR02 current plan、decision 或 validation report。
- 不把 DVR 项目设计提升到 `domains/embedded/standards/`。
- 不导入 DVR session archive 的 handoff、worktree notes 或 memory candidates 作为 active facts。
- 不启用自动化，不写 `~/.codex/memories`。

当前状态仍为 `owner-fill-required`，最终门禁仍预期是 `needs-owner-review`，直到 owner 明确填写并验证通过。

## Source Identity

| 字段 | 值 |
| --- | --- |
| source_id | `pcr02-project-docs` |
| source_path | `plans/2026-06-15-dvr-record-proto-sensor-decoupling-plan.md` |
| worksheet_id | `pcr02-owner-decision-worksheet-005` |
| owner | `project-owner` |
| observed_sha256 | `9134247182e7578eec8c2bb4d702ffaed6c75359039d549b679f058bf8532cb3` |
| observed_size | `4786` |
| identity_status | `match` |

`observed_sha256` 和 `observed_size` 只是只读提示，不能自动替代 owner 在签收 JSONL 中显式填写的 `source_sha256` 和 `source_size`。

## Owner 只需回答的问题

请 owner 对以下问题给出唯一结论：

> 该计划最终只能选一个状态。请确认是 completed、superseded、active-if-owner-confirms-current-baseline 还是 archive-only，并提供 branch/commit/tag 与 proto/build/refcount/grep 的实际结果引用。

允许的 `owner_decision` 只有：

| owner_decision | 含义 | 允许 target_decision |
| --- | --- | --- |
| `completed` | owner 确认该计划已在指定 branch/commit/tag 基线上完成，并补齐实际验证证据。 | `archive-plan-with-completed-closeout` |
| `superseded` | owner 确认该计划已被后续计划、实现或决策替代。 | `archive-plan-with-superseded-by` |
| `active-if-owner-confirms-current-baseline` | owner 明确当前仍以该计划作为执行基线，并补齐当前 branch/commit/tag 与 open items。 | `project-current-pending-verification` |
| `archive-only` | 不保留 active 计划语义，只作为历史材料归档。 | `archive-only` |

## 必填字段

owner decision JSONL 必须填写：

- `owner_decision`
- `target_decision`
- `reviewed_by`
- `reviewed_at`
- `review_after`
- `source_status`
- `source_sha256`
- `source_size`
- `final_branch_commit_or_tag_refs`
- `proto_generation_evidence`
- `build_evidence`
- `api_dvr_refcount_evidence`
- `targeted_grep_evidence`
- `task_iot_dependency_status`
- `replay_data_channel_status`
- `LIST_FETCH_pagination_or_limit_decision`
- `RecordSetEvent_contract_extract_decision`
- `evidence_refs`
- `open_items`
- `status_reason`

## 状态决策边界

### `completed`

只有在 owner 同时补齐以下证据时，才能选择：

- 唯一最终 branch、commit 或 tag。
- `proto_generation_evidence` 是实际运行结果引用，不是计划命令。
- `build_evidence` 是实际运行结果引用，不是计划命令。
- `api_dvr_refcount_evidence` 是实际运行结果引用。
- `targeted_grep_evidence` 覆盖 DVR record/replay、proto、sensor 和旧 timing 符号。
- `task_iot_dependency_status` 明确 owner、状态和未接项。
- `replay_data_channel_status` 明确已接入、占位或后续任务。
- `LIST_FETCH_pagination_or_limit_decision` 明确 128 条限制是否接受，或是否扩展分页/limit。
- `RecordSetEvent_contract_extract_decision` 明确是否批准抽取为 PCR02 project contract。

### `superseded`

必须提供：

- 替代计划、替代实现、替代决策或 release/validation 引用。
- 被替代原因。
- 不再作为 active 计划的明确说明。

### `active-if-owner-confirms-current-baseline`

必须提供：

- owner 对当前基线仍适用的明确确认。
- 当前 branch、commit 或 tag。
- 当前未完成项和下一轮 review_after。
- 不得隐藏 `task/iot`、replay data channel、`LIST_FETCH` 和 `RecordSetEvent` 的开放项。

### `archive-only`

必须提供：

- 只归档、不进入 current 的理由。
- 是否允许未来从该计划抽取 decision / validation / risk 片段。
- 若允许抽取，必须说明抽取前仍需 owner review。

## Hard Gate

以下任一条件出现时，不能越过 owner gate：

- owner decision 不是唯一值。
- `local-codex` 被继续作为长期 owner。
- planned validation commands 被当成已通过 evidence。
- 未确认当前基线却保持 active。
- 当前 checkout 被直接写成已完成实现态。
- `task/iot` integration gap 被隐藏。
- replay data channel 状态不明。
- `LIST_FETCH` 128 条限制没有分页/limit 决策。
- `RecordSetEvent` 语义未被 owner 批准却被抽取为 project contract。
- DVR 项目设计被提升到 `domains/embedded/standards/`。
- DVR session archive 的 handoff、worktree notes 或 memory candidates 被导入 active facts。

## Copyable Owner Decision Skeleton

以下 JSON 只能由 owner 填写空字段后作为单行 JSONL 使用。不要把它当作已签收结果。

```json
{"worksheet_id":"pcr02-owner-decision-worksheet-005","source_id":"pcr02-project-docs","source_path":"plans/2026-06-15-dvr-record-proto-sensor-decoupling-plan.md","worksheet":"artifacts/manifests/pcr02-owner-decision-worksheets-20260618.jsonl","owner":"project-owner","status":"open","worksheet_status":"owner-fill-required","owner_question_zh":"该计划最终只能选一个状态。请确认是 completed、superseded、active-if-owner-confirms-current-baseline 还是 archive-only，并提供 branch/commit/tag 与 proto/build/refcount/grep 的实际结果引用。","default_state":"completed-after-owner-gate preferred, otherwise blocked-pending-owner-status-decision","allowed_owner_decisions":["completed","superseded","active-if-owner-confirms-current-baseline","archive-only"],"must_not":["do not use local-codex as long-term owner","do not treat planned validation commands as passed evidence","do not promote DVR project design to domains/embedded/standards","do not import session archive handoff notes as active facts"],"owner_decision":"","target_decision":"","reviewed_by":"","reviewed_at":"","review_after":"2026-09-17","source_status":"","source_sha256":"","source_size":"","final_branch_commit_or_tag_refs":[],"proto_generation_evidence":"","build_evidence":"","api_dvr_refcount_evidence":"","targeted_grep_evidence":"","task_iot_dependency_status":"","replay_data_channel_status":"","LIST_FETCH_pagination_or_limit_decision":"","RecordSetEvent_contract_extract_decision":"","evidence_refs":[],"open_items":[],"status_reason":""}
```

## 验证和落地顺序

1. Owner 填写 JSONL 后，先只读校验：

```bash
rtk bash tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --validate-forms '<owner-decisions.jsonl>' --json
```

2. 校验通过后，生成只读落地计划：

```bash
rtk bash tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --validate-forms '<owner-decisions.jsonl>' --landing-plan --json
```

3. 只按 landing plan 手工更新 Knowledge Hub，不修改源项目 docs，不把 planned commands 当证据，不提升到团队标准。

4. 手工落地后至少运行：

```bash
rtk bash tools/knowledge-check.sh --dry-run --json --diagnostics
rtk bash tools/knowledge-regression.sh --json
rtk bash tools/knowledge-final-gate.sh --json
```

## Evidence Index

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
| --- | ---: | --- | --- | --- | --- |
| `rtk bash tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --worksheet-id pcr02-owner-decision-worksheet-005 --checklist --forms` | 0 | 单条 checklist 和 form 可生成；source identity 为 match；owner fields 保持空白。 | `tools/knowledge-owner-gates.sh` | Owner gate | `pcr02-dvr-plan-owner-ready-package-20260620` |
| `rtk bash tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --worksheet-id pcr02-owner-decision-worksheet-005 --forms --json` | 0 | JSON form 聚焦 worksheet-005；`owner_decision` 为空，allowed decisions 与 worksheet 一致。 | `tools/knowledge-owner-gates.sh` | Owner gate | `pcr02-dvr-plan-owner-ready-package-20260620` |
| `rtk bash tools/knowledge-check.sh --dry-run --json --diagnostics` | 0 | 全仓一致性通过，0 errors、0 warnings。 | `tools/knowledge-check.sh` | Knowledge Hub | `pcr02-dvr-plan-owner-ready-package-20260620` |
| `rtk bash tools/knowledge-check.sh --dry-run --json --explain pcr02-dvr-plan-owner-ready-package-20260620` | 0 | registry 条目存在，核心索引引用均为 ok。 | `tools/knowledge-check.sh` | Knowledge Hub | `pcr02-dvr-plan-owner-ready-package-20260620` |
| `rtk bash tools/knowledge-regression.sh --json` | 0 | 20 个 governance regression 场景通过，`kept_temp=false`。 | `tools/knowledge-regression.sh` | Regression | `pcr02-dvr-plan-owner-ready-package-20260620` |
| `rtk bash tools/knowledge-final-gate.sh --json` | 1 expected | 预期仍为 `needs-owner-review`；`knowledge_check` 和 `knowledge_regression` 通过，唯一 blocker 是 7 个 owner gates open。 | `tools/knowledge-final-gate.sh` | Final gate | `pcr02-dvr-plan-owner-ready-package-20260620` |

## 非目标

- 不把源 plan 迁移到 `domains/projects/pcr02/current/plans/`。
- 不创建 DVR contract decision。
- 不创建 DVR validation report。
- 不变更 worksheet 状态。
- 不修改 `registry/items.jsonl` 中既有 DVR/motor closeout 目标条目的状态。
