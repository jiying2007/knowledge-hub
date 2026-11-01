---
id: provider-e5bdaadf7c54b310335b06032424a85c0b48ecfbcbfab90de2cec966788b9ff3
title: A123X独立接口：MBI_CVE_RESIZE
kind: runbook
domain: projects/a123x
path: projects/a123x/archive/provider-e5bdaadf7c54b310335b06032424a85c0b48ecfbcbfab90de2cec966788b9ff3.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: provider-candidate-archive
  from: operation:e5bdaadf7c54b310335b06032424a85c0b48ecfbcbfab90de2cec966788b9ff3
  source_sha256: 50b17332ee1b93c223cfbf2b350ab0ea0c04f0de2a2c455d6e6f7fb4bf6f6bdd
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
- MBI_CVE_RESIZE
validation_refs:
- projects/a123x/archive/provider-e5bdaadf7c54b310335b06032424a85c0b48ecfbcbfab90de2cec966788b9ff3.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/a123x/archive/provider-e5bdaadf7c54b310335b06032424a85c0b48ecfbcbfab90de2cec966788b9ff3.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-10-24'
updated_at: '2026-10-24'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-10-24'
manual_validation_pending: true
summary_zh: A123X RC1 MBI_CVE_RESIZE；视觉计算；当前声明：MBP_S32 MBI_CVE_RESIZE(CVE_HANDLE *pCveHandle, CVE_SRC_IMAGE_T *pstSrcImage,
  CVE_SRC_IMAGE_T *pstSrcImage1, CVE_DST_IMAGE_T *pstDstImage, CVE_DST_IMAGE_T *pstDstImage1, CVE_RESIZE_CTRL_T *pstResizeCtrl,
  MBP_BOOL_E bInstant);；文档用途：Creates an image resize task with support for U8C1 bilinear interpolation.；来源：mbi_cve.h:184 头SHA256
  75100801beb6b53e32efcf50e875f724e6b2c539a434900a39ac5e7c5462369b；手册IPC SDK CVE MBI (0.7).pdf物理页88；reviewing；实际库/ABI/设备未验证。
primary_language: zh-CN
source_language: en
translation_status: partial
terminology_status: pending
subject_ref: &id001
  type: project
  id: a123x
created_subject_ref: *id001
principal_id: local-user
provider_operation_id: e5bdaadf7c54b310335b06032424a85c0b48ecfbcbfab90de2cec966788b9ff3
provenance:
  source_kind: session-conclusion
  source_ref: sanitized-conclusion
  verification_state: declared
---

# A123X独立接口：MBI_CVE_RESIZE

证据等级：文档说明级，未经实际库验证。
适用快照：IPC C5 RC1；2026-10-24来源核验。

## 当前接口声明

`MBP_S32 MBI_CVE_RESIZE(CVE_HANDLE *pCveHandle, CVE_SRC_IMAGE_T *pstSrcImage, CVE_SRC_IMAGE_T *pstSrcImage1, CVE_DST_IMAGE_T *pstDstImage, CVE_DST_IMAGE_T *pstDstImage1, CVE_RESIZE_CTRL_T *pstResizeCtrl, MBP_BOOL_E bInstant);`

来源：workspaces/ipc-c5-rc.1.0/linux/mbp/mbi/cve/include/mbi_cve.h:184；SHA256 75100801beb6b53e32efcf50e875f724e6b2c539a434900a39ac5e7c5462369b。

## 文档明确内容

以下为该接口章节的字段摘录，保留英文以避免参数和单位被自动翻译改变。头文件声明与文档说明分别留证；未声称两者ABI一致。

用途：

Creates an image resize task with support for U8C1 bilinear interpolation.

文档声明（与当前头文件分别留证）：

MBP_S32 MBI_CVE_RESIZE(CVE_HANDLE *pCveHandle, CVE_SRC_IMAGE_T pstSrcImage,
CVE_SRC_IMAGE_TpstSrcImage1, CVE_DST_IMAGE_T *pstDstImage, CVE_DST_IMAGE_T *pstDstImage1,
CVE_RESIZE_CTRL_T *pstResizeCtrl, MBP_BOOL_E bInstant);

参数说明：

Parameter name Description input/output
pCveHandle Pointer to the CVE task handle. input/output
pstSrcImage First source image. input
pstSrcImage1 Second source image. input
pstDstImage First destination image. output
pstDstImage1 Second destination image. output
pstResizeCtrl Resize control parameters. input
bInstant Specifies whether the task result is waited for before the call returns. input

返回值：

Return value Description
0 Success.
non-zero Failure.

调用约束：

The control structure is CVE_RESIZE_CTRL_T , containing forward and inverse scale parameters ( u32ScaleX/Y ,
u32InvScaleX/Y , MBP_U32) and stCrop .

芯片差异：

Chip Name Support
C302X N
C308L N
C302X2 Y
C305X2 Y
A123X Y

文档依赖：

Header file: mbi_cve.h , mbp_cve.h , mbp_comm_cve.h .
Library file: libmbi_cve.so

来源：downloads/IPC SDK Documents/IPC SDK CVE MBI (0.7).pdf；物理页88起，章节2.53；SHA256 c64e8de7510cf5ac52de3575680c1c8cc3a78775bd77410670baad32e0a4aa7c。

## 尚未闭环

- 实际库导出、ABI和运行行为尚未验证；源码/文档说明不代表板级、设备或量产结论。

证据更新条件：对应头、文档或实际库身份变化时重新核验；本条为reviewing候选。
