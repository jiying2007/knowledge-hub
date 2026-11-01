---
id: provider-7fd9ecc6c29fff0ef8dc96259b8719cccb7e0a49fd5bea8ada19a39f71f1a5df
title: A123X独立接口：aml_asp_destroy
kind: runbook
domain: projects/a123x
path: projects/a123x/archive/provider-7fd9ecc6c29fff0ef8dc96259b8719cccb7e0a49fd5bea8ada19a39f71f1a5df.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: provider-candidate-archive
  from: operation:7fd9ecc6c29fff0ef8dc96259b8719cccb7e0a49fd5bea8ada19a39f71f1a5df
  source_sha256: 424dd7d5150cdec4bf1a8605d470c67a27529c8ee0a47d86ef44b75e3c35f86d
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
- aml_asp_destroy
- header-described
validation_refs:
- projects/a123x/archive/provider-7fd9ecc6c29fff0ef8dc96259b8719cccb7e0a49fd5bea8ada19a39f71f1a5df.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/a123x/archive/provider-7fd9ecc6c29fff0ef8dc96259b8719cccb7e0a49fd5bea8ada19a39f71f1a5df.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-10-24'
updated_at: '2026-10-24'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-10-24'
manual_validation_pending: true
summary_zh: A123X RC1 音频算法ASP；aml_asp_destroy；当前声明：void aml_asp_destroy(void *handle);；头注释用途：@brief Destroys the ASP instance
  and releases all associated resource. Frees all internal memory and sets the ASP Instance to NULL.；来源：aml_audio_signal_process.h:209
  SHA256 79f407e199c8cadede314093dac1fe28dc78efd90e6b279921090d14b002fbea；实际库/ABI/设备未验证，reviewing候选。
primary_language: zh-CN
source_language: en
translation_status: partial
terminology_status: pending
subject_ref: &id001
  type: project
  id: a123x
created_subject_ref: *id001
principal_id: local-user
provider_operation_id: 7fd9ecc6c29fff0ef8dc96259b8719cccb7e0a49fd5bea8ada19a39f71f1a5df
provenance:
  source_kind: session-conclusion
  source_ref: sanitized-conclusion
  verification_state: declared
---

# A123X独立接口：aml_asp_destroy

接口族：音频算法ASP。证据等级：header-described。

当前声明：`void aml_asp_destroy(void *handle);`

头文件紧邻注释中明确的信息（原文保留；不作为已验证实现）：

### brief

@brief Destroys the ASP instance and releases all associated resource. Frees all internal memory and sets the ASP Instance to NULL.

### param

@param[in] handle         pointer of ASP instance which created by @ref aml_asp_create

来源：workspaces/ipc-c5-rc.1.0/linux/mbp/mbi/audio_process/include/aml_audio_signal_process.h:209；注释起始行205；SHA256 79f407e199c8cadede314093dac1fe28dc78efd90e6b279921090d14b002fbea。

适用边界：只说明本地RC1头文件快照。NN两套API族与MBI_ADLA分别保留，未证明模型、上下文、DMA缓存或版本可互换。实际导出、ABI布局、状态机和板级/设备/量产未验证。reviewing候选，不作active规范。

生命周期注意：参数为void*按值传入；不能据头注释“sets ... NULL”断言调用者的句柄变量已置空。实际资源释放和并发退出仍待实现/库证据。
