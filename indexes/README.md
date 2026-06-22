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
- `by-owner.md` 按 registry 维护 owner 聚合，不等同于 owner decision 的最终签收人；owner decision 分派先看 `knowledge-owner-gates.sh --summary` 的 `owner_route`，再看 `registry/owner-routing.json`。
- `by-source.md` 用于从 source id 恢复 migration、reference、artifact-ref、owner gate、source identity 和 coverage 证据；不要在索引里重复维护 source registry 字段，人工恢复 owner、review_after、final_disposition、check/no_check_reason 时运行 `rtk bash ~/knowledge-hub/tools/knowledge-index-plan.sh --section source`。
- 恢复 source coverage 时先运行 `rtk bash ~/knowledge-hub/tools/knowledge-index-plan.sh --section source --json`，查看 `source_coverage_selection.selected`；只有 `knowledge-hub-source-coverage-closeout-YYYYMMDD.jsonl` 形式的 dated closeout 能成为 latest，非日期 `latest` 文件只作为 ignored metadata，不得当作当前状态。同一 closeout 中如果 `source_id` 重复，`duplicate_source_ids` 和 warnings 会显式暴露，恢复视图只保留第一行，不允许后写行静默覆盖。
- `by-decision.md` 同时记录真实决策、迁移决策和 owner-gated 的 `no owner decision generated` 状态；不得把 owner-ready package 写成已签收决策。
- `by-project.md` 应能从 project id 找到 current、archive、decisions、validation 和 manifests。
- `by-topic.md` 只做主题导航，不复制正文；跨会话、跨项目和跨 source 的恢复优先写清主题入口，不把临时会话 handoff 当 active fact。
- `artifacts/manifests/` 不维护完整人工索引；恢复最新 manifest、Markdown/JSONL 配对、行数和证据计数时运行 `rtk bash ~/knowledge-hub/tools/knowledge-index-plan.sh --section manifest --json`，只在确有长期导航价值时把摘要登记到 registry/index。manifest latest 只按文件名 `YYYYMMDD` 排序，row 内日期只作为 `row_date` 辅助字段，不能让旧文件凭 row 日期抢占最新恢复依据。

## 检查命令

```bash
rtk bash ~/knowledge-hub/tools/knowledge-index-plan.sh --section all
rtk bash ~/knowledge-hub/tools/knowledge-index-plan.sh --section manifest --json
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
