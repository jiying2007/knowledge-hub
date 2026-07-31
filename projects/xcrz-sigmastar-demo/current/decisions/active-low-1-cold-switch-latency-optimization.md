---
related:
- projects/xcrz-sigmastar-demo/README.md
- indexes/obsidian-home.md
- indexes/project-readiness.md
human_reviewed_by: null
human_reviewed_at: null
review_basis: null
decision_status: null
decision_date: null
id: pcr02-active-low-1-cold-switch-latency-optimization-20260728
title: PCR02 ACTIVE_LOW_1 COLD 切换耗时优化决策
kind: decision
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/current/decisions/active-low-1-cold-switch-latency-optimization.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: team-core
source:
  type: manual
  from: manual-entry:knowledge-new.sh
  source_sha256: 7ce01cdbf3966fc66fbc75c3898372a31cc330dbd363f561e64b2c16eadeb1ed
review_after: '2026-10-26'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- pcr02
- hdi-vi
- performance
validation_refs:
- projects/xcrz-sigmastar-demo/current/decisions/active-low-1-cold-switch-latency-optimization.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/current/decisions/active-low-1-cold-switch-latency-optimization.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-07-28'
updated_at: '2026-07-28'
generated_by_ai: true
ai_role: summarized
ai_model_or_tool: Codex
ai_generated_at: '2026-07-28'
manual_validation_pending: true
summary_zh: SSC305 物理 1/30fps 继续使用完整 COLD rebuild；1→30fps 通过 lifecycle gate 内 Sensor teardown boost 与未连接 LDC 并行预热，将 RAW-only
  从 4.812s 降至 3.298～3.354s、both 从 5.845s 降至 3.323～3.426s；ISP DestroyDevice 约 0.999s 为当前安全下界；在线 FRC rebind 与预先 StopChannel
  无有效总收益，retained ISP/Sensor 继续 capability-gated。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
aliases:
- PCR02 ACTIVE_LOW_1 COLD 切换耗时优化决策
---

# 决策标题

## 背景

说明为什么需要 owner 决策。

## 适用范围

说明决策适用的项目、模块、版本、环境和不适用场景。

## 权威来源

- source_id：
- source_path：
- owner：
- source_status：

## 决策问题

用一句话写清要批准、拒绝、延后或废弃什么。

## 选项

| 选项 | 影响范围 | 成本 | 风险 |
| --- | --- | --- | --- |
|  |  |  |  |

## 证据

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
| --- | --- | --- | --- | --- | --- |
| `rtk ...` |  | 中文摘要。 |  | Knowledge Hub / Project / Tool |  |

引用验证报告、runbook、artifact、源文档或 owner review。

## 决策

说明批准、拒绝或延后，并明确生效范围。

## 当前结论

说明当前已生效、待 owner 签收、被延后或被拒绝的结论；推断和建议必须单独标注。

## 生效条件

说明何时 active，依赖哪些验证或 owner 动作。

## 回滚条件

说明什么情况下撤销、归档或 supersede。

## 风险与限制

说明未验证点、外部依赖、过期条件、敏感信息边界和后续 owner 复核要求。

## Review 周期

- owner：
- review_after：
- 下一次复核内容：
