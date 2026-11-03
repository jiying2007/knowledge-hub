---
id: provider-fa209ce1b9cd345198e64eb02f20c75c37456cdc81f768ae6cd27ebbf80edff3
title: A123X：lsusb能看到U盘为什么还没有可挂载分区
kind: runbook
domain: projects/a123x
path: projects/a123x/archive/provider-fa209ce1b9cd345198e64eb02f20c75c37456cdc81f768ae6cd27ebbf80edff3.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: provider-candidate-archive
  from: operation:fa209ce1b9cd345198e64eb02f20c75c37456cdc81f768ae6cd27ebbf80edff3
  source_sha256: a60f54f6144faa83bae49d36c8b6ed89c81a98b5baf5d6846252f2f2485957bf
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
- a123x
- USB存储
- engineering-answer
validation_refs:
- projects/a123x/archive/provider-fa209ce1b9cd345198e64eb02f20c75c37456cdc81f768ae6cd27ebbf80edff3.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/a123x/archive/provider-fa209ce1b9cd345198e64eb02f20c75c37456cdc81f768ae6cd27ebbf80edff3.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-10-24'
updated_at: '2026-10-24'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-10-24'
manual_validation_pending: true
summary_zh: lsusb显示VID/PID只证明设备枚举信息；USB接口还需匹配usb-storage等类驱动，后续依赖SCSI、BLOCK生成块设备并识别分区/文件系统。依次核接口Driver、内核错误、块设备和分区，再处理挂载；不能跳过中间层直接格式化。手册设备序列号和设备号仅为样例，不记录为当前现场身份。
  适用：本地对应版本资料的方法知识；实际A123X内核、库、DTS、节点和制品须绑定验证，手册示例不作为当前板配置或实测。 来源：downloads/Kernel/USB User Guide (0.1).pdf；PDF物理页 23,28,30；SHA256
  198afa8ee3a0d9e6d8b0bbfad8447f5ed533e2343b168d261d7919965b8d2387
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
subject_ref: &id001
  type: project
  id: a123x
created_subject_ref: *id001
principal_id: local-user
provider_operation_id: fa209ce1b9cd345198e64eb02f20c75c37456cdc81f768ae6cd27ebbf80edff3
provenance:
  source_kind: session-conclusion
  source_ref: sanitized-conclusion
  verification_state: declared
---

# lsusb能看到U盘为什么还没有可挂载分区

lsusb显示VID/PID只证明设备枚举信息；USB接口还需匹配usb-storage等类驱动，后续依赖SCSI、BLOCK生成块设备并识别分区/文件系统。依次核接口Driver、内核错误、块设备和分区，再处理挂载；不能跳过中间层直接格式化。手册设备序列号和设备号仅为样例，不记录为当前现场身份。

适用边界：本地对应版本资料的方法知识；实际A123X内核、库、DTS、节点和制品须绑定验证，手册示例不作为当前板配置或实测。

来源：downloads/Kernel/USB User Guide (0.1).pdf；PDF物理页 23,28,30；SHA256 198afa8ee3a0d9e6d8b0bbfad8447f5ed533e2343b168d261d7919965b8d2387

验证状态：2026-10-24原文及必要头文件核对；reviewing候选，未作设备操作或owner人工放行。工程建议不等于当前实现已满足，写操作须另有明确目标及可恢复方案。
