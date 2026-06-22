# Knowledge Hub final proof and maintenance hardening 2026-06-22

## 结论

本轮继续压实 Knowledge Hub 终态证明链和中文维护入口，处理 4 个互不冲突的自动治理切片：

- final gate Level 1 审计直接暴露 7 个 PCR02 owner gate 的来源、worksheet 行数和 owner-ready 覆盖数，避免把 `7/7` 当成不可解释常量。
- regression helper 自检从“ID 文本出现”升级为“覆盖范围表必须为每个回归 ID 提供唯一行，且场景和预期非空”。
- `knowledge-status --json` 增加 `sources.source_recovery_rows[]`，把 source registry 终态、review_after、final_disposition、check/no-check 契约和 latest coverage decision 合成一行，降低人工恢复成本。
- governance 文档和模板里的验证命令统一为 `rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics` 或稳定 `~/knowledge-hub` 入口，避免复制到裸命令、弱验证或依赖仓库 cwd 的命令。

## 变更范围

| 文件 | 变更 |
|---|---|
| `tools/knowledge-final-gate.sh` | `final_state_audit.level1_pcr02_docs` 增加 expected owner gate count、source、worksheet count、row count、owner-ready count 和 match flag。 |
| `tools/knowledge-status.sh` | `sources.source_recovery_rows[]` 合并 registry、source check health 和 latest coverage row 的恢复字段。 |
| `tools/knowledge-regression.sh` | 锁定 Level 1 owner gate provenance；增强 `regression-manifest-coverage` 表格结构自检；锁定 source recovery rows。 |
| `README.md`、`tools/README.md` | 同步终态审计字段、source recovery rows 和中文工具说明。 |
| `governance/*.md`、`templates/*.md` | 收敛可复制验证命令到 `rtk bash ~/knowledge-hub/... --diagnostics` 稳定入口。 |
| `artifacts/manifests/knowledge-hub-governance-regression-helper-20260619.md` | 更新 `regression-manifest-coverage` 的预期说明。 |

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
| `rtk bash -n tools/knowledge-final-gate.sh` | 0 | 通过；final gate 脚本语法检查通过。 | `tools/knowledge-final-gate.sh` | Tool | `knowledge-hub-final-proof-maintenance-hardening-20260622` |
| `rtk bash -n tools/knowledge-status.sh` | 0 | 通过；status dashboard 脚本语法检查通过。 | `tools/knowledge-status.sh` | Tool | `knowledge-hub-final-proof-maintenance-hardening-20260622` |
| `rtk bash -n tools/knowledge-regression.sh` | 0 | 通过；回归入口语法检查通过。 | `tools/knowledge-regression.sh` | Tool | `knowledge-hub-final-proof-maintenance-hardening-20260622` |
| `KNOWLEDGE_FINAL_GATE_INNER_REGRESSION=1 rtk bash tools/knowledge-final-gate.sh --json --as-of 2026-06-22` | 1 | 符合预期；final status 为 `needs-owner-review`，Level 1 审计暴露 expected owner gate count=7、worksheet row count=7、owner-ready count=7。 | `/tmp/kh-final-level1-provenance.json` | Final Gate | `knowledge-hub-final-proof-maintenance-hardening-20260622` |
| `rtk bash tools/knowledge-check.sh --dry-run --json --diagnostics --as-of 2026-06-22` | 0 | 通过；0 errors、0 warnings，source coverage latest 仍选择 `knowledge-hub-source-coverage-closeout-20260620.jsonl`，boundary health 为 pass。 | `tools/knowledge-check.sh` | Gate | `knowledge-hub-final-proof-maintenance-hardening-20260622` |
| `rtk bash tools/knowledge-status.sh --json --as-of 2026-06-22` | 0 | 通过；`sources.source_recovery_rows[]` 输出 13 条 source 恢复行，PCR02 docs/tools 均可一行恢复 final disposition、check/no-check 和 latest coverage decision。 | `tools/knowledge-status.sh` | Status | `knowledge-hub-final-proof-maintenance-hardening-20260622` |
| `rtk rg -n 'validation_refs：\`tools/knowledge-check.sh --dry-run\`|rtk bash tools/|rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run$|rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json$' governance templates README.md tools/README.md indexes/README.md` | 1 | 通过；无匹配项，说明治理/模板可复制验证命令已收敛到稳定 diagnostics 入口。 | `governance/`、`templates/`、`README.md`、`tools/README.md` | Readability Gate | `knowledge-hub-final-proof-maintenance-hardening-20260622` |
| `rtk bash tools/knowledge-regression.sh --json --as-of 2026-06-22` | 0 | 通过；85 个回归场景全部 pass，`regression-manifest-coverage` 确认 manifest 表格 85 行、无缺失、无重复、场景/预期列非空。 | `/tmp/kh-regression-proof-20260622.json` | Regression | `knowledge-hub-final-proof-maintenance-hardening-20260622` |
| `rtk git diff --check` | 0 | 通过；未发现 whitespace 或 conflict marker 问题。 | `git diff --check` | Git | `knowledge-hub-final-proof-maintenance-hardening-20260622` |
| `rtk bash tools/knowledge-final-gate.sh --json --as-of 2026-06-22` | 1 | 符合预期；final status 为 `needs-owner-review`，automatic governance 为 `complete-except-owner-review`，唯一 blocker 为 7 个 `owner-gates-open`。 | `/tmp/kh-final-proof-20260622.json` | Final Gate | `knowledge-hub-final-proof-maintenance-hardening-20260622` |

## 终态验证说明

本轮自动治理切片已完成工具、文档、索引和回归层验证。`knowledge-final-gate.sh` 仍返回非零，状态为 `needs-owner-review`；唯一 blocker 是 PCR02 owner decision worksheet 仍有 7 个 open gate。该 blocker 只能由真实 owner 复核并填写 owner decision 后关闭，本轮未代签、未关闭 gate、未提升 active。
