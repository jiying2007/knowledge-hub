---
id: pcr02-ssc305-readiness-decision-20260713
title: PCR02 SSC305 SDK 权威与维护边界决策候选
kind: decision
domain: projects/pcr02-ssc305
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
review_after: '2026-10-13'
review_status: human-reviewed-accepted
promotion: none
tags:
- pcr02-ssc305
- project-readiness
- decision
- ai-generated
- owner-review-pending
- manual-validation-pending
- no-active-promotion
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-07-13'
manual_validation_pending: true
decision_owner: leiwenjun
summary_zh: 为 PCR02 SSC305 SDK 记录 hash-bound owner attestation 已接受 source/Hub/Obsidian 权威分工；候选继续 reviewing，真实验证与发布证据仍待补齐。
promotion_decision: none; owner boundary attested, no active promotion or evidence-ready claim
path: projects/pcr02-ssc305/decisions/project-boundary-decision-candidate.md
project_id: pcr02-ssc305
readiness_slot: decision
aliases:
- pcr02-ssc305 decision
- pcr02-ssc305-decision
related:
- projects/pcr02-ssc305/README.md
- projects/pcr02-ssc305/current/project-profile.md
- projects/pcr02-ssc305/current/runbooks/maintenance-entry.md
- projects/pcr02-ssc305/validation/project-readiness.md
---

# PCR02 SSC305 SDK 权威与维护边界决策候选

## 决策状态

- decision owner：`leiwenjun`
- 状态：`reviewing`
- 当前决定：`accept-authority-boundary-remain-reviewing`
- 禁止解释：本 attestation 只接受方案 A 的权威分工并绑定 owner；不等于 active promotion、evidence-ready、源码变更或发布授权。

## 待决问题

如何在源项目、Knowledge Hub、Obsidian 和本机运行态之间分配当前事实、长期知识、呈现和授权责任？

## 已确认事实

- 项目 ID、名称、类型、group、repo boundary 和 canonical 路径来自 `registry/projects.json`。
- Git remote key、workspace logical ref 和 lifecycle 来自 `registry/repositories.json`。
- Knowledge Hub 的 Markdown 是长期正文，registry 是生命周期与授权账本；Obsidian 只消费同一份 Markdown。
- 源码、设备行为和发布状态必须由源项目与真实验证证明。

## 方案

| 方案 | 说明 | 风险 |
|---|---|---|
| A | 源项目保存当前事实；Hub 保存受治理摘要/决策/验证；Obsidian 只读呈现 | 需要维护 source-to-Hub 证据引用 |
| B | 在 Hub 复制完整源码文档并作为当前事实 | 容易漂移、重复和误提升，不建议 |
| C | 只依赖会话记忆或个人笔记 | 不可审计、不可稳定复现，不接受 |

## 建议候选

Owner `leiwenjun` 已通过 hash-bound attestation 接受方案 A。候选继续保持 `reviewing`；真实验证、制品/设备、发布、回滚和采用证据未闭环前不得提升。

## 后续仍需补齐

- 参与者与责任分工（decision owner 已绑定为 `leiwenjun`）
- 真实验证、发布与回滚的接受/修改/拒绝及理由
- source of truth、适用版本和失效条件
- 验证命令/环境/制品/设备证据
- 回滚路径和下一次 `review_after`

## Related

- [项目画像候选](../current/project-profile.md)
- [维护 runbook](../current/runbooks/maintenance-entry.md)
- [readiness validation](../validation/project-readiness.md)
- [项目入口](../README.md)
