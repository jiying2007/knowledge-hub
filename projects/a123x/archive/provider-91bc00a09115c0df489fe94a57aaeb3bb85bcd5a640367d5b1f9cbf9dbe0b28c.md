---
id: provider-91bc00a09115c0df489fe94a57aaeb3bb85bcd5a640367d5b1f9cbf9dbe0b28c
title: A123X：IIO缓冲格式le:u12/16大于大于0应该如何解析
kind: runbook
domain: projects/a123x
path: projects/a123x/archive/provider-91bc00a09115c0df489fe94a57aaeb3bb85bcd5a640367d5b1f9cbf9dbe0b28c.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: provider-candidate-archive
  from: operation:91bc00a09115c0df489fe94a57aaeb3bb85bcd5a640367d5b1f9cbf9dbe0b28c
  source_sha256: deabe9da5524e57eb401a0816e06e67e605d18691166fd933fd343b1a653ed8b
  temporary_source_retained: false
review_after: '2027-01-22'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- provider-archive
- runbook
- a123x
- SARADC采样
- engineering-answer
validation_refs:
- projects/a123x/archive/provider-91bc00a09115c0df489fe94a57aaeb3bb85bcd5a640367d5b1f9cbf9dbe0b28c.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/a123x/archive/provider-91bc00a09115c0df489fe94a57aaeb3bb85bcd5a640367d5b1f9cbf9dbe0b28c.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-10-24'
updated_at: '2026-10-24'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-10-24'
manual_validation_pending: true
summary_zh: IIO scan type示例le:u12/16>>0表示小端、无符号、12个有效位、以16位存储、右移0位。解码时还要按scan index、启用通道与时间戳布局处理，不能每个通道固定消费12个连续比特。buffer
  enable、length和scan enable属于配置写操作；先确认当前驱动支持及采样所有权，再启用连续采样。 适用：本地对应版本资料的方法知识；实际A123X内核、库、DTS、节点和制品须绑定验证，手册示例不作为当前板配置或实测。 来源：downloads/Kernel/SARADC
  User Guide (0.3).pdf；PDF物理页 17,18；SHA256 9f90f30a7b4584651d4702a53304df873590babcbd349a1cee987ae341fd2c2e
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
subject_ref: &id001
  type: project
  id: a123x
created_subject_ref: *id001
principal_id: local-user
provider_operation_id: 91bc00a09115c0df489fe94a57aaeb3bb85bcd5a640367d5b1f9cbf9dbe0b28c
provenance:
  source_kind: session-conclusion
  source_ref: sanitized-conclusion
  verification_state: declared
---

# IIO缓冲格式le:u12/16大于大于0应该如何解析

IIO scan type示例le:u12/16>>0表示小端、无符号、12个有效位、以16位存储、右移0位。解码时还要按scan index、启用通道与时间戳布局处理，不能每个通道固定消费12个连续比特。buffer enable、length和scan enable属于配置写操作；先确认当前驱动支持及采样所有权，再启用连续采样。

适用边界：本地对应版本资料的方法知识；实际A123X内核、库、DTS、节点和制品须绑定验证，手册示例不作为当前板配置或实测。

来源：downloads/Kernel/SARADC User Guide (0.3).pdf；PDF物理页 17,18；SHA256 9f90f30a7b4584651d4702a53304df873590babcbd349a1cee987ae341fd2c2e

验证状态：2026-10-24原文及必要头文件核对；reviewing候选，未作设备操作或owner人工放行。工程建议不等于当前实现已满足，写操作须另有明确目标及可恢复方案。
