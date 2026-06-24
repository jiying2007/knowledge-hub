# Knowledge Sources

| Source | Role | Path |
| --- | --- | --- |
| embedded-knowledge | team-knowledge-source | `~/embedded/knowledge` |
| engineering-archive | project-archive-source | `~/embedded/engineering_archive` |
| patent-disclosure | patent-source | `~/embedded/patent_disclosure` |
| codex-archive | codex-governance-source | `~/codex/docs/archive` |
| codex-memories | auxiliary-memory-source | `~/.codex/memories` |
| codex-history | codex-history-source | `~/.codex/history.jsonl` |
| codex-raw-sessions | codex-session-source | `~/.codex/sessions` |
| codex-session-index | codex-session-source | `~/.codex/session_index.jsonl` |
| codex-archive-registry | codex-archive-registry-source | `~/codex/docs/archive/_registry` |
| knowledge-hub-automation-runs | codex-automation-source | `registry/automation-runs.jsonl` |
| pcr02-project-docs | project-current-docs-source | `~/work/sigmastar/pcr02_ssc305/SourceCode/sdk/verify/xcrz_sigmastar_demo/docs` |
| pcr02-project-tools | project-current-tools-source | `~/work/sigmastar/pcr02_ssc305/SourceCode/sdk/verify/xcrz_sigmastar_demo/tools` |
| pcr02-project-knowledge | project-current-knowledge-source | `~/work/sigmastar/pcr02_ssc305/SourceCode/sdk/verify/xcrz_sigmastar_demo/knowledge` |
| pcr02-product-test | project-product-test-source | `~/work/sigmastar/pcr02_ssc305/SourceCode/sdk/verify/xcrz_sigmastar_demo/app_product_test` |
| pcr02-project-scratch | project-scratch-source | `~/work/sigmastar/pcr02_ssc305/SourceCode/sdk/verify/xcrz_sigmastar_demo/scratch` |
| pcr02-project-root-artifacts | project-root-artifact-source | `~/work/sigmastar/pcr02_ssc305/SourceCode/sdk/verify/xcrz_sigmastar_demo` |
| pcr02-module-agent-rules | project-agent-rules-source | `~/work/sigmastar/pcr02_ssc305/SourceCode/sdk/verify/xcrz_sigmastar_demo` |
| pcr02-project-agent-config | project-agent-config-source | `~/work/sigmastar/pcr02_ssc305/SourceCode/sdk/verify/xcrz_sigmastar_demo` |

## PCR02 Source 边界速查

下表是 `registry/sources.json` 的人工可读摘要，只用于快速恢复 PCR02 source 的 owner、复核时间和最终治理边界；权威字段仍以 registry 为准。

| Source | Owner | Review After | Final Disposition | Boundary |
| --- | --- | --- | --- | --- |
| pcr02-project-docs | pcr02-registry-owner | 2026-09-20 | mixed-terminal-coverage | copy/reference/artifact/owner-gated 混合覆盖；7 个 owner gate 不得代签关闭 |
| pcr02-project-tools | pcr02-registry-owner | 2026-09-20 | mixed-terminal-coverage | tool/diag/memory automation 只做 reference/report-only 边界，不写源项目 |
| pcr02-project-knowledge | pcr02-registry-owner | 2026-09-20 | mixed-terminal-coverage | classify-first、secret/config/tool-ref 边界，不提升 active |
| pcr02-product-test | pcr02-registry-owner | 2026-09-20 | mixed-terminal-coverage | artifact/config/interface 只做身份和引用登记，不复制大附件或构建物 |
| pcr02-project-scratch | pcr02-registry-owner | 2026-09-20 | archive-only-registered | scratch/session/resume archive-only，不写 memory，不进 active facts |
| pcr02-project-root-artifacts | pcr02-registry-owner | 2026-09-20 | mixed-terminal-coverage | root loose artifact/tool/config 边界，排除子 source 和生成物 |
| pcr02-module-agent-rules | pcr02-registry-owner | 2026-09-20 | owner-gated-pending-decision | module/local AGENTS 规则保持 owner-gated reference，不升级全局规则 |
| pcr02-project-agent-config | pcr02-registry-owner | 2026-09-20 | artifact-ref-registered | `.vscode`/`.kilo` 配置和 report-only 自动化只做 artifact/config ref |

## Source 治理恢复

