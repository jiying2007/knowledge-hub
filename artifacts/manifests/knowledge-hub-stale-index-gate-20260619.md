# Knowledge Hub Stale Index Gate - 2026-06-19

## 摘要

本次修复把核心索引中的 stale item reference 纳入 `knowledge-check`。上一次治理已经保证 registry item 不会漏进核心索引；本次补齐反向约束，保证核心索引不会保留已删除、改名或拼错的 registry item id。

本 manifest 是治理门禁记录，不是内容迁移；不修改源项目 docs，不写 memory，不启用自动化，不提升任何 owner-gated 条目。

## 问题地图

| ID | 发现 | 级别 | 证据 | 处理 |
| --- | --- | --- | --- | --- |
| KHD-20260619-004 | `by-owner`、`by-review-date`、`by-status` 缺少 stale id 反向校验。 | P1 | 只读核对当前 stale 集合为空，但旧门禁不能防止未来残留 id。 | 已在 `tools/knowledge-check.sh` 中加入 stale item reference 检查。 |
| KHD-20260619-005 | `by-status.md` 含 artifact path 和 overlay bullet，不能简单把所有 code span 当 item id。 | P2 | `by-status.md` 的 overlay 行含 manifest 路径。 | 仅对 canonical `active`、`reviewing`、`archived` 状态行执行反向 stale 校验。 |

## 已改内容

- `tools/knowledge-check.sh`
  - 抽出 range 展开函数。
  - `by-owner`、`by-review-date`：所有反引号 item id 必须存在于 `registry/items.jsonl`。
  - `by-status`：只检查 canonical status 行中的 item id 和 range 展开结果。
- `tools/README.md`
  - 说明核心索引检查同时覆盖 missing 和 stale 两个方向。
- `registry/items.jsonl`、`registry/items.jsonl`、`indexes/by-*`
  - 登记本次门禁修复。

## 验证

已执行：

```bash
rtk bash tools/knowledge-check.sh --dry-run --json
rtk bash tools/knowledge-search.sh "stale-index-gate-applied" --json
rtk git diff --check
```

预期结果：

- `knowledge-check` 返回 `pass`，无 errors/warnings。
- `stale-index-gate-applied` 可检索到 registry、status index 和本 manifest。
- diff 无 whitespace error。

## 剩余风险

- `by-project.md`、`by-topic.md` 是导航索引，仍允许引用 manifest/path/topic，不适合按 item id 做严格反向校验。
- `by-status.md` 的 overlay 状态仍是人读提示；严格校验只覆盖 canonical status 行，避免误杀 artifact 路径。

## Review

- owner：`leiwenjun`
- status：`reviewing`
- review_status：`stale-index-gate-applied`
- promotion：`none`
- review_after：`2026-09-19`
