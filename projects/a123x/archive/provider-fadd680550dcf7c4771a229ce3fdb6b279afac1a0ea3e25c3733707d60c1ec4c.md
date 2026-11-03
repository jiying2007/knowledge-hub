---
id: provider-fadd680550dcf7c4771a229ce3fdb6b279afac1a0ea3e25c3733707d60c1ec4c
title: A123X接口知识卡：MBI_RGN_Create
kind: runbook
domain: projects/a123x
path: projects/a123x/archive/provider-fadd680550dcf7c4771a229ce3fdb6b279afac1a0ea3e25c3733707d60c1ec4c.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: provider-candidate-archive
  from: operation:fadd680550dcf7c4771a229ce3fdb6b279afac1a0ea3e25c3733707d60c1ec4c
  source_sha256: 8025386d7f3934aac0fd068df7d09bac9876f4be551587ff6f4788864479c42f
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
- projects/a123x/archive/provider-fadd680550dcf7c4771a229ce3fdb6b279afac1a0ea3e25c3733707d60c1ec4c.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/a123x/archive/provider-fadd680550dcf7c4771a229ce3fdb6b279afac1a0ea3e25c3733707d60c1ec4c.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-10-23'
updated_at: '2026-10-23'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-10-23'
manual_validation_pending: true
summary_zh: A123X知识卡v2；2026-10-23 RC1候选；接口 MBI_RGN_Create 的头文件声明：MBP_S32 MBI_RGN_Create(RGN_HANDLE Handle, const RGN_ATTR_T
  *pstRegion); 条件编译是否启用及实际运行库导出需分别核实。 来源：workspaces/ipc-c5-rc.1.0/linux/mbp/mbi/mbi_base/include/mbi_region.h:38，头hash 4215d2eadce6a9532734caa59393f3e8f14509ed087a01563c8c625f53742dcb
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
subject_ref: &id001
  type: project
  id: a123x
created_subject_ref: *id001
principal_id: local-user
provider_operation_id: fadd680550dcf7c4771a229ce3fdb6b279afac1a0ea3e25c3733707d60c1ec4c
provenance:
  source_kind: session-conclusion
  source_ref: sanitized-conclusion
  verification_state: declared
---

# A123X接口知识卡：MBI_RGN_Create

接口 MBI_RGN_Create 的头文件声明：MBP_S32 MBI_RGN_Create(RGN_HANDLE Handle, const RGN_ATTR_T *pstRegion); 条件编译是否启用及实际运行库导出需分别核实。

来源：workspaces/ipc-c5-rc.1.0/linux/mbp/mbi/mbi_base/include/mbi_region.h:38，头hash 4215d2eadce6a9532734caa59393f3e8f14509ed087a01563c8c625f53742dcb

适用边界：本地RC1源码/文档快照；reviewing候选，未执行新的设备验证。来源变化须刷新本条，不以目录或其他知识卡替代其证据。
