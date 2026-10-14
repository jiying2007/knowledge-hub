---
id: provider-xcrz-sigmastar-demo-065e64ca16e5bc74491b24dd
title: v37：复相干性连续混合仍未通过
kind: debug-record
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/archive/provider-xcrz-sigmastar-demo-065e64ca16e5bc74491b24dd.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: provider-candidate-archive
  from: provider-policy-sha256:a295759999c3c3c2594752350565bbde6af74808af32b9272604f53a36f82736;operation:065e64ca16e5bc74491b24ddc353e4b4bda4ce42fe3365c06cebccec616a4a31
  source_sha256: c727c30ee3a14d7e14a1d8e823659071e7790d421d3a23d4768c96e073eaf32b
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
- projects/xcrz-sigmastar-demo/archive/provider-xcrz-sigmastar-demo-065e64ca16e5bc74491b24dd.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/archive/provider-xcrz-sigmastar-demo-065e64ca16e5bc74491b24dd.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-10-11'
updated_at: '2026-10-11'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-10-11'
manual_validation_pending: true
summary_zh: 固定 v31 表，保持原上一帧 shadow valid/far/no candidate/no active；按上一帧实际 raw mic1 FFT 和 AEC estimated echo 的归一化复MSC连续混合native/table
  gain。EMA1/8，不足8有效帧beta0； 无参考/非CALL/Reset清状态，DTD旁路保留历史。无真值推理，无阈值扫描或新拟合。 新模型 SHA c91c6d498edcc0766a27076ee313497cdcfa140ccf06100289c7b55e246d1bb2，
  显式声明旧拟合几何不继承，raw design权重只能用于prec
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
subject_ref: &id001
  id: xcrz-sigmastar-demo
  type: project
created_subject_ref: *id001
principal_id: null
provider_operation_id: 065e64ca16e5bc74491b24ddc353e4b4bda4ce42fe3365c06cebccec616a4a31
---

# v37：复相干性连续混合仍未通过

固定 v31 表，保持原上一帧 shadow valid/far/no candidate/no active；按上一帧实际 raw mic1 FFT 和
AEC estimated echo 的归一化复MSC连续混合native/table gain。EMA1/8，不足8有效帧beta0；
无参考/非CALL/Reset清状态，DTD旁路保留历史。无真值推理，无阈值扫描或新拟合。
新模型 SHA c91c6d498edcc0766a27076ee313497cdcfa140ccf06100289c7b55e246d1bb2，
显式声明旧拟合几何不继承，raw design权重只能用于precision轨迹身份，不支持新混合的affine-fit。

208 已暴露样本、十组实际 C 均未通过，far平均约 .2440至.3944dB，全部小于 .5dB。
development8及旧v27暴露24另有双讲损失；三组最终整数PCM精确复核维持相同结论。
development24 far +.30031814873898455、DT -.04000925317655124、target -.052132003853580855；
development8 far +.3942117900030784、DT -.1097390420545592、target -.12061589746352475；
旧v27暴露24 far +.3350963715138313、DT -.22391108824949413、target -.14250500647779574。
550实际DT -.22391108824949413、target -.14250500647779574；831 DT +.2750550677040211、target -.09061309105769455。
相对v31，550损失减轻，831目标损失减轻，但完整收益/语音保护仍不合格，拒绝v37。

三组precision全部校验original metrics与冻结actual C相同，native/candidate窗口和非输出轨迹相同，512样点对齐。
C合同ASAN/UBSAN通过，独立mic/echo FIFO与Q20混合预期、no-ref/Reset/VOICE/AGC状态检查通过；
旧header错误编译被静态断言拒绝。120 Python tests全部通过，无skip，6.637s，diff check通过。
首次把metadata打印块插入struct后，在编译前检查发现并迁到Dump；之后实际编译、合同及全部评分通过。
独立复核修复JSON bool/int在Python相等比较下可能混淆的合同身份：改为canonical编码比较，
并增加False与0、True与1的拒绝控制，重跑120项通过。此修复不改变模型系数、声学二进制或评分。

candidate SHA7f59453501857ae48458b5da499274148f1d9b50ecf24134a3e8f2ac7556982a；
control SHAbadd2299b4f54756b0125ef99b444df409f5313c0930b14c6dcedced2d4ca975；
native observer SHAfee48f15b764f9ef6d4b86e7a0efa1ec33482cf0d2de3bdc0a123642e7043120；
contract SHA10e1f5d7598e217cedf208b5ad87eea0de6a611a4fde17d9ad3654810a94649e。
原生库SHA仍cc9561d29c93d00948eb90c1a59b0a0f28f8d59a01ca3895107c798a9a807532，baseline仍2ac9086d...。
原生build快照总182文件中，两个Host实验头已改变，完整快照不能称一致；
164个非tests身份均核验相同，库SHA相同。实验binary按本轮Host头重新构建，不覆盖原生库。

本轮v33/v35/v37均拒绝，没有可晋升的新候选；仅Host tools/tests/README变更，
生产默认、库、业务协议与reader/lease未在本轮修改，无commit/push/deploy/restart。
下一轮须重建带beta的实际最终PCM映射，再联合优化消回声与双讲约束，不复用旧geometry资格。
2026-10-11T00:35:06Z Execution Policy推荐compact：context .8268，goal仍active，
171594438/200000000 Token，已用121088.545/129600秒；预算尚余约2841万Token和2h21min。
按项目规则保存接力；不能标记主声学目标完成或最佳方案已找到。
