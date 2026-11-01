---
id: provider-d1c9abf3958f9b8dabe81cc5905cfe96ba8f9db978adb0db49ef2a5c282ca6cc
title: A123X：GE2D WaitAllDone是等待一个job还是全部任务
kind: runbook
domain: projects/a123x
path: projects/a123x/archive/provider-d1c9abf3958f9b8dabe81cc5905cfe96ba8f9db978adb0db49ef2a5c282ca6cc.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: provider-candidate-archive
  from: operation:d1c9abf3958f9b8dabe81cc5905cfe96ba8f9db978adb0db49ef2a5c282ca6cc
  source_sha256: 304d13781ce35421b4b87ea8fef13645012dd10d49f60830004ff2f7fb3f387d
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
- GE2D任务
- engineering-answer
validation_refs:
- projects/a123x/archive/provider-d1c9abf3958f9b8dabe81cc5905cfe96ba8f9db978adb0db49ef2a5c282ca6cc.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/a123x/archive/provider-d1c9abf3958f9b8dabe81cc5905cfe96ba8f9db978adb0db49ef2a5c282ca6cc.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-10-24'
updated_at: '2026-10-24'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-10-24'
manual_validation_pending: true
summary_zh: MBI_GE2D_WaitAllDone没有job handle参数，文档描述为等待GE2D所有任务完成；MBI_GE2D_EndJob的职责是提交任务。需要输出数据可用时不能仅根据EndJob名称推断同步完成；应按当前实现确认提交/等待语义和缓冲生命周期。多消费者环境下等待全部任务可能带来额外阻塞，不把它当单job精确完成通知。
  适用：本地对应版本资料的方法知识；实际A123X内核、库、DTS、节点和制品须绑定验证，手册示例不作为当前板配置或实测。 来源：downloads/IPC SDK Documents/IPC SDK GE2D MBI (0.6).pdf；PDF物理页
  9,10；SHA256 ea0ad85cf86c65bdc1c0823bad7d07071d4b35d006e4cc4b4a975bf2ed2dafc9
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
subject_ref: &id001
  type: project
  id: a123x
created_subject_ref: *id001
principal_id: local-user
provider_operation_id: d1c9abf3958f9b8dabe81cc5905cfe96ba8f9db978adb0db49ef2a5c282ca6cc
provenance:
  source_kind: session-conclusion
  source_ref: sanitized-conclusion
  verification_state: declared
---

# GE2D WaitAllDone是等待一个job还是全部任务

MBI_GE2D_WaitAllDone没有job handle参数，文档描述为等待GE2D所有任务完成；MBI_GE2D_EndJob的职责是提交任务。需要输出数据可用时不能仅根据EndJob名称推断同步完成；应按当前实现确认提交/等待语义和缓冲生命周期。多消费者环境下等待全部任务可能带来额外阻塞，不把它当单job精确完成通知。

适用边界：本地对应版本资料的方法知识；实际A123X内核、库、DTS、节点和制品须绑定验证，手册示例不作为当前板配置或实测。

来源：downloads/IPC SDK Documents/IPC SDK GE2D MBI (0.6).pdf；PDF物理页 9,10；SHA256 ea0ad85cf86c65bdc1c0823bad7d07071d4b35d006e4cc4b4a975bf2ed2dafc9

验证状态：2026-10-24原文及必要头文件核对；reviewing候选，未作设备操作或owner人工放行。工程建议不等于当前实现已满足，写操作须另有明确目标及可恢复方案。
