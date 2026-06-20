# Indexes

本目录是 Knowledge Hub 的人工维护索引入口。`registry/items.jsonl`、`registry/sources.json` 和 `registry/migrations.jsonl` 是结构化权威来源，`indexes/*.md` 是人读导航，不能作为唯一事实来源。

## 最小同步

新增或调整 registry item 后，至少同步：

- `indexes/by-owner.md`
- `indexes/by-review-date.md`
- `indexes/by-status.md`

条目涉及项目、source、主题或决策时，还要同步：

- `indexes/by-project.md`
- `indexes/by-source.md`
- `indexes/by-topic.md`
- `indexes/by-decision.md`

## 维护规则

- `by-status.md` 必须使用 canonical 行，例如 `- reviewing: <id>`。
- `by-source.md` 用于从 source id 恢复 migration、reference、artifact-ref、owner gate、source identity 和 coverage 证据。
- `by-decision.md` 同时记录真实决策、迁移决策和 owner-gated 的 `no owner decision generated` 状态；不得把 owner-ready package 写成已签收决策。
- `by-project.md` 应能从 project id 找到 current、archive、decisions、validation 和 manifests。
- `by-topic.md` 只做主题导航，不复制正文。

## 检查命令

```bash
rtk bash ~/knowledge-hub/tools/knowledge-index-plan.sh --section all
rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
```

如果工具不可用，先在正文或相邻维护记录中保留：

```text
manual_validation_pending: true
reason: tools unavailable / AI unavailable / offline field note
required_followup: run knowledge-check and update registry/index
owner: <owner>
review_after: <date>
```

AI 恢复后只能校验 registry/index 一致性、补缺漏和提示风险；不得覆盖人工结论、自动改 active、关闭 owner gate 或写 memory。
