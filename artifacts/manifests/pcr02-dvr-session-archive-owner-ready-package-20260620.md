# PCR02 DVR Session Archive Owner Ready Package - 2026-06-20

## 结论

本包把 `pcr02-owner-decision-worksheet-007` 单独收口成 owner 可签收材料。它只服务 PCR02 docs `reports/2026-06-16-dvr-record-replay-session-archive.md` 这一条 owner gate：

- 不复制源 session archive 正文。
- 不修改源项目 docs。
- 不生成 owner decision。
- 不关闭 owner gate。
- 不创建 active project fact。
- 不创建 current plan、current report 或 current decision。
- 不把 session handoff、dirty worktree notes 或 memory candidates 写成项目事实。
- 不把 Memory Candidates 写入 `~/.codex/memories`。
- 不清理、revert 或 rewrite 源 archive 中提到的 worktree。
- 不在 owner review 前抽取 decision 或 validation fact。
- 不启用自动化。

当前状态仍为 `owner-fill-required`，最终门禁仍预期是 `needs-owner-review`，直到 owner 明确填写并验证通过。

## Source Identity

| 字段 | 值 |
| --- | --- |
| source_id | `pcr02-project-docs` |
| source_path | `reports/2026-06-16-dvr-record-replay-session-archive.md` |
| worksheet_id | `pcr02-owner-decision-worksheet-007` |
| owner | `project-owner` |
| observed_sha256 | `266a1c2706da87b39d9e4b204ccece61b0ec9c7a95183c64324e95f606c1dadc` |
| observed_size | `6697` |
| identity_status | `match` |

`observed_sha256` 和 `observed_size` 只是只读提示，不能自动替代 owner 在签收 JSONL 中显式填写的 `source_sha256` 和 `source_size`。

## Owner 只需回答的问题

请 owner 对以下问题给出唯一结论：

> 是否确认该材料永远只作为 archive-only，且只允许抽取 owner 已确认的 decision/validation evidence，不允许把 handoff、dirty-state、memory candidates 提升成 active fact？

允许的 `owner_decision` 只有：

| owner_decision | 含义 | 允许 target_decision |
| --- | --- | --- |
| `archive-only` | 整份 session archive 只作为历史归档线索保留；任何 validation、decision 或 risk extract 都必须另走 owner review。 | `archive-only-with-extracts-owner-gated` |

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
- `source_status_at_capture`
- `contains_memory_candidates`
- `not_active_source`
- `extracts_require_owner_review`
- `commit_branch_dirty_state_evidence`
- `proto_generation_evidence_refs`
- `build_evidence_refs`
- `refcount_evidence_refs`
- `grep_evidence_refs`
- `final_ready_evidence_refs`
- `task_iot_status`
- `replay_data_channel_status`
- `LIST_FETCH_pagination_risk_status`
- `memory_candidates_exclusion_confirmation`
- `evidence_refs`
- `status_reason`

## Archive Metadata Gate

owner 选择 `archive-only` 时，仍必须显式确认以下元数据：

| 字段 | 期望语义 |
| --- | --- |
| `source_status_at_capture` | `active handoff` 或 owner 更正后的 capture 状态。 |
| `contains_memory_candidates` | 必须明确为 `true` 或 owner 更正后的值。 |
| `not_active_source` | 必须明确为 `true`；整份 session archive 不能成为 active source。 |
| `extracts_require_owner_review` | 必须明确为 `true`；任何抽取都要再次 review。 |
| `memory_candidates_exclusion_confirmation` | 必须确认 Memory Candidates 未写入 memory，且不会进入 active facts。 |
| `commit_branch_dirty_state_evidence` | 只能作为 capture context 或 risk context，不能当作当前事实。 |

## Allowed Extracts

只有在 owner review 后，才允许从该 archive 派生以下材料：

| Extract 类型 | 允许内容 | 禁止内容 |
| --- | --- | --- |
| Validation extract | 命令结果、分支/commit refs、可复现验证证据。 | handoff 叙述、dirty worktree notes、未验证下一步建议。 |
| Decision extract | owner 已确认的 DVR 生命周期状态和接口语义。 | 未 owner review 的 session 结论。 |
| Risk extract | `task/iot`、replay data channel、`LIST_FETCH`、`RecordSetEvent` 风险。 | 把风险改写为已解决事实。 |

## Excluded Sections

以下内容必须排除在 active facts、current docs 和 memory 写入之外：

- `Memory Candidates` 整段。
- handoff / worktree cleanup notes。
- dirty / untracked worktree 说明。
- 未经 owner 确认的 `下一步建议`。
- 任何由 session archive 推断出的完成态、决策态或生产策略。

## Hard Gate

以下任一条件出现时，不能越过 owner gate：

- 整篇 session archive 被复制到 `current`。
- Memory Candidates 写入 `~/.codex/memories`。
- Memory Candidates 写入 team active index。
- handoff、dirty worktree notes 或 untracked notes 被当作 active project facts。
- 未 owner review 就抽取 decision facts。
- 未 owner review 就抽取 validation report。
- `task/iot`、replay data channel、`LIST_FETCH` 或 `RecordSetEvent` 风险被默认关闭。
- 源 archive 中提到的 worktree 被清理、revert 或 rewrite。
- session archive 被用于证明 PCR02 全部治理已经完成。

