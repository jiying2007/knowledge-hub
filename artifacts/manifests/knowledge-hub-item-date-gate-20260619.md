# Knowledge Hub Item Date Gate 2026-06-19

## 目标

让 `registry/items.jsonl` 的 `created_at`、`updated_at` 和 `review_after` 成为可靠的维护字段，避免人工新增或修订条目时写入不可排序日期、错误复核日期或早于创建时间的更新时间。

## 问题地图

| ID | 问题 | 风险 | 处理 |
| --- | --- | --- | --- |
| IDG-001 | `created_at` 和 `updated_at` 是长期追溯字段，但此前没有统一 ISO 日期门禁。 | 排序、审计和人工复核时出现不可解析日期。 | `knowledge-check` 对 `created_at`、`updated_at`、`review_after` 执行 `YYYY-MM-DD` 解析。 |
| IDG-002 | `updated_at` 可能被人工写成早于 `created_at`。 | 后续判断条目是否被维护过时出现反向时间线。 | `knowledge-check` 要求 `updated_at >= created_at`。 |
| IDG-003 | `review_after` 已参与 `by-review-date` 索引和过期提醒。 | 日期格式漂移会破坏复核排期。 | 保持 stale warning 行为，同时把日期格式解析提升为通用 item 门禁。 |

## 决策

- `registry/items.jsonl` 中每个 item 的 `created_at`、`updated_at`、`review_after` 必须是 ISO 日期：`YYYY-MM-DD`。
- `updated_at` 必须等于或晚于 `created_at`。
- `review_after` 过期仍是 warning，不阻断历史条目；格式错误是 error。
- 不自动改写日期，不自动延后 review，不自动生成索引。

## 非目标

- 不修改外部源 docs。
- 不修改 PCR02 源项目 docs。
- 不改变已有条目的 owner、status、review_after 或 promotion 状态。
- 不启用自动化。
- 不写入 `~/.codex/memories`。

## 验证计划

- `rtk bash -n tools/knowledge-check.sh`
- `rtk jq -c . registry/items.jsonl`
- `rtk jq -c . artifacts/manifests/knowledge-hub-item-date-gate-20260619.jsonl`
- `rtk jq -c . registry/items.jsonl`
- `rtk bash tools/knowledge-check.sh --dry-run --json`
- `/tmp` 负向验证：复制仓库后把一个 item 的 `created_at` 改成非法日期，`knowledge-check` 应报 invalid created_at。
- `/tmp` 负向验证：复制仓库后把一个 item 的 `updated_at` 改成早于 `created_at`，`knowledge-check` 应报 updated_at before created_at。
- `/tmp` 兼容验证：复制仓库后把一个 active item 的 `review_after` 改成过期日期，`knowledge-check` 应保持 pass 并输出 stale warning。
- `rtk bash tools/knowledge-search.sh "item-date-gate-applied" --json`

## 结果

- `rtk bash -n tools/knowledge-check.sh`: pass。
- `rtk jq -c . registry/items.jsonl`: pass。
- `rtk jq -c . artifacts/manifests/knowledge-hub-item-date-gate-20260619.jsonl`: pass。
- `rtk jq -c . registry/items.jsonl`: pass。
- `rtk bash tools/knowledge-check.sh --dry-run --json`: pass，`errors=[]`，`warnings=[]`。
- `/tmp` invalid-created-at 负向验证：把一个 item 的 `created_at` 改成 `2026-99-99` 后，`knowledge-check` 报 `items:knowledge-hub-root invalid created_at: 2026-99-99`。
- `/tmp` updated-before-created 负向验证：把一个 item 的 `updated_at` 改成早于 `created_at` 后，`knowledge-check` 报 `items:knowledge-hub-root updated_at before created_at: 2026-06-15 < 2026-06-16`。
- `/tmp` stale-review-after 兼容验证：把一个 active item 的 `review_after` 改成 `2000-01-01` 后，`knowledge-check` 仍 pass，并输出 warning `items:knowledge-hub-root review_after is stale: 2000-01-01`。
- `rtk bash tools/knowledge-search.sh "item-date-gate-applied" --json`: count=3，可从 `registry/items.jsonl`、`indexes/by-status.md` 和本 manifest 找到。

## 子代理复核

- IDG-REVIEW-001 确认日期实现是最小充分路径，`created_at`、`updated_at`、`review_after` 不会重复报 invalid；`review_after` 过期只 warning，不阻断维护。
- IDG-REVIEW-001 建议把 `review_after` 过期 warning 语义写入文档；已补入 `registry/schema.md` 和 `tools/README.md`。
