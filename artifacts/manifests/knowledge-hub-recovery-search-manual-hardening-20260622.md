# Knowledge Hub recovery, search and manual-entry hardening 2026-06-22

## 结论

本轮继续推进终态治理，修复 5 个仍可能让长期维护者误读当前状态的自动治理缺口：

- manifest latest 恢复只按文件名 `YYYYMMDD` 排序，不再让 JSONL row 内日期抢占最新依据。
- source coverage latest 中重复 `source_id` 会显式进入 warnings 和 `duplicate_source_ids`，恢复视图保留第一行，避免后写行静默覆盖。
- 结构化搜索在 `--source-id` / `--status` 等过滤模式下只返回已登记 registry item，排除同关键词未登记 raw file。
- 人工新增草稿默认使用 `knowledge-check --dry-run --json --diagnostics`，离线待验证 follow-up 也锁定 diagnostics。
- source 新增向导的 coverage row `status` 跟随 `--source-status`，退役或废弃 source 不会被固定写成 registered。

## 变更范围

| 文件 | 变更 |
|---|---|
| `tools/knowledge-index-plan.sh` | 增加 source coverage duplicate source_id 可观测性；manifest latest 改为 filename-date-only，并保留 `row_date` 辅助字段。 |
| `tools/knowledge-new.sh` | 默认 validation refs / Evidence Index 使用 diagnostics；source coverage row status 跟随 source status。 |
| `tools/knowledge-regression.sh` | 回归场景从 80 个扩展到 85 个，覆盖本轮 5 个防漂移契约。 |
| `README.md`、`tools/README.md`、`templates/README.md`、`indexes/README.md` | 同步中文维护规则和恢复边界。 |
| `artifacts/manifests/knowledge-hub-governance-regression-helper-20260619.md` | 登记新增回归 ID 与 85 场景证据摘要。 |

## 新增回归 ID

- `manual-entry-validation-diagnostics-default`
- `manifest-latest-filename-date-only`
- `source-coverage-duplicate-source-id-warning`
- `source-manual-entry-status-coverage-sync`
- `knowledge-search-structured-filters-exclude-unregistered-raw`

## 边界

- 不生成 owner decision。
- 不关闭 PCR02 owner gate。
- 不修改 PCR02 源项目文件。
- 不复制 owner-gated source 正文。
- 不把 PCR02 project-specific 内容提升到 `domains/embedded/standards/`。
- 不启用自动化写操作。
- 不写 `~/.codex/memories`。

## Evidence Index

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
|---|---:|---|---|---|---|
| `rtk bash -n tools/knowledge-index-plan.sh` | 0 | 通过；索引恢复脚本语法检查通过。 | `tools/knowledge-index-plan.sh` | Tool | `knowledge-hub-recovery-search-manual-hardening-20260622` |
| `rtk bash -n tools/knowledge-new.sh` | 0 | 通过；人工新增向导语法检查通过。 | `tools/knowledge-new.sh` | Tool | `knowledge-hub-recovery-search-manual-hardening-20260622` |
| `rtk bash -n tools/knowledge-search.sh` | 0 | 通过；搜索入口语法检查通过。 | `tools/knowledge-search.sh` | Tool | `knowledge-hub-recovery-search-manual-hardening-20260622` |
| `rtk bash -n tools/knowledge-regression.sh` | 0 | 通过；回归入口语法检查通过。 | `tools/knowledge-regression.sh` | Tool | `knowledge-hub-recovery-search-manual-hardening-20260622` |
| `rtk bash tools/knowledge-regression.sh --json --as-of 2026-06-22` | 0 | 通过；85 个回归场景全部 pass，新增 5 个场景覆盖 manifest latest、source coverage duplicate、structured search raw 排除、manual diagnostics 和 source status coverage sync。 | `tools/knowledge-regression.sh` | Regression | `knowledge-hub-recovery-search-manual-hardening-20260622` |
| `rtk bash tools/knowledge-check.sh --dry-run --json --diagnostics --as-of 2026-06-22` | 0 | 通过；0 errors、0 warnings，source coverage latest 仍选择 `knowledge-hub-source-coverage-closeout-20260620.jsonl`，boundary health 为 pass。 | `tools/knowledge-check.sh` | Gate | `knowledge-hub-recovery-search-manual-hardening-20260622` |
| `rtk bash tools/knowledge-index-plan.sh --section manifest --json` | 0 | 通过；manifest 恢复视图为 read-only planned，latest 策略为 `filename-date-only`。 | `tools/knowledge-index-plan.sh` | Recovery | `knowledge-hub-recovery-search-manual-hardening-20260622` |
| `rtk bash tools/knowledge-index-plan.sh --section source --json` | 0 | 通过；source coverage latest 选择 `knowledge-hub-source-coverage-closeout-20260620.jsonl`，当前 `duplicate_source_ids=[]`，duplicate policy 为 first-row-kept-duplicates-warned。 | `tools/knowledge-index-plan.sh` | Recovery | `knowledge-hub-recovery-search-manual-hardening-20260622` |
| `rtk git diff --check` | 0 | 通过；未发现 whitespace 或 conflict marker 问题。 | `git diff --check` | Git | `knowledge-hub-recovery-search-manual-hardening-20260622` |
| `rtk bash tools/knowledge-final-gate.sh --json --as-of 2026-06-22` | 1 | 符合预期；final status 为 `needs-owner-review`，回归为 pass，唯一 blocker 为 7 个 `owner-gates-open`，这是人工 owner 语义门禁，不是本轮工具失败。 | `/tmp/kh-final-20260622.json` | Final Gate | `knowledge-hub-recovery-search-manual-hardening-20260622` |

## 终态验证说明

本轮自动治理切片已完成工具和索引层终态验证。`knowledge-final-gate.sh` 仍返回非零，状态为 `needs-owner-review`；唯一 blocker 是 PCR02 owner decision worksheet 仍有 7 个 open gate。该 blocker 只能由真实 owner 复核并填写 owner decision 后关闭，本轮未代签、未关闭 gate、未提升 active。
