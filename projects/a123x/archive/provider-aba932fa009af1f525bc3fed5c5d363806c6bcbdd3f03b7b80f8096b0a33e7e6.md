---
id: provider-aba932fa009af1f525bc3fed5c5d363806c6bcbdd3f03b7b80f8096b0a33e7e6
title: A123X独立接口：MBI_MIPI_RX_DisableMipiClock
kind: runbook
domain: projects/a123x
path: projects/a123x/archive/provider-aba932fa009af1f525bc3fed5c5d363806c6bcbdd3f03b7b80f8096b0a33e7e6.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: provider-candidate-archive
  from: operation:aba932fa009af1f525bc3fed5c5d363806c6bcbdd3f03b7b80f8096b0a33e7e6
  source_sha256: 865af0959799d244e683120c944f3282de598d7f36078bd8afeb1ff0344c80a0
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
- mipi
- document-described
- MBI_MIPI_RX_DisableMipiClock
validation_refs:
- projects/a123x/archive/provider-aba932fa009af1f525bc3fed5c5d363806c6bcbdd3f03b7b80f8096b0a33e7e6.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/a123x/archive/provider-aba932fa009af1f525bc3fed5c5d363806c6bcbdd3f03b7b80f8096b0a33e7e6.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-10-24'
updated_at: '2026-10-24'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-10-24'
manual_validation_pending: true
summary_zh: A123X RC1 MBI_MIPI_RX_DisableMipiClock；相机接收、禁用；当前声明：MBP_S32 MBI_MIPI_RX_DisableMipiClock(COMBO_DEV_T mipiDev);；文档用途：Provide
  interface of disable MIPI_RX clock.；来源：mbi_mipi_rx.h:49 头SHA256 2bd20074612f39586dca25f01ba424893db156ad5c37426714275bc1d9c5e36f；手册IPC
  SDK MIPI Rx MBI (0.6).pdf物理页19；reviewing；实际库/ABI/设备未验证。
primary_language: zh-CN
source_language: en
translation_status: partial
terminology_status: pending
subject_ref: &id001
  type: project
  id: a123x
created_subject_ref: *id001
principal_id: local-user
provider_operation_id: aba932fa009af1f525bc3fed5c5d363806c6bcbdd3f03b7b80f8096b0a33e7e6
provenance:
  source_kind: session-conclusion
  source_ref: sanitized-conclusion
  verification_state: declared
---

# A123X独立接口：MBI_MIPI_RX_DisableMipiClock

证据等级：文档说明级，未经实际库验证。
适用快照：IPC C5 RC1；2026-10-24来源核验。

## 当前接口声明

`MBP_S32 MBI_MIPI_RX_DisableMipiClock(COMBO_DEV_T mipiDev);`

来源：workspaces/ipc-c5-rc.1.0/linux/mbp/mbi/isp/include/mbi_mipi_rx.h:49；SHA256 2bd20074612f39586dca25f01ba424893db156ad5c37426714275bc1d9c5e36f。

## 文档明确内容

以下为该接口章节的字段摘录，保留英文以避免参数和单位被自动翻译改变。头文件声明与文档说明分别留证；未声称两者ABI一致。

用途：

Provide interface of disable MIPI_RX clock.

文档声明（与当前头文件分别留证）：

MBP_S32 MBI_MIPI_RX_DisableMipiClock(COMBO_DEV_T mipiDev);

参数说明：

Parameter name Description input/output
mipiDev Mipi device indexes. input

返回值：

Return value Description
0 success
non-zero failure

调用约束：

No

芯片差异：

No.

文档依赖：

Header file:mbi_mipi_rx.h,mipi_rx_module.h,mbp_comm_mipi_rx.h
Library file:libmbi_isp.so
Kernel object:mbd_mipi_rx.ko

来源：downloads/IPC SDK Documents/IPC SDK MIPI Rx MBI (0.6).pdf；物理页19起，章节2.13；SHA256 b7233da046dee03c2a7020fb743385e587a0d6da2575e163e75ff60c41b35005。

## 尚未闭环

- 实际库导出、ABI和运行行为尚未验证；源码/文档说明不代表板级、设备或量产结论。

证据更新条件：对应头、文档或实际库身份变化时重新核验；本条为reviewing候选。
