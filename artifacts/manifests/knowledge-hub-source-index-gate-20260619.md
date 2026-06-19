# Knowledge Hub Source Index Gate 2026-06-19

## 目标

让 `indexes/by-source.md` 与 `registry/sources.json` 保持可执行一致，避免来源控制面新增、改名或退役后，人工导航入口仍漏源或残留旧源。

## 问题地图

| ID | 问题 | 风险 | 处理 |
| --- | --- | --- | --- |
| SIG-001 | `registry/sources.json` 是来源 registry，但 `indexes/by-source.md` 目前没有覆盖门禁。 | 新增 source 后可能忘记更新导航入口。 | 增加 source id coverage 检查。 |
| SIG-002 | `indexes/by-source.md` 主表可能残留已删除或改名 source。 | 人工会继续从旧路径或旧权威入口查资料。 | 增加 stale source 检查。 |
| SIG-003 | source review artifacts 段落包含非 source id 的说明项。 | 简单扫描全文会误判。 | 只解析主表三列表格的第一列 source id。 |

## 决策

- `registry/sources.json` source id 必须唯一。
- `indexes/by-source.md` 主表必须覆盖所有 source id。
- `indexes/by-source.md` 主表不得包含未登记 source id。
- 不检查 Source-Specific Review Artifacts 段落的项目级说明项。

## 非目标

- 不自动生成 `indexes/by-source.md`。
- 不检查外部 source path 是否在 by-source 中逐字相等；路径可读性由人工维护。
- 不修改外部源 docs。
- 不启用自动化。
- 不写入 `~/.codex/memories`。

## 验证计划

- `rtk bash -n tools/knowledge-check.sh`
- `rtk jq -c . registry/sources.json`
- `rtk jq -c . artifacts/manifests/knowledge-hub-source-index-gate-20260619.jsonl`
- `rtk jq -c . registry/items.jsonl`
- `rtk jq -c . registry/migrations.jsonl`
- `rtk bash tools/knowledge-check.sh --dry-run --json`
- `rtk bash tools/knowledge-check.sh --sources-only --dry-run --json`
- `/tmp` 负向验证：复制仓库后从 `indexes/by-source.md` 主表删除一个 source 行，`knowledge-check` 应报 missing source。
- `/tmp` 负向验证：复制仓库后向 `indexes/by-source.md` 主表添加未登记 source 行，`knowledge-check` 应报 stale source。
- `rtk bash tools/knowledge-search.sh "source-index-gate-applied" --json`

## 结果

- `rtk bash -n tools/knowledge-check.sh`: pass。
- `rtk jq -c . registry/sources.json`: pass。
- `rtk jq -c . artifacts/manifests/knowledge-hub-source-index-gate-20260619.jsonl`: pass。
- `rtk jq -c . registry/items.jsonl`: pass。
- `rtk jq -c . registry/migrations.jsonl`: pass。
- `rtk bash tools/knowledge-check.sh --dry-run --json`: pass，`errors=[]`，`warnings=[]`。
- `rtk bash tools/knowledge-check.sh --sources-only --dry-run --json`: pass，`errors=[]`，`warnings=[]`。
- `/tmp` missing-source 负向验证：从主表删除 `codex-memories` 后，`knowledge-check` 报 `index:indexes/by-source.md missing source codex-memories`。
- `/tmp` stale-source 负向验证：向主表添加 `ghost-source` 后，`knowledge-check` 报 `index:indexes/by-source.md stale source ghost-source`。
- `/tmp` extra-review-table 回归验证：在 review artifact 段落后追加非 source 表格，`knowledge-check` 仍 pass，确认只解析 `# Knowledge Sources` 下的主 source 表。
- `rtk bash tools/knowledge-search.sh "source-index-gate-applied" --json`: count=3，可从 `registry/items.jsonl`、`indexes/by-status.md` 和本 manifest 找到。

## 子代理复核

- SIG-REVIEW-001 发现首版实现会扫描整份 `indexes/by-source.md` 的 Markdown 表格，和“只解析主表”目标不一致；已修复为只读取 `# Knowledge Sources` 下第一个表格，并通过 extra-review-table 回归验证。
- SIG-REVIEW-002 确认 `registry/items.jsonl`、`registry/migrations.jsonl`、owner/status/review/topic 索引链路完整；`indexes/by-source.md` 保持 source-id-only，不登记 gate 自身。
