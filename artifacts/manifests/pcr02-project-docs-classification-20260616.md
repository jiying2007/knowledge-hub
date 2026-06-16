# PCR02 Project Docs Classification - 2026-06-16

## Scope

- Source: `/home/leiwenjun/work/sigmastar/pcr02_ssc305/SourceCode/sdk/verify/xcrz_sigmastar_demo/docs`
- Source id: `pcr02-project-docs`
- Mode: read-only classification.
- Files scanned: 32 files (`31` Markdown, `1` session script).
- Secret keyword scan: no matches from the migration precheck pattern.

## Classification Rules

- `current`: active project-specific design, runbook, spec, index or project-local governance.
- `decisions`: active project-specific architecture/spec decisions that define current behavior.
- `validation`: reports, debug records, release notes or analysis evidence that may support future decisions.
- `archive`: historical plans, completed migration records, session archives or stale implementation plans.
- `personal`: personal/local automation or memory material that must not enter team active indexes without review.
- `review-required`: missing or incomplete metadata, or active material stored under a historical directory.

## File-Level Classification

| source path | title | source status | target bucket | proposed destination | action | rationale |
|---|---|---|---|---|---|---|
| `README.md` | 项目 Docs 总入口 | active | current | `domains/projects/pcr02/current/docs-index.md` | reference-first | Active project docs entry and source authority description. |
| `AGENTS.md` | 项目 Docs Agent 规则 | missing metadata | current | `domains/projects/pcr02/current/project-docs-agent-rules.md` | review-required | Project-local operating rules; metadata missing in source. |
| `architecture/diag-command-architecture-final.md` | PCR02 诊断命令架构终版（唯一主文档） | active | decisions | `domains/projects/pcr02/decisions/diag-command-architecture-final.md` | copy-first-candidate | Active verified architecture decision document. |
| `architecture/hdi-api-app-functional-overview.md` | HDI API APP 模块功能总览 | active | current | `domains/projects/pcr02/current/architecture/hdi-api-app-functional-overview.md` | copy-first-candidate | Current verified architecture/model document. |
| `architecture/module-catalog.md` | PCR02 模块目录与职责清单 | active | current | `domains/projects/pcr02/current/architecture/module-catalog.md` | copy-first-candidate | Current module ownership and responsibility map. |
| `architecture/project-core-module-design.md` | PCR02 核心模块设计 | active | current | `domains/projects/pcr02/current/architecture/project-core-module-design.md` | copy-first-candidate | Current project core module design. |
| `architecture/project-detailed-design.md` | PCR02 项目详细设计 | active | decisions | `domains/projects/pcr02/decisions/project-detailed-design.md` | copy-first-candidate | Active verified design decision document. |
| `architecture/project-overview-design.md` | PCR02 项目概要设计 | active | current | `domains/projects/pcr02/current/architecture/project-overview-design.md` | copy-first-candidate | Current verified architecture overview. |
| `specs/2026-05-10-diag-v4-hybrid-refcount-discovery-spec.md` | PCR02 Diag V4 终态设计（Hybrid RefCount + 发现先行） | active | decisions | `domains/projects/pcr02/decisions/diag-v4-hybrid-refcount-discovery-spec.md` | copy-first-candidate | Active verified spec with decision semantics. |
| `standards/diag-command-metadata-standard.md` | Diag Command Metadata Standard | missing metadata | decisions | `domains/projects/pcr02/decisions/diag-command-metadata-standard.md` | review-required | Project-specific diag metadata standard; do not promote to global standard without owner review. |
| `standards/third-party-libraries-reference.md` | PCR02 第三方库引用基线 | active | current | `domains/projects/pcr02/current/third-party-libraries-reference.md` | copy-first-candidate | Current project dependency baseline. |
| `runbooks/asan-debug-guide.md` | ASAN 调试指导（项目通用） | active | current | `domains/projects/pcr02/current/runbooks/asan-debug-guide.md` | review-required | Marked project-general but may overlap team knowledge; keep project-specific until owner review. |
| `runbooks/diag-usage-guide.md` | Diag 测试使用指南 | active | current | `domains/projects/pcr02/current/runbooks/diag-usage-guide.md` | copy-first-candidate | Current project diag usage guide. |
| `runbooks/irlight-sw-threshold-calibration.md` | SW 光敏（软光敏）阈值标定流程 | active | current | `domains/projects/pcr02/current/runbooks/irlight-sw-threshold-calibration.md` | copy-first-candidate | Current project calibration runbook. |
| `runbooks/prog-tool-usage-guide.md` | prog_tool 使用说明（终态） | active | current | `domains/projects/pcr02/current/runbooks/prog-tool-usage-guide.md` | copy-first-candidate | Current terminal project tool usage guide. |
| `runbooks/project-build-and-deploy-guide.md` | PCR02 构建与部署手册 | active | current | `domains/projects/pcr02/current/runbooks/project-build-and-deploy-guide.md` | copy-first-candidate | Current build and deploy runbook. |
| `runbooks/project-debug-tools-guide.md` | PCR02 项目调试工具入口 | active | current | `domains/projects/pcr02/current/runbooks/project-debug-tools-guide.md` | copy-first-candidate | Current project debug-tool entry. |
| `runbooks/memory-auto-curation-guide.md` | 记忆自动化整理流程 | active | personal | `domains/projects/pcr02/personal/memory-auto-curation-guide.md` | review-required | Memory automation may encode personal workflow; exclude from team active index until reviewed. |
| `runbooks/examples/prog-tool-ci-smoke.session` | prog_tool session script for CI smoke | missing metadata | validation | `domains/projects/pcr02/validation/prog-tool-ci-smoke.session.ref.md` | artifact-ref-candidate | Non-Markdown session script; register as artifact/reference before copying. |
| `plans/2026-05-06-v1-deep-analysis-plan.md` | V1 与主分支深入分析计划 | archived | archive | `domains/projects/pcr02/archive/plans/2026-05-06-v1-deep-analysis-plan.md` | copy-first-candidate | Historical archived plan. |
| `plans/2026-05-06-v1-migration-execution-plan.md` | V1 到主分支迁移执行计划 | archived | archive | `domains/projects/pcr02/archive/plans/2026-05-06-v1-migration-execution-plan.md` | copy-first-candidate | Historical archived migration plan. |
| `plans/2026-05-08-irlight-optimization-plan.md` | IR 补光与光敏控制优化计划 | archived | archive | `domains/projects/pcr02/archive/plans/2026-05-08-irlight-optimization-plan.md` | copy-first-candidate | Historical archived implementation plan. |
| `plans/2026-05-10-diag-v4-hybrid-refcount-discovery-implementation-plan.md` | PCR02 Diag V4 Hybrid RefCount + 发现先行 实现计划 | archived | archive | `domains/projects/pcr02/archive/plans/2026-05-10-diag-v4-hybrid-refcount-discovery-implementation-plan.md` | copy-first-candidate | Historical archived implementation plan. |
| `plans/2026-05-13-diag-ut-hard-switch-progress-plan.md` | Diag UT 硬切进展（2026-05-13） | archived | archive | `domains/projects/pcr02/archive/plans/2026-05-13-diag-ut-hard-switch-progress-plan.md` | copy-first-candidate | Historical progress plan. |
| `plans/2026-06-15-dvr-record-proto-sensor-decoupling-plan.md` | DVR 录像回放 proto/sensor 解耦设计与实施计划 | active, incomplete metadata | current | `domains/projects/pcr02/current/plans/dvr-record-proto-sensor-decoupling-plan.md` | review-required | Active plan under historical directory; confirm current execution state before migration. |
| `reports/2026-05-06-v1-deep-analysis-report.md` | V1 与主分支深入分析报告 | archived | validation | `domains/projects/pcr02/validation/reports/2026-05-06-v1-deep-analysis-report.md` | copy-first-candidate | Historical analysis evidence. |
| `reports/2026-05-07-v1-migration-final-report.md` | V1 到主分支迁移完成报告 | archived | validation | `domains/projects/pcr02/validation/reports/2026-05-07-v1-migration-final-report.md` | copy-first-candidate | Historical migration completion evidence. |
| `reports/2026-05-08-sigmastar-aov-lightsensor-analysis-report.md` | Sigmastar AOV 与光敏控制全面分析 | archived | validation | `domains/projects/pcr02/validation/reports/2026-05-08-sigmastar-aov-lightsensor-analysis-report.md` | copy-first-candidate | Historical analysis evidence. |
| `reports/2026-05-14-prog-tool-terminal-release-report.md` | prog_tool 终版发布说明 | archived | validation | `domains/projects/pcr02/validation/reports/2026-05-14-prog-tool-terminal-release-report.md` | copy-first-candidate | Release evidence for project tool behavior. |
| `reports/2026-05-17-session-archive-report.md` | 会话归档报告（2026-05-17） | archived | archive | `domains/projects/pcr02/archive/reports/2026-05-17-session-archive-report.md` | copy-first-candidate | Historical session archive, not current evidence. |
| `reports/2026-05-29-motor-mcu-debug-record.md` | 电机 MCU 调试详细记录 | missing metadata | validation | `domains/projects/pcr02/validation/reports/2026-05-29-motor-mcu-debug-record.md` | review-required | Debug evidence lacks source metadata; classify as validation candidate only after review. |
| `reports/2026-06-16-dvr-record-replay-session-archive.md` | DVR 录像回放解耦会话归档 | missing metadata | archive | `domains/projects/pcr02/archive/reports/2026-06-16-dvr-record-replay-session-archive.md` | review-required | Session archive lacks source metadata; keep out of active index. |

## Immediate Migration Set

The first safe migration batch should include only `copy-first-candidate` files with active/archived source metadata and no personal or missing-metadata flags.

- Active current/decision candidates: 13 files.
- Historical archive/validation candidates: 10 files.
- Review-required or artifact-ref candidates: 9 files.

## Non-Actions

- No source project docs were copied, moved, deleted, renamed, edited, or pruned.
- No project-specific document was promoted to `domains/embedded/standards/`.
- No personal or memory automation material was added to active team indexes.
- No session script content was imported as text knowledge.

## Next Step

Create a migration dry-run manifest for the first safe batch, with source path, proposed destination, SHA256, owner, review status, and rollback policy. Only after that manifest is reviewed should `copy-first` content migration be executed.
