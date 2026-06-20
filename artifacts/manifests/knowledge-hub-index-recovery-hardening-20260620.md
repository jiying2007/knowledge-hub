# Knowledge Hub index recovery hardening 2026-06-20

## 结论

本批次根据并行 subagent 审查结果，强化 Knowledge Hub 索引和状态看板的长期恢复能力。变更范围只包含 read-only 工具输出、人工维护说明、回归防退化、registry/index 登记和本 manifest。

当前终态预期不变：非 owner 自动治理应通过；PCR02 仍有 7 个 owner gate 等待人工语义签收，因此最终门禁应停在 `needs-owner-review`，而不是 `complete`。

## 已落地项

| ID | 范围 | 处理结果 |
|---|---|---|
| index-plan-source-final-state-fields | `tools/knowledge-index-plan.sh` | `--section source` 输出 owner、review_after、authority、migration_strategy、final_disposition、check/no_check_reason 和 coverage，便于从 source id 恢复治理状态。 |
| index-plan-owner-worksheet-recovery-fields | `tools/knowledge-index-plan.sh` | `--section decision` 的 owner worksheet 行补充 status、owner 和 review_after，并继续明确 `no owner decision generated`。 |
| status-review-after-command | `tools/knowledge-status.sh`、`README.md`、`tools/README.md` | status JSON/text 和人工最短路径暴露 `rtk bash tools/knowledge-index-plan.sh --section review-date`，把过期复核变成可执行的人工作业入口。 |
| index-readme-recovery-rules | `indexes/README.md`、`indexes/by-source.md` | 明确 registry/source/migration 是结构化权威，索引是人读导航；source 字段恢复走 read-only planner，不复制一份易漂移字段表。 |
| regression-index-status-stale-coverage | `tools/knowledge-regression.sh`、`artifacts/manifests/knowledge-hub-governance-regression-helper-20260619.md` | 回归从 36 项扩展到 39 项，固定 indexes README 维护规则、status source/review_after 汇总和 stale review_after warning/status surface。 |

## Deferred

| 项 | 原因 | 后续建议 |
|---|---|---|
| `by-topic.md` 与 `by-decision.md` 强门禁 | 当前 `knowledge-check` 已强检查 `by-owner`、`by-review-date`、`by-status`，但 topic/decision 需要先定义 canonical 解析规则，避免把说明文字误判为权威事实。 | 独立切片设计 topic/decision schema，再加入 check/final gate。 |
| `by-source.md` 人工展开全部治理字段 | 全量展开会和 `registry/sources.json`、coverage JSONL 重复维护，容易产生 drift。 | 保持主表简洁，依赖 `knowledge-index-plan --section source` 输出可恢复字段。 |
| owner gate 关闭 | 缺少 owner 对 7 条 PCR02 review-required 项的正式语义决策。 | 继续使用 owner-ready package 和 owner-gates helper 分派，不由自动化生成决策。 |

## Evidence Index

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
|---|---:|---|---|---|---|
| `rtk git diff --check` | 0 | 通过；无 whitespace/conflict-marker drift。 | Git diff | Gate | `knowledge-hub-index-recovery-hardening-20260620` |
| `rtk bash tools/knowledge-index-plan.sh --section source --json` | 0 | 通过；`item_count=168`、`source_count=13`，source 视图输出 owner、review_after、final_disposition、check/no_check_reason 和 coverage。 | `tools/knowledge-index-plan.sh` | Tool | `knowledge-hub-index-recovery-hardening-20260620` |
| `rtk bash tools/knowledge-index-plan.sh --section decision --json` | 0 | 通过；owner worksheet 派生视图输出 7 条 open worksheet，包含 owner/status/review_after，并保持 `no owner decision generated`。 | `tools/knowledge-index-plan.sh` | Tool | `knowledge-hub-index-recovery-hardening-20260620` |
| `rtk bash tools/knowledge-status.sh --json` | 0 | 通过；`status=needs-owner-review`，`registered_count=13`，latest coverage 为 `knowledge-hub-source-coverage-closeout-20260620.jsonl`，`stale_review_after_count=0`，owner-ready coverage 为 `7/7`。 | `tools/knowledge-status.sh` | Tool | `knowledge-hub-index-recovery-hardening-20260620` |
| `rtk bash tools/knowledge-check.sh --dry-run --json --diagnostics` | 0 | 通过；0 errors、0 warnings。 | `tools/knowledge-check.sh` | Gate | `knowledge-hub-index-recovery-hardening-20260620` |
| `rtk bash tools/knowledge-regression.sh --json` | 0 | 通过；39 个回归场景全部 pass，新增覆盖 indexes README、status source governance summary 和 stale review_after warning/status surface。 | `tools/knowledge-regression.sh` | Regression | `knowledge-hub-index-recovery-hardening-20260620` |
| `rtk bash tools/knowledge-final-gate.sh --json` | 1 | 预期非零；`final_status=needs-owner-review`，`automatic_governance.status=complete-except-owner-review`，`knowledge_check/regression/git_diff_check` 均 pass，唯一 blocker 为 7 个 owner gates。 | `tools/knowledge-final-gate.sh` | Final Gate | `knowledge-hub-index-recovery-hardening-20260620` |

## 边界

- 不生成 owner decision。
- 不关闭 owner gate。
- 不复制或修改 PCR02 源项目 docs。
- 不把 PCR02 project-specific 内容提升到 `domains/embedded/standards/`。
- 不启用自动化；自动化仍默认 `report-only`。
- 不写 `~/.codex/memories`。
