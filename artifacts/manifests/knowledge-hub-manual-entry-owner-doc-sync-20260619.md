# Knowledge Hub manual entry owner doc sync 2026-06-19

## 结论

`tools/knowledge-new.sh` 已支持 `--owner <owner>`、从 `--domain projects/<project>` 推导 project，并输出默认日期草稿。本次同步顶层 README 和 tools README，让人工新增入口显式展示 owner 参数，避免继续无意使用默认 owner。

## 变更范围

| 文件 | 变更 |
|---|---|
| `README.md` | 人工新增示例改为显式传入 `--owner <owner>`，并说明 owner 默认值、project 推导和默认日期语义 |
| `tools/README.md` | `knowledge-new.sh` 工具说明和示例补充 `--owner <owner>`、project 推导和默认日期 |
| `tools/knowledge-new.sh` | help 示例改为项目域显式传 `--owner team-core`，不再要求重复传 `--project pcr02` |
| `tools/knowledge-regression.sh` | 新增 `manual-entry-docs-owner-option` 场景，检查 README 与 tools README 均暴露 owner 参数 |
| `artifacts/manifests/knowledge-hub-governance-regression-helper-20260619.md` | 回归 helper 场景数从 12 更新为 13，并登记 owner 文档可发现性场景 |

## 决策

- 不新增自动写入能力。
- 不修改源项目 docs。
- 不关闭任何 PCR02 owner gate。
- 不把默认 owner 当成团队规范，只作为当前脚本默认值说明。
- 不写 `~/.codex/memories`。

## Evidence Index

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
|---|---:|---|---|---|---|
| `rtk bash tools/knowledge-regression.sh --json` | 0 | 通过；18 个回归场景全部 pass，覆盖人工新增 owner 文档和 help 可发现性 | `tools/knowledge-regression.sh` | Tool | `knowledge-hub-manual-entry-owner-doc-sync-20260619` |
| `rtk bash tools/knowledge-check.sh --dry-run --json --diagnostics` | 0 | 通过；0 errors、0 warnings，确认全仓知识门禁无漂移 | `tools/knowledge-check.sh` | Tool | `knowledge-hub-manual-entry-owner-doc-sync-20260619` |
| `rtk bash tools/knowledge-check.sh --dry-run --json --explain knowledge-hub-manual-entry-owner-doc-sync-20260619` | 0 | 通过；新增 audit item 的 registry、正文和核心索引引用均可解释 | `tools/knowledge-check.sh` | Tool | `knowledge-hub-manual-entry-owner-doc-sync-20260619` |

## 边界

- 本次只同步文档可发现性和回归保护，不改变 `knowledge-new.sh` 行为。
- 人工仍需按 `knowledge-new.sh` 输出手动复制模板、登记 registry、更新索引和迁移记录。
- 自动化仍保持 read-only/report-only。
