---
id: provider-d6ea87ebb9dab68a2dfbfe29f07e8f1a6212cff67474332dad9c5d5bf794a45b
title: A123X独立接口：MBI_AP_DisableChn
kind: runbook
domain: projects/a123x
path: projects/a123x/archive/provider-d6ea87ebb9dab68a2dfbfe29f07e8f1a6212cff67474332dad9c5d5bf794a45b.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: provider-candidate-archive
  from: operation:d6ea87ebb9dab68a2dfbfe29f07e8f1a6212cff67474332dad9c5d5bf794a45b
  source_sha256: d7c627a245a963e46c1898e8f98e1d82fcdf5700670f7a7f4bba21da0fd2aca8
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
- ap
- document-described
- MBI_AP_DisableChn
validation_refs:
- projects/a123x/archive/provider-d6ea87ebb9dab68a2dfbfe29f07e8f1a6212cff67474332dad9c5d5bf794a45b.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/a123x/archive/provider-d6ea87ebb9dab68a2dfbfe29f07e8f1a6212cff67474332dad9c5d5bf794a45b.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-10-24'
updated_at: '2026-10-24'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-10-24'
manual_validation_pending: true
summary_zh: A123X RC1 MBI_AP_DisableChn；音频处理、禁用、通道；当前声明：MBP_S32 MBI_AP_DisableChn(AP_CHN ApChn);；文档用途：Disable audio process
  channel.；来源：mbi_audio.h:149 头SHA256 441a51ef16a15bcce5d0fc0b721c83d85b03439e28288ca191d5f44d7d52cf7b；手册IPC SDK AUDIO MBI
  (0.9).pdf物理页92；reviewing；实际库/ABI/设备未验证。
primary_language: zh-CN
source_language: en
translation_status: partial
terminology_status: pending
subject_ref: &id001
  type: project
  id: a123x
created_subject_ref: *id001
principal_id: local-user
provider_operation_id: d6ea87ebb9dab68a2dfbfe29f07e8f1a6212cff67474332dad9c5d5bf794a45b
provenance:
  source_kind: session-conclusion
  source_ref: sanitized-conclusion
  verification_state: declared
---

# A123X独立接口：MBI_AP_DisableChn

证据等级：文档说明级，未经实际库验证。
适用快照：IPC C5 RC1；2026-10-24来源核验。

## 当前接口声明

`MBP_S32 MBI_AP_DisableChn(AP_CHN ApChn);`

来源：workspaces/ipc-c5-rc.1.0/linux/mbp/mbi/mbi_base/include/mbi_audio.h:149；SHA256 441a51ef16a15bcce5d0fc0b721c83d85b03439e28288ca191d5f44d7d52cf7b。

## 文档明确内容

以下为该接口章节的字段摘录，保留英文以避免参数和单位被自动翻译改变。头文件声明与文档说明分别留证；未声称两者ABI一致。

用途：

Disable audio process channel.

文档声明（与当前头文件分别留证）：

MBP_S32 MBI_AP_DisableChn(AP_CHN ApChn)

参数说明：

Parameter name Description input/output
ApChn AP channel index input

返回值：

Return value Description
0 success
non-zero
20 st ia failure

调用约束：

Functions such as resample, speed up, and vqe, should stop before AP channel disable.
When canceling bind relation, passing AP channel information queried from MBI_AP_QueryChn.

芯片差异：

No.

文档依赖：

Header file: mbi_audio.h, mbp_comm_audio.h.
Library file:

来源：downloads/IPC SDK Documents/IPC SDK AUDIO MBI (0.9).pdf；物理页92起，章节2.76；SHA256 63769300b0abf74b6ebd6267df1c6a62650995c1a2fab2a722c843dc1d7f9b67。

## 尚未闭环

- 实际库导出、ABI和运行行为尚未验证；源码/文档说明不代表板级、设备或量产结论。

证据更新条件：对应头、文档或实际库身份变化时重新核验；本条为reviewing候选。
