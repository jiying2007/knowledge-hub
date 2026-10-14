---
id: provider-xcrz-sigmastar-demo-64a79d0c39aa032433a4a086
title: v33：固定平滑 echo 占优保护未通过
kind: debug-record
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/archive/provider-xcrz-sigmastar-demo-64a79d0c39aa032433a4a086.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: provider-candidate-archive
  from: provider-policy-sha256:a295759999c3c3c2594752350565bbde6af74808af32b9272604f53a36f82736;operation:64a79d0c39aa032433a4a086857e7c7c5706be0ca3019393523a9f5f3c3c6429
  source_sha256: 970e4e6ee8d81e6a3be9d00d3ce4c4496cb3c70aaf2bc57cc36ef1fe04fff9d1
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
- projects/xcrz-sigmastar-demo/archive/provider-xcrz-sigmastar-demo-64a79d0c39aa032433a4a086.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/archive/provider-xcrz-sigmastar-demo-64a79d0c39aa032433a4a086.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-10-11'
updated_at: '2026-10-11'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-10-11'
manual_validation_pending: true
summary_zh: 固定 v31 系数，只增加上一帧 shadow echoSmooth>0 且 residualSmooth<echoSmooth 的 Host 校正保护。 没有重新训练，没有继承 v31 的拟合几何资格。模型 SHA 24d6d7594e2d0d026d734111fcc8fb0062687f2d51aae57f9cb0be4e9d518b6e。
  原 184 开发与后来暴露的 24 共 208 例、十组全部实际 C 配对评分；全部未通过原质量门槛。 十组平均远端抑制改善只有约 0.0815 至 0.2758 dB，均小于 0.5 dB。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
subject_ref: &id001
  id: xcrz-sigmastar-demo
  type: project
created_subject_ref: *id001
principal_id: null
provider_operation_id: 64a79d0c39aa032433a4a086857e7c7c5706be0ca3019393523a9f5f3c3c6429
---

# v33：固定平滑 echo 占优保护未通过

固定 v31 系数，只增加上一帧 shadow echoSmooth>0 且 residualSmooth<echoSmooth 的 Host 校正保护。
没有重新训练，没有继承 v31 的拟合几何资格。模型 SHA
24d6d7594e2d0d026d734111fcc8fb0062687f2d51aae57f9cb0be4e9d518b6e。
原 184 开发与后来暴露的 24 共 208 例、十组全部实际 C 配对评分；全部未通过原质量门槛。
十组平均远端抑制改善只有约 0.0815 至 0.2758 dB，均小于 0.5 dB。

三组进一步逐样点审计最终整数 PCM，observer 原始指标与冻结实际 C 完全一致，
native/candidate 的窗口、原生 AGC 和全部非 output 轨迹一致，512 样点对齐保持。
development24 最差双讲 -0.1962035720115054 dB（18），超过 -0.1 dB 门槛。
exposed24 最差 target -0.2055006689704042 dB（206），超过 -0.2 dB 门槛。
exposed-v27-24 平均 far +0.09538335085361342 dB；550 双讲 -0.02610553480845823、
target -0.06351461066703878；831 双讲 +0.03445903606254097、target -0.07626997429757498。
虽然旧失败 550/831 的双讲损失改善，不能用这些局部改善替代完整回归。

110 Python tests 全部通过；旧、新 C 合同均 ASAN/UBSAN 通过，错配旧 header 的新 guard 编译被静态断言拒绝。
初始新合同失败来自独立预期仍按旧 flags 判定，更新独立预期后重新编译并通过；未掩盖此测试修正。
这些验证证明实验实现和身份边界，不构成声学通过。生产默认、库、上层生命周期未在本轮修改。

candidate SHA481f344222a3b7d5c2ab0282f02de9354f0613050782dba7daf0c65993fd91d0；
control SHA7005490ae10c2ed69af28d893e4e3e756f7ed7e539da651264f0c2778deaf5de；
final contract SHA1b6fae370ed5bfa8def3b96b8eacf1f0778716ce4c59198ef57de92d2960b2b9。

结论：拒绝 v33，shipping_approved=false。更严格的时变旁路不能假定单调改善音质。
继续对真实整数 PCM 做保护切换邻域和稳定区域分解，先验证时变校正失真是否集中于切换，
再决定连续性或校正机制；不能扫描阈值后把已经暴露的 208 例称独立验证。
累计预算仍为 200M Token/36h，主声学目标尚未完成，无 commit/push/deploy/restart。
