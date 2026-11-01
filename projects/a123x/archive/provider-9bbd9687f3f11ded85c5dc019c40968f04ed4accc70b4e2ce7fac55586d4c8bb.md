---
id: provider-9bbd9687f3f11ded85c5dc019c40968f04ed4accc70b4e2ce7fac55586d4c8bb
title: A123X接口知识卡：MBI_DEW_EndJob
kind: runbook
domain: projects/a123x
path: projects/a123x/archive/provider-9bbd9687f3f11ded85c5dc019c40968f04ed4accc70b4e2ce7fac55586d4c8bb.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: provider-candidate-archive
  from: operation:9bbd9687f3f11ded85c5dc019c40968f04ed4accc70b4e2ce7fac55586d4c8bb
  source_sha256: 0a7586d3955920103e534830a4d36181572c4d85e48e6a0eb0ce40e0f5a8aeeb
  temporary_source_retained: false
review_after: '2027-01-21'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- provider-archive
- runbook
- a123x-answer-card-v2
- api
validation_refs:
- projects/a123x/archive/provider-9bbd9687f3f11ded85c5dc019c40968f04ed4accc70b4e2ce7fac55586d4c8bb.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/a123x/archive/provider-9bbd9687f3f11ded85c5dc019c40968f04ed4accc70b4e2ce7fac55586d4c8bb.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-10-23'
updated_at: '2026-10-23'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-10-23'
manual_validation_pending: true
summary_zh: A123X知识卡v2；2026-10-23 RC1候选；接口 MBI_DEW_EndJob 的头文件声明：MBP_S32 MBI_DEW_EndJob(DEW_HANDLE handle, MBP_BOOL_E bBlock,
  MBP_U32 u32TimeOut); 条件编译是否启用及实际运行库导出需分别核实。 来源：workspaces/ipc-c5-rc.1.0/linux/mbp/mbi/dewarp/include/mbi_dewarp.h:46，头hash
  24543c1bc8e268d7f977261f34f58862af3e6c95b626c4df48b385a31dbcae39
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
subject_ref: &id001
  type: project
  id: a123x
created_subject_ref: *id001
principal_id: local-user
provider_operation_id: 9bbd9687f3f11ded85c5dc019c40968f04ed4accc70b4e2ce7fac55586d4c8bb
provenance:
  source_kind: session-conclusion
  source_ref: sanitized-conclusion
  verification_state: declared
---

# A123X接口知识卡：MBI_DEW_EndJob

接口 MBI_DEW_EndJob 的头文件声明：MBP_S32 MBI_DEW_EndJob(DEW_HANDLE handle, MBP_BOOL_E bBlock, MBP_U32 u32TimeOut); 条件编译是否启用及实际运行库导出需分别核实。

来源：workspaces/ipc-c5-rc.1.0/linux/mbp/mbi/dewarp/include/mbi_dewarp.h:46，头hash 24543c1bc8e268d7f977261f34f58862af3e6c95b626c4df48b385a31dbcae39

适用边界：本地RC1源码/文档快照；reviewing候选，未执行新的设备验证。来源变化须刷新本条，不以目录或其他知识卡替代其证据。
