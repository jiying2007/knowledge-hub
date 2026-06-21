# Knowledge Hub owner target and landing validation 2026-06-21

## 结论

本轮继续压实 owner-gated 内容的人工签收路径，完成四个非 owner 冲突切片：

1. `knowledge-owner-gates.sh --validate-forms` 校验 `target_decision` 必须来自 worksheet 的 `target_candidates`，防止 owner 表单把 PCR02 项目内容落到候选范围之外，例如误写到 `domains/embedded/standards/`。
2. `knowledge-owner-gates.sh --landing-plan` 的每个 step 带出 worksheet 原始 `verification_commands`，让人工落地后能直接按 source-specific 命令或等价证据复核。
3. `knowledge-owner-gates.sh --validate-forms` 把 `must_not` 和 `allowed_owner_decisions` 漂移从 warning 提升为 hard error，防止表单携带被改写的 guardrail 或决策枚举进入 landing plan。
4. `knowledge-status.sh` 增加 by-owner validate/landing command templates，并在 README 恢复路径补 `indexes/by-status.md`，降低人工分派和跨会话恢复的发现成本。

这些改动只增强表单校验和人工落地提示，不生成 owner decision，不关闭 owner gate，不修改 PCR02 源项目文件。

## 变更范围

- `tools/knowledge-owner-gates.sh`
  - 在 owner form 校验中拒绝非空且不属于 `target_candidates` 的 `target_decision`。
  - 在 owner form 校验中拒绝 `must_not` 或 `allowed_owner_decisions` 与 worksheet 不一致。
  - 在 landing plan step 中增加 `worksheet_verification_commands`。
  - 文本 landing plan 输出同步展示每个 step 的 worksheet 验证命令。
- `tools/knowledge-status.sh`
  - 增加 `owner_validate_forms_command_templates` 与 `owner_landing_plan_command_templates`。
  - 文本模式和 strict blocker 同步暴露 by-owner 校验与 landing 模板，仍要求人工替换 `<owner-decisions.jsonl>`。
- `tools/knowledge-regression.sh`
  - 新增 `owner-form-target-decision-candidate-gate` 负向场景。
  - 新增 `owner-form-must-not-tamper-gate` 和 `owner-form-allowed-decisions-tamper-gate` 负向场景。
  - 扩展 `status-next-owner-gate` 和 `status-text-owner-summary-commands`，要求状态看板暴露 by-owner validate/landing 模板。
  - 扩展 `owner-landing-plan-project-index`，要求 landing plan step 带出 worksheet 验证命令。
  - 回归场景数更新为 55。
- `README.md`、`tools/README.md`
  - 补充 owner 表单 `target_decision` 必须从 `target_candidates` 选择。
  - 补充 landing plan 会带出 `worksheet_verification_commands`。
  - 补充 by-owner owner 表单校验、landing plan 和 `by-status` 恢复入口。
- `artifacts/manifests/knowledge-hub-governance-regression-helper-20260619.md`
  - 同步新增回归场景和 55 个场景计数。

## 边界

- 不生成 owner decision。
- 不关闭 owner gate。
- 不修改 PCR02 源项目 docs / tools / knowledge / app_product_test / scratch / source tree。
- 不复制 owner-gated source 正文。
- 不把 PCR02 project-specific 内容提升到 `domains/embedded/standards/`。
- 不启用自动化写操作，不写 memory。

## Evidence Index

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
|---|---:|---|---|---|---|
| `rtk bash -n tools/knowledge-owner-gates.sh` | 0 | 通过；owner gate 工具语法有效。 | `tools/knowledge-owner-gates.sh` | Tool | `knowledge-hub-owner-target-landing-validation-20260621` |
| `rtk bash -n tools/knowledge-status.sh` | 0 | 通过；status dashboard 入口语法有效。 | `tools/knowledge-status.sh` | Tool | `knowledge-hub-owner-target-landing-validation-20260621` |
| `rtk bash -n tools/knowledge-regression.sh` | 0 | 通过；回归入口语法有效。 | `tools/knowledge-regression.sh` | Tool | `knowledge-hub-owner-target-landing-validation-20260621` |
| `rtk bash tools/knowledge-status.sh --json` | 0 | 通过；状态看板输出 by-owner `owner_validate_forms_command_templates`、`owner_landing_plan_command_templates` 和 strict blocker command_templates，仍保持 `needs-owner-review`。 | `tools/knowledge-status.sh` | Tool | `knowledge-hub-owner-target-landing-validation-20260621` |
| `rtk bash tools/knowledge-regression.sh --json` | 0 | 通过；55 个回归场景全部 pass，覆盖 owner target_decision 候选目标门禁、owner guardrail/decision enum 篡改拒绝、status by-owner validate/landing 模板和 landing plan worksheet 验证命令。 | `tools/knowledge-regression.sh` | Tool | `knowledge-hub-owner-target-landing-validation-20260621` |
| `rtk bash tools/knowledge-check.sh --dry-run --json --diagnostics` | 0 | 通过；0 errors、0 warnings。 | `tools/knowledge-check.sh` | Tool | `knowledge-hub-owner-target-landing-validation-20260621` |
| `rtk git diff --check` | 0 | 通过；无 whitespace 或 conflict marker 问题。 | git diff | Tool | `knowledge-hub-owner-target-landing-validation-20260621` |
| `rtk bash tools/knowledge-final-gate.sh --json` | 1 | 符合预期；`final_status=needs-owner-review`，`automatic_governance.status=complete-except-owner-review`，`knowledge_check`/`knowledge_regression`/`git_diff_check` 均 pass，唯一 blocker 为 7 个 owner gate。 | `tools/knowledge-final-gate.sh` | Tool | `knowledge-hub-owner-target-landing-validation-20260621` |

## 最终验证

已完成提交前验证。当前终态仍是 `needs-owner-review`：Codex 自动治理可闭环，但 7 个 PCR02 owner decision worksheet 仍需人工语义签收。
