---
id: provider-0a52d772ca8ecd4417a03d6476ecbd17ca0b2efdb400c1dfc9192e9ba8e63c26
title: A123X独立接口：aml_asp_speaker_process
kind: runbook
domain: projects/a123x
path: projects/a123x/archive/provider-0a52d772ca8ecd4417a03d6476ecbd17ca0b2efdb400c1dfc9192e9ba8e63c26.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: provider-candidate-archive
  from: operation:0a52d772ca8ecd4417a03d6476ecbd17ca0b2efdb400c1dfc9192e9ba8e63c26
  source_sha256: d293d682e9a69ab9ca5515f61904122edad41200ee19139bf8f65eb8d92866e8
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
- aml_asp_speaker_process
- header-described
validation_refs:
- projects/a123x/archive/provider-0a52d772ca8ecd4417a03d6476ecbd17ca0b2efdb400c1dfc9192e9ba8e63c26.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/a123x/archive/provider-0a52d772ca8ecd4417a03d6476ecbd17ca0b2efdb400c1dfc9192e9ba8e63c26.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-10-24'
updated_at: '2026-10-24'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-10-24'
manual_validation_pending: true
summary_zh: A123X RC1 音频算法ASP；aml_asp_speaker_process；当前声明：void aml_asp_speaker_process(void *handle, void *data, int size,
  int bypass);；头注释用途：@brief Perform simple post-processing on the audio data need to be play out.；来源：aml_audio_signal_process.h:285
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
provider_operation_id: 0a52d772ca8ecd4417a03d6476ecbd17ca0b2efdb400c1dfc9192e9ba8e63c26
provenance:
  source_kind: session-conclusion
  source_ref: sanitized-conclusion
  verification_state: declared
---

# A123X独立接口：aml_asp_speaker_process

接口族：音频算法ASP。证据等级：header-described。

当前声明：`void aml_asp_speaker_process(void *handle, void *data, int size, int bypass);`

头文件紧邻注释中明确的信息（原文保留；不作为已验证实现）：

### brief

@brief Perform simple post-processing on the audio data need to be play out.

### param

@param[in] handle         pointer of ASP instance which created by @ref aml_asp_create.
@param[in] data           pointer for the audio buffer need to be play out and the processed data will overwrite the input data.
@param[in] size           size in frame need to be processed in each call
@param[in] bypass         bypass the post-processing

来源：workspaces/ipc-c5-rc.1.0/linux/mbp/mbi/audio_process/include/aml_audio_signal_process.h:285；注释起始行278；SHA256 79f407e199c8cadede314093dac1fe28dc78efd90e6b279921090d14b002fbea。

适用边界：只说明本地RC1头文件快照。NN两套API族与MBI_ADLA分别保留，未证明模型、上下文、DMA缓存或版本可互换。实际导出、ABI布局、状态机和板级/设备/量产未验证。reviewing候选，不作active规范。
