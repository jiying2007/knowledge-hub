# Knowledge Hub status owner landing command（2026-06-20）

## 结论

`tools/knowledge-status.sh` 的 owner gate 控制面现在直接暴露 owner 表单填完后的只读闭环命令：

- `owner_gates.validate_forms_command_templates`：按 source 校验 owner 填好的 JSONL 表单，包含需人工替换的 `<owner-decisions.jsonl>` 占位符。
- `owner_gates.landing_plan_command_templates`：按 source 生成无写入人工 landing plan，包含需人工替换的 `<owner-decisions.jsonl>` 占位符。
- `owner_gates.next_open.focus_validate_forms_command_template`：按下一条 open worksheet 聚焦校验 owner 表单。
- `owner_gates.next_open.focus_landing_plan_command_template`：按下一条 open worksheet 聚焦生成人工 landing plan。
- `strict_blockers[].commands` 只保留可直接执行的命令；`strict_blockers[].command_templates` 和 `next_actions_zh` 会在 owner gate 未签收时包含 `--validate-forms '<owner-decisions.jsonl>'` 与 `--landing-plan` 模板。

这个变更把 owner 审核路径从“导出空白表单”延伸到“校验已填表单”和“生成人工落地计划”，但不代替 owner 决策。

## 边界

- 不生成 owner decision。
- 不关闭 owner gate。
- 不自动填 `owner_decision`、`source_sha256` 或 `source_size`。
- 不自动写 registry、index、source policy 或迁移正文。
- 不修改源项目 docs。
- 不迁移 owner-gated source 正文。
- 不把 PCR02 project-specific 内容提升到 `domains/embedded/standards/`。
- 不启用自动化。
- 不写 `~/.codex/memories`。

## Evidence Index

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
| --- | ---: | --- | --- | --- | --- |
| `rtk bash tools/knowledge-status.sh --json` | 0 | 通过；`owner_gates.validate_forms_command_templates`、`owner_gates.landing_plan_command_templates`、`next_open.focus_validate_forms_command_template` 和 `next_open.focus_landing_plan_command_template` 均存在。 | `tools/knowledge-status.sh` | Tool | status-owner-landing-command |
| `rtk bash tools/knowledge-regression.sh --json` | 0 | 通过；`status-next-owner-gate` 回归覆盖 owner 表单校验、landing-plan、next-open 聚焦命令和 strict blocker 命令。 | `tools/knowledge-regression.sh` | Tool | status-owner-landing-command |
| `rtk bash tools/knowledge-check.sh --dry-run --json --diagnostics` | 0 | 通过；0 errors、0 warnings，本 manifest、registry、migration 和索引登记一致。 | `tools/knowledge-check.sh` | Knowledge Hub | status-owner-landing-command |
| `rtk bash tools/knowledge-final-gate.sh --json` | expected 1 | 终态门禁仍返回 `needs-owner-review`，因为 7 条 owner gate 尚未由 owner 人工签收；blocker `command_templates` 包含 validate-forms 和 landing-plan 模板。 | `tools/knowledge-final-gate.sh` | Knowledge Hub | status-owner-landing-command |

## Review

- owner：`leiwenjun`
- review_after：`2026-09-20`
- review_status：`status-owner-landing-command-applied`
- 下一次复核内容：若 owner status dashboard 的命令字段、owner 表单校验契约或 landing-plan 输出契约变化，需同步更新 README、tools README、回归和本 manifest。
