---
id: provider-xcrz-sigmastar-demo-08b04efa5eb99b197ccce4e4
title: v31：开发完整通过，保留独立集双讲失败
kind: debug-record
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/archive/provider-xcrz-sigmastar-demo-08b04efa5eb99b197ccce4e4.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: provider-candidate-archive
  from: provider-policy-sha256:a295759999c3c3c2594752350565bbde6af74808af32b9272604f53a36f82736;operation:08b04efa5eb99b197ccce4e4e448ca64e2a6588e063a499786ce7d17ef8aea90
  source_sha256: f0d4529bb43033070f7c9cb7f7360cd9d9125672f3bea34af972ba257979ecf8
  temporary_source_retained: false
review_after: '2027-01-08'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- provider-archive
- debug-record
validation_refs:
- projects/xcrz-sigmastar-demo/archive/provider-xcrz-sigmastar-demo-08b04efa5eb99b197ccce4e4.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/archive/provider-xcrz-sigmastar-demo-08b04efa5eb99b197ccce4e4.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-10-10'
updated_at: '2026-10-10'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-10-10'
manual_validation_pending: true
summary_zh: 累计Token预算200M、时间36h。固定184开发九组log切线；统计/参考/模型/二进制及开发验收 详见DEVELOPMENT-PASS-v31.md，SHA613b53d6377a73c67b647698e4fc25b9efc16d5e26ae6669527dba3ca012446a。
  104 Python tests PASS；实际C ASAN/UBSAN合同PASS；184九组实际和精确整数PCM全部PASS。 模型SHAfdc9f79f1f2f80918a9d72d9e8187c8b68bf3aa2e84d0f69299b3d91bc2a48d3。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
subject_ref: &id001
  id: xcrz-sigmastar-demo
  type: project
created_subject_ref: *id001
principal_id: null
provider_operation_id: 08b04efa5eb99b197ccce4e4e448ca64e2a6588e063a499786ce7d17ef8aea90
---

# v31：开发完整通过，保留独立集双讲失败

累计Token预算200M、时间36h。固定184开发九组log切线；统计/参考/模型/二进制及开发验收
详见DEVELOPMENT-PASS-v31.md，SHA613b53d6377a73c67b647698e4fc25b9efc16d5e26ae6669527dba3ca012446a。
104 Python tests PASS；实际C ASAN/UBSAN合同PASS；184九组实际和精确整数PCM全部PASS。
模型SHAfdc9f79f1f2f80918a9d72d9e8187c8b68bf3aa2e84d0f69299b3d91bc2a48d3。

随后按计划首次评分1996独立24。实际及精确均失败：far平均+.7468382067643878dB，
far最差+.025779545104327894dB；double最差-.28703294049510575dB（550）；
target最差-.32696771150569814dB（831）。550 target也-.20107078619919871dB。
near_exact、削顶、AGC内部饱和通过，但不能抵消语音保护失败，v31拒绝采用，shipping=false。
1996从此已暴露，后续不得继续称新独立或反向调参后宣称独立通过；当前训练允许集仍排除它。

只读trace诊断：550双讲shadow candidate/active率.18033/.22131，831为.06803/.06122。
按前一/前两hop相同真值phase排除混合边界，在550双讲346帧仍223帧有允许校正频点；
831双讲291帧仍154帧。此为诊断真值标签，不参与推理。
原NN增益.8..1.01的频点占550双讲校正频谱能量约50.3%，831约63.2%；
但它们也占远端独讲校正能量91.9%/82.8%，所以简单屏蔽高NN增益可能损失消回声收益。
频谱校正能量不是目标损失因果分解，不能据此断言高增益是唯一根因。
该只读诊断首次将variant误写native导致StopIteration，按实际JSON schema baseline修正；
修正版固定hop标签与nearend_scale，没有改变音频或模型。

下一方向：以实际逐帧DTD量取证，核对残差/echo瞬时与平滑比、相似度条件、NN延迟对齐；
先诊断可分辨性，再冻结保护机制实验，不再仅扩大表训练覆盖。
无生产默认、库或上层生命周期改动；无commit/push/deploy/restart。严重CALL回声仍未解决。
