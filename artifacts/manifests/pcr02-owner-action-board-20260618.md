# PCR02 Owner Action Board - 2026-06-18

## 摘要

本 action board 把 PCR02 docs governance closeout 后剩余的 7 个 owner-gated 条目整理为可执行的 owner 决策清单。它不是 owner 决策结果，不关闭 blocker，不创建 active/current 知识正文。

适用原则：

- 先补 owner decision 和 evidence，再考虑迁移、抽取或提升。
- 所有 owner-gated 条目继续保持 `reviewing` / blocked。
- 不写 `~/.codex/memories`。
- 不修改源项目 docs。
- 不把 PCR02 project-specific 内容提升到 `domains/embedded/standards/`。

## Action Board

| Source path | Owner candidate | Default state | Decision options | Next evidence source |
| --- | --- | --- | --- | --- |
| `AGENTS.md` | `team-core-or-pcr02-docs-owner` | `reference-only-pending-owner-gate` | `project-local-rule`, `reference-only`, `no-migration` | `pcr02-owner-decision-worksheet-001` |
| `standards/diag-command-metadata-standard.md` | `pcr02-diag-owner-or-team-core` | `reference-only-pending-owner-gate` | `pcr02-project-decision-after-owner-gate`, `pcr02-project-current-after-owner-gate`, `reference-only`, `no-migration` | `pcr02-owner-decision-worksheet-002` + diag gate output |
| `runbooks/asan-debug-guide.md` | `team-core` | `split-required / blocked-pending-owner-review` | `split-approved`, `active-project-local`, `reference-only`, `rejected`, `team-candidate-only` | `pcr02-owner-decision-worksheet-003` |
| `runbooks/memory-auto-curation-guide.md` | `personal-owner-and-team-review-if-teamized` | `blocked-personal-local` | `personal-local`, `teamized-report-only`, `rejected`, `no-migration` | `pcr02-owner-decision-worksheet-004` + no-memory-write runtime evidence |
| `plans/2026-06-15-dvr-record-proto-sensor-decoupling-plan.md` | `project-owner` | `completed-after-owner-gate` preferred, otherwise blocked | `completed`, `superseded`, `active-if-owner-confirms-current-baseline`, `archive-only` | branch/commit/tag + proto/build/refcount/grep output |
| `reports/2026-05-29-motor-mcu-debug-record.md` | `motor-mcu-or-soc-owner` | `archive-only` | `archive-only`, `validation-report-candidate` | firmware/parameter/log/retest/calibration/whole-device validation records |
| `reports/2026-06-16-dvr-record-replay-session-archive.md` | `project-owner` | `archive-only` | `archive-only` | archive metadata approval + extract approvals |

## Required Evidence

### `AGENTS.md`

- owner sign-off
- current validity
- project-only scope
- applicable branch / SDK / project phase
- `reviewed_by` / `reviewed_at` / `review_after`
- source sha256 / size
- target decision reason
- `~/embedded/knowledge` path decision

Pass gate：owner/status/scope/review cycle/applicable version 明确，target 只在 PCR02 project boundary，不覆盖 Knowledge Hub 根 `AGENTS.md`。

Fail gate：当前有效性未确认，被解释成全局 Codex rule 或 team standard，target 写 root `AGENTS.md` 或 `domains/embedded/standards`。

### `standards/diag-command-metadata-standard.md`

- diag owner sign-off
- project-only source-of-truth
- applicable branch / firmware / SDK version
- provider lifecycle match evidence
- command metadata / catalog / help runtime match evidence
- 5 个 diag gate 实际结果或 documented owner exception

Pass gate：owner sign-off 存在，project-only 和版本明确，实现仍匹配文档，target 只在 PCR02 decisions/current。

Fail gate：gate evidence 缺失且无 owner exception，provider/metadata 未验证，PCR02 命令名/路径/生命周期被泛化，整篇提升为 team standard。

### `runbooks/asan-debug-guide.md`

- owner review
- split approval
- applicable branch / SDK
- target binary
- actual build artifact path
- `DEBUG` / `libasan` / `prog_pcr02` / `/customer` paths 是否仍适用
- team candidate status
- external overlap decision

