# Knowledge Hub status owner forms JSONL command（2026-06-20）

## 结论

`tools/knowledge-status.sh` 的 owner gate 控制面现在直接暴露纯 JSONL 表单命令：

- `owner_gates.forms_jsonl_commands`：按 source 输出全部 open owner gate 的纯 JSONL skeleton。
- `owner_gates.next_open.next_open_forms_jsonl_command`：按 `review_after, worksheet_id` 聚焦下一条 open owner gate 的纯 JSONL skeleton。
- `owner_gates.next_open.focus_forms_jsonl_command`：兼容具体 worksheet id 的纯 JSONL skeleton 命令。
- `strict_blockers[].commands` 和 `next_actions_zh` 会在 owner gate 未签收时包含下一条 `--forms-jsonl` 命令。

这个变更只让终态阻塞的下一步更可执行，不生成 owner decision，不关闭 gate。

## 边界

- 不生成 owner decision。
- 不关闭 owner gate。
- 不自动填 `owner_decision`、`source_sha256` 或 `source_size`。
- 不修改源项目 docs。
- 不迁移 owner-gated source 正文。
- 不把 PCR02 project-specific 内容提升到 `domains/embedded/standards/`。
- 不启用自动化。
- 不写 `~/.codex/memories`。

## Evidence Index

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
| --- | ---: | --- | --- | --- | --- |
| `rtk bash tools/knowledge-status.sh --json` | 0 | 通过；`owner_gates.forms_jsonl_commands`、`next_open.next_open_forms_jsonl_command` 和 `focus_forms_jsonl_command` 均存在。 | `tools/knowledge-status.sh` | Tool | status-owner-forms-jsonl-command |
| `rtk bash tools/knowledge-regression.sh --json` | 0 | 通过；`status-next-owner-gate` 回归覆盖 status JSONL 命令字段和 strict blocker 命令。 | `tools/knowledge-regression.sh` | Tool | status-owner-forms-jsonl-command |
| `rtk bash tools/knowledge-check.sh --dry-run --json --diagnostics` | 0 | 通过；0 errors、0 warnings，本 manifest、registry、migration 和索引登记一致。 | `tools/knowledge-check.sh` | Knowledge Hub | status-owner-forms-jsonl-command |
| `rtk bash tools/knowledge-final-gate.sh --json` | expected 1 | 终态门禁仍返回 `needs-owner-review`，因为 7 条 owner gate 尚未由 owner 人工签收；blocker commands 包含 `--forms-jsonl`。 | `tools/knowledge-final-gate.sh` | Knowledge Hub | status-owner-forms-jsonl-command |

## Review

- owner：`leiwenjun`
- review_after：`2026-09-20`
- review_status：`status-owner-forms-jsonl-command-applied`
- 下一次复核内容：若 owner status dashboard 的命令字段或 owner 表单导出契约变化，需同步更新 README、tools README、回归和本 manifest。
