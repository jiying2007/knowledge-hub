---
id: provider-285230df3c2cc86dedccbd3c63d6caf09c4d9880c111351f4f9e6fb7ce0cd044
title: A123X：GE2D结构体有bCompress就能启用压缩吗
kind: runbook
domain: projects/a123x
path: projects/a123x/archive/provider-285230df3c2cc86dedccbd3c63d6caf09c4d9880c111351f4f9e6fb7ce0cd044.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: provider-candidate-archive
  from: operation:285230df3c2cc86dedccbd3c63d6caf09c4d9880c111351f4f9e6fb7ce0cd044
  source_sha256: 391c33dd9a59ae46a3f2d4c9fb2acfdeab533145099cf458145f4160d0ba6dde
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
- GE2D能力
- engineering-answer
validation_refs:
- projects/a123x/archive/provider-285230df3c2cc86dedccbd3c63d6caf09c4d9880c111351f4f9e6fb7ce0cd044.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/a123x/archive/provider-285230df3c2cc86dedccbd3c63d6caf09c4d9880c111351f4f9e6fb7ce0cd044.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-10-24'
updated_at: '2026-10-24'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-10-24'
manual_validation_pending: true
summary_zh: GE2D_OPT_T虽然保留bCompress和bDecompress字段，但该版本成员说明明确标注Not support。字段存在、头文件编译通过或概述提到相关能力，都不能证明当前接口可用压缩/解压。按实际SoC、库与操作支持表确认，再决定格式和内存路径；不能用未支持字段减少缓冲区分配或跳过解压。
  适用：本地对应版本资料的方法知识；实际A123X内核、库、DTS、节点和制品须绑定验证，手册示例不作为当前板配置或实测。 来源：downloads/IPC SDK Documents/IPC SDK GE2D MBI (0.6).pdf；PDF物理页
  30,31；SHA256 ea0ad85cf86c65bdc1c0823bad7d07071d4b35d006e4cc4b4a975bf2ed2dafc9
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
subject_ref: &id001
  type: project
  id: a123x
created_subject_ref: *id001
principal_id: local-user
provider_operation_id: 285230df3c2cc86dedccbd3c63d6caf09c4d9880c111351f4f9e6fb7ce0cd044
provenance:
  source_kind: session-conclusion
  source_ref: sanitized-conclusion
  verification_state: declared
---

# GE2D结构体有bCompress就能启用压缩吗

GE2D_OPT_T虽然保留bCompress和bDecompress字段，但该版本成员说明明确标注Not support。字段存在、头文件编译通过或概述提到相关能力，都不能证明当前接口可用压缩/解压。按实际SoC、库与操作支持表确认，再决定格式和内存路径；不能用未支持字段减少缓冲区分配或跳过解压。

适用边界：本地对应版本资料的方法知识；实际A123X内核、库、DTS、节点和制品须绑定验证，手册示例不作为当前板配置或实测。

来源：downloads/IPC SDK Documents/IPC SDK GE2D MBI (0.6).pdf；PDF物理页 30,31；SHA256 ea0ad85cf86c65bdc1c0823bad7d07071d4b35d006e4cc4b4a975bf2ed2dafc9

验证状态：2026-10-24原文及必要头文件核对；reviewing候选，未作设备操作或owner人工放行。工程建议不等于当前实现已满足，写操作须另有明确目标及可恢复方案。
