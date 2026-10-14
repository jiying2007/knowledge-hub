---
aliases:
- v69 原生 v67 候选接入验证
related:
- projects/xcrz-sigmastar-demo/README.md
- indexes/obsidian-home.md
- indexes/project-readiness.md
id: provider-xcrz-sigmastar-demo-09191df8a6dcd01329f29b83
title: v69 原生 v67 候选接入验证
kind: validation
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/validation/provider-xcrz-sigmastar-demo-09191df8a6dcd01329f29b83.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: provider-candidate-archive
  from: provider-policy-sha256:a295759999c3c3c2594752350565bbde6af74808af32b9272604f53a36f82736;operation:09191df8a6dcd01329f29b8329e03765731e73c6246bba2735682a6dc179d5fa
  source_sha256: 87048c52c189446d116aca09ab2628296a5a414b31cd537b83d043d9cc21bcb6
  temporary_source_retained: false
review_after: '2027-01-09'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- provider-archive
- validation
validation_refs:
- projects/xcrz-sigmastar-demo/validation/provider-xcrz-sigmastar-demo-09191df8a6dcd01329f29b83.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/validation/provider-xcrz-sigmastar-demo-09191df8a6dcd01329f29b83.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-10-11'
updated_at: '2026-10-11'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-10-11'
manual_validation_pending: true
summary_zh: 当前证据范围内优先候选为v67幅度占比修正；主目标持续电话远端明显回声完全解决仍UNSOLVED，goal active/open1，不complete。累计Token已按用户“提高预算”从250M更新300M，48h截止2026-10-11T14:56:57Z不重置。376例保护PASS及原录音改进见REPORT-v67-v68.md；Provider
  operation6d1596fda156ad137fd38ddc04cf4ac4f2b36e9d77785f67ecfad0a200dad86b已ARCHIVED/reviewing，非owner。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
subject_ref: &id001
  id: xcrz-sigmastar-demo
  type: project
created_subject_ref: *id001
principal_id: null
provider_operation_id: 09191df8a6dcd01329f29b8329e03765731e73c6246bba2735682a6dc179d5fa
---

# v69 原生 v67 候选接入验证

当前证据范围内优先候选为v67幅度占比修正；主目标持续电话远端明显回声完全解决仍UNSOLVED，goal active/open1，不complete。累计Token已按用户“提高预算”从250M更新300M，48h截止2026-10-11T14:56:57Z不重置。376例保护PASS及原录音改进见REPORT-v67-v68.md；Provider operation6d1596fda156ad137fd38ddc04cf4ac4f2b36e9d77785f67ecfad0a200dad86b已ARCHIVED/reviewing，非owner。

本阶段只接入已冻结v67算法，不增加评分后参数调整：alpha=.5sqrt(min(1,pe/pm))，父平滑1/8/count8/invalid->native/uint64端点上限/native floor/旧DTD-ref-phase与原生AGCdriver。冻结原sevc_func.c SHA1770ad5d025e5078e61f5396c69ff862467d2c6ada115896bad6b5d634cb8c0f未改；独立EV overlay SHAe48b4f9fe2d8c35473584e87f214c27b570f831aca3cec8f2f6e3dff849bd925仅有频率输出处单一hunk。新native_variant_build复用actualMakefile，唯一替换sevc_func.c命令，源身份记录实际overlay，绑定原sourceSHA与overlaySHA，加入原sevc/src include，不把复制C加入默认源码glob。

实际69条编译命令的Host candidate/disabled及SigmaStar GCC11.1.0 ARM candidate完成。candidate共享库SHAf0f6c7c7b07a4b27f0e9e901c93bf787fa1a313dc1dce9074d1e84d6d79eaa73，disabledSHAca84fec264124ef2ebb1770b2147bf8a5be8282602939b120d977e14f742d67e与既有关闭控制库完全相同；ARM共享库SHA59907dffb85e1b3f3e31da1d1091e92207d2670fe281dcf61afe9b68d0f9f832，ELF32 ARM EABI5，BuildIDc5083b9ecf08058d6a058e3bfa56dd6c7dae1970。三build各196source/header actualSHA复验PASS；106旧新source/bin/plan/report独立绑定PASS。ARM仅构建，没有ARM执行或设备安装。

