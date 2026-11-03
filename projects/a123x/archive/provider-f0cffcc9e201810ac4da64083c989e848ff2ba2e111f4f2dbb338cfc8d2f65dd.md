---
id: provider-f0cffcc9e201810ac4da64083c989e848ff2ba2e111f4f2dbb338cfc8d2f65dd
title: A123X接口知识卡：MBI_VENC_CreateChn
kind: runbook
domain: projects/a123x
path: projects/a123x/archive/provider-f0cffcc9e201810ac4da64083c989e848ff2ba2e111f4f2dbb338cfc8d2f65dd.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: provider-candidate-archive
  from: operation:f0cffcc9e201810ac4da64083c989e848ff2ba2e111f4f2dbb338cfc8d2f65dd
  source_sha256: 68f8bc5fe61a67314dc115c95b6af0a8554901b29e80cf4d20bb1b7a066b8dc8
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
- a123x-answer-card-v2
- api
validation_refs:
- projects/a123x/archive/provider-f0cffcc9e201810ac4da64083c989e848ff2ba2e111f4f2dbb338cfc8d2f65dd.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/a123x/archive/provider-f0cffcc9e201810ac4da64083c989e848ff2ba2e111f4f2dbb338cfc8d2f65dd.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-10-24'
updated_at: '2026-10-24'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-10-24'
manual_validation_pending: true
summary_zh: A123X知识卡v2；2026-10-23 RC1候选；接口 MBI_VENC_CreateChn 的头文件声明：MBP_S32 MBI_VENC_CreateChn(VENC_CHN VencChn, const VENC_CHN_ATTR_T
  *pstAttr); 条件编译是否启用及实际运行库导出需分别核实。 来源：workspaces/ipc-c5-rc.1.0/linux/mbp/mbi/venc/include/mbi_venc.h:45，头hash 18f7711dd88dcbe744d869373cb10795bf4281940a075323f1d41d3f60a48fbb
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
subject_ref: &id001
  type: project
  id: a123x
created_subject_ref: *id001
principal_id: local-user
provider_operation_id: f0cffcc9e201810ac4da64083c989e848ff2ba2e111f4f2dbb338cfc8d2f65dd
provenance:
  source_kind: session-conclusion
  source_ref: sanitized-conclusion
  verification_state: declared
---

# A123X接口知识卡：MBI_VENC_CreateChn

接口 MBI_VENC_CreateChn 的头文件声明：MBP_S32 MBI_VENC_CreateChn(VENC_CHN VencChn, const VENC_CHN_ATTR_T *pstAttr); 条件编译是否启用及实际运行库导出需分别核实。

来源：workspaces/ipc-c5-rc.1.0/linux/mbp/mbi/venc/include/mbi_venc.h:45，头hash 18f7711dd88dcbe744d869373cb10795bf4281940a075323f1d41d3f60a48fbb

适用边界：本地RC1源码/文档快照；reviewing候选，未执行新的设备验证。来源变化须刷新本条，不以目录或其他知识卡替代其证据。
