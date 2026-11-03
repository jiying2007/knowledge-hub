---
id: provider-2dcb906a5de51bf0d1c4eafb3b9ff542ae6dc33ea1e90c82bec60e5ed85180c2
title: A123X独立接口：MBI_AI_GetVolume
kind: runbook
domain: projects/a123x
path: projects/a123x/archive/provider-2dcb906a5de51bf0d1c4eafb3b9ff542ae6dc33ea1e90c82bec60e5ed85180c2.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: provider-candidate-archive
  from: operation:2dcb906a5de51bf0d1c4eafb3b9ff542ae6dc33ea1e90c82bec60e5ed85180c2
  source_sha256: 9a37a779e8e1d02b1528f28bf2a0122ffda5c06960247c27d624f4dad296fb16
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
- ai
- document-described
- MBI_AI_GetVolume
validation_refs:
- projects/a123x/archive/provider-2dcb906a5de51bf0d1c4eafb3b9ff542ae6dc33ea1e90c82bec60e5ed85180c2.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/a123x/archive/provider-2dcb906a5de51bf0d1c4eafb3b9ff542ae6dc33ea1e90c82bec60e5ed85180c2.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-10-24'
updated_at: '2026-10-24'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-10-24'
manual_validation_pending: true
summary_zh: A123X RC1 MBI_AI_GetVolume；检索词（符号释义）：音频输入、获取、音量；文档用途：Get audio ADC digital volume.；参数类型和来源见正文；实际库/板级/量产未验证。
primary_language: zh-CN
source_language: en
translation_status: partial
terminology_status: pending
subject_ref: &id001
  type: project
  id: a123x
created_subject_ref: *id001
principal_id: local-user
provider_operation_id: 2dcb906a5de51bf0d1c4eafb3b9ff542ae6dc33ea1e90c82bec60e5ed85180c2
provenance:
  source_kind: session-conclusion
  source_ref: sanitized-conclusion
  verification_state: declared
---

# A123X独立接口：MBI_AI_GetVolume

证据等级：文档说明级，未经实际库验证。
适用快照：IPC C5 RC1；2026-10-24来源核验。

## 当前接口声明

`MBP_S32 MBI_AI_GetVolume(MBP_S32 AiDevId, AI_AUDIO_DEV AiChn, MBP_S32 *s32VolLevel);`

来源：workspaces/ipc-c5-rc.1.0/linux/mbp/mbi/mbi_base/include/mbi_audio.h:111；SHA256 441a51ef16a15bcce5d0fc0b721c83d85b03439e28288ca191d5f44d7d52cf7b。

## 文档明确内容

以下为该接口章节的字段摘录，保留英文以避免参数和单位被自动翻译改变。头文件声明与文档说明分别留证；未声称两者ABI一致。

用途：

Get audio ADC digital volume.

文档声明（与当前头文件分别留证）：

MBP_S32 MBI_AI_GetVolume(MBP_S32 AiDevId,AI_AUDIO_DEV AiChn, MBP_S32 *s32VolLevel);

参数说明：

Parameter name Description input/output
AiDevId Ai device id input
AiChn Ai channel id input
s32VolLevel number of audio input volume level input/output

返回值：

Return value Description
0 success
non-zero failure

调用约束：

No.

芯片差异：

No.

文档依赖：

Header file: mbi_audio.h, mbp_comm_audio.h.
Library file: libmbi.so, libmbi.a.

来源：downloads/IPC SDK Documents/IPC SDK AUDIO MBI (0.9).pdf；物理页30起，章节2.14；SHA256 63769300b0abf74b6ebd6267df1c6a62650995c1a2fab2a722c843dc1d7f9b67。

## 尚未闭环

- 实际库导出、ABI和运行行为尚未验证；源码/文档说明不代表板级、设备或量产结论。

证据更新条件：对应头、文档或实际库身份变化时重新核验；本条为reviewing候选。