Pass gate：split 明确 project-local keep 与 team-level candidate-only；PCR02 build/binary/deploy/libasan 细节仅留在 `domains/projects/pcr02`；team-level 内容必须重写为通用候选并单独 review。

Fail gate：整篇复制到 team active path；`DEBUG=256`、`prog_pcr02`、`/customer`、`libasan` 被设为跨项目默认；owner/status/version 缺失。

### `runbooks/memory-auto-curation-guide.md`

- personal owner decision
- team owner approval if teamized
- `mode=report-only`
- `enabled=false`
- `writes_memory=false`
- `writes_team_active_index=false`
- hard no-memory-write gate
- allowed report artifact path
- secret scan
- rollback
- runtime evidence

Pass gate：report-only 且 disabled；不写 memory / team active index；no-memory-write 是 hard block；只允许 owner-approved report artifacts。

Fail gate：写 `~/.codex/memories` 或 curation inbox；进入 team active index；启用自动 send/commit/publish/delete/promote/memory-write；把 report-only 当 enablement approval。

### DVR plan

- unique status decision
- final branch / commit / tag
- proto generation / build / API DVR refcount / targeted grep 实际结果
- `task/iot` owner 和接入状态
- replay data channel
- `LIST_FETCH` 决策
- `RecordSetEvent` contract decision

Pass gate：owner 确认唯一状态；计划命令有实际结果 refs；最终 branch/commit/tag 附齐；`task/iot` 与 open items 明确。

Fail gate：owner 仍是 `local-codex`；无当前基线确认却保持 active；计划命令当作已通过；隐藏 `task/iot` gap；DVR 设计提升为 team standard。

### Motor MCU debug record

- Motor MCU / SoC owner review
- firmware version refs
- protection parameter table
- serial waveform / protocol log / hardware-start evidence
- field retest
- calibration before/after
- fault code / protocol fields
- whole-device validation
- unresolved items acknowledgement

Pass gate：archive-only 保留 unresolved items；facts/feedback/inference/recommendations/open items 分离；版本和参数证据齐全后才可 validation。

Fail gate：推断变 verified root cause；阶段固件行为当生产策略；无复测就写根因；参数冲突隐藏；open issues 被删除、关闭或省略。

### DVR session archive

- archive metadata approval
- `reviewed_by` / `reviewed_at`
- `source_status_at_capture`
- `contains_memory_candidates=true`
- `not_active_source=true`
- `extracts_require_owner_review=true`
- commit / branch / dirty-state
- validation refs
- memory candidate exclusion confirmation

Pass gate：target status 为 archive-only；Memory Candidates 排除 active extraction；validation extract 只含命令结果、branch/commit refs 和可复现证据；decision extract 只含 owner-confirmed DVR 生命周期和接口语义。

Fail gate：整篇复制到 current；handoff 当 active fact；memory candidates 写入 `~/.codex/memories`；dirty worktree notes 变项目事实；未 review 抽取 decision；因 archive 提及而清理/回退 source worktree。

## Forbidden Before Owner Decision

- 不把 owner-gated/reference-only 材料提前当成 active/current。
- 不把计划命令当验证结果。
- 不把 session handoff 或 memory candidates 当项目事实。
- 不把 PCR02 项目经验提升到团队标准。
- 不写 memory。
- 不启用 automation。
- 不修改源项目 docs。
- 不清理或回退源 worktree。

## Verification plan

```bash
rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run
rtk bash ~/knowledge-hub/tools/knowledge-search.sh "PCR02 owner action board"
rtk bash ~/knowledge-hub/tools/knowledge-search.sh "pcr02-owner-decision-worksheet-001"
rtk bash ~/knowledge-hub/tools/knowledge-search.sh "DVR session archive memory candidates"
rtk jq -c . artifacts/manifests/pcr02-owner-action-board-20260618.jsonl
```

## Review

- owner：`leiwenjun`
- review_after：`2026-09-17`
- validation_refs：`tools/knowledge-check.sh --dry-run`
