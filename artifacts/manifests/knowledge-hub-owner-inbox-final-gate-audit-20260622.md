# Knowledge Hub owner inbox and final gate audit 2026-06-22

## 结论

本轮把两个终态维护缺口收敛为可验证的只读工具契约。

- `tools/knowledge-owner-gates.sh --owner-inbox`
  - 用途：给真实 owner 一个单屏待办入口，按 worksheet 汇总 owner 中文问题、路由、字段分组、只读候选、owner-ready package、verification commands 和 validate/landing 模板。
  - 边界：不生成 owner decision，不写本地 JSONL，不关闭 owner gate，不把 `routing_owner` 当 `reviewed_by`。
- `tools/knowledge-final-gate.sh`
  - 用途：在原有 terminal gate 上增加当前 PCR02 Level 2 report-only source availability 证据和 10 条高优先级规则审计。
  - 边界：source check 只执行 allowlist 的 `test -d` / `test -f`，不读取 source 正文，不修改源项目，不改变 `knowledge-check` 的 `source_check_health` 静态契约。

本轮没有修改 PCR02 源项目文件，没有生成 owner decision，没有关闭 owner gate，没有把 PCR02 project-specific 内容提升到 `domains/embedded/standards/`，没有启用自动化写操作，也没有写 `~/.codex/memories`。

## Owner Inbox 合约

`--owner-inbox --json` 输出新增 `owner_inbox` 字段：

- `read_only=true`
- `report_only=true`
- `no_owner_decision_generated=true`
- `no_owner_gate_closed=true`
- `routing_owner_is_not_reviewed_by=true`
- `rows[].required_field_groups`
- `rows[].read_only_prefill_candidates`
- `rows[].commands.focus_command`
- `rows[].commands.forms_jsonl_command`
- `rows[].commands.evidence_readiness_command`
- `rows[].commands.validate_forms_command_template`
- `rows[].commands.landing_plan_command_template`
- `rows[].commands.landing_audit_command_template`

字段分组只降低人工复核成本；`owner_decision`、`target_decision`、`reviewed_by`、`reviewed_at`、`source_status` 和 `status_reason` 仍必须由真实 owner 填写。`source_sha256`、`source_size` 和 `review_after` 即使有候选值，也必须人工签收后才能落地。

## Final Gate 新证据

`knowledge-final-gate.sh --json` 新增：

- `source_check_runtime`
  - 当前执行 `rtk bash tools/knowledge-source-check.sh --scope pcr02-level2 --json --as-of <date>`。
  - 要求 `read_only=true`、`report_only=true`、`source_body_read=false`、`owner_gate_mutation=false`、`memory_write=false`、`automation_write=false`。
  - 当前期望 7 条 PCR02 Level 2 source availability row 全部 pass。
- `highest_priority_rules_audit`
  - 覆盖 `rtk` 命令边界、`apply_patch` 手工写入边界、no-memory-write、no-source-modification、no project-specific standards promotion、automation report-only、single canonical body、session/archive 不进入 active facts、尊重已有 worktree 改动和 evidence-before-completion。
  - 对无法机器证明的流程规则标记为 `process-audited`，避免把运行脚本误写成历史全过程证明。

## Evidence Index

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
|---|---:|---|---|---|---|
| `rtk bash -n tools/knowledge-owner-gates.sh` | 0 | 通过；owner gate helper 语法检查通过。 | `tools/knowledge-owner-gates.sh` | Tool | `knowledge-hub-owner-inbox-final-gate-audit-20260622` |
| `rtk bash -n tools/knowledge-final-gate.sh` | 0 | 通过；final gate helper 语法检查通过。 | `tools/knowledge-final-gate.sh` | Tool | `knowledge-hub-owner-inbox-final-gate-audit-20260622` |
| `rtk bash -n tools/knowledge-regression.sh` | 0 | 通过；regression helper 语法检查通过。 | `tools/knowledge-regression.sh` | Tool | `knowledge-hub-owner-inbox-final-gate-audit-20260622` |
| `rtk bash tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --owner project-owner --owner-inbox --json` | 0 | 通过；`owner_inbox.row_count=2`，`read_only=true`，`no_owner_decision_generated=true`，`routing_owner_is_not_reviewed_by=true`。 | `tools/knowledge-owner-gates.sh` | Tool | `owner-inbox-contract` |
| `rtk bash tools/knowledge-final-gate.sh --json --as-of 2026-06-22` | 1 | 预期停在 owner-review；`automatic_governance.status=complete-except-owner-review`，`source_check_runtime.status=pass`，唯一 blocker 为 7 个 `owner-gates-open`。 | `tools/knowledge-final-gate.sh` | Gate | `knowledge-final-gate` |
| `rtk bash tools/knowledge-regression.sh --json --as-of 2026-06-22` | 0 | 通过；`status=pass`，`result_count=91`。 | `tools/knowledge-regression.sh` | Gate | `knowledge-regression` |
| `rtk bash tools/knowledge-check.sh --dry-run --json --diagnostics --as-of 2026-06-22` | 0 | 通过；`status=pass`，errors=0，warnings=0。 | `tools/knowledge-check.sh` | Gate | `knowledge-check` |

## 边界

- 不生成 owner decision。
- 不关闭 owner gate。
- 不修改 PCR02 源项目。
- 不读取 PCR02 source 正文。
- 不写 `~/.codex/memories`。
- 不启用自动化写操作。
- 不把 `routing_owner` 自动填成 `reviewed_by`。
- 不把 `path-exists` 当作内容正确、语义可迁移或 owner 已签收。
