---
id: provider-38a1465db5827fbfb2df0e7abb41bb2dfa42fc79baaa87145d6d0451ce867a94
title: A123X：CCM系数能否只分配普通3乘3的9个元素
kind: runbook
domain: projects/a123x
path: projects/a123x/archive/provider-38a1465db5827fbfb2df0e7abb41bb2dfa42fc79baaa87145d6d0451ce867a94.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: provider-candidate-archive
  from: operation:38a1465db5827fbfb2df0e7abb41bb2dfa42fc79baaa87145d6d0451ce867a94
  source_sha256: e4dd713324a441d476e595df56551b9889bb3f008a2739c46c5fd9d5f0b26934
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
- ISP色彩
- engineering-answer
validation_refs:
- projects/a123x/archive/provider-38a1465db5827fbfb2df0e7abb41bb2dfa42fc79baaa87145d6d0451ce867a94.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/a123x/archive/provider-38a1465db5827fbfb2df0e7abb41bb2dfa42fc79baaa87145d6d0451ce867a94.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-10-24'
updated_at: '2026-10-24'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-10-24'
manual_validation_pending: true
summary_zh: 该接口的CCM_MATRIX_SIZE为12，手动色彩矩阵s32Coef按该常量分配，ISP_COLORMATRIX_ATTR_T还以enOpType区分手动与自动数据。不能按普通3×3矩阵直觉只传9个系数；具体系数排列、定点格式和标定数据须遵守匹配版本契约，不能从数组长度自行推导。设置后结合读回和色卡验证，不把返回成功当色彩合格。
  适用：本地对应版本资料的方法知识；实际A123X内核、库、DTS、节点和制品须绑定验证，手册示例不作为当前板配置或实测。 来源：downloads/IPC SDK Documents/IPC SDK ISP MBI (02).pdf；PDF物理页
  304,307；SHA256 5c9c6f0a03e0529f82e5d4062f3c5b2b273fd69401a7151e2c6a6b8d229ca213；workspaces/ipc-c5-rc.1.0/linux/mbp/mbi/isp/include/aml_comm_isp.h:132；SHA256
  c7d4aed4e968ac31433f76b5f49794701b979090e6f1bcc265040031491dd3fa
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
subject_ref: &id001
  type: project
  id: a123x
created_subject_ref: *id001
principal_id: local-user
provider_operation_id: 38a1465db5827fbfb2df0e7abb41bb2dfa42fc79baaa87145d6d0451ce867a94
provenance:
  source_kind: session-conclusion
  source_ref: sanitized-conclusion
  verification_state: declared
---

# CCM系数能否只分配普通3乘3的9个元素

该接口的CCM_MATRIX_SIZE为12，手动色彩矩阵s32Coef按该常量分配，ISP_COLORMATRIX_ATTR_T还以enOpType区分手动与自动数据。不能按普通3×3矩阵直觉只传9个系数；具体系数排列、定点格式和标定数据须遵守匹配版本契约，不能从数组长度自行推导。设置后结合读回和色卡验证，不把返回成功当色彩合格。

适用边界：本地对应版本资料的方法知识；实际A123X内核、库、DTS、节点和制品须绑定验证，手册示例不作为当前板配置或实测。

来源：downloads/IPC SDK Documents/IPC SDK ISP MBI (02).pdf；PDF物理页 304,307；SHA256 5c9c6f0a03e0529f82e5d4062f3c5b2b273fd69401a7151e2c6a6b8d229ca213；workspaces/ipc-c5-rc.1.0/linux/mbp/mbi/isp/include/aml_comm_isp.h:132；SHA256 c7d4aed4e968ac31433f76b5f49794701b979090e6f1bcc265040031491dd3fa

验证状态：2026-10-24原文及必要头文件核对；reviewing候选，未作设备操作或owner人工放行。工程建议不等于当前实现已满足，写操作须另有明确目标及可恢复方案。
