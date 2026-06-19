# Knowledge Hub status next action command 2026-06-19

## 结论

`tools/knowledge-status.sh` 的 `next_actions_zh` 已直接包含 owner gate 总览命令和下一条 owner gate 的可执行聚焦命令。总览命令来自 `owner_gates.summary_commands`，下一条命令来自 `owner_gates.next_open.next_open_command`，这样 AI 或人工只读取 `next_actions_zh` 也能先看全局、再继续处理 owner gate，不需要复制具体 worksheet id。

## 变更范围

| 文件 | 变更 |
|---|---|
| `tools/knowledge-status.sh` | `next_actions_zh` 中加入 owner gate 的 `summary_commands` 和下一条 owner gate 的 `next_open_command` |
| `tools/knowledge-regression.sh` | `status-next-owner-gate` 回归断言要求 `next_actions_zh` 同时包含 `--summary` 和 `--next-open --checklist --forms` |
| `artifacts/manifests/knowledge-hub-governance-regression-helper-20260619.md` | 同步 `status-next-owner-gate` 场景预期 |

## 决策

- 只增强只读状态提示，不改变 strict gate 判定。
- 不生成 owner decision，不关闭 owner gate，不改 registry/index 的 owner gate 语义。
- 不修改 PCR02 源项目 docs，不启用自动化，不写 memory。

## Evidence Index

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
|---|---:|---|---|---|---|
| `rtk bash tools/knowledge-status.sh --json` | 0 | 通过；`next_actions_zh` 包含全部 owner gate 的 `--summary` 总览命令和下一条 owner gate 的 `--next-open --checklist --forms` 聚焦命令 | `tools/knowledge-status.sh` | Tool | `knowledge-hub-status-next-action-command-20260619` |
| `rtk bash tools/knowledge-regression.sh --json` | 0 | 通过；19 个回归场景全部 pass，`status-next-owner-gate` 覆盖 next action 命令 | `tools/knowledge-regression.sh` | Tool | `knowledge-hub-status-next-action-command-20260619` |
| `rtk bash tools/knowledge-check.sh --dry-run --json --diagnostics` | 0 | 通过；0 errors、0 warnings，全仓知识门禁无漂移 | `tools/knowledge-check.sh` | Tool | `knowledge-hub-status-next-action-command-20260619` |

## 边界

- `next_actions_zh` 是提示，不是审批。
- owner gate 仍需真实 owner 决策、证据、review cycle 和后续人工落地。
- `knowledge-status.sh --strict` 在 7 条 PCR02 owner gate open 时仍应返回 `needs-owner-review`。
