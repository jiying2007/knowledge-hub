# Knowledge Hub proof 与搜索运行时加固 2026-06-22

## 结论

本轮继续压实终态自动治理证据面，重点处理两个可自动闭环的 P1 漂移风险：

- `knowledge-final-gate.sh` 的终态 proof 动态选择不再绑定固定 `2026-06-22` 日期；默认按 `--as-of` / `KNOWLEDGE_TODAY` / 系统日期选择当天 governance proof，同时保留 2026-06-22 seed 基线用于历史终态复现。
- `knowledge-search.sh` 增加 registry metadata-only fallback；当关键词只命中 `registry/items.jsonl` 中的 `id`、`title`、`path`、`tags`、`summary_zh`、`review_status` 或 `source.source_id` 时，也能返回带 `item_id` 的可追溯结果。
- `knowledge-regression.sh` 增加 2 个回归场景：`final-proof-artifact-as-of-date-selector` 和 `knowledge-search-registry-metadata-fallback`。
- `knowledge-hub-governance-regression-helper-20260619.md` 已同步登记 103 个回归场景，避免 regression manifest 自检漏登新增 ID。

## 边界

- 不生成 owner decision。
- 不代填 `reviewed_by`，不关闭 PCR02 7 个 owner gate。
- 不修改 PCR02 源项目 docs、tools、knowledge、app_product_test、scratch 或 source tree。
- 不复制 owner-gated source 正文。
- 不把 PCR02 project-specific 内容提升到 `domains/embedded/standards/`。
- 不启用自动化写操作，不写 `~/.codex/memories`。
- `proof_artifacts_20260622` 字段名暂保留为兼容面；新的选择语义通过 `selection_mode`、`baseline_date`、`selection_date` 和 `dynamic_selector.date` 表达。

## 变更明细

| 区域 | 文件 | 变更 |
|---|---|---|
| final gate | `tools/knowledge-final-gate.sh` | 将 dynamic proof selector 改为按 as-of 日期选择；保留 2026-06-22 seed 基线 |
| search | `tools/knowledge-search.sh` | 增加 registry metadata haystack 和 metadata-only fallback 结果，结构化过滤仍只返回 registry item |
| regression | `tools/knowledge-regression.sh` | 新增未来日期 proof fixture 和 metadata-only search fixture，回归数量扩展到 103 |
| regression manifest | `artifacts/manifests/knowledge-hub-governance-regression-helper-20260619.md` | 登记新增回归 ID 与 Evidence Index 中的 103 场景摘要 |

## Evidence Index

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
|---|---:|---|---|---|---|
| `rtk bash -n tools/knowledge-search.sh` | 0 | shell 语法通过 | `tools/knowledge-search.sh` | Tool | `knowledge-hub-proof-search-runtime-hardening-20260622` |
| `rtk bash -n tools/knowledge-final-gate.sh` | 0 | shell 语法通过 | `tools/knowledge-final-gate.sh` | Tool | `knowledge-hub-proof-search-runtime-hardening-20260622` |
| `rtk bash -n tools/knowledge-regression.sh` | 0 | shell 语法通过 | `tools/knowledge-regression.sh` | Tool | `knowledge-hub-proof-search-runtime-hardening-20260622` |
| `rtk bash tools/knowledge-search.sh knowledge-hub-owner-status-review-proof-hardening-20260622 --json --limit 3` | 0 | 搜索入口保持兼容，仍能返回既有正文/registry 命中 | `tools/knowledge-search.sh` | Tool | `knowledge-hub-proof-search-runtime-hardening-20260622` |
| `rtk bash tools/knowledge-regression.sh --json --as-of 2026-06-22` | 0 | 103 个回归场景通过，包含 proof as-of 日期选择和 registry metadata-only fallback | `tools/knowledge-regression.sh` | Tool | `knowledge-hub-proof-search-runtime-hardening-20260622` |
| `rtk bash tools/knowledge-check.sh --dry-run --json --diagnostics --as-of 2026-06-22` | 0 | 全仓知识门禁通过，0 errors | `tools/knowledge-check.sh` | Tool | `knowledge-hub-proof-search-runtime-hardening-20260622` |
| `rtk bash tools/knowledge-final-gate.sh --json --as-of 2026-06-22` | 1 | 预期停在 `needs-owner-review`；自动治理为 `complete-except-owner-review`，唯一 blocker 为 7 个 owner gate | `tools/knowledge-final-gate.sh` | Tool | `knowledge-hub-proof-search-runtime-hardening-20260622` |

## 后续人工动作

- 真实 owner 仍需按 `knowledge-owner-gates.sh` 的 owner inbox / forms-jsonl / validate / landing-plan / landing-audit 路径处理 7 个 open gate。
- 后续新增 governance proof 时，文件名日期、`created_at` / `updated_at` 和 `--as-of` 日期必须一致，才能自动进入 dynamic proof selector。
- 搜索命中 `match=registry-metadata` 时，应优先读取返回的 `item_id`、`path`、`summary_zh` 和 `evidence_refs`，不要把未登记 raw file 当作 current fact。
