# Knowledge Hub status dispatch and notes_zh sync 2026-06-21

## 结论

本轮继续压实 Knowledge Hub 终态恢复路径，聚焦可由 Codex 自动完成、且不需要 owner 语义决策的维护缺口：

- `knowledge-status.sh --json` 现在直接输出 `owner_gates.owner_dispatch[]`，让状态看板本身携带按 owner 分派的 summary、forms-jsonl、validate-forms、landing-plan 和 next focus 入口。
- `knowledge-final-gate.sh --json` 现在透传 `owner_recovery`，让终态 gate 结果本身携带 open owner 数量、owner-ready 覆盖、`owner_dispatch[]` 和下一条 open gate。
- `knowledge-owner-gates.sh` 的 forms/checklist/landing plan 现在显式带出 `verification_cwd` / `worksheet_verification_cwd`，降低 owner 人工执行项目侧相对命令时走错 cwd 的风险。
- `knowledge-check.sh` 现在阻断 2026-06-21 及之后缺少 `ai_model_or_tool` 或 `ai_generated_at` 的 AI-generated registry item。
- `knowledge-new.sh` 的 `registry/items.jsonl` 可复制草稿补齐 `notes_zh`，避免 2026-06-21 及之后人工按向导复制出的 source policy row 先天不满足中文可读性门禁。

本轮不生成 owner decision，不关闭 owner gate，不修改 PCR02 源项目，不复制 owner-gated source 正文，不提升 PCR02 project-specific 内容到 `domains/embedded/standards/`，不启用自动化写操作，不写 `~/.codex/memories`。

## 处理的 Gap

| gap_id | gap_type | evidence | 当前影响 | 本轮动作 | 状态 |
|---|---|---|---|---|---|
| SDNZ-20260621-001 | cross-session-linking | `knowledge-status --json` 只有 owner command lists，没有结构化 `owner_dispatch` rows | 新会话只看 status dashboard 时，仍需二次调用 summary 或人工重新聚合 owner 分派包 | 在 status JSON 的 `owner_gates` 下增加 `owner_dispatch[]`，字段与 owner summary 分派包保持一致 | applied |
| SDNZ-20260621-002 | Chinese-readability | `knowledge-new.sh` source policy 草稿缺少 `notes_zh` | 人工按向导新增迁移/引用/归档记录后，会触发 2026-06-21 后 source policy `notes_zh` 门禁 | 在 migration skeleton 中补 `notes_zh` 中文摘要，并补回归断言 | applied |
| SDNZ-20260621-003 | final-state-recovery | `knowledge-final-gate --json` 只有 blockers/gap_map，没有直接透传 owner 分派队列 | 新线程只拿 final gate JSON 时，还要回读 status dashboard 才能恢复 owner 分派 | 增加 `owner_recovery`，包含 open_count、owner_ready_package_coverage、owner_dispatch 和 next_open | applied |
| SDNZ-20260621-004 | owner-command-cwd | owner landing plan 只有 worksheet 命令，没有机器可读 cwd | PCR02 项目侧相对命令容易被误认为在 Knowledge Hub root 下运行 | forms/checklist/landing plan 带出 `verification_cwd` / `worksheet_verification_cwd`，并为 branch/dirty owner 字段补 git 状态命令 | applied |
| SDNZ-20260621-005 | ai-provenance | 2026-06-21 AI-generated registry item 缺少统一模型/工具和生成时间字段 | 长期追溯时无法区分 AI 生成来源，也无法稳定审计新增条目的 provenance | `knowledge-check` 增加 AI provenance 硬门禁，并补齐已有同日 registry item | applied |

## `owner_gates.owner_dispatch[]` 契约

`knowledge-status.sh --json` 的 `owner_gates.owner_dispatch[]` 每行包含：

- `owner`
- `source_id`
- `row_count`
- `open_count`
- `worksheet_ids`
- `source_paths`
- `summary_command`
- `forms_jsonl_command`
- `validate_forms_command_template`
- `landing_plan_command_template`
- `next_focus_command`
- `notes_zh`

这些字段只用于跨会话恢复 owner 分派和人工签收入口，不生成 owner decision，不关闭 gate。

## `owner_recovery` 契约

`knowledge-final-gate.sh --json` 的 `owner_recovery` 包含：

- `open_count`
- `owner_ready_package_coverage`
- `active_exposure_count`
- `owner_dispatch`
- `next_open`
- `notes_zh`