先新目录1例smoke逐点PASS，不称完整资格。随后完整376四轨输入，以相同reference delay、80silentwarmup重构，不添加EOF padding，将native library与独立冻结capture-wrapper-v67输出wholePCM逐点比较。376 mixed及376 explicit-near-only全部exact，前端列(除单列clip计数)和AGC驱动轨迹与disabled原生一致；既有实际audit整数per-frame输出energy exact。干净目标dot/power因NumPy与C求和差异使用预先代码指定abs<=.5或relative1e-12比较，不能把浮点dot称bit-exact。报告record旧字段frozen_energy_dot_exact是算法对齐通过含容差，精确范围以此说明和NATIVE-READBACK-v69为准，不重写sealed输出。

16原始录音×VOICE/CALL native输出与v67冻结WAV全PCMexact；candidate VOICE与disabled exact；disabled的PCM/前端/AGC与原frozen baseline exact，candidate frontend/AGC与disabled exact，clip stage计数与v67重放一致。raw录音缺cleantruth，不声称ERLE/双讲音质资格。全部parity4173独立输入/trace/generatedPCM/source/bin/report绑定freshPASS。paritySHA1f48194c909d8516b50633ed85ff080ef27a3d68ab58b8344cd8b57e92524857，host_parity_qualified true限定本实验范围。实际arena candidate336092、disabled308308，增加27784B，原生状态在arena不增加此算法的逐帧heap/thread/NN/AECinstance；不把arena当整个应用内存。此前Host包装父31064+own64+slots16的heap数据不能替代原生资源。

12轮CALL/VOICE/Reset实际5520帧frontend+AGC exact，VOICE排原既有2hop overlapflush后2592帧exact，ref消失并排历史后840帧CALLexact，生命周期PASS；SHAa71be1c90ae48a84752a1fdcf3c42e995b6746a9f08af580ee1b0dc6ec93ef6c。复用既有native_residual_lifecycle工具，其输出kind历史literal native-v52-opt-in-lifecycle；真实candidate由本轮native_variant.version67/integration69与lib/sourceSHA绑定，external erratum在NATIVE-READBACK-v69，旧输出不覆盖，不误称旧v52声学资格。

新build/parity工具及4条meaningful新负向测试(5项：build3/parity2)已纳入总200 Pythontests/7.476s/exit0noskip，非repohelp与dryPASS/writesfalse；prototype v67数学20kASAN/UBSAN与195阶段结果保留。新native嵌入的算术与冻结v67一致，native库未整体ASAN/UBSAN插桩。独立C diff只上述hunk，parent/nested diffcheck0，HEAD99b5f958ffefd93c2cf939b0b28f91f48dde9b57/9ce7a7f87b4835816e68df7fade6d43ebb3d47a1。

综合376同范围：v62/v63/v66/v67远端输出energy均值1.4984852324319122/2.4424571748517194/2.0150303731576193/2.5672459659015634%；最差DT分别-.044629001981391525/-.0796023880658634/-.03754662349140281/-.057469997468510226dB。v67比v63回声收益和最差双讲均更好，v66最差双讲更保守。四rawfar v67输出energy下降.524658/.646776/.409684/.369883dB。每组farmean>=.5dB仍FAIL，不能称完全消回声/全局最优或shipping approved。

当前runtime在14:07Z按user AGENTS ExecutionPolicy要求compact：context_ratio .627326，host_context_maintenance.required=true,next checkpoint-then-host-compaction-and-recheck。只完成已运行parity与必要取证收口，不开启新实验。无可调用宿主compaction工具，不能制造compaction事件或重置预算。native perf binary已编译但尚未运行；wrapper Host CALL mediansnative206.575/v67 241.054us不代替nativeCPU。恢复并实际压缩后先gate/recheck，补原生五轮交错CPU，然后新独立更强机制计划(如幅度占比与coherence共同控制上限；仅假设，未实现/未固定参数)，首反例门槛再完整376/新未评分排speaker/sourceclip。不得把v68已暴露24再次称blind。

默认产品源码/候选开关仍关闭，上层业务/reader/订阅/lease未改变；隔离候选在EV可审查，不是应用已链接/设备已安装。无commit/push/deploy/restart/cleanup，保存全部dirty/raw/冻结source/bin。证据BUILD-v67-v69、DRY-v67-v69、REPO-v67-v69、NATIVE-READBACK-v69和实际parity/lifecycle；Knowledge Provider只能形成脱敏reviewing候选，不替代owner/产品/设备责任。