本索引主表只保留 source id、role 和 path，避免和 `registry/sources.json` 重复维护。需要恢复 owner、review_after、authority、write_policy、migration_strategy、final_disposition、check/no_check_reason、coverage 和 migration refs 时，运行：

```bash
rtk bash ~/knowledge-hub/tools/knowledge-index-plan.sh --section source
rtk bash ~/knowledge-hub/tools/knowledge-index-plan.sh --section source --json
```

`knowledge-index-plan` 只读输出 planned 视图，不写 registry、index、owner decision、memory，也不关闭 owner gate。

- 最新 source check 文档、边界和搜索限制：`artifacts/manifests/knowledge-hub-source-check-docs-search-limit-20260621.md`。
- 最新 final gap 可读性和索引硬化：`artifacts/manifests/knowledge-hub-final-gap-readability-index-20260621.md`。
- 最新 owner dispatch、可读性和 source scan 同步：`artifacts/manifests/knowledge-hub-owner-dispatch-readability-sync-20260621.md`。
- 最新 status dispatch、owner recovery 和 AI provenance 同步：`artifacts/manifests/knowledge-hub-status-dispatch-notes-zh-20260621.md`。
- 最新 terminal contract、AI provenance 和模板同步：`artifacts/manifests/knowledge-hub-terminal-contract-template-sync-20260621.md`。
- 最新 as-of、source coverage selection/health 契约：`artifacts/manifests/knowledge-hub-asof-coverage-contract-20260621.md`。
- 最新 final gate regression skip blocker：`artifacts/manifests/knowledge-hub-final-gate-regression-skip-blocker-20260621.md`。
- 最新 manual entry 模板和 source 边界同步：`artifacts/manifests/knowledge-hub-manual-entry-source-boundary-sync-20260621.md`。
- 最新 manual/offline 恢复和 PCR02 可读边界同步：`artifacts/manifests/knowledge-hub-manual-recovery-boundary-hardening-20260621.md`。
- 最新 source check 快照证据和核心索引可读性硬化：`artifacts/manifests/knowledge-hub-source-check-snapshot-evidence-readability-20260622.md`。
- 最新 owner/source/subagent 边界加固：`artifacts/manifests/knowledge-hub-owner-source-subagent-boundary-hardening-20260623.md`。
- 最新 source 主控目录统一收口：`artifacts/manifests/knowledge-hub-source-control-unification-20260624.md`。
- 每个 registered source 的 Hub 内管理面位于 sources/<source_id>/，至少包含 `README.md`、`inventory.jsonl`、`coverage.md`、`migration-plan.md`。

## Source 专项审查制品

