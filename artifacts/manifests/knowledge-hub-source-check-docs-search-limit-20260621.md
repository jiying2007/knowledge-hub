# Knowledge Hub source check docs, guardrails and index visibility 2026-06-21

## 结论

本轮继续压实 Knowledge Hub 终态维护入口，完成四个非 owner 冲突切片：

1. source 新增文档与 `knowledge-new.sh --help` 对齐上一轮 `--check` 优先路径。
2. `knowledge-new.sh --source` 强制 `--check` 与 `--no-check-reason` 二选一，避免生成无检查证据或冲突证据的 source coverage 草稿。
3. `knowledge-index-plan.sh --section source` 在 source 视图中暴露最新 coverage 的 `decision` 和 `risk`，让人工维护者能直接看到 source coverage 状态边界。
4. `knowledge-search.sh` 拒绝非正 `--limit`，避免人工误传 `0` 或负数时得到低信号搜索结果。

这些改动不改变 PCR02 owner gate 状态，不生成 owner decision，不修改 PCR02 源项目文件。

## 变更范围

- `tools/knowledge-search.sh`
  - 增加 `--limit >= 1` 参数校验。
- `tools/knowledge-new.sh`
  - help 示例新增 `--source ... --check "rtk bash tools/knowledge-check.sh --dry-run"`。
  - source 模式要求 `--check` / `--no-check-reason` 二选一。
  - source 模式拒绝二者同时传入，防止草稿证据语义冲突。
- `tools/knowledge-index-plan.sh`
  - source JSON 视图中的 coverage 对象补 `risk`。
  - source 文本视图补 `coverage decision` 和 `coverage risk`。
- `README.md`
  - 新增 source 维护路径把 `--check` 示例放在 `--no-check-reason` 之前。
  - 明确有稳定检查命令时 registry source object 和 source coverage JSONL row 草稿都记录 `check`，不再补 JSON 形式的 `no_check_reason`。
- `tools/README.md`
  - 同步 source `--check` 优先路径和 `no_check_reason` fallback 口径。
- `tools/knowledge-regression.sh`
  - 新增 `source-manual-entry-docs-check-preferred` 场景。
  - 新增 `source-manual-entry-requires-check-or-reason` 场景。
  - 扩展 `index-plan-extended-sections`，覆盖 source coverage `decision` / `risk`。
  - 扩展 `knowledge-search-invalid-filters`，覆盖 `--limit 0`。
- `artifacts/manifests/knowledge-hub-governance-regression-helper-20260619.md`
  - 回归场景数更新为 52。
  - 补 source check 文档优先路径、source 二选一、index-plan coverage decision/risk 和 search limit 负向场景说明。

## 边界

- 不新增 source。
- 不修改 `registry/sources.json`。
- 不修改 PCR02 源项目 docs / tools / knowledge / app_product_test / scratch / source tree。
- 不生成 owner decision，不关闭 owner gate。
- 不启用自动化写操作，不写 memory。

## Evidence Index

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
|---|---:|---|---|---|---|
| `rtk bash -n tools/knowledge-search.sh` | 0 | 通过；搜索入口语法有效。 | `tools/knowledge-search.sh` | Tool | `knowledge-hub-source-check-docs-search-limit-20260621` |
| `rtk bash -n tools/knowledge-new.sh` | 0 | 通过；人工新增向导语法有效。 | `tools/knowledge-new.sh` | Tool | `knowledge-hub-source-check-docs-search-limit-20260621` |
| `rtk bash -n tools/knowledge-index-plan.sh` | 0 | 通过；索引规划入口语法有效。 | `tools/knowledge-index-plan.sh` | Tool | `knowledge-hub-source-check-docs-search-limit-20260621` |
| `rtk bash -n tools/knowledge-regression.sh` | 0 | 通过；回归入口语法有效。 | `tools/knowledge-regression.sh` | Tool | `knowledge-hub-source-check-docs-search-limit-20260621` |
| `rtk bash tools/knowledge-search.sh "Knowledge Hub" --limit 0` | 2 | 预期失败；输出 `--limit must be >= 1`，证明非正 limit 不会静默退化。 | `tools/knowledge-search.sh` | Tool | `knowledge-hub-source-check-docs-search-limit-20260621` |
| `rtk bash tools/knowledge-new.sh --help` | 0 | 通过；help 同时展示 source `--check` 示例和 `--no-check-reason` fallback。 | `tools/knowledge-new.sh` | Tool | `knowledge-hub-source-check-docs-search-limit-20260621` |
| `rtk bash tools/knowledge-new.sh --source --source-id demo --source-path /tmp/demo --role project-current-docs-source --authority legacy-project-current-docs --write-policy read-only-unless-explicitly-approved` | 2 | 预期失败；输出 `requires either --check`，证明 source 草稿不能缺少检查命令或 no-check 原因。 | `tools/knowledge-new.sh` | Tool | `knowledge-hub-source-check-docs-search-limit-20260621` |
| `rtk bash tools/knowledge-new.sh --source --source-id demo --source-path /tmp/demo --role project-current-docs-source --authority legacy-project-current-docs --write-policy read-only-unless-explicitly-approved --check "rtk bash tools/knowledge-check.sh --dry-run" --no-check-reason "pending"` | 2 | 预期失败；输出 `cannot combine --check with --no-check-reason`，证明 source 草稿不会产生冲突证据。 | `tools/knowledge-new.sh` | Tool | `knowledge-hub-source-check-docs-search-limit-20260621` |
| `rtk bash tools/knowledge-regression.sh --json` | 1 | 负结果；新增 `source-manual-entry-docs-check-preferred` 首次失败，指出 `tools/README.md` 缺少统一口径“优先使用稳定只读”。 | `tools/README.md` | Tool | `knowledge-hub-source-check-docs-search-limit-20260621` |
| `rtk bash tools/knowledge-regression.sh --json` | 0 | 通过；52 个回归场景全部 pass，覆盖 source check 文档优先路径、source 二选一、index-plan coverage decision/risk 和 search invalid limit。 | `tools/knowledge-regression.sh` | Tool | `knowledge-hub-source-check-docs-search-limit-20260621` |
| `rtk bash tools/knowledge-check.sh --dry-run --json --diagnostics` | 0 | 通过；0 errors、0 warnings，确认 registry、index、manifest 登记一致。 | `tools/knowledge-check.sh` | Tool | `knowledge-hub-source-check-docs-search-limit-20260621` |
| `rtk git diff --check` | 0 | 通过；无 whitespace 或 patch 格式问题。 | `git diff` | Repo | `knowledge-hub-source-check-docs-search-limit-20260621` |
| `rtk bash tools/knowledge-final-gate.sh --json` | 1 | 预期终态；`final_status=needs-owner-review`，`automatic_governance.status=complete-except-owner-review`，核心检查和 52 个回归场景通过，剩余 7 个 PCR02 owner gate 未签收。 | `tools/knowledge-final-gate.sh` | Workflow | `knowledge-hub-source-check-docs-search-limit-20260621` |

## 最终验证

提交前已完成终态门禁复核：

- `rtk bash tools/knowledge-check.sh --dry-run --json --diagnostics`
- `rtk bash tools/knowledge-regression.sh --json`
- `rtk git diff --check`
- `rtk bash tools/knowledge-final-gate.sh --json`

当前预期终态仍是 `needs-owner-review`：Codex 自动治理已闭环，剩余事项是 7 个 PCR02 owner decision worksheet 的人工语义签收。
