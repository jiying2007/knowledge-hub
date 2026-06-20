# Knowledge Hub status final gate command 2026-06-20

## 结论

本轮在 `knowledge-status.sh` 中增加 `final_gate_command`，让恢复会话、人工维护者和自动化调用方能从 status JSON 直接找到最终验收入口。

`knowledge-status.sh` 仍是只读状态看板和 blocker dashboard；最终验收仍以 `knowledge-final-gate.sh --json` 为准，因为 final gate 会同时聚合 `knowledge-check`、`knowledge-regression` 和 `knowledge-status --strict`。

## Issue Map

| ID | Finding | Severity | Evidence | Action | Status |
|---|---|---|---|---|---|
| SFGC-001 | status JSON 能说明 `needs-owner-review` 和 owner 下一步，但没有明确 terminal final gate 命令 | P2 | `tools/knowledge-status.sh --strict --json` | 增加 `final_gate_command` | applied |
| SFGC-002 | `next_actions_zh` 只引导 owner 表单处理，未显式提醒需要 final gate 判断是否只剩 owner blocker | P2 | `docs/goals/knowledge-hub-final-state.md` 状态可恢复要求 | 增加最终门禁 next action | applied |
| SFGC-003 | 文档可能让维护者把 status strict 当最终门禁 | P2 | `README.md`、`tools/README.md` | 明确 status 是 dashboard，final gate 是 terminal gate | applied |
| SFGC-004 | 回归未固定 status 到 final gate 的恢复链接 | P2 | `tools/knowledge-regression.sh` | 增加 `final_gate_command` 和 next action 断言 | applied |

## 边界

- 不改变 `knowledge-status.sh --strict` 退出码语义。
- 不让 status 执行 regression 或 final gate。
- 不生成 owner decision，不关闭 owner gate。
- 不修改 PCR02 源项目 docs。
- 不启用自动化写操作，不写 `~/.codex/memories`。

## Evidence Index

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
|---|---:|---|---|---|---|
| `rtk bash tools/knowledge-status.sh --strict --json` | 1 | 预期停在 `needs-owner-review`；JSON 输出 `final_gate_command=rtk bash tools/knowledge-final-gate.sh --json`，`next_actions_zh` 包含最终门禁提示 | `tools/knowledge-status.sh` | Status | `knowledge-hub-status-final-gate-command-20260620` |
| `rtk bash tools/knowledge-check.sh --dry-run --json --diagnostics` | 0 | 全仓知识库检查通过，0 errors / 0 warnings | `tools/knowledge-check.sh` | Knowledge Hub | `knowledge-hub-status-final-gate-command-20260620` |
| `rtk bash tools/knowledge-regression.sh --json` | 0 | 33 个回归场景通过，包含 status/final gate 恢复链接断言 | `tools/knowledge-regression.sh` | Regression | `knowledge-hub-status-final-gate-command-20260620` |
| `rtk bash tools/knowledge-check.sh --dry-run --json --explain knowledge-hub-status-final-gate-command-20260620` | 0 | 新审计工件 registry 与核心索引引用正常 | `tools/knowledge-check.sh` | Registry/index | `knowledge-hub-status-final-gate-command-20260620` |
| `rtk bash tools/knowledge-final-gate.sh --json` | 1 | 预期停在 `needs-owner-review`；Level 1/2/3 为 `complete-except-owner-review` / `complete` / `complete`，唯一 gap 为 `owner-gates-open` | `tools/knowledge-final-gate.sh` | Final gate | `knowledge-hub-status-final-gate-command-20260620` |

## Review

- owner：`leiwenjun`
- review_after：`2026-09-20`
- review_status：`status-final-gate-command-applied`
- 下一步：继续保持 `knowledge-final-gate.sh --json` 为终态验收入口；status 只负责恢复、分派和 blocker 提示。
