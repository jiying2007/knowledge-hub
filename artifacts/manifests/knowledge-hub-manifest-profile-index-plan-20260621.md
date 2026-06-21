# Knowledge Hub manifest profile and index plan 2026-06-21

## 摘要

本记录登记一次 Knowledge Hub 治理工具收口：为 `knowledge-index-plan.sh` 增加 `--section manifest` 恢复视图，为 2026-06-21 及之后新增的 `knowledge-hub-*.jsonl` 治理 manifest 增加轻量 profile gate，并把长期模板的中文可读性字段纳入 `knowledge-check` 与 regression 负向场景。

目标是降低三类长期维护风险：

- 新线程恢复时必须人工翻阅 100+ 个 manifest。
- 新增治理 JSONL 只有机器字段，缺少中文摘要、证据或边界。
- 模板字段回退后，后续中文开发者难以判断来源、证据、review 状态和 AI 生成边界。

## 变更范围

- `tools/knowledge-index-plan.sh`
  - 新增 `--section manifest`。
  - 输出 `by_manifest.summary/latest/unpaired/rows`。
  - 行级暴露 Markdown/JSONL 配对、JSONL 行数、日期、owner、classification/mode/decision、中文摘要和证据计数。
- `tools/knowledge-check.sh`
  - 新增 `manifest-jsonl-profile` diagnostics 分类。
  - 对 `artifacts/manifests/knowledge-hub-*-20260621.jsonl` 执行轻量 profile gate。
  - 对长期模板执行可读性字段 gate。
- `tools/knowledge-regression.sh`
  - 扩展 index-plan section 回归到 `manifest`。
  - 新增 `manifest-jsonl-profile-gate` 负向场景。
  - 新增 `template-readability-field-gate` 负向场景。
- `registry/schema.md`、`README.md`、`tools/README.md`、`indexes/README.md`
  - 补充 manifest JSONL 轻量契约、恢复命令和人工维护边界。
- `artifacts/manifests/knowledge-hub-governance-regression-helper-20260619.md`
  - 同步回归 helper 场景清单和数量。

## 边界

- 不回填或重写 2026-06-21 之前的历史 manifest。
- 不把 copy-first、artifact-ref、owner worksheet、source coverage 等类型化 JSONL 强行改成统一 registry item schema。
- 不关闭 PCR02 owner gate。
- 不生成 owner decision。
- 不修改 PCR02 源项目 docs。
- 不把 PCR02 project-specific 内容提升到 `domains/embedded/standards/`。
- 不启用自动化写操作，不写 `~/.codex/memories`。

## Evidence Index

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
|---|---:|---|---|---|---|
| `rtk bash -n tools/knowledge-index-plan.sh` | 0 | 通过；shell 语法检查无输出 | `tools/knowledge-index-plan.sh` | Tool | `knowledge-hub-manifest-profile-index-plan-20260621` |
| `rtk bash -n tools/knowledge-check.sh` | 0 | 通过；shell 语法检查无输出 | `tools/knowledge-check.sh` | Tool | `knowledge-hub-manifest-profile-index-plan-20260621` |
| `rtk bash -n tools/knowledge-regression.sh` | 0 | 通过；shell 语法检查无输出 | `tools/knowledge-regression.sh` | Tool | `knowledge-hub-manifest-profile-index-plan-20260621` |
| `rtk bash tools/knowledge-index-plan.sh --section manifest --json` | 0 | 通过；输出 `by_manifest` 恢复视图，当前 `jsonl_count=137`、`markdown_count=137`、`paired_count=134`、`unpaired_count=6`，并能定位本轮 manifest | `tools/knowledge-index-plan.sh` | Tool | `knowledge-hub-manifest-profile-index-plan-20260621` |
| `rtk bash tools/knowledge-check.sh --dry-run --json --diagnostics` | 0 | 通过；`status=pass`，0 errors、0 warnings，新增 manifest profile/template readability gate 未发现当前仓漂移 | `tools/knowledge-check.sh` | Tool | `knowledge-hub-manifest-profile-index-plan-20260621` |
| `rtk bash tools/knowledge-regression.sh --json` | 0 | 通过；66 个回归场景全部 pass，包含 `manifest-jsonl-profile-gate`、`template-readability-field-gate` 和 regression manifest 自检 | `tools/knowledge-regression.sh` | Tool | `knowledge-hub-manifest-profile-index-plan-20260621` |
| `rtk git diff --check` | 0 | 通过；未发现 whitespace error 或 conflict marker | Git | Tool | `knowledge-hub-manifest-profile-index-plan-20260621` |
| `rtk bash tools/knowledge-final-gate.sh --json` | 1 | 预期非零；`final_status=needs-owner-review`，核心检查全通过，`automatic_governance.status=complete-except-owner-review`，剩余 7 个 PCR02 owner gate 只能人工签收 | `tools/knowledge-final-gate.sh` | Tool | `knowledge-hub-manifest-profile-index-plan-20260621` |

## Review

- review_status: `manifest-profile-index-plan-applied`
- owner: `leiwenjun`
- review_after: `2026-09-21`
- promotion_decision: `none`
- evidence_strength: `subagent-review-plus-positive-negative-regression-and-final-gate`
