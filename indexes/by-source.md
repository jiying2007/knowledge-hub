# Knowledge Sources

| Source | Status | Hub Path | Current Policy |
| --- | --- | --- | --- |
| embedded-knowledge | retired | `sources/embedded-knowledge` | Hub-only source control |
| engineering-archive | retired | `sources/engineering-archive` | Hub-only source control |
| patent-disclosure | retired | `sources/patent-disclosure` | Hub-only source control |
| codex-archive | retired | `sources/codex-archive` | Hub-only source control |
| codex-memories | runtime input | `sources/codex-memories` | runtime input, not copied, not deleted |
| codex-history | runtime input | `sources/codex-history` | runtime input, not copied, not deleted |
| codex-raw-sessions | runtime input | `sources/codex-raw-sessions` | runtime input, not copied, not deleted |
| codex-session-index | runtime input | `sources/codex-session-index` | runtime input, not copied, not deleted |
| codex-archive-registry | retired | `sources/codex-archive-registry` | Hub-only source control |
| knowledge-hub-automation-runs | hub-native | `sources/knowledge-hub-automation-runs` | Hub native ledger |
| pcr02-project-docs | retired | `sources/pcr02-project-docs` | Hub-only source control |
| pcr02-project-tools | retired | `sources/pcr02-project-tools` | Hub-only source control |
| pcr02-project-knowledge | retired | `sources/pcr02-project-knowledge` | Hub-only source control |
| pcr02-product-test | retired | `sources/pcr02-product-test` | Hub-only source control |
| pcr02-project-scratch | retired | `sources/pcr02-project-scratch` | Hub-only source control |
| pcr02-project-root-artifacts | retired | `sources/pcr02-project-root-artifacts` | Hub-only source control |
| pcr02-module-agent-rules | retired | `sources/pcr02-module-agent-rules` | Hub-only source control |
| pcr02-project-agent-config | retired | `sources/pcr02-project-agent-config` | config not deleted; active source path retired |

## PCR02 Source 边界速查

下表是 `registry/sources.json` 的人工可读摘要，只用于快速恢复 PCR02 source 的 owner、复核时间和最终治理边界；权威字段仍以 registry 为准。

| Source | Owner | Review After | Final Disposition | Boundary |
| --- | --- | --- | --- | --- |
| pcr02-project-docs | pcr02-registry-owner | 2026-09-20 | mixed-terminal-coverage | copy/reference/artifact/owner decision landing 混合覆盖；7 个 owner gate 已按 2026-06-23 landing 收口 |
| pcr02-project-tools | pcr02-registry-owner | 2026-09-20 | mixed-terminal-coverage | tool/diag/memory automation 只做 reference/report-only 边界，不写源项目 |
| pcr02-project-knowledge | pcr02-registry-owner | 2026-09-20 | mixed-terminal-coverage | classify-first、secret/config/tool-ref 边界，不提升 active |
| pcr02-product-test | pcr02-registry-owner | 2026-09-20 | mixed-terminal-coverage | artifact/config/interface 只做身份和引用登记，不复制大附件或构建物 |
| pcr02-project-scratch | pcr02-registry-owner | 2026-09-20 | archive-only-registered | scratch/session/resume archive-only，不写 memory，不进 active facts |
| pcr02-project-root-artifacts | pcr02-registry-owner | 2026-09-20 | mixed-terminal-coverage | root loose artifact/tool/config 边界，排除子 source 和生成物 |
| pcr02-module-agent-rules | pcr02-registry-owner | 2026-09-20 | hard-migrated-to-hub | module/local AGENTS 规则进入 Hub source control；未签收前不升级全局规则 |
| pcr02-project-agent-config | pcr02-registry-owner | 2026-09-20 | artifact-ref-registered | `.vscode`/`.kilo` 配置和 report-only 自动化只做 artifact/config ref |

## Source 治理恢复

本索引主表只保留 source id、终态状态、Hub path 和当前策略，避免和 `registry/sources.json` 重复维护。需要恢复 owner、review_after、authority、write_policy、migration_strategy、final_disposition、check 和 coverage 时，运行：

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
- 每个 source 的 Hub 内管理面位于 `sources/<source_id>/`，至少包含 `README.md`、`inventory.jsonl`、`coverage.md`、`source-policy.md`。
- `registry/sources.json` 的 `path` 必须指向 `sources/<source_id>`；当前知识入口只使用 Hub 内路径，旧外部路径不作为 active source、check command 或新增归档入口。

