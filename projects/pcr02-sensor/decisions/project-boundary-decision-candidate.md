---
id: pcr02-sensor-readiness-decision-20260713
title: PCR02 Sensor Module 权威与维护边界决策候选
kind: decision
domain: projects/pcr02-sensor
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
review_after: '2026-10-13'
review_status: ai-generated-project-readiness-pending-owner-and-real-validation
promotion: none
tags:
- pcr02-sensor
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
decision_owner: unassigned
summary_zh: 为 PCR02 Sensor Module 提供 source/Hub/Obsidian 权威分工的 owner-review 候选；decision owner 尚未指定，当前没有生效决定。
promotion_decision: none; structural readiness asset only, no active promotion or owner decision
path: projects/pcr02-sensor/decisions/project-boundary-decision-candidate.md
project_id: pcr02-sensor
readiness_slot: decision
aliases:
- pcr02-sensor decision
- pcr02-sensor-decision
related:
- projects/pcr02-sensor/README.md
- projects/pcr02-sensor/current/project-profile.md
- projects/pcr02-sensor/current/runbooks/maintenance-entry.md
- projects/pcr02-sensor/validation/project-readiness.md
---

# PCR02 Sensor Module 权威与维护边界决策候选

## 决策状态

- decision owner：`unassigned`
- 状态：`reviewing`
- 当前决定：未作出
- 禁止解释：本候选不等于 owner approval、active promotion、源码变更或发布授权。

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

建议 owner 选择 A，并明确项目级 owner、验证责任、复核周期和失效条件。该建议在 owner 决策前不生效。

## owner 必填

- decision owner 与参与者
- 接受/修改/拒绝及理由
- source of truth、适用版本和失效条件
- 验证命令/环境/制品/设备证据
- 回滚路径和下一次 `review_after`

## Related

- [项目画像候选](../current/project-profile.md)
- [维护 runbook](../current/runbooks/maintenance-entry.md)
- [readiness validation](../validation/project-readiness.md)
- [项目入口](../README.md)
