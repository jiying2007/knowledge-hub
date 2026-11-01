---
id: provider-81e9256474b0e8fe8cd61c511ca0715be3c7e3dc2abcd10f8f3171be1dcdb06f
title: A123X独立接口：MBI_VBP_GetSupplementAddr
kind: runbook
domain: projects/a123x
path: projects/a123x/archive/provider-81e9256474b0e8fe8cd61c511ca0715be3c7e3dc2abcd10f8f3171be1dcdb06f.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: provider-candidate-archive
  from: operation:81e9256474b0e8fe8cd61c511ca0715be3c7e3dc2abcd10f8f3171be1dcdb06f
  source_sha256: 5d7bd699cafeeba5b332cce49e4b4c447646105e5eab31f564937dd8c5dfce67
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
- a123x-api-451
- vbp
- declaration-only
- MBI_VBP_GetSupplementAddr
validation_refs:
- projects/a123x/archive/provider-81e9256474b0e8fe8cd61c511ca0715be3c7e3dc2abcd10f8f3171be1dcdb06f.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/a123x/archive/provider-81e9256474b0e8fe8cd61c511ca0715be3c7e3dc2abcd10f8f3171be1dcdb06f.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-10-24'
updated_at: '2026-10-24'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-10-24'
manual_validation_pending: true
summary_zh: A123X RC1 MBI_VBP_GetSupplementAddr；视频缓冲池、获取；当前声明：MBP_S32 MBI_VBP_GetSupplementAddr(VBP_VB_HANDLE vbHandle, VIDEO_SUPPLEMENT_S
  *pstSupplement);；文档用途：未定位唯一匹配新版接口章节，仅核声明。；来源：mbi_vbp.h:49 头SHA256 8c449e8e946aff0d15d1b3555cbe0e460dc8e734f215d5652603abea84d361b1；reviewing；实际库/ABI/设备未验证。
primary_language: zh-CN
source_language: en
translation_status: partial
terminology_status: pending
subject_ref: &id001
  type: project
  id: a123x
created_subject_ref: *id001
principal_id: local-user
provider_operation_id: 81e9256474b0e8fe8cd61c511ca0715be3c7e3dc2abcd10f8f3171be1dcdb06f
provenance:
  source_kind: session-conclusion
  source_ref: sanitized-conclusion
  verification_state: declared
---

# A123X独立接口：MBI_VBP_GetSupplementAddr

证据等级：声明级，语义待补齐。
适用快照：IPC C5 RC1；2026-10-24来源核验。

## 当前接口声明

`MBP_S32 MBI_VBP_GetSupplementAddr(VBP_VB_HANDLE vbHandle, VIDEO_SUPPLEMENT_S *pstSupplement);`

来源：workspaces/ipc-c5-rc.1.0/linux/mbp/mbi/mbi_base/include/mbi_vbp.h:49；SHA256 8c449e8e946aff0d15d1b3555cbe0e460dc8e734f215d5652603abea84d361b1。

## 尚未闭环

- 实际库导出、ABI和运行行为尚未验证；源码/文档说明不代表板级、设备或量产结论。
- 当前13份新版MBI手册中未定位唯一完整接口章节；本条仅证实头文件声明，功能、参数单位和调用约束仍待提炼核实。

证据更新条件：对应头、文档或实际库身份变化时重新核验；本条为reviewing候选。
