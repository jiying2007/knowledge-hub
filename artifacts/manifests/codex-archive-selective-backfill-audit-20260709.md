# Codex archive 选择性回填审计 2026-07-09

## 摘要

本审计落实 `codex-archive` 的 `reference-first` 边界：不整库迁移旧 Codex archive，不批量复制历史正文，只把现有 Hub canonical archive 按 topic 级别分成可复查的迁移决策。后续“慢慢迁移并移除”的执行台账见 `artifacts/manifests/codex-archive-phased-migration-removal-20260709.md`。

- 审计范围：`domains/codex/archive/codex-archive`。
- 退役来源：`~/codex/docs/archive`，当前本机路径不存在；仅保留在 `origin_path`、tombstone 和迁移 manifest 中作 provenance。
- 明细粒度：1 条边界记录 + 12 条 topic 记录。
- 现有正文覆盖：85 个非 `index.md` Markdown 文件，12 个 topic 目录。
- 本轮动作：report-only，不生成逐条归档正文，不写 `~/.codex/memories`，不提升 active rule。

结构化明细见：`artifacts/manifests/codex-archive-selective-backfill-audit-20260709.jsonl`。

## 分类口径

| 分类 | 含义 | 本轮动作 |
| --- | --- | --- |
| `covered` | 当前 Hub 已有 canonical 入口或等价控制面 | 不迁移 |
| `promote-candidate` | 仍可能有长期价值，但需要后续逐条重写、脱敏、去重和 review | 只入候选队列 |
| `provenance-only` | 适合追溯历史，不适合成为当前知识正文 | 保留引用 |
| `discard-noise` | 过程噪音、过期实现口径或 raw/runtime 材料 | 不迁移；本轮 topic 级别未发现需要单列的 `discard-noise` 目录 |

## 审计结论

| 对象 | 文件数 | 分类 | 结论 |
| --- | ---: | --- | --- |
| root boundary | 1 | `covered` | `codex-archive.ref.md` 已定义 reference-first / no-wholesale 边界。 |
| `_registry` | 1 | `covered` | 仅保留旧 archive v2 schema 说明；当前 Hub registry/schema 已是权威。 |
| `archive-governance` | 1 | `covered` | 已作为归档治理历史保留，不需要重新迁移。 |
| `control-archives` | 2 | `provenance-only` | 属于旧控制面知识，保留溯源即可。 |
| `daily-summary` | 2 | `promote-candidate` | 个别日报可能包含跨项目长期结论；后续只能逐条拆分回填。 |
| `debug-notes` | 3 | `promote-candidate` | 调试结论有复用价值，但需按项目/debug 记录重新脱敏和验证。 |
| `diag-architecture` | 2 | `covered` | 诊断架构主结论已被 PCR02 current/decisions 或 Codex archive 覆盖。 |
| `memory-curation` | 40 | `provenance-only` | 只作为 memory 治理来源；不得静默写 memory 或提升规则。 |
| `patent-disclosure` | 2 | `covered` | 专利材料长期边界在 `domains/patents/`，Codex archive 只保留过程记录。 |
| `release-governance` | 3 | `promote-candidate` | 发布治理结论可能复用；后续需按 release/runbook 独立审查。 |
| `research-notes` | 2 | `promote-candidate` | 调研结论可能值得转成 research note，但必须重新核验证据。 |
| `session-wrap` | 25 | `provenance-only` | 会话收尾适合恢复上下文，不直接成为 current fact。 |
| `tools` | 1 | `provenance-only` | 工具入口历史只保留索引价值；当前工具事实以 live docs/scripts 为准。 |

## 候选队列

本轮只登记 topic 级候选，不落地正文：

- `daily-summary`：优先检查是否还有未归档的跨项目工程结论；已存在的 2026-07-08 日报不重复。
- `debug-notes`：逐条判断是否应进入 `projects/<project>/archive/debug/` 或 `domains/codex/archive/codex-archive/debug-notes/`。
- `release-governance`：只提升经过 release evidence 支撑的治理结论，不把历史计划当完成事实。
- `research-notes`：只提升仍有效、有证据、无等价 Hub 条目的调研结论。

每个候选后续必须作为独立任务处理，并满足：

- 不含 secrets、token、cookie、private key、raw session、cache、runtime state、core 或 binary。
- 有明确 source provenance、目标路径、owner/review 边界和验证证据。
- 与 `registry/items.jsonl`、`indexes/by-source.md`、`knowledge-search` 结果不重复。
- 不把 project-specific 结论提升为全局 active rule。
- 若要提升为 active governance，必须另建 manifest，补 owner review、`promotion_decision`、rollback 和验证命令。

## 证据

- `domains/codex/archive/codex-archive.ref.md`
- `sources/codex-archive/inventory.jsonl`
- `sources/codex-archive/coverage.md`
- `sources/codex-archive/source-policy.md`
- `registry/items.jsonl`
- `indexes/by-source.md`
- `artifacts/manifests/knowledge-hub-source-coverage-closeout-20260624.jsonl`

## 验证计划

```bash
rtk bash ~/knowledge-hub/tools/knowledge-context.sh --cwd "$PWD" --query "旧 Codex archive 选择性回填审计" --task-type archive --json
rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run
rtk bash ~/knowledge-hub/tools/knowledge-search.sh "Codex archive 选择性回填"
rtk jq -c . artifacts/manifests/codex-archive-selective-backfill-audit-20260709.jsonl
rtk rg -n "password|token|cookie|private key|auth.json|\\.codex/sessions" artifacts/manifests/codex-archive-selective-backfill-audit-20260709.md artifacts/manifests/codex-archive-selective-backfill-audit-20260709.jsonl
```

## 结论

旧 Codex archive 仍有 provenance 价值，但不需要整库迁移。当前维护方向已调整为逐步收缩：保留 Hub canonical archive 作为过渡 corpus，按 topic 保留候选队列，只对 `promote-candidate` 中仍有效、未覆盖且有证据的内容逐条回填；其余 covered/provenance-only 内容在补齐 tombstone 或 covered_by 后进入后续删除批次。
