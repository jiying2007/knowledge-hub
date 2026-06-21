# Knowledge Hub as-of and coverage contract 2026-06-21

## 结论

本轮继续压实 Knowledge Hub 终态门禁的可复现性和 source coverage 可观测性。当前 final gate 的终态仍是 `needs-owner-review`，并且自动治理状态为 `complete-except-owner-review`；唯一剩余 blocker 仍是 PCR02 7 个人工 owner decision gate。

本轮不生成 owner decision、不关闭 owner gate、不修改 PCR02 源项目 docs、不复制 source 正文、不提升 PCR02 project-specific 内容到 `domains/embedded/standards/`、不启用自动化写操作、不写 `~/.codex/memories`。

## 改动范围

| 文件 | 改动 |
| --- | --- |
| `tools/knowledge-check.sh` | 增加 `--as-of YYYY-MM-DD` 和 `KNOWLEDGE_TODAY` 日期来源；JSON 输出 `today`、`as_of_source`、`source_coverage_selection` 和 `source_coverage_health`。 |
| `tools/knowledge-status.sh` | 增加 `--as-of` 日期来源，透传给 `knowledge-check`；固定日期时 `final_gate_command` 和 next action 保留同一个 `--as-of`；JSON 暴露 latest coverage selection。 |
| `tools/knowledge-final-gate.sh` | 增加 `--as-of` 日期来源，透传给 `knowledge-check`、`knowledge-status` 和 `knowledge-regression`；checks 中记录 regression 子命令。 |
| `tools/knowledge-regression.sh` | 增加 `--as-of` 和 `KNOWLEDGE_TODAY` 子进程环境，回归覆盖固定日期、final-gate as-of 透传、coverage selection/health。 |
| `tools/knowledge-new.sh` | 只读人工新增向导支持 `KNOWLEDGE_TODAY`，用于固定草稿日期，默认仍使用 UTC 当前日期。 |
| `tools/knowledge-index-plan.sh` | source section JSON 顶层输出 `source_coverage_selection`，使 `by_source[*].coverage` 的来源可追溯。 |
| `tools/README.md`、`registry/schema.md` | 记录 `--as-of`、`KNOWLEDGE_TODAY`、source coverage selection/health 的中文维护契约。 |
| `artifacts/manifests/knowledge-hub-governance-regression-helper-20260619.md` | 回归场景数从 63 更新到 64，补 `review-after-as-of-deterministic`。 |

## 契约

### 日期复现契约

- `knowledge-check.sh`、`knowledge-status.sh`、`knowledge-final-gate.sh` 支持 `--as-of YYYY-MM-DD`。
- `knowledge-check.sh`、`knowledge-status.sh`、`knowledge-regression.sh`、`knowledge-new.sh` 支持 `KNOWLEDGE_TODAY=YYYY-MM-DD`。
- `--as-of` 只用于复现 `review_after` stale 判断和终态证据，不修改 registry，不改变 owner gate，不生成 owner decision。
- `knowledge-status.sh --json --as-of <date>` 输出的 `final_gate_command` 必须保留同一个 `<date>`，避免人工复制恢复命令时回到系统日期。
- `knowledge-final-gate.sh --json --as-of <date>` 必须把同一个 `<date>` 传给 regression，避免终态门禁表面固定日期、内部仍用真实日期。

### Source coverage 可观测性契约

- latest source coverage manifest 当前策略仍是 `lexicographic-path-sort-last`，即按 `artifacts/manifests/knowledge-hub-source-coverage-closeout-*.jsonl` 路径字典序排序后取最后一个。
- `knowledge-status.sh --json`、`knowledge-check.sh --json` 和 `knowledge-index-plan.sh --section source --json` 必须暴露 selection metadata：`pattern`、`strategy`、`candidate_count`、`candidates`、`selected`、`reason_zh`。
- `knowledge-check.sh --json` 必须在 pass 状态下也暴露 `source_coverage_health`，包括 registered source 数、coverage row 数、唯一 source 数、missing/stale/duplicate source、缺字段行和非法 `checked_at` 行。
- selection/health 只是可审计摘要，不替代 source coverage JSONL row，不替代 owner decision，也不代表 active fact。

## 回归契约