## Source 专项审查制品

- `pcr02-project-docs/runbooks/asan-debug-guide.md`: ASAN 拆分目标证据：`artifacts/manifests/pcr02-asan-split-targets-20260618.md`。
- `pcr02-project-docs/runbooks/asan-debug-guide.md owner-ready package`: 单项 owner 签收材料：`artifacts/manifests/pcr02-asan-owner-ready-package-20260620.md`。
- `pcr02-project-docs/runbooks/memory-auto-curation-guide.md`: report-only 治理证据：`artifacts/manifests/memory-auto-curation-report-only-governance-20260618.md`。
- `pcr02-project-docs/runbooks/memory-auto-curation-guide.md owner-ready package`: 单项 owner 签收材料：`artifacts/manifests/pcr02-memory-auto-curation-owner-ready-package-20260620.md`。
- `pcr02-project-docs/plans/2026-06-15-dvr-record-proto-sensor-decoupling-plan.md`: DVR plan 历史收口证据：`artifacts/manifests/pcr02-dvr-motor-closeout-targets-20260618.md`；终态目标为 `projects/pcr02/archive/plans/2026-06-15-dvr-record-proto-sensor-decoupling-plan.md`。
- `pcr02-project-docs/plans/2026-06-15-dvr-record-proto-sensor-decoupling-plan.md owner-ready package`: 单项 owner 签收材料：`artifacts/manifests/pcr02-dvr-plan-owner-ready-package-20260620.md`。
- `pcr02-project-docs/reports/2026-05-29-motor-mcu-debug-record.md`: motor MCU 事实拆分和 archive-only 边界：`artifacts/manifests/pcr02-dvr-motor-closeout-targets-20260618.md`。
- `pcr02-project-docs/reports/2026-05-29-motor-mcu-debug-record.md owner-ready package`: 单项 owner 签收材料：`artifacts/manifests/pcr02-motor-mcu-owner-ready-package-20260620.md`。
- `pcr02-project-docs/reports/2026-06-16-dvr-record-replay-session-archive.md`: DVR session archive-only 元数据和 memory-candidate 排除：`artifacts/manifests/pcr02-dvr-motor-closeout-targets-20260618.md`。
- `pcr02-project-docs/reports/2026-06-16-dvr-record-replay-session-archive.md owner-ready package`: 单项 owner 签收材料：`artifacts/manifests/pcr02-dvr-session-archive-owner-ready-package-20260620.md`。
- `pcr02-project-docs/AGENTS.md`: PCR02 project-local docs rule 已由 landing 确认为 `reference-only`；历史证据：`artifacts/manifests/pcr02-remaining-owner-gates-20260618.md`。
- `pcr02-project-docs/AGENTS.md owner-ready package`: 单项 owner 签收材料：`artifacts/manifests/pcr02-agents-owner-ready-package-20260620.md`。
- `pcr02-project-docs/standards/diag-command-metadata-standard.md`: PCR02 diag metadata 已由 landing 确认为 `reference-only`；历史证据边界：`artifacts/manifests/pcr02-remaining-owner-gates-20260618.md`。
- `pcr02-project-docs/standards/diag-command-metadata-standard.md owner-ready package`: 单项 owner 签收材料：`artifacts/manifests/pcr02-diag-owner-ready-package-20260620.md`。
- `pcr02-project-docs`: 32/32 docs 治理覆盖和 registry/index 收口：`artifacts/manifests/pcr02-docs-governance-closeout-20260618.md`。
- `pcr02-project-docs owner gates`: 旧 owner decision action board 已由 `artifacts/manifests/pcr02-project-docs-owner-decision-landing-20260623.md` 取代；历史行动板：`artifacts/manifests/pcr02-owner-action-board-20260618.md`。
- `pcr02-project-docs owner intake`: 旧中文 owner 签收字段包已由 landing 取代；历史 intake：`artifacts/manifests/pcr02-owner-intake-package-20260618.md`。
- `pcr02-project-docs owner-gated source identity`: landing 前 source SHA256/size preflight 历史证据：`artifacts/manifests/pcr02-owner-source-identity-preflight-20260618.md`。
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
- `pcr02-project-docs source control`: Hub 内 source 主控目录：`sources/pcr02-project-docs/README.md`、`sources/pcr02-project-docs/inventory.jsonl`、`sources/pcr02-project-docs/coverage.md`、`sources/pcr02-project-docs/source-policy.md`。
- `pcr02-project-docs ASAN owner target`: `projects/pcr02/current/runbooks/asan-debug-guide.md`，registry item `pcr02-asan-debug-guide-project-local-20260624`。
- `pcr02-project-docs DVR plan owner target`: `projects/pcr02/archive/plans/2026-06-15-dvr-record-proto-sensor-decoupling-plan.md`，registry item `pcr02-dvr-plan-archive-only-20260624`。
- `pcr02-project-docs motor MCU owner target`: `projects/pcr02/archive/reports/2026-05-29-motor-mcu-debug-record.md`，registry item `pcr02-motor-mcu-debug-record-archive-only-20260624`。
- `pcr02-project-docs DVR session owner target`: `projects/pcr02/archive/reports/2026-06-16-dvr-record-replay-session-archive.md`，registry item `pcr02-dvr-session-archive-only-20260624`。
- `pcr02-project-docs governance closeout`: 可恢复 handoff：`artifacts/manifests/pcr02-governance-handoff-20260618.md`。
- `registry/items.jsonl`、`indexes/by-*.md`: PCR02 control-plane closeout audit：`artifacts/manifests/pcr02-docs-governance-closeout-20260618.md`。
- `codex-memories`: runtime input；不迁移 raw memory，不写 `~/.codex/memories/**`，只在 Hub 生成候选、摘要或人工复核记录。
- `codex-history`: runtime input；不复制 raw history 行，只在 Hub 生成索引、摘要和候选治理。
- `codex-raw-sessions`: runtime input；不复制完整 raw session 正文，只做摘要、证据定位和候选。
- `codex-session-index`: runtime input；跨项目恢复索引必须落成 Hub 摘要或 registry 后才可长期引用。
- `codex-archive-registry`: 已硬迁移到 `domains/codex/archive/codex-archive-registry`；后续索引维护以 Hub registry/index 为准。
- `knowledge-hub-automation-runs`: Hub native ledger；用于串联 automation、authorization、project、session、source 和验证证据。
- `engineering-archive`: 已归位到 `projects/pcr02/archive/engineering-archive` 终态工程归档目录；旧过渡副本不再保留。
- `patent-disclosure`: 已归位到 `domains/patents/archive/patent-disclosure` 和 `artifacts/vault/patent-disclosure`。
- `embedded-knowledge`: 已完整迁移到 `domains/embedded/*`；旧过渡快照目录已删除，旧外部路径不再作为 source authority。
- `codex-archive`: 已硬迁移到 `domains/codex/archive/codex-archive`；旧 Codex archive 工具不再作为新增归档入口。
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
- `pcr02-module-agent-rules`: AGENTS/local rule owner-gated 边界；当前源项目根和独立子仓 `AGENTS.md` 仅作为项目本地 Codex 运行控制文件由源项目 Git 管理，Hub 已剪枝历史 AGENTS 正文副本并保留 hash/provenance：`artifacts/manifests/pcr02-module-agent-rules-boundary-20260620.md`、`artifacts/manifests/pcr02-agent-rules-body-prune-20260625.md`。
- `pcr02-module-agent-rules`: 8 个 module/project/local AGENTS 文件的 source identity：`artifacts/manifests/pcr02-p2-archive-rule-identity-20260621.md`。
- `pcr02-module-agent-rules`: report-only source check 执行快照：`artifacts/manifests/pcr02-level2-source-check-execution-snapshot-20260621.md`。
- `pcr02-project-agent-config`: config/artifact-ref 和 report-only automation boundary coverage：`artifacts/manifests/knowledge-hub-source-coverage-closeout-20260620.md`。
- `pcr02-project-agent-config`: `.vscode`/`.kilo` config、artifact 和 report-only automation 边界：`artifacts/manifests/pcr02-agent-config-boundary-20260620.md`。
- `pcr02-project-agent-config`: 10 个 `.vscode`/`.kilo` config/package 文件的 source identity：`artifacts/manifests/pcr02-p1-source-identity-20260621.md`。
- `pcr02-project-agent-config`: report-only source check 执行快照：`artifacts/manifests/pcr02-level2-source-check-execution-snapshot-20260621.md`。
- `registered sources`: 当前 source coverage matrix 和 terminal boundaries：`artifacts/manifests/knowledge-hub-source-coverage-closeout-20260620.md`。
