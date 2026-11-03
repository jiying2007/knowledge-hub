---
id: provider-71efcd6faeaf736149075ca984fc4a4f12e52c9b57c8dd7a02a6baa61b8ad9f7
title: A123X独立接口：MBI_ISP_FPNCalibrate
kind: runbook
domain: projects/a123x
path: projects/a123x/archive/provider-71efcd6faeaf736149075ca984fc4a4f12e52c9b57c8dd7a02a6baa61b8ad9f7.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: provider-candidate-archive
  from: operation:71efcd6faeaf736149075ca984fc4a4f12e52c9b57c8dd7a02a6baa61b8ad9f7
  source_sha256: db8119e1c00a78974fe02ced3a05bbdcf6aef93dd40af3c2989bc64a82e771f4
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
- isp
- document-described
- MBI_ISP_FPNCalibrate
validation_refs:
- projects/a123x/archive/provider-71efcd6faeaf736149075ca984fc4a4f12e52c9b57c8dd7a02a6baa61b8ad9f7.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/a123x/archive/provider-71efcd6faeaf736149075ca984fc4a4f12e52c9b57c8dd7a02a6baa61b8ad9f7.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-10-24'
updated_at: '2026-10-24'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-10-24'
manual_validation_pending: true
summary_zh: A123X RC1 MBI_ISP_FPNCalibrate；图像处理；当前声明：MBP_S32 MBI_ISP_FPNCalibrate(VI_PIPE ViPipe, ISP_FPN_LUT_ATTR_T *pstCalibrateAttr);；文档用途：Sets
  the calibration attribute of the FPN(Fixed Pattern Noise) removal module.；来源：mbi_isp.h:215 头SHA256 2a1ff1e69916846d48f35f17f16b624fa9d934b9acbbc3ba9b2c886939184bc8；手册IPC
  SDK ISP MBI (02).pdf物理页104；reviewing；实际库/ABI/设备未验证。
primary_language: zh-CN
source_language: en
translation_status: partial
terminology_status: pending
subject_ref: &id001
  type: project
  id: a123x
created_subject_ref: *id001
principal_id: local-user
provider_operation_id: 71efcd6faeaf736149075ca984fc4a4f12e52c9b57c8dd7a02a6baa61b8ad9f7
provenance:
  source_kind: session-conclusion
  source_ref: sanitized-conclusion
  verification_state: declared
---

# A123X独立接口：MBI_ISP_FPNCalibrate

证据等级：文档说明级，未经实际库验证。
适用快照：IPC C5 RC1；2026-10-24来源核验。

## 当前接口声明

`MBP_S32 MBI_ISP_FPNCalibrate(VI_PIPE ViPipe, ISP_FPN_LUT_ATTR_T *pstCalibrateAttr);`

来源：workspaces/ipc-c5-rc.1.0/linux/mbp/mbi/isp/include/mbi_isp.h:215；SHA256 2a1ff1e69916846d48f35f17f16b624fa9d934b9acbbc3ba9b2c886939184bc8。

## 文档明确内容

以下为该接口章节的字段摘录，保留英文以避免参数和单位被自动翻译改变。头文件声明与文档说明分别留证；未声称两者ABI一致。

用途：

Sets the calibration attribute of the FPN(Fixed Pattern Noise) removal module.

文档声明（与当前头文件分别留证）：

MBP_S32 MBI_ISP_FPNCalibrate(VI_PIPE ViPipe, ISP_FPN_LUT_ATTR_T *pstCalibrateAttr);

参数说明：

Parameter name Description input/output
ViPipe VI pipe ID. Input
pstCalibrateAttr Pointer to the calibration attribute of the FPN removal module. Input

返回值：

Return value Description
0 success
non-zero failure

调用约束：

No

芯片差异：

No.

文档依赖：

Header file:mbi_isp.h,mbp_comm_isp.h
Library file:libmbi_isp.so

来源：downloads/IPC SDK Documents/IPC SDK ISP MBI (02).pdf；物理页104起，章节2.98；SHA256 5c9c6f0a03e0529f82e5d4062f3c5b2b273fd69401a7151e2c6a6b8d229ca213。

## 尚未闭环

- 实际库导出、ABI和运行行为尚未验证；源码/文档说明不代表板级、设备或量产结论。
- ISP相关语义仍待实现/供应商/库绑定验证。曝光时间存在头文件us与手册x/4096ms差异，增益存在Q22.10与log2/4096差异，AWB使能/旁路字段亦有差异；涉及这些字段时不得直接换算或下发。

证据更新条件：对应头、文档或实际库身份变化时重新核验；本条为reviewing候选。
