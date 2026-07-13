# Knowledge Hub operational audit 2026-07-13

## Scope

本记录收口 2026-07-13 对 Knowledge Hub mature 终态后的运营优化：

- 刷新 18 条 2026-08-09..2026-08-11 近期待复核的 Codex archive 条目。
- 固化 2026-07-13 mature full final gate 审计结果。
- 固定后续性能优化只盯 full regression slowest 10，不做泛化重构。
- 收口当前 P1/P2/P3 dirty worktree 进入同一批可审查提交。

本记录只处理 Hub 控制面、registry、index、manifest 和只读工具边界；不生成 owner decision、不关闭 owner gate、不提升 active、不写 memory、不修改源项目、不 push/merge/release/tag。

## Codex Archive Review

2026-07-13 运行：

```bash
rtk bash ~/knowledge-hub/tools/knowledge-review-after.sh --as-of 2026-07-13 --window-days 30 --json
```

结果显示 18 条 near-due item，全部属于 `codex-archive`，其中 4 条为 `reviewing`，14 条为 `archived`。本轮复核结论：

- `reviewing` 的 migration/removal/preflight 条目继续保持 reviewing，仅作为 Codex archive provenance / removal planning，不提升 active。
- `archived` 的 removal/coverage/readiness 条目继续保持 archive-only / tombstone / provenance 边界，不声明 current fact。
- 18 条均不涉及 owner gate、active promotion、memory write 或 source project write。
- 下一轮 `review_after` 按同日顺延三个月：2026-08-09 -> 2026-11-09，2026-08-10 -> 2026-11-10，2026-08-11 -> 2026-11-11。

## Mature Gate Evidence

2026-07-13 审计命令：

| Command | Result |
|---|---|
| `rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics --as-of 2026-07-13` | exit 0；status=pass；errors=0；warnings=0 |
| `rtk bash ~/knowledge-hub/tools/knowledge-orphan-files.sh --json --strict` | exit 0；checked=2；missing_registry_count=0 |
| `rtk bash ~/knowledge-hub/tools/knowledge-review-after.sh --as-of 2026-07-13 --window-days 30 --json` | exit 0；near_due_items=18；stale_items=0；owner_gate_open_count=0 |
| `rtk bash ~/knowledge-hub/tools/knowledge-final-gate.sh --json --final-profile mature --full-regression --as-of 2026-07-13` | exit 0；final_status=ok；blockers=[]；gap_map=[]；full regression result_count=140 |
| `rtk bash ~/knowledge-hub/tools/knowledge-regression-trend.sh --run --suite full --as-of 2026-07-13 --json` | exit 0；regression_status=pass；result_count=140；failed_ids=[] |
| `rtk git diff --check` | exit 0；当前 diff 无空白错误 |

## Regression Watchlist

后续性能优化只处理 full regression slowest 10 的可证实瓶颈，不做泛化重构。2026-07-13 slowest 10：

| ID | Duration |
|---|---:|
| `review-after-as-of-deterministic` | 10.411s |
| `final-gap-readability-positive-contracts` | 10.266s |
| `review-queue-apply-tool-contract` | 9.763s |
| `review-queue-json-contract` | 9.282s |
| `source-coverage-date-filename-selection` | 8.041s |
| `status-next-owner-gate` | 6.915s |
| `manual-entry-template-selection` | 5.867s |
| `final-gate-owner-review-blocker` | 5.773s |
| `owner-form-decision-target-pair-reference-only-project-path` | 5.741s |
| `owner-form-decision-target-pair-no-migration-project-path` | 5.741s |

优化边界：

- 只优化 fixture 复制、重复子门禁、明显串行等待和单测局部算法。
- 不降低 final gate、strict status、owner gate、review queue 或 source boundary 语义。
- 不把 `KNOWLEDGE_FINAL_GATE_SKIP_REGRESSION=1` 用作 release gate。
- 每次性能改动后记录 `jobs`、`result_count`、`failed_ids` 和 slowest 10。

## Residual Risk

- Codex archive near-due 已刷新到 2026-11，但这只是运营复核排期，不是 owner approval、active promotion 或 corpus deletion 授权。
- PCR02 owner-ready decision candidate 的真实 owner/实机/发布验证路径另见 `pcr02-owner-ready-validation-paths-20260713`。
- 本记录不代表远端发布完成；远端 push/merge/release/tag 仍需显式授权。
