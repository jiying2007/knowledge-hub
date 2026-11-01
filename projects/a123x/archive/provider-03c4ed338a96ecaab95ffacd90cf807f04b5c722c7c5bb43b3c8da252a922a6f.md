---
id: provider-03c4ed338a96ecaab95ffacd90cf807f04b5c722c7c5bb43b3c8da252a922a6f
title: A123X独立接口：aml_asp_create
kind: runbook
domain: projects/a123x
path: projects/a123x/archive/provider-03c4ed338a96ecaab95ffacd90cf807f04b5c722c7c5bb43b3c8da252a922a6f.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: provider-candidate-archive
  from: operation:03c4ed338a96ecaab95ffacd90cf807f04b5c722c7c5bb43b3c8da252a922a6f
  source_sha256: a62d0c847b00243e79f9f077c3d590c3b22e2654c0a58305c96a557e16091a2d
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
- a123x-non-mbi
- aml_asp_create
- header-described
validation_refs:
- projects/a123x/archive/provider-03c4ed338a96ecaab95ffacd90cf807f04b5c722c7c5bb43b3c8da252a922a6f.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/a123x/archive/provider-03c4ed338a96ecaab95ffacd90cf807f04b5c722c7c5bb43b3c8da252a922a6f.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-10-24'
updated_at: '2026-10-24'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-10-24'
manual_validation_pending: true
summary_zh: A123X RC1 音频算法ASP；aml_asp_create；当前声明：void *aml_asp_create(AI_ASP_CONFIG_S *config);；头注释用途：@brief Create and initialize
  the ASP with the specified configuration parameters.；来源：aml_audio_signal_process.h:203 SHA256 79f407e199c8cadede314093dac1fe28dc78efd90e6b279921090d14b002fbea；实际库/ABI/设备未验证，reviewing候选。
primary_language: zh-CN
source_language: en
translation_status: partial
terminology_status: pending
subject_ref: &id001
  type: project
  id: a123x
created_subject_ref: *id001
principal_id: local-user
provider_operation_id: 03c4ed338a96ecaab95ffacd90cf807f04b5c722c7c5bb43b3c8da252a922a6f
provenance:
  source_kind: session-conclusion
  source_ref: sanitized-conclusion
  verification_state: declared
---

# A123X独立接口：aml_asp_create

接口族：音频算法ASP。证据等级：header-described。

当前声明：`void *aml_asp_create(AI_ASP_CONFIG_S *config);`

头文件紧邻注释中明确的信息（原文保留；不作为已验证实现）：

### brief

@brief Create and initialize the ASP with the specified configuration parameters.

### param

@param[in] config         ASP specified @ref AI_ASP_CONFIG_S configuration pointer

### return

@return    ASP instance pointer

来源：workspaces/ipc-c5-rc.1.0/linux/mbp/mbi/audio_process/include/aml_audio_signal_process.h:203；注释起始行198；SHA256 79f407e199c8cadede314093dac1fe28dc78efd90e6b279921090d14b002fbea。

适用边界：只说明本地RC1头文件快照。NN两套API族与MBI_ADLA分别保留，未证明模型、上下文、DMA缓存或版本可互换。实际导出、ABI布局、状态机和板级/设备/量产未验证。reviewing候选，不作active规范。
