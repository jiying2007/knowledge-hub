# Knowledge Hub owner worksheet focus helper 2026-06-19

## 结论

`tools/knowledge-owner-gates.sh` 新增 `--worksheet-id <id>` 过滤参数，用于按单个 owner decision worksheet 聚焦输出 owner gate board、copyable form、form validation 和 landing plan 输入范围。

该参数只缩小只读输出范围，不写文件、不关闭 gate、不替 owner 做决策。

## 问题地图

| ID | 发现 | 风险 | 修复 |
|---|---|---|---|
| OWF-001 | owner gate 当前一次展示 7 条 worksheet | 人工 owner 每次处理单条时噪音偏高，容易漏看边界 | 新增 `--worksheet-id <id>` |
| OWF-002 | `--forms` 可输出完整骨架，但默认是全部 open rows | 人工复制时可能误带其他 row | 与 `--worksheet-id` 组合时只输出 1 条 form |
| OWF-003 | 回归入口未覆盖聚焦输出 | 后续改动可能破坏单条 owner workflow | `knowledge-regression.sh` 增加 `owner-single-form` 场景 |

## Evidence Index

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
|---|---:|---|---|---|---|
| `rtk bash tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --worksheet-id pcr02-owner-decision-worksheet-001 --forms --json` | 0 | 通过；`row_count=1`、`open_count=1`、`decision_forms=1`，只输出 AGENTS.md 对应 worksheet | `tools/knowledge-owner-gates.sh` | Tool | `knowledge-hub-owner-worksheet-focus-helper-20260619` |
| `rtk bash tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --json` | 0 | 通过；默认行为保持 7 open、0 resolved、0 active_exposure | `tools/knowledge-owner-gates.sh` | Tool | `knowledge-hub-owner-worksheet-focus-helper-20260619` |
| `rtk bash tools/knowledge-regression.sh --json` | 0 | 通过；5 个场景全部 pass，新增 `owner-single-form` 聚焦输出回归 | `tools/knowledge-regression.sh` | Tool | `knowledge-hub-owner-worksheet-focus-helper-20260619` |
| `rtk bash tools/knowledge-check.sh --dry-run --json --diagnostics` | 0 | 通过；0 errors、0 warnings | `tools/knowledge-check.sh` | Tool | `knowledge-hub-owner-worksheet-focus-helper-20260619` |

## 边界

- 不修改 PCR02 源项目 docs。
- 不关闭任何 PCR02 owner gate。
- 不生成 owner decision。
- 不启用自动化，不写 memory。
- 不提升 project-specific 内容到 `domains/embedded/standards/`。
