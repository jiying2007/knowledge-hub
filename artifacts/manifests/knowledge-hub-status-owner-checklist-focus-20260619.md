# Knowledge Hub status owner checklist focus 2026-06-19

## 结论

`tools/knowledge-status.sh` 的下一条 owner gate 聚焦命令已从只输出 `--forms` 升级为 `--checklist --forms`。当前推荐入口是 `owner_gates.next_open.next_open_command`，它通过 `--next-open --checklist --forms` 自动选择下一条 open gate；兼容 `focus_command` 仍保留具体 worksheet id。

## 变更范围

| 文件 | 变更 |
|---|---|
| `tools/knowledge-status.sh` | `owner_gates.next_open.next_open_command` 使用 `--next-open --checklist --forms`，兼容 `focus_command` 保持 `--worksheet-id ... --checklist --forms` |
| `tools/knowledge-regression.sh` | `status-next-owner-gate` 回归断言要求推荐命令和兼容命令都包含 checklist/forms 上下文 |
| `artifacts/manifests/knowledge-hub-status-next-owner-gate-20260619.md` | 同步聚焦命令和 Evidence 摘要 |
| `artifacts/manifests/knowledge-hub-governance-regression-helper-20260619.md` | 同步 `status-next-owner-gate` 场景预期 |

## 决策

- 仍然只读，不生成 owner decision。
- 不改变 `knowledge-status.sh --strict` 的终态判定；7 条 PCR02 owner gate 未闭环时仍返回 `needs-owner-review`。
- 不修改 PCR02 源项目 docs，不关闭 owner gate，不启用自动化，不写 memory。

## Evidence Index

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
|---|---:|---|---|---|---|
| `rtk bash tools/knowledge-status.sh --json` | 0 | 通过；`owner_gates.next_open.next_open_command` 包含 `--next-open --checklist --forms`，兼容 `focus_command` 包含 `--checklist --forms` | `tools/knowledge-status.sh` | Tool | `knowledge-hub-status-owner-checklist-focus-20260619` |
| `rtk bash tools/knowledge-regression.sh --json` | 0 | 通过；19 个回归场景全部 pass，`status-next-owner-gate` 覆盖 checklist/forms 聚焦命令 | `tools/knowledge-regression.sh` | Tool | `knowledge-hub-status-owner-checklist-focus-20260619` |
| `rtk bash tools/knowledge-check.sh --dry-run --json --diagnostics` | 0 | 通过；0 errors、0 warnings，全仓知识门禁无漂移 | `tools/knowledge-check.sh` | Tool | `knowledge-hub-status-owner-checklist-focus-20260619` |

## 边界

- 本轮只调整人工下一步提示，不处理 owner 决策。
- checklist/form 输出仍由 `tools/knowledge-owner-gates.sh` 只读生成。
- strict 终态仍依赖 owner 真实签收和后续人工落地。
