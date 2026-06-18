# PCR02 Owner Resolution Schema - 2026-06-18

## 摘要

本 schema 固化 PCR02 剩余 7 个 owner-gated 文档在 owner 决策返回后的字段、枚举和禁止组合。它是 `pcr02-owner-resolution-playbook-20260618.md` 的机器校验补充，不是 owner 决策结果，不关闭 blocker，不把任何条目标记为 active/current。

检索提示：`identity_status 独立建模`、`owner invalid-combination gate`、`source identity match 不能自动 active`、`owner-resolution-schema-ready`。

适用范围：

- 仅适用于 PCR02 owner-gated docs 的 owner 决策落地记录。
- 不替代全局 `registry/schema.md`。
- 不修改源项目 docs。
- 不写 `~/.codex/memories`。
- 不启用 automation。
- 不把 PCR02 project-specific 内容提升到 `domains/embedded/standards/`。

## 设计原则

1. `identity_status` 独立表示源文件身份核验结果，不能混入 `review_status`。
2. `review_status` 表示 owner gate 和控制面进度，不表示语义已生效。
3. `status` 仍使用 registry canonical 子集：`active`、`reviewing`、`archived`。
4. `owner_decision` 记录 owner 原始决策；`promotion_decision` 记录 Knowledge Hub 落地路线。
5. `source_path` 到 `owner_decision` 的枚举以 owner decision worksheet 为准。
6. 所有自动生效、写 memory、写源文档、提升 team standard 的字段默认必须为 false。

## 公共必填字段

每条 owner resolution row 必须包含：

| 字段 | 说明 |
| --- | --- |
| `id` | 本次 resolution row 唯一 ID。 |
| `source_review_id` | 对应 `pcr02-review-required-*` 源 review row。 |
| `source_id` | 固定为 `pcr02-project-docs`。 |
| `source_path` | PCR02 docs 相对路径。 |
| `source_sha256_expected` | owner worksheet 中的 expected hash。 |
| `source_size_expected` | owner worksheet 中的 expected size。 |
| `source_sha256` | 落地前实际核验 hash。 |
| `source_size` | 落地前实际核验 size。 |
| `identity_status` | 源文件身份核验状态。 |
| `owner_required` | owner 是否必需。 |
| `owner_decision` | owner 原始选择。 |
| `target_decision` | 中文目标落地说明。 |
| `target_scope` | 目标范围，例如 `pcr02-project-local`、`reference-only`、`archive-only`。 |
| `reviewed_by` | owner 或 reviewer。 |
| `reviewed_at` | owner 决策日期。 |
| `review_after` | 下一次复核日期。 |
| `source_status` | 源材料状态，例如 `current-source-match`。 |
| `review_status` | owner gate 进度。 |
| `status` | registry canonical status。 |
| `promotion_decision` | Knowledge Hub 提升或保留路线。 |
| `auto_effective` | 是否自动生效；默认 false。 |
| `automation_enabled` | 是否启用自动化；默认 false。 |
| `writes_memory` | 是否写 memory；必须 false。 |
| `writes_source_doc` | 是否写源项目 docs；必须 false。 |
| `promotes_to_embedded_standard` | 是否提升 embedded standard；必须 false。 |
| `source_identity_verified` | 是否完成 hash/size 身份核验。 |
| `owner_gate_verified` | owner gate 是否满足。 |
| `knowledge_check_passed` | 本次落地后 knowledge-check 是否通过。 |
| `evidence_refs` | owner、hash、size、验证证据引用。 |
| `validation_refs` | 实际验证命令或报告引用。 |
| `status_reason` | 中文状态原因。 |
| `open_items` | 未决事项。 |

## 枚举

### `identity_status`

- `identity-unchecked`
- `source-identity-match`
- `source-identity-mismatch`
- `source-missing`
- `source-changed-after-review`

### `review_status`

- `pending-owner-review`
- `needs-owner-resolution`
- `owner-intake-ready`
- `source-identity-match`
- `owner-resolution-playbook-ready`
- `owner-resolution-schema-ready`
- `owner-decision-recorded`
- `owner-gate-satisfied`
- `owner-approved-reference-only`
- `owner-approved-archive-only`
- `owner-approved-project-local-rule-pending-verification`
- `owner-approved-project-current-pending-verification`
- `owner-approved-project-decision-pending-verification`
- `owner-approved-validation-candidate-pending-verification`
- `owner-approved-split-pending-rewrite`
- `owner-rejected`

### `status`

- `active`
- `reviewing`
- `archived`

### `promotion_decision`

- `none`
- `reference-only`
- `archive-only`
- `project-local-rule`
- `project-current`
- `project-decision`
- `candidate-only`
- `validation-candidate`
- `no-migration`

## Source Path 决策枚举

