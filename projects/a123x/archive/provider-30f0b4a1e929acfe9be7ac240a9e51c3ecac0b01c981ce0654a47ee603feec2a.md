---
id: provider-30f0b4a1e929acfe9be7ac240a9e51c3ecac0b01c981ce0654a47ee603feec2a
title: A123X独立接口：MBI_DEW_ConnectOnlineMode
kind: runbook
domain: projects/a123x
path: projects/a123x/archive/provider-30f0b4a1e929acfe9be7ac240a9e51c3ecac0b01c981ce0654a47ee603feec2a.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: provider-candidate-archive
  from: operation:30f0b4a1e929acfe9be7ac240a9e51c3ecac0b01c981ce0654a47ee603feec2a
  source_sha256: 1398b859d6b7712334789ff868b44b0a12753c529fc36e231acfaddd1182becb
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
- dew
- document-described
- MBI_DEW_ConnectOnlineMode
validation_refs:
- projects/a123x/archive/provider-30f0b4a1e929acfe9be7ac240a9e51c3ecac0b01c981ce0654a47ee603feec2a.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/a123x/archive/provider-30f0b4a1e929acfe9be7ac240a9e51c3ecac0b01c981ce0654a47ee603feec2a.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-10-24'
updated_at: '2026-10-24'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-10-24'
manual_validation_pending: true
summary_zh: A123X RC1 MBI_DEW_ConnectOnlineMode；去畸变；当前声明：MBP_S32 MBI_DEW_ConnectOnlineMode(MBP_VOID);；文档用途：Enable connect
  Online Mode；来源：mbi_dewarp.h:64 头SHA256 24543c1bc8e268d7f977261f34f58862af3e6c95b626c4df48b385a31dbcae39；手册IPC SDK DEWARP
  MBI (0.7).pdf物理页20；reviewing；实际库/ABI/设备未验证。
primary_language: zh-CN
source_language: en
translation_status: partial
terminology_status: pending
subject_ref: &id001
  type: project
  id: a123x
created_subject_ref: *id001
principal_id: local-user
provider_operation_id: 30f0b4a1e929acfe9be7ac240a9e51c3ecac0b01c981ce0654a47ee603feec2a
provenance:
  source_kind: session-conclusion
  source_ref: sanitized-conclusion
  verification_state: declared
---

# A123X独立接口：MBI_DEW_ConnectOnlineMode

证据等级：文档说明级，未经实际库验证。
适用快照：IPC C5 RC1；2026-10-24来源核验。

## 当前接口声明

`MBP_S32 MBI_DEW_ConnectOnlineMode(MBP_VOID);`

来源：workspaces/ipc-c5-rc.1.0/linux/mbp/mbi/dewarp/include/mbi_dewarp.h:64；SHA256 24543c1bc8e268d7f977261f34f58862af3e6c95b626c4df48b385a31dbcae39。

## 文档明确内容

以下为该接口章节的字段摘录，保留英文以避免参数和单位被自动翻译改变。头文件声明与文档说明分别留证；未声称两者ABI一致。

用途：

Enable connect Online Mode

文档声明（与当前头文件分别留证）：

MBP_S32 MBI_DEW_ConnectOnlineMode(MBP_VOID);
1. Overview
2. API reference
2. 1. MBI_DEW_Open
2. 2. MBI_DEW_Close
2. 3. MBI_DEW_BeginJob
2. 4. MBI_DEW_CancelJob
2. 5. MBI_DEW_EndJob
2. 6. MBP_S32 MBI_DEW_WaitDone
2. 7. MBI_DEW_AddCorrectionTask
2. 8. MBI_DEW_AddRectBoxTask
2. 9. MBI_DEW_LoadFirmware
2. 10. MBI_DEW_CalcAndLoadFirmware
2. 11. MBI_DEW_RectBox_CalcAndLoadFirmware
2. 12. MBI_DEW_Append_RectBox_CalcAndLoadFirmware
2. 13. MBI_DEW_StoreFirmwareIntoMbd
2. 14. MBI_DEW_DisconnectOnlineMode
2. 15. MBI_DEW_ConnectOnlineMode
3. Data Type
3. 1. DEW_INPUT_PARAM_T
3. 2. DEW_OUTPUT_PARAM_T
3. 3. DEW_BOX_PARAM_T
3. 4. DEW_FW_RECT_BOX_PARAM_T
3. 5. DEW_DAT_MODE_E
3. 6. DEWARP_FORMAT_E
3. 7. DEW_STORED_FW_T
3. 8. DEW_SURFACE_T
3. 9. DEW_TASK_T
3. 10. DEW_RECT_BOX_TASK_T
3. 11. DEW_END_JOB_T
3. 12. DEW_FW_PARAM_T
3. 13. DEW_PROJ_PARAM_T
3. 14. DEW_CLB_PARAM_T
3. 15. DEW_MESHIN_PARAM_T
3. 16. DEW_DPTZ_PARAM_T
3. 17. DEW_WIN_PARAM_T
3. 18. DEW_PROC_PARAM_T
3. 19. CAMERA_PARAM_T
3. 20. EIS2_PARAM_T
3. 21. DEW_PANO_PARAM_T
4. Error code
5. Proc Debug Information
5. 1. Overview
5. 2. Proc Information Description

参数说明：

Parameter name Description input/output

返回值：

Return value Description
0 Success
non-zero Failure

调用约束：

No.

芯片差异：

Chip Name Support
C302X N
C308L N
C302X2 Y
C305X2 Y
A123X Y

文档依赖：

Header file:mbp_comm_dewarp.h.
Library file:

来源：downloads/IPC SDK Documents/IPC SDK DEWARP MBI (0.7).pdf；物理页20起，章节2.15；SHA256 f2710955f07aad9cb8c75c7780f0334aff14f3a905d74dbf29012734dc8332be。

## 尚未闭环

- 实际库导出、ABI和运行行为尚未验证；源码/文档说明不代表板级、设备或量产结论。

证据更新条件：对应头、文档或实际库身份变化时重新核验；本条为reviewing候选。
