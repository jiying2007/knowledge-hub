# Knowledge Hub status owner summary command 2026-06-20

## 结论

`tools/knowledge-status.sh` 已在 owner gate 未闭环时输出 owner gate 总览命令。状态看板现在同时给出两类入口：

- `summary_commands`：先看全部 open owner gate，便于分派和排期。
- `next_open.next_open_command`：继续处理下一条 open owner gate。

该变更只读，不生成 owner decision，不关闭 owner gate，不修改源项目 docs。

## 问题地图

| ID | 问题 | 风险 | 处理 |
|---|---|---|---|
| SOS-001 | `knowledge-status.sh` 只暴露下一条 owner gate，未暴露全部 open gate 总览。 | 人工或 AI 从 status 看板进入时容易只逐条处理，难以判断 owner 分派和总体收口成本。 | 增加 `owner_gates.summary_commands`，指向 `knowledge-owner-gates.sh --summary`。 |
| SOS-002 | `next_actions_zh` 只提示下一条命令。 | 终态治理时缺少“先看全局再处理下一条”的可执行路径。 | 在 `next_actions_zh` 中先提示 summary command，再提示 next-open command。 |
| SOS-003 | 状态看板命令漂移如果没有回归，后续容易被删。 | owner gate 入口再次变成隐式知识。 | 扩展 `status-next-owner-gate` 回归，要求 JSON 和 next actions 同时包含 `--summary`。 |

## Evidence Index

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
|---|---:|---|---|---|---|
| `rtk bash tools/knowledge-status.sh --json` | 0 | 通过；`owner_gates.summary_commands` 包含 `--summary`，`next_actions_zh` 同时提示 summary 和 next-open | `tools/knowledge-status.sh` | Tool | `knowledge-hub-status-owner-summary-command-20260620` |
| `rtk bash tools/knowledge-regression.sh --json` | 0 | 通过；20 个回归场景全部 pass，`status-next-owner-gate` 覆盖 summary command 和 next-open command | `tools/knowledge-regression.sh` | Tool | `knowledge-hub-status-owner-summary-command-20260620` |
| `rtk bash tools/knowledge-check.sh --dry-run --json --diagnostics` | 0 | 通过；0 errors、0 warnings，确认新增 manifest、registry 和 index 登记无漂移 | `tools/knowledge-check.sh` | Tool | `knowledge-hub-status-owner-summary-command-20260620` |

## 边界

- 不修改 PCR02 源项目 docs。
- 不关闭 owner gate，不生成 owner decision。
- 不把 PCR02 project-specific 内容提升到 `domains/embedded/standards/`。
- 不启用自动化，不写 `~/.codex/memories`。
- 不替代 owner review、`knowledge-check` 或 `knowledge-status --strict`。
