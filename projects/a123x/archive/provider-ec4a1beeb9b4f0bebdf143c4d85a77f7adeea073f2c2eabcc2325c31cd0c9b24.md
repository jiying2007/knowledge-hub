---
id: provider-ec4a1beeb9b4f0bebdf143c4d85a77f7adeea073f2c2eabcc2325c31cd0c9b24
title: A123X独立接口：aml_util_disableProfile
kind: runbook
domain: projects/a123x
path: projects/a123x/archive/provider-ec4a1beeb9b4f0bebdf143c4d85a77f7adeea073f2c2eabcc2325c31cd0c9b24.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: provider-candidate-archive
  from: operation:ec4a1beeb9b4f0bebdf143c4d85a77f7adeea073f2c2eabcc2325c31cd0c9b24
  source_sha256: ac487fe13c75be5e58e6dc00ab96ee5e694fcdd4062304e92a55d64734045414
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
- aml_util_disableProfile
- header-described
validation_refs:
- projects/a123x/archive/provider-ec4a1beeb9b4f0bebdf143c4d85a77f7adeea073f2c2eabcc2325c31cd0c9b24.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/a123x/archive/provider-ec4a1beeb9b4f0bebdf143c4d85a77f7adeea073f2c2eabcc2325c31cd0c9b24.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-10-24'
updated_at: '2026-10-24'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-10-24'
manual_validation_pending: true
summary_zh: A123X RC1 NN SDK上下文及缓冲管理；aml_util_disableProfile；当前声明：NNSDK_Status aml_util_disableProfile(void* context, aml_profiling_data_t*
  profile_data);；头注释用途：@brief Didable profile.；来源：nn_sdk.h:1085 SHA256 3ac25e1ece9a294eb6c8df34c3a41ecbe8757b6246220d53d5d51ea339d905f6；实际库/ABI/设备未验证，reviewing候选。
primary_language: zh-CN
source_language: en
translation_status: partial
terminology_status: pending
subject_ref: &id001
  type: project
  id: a123x
created_subject_ref: *id001
principal_id: local-user
provider_operation_id: ec4a1beeb9b4f0bebdf143c4d85a77f7adeea073f2c2eabcc2325c31cd0c9b24
provenance:
  source_kind: session-conclusion
  source_ref: sanitized-conclusion
  verification_state: declared
---

# A123X独立接口：aml_util_disableProfile

接口族：NN SDK上下文及缓冲管理。证据等级：header-described。

当前声明：`NNSDK_Status aml_util_disableProfile(void* context, aml_profiling_data_t* profile_data);`

头文件紧邻注释中明确的信息（原文保留；不作为已验证实现）：

### brief

@brief Didable profile.

### param

@param context Aml runtime context pointer.
@param profile_data Profile data pointer.

### return

@return Status code (0 for success, non-zero indicates failure).

来源：workspaces/ipc-c5-rc.1.0/linux/mbp/mbi/adla/include/nn_sdk.h:1085；注释起始行1078；SHA256 3ac25e1ece9a294eb6c8df34c3a41ecbe8757b6246220d53d5d51ea339d905f6。

适用边界：只说明本地RC1头文件快照。NN两套API族与MBI_ADLA分别保留，未证明模型、上下文、DMA缓存或版本可互换。实际导出、ABI布局、状态机和板级/设备/量产未验证。reviewing候选，不作active规范。
