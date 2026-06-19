# Knowledge Hub owner next-open helper 2026-06-19

## 结论

`tools/knowledge-owner-gates.sh` 已新增 `--next-open`，用于按 `review_after, worksheet_id` 自动聚焦下一条 open owner gate。人工或 AI 不再需要从 status JSON 中复制具体 `worksheet_id`，可以直接运行 `--next-open --checklist --forms` 获取下一条 gate 的中文清单和可填写 form。

## 问题地图

| ID | 问题 | 风险 | 处理 |
|---|---|---|---|
| NOH-001 | 下一条 owner gate 过去依赖 `knowledge-status.sh` 拼出具体 `--worksheet-id`。 | 长期维护时人工需要复制 id，容易复制错、漏 `--checklist` 或漏 `--forms`。 | 新增 `--next-open`，在 owner gate helper 内部统一排序和聚焦。 |
| NOH-002 | status action 只有具体 worksheet 命令。 | owner gate 顺序变化后，旧命令可能不再代表“下一条”。 | `knowledge-status.sh` 继续保留兼容 `focus_command`，同时新增 `next_open_command` 并在 `next_actions_zh` 中使用。 |
| NOH-003 | 新入口如果没有回归，后续可能被删除或排序漂移。 | AI/人工续跑路径再次变成手工解析 JSON。 | 新增 `owner-next-open-focus` 回归场景。 |

## 决策

- `--next-open` 只读，只筛选输出，不写文件、不关闭 gate、不生成 owner decision。
- 排序规则沿用 status dashboard：`review_after, worksheet_id`。
- `--next-open` 不能和 `--worksheet-id` 同时使用，避免语义冲突。
- `knowledge-status.sh` 保留 `focus_command` 兼容字段，新增 `next_open_command` 作为推荐续跑命令。

## Evidence Index

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
|---|---:|---|---|---|---|
| `rtk bash tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --next-open --checklist --forms --json` | 0 | 通过；只输出 1 条 next open owner gate，包含 checklist 和 decision form | `tools/knowledge-owner-gates.sh` | Tool | `knowledge-hub-owner-next-open-helper-20260619` |
| `rtk bash tools/knowledge-status.sh --json` | 0 | 通过；`owner_gates.next_open.next_open_command` 和 `next_actions_zh` 使用 `--next-open --checklist --forms` | `tools/knowledge-status.sh` | Tool | `knowledge-hub-owner-next-open-helper-20260619` |
| `rtk bash tools/knowledge-regression.sh --json` | 0 | 通过；20 个回归场景全部 pass，包含 `owner-next-open-focus` | `tools/knowledge-regression.sh` | Tool | `knowledge-hub-owner-next-open-helper-20260619` |
| `rtk bash tools/knowledge-check.sh --dry-run --json --diagnostics` | 0 | 通过；0 errors、0 warnings，确认新增 manifest、registry 和 index 登记无漂移 | `tools/knowledge-check.sh` | Tool | `knowledge-hub-owner-next-open-helper-20260619` |

## 边界

- 不修改 PCR02 源项目 docs。
- 不关闭任何 PCR02 owner gate。
- 不生成 owner decision。
- 不启用自动化，不写 memory。
- 不把 PCR02 project-specific 内容提升到 `domains/embedded/standards`。
