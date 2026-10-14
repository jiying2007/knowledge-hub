---
id: provider-xcrz-sigmastar-demo-95a5c0ea0390142335570b21
title: v39：已保留小幅消回声优化候选
kind: debug-record
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/archive/provider-xcrz-sigmastar-demo-95a5c0ea0390142335570b21.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: provider-candidate-archive
  from: provider-policy-sha256:a295759999c3c3c2594752350565bbde6af74808af32b9272604f53a36f82736;operation:95a5c0ea0390142335570b2108fff83c165b63a1437206d8ec1affda635c3fce
  source_sha256: 885999cde4c448675421989cb90fcc691e688d1b13b956024d1aecb95fe4e50b
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
- projects/xcrz-sigmastar-demo/archive/provider-xcrz-sigmastar-demo-95a5c0ea0390142335570b21.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/archive/provider-xcrz-sigmastar-demo-95a5c0ea0390142335570b21.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-10-11'
updated_at: '2026-10-11'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-10-11'
manual_validation_pending: true
summary_zh: 本轮按用户要求，将完全解决持续回声与保留可量化优化候选分开。 最终目标仍未完成。v39只取得小幅离线改善，未采用为产品默认。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
subject_ref: &id001
  id: xcrz-sigmastar-demo
  type: project
created_subject_ref: *id001
principal_id: null
provider_operation_id: 95a5c0ea0390142335570b2108fff83c165b63a1437206d8ec1affda635c3fce
---

# v39：已保留小幅消回声优化候选

本轮按用户要求，将完全解决持续回声与保留可量化优化候选分开。
最终目标仍未完成。v39只取得小幅离线改善，未采用为产品默认。

冻结方案为v31模型、原v26上一帧shadow DTD判据，实际native NN gain与table gain按3:1混合；
不拟合新表、不扫描强度、不使用推理真值。divisor4独立申报，不继承原表拟合资格。
模型SHA fdc9f79f1f2f80918a9d72d9e8187c8b68bf3aa2e84d0f69299b3d91bc2a48d3。

全部208例、10组实际C输出和精确整数PCM完成。分级文件candidate-registry-v39.json SHA 586a653f37d4b6eca8911b3d8a3cc0981c7e23f864f027c1449cc008aa5b2a57。
按各片相对原生baseline的残留回声能量比算术平均，全部208片平均改善3.934548332929564%；
逐组平均改善3.3115556708359932%到5.216719193348707%。该百分比不是感知分数或dB平均值直接换算。
各组平均额外ERLE为0.14766938183109582到0.2400852434203884 dB。
逐例最差far变化-0.004023993872237952 dB；最差双讲SI-SDR变化-0.024031155301329044 dB；
最差target投影变化-0.08059350050294789 dB，均在原保护门限内。
near-only原指标精确保持，最终/IFFT/OLA/output_gain削顶及AGC内部饱和均不增加。
每组原farmean>=0.5dB门禁仍失败，保留原qualified=false；优化分级optimization_candidate=true。
新的1%逐组改善保留门槛不表示听感显著或生产放行；complete_solution=false/shipping_approved=false。

| 已暴露组 | 数量 | 平均残留能量降低 | 最差双讲变化dB |
|---|---:|---:|---:|
| development24 |24|4.104010%|-0.011472|
| development8 |8|5.216719%|-0.001421|
| exposed24 |24|3.773459%|-0.000916|
| expanded24 |24|3.847355%|-0.006775|
| expanded8 |8|3.488692%|+0.000726|
| exposed-new24 |24|3.311556%|0|
| exposed-failed24 |24|4.632298%|-0.012031|
| regression24 |24|3.361787%|-0.009410|
| exposed-independent24 |24|3.564703%|-0.000332|
| exposed-v27-24 |24|4.602447%|-0.024031|

127项Python工具回归通过、无skip；独立整数C预测/历史FIFO/无参考/Reset/VOICE及负控制通过ASAN/UBSAN。
静态原生库没有整体ASAN插桩。最新源码重建candidate/control/native三个实际评分二进制，SHA与冻结评分二进制精确一致；
最终contract二进制SHA 7622b8d494b6e2500f317a92356a386271e7d8d447b07420a99f87d470f95a1e。diff --check通过。

当前208全部已暴露，不能再称独立集。本轮已从pinned official train partition取得新24片、96四轨；
与208的speaker/clip按meta排除、四组合均衡、来源NN预训练独立性未知，不能称官方挑战验证或设备验收。
新split SHA a348b11708e5d27b9b6bdf06d685b31d641d937009af3971018b884c93db27aa，尚未评分；为后续更强模型保留。

v38显式PCMC38 beta格式已落地，旧PCMD17仍拒绝新格式；后续新几何收集/映射验证正在执行。
该映射任务不是声学候选通过，v37仍只作冻结映射控制。原生库及baseline未改；
没有ARM/app/HIL新证据，没有改上层订阅、reader或lease，没有覆盖生产库、commit/push/deploy。

候选身份、原门禁、声学改善、Provider reviewing及Runtime conformance分别报告。

