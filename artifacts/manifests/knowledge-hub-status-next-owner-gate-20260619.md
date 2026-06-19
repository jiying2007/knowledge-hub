# Knowledge Hub status next owner gate 2026-06-19

## 结论

`tools/knowledge-status.sh` 现在会在 owner gate 未闭环时直接输出下一条可处理的 owner decision worksheet，并在 JSON 中提供可复制的聚焦命令。

这个能力只负责把“下一步该看哪一条”显式化，不关闭 owner gate，不生成 owner decision，不修改源项目 docs，也不启用任何自动化。

## 变更范围

| 文件 | 变更 |
|---|---|
| `tools/knowledge-status.sh` | 在 `owner_gates.next_open` 中输出下一条 open worksheet 的 `worksheet_id`、`source_id`、`source_path`、`owner`、`review_after`、`selection_order` 和 `focus_command`。 |
| `tools/knowledge-regression.sh` | 增加 `status-next-owner-gate` 回归场景，固定校验当前下一条 owner gate 聚焦命令。 |
| `README.md` | 在人工维护最短路径中提示可先读取 `owner_gates.next_open.focus_command`。 |
| `tools/README.md` | 更新 `knowledge-status.sh` 描述，明确它会提示下一条 open owner gate。 |

## 当前下一条 owner gate

| 字段 | 值 |
|---|---|
| worksheet_id | `pcr02-owner-decision-worksheet-001` |
| source_id | `pcr02-project-docs` |
| source_path | `AGENTS.md` |
| owner | `team-core-or-pcr02-docs-owner` |
| review_after | `2026-09-17` |

聚焦命令：

```bash
rtk bash tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --worksheet-id pcr02-owner-decision-worksheet-001 --forms
```

## 决策

- 保持 `knowledge-status.sh` 默认只读，`--strict` 仍然只按最终状态是否为 `ok` 决定退出码。
- `needs-owner-review` 仍表示语义 owner 决策未闭环，不是工具失败。
- 按 `review_after, worksheet_id` 稳定排序后选择下一条 open worksheet，降低人工入口复杂度。
- 聚焦命令使用 shell-safe quoting 生成，保持可复制且避免未来 ID 格式变化带来的命令拼接风险。
- 不自动生成 owner decision，不自动改 registry/index，不自动提升 active。

## Evidence Index

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
|---|---:|---|---|---|---|
| `rtk bash tools/knowledge-status.sh --json` | 0 | 通过；JSON 中 `owner_gates.next_open.worksheet_id` 为 `pcr02-owner-decision-worksheet-001`，并包含 `focus_command` | `tools/knowledge-status.sh` | Tool | `knowledge-hub-status-next-owner-gate-20260619` |
| `rtk bash tools/knowledge-status.sh` | 0 | 通过；文本看板输出 `next open` 和 `focus command` | `tools/knowledge-status.sh` | Tool | `knowledge-hub-status-next-owner-gate-20260619` |
| `rtk bash tools/knowledge-regression.sh --json` | 0 | 通过；6 个回归场景全部 pass，包含新增 `status-next-owner-gate` 场景 | `tools/knowledge-regression.sh` | Tool | `knowledge-hub-status-next-owner-gate-20260619` |
| `rtk bash tools/knowledge-check.sh --dry-run --json --diagnostics` | 0 | 通过；0 errors、0 warnings，确认新增 manifest、registry 和 index 登记无漂移 | `tools/knowledge-check.sh` | Tool | `knowledge-hub-status-next-owner-gate-20260619` |

## 边界

- 不修改 PCR02 源项目 docs。
- 不关闭任何 PCR02 owner gate。
- 不生成 owner decision。
- 不把 PCR02 project-specific 内容提升到 `domains/embedded/standards/`。
- 不启用自动化，不写 memory。
- 严格终态仍依赖 7 条 owner gate 的人工决策。
