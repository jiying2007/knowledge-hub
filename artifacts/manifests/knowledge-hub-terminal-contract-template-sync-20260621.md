# Knowledge Hub terminal contract and template sync 2026-06-21

## 结论

本轮继续压实 Knowledge Hub 终态治理的长期维护面。当前 terminal final gate 仍应停在 `needs-owner-review`，并且唯一真实 blocker 仍是 PCR02 7 个 owner gate；本轮不生成 owner decision、不关闭 gate、不复制 PCR02 源正文。

本轮自动收口 4 类非 owner 风险：

- `knowledge-status.sh` 把 `knowledge-owner-gates.sh` 子命令非零退出提升为 `owner-gates-command-failed` blocker，避免 owner gate 工具失败时 status dashboard 被误用为终态证据。
- `knowledge-final-gate.sh` 把子命令 `exit 0` 但 stdout 为空的情况标记为 `empty JSON output`，避免静默成功被当作核心检查通过。
- `knowledge-new.sh` 的 AI 草稿在 `--generated-by-ai` 时自动带出 `ai_model_or_tool=Codex` 和 `ai_generated_at=<UTC date>`，避免生成后立刻触发 2026-06-21 AI provenance 门禁。
- 核心和专用模板统一补齐 `promotion_decision`、中文可读性字段、证据字段和 AI provenance 字段，并在 README/schema/template docs 中明确 `promotion` 与 `promotion_decision` 的边界。

## 改动范围

| 文件 | 改动 |
| --- | --- |
| `tools/knowledge-status.sh` | owner-gates 子命令非零退出进入 `needs-fix` 和 `owner-gates-command-failed` strict blocker；JSON 暴露 command、stderr_sample 和 parse_error。 |
| `tools/knowledge-final-gate.sh` | `run_json()` 对空 stdout 设置 `parse_error=empty JSON output`，由现有 unparseable blocker 处理。 |
| `tools/knowledge-regression.sh` | 新增 `status-owner-gates-exit-code-blocker`、`final-gate-empty-child-json-blocker`；回归自检用实际 result id 反查 required 清单，并覆盖 AI provenance / `promotion_decision` 字段。 |
| `tools/knowledge-new.sh` | AI 生成草稿补非空 provenance；人工新增说明明确 `promotion` 与 `promotion_decision` 不可混用。 |
| `templates/*.md` | 专用模板收敛到 `primary_language` / `source_language` / `translation_status` / `terminology_status`，补 AI provenance、证据字段和 `promotion_decision`。 |
| `README.md`、`templates/README.md`、`registry/schema.md` | 补中文维护说明，明确 `promotion_decision` 只是提升边界说明，不替代 owner decision 或 active gate。 |
| `artifacts/manifests/knowledge-hub-governance-regression-helper-20260619.md` | 回归场景说明从 61 更新到 63，并记录两个新负向契约。 |

## 回归契约

新增或加固的契约：

| ID | 类型 | 预期 |
| --- | --- | --- |
| `status-owner-gates-exit-code-blocker` | negative fixture | 临时副本中 owner-gates 输出可解析 JSON 但 exit 1 时，`knowledge-status --strict --json` 必须返回 `needs-fix` 并输出 `owner-gates-command-failed`。 |
| `final-gate-empty-child-json-blocker` | negative fixture | 临时副本中 child gate exit 0 但 stdout 为空时，final gate 必须返回 `needs-fix`，不能把空 JSON 输出当作通过。 |
| `regression-manifest-coverage` | self-check | 回归自检按实际 result id 反查 required 清单，避免漏登 ID 但靠固定数量文本通过。 |
| `manual-entry-readability-fields` | positive contract | `knowledge-new.sh --generated-by-ai` 草稿带非空 `ai_model_or_tool` 和 `ai_generated_at`。 |
| `templates-required-sections` | positive contract | 核心模板包含 `promotion_decision` 与长期可读性 / provenance 字段。 |

