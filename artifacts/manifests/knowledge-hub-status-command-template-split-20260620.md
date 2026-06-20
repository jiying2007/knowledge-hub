# Knowledge Hub status command template split（2026-06-20）

## 结论

`tools/knowledge-status.sh` 和 `tools/knowledge-final-gate.sh` 现在区分两类 owner blocker 后续动作：

- `strict_blockers[].commands`：只放不含占位符、可直接复制执行的只读命令。
- `strict_blockers[].command_templates`：放需要人工替换 `<owner-decisions.jsonl>` 的只读命令模板。
- `owner_gates.validate_forms_command_templates` 和 `owner_gates.landing_plan_command_templates` 明确表达表单校验与 landing-plan 是模板，不是自动执行命令。
- `owner_gates.next_open.focus_validate_forms_command_template` 和 `owner_gates.next_open.focus_landing_plan_command_template` 保留下一条 worksheet 聚焦模板。

该拆分降低未来自动化或人工脚本误把占位符命令当作可执行命令的风险。

## 边界

- 不改变 owner gate 状态。
- 不生成 owner decision。
- 不执行 validate-forms 或 landing-plan。
- 不修改源项目 docs。
- 不自动写 registry、index、migration 或迁移正文。
- 不启用自动化。
- 不写 `~/.codex/memories`。

## Evidence Index

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
| --- | ---: | --- | --- | --- | --- |
| `rtk bash tools/knowledge-status.sh --json` | 0 | 通过；owner blocker 的 `commands` 不含 `<owner-decisions.jsonl>`，`command_templates` 包含 validate-forms 和 landing-plan 模板。 | `tools/knowledge-status.sh` | Tool | status-command-template-split |
| `rtk bash tools/knowledge-regression.sh --json` | 0 | 通过；`status-next-owner-gate` 回归覆盖 commands 与 command_templates 拆分。 | `tools/knowledge-regression.sh` | Tool | status-command-template-split |
| `rtk bash tools/knowledge-check.sh --dry-run --json --diagnostics` | 0 | 通过；0 errors、0 warnings，本 manifest、registry、migration 和索引登记一致。 | `tools/knowledge-check.sh` | Knowledge Hub | status-command-template-split |
| `rtk bash tools/knowledge-final-gate.sh --json` | expected 1 | 终态门禁仍返回 `needs-owner-review`，因为 7 条 owner gate 尚未由 owner 人工签收；blocker 同时展示 commands 与 command_templates。 | `tools/knowledge-final-gate.sh` | Knowledge Hub | status-command-template-split |

## Review

- owner：`leiwenjun`
- review_after：`2026-09-20`
- review_status：`status-command-template-split-applied`
- 下一次复核内容：若 status/final gate 后续动作字段被自动化消费，必须继续保持 commands 与 command_templates 的执行语义分离。
