# PCR02 Owner Intake Package - 2026-06-18

## 摘要

本 intake package 把 PCR02 docs governance 剩余 7 个 owner-gated 条目整理成中文可签收清单。它面向 owner 填写、补证和确认边界，不代表 owner 已签收，不关闭 blocker，不创建 active/current 项目事实。

当前安全终态：

- 32 个 PCR02 docs 源文件已有治理归宿覆盖。
- 7 个 owner-gated 条目仍未 resolved。
- closeout 已完成到 governance / handoff 层，promotion 仍 blocked 于 owner resolution。
- 本包只负责提高 owner 签收可读性和可执行性。

## 共同必填字段

每个 owner-gated 条目进入任何迁移、抽取、提升或归档状态变更前，必须补齐以下字段：

| 中文字段 | 对应结构化字段 | 说明 |
| --- | --- | --- |
| 条目编号 | `id` / `source_review_id` | 必须能回链到 worksheet 和 action board。 |
| 源文件路径 | `source_path` | 必须保持源路径原样，不改写成目标路径。 |
| 候选 Owner | `owner_candidate` / `owner_required` | 必须由真实 owner 或授权 reviewer 确认。 |
| Owner 决策 | `owner_decision` | 只能从该条目的允许选项中选择。 |
| 目标落点决策 | `target_decision` | 必须说明 reference-only、archive-only、project-local 或 no-migration。 |
| 当前源状态 | `source_status` | 必须说明 current、stale、superseded、archive-only 或 unknown。 |
| 审核人 | `reviewed_by` | 不能长期保留为空。 |
| 审核时间 | `reviewed_at` | 使用 `YYYY-MM-DD`。 |
| 下次复核时间 | `review_after` | 当前建议统一为 `2026-09-17`。 |
| 源文件 SHA256 | `source_sha256` | 必须匹配 worksheet 中的 expected hash。 |
| 源文件大小 | `source_size` | 必须匹配 worksheet 中的 expected size。 |
| 适用范围/版本 | `scope_statement` / `applicable_*` | 必须说明项目、分支、SDK、固件或阶段。 |
| 证据引用 | `evidence_refs` | 必须引用可复查的命令输出、commit、tag、日志、报告或 owner exception。 |
| 状态原因 | `status_reason` | 必须解释为什么选择该状态。 |
| 硬门禁结论 | `hard_gate_summary` | 当前只能是 `门禁待补证`，不能写 `已通过`。 |
| 未决事项 | `open_items` | 不得隐藏仍未验证的问题。 |

## Owner 签收清单

### 1. `AGENTS.md`

- 候选 owner：`team-core-or-pcr02-docs-owner`
- 当前默认状态：`reference-only-pending-owner-gate`
- Owner 提问：是否确认该文件只代表 PCR02 项目本地规则，而不是 Knowledge Hub 根规则或团队标准；若保留，目标只允许落在 PCR02 项目边界的哪个位置？
- 必补证据：当前有效性、project-only scope、适用分支 / SDK / 项目阶段、owner sign-off、review cycle、source hash / size、target decision reason。
- 硬门禁：未明确当前有效性、项目边界、适用版本，或目标指向根 `AGENTS.md` / `domains/embedded/standards/`，一律不能越过。
- 硬门禁结论：`门禁待补证`
- 推荐下一步：填写 `pcr02-owner-decision-worksheet-001`，只允许 `project-local-rule`、`reference-only` 或 `no-migration`。

### 2. `standards/diag-command-metadata-standard.md`

- 候选 owner：`pcr02-diag-owner-or-team-core`
- 当前默认状态：`reference-only-pending-owner-gate`
- Owner 提问：是否确认它仍是 PCR02 的 project-only source of truth，且 provider lifecycle、metadata、catalog/help 运行态与文档一致；若不一致，是转 `reference-only` 还是给 documented owner exception？
- 必补证据：diag owner sign-off、适用 branch / firmware / SDK、provider lifecycle match、metadata / catalog / help runtime match、5 类 diag gate 实际结果或 owner exception。
- 硬门禁：缺少 gate evidence 且没有 owner exception，或把 PCR02 命令名、路径、生命周期泛化为团队标准，不能越过。
- 硬门禁结论：`门禁待补证`
- 推荐下一步：填写 `pcr02-owner-decision-worksheet-002`，并附实际 diag gate 输出。

### 3. `runbooks/asan-debug-guide.md`

- 候选 owner：`team-core`
- 当前默认状态：`split-required / blocked-pending-owner-review`
- Owner 提问：是否批准拆分边界，把 `DEBUG=256`、`prog_pcr02`、`/customer/*`、`libasan` 等 PCR02 细节仅保留项目内；团队层是否只保留 candidate-only 并另行重写审查？
- 必补证据：split approval、适用 branch / SDK、target binary、实际 build artifact path、PCR02 构建/部署路径适用性、team candidate status、external overlap decision。
- 硬门禁：未明确 split-approved，或整篇复制到 team active path，或把 PCR02 构建/部署路径当跨项目默认，不能越过。
- 硬门禁结论：`门禁待补证`
- 推荐下一步：填写 `pcr02-owner-decision-worksheet-003`，只做 project-local keep 与 team candidate boundary，不直接创建团队标准。

### 4. `runbooks/memory-auto-curation-guide.md`

