# Knowledge Sources

本页覆盖 current source 主表和 retired source provenance ledger。当前主表只在 `registry/sources.json`；已关闭来源在 `registry/retired-sources.jsonl`，仅用于历史 source_id、coverage、source-control 和 owner gate 审计恢复。

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

下表是 `registry/retired-sources.jsonl` 中 PCR02 retired source 的人工可读摘要，只用于快速恢复 owner、复核时间和最终治理边界；权威字段仍以 registry ledger 为准。

| Source | Owner | Review After | Final Disposition | Boundary |
| --- | --- | --- | --- | --- |
| pcr02-project-docs | pcr02-registry-owner | 2026-09-20 | mixed-terminal-coverage | copy/reference/artifact/owner decision landing 混合覆盖；7 个 owner gate 已按 2026-06-23 landing 收口 |
| pcr02-project-tools | pcr02-registry-owner | 2026-09-20 | mixed-terminal-coverage | tool/diag/memory automation 只做 reference/report-only 边界，不写源项目 |
| pcr02-project-knowledge | pcr02-registry-owner | 2026-09-20 | mixed-terminal-coverage | classify-first、secret/config/tool-ref 边界，不提升 active |
| pcr02-product-test | pcr02-registry-owner | 2026-09-20 | mixed-terminal-coverage | artifact/config/interface 只做身份和引用登记，不复制大附件或构建物 |
| pcr02-project-scratch | pcr02-registry-owner | 2026-09-20 | archive-only-registered | scratch/session/resume archive-only，不写 memory，不进 active facts |
| pcr02-project-root-artifacts | pcr02-registry-owner | 2026-09-20 | mixed-terminal-coverage | root loose artifact/tool/config 边界，排除子 source 和生成物 |
| pcr02-module-agent-rules | pcr02-registry-owner | 2026-09-20 | hub-canonical | module/local AGENTS 规则进入 Hub source control；未签收前不升级全局规则 |
| pcr02-project-agent-config | pcr02-registry-owner | 2026-09-20 | artifact-ref-registered | `.vscode`/`.kilo` 配置和 report-only 自动化只做 artifact/config ref |

## Source 治理恢复

本索引主表只保留 source id、终态状态、Hub path 和当前策略，避免和 source registry 重复维护。需要恢复 owner、review_after、authority、write_policy、source_strategy、final_disposition、check 和 coverage 时，运行：

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
- 每个 current/retired source 的 Hub 内管理面位于 `sources/<source_id>/`，至少包含 `README.md`、`inventory.jsonl`、`coverage.md`、`source-policy.md`。
- current/retired source registry 的 `path` 必须指向 `sources/<source_id>`；当前知识入口只使用 Hub 内路径，旧外部路径不作为 active source、check command 或新增归档入口。

## Source 专项审查制品