## Evidence Index

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
| --- | ---: | --- | --- | --- | --- |
| `rtk bash -n tools/knowledge-status.sh` | 0 | 通过；status dashboard shell 语法有效。 | `tools/knowledge-status.sh` | Tool | `knowledge-hub-terminal-contract-template-sync-20260621` |
| `rtk bash -n tools/knowledge-final-gate.sh` | 0 | 通过；final gate shell 语法有效。 | `tools/knowledge-final-gate.sh` | Tool | `knowledge-hub-terminal-contract-template-sync-20260621` |
| `rtk bash -n tools/knowledge-regression.sh` | 0 | 通过；regression shell 语法有效。 | `tools/knowledge-regression.sh` | Tool | `knowledge-hub-terminal-contract-template-sync-20260621` |
| `rtk bash -n tools/knowledge-new.sh` | 0 | 通过；manual entry guide shell 语法有效。 | `tools/knowledge-new.sh` | Tool | `knowledge-hub-terminal-contract-template-sync-20260621` |
| `rtk bash tools/knowledge-new.sh --kind runbook --domain projects/pcr02 --owner team-core --id pcr02-readable-runbook --path domains/projects/pcr02/current/runbooks/readable.md --manual-source-reason field-debug --manual-validation-pending --manual-validation-reason "offline lab note awaiting rtk validation" --generated-by-ai --ai-role drafted` | 0 | 通过；草稿带 `promotion_decision`、`ai_model_or_tool=Codex` 和 `ai_generated_at=2026-06-21`，无 here-doc 字段名命令替换噪音。 | `tools/knowledge-new.sh` | Tool | `knowledge-hub-terminal-contract-template-sync-20260621` |
| `rtk bash tools/knowledge-status.sh --json` | 0 | 通过；当前仍为 `needs-owner-review`，owner-gates 子命令 exit 0、parse_error 为空，7 个 owner gate 全部 open 且 active exposure 为 0。 | `tools/knowledge-status.sh` | Tool | `knowledge-hub-terminal-contract-template-sync-20260621` |
| `rtk bash tools/knowledge-regression.sh --json` | 0 | 通过；63 个回归场景全部 pass，新增 `status-owner-gates-exit-code-blocker`、`final-gate-empty-child-json-blocker` 和自检反查契约均通过。 | `tools/knowledge-regression.sh` | Tool | `knowledge-hub-terminal-contract-template-sync-20260621` |
| `rtk bash tools/knowledge-check.sh --dry-run --json --diagnostics` | 0 | 通过；0 errors / 0 warnings，确认 registry、migration、index、模板和 manifest 登记一致。 | `tools/knowledge-check.sh` | Tool | `knowledge-hub-terminal-contract-template-sync-20260621` |
| `rtk git diff --check` | 0 | 通过；当前 diff 无空白或补丁格式问题。 | Git diff | Tool | `knowledge-hub-terminal-contract-template-sync-20260621` |
| `rtk bash tools/knowledge-final-gate.sh --json` | 1 | 预期阻断；`final_status=needs-owner-review`、`automatic_governance.status=complete-except-owner-review`、`knowledge_regression.result_count=63`，唯一 blocker 为 `owner-gates-open`。 | `tools/knowledge-final-gate.sh` | Tool | `knowledge-hub-terminal-contract-template-sync-20260621` |

## 边界

- 不生成 owner decision。
- 不关闭 PCR02 owner gate。
- 不修改 PCR02 源项目 docs、tools、knowledge、app_product_test、scratch 或源码树。
- 不复制 `.env`、PDF、zip/tgz、bin、patch、log、C/C++、Python、shell 脚本正文。
- 不把 PCR02 project-specific 内容提升到 `domains/embedded/standards/`。
- 不启用自动化写操作，不写 `~/.codex/memories`。
- `promotion_decision` 只记录提升边界说明，不替代 `promotion` 枚举、owner decision、active review 或 team-level promotion gate。
