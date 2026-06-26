# Knowledge Hub owner checklist helper 2026-06-19

## 结论

新增 `tools/knowledge-owner-gates.sh --checklist` 作为只读 owner 收口清单。它把 owner decision worksheet 与 PCR02 owner intake package 的中文问题、默认状态、硬门禁和必填字段合并到同一输出，降低人工 owner 填表前的来回查找成本。

## 变更范围

| 文件 | 变更 |
|---|---|
| `tools/knowledge-owner-gates.sh` | 新增 `--checklist`，JSON 输出增加 `owner_checklists`，文本输出增加 owner closure checklist |
| `tools/knowledge-regression.sh` | 新增 `owner-checklist-context` 回归场景，确认 checklist 合并 intake 中文问题、硬门禁和 worksheet 必填字段 |
| `README.md` | 常用命令和人工新增路径补充 `--checklist` |
| `tools/README.md` | owner gate helper 说明和示例补充 `--checklist` |
| `artifacts/manifests/knowledge-hub-governance-regression-helper-20260619.md` | 回归 helper 场景数从 13 更新为 14 |

## 决策

- `--checklist` 只读，不生成 owner decision，不写 registry/index/source-policy。
- checklist 只汇总已有 intake/worksheet 信息，不新增事实、不替代 owner sign-off。
- 未找到 intake package 时，worksheet board 仍可工作；对应 checklist 字段为空，由人工继续使用 worksheet 原始字段。
- 不修改 PCR02 源项目 docs，不关闭 owner gate，不启用自动化，不写 memory。

## Evidence Index

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
|---|---:|---|---|---|---|
| `rtk bash tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --worksheet-id pcr02-owner-decision-worksheet-001 --checklist --json` | 0 | 通过；输出 1 条 owner checklist，包含中文 owner question、`门禁待补证` 和 `owner_decision` 必填字段 | `tools/knowledge-owner-gates.sh` | Tool | `knowledge-hub-owner-checklist-helper-20260619` |
| `rtk bash tools/knowledge-regression.sh --json` | 0 | 通过；20 个回归场景全部 pass，包含 `owner-checklist-context` | `tools/knowledge-regression.sh` | Tool | `knowledge-hub-owner-checklist-helper-20260619` |
| `rtk bash tools/knowledge-check.sh --dry-run --json --diagnostics` | 0 | 通过；0 errors、0 warnings，全仓知识门禁无漂移 | `tools/knowledge-check.sh` | Tool | `knowledge-hub-owner-checklist-helper-20260619` |
| `rtk bash tools/knowledge-check.sh --dry-run --json --diagnostics` | 1 expected | 负结果；`indexes/by-status.md` 中 command-shaped code span 被识别为 missing local path reference，已拆成路径和参数后恢复通过 | `indexes/by-status.md` | Negative fixture | `knowledge-hub-owner-checklist-helper-20260619` |

## 边界

- 本轮不处理 owner 决策语义，不选择 `owner_decision`。
- 本轮不修改源项目 docs。
- 本轮不把 PCR02 project-specific 内容提升到 `domains/embedded/standards/`。
- 本轮不写 `~/.codex/memories`。
