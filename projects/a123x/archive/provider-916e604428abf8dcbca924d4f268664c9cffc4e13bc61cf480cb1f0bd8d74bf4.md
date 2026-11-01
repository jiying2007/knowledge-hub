---
id: provider-916e604428abf8dcbca924d4f268664c9cffc4e13bc61cf480cb1f0bd8d74bf4
title: A123X独立接口：MBI_CVE_Dilate
kind: runbook
domain: projects/a123x
path: projects/a123x/archive/provider-916e604428abf8dcbca924d4f268664c9cffc4e13bc61cf480cb1f0bd8d74bf4.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: provider-candidate-archive
  from: operation:916e604428abf8dcbca924d4f268664c9cffc4e13bc61cf480cb1f0bd8d74bf4
  source_sha256: 57afa068c39a74669bdbeea0b3fa18be64fc3fdd12a8467f1221ceb51243f9d2
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
- cve
- document-described
- MBI_CVE_Dilate
validation_refs:
- projects/a123x/archive/provider-916e604428abf8dcbca924d4f268664c9cffc4e13bc61cf480cb1f0bd8d74bf4.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/a123x/archive/provider-916e604428abf8dcbca924d4f268664c9cffc4e13bc61cf480cb1f0bd8d74bf4.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-10-24'
updated_at: '2026-10-24'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-10-24'
manual_validation_pending: true
summary_zh: A123X RC1 MBI_CVE_Dilate；视觉计算；当前声明：MBP_S32 MBI_CVE_Dilate(CVE_HANDLE *pCveHandle, CVE_SRC_IMAGE_T *pstSrc, CVE_DST_IMAGE_T
  *pstDst, CVE_DILATE_CTRL_T *pstDilateCtrl, MBP_BOOL_E bInstant);；文档用途：Creates a 5x5 template dilate task for binary images.；来源：mbi_cve.h:51
  头SHA256 75100801beb6b53e32efcf50e875f724e6b2c539a434900a39ac5e7c5462369b；手册IPC SDK CVE MBI (0.7).pdf物理页29；reviewing；实际库/ABI/设备未验证。
primary_language: zh-CN
source_language: en
translation_status: partial
terminology_status: pending
subject_ref: &id001
  type: project
  id: a123x
created_subject_ref: *id001
principal_id: local-user
provider_operation_id: 916e604428abf8dcbca924d4f268664c9cffc4e13bc61cf480cb1f0bd8d74bf4
provenance:
  source_kind: session-conclusion
  source_ref: sanitized-conclusion
  verification_state: declared
---

# A123X独立接口：MBI_CVE_Dilate

证据等级：文档说明级，未经实际库验证。
适用快照：IPC C5 RC1；2026-10-24来源核验。

## 当前接口声明

`MBP_S32 MBI_CVE_Dilate(CVE_HANDLE *pCveHandle, CVE_SRC_IMAGE_T *pstSrc, CVE_DST_IMAGE_T *pstDst, CVE_DILATE_CTRL_T *pstDilateCtrl, MBP_BOOL_E bInstant);`

来源：workspaces/ipc-c5-rc.1.0/linux/mbp/mbi/cve/include/mbi_cve.h:51；SHA256 75100801beb6b53e32efcf50e875f724e6b2c539a434900a39ac5e7c5462369b。

## 文档明确内容

以下为该接口章节的字段摘录，保留英文以避免参数和单位被自动翻译改变。头文件声明与文档说明分别留证；未声称两者ABI一致。

用途：

Creates a 5x5 template dilate task for binary images.

文档声明（与当前头文件分别留证）：

MBP_S32 MBI_CVE_Dilate(CVE_HANDLE *pCveHandle, CVE_SRC_IMAGE_T *pstSrc, CVE_DST_IMAGE_T
*pstDst,CVE_DILATE_CTRL_T *pstDilateCtrl, MBP_BOOL_E bInstant)

参数说明：

Parameter
Description input/output
name
pCveHandle Pointer to the handle, can not be null output
pstSrc Pointer to the source data, can not be null input
Pointer to the output data, can not be null.The height and width are the
pstDst output
same as those of Src
pstDilateCtrl Dilate control parameter pointer,can not be null input
bInstant Return the result flag in time input

返回值：

Return value Description
0 success
non-zero failure

调用约束：

The template coefficient must be 0 or 255.
The following dilate template samples:
Figure 2.9 show dilate formula

芯片差异：

No.

文档依赖：

Header file:mbi_cve.h,mbp_cve.h,mbp_comm_cve.h.
Library file:

来源：downloads/IPC SDK Documents/IPC SDK CVE MBI (0.7).pdf；物理页29起，章节2.10；SHA256 c64e8de7510cf5ac52de3575680c1c8cc3a78775bd77410670baad32e0a4aa7c。

## 尚未闭环

- 实际库导出、ABI和运行行为尚未验证；源码/文档说明不代表板级、设备或量产结论。

证据更新条件：对应头、文档或实际库身份变化时重新核验；本条为reviewing候选。
