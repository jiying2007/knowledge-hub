# Knowledge Hub index/source maintenance tools 2026-06-20

## 结论

本轮把索引维护和 source 新增入口从“文档提示”压实为可执行、可回归、可登记的人工维护控制面：

- `tools/knowledge-index-plan.sh` 增加 `project`、`source`、`topic`、`decision` 四类 section，并派生 `by_project`、`by_source`、`by_topic`、`by_decision` 视图。
- `tools/knowledge-new.sh --source` 输出 source 登记草案，覆盖 `registry/sources.json`、`indexes/by-source.md` 和 source coverage JSONL row。
- `README.md` 与 `tools/README.md` 增加新会话恢复、搜索、source 新增和 index planner 示例。
- `registry/schema.md` 增加 source check、no-check reason、coverage row 与 directory identity 约定。
- `tools/knowledge-regression.sh` 增加 2 个回归场景，回归 helper manifest 从 31 个场景更新为 33 个场景。

这只是维护入口增强，不生成 owner decision，不关闭 PCR02 7 个 owner gate，不修改 PCR02 源项目 docs，不启用自动化写操作，也不写 memory。

## 问题地图

| ID | Finding | Severity | Evidence | Action |
|---|---|---:|---|---|
| GAP-INDEX-PLAN-EXTENDED | 原 index planner 只覆盖 owner/review-date/status，核心索引 `by-project/by-source/by-topic/by-decision` 缺少只读规划入口 | P1 | `tools/knowledge-index-plan.sh` | 增加 project/source/topic/decision section，并输出派生视图 |
| GAP-SOURCE-MANUAL-GUIDE | 新增 source 的人工路径可读但仍偏手工，容易漏掉 source coverage JSONL 或 no-check reason | P1 | `tools/knowledge-new.sh`、`registry/schema.md` | 增加 `--source` 向导，输出 registry、by-source、coverage 草案 |
| GAP-RECOVERY-SEARCH-DOCS | 新会话恢复和搜索入口分散，长期维护时不够直接 | P2 | `README.md`、`tools/README.md` | 增加恢复命令、搜索命令和 index planner 示例 |
| GAP-REGRESSION-COVERAGE | 新维护入口缺少回归，后续容易退化 | P1 | `tools/knowledge-regression.sh` | 增加 `index-plan-extended-sections` 和 `source-manual-entry-guide` |

## 变更范围

| 文件 | 类型 | 说明 |
|---|---|---|
| `tools/knowledge-index-plan.sh` | 工具 | 只读扩展；读取 registry/source/project/topic/decision/migration/worksheet 资料后输出索引规划 |
| `tools/knowledge-new.sh` | 工具 | 只读扩展；新增 `--source` 模式和 compact coverage id |
| `tools/knowledge-regression.sh` | 回归 | 增加 index planner extended sections 和 source manual entry guide 两个场景 |
| `README.md` | 文档 | 增加新会话恢复、搜索和 source 新增路径 |
| `tools/README.md` | 文档 | 增加工具索引、source 新增和恢复/搜索示例 |
| `registry/schema.md` | Schema 文档 | 增加 source coverage/no-check/source identity 约定 |
| `artifacts/manifests/knowledge-hub-governance-regression-helper-20260619.md` | manifest | 回归 helper 覆盖数更新到 33 个场景 |

## 验收标准

- `knowledge-index-plan.sh --section source --json` 和 `--section decision --json` 输出 `status=planned`、`read_only=true`、`errors=[]`。
- `knowledge-new.sh --source ...` 输出 source registry object、by-source 主表行、source coverage JSONL row 和 no-check reason。
- `knowledge-regression.sh --json` 通过，并包含 33 个场景。
- `knowledge-check.sh --dry-run --json --diagnostics` 通过。
- `knowledge-final-gate.sh --json` 只因 7 个 PCR02 owner gate 仍 open 返回 `needs-owner-review`。

## Evidence Index

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
|---|---:|---|---|---|---|
| `rtk bash tools/knowledge-index-plan.sh --section source --json` | 0 | 通过；只读输出 source 索引派生视图，包含 `pcr02-project-docs` 和 source coverage rows | `tools/knowledge-index-plan.sh` | Tool | `knowledge-hub-index-source-maintenance-tools-20260620` |
| `rtk bash tools/knowledge-index-plan.sh --section decision --json` | 0 | 通过；只读输出 registry decisions、owner worksheets 和 source-policy decisions；owner worksheets 标记 no owner decision generated | `tools/knowledge-index-plan.sh` | Tool | `knowledge-hub-index-source-maintenance-tools-20260620` |
| `rtk bash tools/knowledge-new.sh --source --source-id example-source --source-path /tmp/example --role project-current-docs-source --authority legacy-project-current-docs --write-policy read-only-unless-explicitly-approved --no-check-reason "classify-first pending source coverage"` | 0 | 通过；输出 source registry object、by-source 主表行和 source coverage JSONL row 草案 | `tools/knowledge-new.sh` | Tool | `knowledge-hub-index-source-maintenance-tools-20260620` |
| `rtk bash tools/knowledge-regression.sh --json` | 0 | 通过；33 个回归场景全部 pass，新增 index planner extended sections 和 source manual entry guide 覆盖 | `tools/knowledge-regression.sh` | Tool | `knowledge-hub-index-source-maintenance-tools-20260620` |
| `rtk bash tools/knowledge-check.sh --dry-run --json --diagnostics` | 0 | 通过；0 errors、0 warnings | `tools/knowledge-check.sh` | Tool | `knowledge-hub-index-source-maintenance-tools-20260620` |
| `rtk bash tools/knowledge-final-gate.sh --json` | 1 | 预期阻塞；`final_status=needs-owner-review`，唯一 blocker 为 7 个 open owner gate | `tools/knowledge-final-gate.sh` | Gate | `knowledge-hub-index-source-maintenance-tools-20260620` |

## 边界

- 不修改 PCR02 源项目 docs。
- 不复制 source 正文，不提升 project-specific 内容到 `domains/embedded/standards/`。
- 不生成 owner decision，不关闭 owner gate。
- 不启用自动化写操作，不写 `~/.codex/memories`。
- `knowledge-index-plan.sh --section <name> --json` 仍返回完整派生索引对象；`--section` 决定 Markdown 输出重点与 smoke 入口，不构成 JSON 局部裁剪契约。
