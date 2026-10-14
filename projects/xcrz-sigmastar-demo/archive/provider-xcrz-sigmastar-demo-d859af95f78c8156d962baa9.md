---
id: provider-xcrz-sigmastar-demo-d859af95f78c8156d962baa9
title: v29：扩大开发覆盖后的固定 SI 锥候选
kind: debug-record
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/archive/provider-xcrz-sigmastar-demo-d859af95f78c8156d962baa9.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: provider-candidate-archive
  from: provider-policy-sha256:a295759999c3c3c2594752350565bbde6af74808af32b9272604f53a36f82736;operation:d859af95f78c8156d962baa95531f9db06f88071ee0b5f4e10207d6c2a49a351
  source_sha256: 4990ef366ab6600f3b74c06b647aa28c4b078cf053b96a41cac2721ecd404c6c
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
- projects/xcrz-sigmastar-demo/archive/provider-xcrz-sigmastar-demo-d859af95f78c8156d962baa9.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/archive/provider-xcrz-sigmastar-demo-d859af95f78c8156d962baa9.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-10-10'
updated_at: '2026-10-10'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-10-10'
manual_validation_pending: true
summary_zh: 用户批准累计时间36小时、Token150000000；2亿Token提问尚未收到回复。 新1996独立24未评分、未参与训练。已暴露2b9/c8f48自v29明确重分类开发； 旧136允许集仍拒绝48，184入口仍拒绝1996。无生产默认/ABI/VOICE/上层生命周期修改。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
subject_ref: &id001
  id: xcrz-sigmastar-demo
  type: project
created_subject_ref: *id001
principal_id: null
provider_operation_id: d859af95f78c8156d962baa95531f9db06f88071ee0b5f4e10207d6c2a49a351
---

# v29：扩大开发覆盖后的固定 SI 锥候选

用户批准累计时间36小时、Token150000000；2亿Token提问尚未收到回复。
新1996独立24未评分、未参与训练。已暴露2b9/c8f48自v29明确重分类开发；
旧136允许集仍拒绝48，184入口仍拒绝1996。无生产默认/ABI/VOICE/上层生命周期修改。

184 guard统计SHA bd12fdd77de25cccb772167547a71969af90eb59a244513210a1b5ad40171e6e；
完整99 Python测试通过（6.775秒，无skip）；两组新增mapping误差均远低于.05dB。
模型SHA 1a5f5b4b4a3e45b196dedee90705e75a49debde2ca8d7d3c801e5d498e1fb62b；
同固定参数单轮拟合收敛，239量化保护约束通过，预测far_mean +0.6044508505561741dB。

实际candidate/control编译通过；实际C ASAN/UBSAN合同通过，包括基函数整数数值、
echo FIFO、无reference、Reset/VOICE、原生AGC、guard允许/跳过及前一整Feed shadow快照。
编译初两次遗漏evaluator强制adapter include（第二次加ABLATION=0不能代替include），
报缺少tailAblationState；核对源后以 -include tests/sevc_tail_ablation_adapter.h 及
-DSEVC_TEST_TAIL_MODE=1 修复真实构建命令，未改源码绕过编译错误。

九个184 actual C配对评估及资格检查均正常exit0，各原始/qualification JSON已保存。
所有cohort double_worst、target_worst、near_exact、near_worst、clips、
agc_internal_saturation、far_worst通过，双讲最差约-.080dB、target最差约-.198dB。
八组全门槛通过；exposed-new24（c217，现开发数据）的far_mean
+0.48904166666666676dB < +0.5dB，qualified=false，v29拒绝采用。
其余far_mean依次development24 .6799583333、development8 .88975、
exposed24 .5920833333、expanded24 .5992916667、expanded8 .514625、
exposed-failed24 .7164166667、regression24 .5212083333、exposed-independent24 .5681666667。
三位小数评估已明确失败；尚未执行v29精确PCM复核，不能把训练预测或四舍五入评估
升级为精确PCM资格，更不能评分新1996或声称设备严重回声已解决。

结论：shipping_approved=false，main acoustic goal未完成。未commit/push/deploy。
同目录 REPORT-v28/PLAN-v29/DRY-v29/FIT-DRY-v29.md 与实际JSON提供完整证据。
下一步建议先对失败cohort精确PCM确认，再明确冻结包含九组far_mean下界的约束方案；
v29仅优化总体far目标，没有各cohort均值下界，不能把总体+0.604当成各cohort均合格。
新cohort收益约束属于新版本规划，不能扫参数或改变原验收门槛来采用v29。
