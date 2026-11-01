---
id: provider-c59a0bdf056475a62eea247c4c1bfd115a54f777ebe8ebf4473e16f673dbd5fb
title: A123X独立接口：MBI_CVE_MagAndAng
kind: runbook
domain: projects/a123x
path: projects/a123x/archive/provider-c59a0bdf056475a62eea247c4c1bfd115a54f777ebe8ebf4473e16f673dbd5fb.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: provider-candidate-archive
  from: operation:c59a0bdf056475a62eea247c4c1bfd115a54f777ebe8ebf4473e16f673dbd5fb
  source_sha256: 272d01859ea16835e4d09d1b5bd223189a296f4c87c04a665354b7e6873c98e4
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
- MBI_CVE_MagAndAng
validation_refs:
- projects/a123x/archive/provider-c59a0bdf056475a62eea247c4c1bfd115a54f777ebe8ebf4473e16f673dbd5fb.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/a123x/archive/provider-c59a0bdf056475a62eea247c4c1bfd115a54f777ebe8ebf4473e16f673dbd5fb.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-10-24'
updated_at: '2026-10-24'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-10-24'
manual_validation_pending: true
summary_zh: A123X RC1 MBI_CVE_MagAndAng；视觉计算；当前声明：MBP_S32 MBI_CVE_MagAndAng(CVE_HANDLE *pCveHandle, CVE_SRC_IMAGE_T *pstSrc,
  CVE_DST_IMAGE_T *pstDstMag, CVE_DST_IMAGE_T *pstDstAng, CVE_MAG_AND_ANG_CTRL_T *pstMagAndAngCtrl, MBP_BOOL_E bInstant);；文档用途：Create
  a 5x5 filter template task for calculating the gradient magnitude and angle.；来源：mbi_cve.h:62 头SHA256 75100801beb6b53e32efcf50e875f724e6b2c539a434900a39ac5e7c5462369b；手册IPC
  SDK CVE MBI (0.7).pdf物理页23；reviewing；实际库/ABI/设备未验证。
primary_language: zh-CN
source_language: en
translation_status: partial
terminology_status: pending
subject_ref: &id001
  type: project
  id: a123x
created_subject_ref: *id001
principal_id: local-user
provider_operation_id: c59a0bdf056475a62eea247c4c1bfd115a54f777ebe8ebf4473e16f673dbd5fb
provenance:
  source_kind: session-conclusion
  source_ref: sanitized-conclusion
  verification_state: declared
---

# A123X独立接口：MBI_CVE_MagAndAng

证据等级：文档说明级，未经实际库验证。
适用快照：IPC C5 RC1；2026-10-24来源核验。

## 当前接口声明

`MBP_S32 MBI_CVE_MagAndAng(CVE_HANDLE *pCveHandle, CVE_SRC_IMAGE_T *pstSrc, CVE_DST_IMAGE_T *pstDstMag, CVE_DST_IMAGE_T *pstDstAng, CVE_MAG_AND_ANG_CTRL_T *pstMagAndAngCtrl, MBP_BOOL_E bInstant);`

来源：workspaces/ipc-c5-rc.1.0/linux/mbp/mbi/cve/include/mbi_cve.h:62；SHA256 75100801beb6b53e32efcf50e875f724e6b2c539a434900a39ac5e7c5462369b。

## 文档明确内容

以下为该接口章节的字段摘录，保留英文以避免参数和单位被自动翻译改变。头文件声明与文档说明分别留证；未声称两者ABI一致。

用途：

Create a 5x5 filter template task for calculating the gradient magnitude and angle.

文档声明（与当前头文件分别留证）：

MBP_S32 MBI_CVE_MagAndAng(CVE_HANDLE *pCveHandle, CVE_SRC_IMAGE_T *pstSrc, CVE_DST_IMAGE_T
*pstDstMag, CVE_DST_IMAGE_T *pstDstAng,CVE_MAG_AND_ANG_CTRL_T *pstMagAndAngCtrl, MBP_BOOL_E
bInstant)

参数说明：

Parameter name Description input/output
pCveHandle Pointer to the handle, can not be null input
pstSrc Pointer to the source data, can not be null input
Output magnitude image pointer, can not be null.The height and width
pstDstMag output
are the same as those of Src
Output Angle image pointer, can not be null.The height and width are
pstDstAng output
the same as those of Src
pstMagAndAngCtrl MagAndAng control parameter pointer,can not be null input
bInstant Return the result flag in time input

返回值：

Return value Description
0 success
non-zero failure

调用约束：

Three output modes are supported，For details, see CVE_MAG_AND_ANG_OUT_CTRL_E.
The algorithm has the following Three output modes,see Figure 2.7.
Figure 2.7 MagAndAng formula
Isrc(xi,yi) corresponds to pstSrc, and coef (mask) corresponds to as8Mask[25] in CVE_MAG_AND_ANG_CTRL_T.
MAG_AND_ANG_OUT_MAG: Output only magnitude.
Mag(x0,y0) corresponds to pstDstMag.
MAG_AND_ANG_OUT_MAG_AND_ANG:Output both magnitude and angle.
Figure 2.8 MagAndAng reg_magandang_mode formula
The value of Ang(x0,y0) is selected from the preceding directions 0-7(reg_magandang_mode = 0) or 0-
8(reg_magandang_mode = 1) based on Hout(x0,y0),Vout(x0,y0) and θ(x0,y0) Mag(x0,y0) corresponds to
pstDstMag,Ang(x0,y0) corresponds to pstDstAng.
MAG_AND_ANG_OUT_HOG: Output both magnitude and angle in HOG mode.
Mag(x0,y0)corresponds to dstPtr[0], Ang(x0,y0) corresponds to dstPtr[1].
You can perform a thresh operation on a magnitude image by using u16Thr in CVE_MAG_AND_ANG_CTRL_T to
implement edge orientation histogram (EOH).The formula is as follows:

芯片差异：

No.

文档依赖：

Header file:mbi_cve.h,mbp_cve.h,mbp_comm_cve.h.
Library file:

来源：downloads/IPC SDK Documents/IPC SDK CVE MBI (0.7).pdf；物理页23起，章节2.7；SHA256 c64e8de7510cf5ac52de3575680c1c8cc3a78775bd77410670baad32e0a4aa7c。

## 尚未闭环

- 实际库导出、ABI和运行行为尚未验证；源码/文档说明不代表板级、设备或量产结论。

证据更新条件：对应头、文档或实际库身份变化时重新核验；本条为reviewing候选。