- 候选 owner：`personal-owner-and-team-review-if-teamized`
- 当前默认状态：`blocked-personal-local`
- Owner 提问：是否仅允许 `personal-local`，还是批准一个 `teamized-report-only` 的禁用治理版本；若团队化，能否明确 `enabled=false`、`writes_memory=false`、`writes_team_active_index=false`？
- 必补证据：personal owner decision、team owner approval if teamized、report-only mode、enabled=false、no-memory-write hard gate、secret scan、rollback、runtime no-write evidence。
- 硬门禁：任何写 `~/.codex/memories`、写 team active index、自动 send/commit/publish/delete/promote/memory-write 的路径都不能越过。
- 硬门禁结论：`门禁待补证`
- 推荐下一步：填写 `pcr02-owner-decision-worksheet-004`，只允许 disabled report-only governance 或 personal-local reference。

### 5. `plans/2026-06-15-dvr-record-proto-sensor-decoupling-plan.md`

- 候选 owner：`project-owner`
- 当前默认状态：`completed-after-owner-gate preferred, otherwise blocked-pending-owner-status-decision`
- Owner 提问：该计划最终只能选一个状态。请确认是 `completed`、`superseded`、`active-if-owner-confirms-current-baseline` 还是 `archive-only`，并提供 branch / commit / tag 与 proto / build / refcount / grep 的实际结果引用。
- 必补证据：唯一状态、最终 branch / commit / tag、proto generation、build、API DVR refcount、targeted grep、`task/iot` 状态、replay data channel、`LIST_FETCH` 决策、`RecordSetEvent` contract extract decision。
- 硬门禁：把计划命令当已验证结果、继续使用 `local-codex` 作为长期 owner、未确认当前基线却保持 active，不能越过。
- 硬门禁结论：`门禁待补证`
- 推荐下一步：填写 `pcr02-owner-decision-worksheet-005`，优先将状态收敛为 completed / superseded / archive-only。

### 6. `reports/2026-05-29-motor-mcu-debug-record.md`

- 候选 owner：`motor-mcu-or-soc-owner`
- 当前默认状态：`archive-only`
- Owner 提问：是否只按 `archive-only` 保留，还是补齐固件版本、保护参数、波形 / 协议日志、复测、校准前后、整机验证后再考虑 `validation-report-candidate`？
- 必补证据：Motor MCU / SoC owner review、firmware version refs、protection parameter table、serial waveform / protocol log、hardware-start evidence、field retest、calibration before/after、fault code / protocol fields、whole-device validation、unresolved items acknowledgement。
- 硬门禁：把推断写成已验证根因、把阶段固件行为写成生产策略、隐藏 `1.3A for 3s` vs `10s` 等未决冲突，不能越过。
- 硬门禁结论：`门禁待补证`
- 推荐下一步：填写 `pcr02-owner-decision-worksheet-006`，默认保留 archive-only，验证证据补齐后再考虑 validation candidate。

### 7. `reports/2026-06-16-dvr-record-replay-session-archive.md`

- 候选 owner：`project-owner`
- 当前默认状态：`archive-only`
- Owner 提问：是否确认该材料永远只作为 `archive-only`，且只允许抽取 owner 已确认的 decision / validation evidence，不允许把 handoff、dirty-state、memory candidates 提升成 active fact？
- 必补证据：archive metadata approval、reviewed_by / reviewed_at、source_status_at_capture、contains_memory_candidates=true、not_active_source=true、extracts_require_owner_review=true、commit / branch / dirty-state、validation refs、memory candidate exclusion confirmation。
- 硬门禁：把整篇 session archive 复制进 current、把 `Memory Candidates` 写入 `~/.codex/memories`、未 owner review 就抽 decision，不能越过。
- 硬门禁结论：`门禁待补证`
- 推荐下一步：填写 `pcr02-owner-decision-worksheet-007`，只允许 archive-only。

## 回填流程

1. Owner 先确认源文件 SHA256 和 size。
2. Owner 在对应 worksheet 中填写 owner decision、target decision、source status、status reason 和 evidence refs。
3. 若涉及 gate 命令，必须附实际输出或 documented owner exception。
4. 主线程根据 owner 决策更新 registry/index/manifest，仍不得修改源项目 docs。
5. 只有在 owner 决策、证据、review cycle 和知识库验证都满足后，才允许考虑迁移、抽取或状态提升。

## 禁止事项

- 不把 owner-gated/reference-only 材料提前当成 active/current。
- 不把计划命令当验证结果。
- 不把 handoff、session archive、memory candidates 当项目事实。
- 不写 `~/.codex/memories`。
- 不启用 automation。
- 不修改源项目 docs。
- 不把 PCR02 project-specific 内容提升到 `domains/embedded/standards/`。
- 不处理无关 `~/codex` 脏文件。

## 验证计划

```bash
rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run
rtk bash ~/knowledge-hub/tools/knowledge-search.sh "PCR02 owner intake package"
rtk bash ~/knowledge-hub/tools/knowledge-search.sh "硬门禁结论"
rtk bash ~/knowledge-hub/tools/knowledge-search.sh "门禁待补证"
rtk jq -c . artifacts/manifests/pcr02-owner-intake-package-20260618.jsonl
```

## Review

- owner：`leiwenjun`
- status：`reviewing`
- review_status：`owner-intake-ready`
- promotion：`none`
- review_after：`2026-09-17`
