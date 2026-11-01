---
id: provider-2be4f0cc45dc912d8107b54b11df8dbdcdd5fe54a8cbbe1d179482d69018e9df
title: A123X独立接口：MBI_GE2D_BitmapBlend
kind: runbook
domain: projects/a123x
path: projects/a123x/archive/provider-2be4f0cc45dc912d8107b54b11df8dbdcdd5fe54a8cbbe1d179482d69018e9df.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: provider-candidate-archive
  from: operation:2be4f0cc45dc912d8107b54b11df8dbdcdd5fe54a8cbbe1d179482d69018e9df
  source_sha256: c1aa32ae42b9194df2ceff8e5b8cdd8c13fee33512973795b51343e6aa272f88
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
- ge2d
- document-described
- MBI_GE2D_BitmapBlend
validation_refs:
- projects/a123x/archive/provider-2be4f0cc45dc912d8107b54b11df8dbdcdd5fe54a8cbbe1d179482d69018e9df.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/a123x/archive/provider-2be4f0cc45dc912d8107b54b11df8dbdcdd5fe54a8cbbe1d179482d69018e9df.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-10-24'
updated_at: '2026-10-24'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-10-24'
manual_validation_pending: true
summary_zh: A123X RC1 MBI_GE2D_BitmapBlend；二维图形、位图；当前声明：MBP_S32 MBI_GE2D_BitmapBlend(GE2D_HANDLE handle, const GE2D_SURFACE_T
  *pstBackGround, const GE2D_RECT_T *pstBackGroundRect, const GE2D_SURFACE_T *pstForeGround, const GE2D_RECT_T *pstForeGroundRect,
  const GE2D_SURFACE_T *pstDst, const GE2D_RECT_T *pstDstRect, MBP_U8 u8Alpha, GE2D_ALUCMD_E enBlendMode);；文档用途：Overlay bitmap
  to target area.；来源：mbi_ge2d.h:61 头SHA256 127b92d7864dd2faf71649c79213f0a7a816ca77f2f5d64bf404dc6c77a15f07；手册IPC SDK GE2D
  MBI (0.6).pdf物理页16；reviewing；实际库/ABI/设备未验证。
primary_language: zh-CN
source_language: en
translation_status: partial
terminology_status: pending
subject_ref: &id001
  type: project
  id: a123x
created_subject_ref: *id001
principal_id: local-user
provider_operation_id: 2be4f0cc45dc912d8107b54b11df8dbdcdd5fe54a8cbbe1d179482d69018e9df
provenance:
  source_kind: session-conclusion
  source_ref: sanitized-conclusion
  verification_state: declared
---

# A123X独立接口：MBI_GE2D_BitmapBlend

证据等级：文档说明级，未经实际库验证。
适用快照：IPC C5 RC1；2026-10-24来源核验。

## 当前接口声明

`MBP_S32 MBI_GE2D_BitmapBlend(GE2D_HANDLE handle, const GE2D_SURFACE_T *pstBackGround, const GE2D_RECT_T *pstBackGroundRect, const GE2D_SURFACE_T *pstForeGround, const GE2D_RECT_T *pstForeGroundRect, const GE2D_SURFACE_T *pstDst, const GE2D_RECT_T *pstDstRect, MBP_U8 u8Alpha, GE2D_ALUCMD_E enBlendMode);`

来源：workspaces/ipc-c5-rc.1.0/linux/mbp/mbi/mbi_base/include/mbi_ge2d.h:61；SHA256 127b92d7864dd2faf71649c79213f0a7a816ca77f2f5d64bf404dc6c77a15f07。

## 文档明确内容

以下为该接口章节的字段摘录，保留英文以避免参数和单位被自动翻译改变。头文件声明与文档说明分别留证；未声称两者ABI一致。

用途：

Overlay bitmap to target area.

文档声明（与当前头文件分别留证）：

MBP_S32 MBI_GE2D_BitmapBlend(GE2D_HANDLE handle, const GE2D_SURFACE_T *pstBackGround,
const GE2D_RECT_T *pstBackGroundRect, const GE2D_SURFACE_T *pstForeGround, const GE2D_RECT_T
*pstForeGroundRect, const GE2D_SURFACE_T *pstDst, const GE2D_RECT_T *pstDstRect, MBP_U8 u8Alpha,
GE2D_ALUCMD_E enBlendMode);

参数说明：

Parameter name Description input/output
handle Indicates the HANDLE of a started job. input
pstBackGround Background canvas pointer. input
Parameter name Description input/output
pstBackGroundRect Background canvas attribute. input
pstForeGround Foreground canvas pointer. input
pstForeGroundRect Foreground canvas attribute. input
pstDst Target canvas pointer. output
pstDstRect Target canvas attribute. output
u8Alpha transparency. input
enBlendMode Mode selection of transparency overlay. input

返回值：

Return value Description
0 success.
non-zero failure, see error code.

调用约束：

The job identified by the hHandle must be a started job.

芯片差异：

No.

文档依赖：

Header file: mbi_ge2d.h, mbp_comm_ge2d.h.
Library file: No.

来源：downloads/IPC SDK Documents/IPC SDK GE2D MBI (0.6).pdf；物理页16起，章节2.11；SHA256 ea0ad85cf86c65bdc1c0823bad7d07071d4b35d006e4cc4b4a975bf2ed2dafc9。

## 尚未闭环

- 实际库导出、ABI和运行行为尚未验证；源码/文档说明不代表板级、设备或量产结论。

证据更新条件：对应头、文档或实际库身份变化时重新核验；本条为reviewing候选。