| ID | 类型 | 预期 |
| --- | --- | --- |
| `review-after-as-of-deterministic` | positive/negative mixed fixture | 临时副本固定 item `review_after=2026-06-30` 后，`--as-of 2026-06-01` 不产生 stale，`--as-of 2026-07-01` 产生 stale，并且 status/final-gate 保留固定日期。 |
| `status-source-governance-summary` | positive contract | status JSON 暴露 latest coverage selection；check JSON 暴露 source coverage selection/health，且 13 个 registered source 全部覆盖、无缺失、无重复、无 stale。 |
| `index-plan-extended-sections` | positive contract | source index-plan JSON 暴露 source coverage selection，且 `pcr02-project-tools` coverage decision/risk 来源可追溯。 |
| `final-gate-default-regression-path` | positive contract | final gate 默认路径真实执行 regression，并在 checks 中记录带 `--as-of` 的 regression 子命令。 |

## Evidence Index

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
| --- | ---:| --- | --- | --- | --- |
| `rtk bash -n tools/knowledge-new.sh` | 0 | 通过；manual entry guide shell 语法有效。 | `tools/knowledge-new.sh` | Tool | `knowledge-hub-asof-coverage-contract-20260621` |
| `rtk bash -n tools/knowledge-regression.sh` | 0 | 通过；regression shell 语法有效。 | `tools/knowledge-regression.sh` | Tool | `knowledge-hub-asof-coverage-contract-20260621` |
| `rtk bash -n tools/knowledge-check.sh` | 0 | 通过；knowledge-check shell 语法有效。 | `tools/knowledge-check.sh` | Tool | `knowledge-hub-asof-coverage-contract-20260621` |
| `rtk bash -n tools/knowledge-index-plan.sh` | 0 | 通过；index planner shell 语法有效。 | `tools/knowledge-index-plan.sh` | Tool | `knowledge-hub-asof-coverage-contract-20260621` |
| `rtk bash tools/knowledge-status.sh --json --as-of 2026-06-01` | 0 | 通过；status 输出 `today=2026-06-01`、`as_of_source=arg:--as-of`，并保留 `final_gate_command` 的 `--as-of 2026-06-01`。 | `tools/knowledge-status.sh` | Tool | `knowledge-hub-asof-coverage-contract-20260621` |
| `KNOWLEDGE_TODAY=2026-06-01 rtk bash tools/knowledge-new.sh --kind decision --domain governance --id governance-date-defaults --path governance/date-defaults.md` | 0 | 通过；人工新增草稿日期固定为 2026-06-01，`review_after` 为 2026-09-01。 | `tools/knowledge-new.sh` | Tool | `knowledge-hub-asof-coverage-contract-20260621` |
| `rtk bash tools/knowledge-regression.sh --as-of 2026-06-01 --json` | 0 | 通过；64 个回归场景全部 pass，固定日期路径无失败 ID。 | `/tmp/kh-regression-asof.json` | Tool | `knowledge-hub-asof-coverage-contract-20260621` |
| `rtk bash tools/knowledge-regression.sh --json` | 0 | 通过；64 个回归场景全部 pass，默认系统日期路径无失败 ID。 | `/tmp/kh-regression-default.json` | Tool | `knowledge-hub-asof-coverage-contract-20260621` |
| `rtk bash tools/knowledge-check.sh --dry-run --json --diagnostics` | 0 | 通过；0 errors / 0 warnings，并输出 source coverage selection/health。 | `tools/knowledge-check.sh` | Tool | `knowledge-hub-asof-coverage-contract-20260621` |
| `rtk bash tools/knowledge-index-plan.sh --section source --json` | 0 | 通过；source section JSON 输出 latest source coverage selection。 | `tools/knowledge-index-plan.sh` | Tool | `knowledge-hub-asof-coverage-contract-20260621` |
| `rtk bash tools/knowledge-final-gate.sh --json` | 1 | 预期阻断；`automatic_governance.status=complete-except-owner-review`，`knowledge_regression.result_count=64`，唯一 blocker 为 `owner-gates-open`。 | `tools/knowledge-final-gate.sh` | Tool | `knowledge-hub-asof-coverage-contract-20260621` |

## 边界

- 不生成 owner decision。
- 不关闭 PCR02 owner gate。
- 不修改 PCR02 源项目 docs。
- 不复制 source 正文。
- 不把 PCR02 project-specific 内容提升到 `domains/embedded/standards/`。
- 不启用自动化写操作。
- 不写 `~/.codex/memories`。
- `--as-of` 与 `KNOWLEDGE_TODAY` 只用于只读工具证据复现，不作为长期事实日期来源。