- `pcr02-project-docs/runbooks/asan-debug-guide.md`: ASAN 拆分目标证据：`artifacts/manifests/pcr02-asan-split-targets-20260618.md`。
- `pcr02-project-docs/runbooks/asan-debug-guide.md team active runbook`: 团队级 ASAN 方法论已去项目化落到 `domains/embedded/runbooks/asan-debug-guide.md` 并提升为 active，证据：`artifacts/manifests/embedded-asan-active-promotion-20260629.md`。
- `pcr02-project-docs/runbooks/asan-debug-guide.md team owner-ready`: 团队级 ASAN 方法论的前置审查包已由 active promotion 消解，证据：`artifacts/manifests/embedded-asan-team-owner-ready-package-20260629.md`。
- `team ASAN non-PCR02 evidence follow-up`: 非 PCR02 实操验证尚未在 Hub 中找到，已登记后续证据验收标准：`artifacts/manifests/embedded-asan-non-pcr02-evidence-followup-20260629.md`。
- `team ASAN non-PCR02 validation template`: 后续非 PCR02 项目验证记录优先使用 `templates/asan-validation-report.md`，确保构建、运行、符号化、复测、资源和回退证据完整。
- `pcr02-project-docs/runbooks/asan-debug-guide.md historical owner signoff package`: 历史 owner 签收材料，已由 `artifacts/manifests/pcr02-project-docs-owner-decision-landing-20260623.md` 取代：`artifacts/manifests/pcr02-asan-owner-ready-package-20260620.md`。
- `pcr02-project-docs/runbooks/memory-auto-curation-guide.md`: report-only 治理证据：`artifacts/manifests/memory-auto-curation-report-only-governance-20260618.md`。
- `pcr02-project-docs/runbooks/memory-auto-curation-guide.md historical owner signoff package`: 历史 owner 签收材料，已由 `artifacts/manifests/pcr02-project-docs-owner-decision-landing-20260623.md` 取代：`artifacts/manifests/pcr02-memory-auto-curation-owner-ready-package-20260620.md`。
- `pcr02-project-docs/plans/2026-06-15-dvr-record-proto-sensor-decoupling-plan.md`: DVR plan 历史收口证据：`artifacts/manifests/pcr02-dvr-motor-closeout-targets-20260618.md`；终态目标为 `projects/pcr02/archive/plans/2026-06-15-dvr-record-proto-sensor-decoupling-plan.md`。
- `pcr02-project-docs/plans/2026-06-15-dvr-record-proto-sensor-decoupling-plan.md historical owner signoff package`: 历史 owner 签收材料，已由 `artifacts/manifests/pcr02-project-docs-owner-decision-landing-20260623.md` 取代：`artifacts/manifests/pcr02-dvr-plan-owner-ready-package-20260620.md`。
- `pcr02-project-docs/reports/2026-05-29-motor-mcu-debug-record.md`: motor MCU 事实拆分和 archive-only 边界：`artifacts/manifests/pcr02-dvr-motor-closeout-targets-20260618.md`。
- `pcr02-project-docs/reports/2026-05-29-motor-mcu-debug-record.md historical owner signoff package`: 历史 owner 签收材料，已由 `artifacts/manifests/pcr02-project-docs-owner-decision-landing-20260623.md` 取代：`artifacts/manifests/pcr02-motor-mcu-owner-ready-package-20260620.md`。
- `pcr02-project-docs/reports/2026-06-16-dvr-record-replay-session-archive.md`: DVR session archive-only 元数据和 memory-candidate 排除：`artifacts/manifests/pcr02-dvr-motor-closeout-targets-20260618.md`。
- `pcr02-project-docs/reports/2026-06-16-dvr-record-replay-session-archive.md historical owner signoff package`: 历史 owner 签收材料，已由 `artifacts/manifests/pcr02-project-docs-owner-decision-landing-20260623.md` 取代：`artifacts/manifests/pcr02-dvr-session-archive-owner-ready-package-20260620.md`。
- `pcr02-project-docs/AGENTS.md`: PCR02 project-local docs rule 已由 landing 确认为 `reference-only`；历史证据：`artifacts/manifests/pcr02-remaining-owner-gates-20260618.md`。
- `pcr02-project-docs/AGENTS.md historical owner signoff package`: 历史 owner 签收材料，已由 `artifacts/manifests/pcr02-project-docs-owner-decision-landing-20260623.md` 取代：`artifacts/manifests/pcr02-agents-owner-ready-package-20260620.md`。
- `pcr02-project-docs/standards/diag-command-metadata-standard.md`: PCR02 diag metadata 已由 landing 确认为 `reference-only`；历史证据边界：`artifacts/manifests/pcr02-remaining-owner-gates-20260618.md`。
- `pcr02-project-docs/standards/diag-command-metadata-standard.md historical owner signoff package`: 历史 owner 签收材料，已由 `artifacts/manifests/pcr02-project-docs-owner-decision-landing-20260623.md` 取代：`artifacts/manifests/pcr02-diag-owner-ready-package-20260620.md`。
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
- `codex-archive/session-wrap/20260518-223626-mcu-session-wrap-firmware-release-nas.md`: 已迁移为 firmware-release-tools NAS 发布同步历史归档，旧正文已按授权删除并保留 tombstone：`artifacts/manifests/codex-archive-removal-execution-20260710-session-wrap-caef-001-004-009.md`。
- `codex-archive/control-archives` and `codex-archive/tools`: 3 个 provenance-only 旧正文已按授权删除并保留 tombstone：`artifacts/manifests/codex-archive-removal-execution-20260710.md`。
- `codex-archive/debug-notes/20260516-222503-windows-builder-runbook.md`: 已迁移为 llm_tools Windows builder runbook 候选归档，旧正文已按授权删除并保留 tombstone；目标为 archive-only，不声明 current verified：`artifacts/manifests/codex-archive-removal-execution-20260710-migrated-extract-first.md`。
- `codex-archive/release-governance/20260516-225144-llm-tools-release-governance-20260516.md`: 已迁移为 llm_tools release governance archive-only 历史记录，旧正文已按授权删除并保留 tombstone：`artifacts/manifests/codex-archive-removal-execution-20260710-migrated-extract-first.md`。
- `codex-archive/research-notes/20260514-102409-dual-screen-animation-analysis.md`: 已迁移为 xcrz_sigmastar_demo dual-screen historical analysis，旧正文已按授权删除并保留 tombstone：`artifacts/manifests/codex-archive-removal-execution-20260710-migrated-extract-first.md`。
- `codex-archive/_registry/schema.md`: legacy archive schema 正文已按授权删除并保留 tombstone；当前权威是 `registry/schema.md`：`artifacts/manifests/codex-archive-removal-execution-20260710-covered-tombstone-001-003.md`。
- `codex-archive/archive-governance/20260519-221757-archive-quality-remediation.md`: 旧 archive governance 过程记录已按授权删除并保留 tombstone-only provenance：`artifacts/manifests/codex-archive-removal-execution-20260710-covered-tombstone-001-003.md`。
- `codex-archive/diag-architecture/20260510-000000-diag-command-architecture-v4-conclusion.md`: PCR02 diag v4 旧收口正文已按授权删除并保留 tombstone；当前设计权威是 PCR02 decision/spec：`artifacts/manifests/codex-archive-removal-execution-20260710-covered-tombstone-001-003.md`。
- `codex-archive/diag-architecture/20260511-112520-codex-token-optimization-roadmap.md`: Codex token efficiency roadmap 旧正文已按授权删除并保留 tombstone；coverage audit 保留 corrected topic、not-covered 项和 no active roadmap 边界：`artifacts/manifests/codex-archive-removal-execution-20260710-token-patent-004-006.md`。
- `codex-archive/patent-disclosure/20260530-215617-patent_skill_archive_note_20260530215400.md`: 四件专利组合旧过程记录已按授权删除并保留 tombstone；safe OTA 组合变化 provenance 保留，不声明 legal review completed：`artifacts/manifests/codex-archive-removal-execution-20260710-token-patent-004-006.md`。
- `codex-archive/patent-disclosure/20260530-220612-patent_skill_archive_note_20260530215400.md`: patents canonical note 的旧 Codex archive 重复副本已按授权删除并保留 tombstone；canonical patents corpus 保留，不声明 legal review completed：`artifacts/manifests/codex-archive-removal-execution-20260710-token-patent-004-006.md`。
- `codex-archive/session-wrap/20260602-132025-codex-adk-hardcut-session-wrap.md`: 已迁移为 ADK hardcut source-to-live coverage audit，旧正文已按授权删除并保留 tombstone：`artifacts/manifests/codex-archive-removal-execution-20260710-session-wrap-caef-001-004-009.md`。
- `codex-archive/session-wrap/20260627-230744-knowledge-hub-final-hardcut-session-wrap.md`: 已压实为 Knowledge Hub final hardcut tombstone audit，旧正文已按授权删除并保留 tombstone：`artifacts/manifests/codex-archive-removal-execution-20260710-session-wrap-caef-001-004-009.md`。
- `codex-archive/session-wrap/20260526-162109-pcr02-session-wrap-20260526-customer-ro-sd-upgrade.md`: 已迁移为 PCR02 /customer ro SD upgrade 历史 session 归档，旧正文已按授权删除并保留 tombstone：`artifacts/manifests/codex-archive-removal-execution-20260710-session-wrap-caef-001-004-009.md`。
- `codex-archive/session-wrap/20260524-231443-codex-session-wrap-20260524-openai-local-runtime-boundary.md`: 已迁移为 OpenAI local runtime boundary archive-only/freshness-required 记录，旧正文已按授权删除并保留 tombstone：`artifacts/manifests/codex-archive-removal-execution-20260710-session-wrap-caef-001-004-009.md`。
- `codex-archive/session-wrap/20260510-000000-diag-v4-hybrid-refcount-session-wrap.md`: 已由 PCR02 diag decision 与归档台账覆盖，旧 session-wrap 正文已按授权删除并保留 tombstone：`artifacts/manifests/codex-archive-removal-execution-20260710-session-wrap-covered-018-026.md`。
- `codex-archive/session-wrap/20260510-135300-session-wrap.md`: Codex V2 context/assets 过程记录已由当前 daily summary、memory-curation 和运行规则覆盖，旧正文已按授权删除并保留 tombstone：`artifacts/manifests/codex-archive-removal-execution-20260710-session-wrap-covered-018-026.md`。
- `codex-archive/session-wrap/20260510-150728-session-wrap.md`: 旧 bwrap/context handoff 运行态记录只保留 provenance，正文已按授权删除并保留 tombstone：`artifacts/manifests/codex-archive-removal-execution-20260710-session-wrap-covered-018-026.md`。
- `codex-archive/session-wrap/20260511-104901-session-wrap.md`: Usage TUI/token efficiency 过程会话已由 token/context efficiency 覆盖审计和 live skill 覆盖，旧正文已按授权删除并保留 tombstone：`artifacts/manifests/codex-archive-removal-execution-20260710-session-wrap-covered-018-026.md`。
- `codex-archive/session-wrap/20260511-132348-session-wrap.md`: Codex token/context efficiency 过程会话已由覆盖审计压实，旧正文已按授权删除并保留 tombstone：`artifacts/manifests/codex-archive-removal-execution-20260710-session-wrap-covered-018-026.md`。
- `codex-archive/session-wrap/20260523-082158-wechat-absorption.md`: WeChat P0 中间 handoff 已由 final all-cleared handoff 覆盖，旧正文已按授权删除并保留 tombstone：`artifacts/manifests/codex-archive-removal-execution-20260710-session-wrap-covered-018-026.md`。
- `codex-archive/session-wrap/20260523-085953-wechat-p0-batches.md`: WeChat P0 batch 中间记录已由 final all-cleared handoff 覆盖，旧正文已按授权删除并保留 tombstone：`artifacts/manifests/codex-archive-removal-execution-20260710-session-wrap-covered-018-026.md`。
- `codex-archive/session-wrap/20260523-101841-wechat-p0-context-handoff.md`: WeChat P0 context handoff 中间记录已由 final all-cleared handoff 覆盖，旧正文已按授权删除并保留 tombstone：`artifacts/manifests/codex-archive-removal-execution-20260710-session-wrap-covered-018-026.md`。
- `codex-archive/session-wrap/20260523-112927-context-compress-handoff-wechat-p0-after-006.md`: WeChat P0 after-006 中间 handoff 已由 final all-cleared handoff 覆盖，旧正文已按授权删除并保留 tombstone：`artifacts/manifests/codex-archive-removal-execution-20260710-session-wrap-covered-018-026.md`。
- `codex-archive/session-wrap/20260515-142200-session-wrap-crash-debug-tools.md`: 已迁移为 PCR02 SIGBUS core/debug tools 历史归档，旧正文已按授权删除并保留 tombstone：`artifacts/manifests/codex-archive-removal-execution-20260710-pcr02-session-wrap-027-031.md`。
- `codex-archive/session-wrap/20260515-154658-session-wrap-core-debug-and-busybox-tools.md`: 已迁移为 PCR02 SIGBUS core/debug tools 历史归档，旧正文已按授权删除并保留 tombstone：`artifacts/manifests/codex-archive-removal-execution-20260710-pcr02-session-wrap-027-031.md`。
- `codex-archive/session-wrap/20260517-154205-pcr02-gros-session-wrap.md`: 已迁移为 PCR02 GROS/SSC305/HDI historical session，旧正文已按授权删除并保留 tombstone：`artifacts/manifests/codex-archive-removal-execution-20260710-pcr02-session-wrap-027-031.md`。
- `codex-archive/session-wrap/20260518-223733-pcr02-ssc305-session-wrap.md`: 已迁移为 PCR02 GROS/SSC305/HDI historical session，旧正文已按授权删除并保留 tombstone：`artifacts/manifests/codex-archive-removal-execution-20260710-pcr02-session-wrap-027-031.md`。
- `codex-archive/session-wrap/20260521-091035-session-wrap-hdi-warning-zero.md`: 已迁移为 PCR02 GROS/SSC305/HDI historical session，旧正文已按授权删除并保留 tombstone：`artifacts/manifests/codex-archive-removal-execution-20260710-pcr02-session-wrap-027-031.md`。
- `codex-archive/session-wrap/20260517-154126-llm-tools-session-wrap.md`: 已迁移为 llm_tools three-repo governance historical session，旧正文已按授权删除并保留 tombstone：`artifacts/manifests/codex-archive-removal-execution-20260710-session-wrap-final-032-037.md`。
- `codex-archive/session-wrap/20260517-154134-gd32-firmware-session-wrap.md`: 已迁移为 MCU GD32/HC32 Codex maintenance historical session，旧正文已按授权删除并保留 tombstone：`artifacts/manifests/codex-archive-removal-execution-20260710-session-wrap-final-032-037.md`。
- `codex-archive/session-wrap/20260517-180051-knowledge-session-wrap.md`: 已压实为 Knowledge legacy coverage audit，旧正文已按授权删除并保留 tombstone：`artifacts/manifests/codex-archive-removal-execution-20260710-session-wrap-final-032-037.md`。
- `codex-archive/session-wrap/20260523-135801-wechat-all-cleared-handoff.md`: 已压实为 WeChat absorption final handoff coverage audit，旧正文已按授权删除并保留 tombstone：`artifacts/manifests/codex-archive-removal-execution-20260710-session-wrap-final-032-037.md`。
- `codex-archive/session-wrap/20260524-141359-gd32l235-app-boot-v1-session-wrap-20260524.md`: 已迁移为 MCU GD32L235 app_boot_v1 refactor historical session，旧正文已按授权删除并保留 tombstone：`artifacts/manifests/codex-archive-removal-execution-20260710-session-wrap-final-032-037.md`。
- `codex-archive/session-wrap/20260524-231336-gd32l235-app-boot-v1-session-wrap.md`: 已合并到 MCU GD32L235 app_boot_v1 refactor historical session，旧正文已按授权删除并保留 tombstone：`artifacts/manifests/codex-archive-removal-execution-20260710-session-wrap-final-032-037.md`。
- `codex-archive-registry`: 已终态归位到 `domains/codex/archive/codex-archive-registry`；后续索引维护以 Hub registry/index 为准。
- `knowledge-hub-automation-runs`: Hub native ledger；用于串联 automation、authorization、project、session、source 和验证证据。
- `engineering-archive`: 已归位到 `projects/pcr02/archive/engineering-archive` 终态工程归档目录；旧过渡副本不再保留。
- `patent-disclosure`: 已归位到 `domains/patents/archive/patent-disclosure` 和 `artifacts/vault/patent-disclosure`。
- `embedded-knowledge`: 已完整迁移到 `domains/embedded/*`；旧过渡快照目录已删除，旧外部路径不再作为 source authority。
- `codex-archive`: 已终态归位到 `domains/codex/archive/codex-archive`；旧 Codex archive 工具不再作为新增归档入口。
- `codex-archive`: ADK hardcut source-to-live 旧 session-wrap 已迁移为 coverage audit，旧正文已按授权删除并保留 tombstone：`artifacts/manifests/codex-archive-removal-execution-20260710-session-wrap-caef-001-004-009.md`。
- `codex-archive`: Knowledge Hub final hardcut 旧 session-wrap 已压实为 tombstone audit，旧正文已按授权删除并保留 tombstone：`artifacts/manifests/codex-archive-removal-execution-20260710-session-wrap-caef-001-004-009.md`。
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
- `codex-archive/memory-curation/20260517-154419-llm-tools-targeted-memory-curation.md` and `codex-archive/memory-curation/20260517-155031-llm-tools-memory-curation-normal-iteration.md`: migrated to llm_tools normal iteration historical policy: `projects/llm-tools/archive/release/2026-05-17-llm-tools-normal-iteration-policy.md`; `llm-tools-normal-iteration-policy-20260517`.
- `codex-archive/memory-curation/20260519-221757-llm-tools-v1-release-memory-review.md`: migrated to llm_tools v1.0.0 release memory review: `projects/llm-tools/archive/release/2026-05-19-llm-tools-v1-release-memory-review.md`; `llm-tools-v1-release-memory-review-20260519`.
- `codex-archive/memory-curation/20260518-224302-mcu-memory-curation.md`: migrated to MCU memory-curation coverage: `projects/mcu/archive/2026-05-18-mcu-memory-curation-coverage.md`; `mcu-memory-curation-coverage-20260518`.
- `codex-archive/memory-curation/20260519-221757-pcr02-ssc305-post-release-memory-review.md`: migrated to PCR02 2026-05-19 release validation historical record: `projects/pcr02/archive/engineering-archive/pcr02/ota-release/pcr02_release_validation_20260519.md`; `pcr02-release-validation-20260519`.
- `codex-archive/memory-curation/*`: 40 old memory-curation source bodies classified by terminal coverage ledger: `artifacts/manifests/codex-archive-memory-curation-coverage-20260711.md`; `codex-archive-memory-curation-coverage-20260711`.
- `codex-archive/memory-curation/*`: 40 old memory-curation source bodies deleted with tombstone; topic index retained: `artifacts/manifests/codex-archive-removal-execution-20260711-memory-curation.md`; `codex-archive-removal-execution-20260711-memory-curation`.
- `codex-archive`: post-memory-curation remaining blocker scan recorded 7 non-index bodies; superseded by final body coverage: `artifacts/manifests/codex-archive-remaining-blockers-scan-20260711.md`; `codex-archive-remaining-blockers-scan-20260711`.
- `codex-archive`: 7 final old bodies classified by terminal coverage ledger: `artifacts/manifests/codex-archive-final-body-coverage-20260711.md`; `codex-archive-final-body-coverage-20260711`.
- `codex-archive`: 7 final old bodies deleted with tombstone; topic indexes retained: `artifacts/manifests/codex-archive-removal-execution-20260711-final-bodies.md`; `codex-archive-removal-execution-20260711-final-bodies`.
- `codex-archive`: corpus readiness reports no remaining non-index/README body, but corpus deletion requires separate authorization: `artifacts/manifests/codex-archive-corpus-deletion-readiness-20260711.md`; `codex-archive-corpus-deletion-readiness-20260711`.
