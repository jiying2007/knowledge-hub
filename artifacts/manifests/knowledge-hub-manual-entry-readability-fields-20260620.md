# Knowledge Hub manual entry readability fields 2026-06-20

## 结论

本轮把人工新增知识的只读入口和核心模板继续收敛到中文长期资产规则：新增条目草稿默认暴露中文摘要、语言、术语、review、证据强度、AI provenance 和人工待验证原因字段，避免后续人工复制时遗漏 `registry/schema.md` 推荐字段。

这不是 owner decision，不关闭 PCR02 owner gate，不把任何 PCR02 project-specific 内容提升到 `domains/embedded/standards/`，不修改源项目 docs，不启用自动化，也不写 memory。

## 变更范围

- `tools/knowledge-new.sh`
  - 普通 item 模式新增 `--manual-source-reason`、`--manual-validation-pending`、`--manual-validation-reason`、`--generated-by-ai`、`--ai-role`。
  - registry 草稿新增 `summary_zh`、`primary_language`、`source_language`、`translation_status`、`terminology_status`、`review_status`、`evidence_strength`、`evidence_refs` 和 AI provenance 字段。
  - `registry/items.jsonl` 明确为迁移、引用或归档时使用，普通新知识不强制新增 migration。
- `templates/item.md`、`templates/runbook.md`、`templates/decision.md`
  - 对齐 `summary_zh` / `primary_language` canonical 字段。
  - 补齐 review/evidence/AI provenance 字段。
  - 补齐 Evidence Index、风险与 Review 等长期资产章节。
- `README.md`、`tools/README.md`、`templates/README.md`
  - 同步人工新增入口、离线待验证、AI provenance 和 migration 条件化口径。
- `tools/knowledge-regression.sh`
  - 回归场景从 45 扩展到 50，覆盖人工字段、模板选择、migration 条件提示、模板章节和 source `--check` 分支。

## 风险与限制

- `manual_validation_pending: true` 只能表示待复核，不能替代命令验证。
- `generated_by_ai: true` 不能让条目进入 active；active 前仍必须满足人工复核字段和证据要求。
- `evidence_strength` 默认使用保守的 `manual-entry-pending-validation`，不伪装成人工已复核或 owner 已批准。
- source 模式仍只输出 registry/by-source/coverage 草稿，本轮没有扩展 source owner decision 语义。

## Evidence Index

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
|---|---:|---|---|---|---|
| `rtk bash tools/knowledge-new.sh --kind runbook --domain projects/pcr02 --owner team-core --id pcr02-readable-runbook --path domains/projects/pcr02/current/runbooks/readable.md --manual-source-reason field-debug --manual-validation-pending --manual-validation-reason "offline lab note awaiting rtk validation" --generated-by-ai --ai-role drafted` | 0 | 通过；输出中文长期资产字段、AI provenance 和人工待验证原因；不写文件。 | `tools/knowledge-new.sh` | Tool | `knowledge-hub-manual-entry-readability-fields-20260620` |
| `rtk bash tools/knowledge-regression.sh --json` | 0 | 通过；50 个回归场景全部 pass。 | `tools/knowledge-regression.sh` | Tool | `knowledge-hub-manual-entry-readability-fields-20260620` |
| `rtk bash tools/knowledge-check.sh --dry-run --json --diagnostics` | 0 | 通过；0 errors、0 warnings。 | `tools/knowledge-check.sh` | Tool | `knowledge-hub-manual-entry-readability-fields-20260620` |
| `rtk bash tools/knowledge-final-gate.sh --json` | 1 | 符合预期；`final_status=needs-owner-review`，`automatic_governance.status=complete-except-owner-review`，非 owner 检查全部通过，剩余 7 个 owner gates。 | `tools/knowledge-final-gate.sh` | Tool | `knowledge-hub-manual-entry-readability-fields-20260620` |

## 边界

- 不修改 PCR02 源项目 docs。
- 不关闭任何 owner gate。
- 不生成 owner decision。
- 不启用自动化写操作。
- 不写 `~/.codex/memories`。
