---
id: provider-xcrz-sigmastar-demo-465bd4ca70156a64a0b84fdc
title: v35：瞬时残差保护未通过
kind: debug-record
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/archive/provider-xcrz-sigmastar-demo-465bd4ca70156a64a0b84fdc.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: provider-candidate-archive
  from: provider-policy-sha256:a295759999c3c3c2594752350565bbde6af74808af32b9272604f53a36f82736;operation:465bd4ca70156a64a0b84fdc840430e2cac202646ae6d97d10fcd5933d6b7d0a
  source_sha256: 2ea3d765c046136663a0e316b4d2b5052631b026a58418b40c2b83b7134d9250
  temporary_source_retained: false
review_after: '2027-01-09'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- provider-archive
- debug-record
validation_refs:
- projects/xcrz-sigmastar-demo/archive/provider-xcrz-sigmastar-demo-465bd4ca70156a64a0b84fdc.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/archive/provider-xcrz-sigmastar-demo-465bd4ca70156a64a0b84fdc.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-10-11'
updated_at: '2026-10-11'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-10-11'
manual_validation_pending: true
summary_zh: 冻结 v31 系数，新 Host guard variant 在原上一帧 shadow guard 上增加：上一整 Feed AES 已处理、 echo magnitude>0、instant residual/echo<=3:2。缓存仅在
  Feed 完整返回后更新，NN callback 读取上一份。 模型 SHA dde69b765c0e053ab118fcb5733bd3bd1068264f064bb91afd5d94ef985d1c6b，旧拟合资格不继承。 ASAN/UBSAN
  合同通过，原生独立实例核验每次缓存；128位独立比较核验边界与最大U64。 旧 header 错配和同时启用
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
subject_ref: &id001
  id: xcrz-sigmastar-demo
  type: project
created_subject_ref: *id001
principal_id: null
provider_operation_id: 465bd4ca70156a64a0b84fdc840430e2cac202646ae6d97d10fcd5933d6b7d0a
---

# v35：瞬时残差保护未通过

冻结 v31 系数，新 Host guard variant 在原上一帧 shadow guard 上增加：上一整 Feed AES 已处理、
echo magnitude>0、instant residual/echo<=3:2。缓存仅在 Feed 完整返回后更新，NN callback 读取上一份。
模型 SHA dde69b765c0e053ab118fcb5733bd3bd1068264f064bb91afd5d94ef985d1c6b，旧拟合资格不继承。
ASAN/UBSAN 合同通过，原生独立实例核验每次缓存；128位独立比较核验边界与最大U64。
旧 header 错配和同时启用 smooth/instant guard 的编译均预期拒绝。
一次合同调用发生在编译进程尚未结束前，返回未找到 binary；等待编译完成后执行通过，非声学失败。

208 已暴露样本全部 actual C 配对，十组仅 development8/exposed-failed24 两组合格。
八组远端均值未达 .5dB；expanded24/exposed-independent24/exposed-v27-24 双讲另失败。
四组精确最终整数 PCM 复核，原始 metrics 与冻结 actual C 相同，窗口和非输出轨迹完全一致。
development24 far +.3277823602296947dB；expanded24 far +.4461067425819003、DT -.16524698671609084；
exposed-independent24 far +.39984650397458904、DT -.11955898188902303；
exposed-v27-24 far +.48077907830884453、DT -.34961279843876714、target -.2251776831961747。
550 的实际 DT -.34961279843876714、target -.2045696955786671；831 DT +.1723054960854471、target -.2251776831961747。
拒绝 v35，不能用两个局部合格组替代全体通过。整帧风险旁路仍难兼顾消回声收益与双讲保护。

candidate SHA2f20a41b7769652541f9e01fa974a096f9e7f0b67d2c39606081b6fffebe21cb；
control SHA4c61d9712f4cc7ed50bb5ba5a0e189b63e8cb17ce7b349df240dd09cbfdc2a42；
native observer SHA08404cb43bea37b603d3c2770efebdf3f56305f078d3e01aafcfce39d3fe94ab；
contract SHA33ce46629a70ac4a6e99d1539a575578b0ead4c211214bb05944a7fd44527230。
本轮只改 Host tools/tests，无生产默认/库/协议/reader/lease 修改，无commit/push/deploy/restart。
下一步先只观察频点信息：上一帧实际 raw microphone 与 AEC estimated echo 的归一化复相干性，
验证它是否有助于区分被校正的 far/double 频点，再决定是否增加连续置信度校正。
主声学目标未完成；累计预算200M/36h仍有效。