- `pcr02-project-docs/runbooks/asan-debug-guide.md`: ASAN 拆分目标证据：`artifacts/manifests/pcr02-asan-split-targets-20260618.md`。
- `pcr02-project-docs/runbooks/asan-debug-guide.md owner-ready package`: 单项 owner 签收材料：`artifacts/manifests/pcr02-asan-owner-ready-package-20260620.md`。
- `pcr02-project-docs/runbooks/memory-auto-curation-guide.md`: report-only 治理证据：`artifacts/manifests/memory-auto-curation-report-only-governance-20260618.md`。
- `pcr02-project-docs/runbooks/memory-auto-curation-guide.md owner-ready package`: 单项 owner 签收材料：`artifacts/manifests/pcr02-memory-auto-curation-owner-ready-package-20260620.md`。
- `pcr02-project-docs/plans/2026-06-15-dvr-record-proto-sensor-decoupling-plan.md`: owner-gated DVR plan 收口证据：`artifacts/manifests/pcr02-dvr-motor-closeout-targets-20260618.md`。
- `pcr02-project-docs/plans/2026-06-15-dvr-record-proto-sensor-decoupling-plan.md owner-ready package`: 单项 owner 签收材料：`artifacts/manifests/pcr02-dvr-plan-owner-ready-package-20260620.md`。
- `pcr02-project-docs/reports/2026-05-29-motor-mcu-debug-record.md`: motor MCU 事实拆分和 archive-only 边界：`artifacts/manifests/pcr02-dvr-motor-closeout-targets-20260618.md`。
- `pcr02-project-docs/reports/2026-05-29-motor-mcu-debug-record.md owner-ready package`: 单项 owner 签收材料：`artifacts/manifests/pcr02-motor-mcu-owner-ready-package-20260620.md`。
- `pcr02-project-docs/reports/2026-06-16-dvr-record-replay-session-archive.md`: DVR session archive-only 元数据和 memory-candidate 排除：`artifacts/manifests/pcr02-dvr-motor-closeout-targets-20260618.md`。
- `pcr02-project-docs/reports/2026-06-16-dvr-record-replay-session-archive.md owner-ready package`: 单项 owner 签收材料：`artifacts/manifests/pcr02-dvr-session-archive-owner-ready-package-20260620.md`。
- `pcr02-project-docs/AGENTS.md`: PCR02 project-local docs rule owner gate：`artifacts/manifests/pcr02-remaining-owner-gates-20260618.md`。
- `pcr02-project-docs/AGENTS.md owner-ready package`: 单项 owner 签收材料：`artifacts/manifests/pcr02-agents-owner-ready-package-20260620.md`。
- `pcr02-project-docs/standards/diag-command-metadata-standard.md`: PCR02 diag metadata owner/gate 证据边界：`artifacts/manifests/pcr02-remaining-owner-gates-20260618.md`。
- `pcr02-project-docs/standards/diag-command-metadata-standard.md owner-ready package`: 单项 owner 签收材料：`artifacts/manifests/pcr02-diag-owner-ready-package-20260620.md`。
- `pcr02-project-docs`: 32/32 docs 治理覆盖和 registry/index 收口：`artifacts/manifests/pcr02-docs-governance-closeout-20260618.md`。
- `pcr02-project-docs owner gates`: owner decision action board：`artifacts/manifests/pcr02-owner-action-board-20260618.md`。
- `pcr02-project-docs owner intake`: 中文 owner 签收字段和 hard-gate 问题：`artifacts/manifests/pcr02-owner-intake-package-20260618.md`。
- `pcr02-project-docs owner-gated source identity`: 当前 source SHA256/size preflight：`artifacts/manifests/pcr02-owner-source-identity-preflight-20260618.md`。
- `pcr02-project-docs owner form source identity validation`: owner 表单拒绝过期 SHA256/size：`artifacts/manifests/knowledge-hub-owner-source-identity-validation-20260620.md`。
- `pcr02-project-docs owner target and landing validation`: owner 表单 target decision、guardrail 和 worksheet 验证命令：`artifacts/manifests/knowledge-hub-owner-target-landing-validation-20260621.md`。
- `pcr02-project-docs owner-ready command stability`: owner-ready 和 terminal status 命令使用 `~/knowledge-hub/tools` 稳定入口：`artifacts/manifests/knowledge-hub-owner-ready-command-stability-20260621.md`。
- `pcr02-project-docs final gap/readability recovery`: terminal typed gap、governance readability gate 和 latest index 锚点：`artifacts/manifests/knowledge-hub-final-gap-readability-index-20260621.md`。
- `pcr02-project-docs owner dispatch/readability sync`: owner_dispatch 分派包、中文维护字段和 source scan no-drift 证据：`artifacts/manifests/knowledge-hub-owner-dispatch-readability-sync-20260621.md`。
- `pcr02-project-docs status dispatch/owner recovery sync`: status dashboard、final gate owner_recovery、owner landing cwd 和 AI provenance gate：`artifacts/manifests/knowledge-hub-status-dispatch-notes-zh-20260621.md`。
- `pcr02-project-docs final maintenance/linking audit`: final gate 维护入口审计和 index-plan 关联恢复审计：`artifacts/manifests/knowledge-hub-maintenance-linking-audit-hardening-20260622.md`。
- `knowledge-hub source coverage selection/health`: latest source coverage selection 和 pass-state coverage health：`artifacts/manifests/knowledge-hub-asof-coverage-contract-20260621.md`。
- `pcr02-project-docs owner routing recovery`: owner decision role routing 和 status/final-gate owner_route 恢复：`artifacts/manifests/knowledge-hub-owner-routing-recovery-20260621.md`。
- `pcr02-project-docs owner landing audit and manual index recovery`: owner landing audit、worksheet/manual index 落点和 manifest unpaired 分类：`artifacts/manifests/knowledge-hub-owner-landing-audit-manual-index-20260621.md`。
- `pcr02-project-docs source check and boundary health`: source check/no-check 静态契约和 PCR02 Level 2 boundary 内部证据链：`artifacts/manifests/knowledge-hub-source-boundary-health-20260621.md`。
- `pcr02-project-docs owner resolution`: owner decision landing 规则：`artifacts/manifests/pcr02-owner-resolution-playbook-20260618.md`。
- `pcr02-project-docs owner resolution schema`: owner decision 字段、枚举和非法组合：`artifacts/manifests/pcr02-owner-resolution-schema-20260618.md`。
- `pcr02-project-docs owner decision landing`: 7 条 owner gate 人工授权决策落地：`artifacts/manifests/pcr02-project-docs-owner-decision-landing-20260623.md`。
- `pcr02-project-docs source control`: Hub 内 source 主控目录：`sources/pcr02-project-docs/README.md`、`sources/pcr02-project-docs/inventory.jsonl`、`sources/pcr02-project-docs/coverage.md`、`sources/pcr02-project-docs/migration-plan.md`。
- `pcr02-project-docs ASAN owner target`: `projects/pcr02/current/runbooks/asan-debug-guide.md`，registry item `pcr02-asan-debug-guide-project-local-20260624`。
- `pcr02-project-docs DVR plan owner target`: `projects/pcr02/archive/plans/2026-06-15-dvr-record-proto-sensor-decoupling-plan.md`，registry item `pcr02-dvr-plan-archive-only-20260624`。
- `pcr02-project-docs motor MCU owner target`: `projects/pcr02/archive/reports/2026-05-29-motor-mcu-debug-record.md`，registry item `pcr02-motor-mcu-debug-record-archive-only-20260624`。
- `pcr02-project-docs DVR session owner target`: `projects/pcr02/archive/reports/2026-06-16-dvr-record-replay-session-archive.md`，registry item `pcr02-dvr-session-archive-only-20260624`。
- `pcr02-project-docs governance closeout`: 可恢复 handoff：`artifacts/manifests/pcr02-governance-handoff-20260618.md`。
- `registry/items.jsonl`、`registry/migrations.jsonl`、`indexes/by-*.md`: PCR02 control-plane closeout audit：`artifacts/manifests/pcr02-docs-governance-closeout-20260618.md`。
- `codex-memories`: 仅作为辅助召回；memory auto-curation governance 不得写 `~/.codex/memories/**`。
- `codex-history`: Hub 主库历史来源；只做索引、摘要和候选治理，不把 raw history 行直接提升为 active fact。
- `codex-raw-sessions`: Hub 主库 raw session 来源；只做引用、摘要和证据定位，不复制完整 raw session 正文。
- `codex-session-index`: Hub 主库 session 恢复索引；用于跨项目、跨会话串联 project/workstream/session。
- `codex-archive-registry`: Hub 主库吸收 Codex archive registry；用于迁移项目、topic、session 和 workstream 索引。
- `knowledge-hub-automation-runs`: Hub 内自动化运行账本；用于串联 automation、authorization、project、session、source 和验证证据。
- `engineering-archive`: 38 PCR02 historical engineering archive files were copy-first migrated to `projects/pcr02/archive/engineering-archive` and verified by `artifacts/manifests/engineering-archive-copy-first-applied-20260619.md`.
- `patent-disclosure`: 10 Markdown patent disclosure files were copy-first migrated to `domains/patents/archive/patent-disclosure`; 181 non-text attachments are registered by `artifacts/manifests/patent-disclosure-artifact-ref-20260619.jsonl` and summarized in `domains/patents/artifacts/patent-disclosure-artifacts.ref.md`.
- `embedded-knowledge`: 外部 legacy team SSOT，等待 owner review 和 source 稳定；source coverage 边界：`artifacts/manifests/knowledge-hub-source-coverage-closeout-20260619.md`。
- `codex-archive`: 通过 Codex archive 工具保持 reference-first；边界：`domains/codex/archive/codex-archive.ref.md` 和 `artifacts/manifests/knowledge-hub-source-coverage-closeout-20260619.md`。
- `pcr02-project-tools`: tool/diag/memory automation source coverage：`artifacts/manifests/knowledge-hub-source-coverage-closeout-20260620.md`。
- `pcr02-project-tools`: README/AGENTS、diag、runtime diagnostic、memory automation 和生成制品边界：`artifacts/manifests/pcr02-tools-boundary-20260620.md`。
- `pcr02-project-tools`: 18 个非生成 tool 文件的 source identity：`artifacts/manifests/pcr02-p1-source-identity-20260621.md`。
- `pcr02-project-tools`: report-only source check 执行快照：`artifacts/manifests/pcr02-level2-source-check-execution-snapshot-20260621.md`。
- `pcr02-project-knowledge`: classify-first、secret-boundary 和 tool/artifact boundary coverage：`artifacts/manifests/knowledge-hub-source-coverage-closeout-20260620.md`。
- `pcr02-project-knowledge`: env/config、项目本地规则、runbook、standards-like doc、治理工具和 skill 资产边界：`artifacts/manifests/pcr02-knowledge-secret-config-boundary-20260620.md`。
- `pcr02-project-knowledge`: report-only source check 执行快照：`artifacts/manifests/pcr02-level2-source-check-execution-snapshot-20260621.md`。
- `pcr02-product-test`: product-test artifact/config/interface boundary coverage：`artifacts/manifests/knowledge-hub-source-coverage-closeout-20260620.md`。
- `pcr02-product-test`: Markdown、PDF/archive、config、C/C++ reference 和 build artifact 边界：`artifacts/manifests/pcr02-product-test-artifact-config-interface-boundary-20260620.md`。
- `pcr02-product-test`: 73 个非生成 artifact/config/interface 文件的 source identity：`artifacts/manifests/pcr02-product-test-artifact-config-interface-identity-20260621.md`。
- `pcr02-product-test`: report-only source check 执行快照：`artifacts/manifests/pcr02-level2-source-check-execution-snapshot-20260621.md`。
- `pcr02-project-scratch`: archive-only/no-memory-write coverage：`artifacts/manifests/knowledge-hub-source-coverage-closeout-20260620.md`。
- `pcr02-project-scratch`: session/context/resume archive-only 边界：`artifacts/manifests/pcr02-scratch-archive-boundary-20260620.md`。
- `pcr02-project-scratch`: 8 个 scratch Markdown session/context/resume 文件的 source identity：`artifacts/manifests/pcr02-p2-archive-rule-identity-20260621.md`。
- `pcr02-project-scratch`: report-only source check 执行快照：`artifacts/manifests/pcr02-level2-source-check-execution-snapshot-20260621.md`。
- `pcr02-project-root-artifacts`: root loose artifact/tool boundary coverage：`artifacts/manifests/knowledge-hub-source-coverage-closeout-20260620.md`。
- `pcr02-project-root-artifacts`: root loose artifact/tool/config 边界和历史/当前数量漂移：`artifacts/manifests/pcr02-root-artifacts-boundary-20260620.md`。
- `pcr02-project-root-artifacts`: 16 个当前 root loose 文件的 source identity：`artifacts/manifests/pcr02-p1-source-identity-20260621.md`。
- `pcr02-project-root-artifacts`: report-only source check 执行快照：`artifacts/manifests/pcr02-level2-source-check-execution-snapshot-20260621.md`。
- `pcr02-module-agent-rules`: module-local owner-gated rule coverage：`artifacts/manifests/knowledge-hub-source-coverage-closeout-20260620.md`。
- `pcr02-module-agent-rules`: AGENTS/local rule owner-gated 边界：`artifacts/manifests/pcr02-module-agent-rules-boundary-20260620.md`。
- `pcr02-module-agent-rules`: 8 个 module/project/local AGENTS 文件的 source identity：`artifacts/manifests/pcr02-p2-archive-rule-identity-20260621.md`。
- `pcr02-module-agent-rules`: report-only source check 执行快照：`artifacts/manifests/pcr02-level2-source-check-execution-snapshot-20260621.md`。
- `pcr02-project-agent-config`: config/artifact-ref 和 report-only automation boundary coverage：`artifacts/manifests/knowledge-hub-source-coverage-closeout-20260620.md`。
- `pcr02-project-agent-config`: `.vscode`/`.kilo` config、artifact 和 report-only automation 边界：`artifacts/manifests/pcr02-agent-config-boundary-20260620.md`。
- `pcr02-project-agent-config`: 10 个 `.vscode`/`.kilo` config/package 文件的 source identity：`artifacts/manifests/pcr02-p1-source-identity-20260621.md`。
- `pcr02-project-agent-config`: report-only source check 执行快照：`artifacts/manifests/pcr02-level2-source-check-execution-snapshot-20260621.md`。
- `registered sources`: 当前 source coverage matrix 和 terminal boundaries：`artifacts/manifests/knowledge-hub-source-coverage-closeout-20260620.md`。