## Copyable Owner Decision Skeleton

以下 JSON 只能由 owner 填写空字段后作为单行 JSONL 使用。不要把它当作已签收结果。

```json
{"worksheet_id":"pcr02-owner-decision-worksheet-007","source_id":"pcr02-project-docs","source_path":"reports/2026-06-16-dvr-record-replay-session-archive.md","worksheet":"artifacts/manifests/pcr02-owner-decision-worksheets-20260618.jsonl","owner":"project-owner","status":"open","worksheet_status":"owner-fill-required","owner_question_zh":"是否确认该材料永远只作为 archive-only，且只允许抽取 owner 已确认的 decision/validation evidence，不允许把 handoff、dirty-state、memory candidates 提升成 active fact？","default_state":"archive-only","allowed_owner_decisions":["archive-only"],"must_not":["do not treat session handoff as active facts","do not write memory candidates to ~/.codex/memories","do not copy whole file to current","do not clean revert or rewrite source worktrees mentioned by the archive"],"owner_decision":"","target_decision":"","reviewed_by":"","reviewed_at":"","review_after":"2026-09-17","source_status":"","source_sha256":"","source_size":"","source_status_at_capture":"","contains_memory_candidates":null,"not_active_source":null,"extracts_require_owner_review":"","commit_branch_dirty_state_evidence":"","proto_generation_evidence_refs":[],"build_evidence_refs":[],"refcount_evidence_refs":[],"grep_evidence_refs":[],"final_ready_evidence_refs":[],"task_iot_status":"","replay_data_channel_status":"","LIST_FETCH_pagination_risk_status":"","memory_candidates_exclusion_confirmation":"","evidence_refs":[],"status_reason":""}
```

## 验证和落地顺序

1. Owner 填写 JSONL 后，先只读校验：

```bash
rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --validate-forms '<owner-decisions.jsonl>' --json
```

2. 校验通过后，生成只读落地计划：

```bash
rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --validate-forms '<owner-decisions.jsonl>' --landing-plan --json
```

3. 只按 landing plan 手工更新 Knowledge Hub，不修改源项目 docs，不复制整份 session archive，不写 memory，不把 handoff 或 memory candidates 变成 active facts。

4. 手工落地后至少运行：

```bash
rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
rtk bash ~/knowledge-hub/tools/knowledge-regression.sh --json
rtk bash ~/knowledge-hub/tools/knowledge-final-gate.sh --json
```

## Evidence Index

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
| --- | ---: | --- | --- | --- | --- |
| `rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --worksheet-id pcr02-owner-decision-worksheet-007 --checklist --forms` | 0 | 单条 checklist 和 form 可生成；`open_count=1`，`resolved_count=0`，`active_exposure_count=0`；source identity 为 match；owner fields 保持空白。 | `tools/knowledge-owner-gates.sh` | Owner gate | `pcr02-dvr-session-archive-owner-ready-package-20260620` |
| `rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --worksheet-id pcr02-owner-decision-worksheet-007 --forms --json` | 0 | JSON form 聚焦 worksheet-007；`owner_decision` 为空，allowed decisions 仅为 `archive-only`；`open_count=1`，`resolved_count=0`，`active_exposure_count=0`。 | `tools/knowledge-owner-gates.sh` | Owner gate | `pcr02-dvr-session-archive-owner-ready-package-20260620` |
| `rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics` | 0 | `status=pass`，`errors=[]`，`warnings=[]`。 | `tools/knowledge-check.sh` | Knowledge Hub | `pcr02-dvr-session-archive-owner-ready-package-20260620` |
| `rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --explain pcr02-dvr-session-archive-owner-ready-package-20260620` | 0 | registry item 存在，artifact path 存在，owner/review-date/status core indexes 均命中。 | `tools/knowledge-check.sh` | Knowledge Hub | `pcr02-dvr-session-archive-owner-ready-package-20260620` |
| `rtk bash ~/knowledge-hub/tools/knowledge-regression.sh --json` | 0 | 20 个回归场景通过，`kept_temp=false`。 | `tools/knowledge-regression.sh` | Regression | `pcr02-dvr-session-archive-owner-ready-package-20260620` |
| `rtk bash ~/knowledge-hub/tools/knowledge-final-gate.sh --json` | 1 | 预期返回 `needs-owner-review`；knowledge-check 与 regression 均 pass；全仓 final gate 阻塞项为 7 个 open owner gates，其中 worksheet-007 仍 open；这是 owner-review 语义门禁，不是工具失败。 | `tools/knowledge-final-gate.sh` | Final gate | `pcr02-dvr-session-archive-owner-ready-package-20260620` |

## 非目标

- 不把源 archive 迁移到 `domains/projects/pcr02/current/`。
- 不创建 DVR current fact。
- 不创建 DVR decision。
- 不创建 DVR validation report。
- 不变更 worksheet 状态。
- 不修改 `registry/items.jsonl` 中既有 DVR closeout 目标条目的状态。
- 不写 `~/.codex/memories`。