| Source path | 允许的 `owner_decision` | 额外必填字段 |
| --- | --- | --- |
| `AGENTS.md` | `project-local-rule`、`reference-only`、`no-migration` | `current_validity`、`scope_statement`、`applicable_project_version` |
| `standards/diag-command-metadata-standard.md` | `pcr02-project-decision-after-owner-gate`、`pcr02-project-current-after-owner-gate`、`reference-only`、`no-migration` | `project_only_source_of_truth`、`applicable_branch_firmware_version`、`implementation_match`、`gate_evidence` |
| `runbooks/asan-debug-guide.md` | `split-approved`、`active-project-local`、`team-candidate-only`、`reference-only`、`rejected` | `split_approval`、`applicable_branch_or_sdk_version`、`target_binary`、`team_level_status` |
| `runbooks/memory-auto-curation-guide.md` | `personal-local`、`teamized-report-only`、`rejected`、`no-migration` | `governance_mode`、`automation_enabled`、`writes_memory`、`writes_team_active_index`、`no_memory_write_gate`、`manual_approval_owner`、`manual_approval_cadence` |
| `plans/2026-06-15-dvr-record-proto-sensor-decoupling-plan.md` | `completed`、`superseded`、`active-if-owner-confirms-current-baseline`、`archive-only` | `final_branch_commit_or_tag_refs`、`proto_generation_evidence`、`build_evidence`、`api_dvr_refcount_evidence`、`targeted_grep_evidence`、`task_iot_dependency_status`、`replay_data_channel_status` |
| `reports/2026-05-29-motor-mcu-debug-record.md` | `archive-only`、`validation-report-candidate` | `firmware_version_refs`、`protection_parameter_table`、`serial_waveform_or_protocol_logs`、`hardware_start_evidence`、`field_retest_records`、`calibration_before_after_data`、`fault_code_or_protocol_field_definitions`、`whole_device_validation_records`、`unresolved_items_acknowledgement` |
| `reports/2026-06-16-dvr-record-replay-session-archive.md` | `archive-only` | `source_status_at_capture`、`contains_memory_candidates`、`not_active_source`、`extracts_require_owner_review`、`commit_branch_dirty_state_evidence`、`proto_generation_evidence_refs`、`build_evidence_refs`、`refcount_evidence_refs`、`grep_evidence_refs`、`final_ready_evidence_refs`、`memory_candidates_exclusion_confirmation` |

## 禁止组合

1. `review_status in ["source-identity-match","owner-intake-ready","owner-resolution-playbook-ready","owner-resolution-schema-ready"]` 时，`status` 必须为 `reviewing`，`auto_effective` 必须为 false。
2. `review_status="source-identity-match"` 不能推出 `owner_gate_verified=true`、`knowledge_check_passed=true` 或 current/decision 目标。
3. overlay 状态词不得写入 registry canonical `status`。
4. `AGENTS.md` + `owner_decision="project-local-rule"` 不得使用 root `AGENTS.md`、team-global、embedded-standard 作为目标。
5. diag current/decision 必须有 `project_only_source_of_truth=true`，且必须有 `implementation_match` 与 `gate_evidence`，或明确 owner exception。
6. memory auto-curation 的 `teamized-report-only` 必须满足 `automation_enabled=false`、`governance_mode="report-only"`、`writes_memory=false`、`writes_team_active_index=false`、`writes_source_doc=false`。
7. DVR session archive 的 `archive-only` 必须满足 `contains_memory_candidates=true`、`not_active_source=true`、`extracts_require_owner_review=true`，且不得设置 project-current/project-decision。
8. DVR plan 终态必须且只能是 `completed`、`superseded`、`active-if-owner-confirms-current-baseline`、`archive-only` 之一。
9. Motor validation-report-candidate 必须保留 unresolved acknowledgement，且不得直接 active。
10. `writes_memory`、`writes_source_doc`、`promotes_to_embedded_standard` 默认必须为 false。
11. `owner_gate_verified=false` 时不得设置 `status=active`。
12. `source_identity_verified=false` 或 `identity_status!="source-identity-match"` 时不得继续 owner 决策落地。

## 机器校验建议

后续若新增校验脚本，可按本 manifest 的 JSONL 条目生成 report-only 检查：

```bash
rtk jq -c . artifacts/manifests/pcr02-owner-resolution-schema-20260618.jsonl
rtk jq -r 'select(.category=="invalid-combination") | .id' artifacts/manifests/pcr02-owner-resolution-schema-20260618.jsonl
rtk bash tools/knowledge-check.sh --dry-run --json
```

校验脚本不得自动修改 registry、index、source docs 或 memory。

## Review

- owner：`leiwenjun`
- status：`reviewing`
- review_status：`owner-resolution-schema-ready`
- promotion：`none`
- review_after：`2026-09-17`
