# Knowledge Hub Index Duplicate Gate 2026-06-19

## 目标

补齐核心索引的重复引用门禁，防止人工维护 `indexes/by-owner.md`、`indexes/by-review-date.md` 和 `indexes/by-status.md` 时，同一个 registry item 被重复列入索引，导致复核队列、owner 责任或状态视图出现噪音。

## 问题地图

| ID | 问题 | 风险 | 处理 |
| --- | --- | --- | --- |
| IDUP-001 | 核心索引已检查 missing item，但不检查同一 item 重复出现。 | 人工复核时可能重复处理同一条目，降低索引可信度。 | `knowledge-check` 对 `by-owner`、`by-review-date` 的 registry item id 计数，发现重复即报错。 |
| IDUP-002 | `by-status` 下方包含状态说明和 artifact path，不能全文件做重复 item 检查。 | 误把说明段中的路径或补充说明当成规范状态索引。 | `by-status` 只检查 `active`、`reviewing`、`archived` 三个规范状态行中的 registry item id。 |
| IDUP-003 | range 写法可能和显式 id 混用。 | 同一 item 既在 range 中又被显式列出时，人工肉眼不容易发现。 | range 展开后参与计数，重复仍报错。 |

## 决策

- `indexes/by-owner.md` 中每个 registry item id 只能出现一次。
- `indexes/by-review-date.md` 中每个 registry item id 只能出现一次。
- `indexes/by-status.md` 仅在 `active`、`reviewing`、`archived` 三个规范状态行内检查重复。
- 状态说明段里的 artifact path 和非 item 引用不参与重复 item 检查。
- 不自动重排或生成索引，仍保持人工可维护。

## 非目标

- 不重写现有索引格式。
- 不引入索引生成器。
- 不改变 item owner、status、review_after 或 promotion。
- 不修改源项目 docs。
- 不启用自动化。
- 不写入 `~/.codex/memories`。

## 验证计划

- `rtk bash -n tools/knowledge-check.sh`
- `rtk jq -c . registry/items.jsonl`
- `rtk jq -c . artifacts/manifests/knowledge-hub-index-duplicate-gate-20260619.jsonl`
- `rtk jq -c . registry/items.jsonl`
- `rtk bash tools/knowledge-check.sh --dry-run --json`
- `/tmp` 负向验证：复制仓库后在 `indexes/by-owner.md` 重复一个 item id，`knowledge-check` 应报 duplicate item reference。
- `/tmp` 负向验证：复制仓库后在 `indexes/by-review-date.md` 重复一个 item id，`knowledge-check` 应报 duplicate item reference。
- `/tmp` 负向验证：复制仓库后在 `indexes/by-status.md` 规范状态行重复一个 item id，`knowledge-check` 应报 duplicate item reference。
- `rtk bash tools/knowledge-search.sh index-duplicate-gate-applied --json`

## 结果

- `rtk bash -n tools/knowledge-check.sh`: pass。
- `rtk jq -c . registry/items.jsonl`: pass。
- `rtk jq -c . artifacts/manifests/knowledge-hub-index-duplicate-gate-20260619.jsonl`: pass。
- `rtk jq -c . registry/items.jsonl`: pass。
- `rtk bash tools/knowledge-check.sh --dry-run --json`: pass，`errors=[]`，`warnings=[]`。
- `/tmp` by-owner duplicate 负向验证：重复 `knowledge-hub-root` 后，`knowledge-check` 报 `index:indexes/by-owner.md duplicate item reference knowledge-hub-root (2x)`。
- `/tmp` by-review-date duplicate 负向验证：重复 `knowledge-hub-root` 后，`knowledge-check` 报 `index:indexes/by-review-date.md duplicate item reference knowledge-hub-root (2x)`。
- `/tmp` by-status duplicate 负向验证：在 active 行重复 `knowledge-hub-root` 后，`knowledge-check` 报 `index:indexes/by-status.md duplicate item reference knowledge-hub-root (2x)`。
- `/tmp` by-status range duplicate 负向验证：在 range 后显式列出 `migrated-pcr02-docs-copyfirst-001` 后，`knowledge-check` 报 `index:indexes/by-status.md duplicate item reference migrated-pcr02-docs-copyfirst-001 (2x)`。
- `rtk bash tools/knowledge-search.sh index-duplicate-gate-applied --json`: count=3，可从 `registry/items.jsonl`、`indexes/by-status.md` 和本 manifest 找到。
