---
id: codex-archive-phased-migration-removal-20260709
title: Codex archive 分阶段迁移与移除台账 2026-07-09
kind: audit
domain: codex
scope: team-general
visibility: team-internal
status: archived
owner: leiwenjun
review_after: '2026-11-09'
review_status: human-directed-delegated-retired
promotion: none
tags:
- codex-archive
- phased-migration
- archive-removal
- archive-governance
- tombstone
- report-only
- no-memory-write
- no-active-promotion
generated_by_ai: true
ai_role: classified
ai_model_or_tool: Codex
ai_generated_at: '2026-07-09'
manual_validation_pending: false
summary_zh: 将 Codex archive 从 reference-first 审计推进到分阶段迁移/移除台账：旧 origin 已不存在；Hub 内 canonical archive corpus 按 covered、tombstone-candidate、extract-first
  分类排队；实际删除必须另建批次并满足 migrated_as、covered_by 或 tombstone_as 门禁。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
promotion_decision: explicit human lifecycle decision delegated to Codex; direct content review not asserted; token=KH-ATTEST-670bed5b38521f108005;
  source=current-session exact hash-bound lifecycle attestation and reviewer binding on 2026-07-15
---

# Codex archive 分阶段迁移与移除台账 2026-07-09

## 摘要

本台账把 `codex-archive` 从单纯 `reference-first` 推进到可执行的分阶段收缩策略：旧来源路径已经退役，Hub 内 canonical archive corpus 也不再无限期整体保留；后续按 topic 和单条文件逐步迁移、tombstone、再移除。

本轮不删除任何正文文件，先建立 removal gate 和第一批迁移队列。

- 旧 origin：`~/codex/docs/archive`，当前本机不存在，视为已退役来源。
- 当前 corpus：`domains/codex/archive/codex-archive`，85 个非 `index.md` Markdown 正文。
- 控制原则：先迁移或 tombstone，再移除；不允许无替代删除。
- 结构化台账：`artifacts/manifests/codex-archive-phased-migration-removal-20260709.jsonl`。
- 前置审计：`artifacts/manifests/codex-archive-selective-backfill-audit-20260709.md`。

## 移除门禁

任何旧 archive 正文进入删除批次前，必须满足全部条件：

- 已有 `migrated_as`、`covered_by` 或 `tombstone_as`。
- 已完成敏感信息扫描，没有 secrets、auth、raw session、cache、runtime state、core 或 binary。
- 已确认目标路径属于 `projects/`、`domains/`、`notes/`、`artifacts/manifests/` 或 `sources/` 的 canonical 边界。
- 若内容会影响当前规则、runbook、owner decision 或 active 状态，必须另走 owner review，不得从旧 archive 直接提升。
- 删除批次必须是独立 manifest，列出源文件、替代文件、hash、回滚方式和验证命令。

## 分阶段策略

| 阶段 | 范围 | 动作 |
| --- | --- | --- |
| Phase 0 | 旧 origin `~/codex/docs/archive` | 已不存在，只保留 provenance。 |
| Phase 1 | 已 covered topic | 允许进入 removal-candidate，但需要 tombstone/covered_by 台账。 |
| Phase 2 | promote-candidate topic | 逐条抽取长期结论，落到 canonical 目标后再移除旧正文。 |
| Phase 3 | provenance-only topic | 默认只写 tombstone，不迁移正文；等待一个 review 周期后再删。 |
| Phase 4 | 旧 topic 目录 | 当目录内正文全部迁移或 tombstone 后，删除 topic index 和空目录。 |

## 第一批队列

第一批只做队列标定：

- `covered` removal-candidate：`_registry`、`archive-governance`、`diag-architecture`、`patent-disclosure`。
- `provenance-only` tombstone-candidate：`control-archives`、`memory-curation`、`session-wrap`、`tools`。
- `promote-candidate` extract-first：`debug-notes/20260516-222503-windows-builder-runbook.md`、`release-governance/20260516-225144-llm-tools-release-governance-20260516.md`、`research-notes/20260514-102409-dual-screen-animation-analysis.md`。

## 下一批执行建议

1. 先处理 llm_tools 相关两条：
   - Windows 构建机 runbook 应迁移到 `projects/llm-tools/current/` 或 `projects/llm-tools/archive/`，但需要确认 llm-tools 当前项目目录结构和 owner 边界。
   - llm_tools 发布治理应迁移到 release/runbook 或 archive report，不直接提升为 active。
2. 再处理 Sigmastar 双屏动画分析：
   - 若属于 PCR02/SigmaStar 项目事实，迁移到 `projects/pcr02/archive/reports/` 或对应 Sigmastar 项目 archive。
   - 若只是旧代码快照分析，保留为 archive-only，不进入 current。
3. 最后批量 tombstone `memory-curation`：
   - 只保留 memory governance 的高层台账，不迁移 40 条过程记录。
   - 不写 `~/.codex/memories`。

## 验证计划

```bash
rtk jq -c . artifacts/manifests/codex-archive-phased-migration-removal-20260709.jsonl
rtk bash ~/knowledge-hub/tools/knowledge-search.sh "Codex archive 分阶段迁移"
rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run
rtk rg -n "(?i)(password|token|cookie|private[_ -]?key|secret)\\s*[:=]" artifacts/manifests/codex-archive-phased-migration-removal-20260709.md artifacts/manifests/codex-archive-phased-migration-removal-20260709.jsonl
```

## 当前结论

旧 archive 的目标状态不是永久保留，而是逐步收缩到 canonical Hub 条目、tombstone 和 source provenance。当前阶段只建立迁移/移除控制台；实际删除必须另开批次，按本台账逐条验证。

2026-07-10 后续批次已补 `artifacts/manifests/codex-adk-hardcut-source-to-live-audit-20260710.md`，将 `session-wrap/20260602-132025-codex-adk-hardcut-session-wrap.md` 从 extract-first 阻塞转为 coverage audit。旧正文仍未删除，且 topic 级删除继续阻塞。

2026-07-10 后续批次已补 `artifacts/manifests/codex-knowledge-hub-final-hardcut-tombstone-audit-20260710.md`，将 `session-wrap/20260627-230744-knowledge-hub-final-hardcut-session-wrap.md` 从 covered-removal 转为 tombstone-only audit。旧正文仍未删除，且 topic 级删除继续阻塞。

2026-07-10 后续批次已补 `artifacts/manifests/codex-archive-removal-execution-20260710-token-patent-004-006.md`，将 `diag-architecture/20260511-112520-codex-token-optimization-roadmap.md` 和两篇 `patent-disclosure` 旧副本按授权删除并 tombstone。token roadmap 以 corrected topic `codex/token-efficiency` 保留 coverage audit；patent-disclosure 保留 safe OTA 组合变化 provenance，且不声明 legal review 完成。旧 archive 整体删除仍被 `session-wrap` 和 `memory-curation` 阻塞。
