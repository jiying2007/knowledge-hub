---
id: provider-edbb1b96f37dae74d77b59eef5fdedd67a890f99dec2309ac06718acf13917eb
title: A123X独立接口：MBI_AO_SetVolume
kind: runbook
domain: projects/a123x
path: projects/a123x/archive/provider-edbb1b96f37dae74d77b59eef5fdedd67a890f99dec2309ac06718acf13917eb.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: provider-candidate-archive
  from: operation:edbb1b96f37dae74d77b59eef5fdedd67a890f99dec2309ac06718acf13917eb
  source_sha256: a9b3fcef4df576d13f4f5d7a2d8040635061841b3b9a94e9ed950a2310cb179c
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
- ao
- document-described
- MBI_AO_SetVolume
validation_refs:
- projects/a123x/archive/provider-edbb1b96f37dae74d77b59eef5fdedd67a890f99dec2309ac06718acf13917eb.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/a123x/archive/provider-edbb1b96f37dae74d77b59eef5fdedd67a890f99dec2309ac06718acf13917eb.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-10-24'
updated_at: '2026-10-24'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-10-24'
manual_validation_pending: true
summary_zh: A123X RC1 MBI_AO_SetVolume；音频输出、设置、音量；当前声明：MBP_S32 MBI_AO_SetVolume(MBP_S32 AiDevId, AI_AUDIO_DEV AiChn, MBP_S32
  s32VolLevel);；文档用途：Set audio DAC volume.；来源：mbi_audio.h:128 头SHA256 441a51ef16a15bcce5d0fc0b721c83d85b03439e28288ca191d5f44d7d52cf7b；手册IPC
  SDK AUDIO MBI (0.9).pdf物理页45；reviewing；实际库/ABI/设备未验证。
primary_language: zh-CN
source_language: en
translation_status: partial
terminology_status: pending
subject_ref: &id001
  type: project
  id: a123x
created_subject_ref: *id001
principal_id: local-user
provider_operation_id: edbb1b96f37dae74d77b59eef5fdedd67a890f99dec2309ac06718acf13917eb
provenance:
  source_kind: session-conclusion
  source_ref: sanitized-conclusion
  verification_state: declared
---

# A123X独立接口：MBI_AO_SetVolume

证据等级：文档说明级，未经实际库验证。
适用快照：IPC C5 RC1；2026-10-24来源核验。

## 当前接口声明

`MBP_S32 MBI_AO_SetVolume(MBP_S32 AiDevId, AI_AUDIO_DEV AiChn, MBP_S32 s32VolLevel);`

来源：workspaces/ipc-c5-rc.1.0/linux/mbp/mbi/mbi_base/include/mbi_audio.h:128；SHA256 441a51ef16a15bcce5d0fc0b721c83d85b03439e28288ca191d5f44d7d52cf7b。

## 文档明确内容

以下为该接口章节的字段摘录，保留英文以避免参数和单位被自动翻译改变。头文件声明与文档说明分别留证；未声称两者ABI一致。

用途：

Set audio DAC volume.

文档声明（与当前头文件分别留证）：

MBP_S32 MBI_AO_SetVolume(MBP_S32 AoDevId,AI_AUDIO_DEV AoChn, MBP_S32 s32VolLevel);

参数说明：

Parameter
Description input/output
name
AoDevId Ao device id input
AoChn Ao channel id input
number of audio output volume level. Range [0, 255];$Gain
s32VolLevel input/output
=-95.625db + 0.375db \times level$ ; 0: Mute; 0.375db / each step

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

来源：downloads/IPC SDK Documents/IPC SDK AUDIO MBI (0.9).pdf；物理页45起，章节2.32；SHA256 63769300b0abf74b6ebd6267df1c6a62650995c1a2fab2a722c843dc1d7f9b67。

## 尚未闭环

- 实际库导出、ABI和运行行为尚未验证；源码/文档说明不代表板级、设备或量产结论。

证据更新条件：对应头、文档或实际库身份变化时重新核验；本条为reviewing候选。