该字段是只读恢复队列；即使 final gate 返回 `needs-owner-review`，也不代表 owner 已签收，不自动落地 owner decision。

## Evidence Index

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
|---|---:|---|---|---|---|
| `rtk bash -n tools/knowledge-status.sh` | 0 | 通过；status dashboard shell wrapper 语法有效。 | `tools/knowledge-status.sh` | Tool | `knowledge-hub-status-dispatch-notes-zh-20260621` |
| `rtk bash -n tools/knowledge-new.sh` | 0 | 通过；manual entry guide shell wrapper 语法有效。 | `tools/knowledge-new.sh` | Tool | `knowledge-hub-status-dispatch-notes-zh-20260621` |
| `rtk bash -n tools/knowledge-owner-gates.sh` | 0 | 通过；owner gate helper shell wrapper 语法有效。 | `tools/knowledge-owner-gates.sh` | Tool | `knowledge-hub-status-dispatch-notes-zh-20260621` |
| `rtk bash -n tools/knowledge-final-gate.sh` | 0 | 通过；final gate shell wrapper 语法有效。 | `tools/knowledge-final-gate.sh` | Tool | `knowledge-hub-status-dispatch-notes-zh-20260621` |
| `rtk bash -n tools/knowledge-check.sh` | 0 | 通过；knowledge-check shell wrapper 语法有效。 | `tools/knowledge-check.sh` | Tool | `knowledge-hub-status-dispatch-notes-zh-20260621` |
| `rtk bash -n tools/knowledge-regression.sh` | 0 | 通过；knowledge-regression shell wrapper 语法有效。 | `tools/knowledge-regression.sh` | Tool | `knowledge-hub-status-dispatch-notes-zh-20260621` |
| `rtk bash ~/knowledge-hub/tools/knowledge-status.sh --json` | 0 | 通过；JSON 中 `owner_gates.owner_dispatch[]` 暴露 6 个 owner 分派包，project-owner 包含 2 个 open gate；`knowledge_check.status=pass`。 | `tools/knowledge-status.sh` | Tool | `knowledge-hub-status-dispatch-notes-zh-20260621` |
| `rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --owner project-owner --forms-jsonl` | 0 | 通过；owner form JSONL 带出 `verification_cwd`，DVR plan/session worksheet 带出项目侧 git 状态命令。 | `tools/knowledge-owner-gates.sh` | Tool | `knowledge-hub-status-dispatch-notes-zh-20260621` |
| `rtk bash ~/knowledge-hub/tools/knowledge-new.sh --kind decision --domain governance --id governance-conditional-migration --path governance/conditional-migration.md` | 0 | 通过；source policy 草稿包含 `notes_zh`。 | `tools/knowledge-new.sh` | Tool | `knowledge-hub-status-dispatch-notes-zh-20260621` |
| `rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics` | 0 | 通过；全仓 0 errors / 0 warnings。 | `tools/knowledge-check.sh` | Gate | `knowledge-hub-status-dispatch-notes-zh-20260621` |
| `rtk bash ~/knowledge-hub/tools/knowledge-regression.sh --json` | 0 | 通过；61 个回归场景全部 pass，覆盖 status owner_dispatch、final gate owner_recovery、owner cwd、AI provenance gate 和 source policy notes_zh。 | `tools/knowledge-regression.sh` | Regression | `knowledge-hub-status-dispatch-notes-zh-20260621` |
| `rtk bash ~/knowledge-hub/tools/knowledge-final-gate.sh --json` | 1 | 预期返回 1；`final_status=needs-owner-review`，`automatic_governance.status=complete-except-owner-review`，唯一 gap 为 7 个 `owner-gates-open`。 | `tools/knowledge-final-gate.sh` | Final Gate | `knowledge-hub-status-dispatch-notes-zh-20260621` |
| `rtk git diff --check` | 0 | 通过；无 whitespace error。 | git diff | Git | `knowledge-hub-status-dispatch-notes-zh-20260621` |

## 边界

- 不生成或伪造 owner decision。
- 不关闭任何 owner gate。
- 不修改 PCR02 源项目。
- 不复制 owner-gated source 正文。
- 不把 PCR02 project-specific 内容提升为团队标准。
- 不启用自动化写操作。
- 不写 `~/.codex/memories`。
