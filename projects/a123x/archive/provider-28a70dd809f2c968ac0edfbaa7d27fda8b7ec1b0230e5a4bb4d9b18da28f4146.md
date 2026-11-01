---
id: provider-28a70dd809f2c968ac0edfbaa7d27fda8b7ec1b0230e5a4bb4d9b18da28f4146
title: A123X独立知识卡：CB400 PERIPHERALS DEVWIRE EVT1配置区别
kind: runbook
domain: projects/a123x
path: projects/a123x/archive/provider-28a70dd809f2c968ac0edfbaa7d27fda8b7ec1b0230e5a4bb4d9b18da28f4146.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: provider-candidate-archive
  from: operation:28a70dd809f2c968ac0edfbaa7d27fda8b7ec1b0230e5a4bb4d9b18da28f4146
  source_sha256: e28b76ca208e8b90f2b4a3ba17a84f2a0a1f6fc639d141ee5abe1bde16390dac
  temporary_source_retained: false
review_after: '2027-01-21'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- provider-archive
- runbook
- a123x-answer-card-v2
- question
validation_refs:
- projects/a123x/archive/provider-28a70dd809f2c968ac0edfbaa7d27fda8b7ec1b0230e5a4bb4d9b18da28f4146.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/a123x/archive/provider-28a70dd809f2c968ac0edfbaa7d27fda8b7ec1b0230e5a4bb4d9b18da28f4146.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-10-23'
updated_at: '2026-10-23'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-10-23'
manual_validation_pending: true
summary_zh: A123X知识卡v2；2026-10-23 RC1候选；原厂CB400目标保留供应商默认；CB400_PERIPHERALS承接外围和调试定制；F20_DEVWIRE为飞线候选；F20_EVT1仍是参考骨架。CB400
  LP5与F20 LP4X硬件不混用DDR训练或启动配置，编译通过不证明正式EVT板可烧录。 来源：integration/docs/sdk-native-inputs.md；project/02-architecture/hardware/CB400-USER-MANUAL.md
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
subject_ref: &id001
  type: project
  id: a123x
created_subject_ref: *id001
principal_id: local-user
provider_operation_id: 28a70dd809f2c968ac0edfbaa7d27fda8b7ec1b0230e5a4bb4d9b18da28f4146
provenance:
  source_kind: session-conclusion
  source_ref: sanitized-conclusion
  verification_state: declared
---

# A123X独立知识卡：CB400 PERIPHERALS DEVWIRE EVT1配置区别

原厂CB400目标保留供应商默认；CB400_PERIPHERALS承接外围和调试定制；F20_DEVWIRE为飞线候选；F20_EVT1仍是参考骨架。CB400 LP5与F20 LP4X硬件不混用DDR训练或启动配置，编译通过不证明正式EVT板可烧录。

来源：integration/docs/sdk-native-inputs.md；project/02-architecture/hardware/CB400-USER-MANUAL.md

适用边界：本地RC1源码/文档快照；reviewing候选，未执行新的设备验证。来源变化须刷新本条，不以目录或其他知识卡替代其证据。
