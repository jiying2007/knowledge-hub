---
id: provider-xcrz-sigmastar-demo-de2a4495d0dad20b8e471cbf
title: CALL AEC v65/v66 有界优化结果
kind: debug-record
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/archive/provider-xcrz-sigmastar-demo-de2a4495d0dad20b8e471cbf.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: provider-candidate-archive
  from: provider-policy-sha256:a295759999c3c3c2594752350565bbde6af74808af32b9272604f53a36f82736;operation:de2a4495d0dad20b8e471cbff111486424c5da37f4b077aaca5bc192be2ba0cd
  source_sha256: 02159b558fd0a496b48f546b1cf6a5425286281a5aae22cec70d28941253b0c3
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
- projects/xcrz-sigmastar-demo/archive/provider-xcrz-sigmastar-demo-de2a4495d0dad20b8e471cbf.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/archive/provider-xcrz-sigmastar-demo-de2a4495d0dad20b8e471cbf.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-10-11'
updated_at: '2026-10-11'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-10-11'
manual_validation_pending: true
summary_zh: 持续CALL远端自回声尚未解决。v66 新的逐频点回声功率占比机制通过完整352例/16组保护，作为更保护双讲的候选保留；回声优先的已有同范围候选仍为v63，不称全局最优、生产可用或完全解决。用户继续优化授权在累计250M/48h内沿用；2026-10-11T12:15:30Z
  Runtime实际goal_tokens=250566128，超过250000000，recommended_action=stop。本轮按用户AGENTS保存证据和检查点，不继续新实验、不重置预算；goal active/open1，completion_claim=false。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
subject_ref: &id001
  id: xcrz-sigmastar-demo
  type: project
created_subject_ref: *id001
principal_id: null
provider_operation_id: de2a4495d0dad20b8e471cbff111486424c5da37f4b077aaca5bc192be2ba0cd
---

# CALL AEC v65/v66 有界优化结果

持续CALL远端自回声尚未解决。v66 新的逐频点回声功率占比机制通过完整352例/16组保护，作为更保护双讲的候选保留；回声优先的已有同范围候选仍为v63，不称全局最优、生产可用或完全解决。用户继续优化授权在累计250M/48h内沿用；2026-10-11T12:15:30Z Runtime实际goal_tokens=250566128，超过250000000，recommended_action=stop。本轮按用户AGENTS保存证据和检查点，不继续新实验、不重置预算；goal active/open1，completion_claim=false。

## 实际行为与同范围比较

v65透明观测了644/686/27各624主帧以及rpm240第03份far原录音1880 NN回调。所有metrics/counters、前端/AGC/对齐整数PCM统计与冻结v63相同，原录音全PCM逐点exact。发现高NNgain同时包含644双讲风险与686远端收益，而每bin估计echo/mic功率占比不同；频率归因不是clean truth或PCM质量，详见REPORT-v65-diagnosis.md。

v66因果系数为0.5*min(1,parent-smoothed-echo-power/parent-smoothed-mic-power)，父已有逐bin1/8平滑与8帧暖机；非有限/非正/未暖机回退原生。保持v52参考/DTD/phase保护、原生AGCdriver、精确uint64端点功率和NNfloor；没有新AEC回调、raw队列、未来/clean目标、上层改动。

|方案|352例远端输出能量平均下降|最差双讲变化dB|最差远端变化dB|最差target投影变化dB|
|---|---:|---:|---:|---:|
|v62 固定3/16|1.5091393324%|-0.0446290020|-0.0110228208|-0.0290891233|
|v63 固定5/16|2.4599451881%|-0.0796023881|-0.0188995573|-0.0485235988|
|v66 逐bin功率占比|2.0166460426%|-0.0305015913|-0.0000583381|-0.0424434333|

v66最差DT为215、最差far582、target1088；644双讲精确变化见实际fresh24审计record，控制台约-0.004dB。所有16组能量收益>=1%（1.4097442450%到2.5812004856%），352例far/DT>=-0.1,target>=-0.2、全部explicit_near metrics exact、clips非增、原生AGCdriver/gain及前端轨迹保护PASS。每组far均值>=0.5dB仍FAIL，实际持续电话听感未验证。所有数据组均已暴露，v64数据被本轮机制诊断使用，不称独立盲验证。

## 实现与验证

新增Host v65 observer/header、tail_bin_probe/tail_raw_bin_probe与两项解析负测试；新增Host v66 header/contract、echo_leverage_audit与三项审计负测试。仅tests/README追加旧v52/v59新反例边界和v63当前352保护范围；未改生产算法/default/native开关/上层reader/订阅/lease/proto。旧v52/v59在644 DT约-0.343dB仍不合格，不能启用旧nativeflag替代v66。

v66四源/三bin在评分前冻结BUILD-v66-pre-score.json；20,000 full-int32变权重数学例、NaN/Inf/暖机/非法权重、ASan/UBSan身份PCM/原生AGC/两个实例/第三实例拒绝/CALL参考消失/VOICE/Reset/释放实际PASS。库内部未整体插桩。全Python192项/8.272s/exit0，无skip；三个工具非repo cwd help/dry实际PASS/writes=false。父子git diff --check exit0。关闭前fresh 83个旧新source/bin/plan/report绑定PASS；v66全部704 trace、1408输入绑定读回PASS。绑定次数不等于唯一文件数。

第一次v65 observer编译因fprintf少一个占位符被Werror拒绝，修正后冻结且编译通过。v66构造脚本首次在apply之前断言拒绝，不产生source；修正构造后所有编译和contract通过。v66审计JSON的kind字面量仍为历史host-bounded-followup-v63-actual-output-energy-audit，属于克隆标签遗漏；实际严格校验echo_leverage.version=66/动态系数机制且candidate SHA绑定正确，输出目录v66、source/bin冻结正确。保留原sealed脚本/审计不重写，REGISTRY-v66-352.json记录该标签erratum，不把它当成v63机制。

## 未完成与恢复

v66原16录音全重放、Host性能/资源、独立新盲集、默认off native接入、ARM运行和设备/电话资格均未做；此前v63原录音资源结果不能替代v66。v65第03原录音仅透明诊断。v66有更好的双讲余量，但效果/成本尚不能用于选择产品最终方案。

在新累计预算获批准后，优先补v66原16录音与资源并固定候选选择，再冻结新机制。例如线性修正的echo幅度占比与功率占比是否匹配，必须独立计划/固定参数/新binary/首56反例门槛后全352，不能改写v66 identity或无界强度扫描。任何新独立数据须排全部352 speaker/clip。预算和deadline不重置，无commit/push/deploy/restart/cleanup。脱敏Provider归档只声明实际回执语义，不等于owner review或产品放行。
