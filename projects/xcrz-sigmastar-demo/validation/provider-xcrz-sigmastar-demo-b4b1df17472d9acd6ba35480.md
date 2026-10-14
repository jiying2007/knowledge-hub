---
aliases:
- v70原生隔离集成v72验证
related:
- projects/xcrz-sigmastar-demo/README.md
- indexes/obsidian-home.md
- indexes/project-readiness.md
id: provider-xcrz-sigmastar-demo-b4b1df17472d9acd6ba35480
title: v70原生隔离集成v72验证
kind: validation
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/validation/provider-xcrz-sigmastar-demo-b4b1df17472d9acd6ba35480.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: provider-candidate-archive
  from: provider-policy-sha256:a295759999c3c3c2594752350565bbde6af74808af32b9272604f53a36f82736;operation:b4b1df17472d9acd6ba35480a40ff65242392570d55cc35146a2b8d960ac0427
  source_sha256: 6c9a1e8020500be05b0e41eadc14318f2b5deb73024524d60f3659f9fd06ee9a
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
- projects/xcrz-sigmastar-demo/validation/provider-xcrz-sigmastar-demo-b4b1df17472d9acd6ba35480.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/validation/provider-xcrz-sigmastar-demo-b4b1df17472d9acd6ba35480.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-10-11'
updated_at: '2026-10-11'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-10-11'
manual_validation_pending: true
summary_zh: 结果：冻结v70相干幅度机制已在实际sevc_func C副本中集成，默认生产原source不开启。Host 400 mixed与400 explicit-near，在原有80帧warmup后全PCM与冻结v70wrapper逐样本一致；16run
  CALL/VOICE raw全PCM一致；nativefrontend/AGC exact、disabled原生基线exact、clip对齐均通过。整数能量exact，near-dot/near-power容差abs.5或relative1e-12，字段已明确区分，不能称floatbitexact。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
subject_ref: &id001
  id: xcrz-sigmastar-demo
  type: project
created_subject_ref: *id001
principal_id: null
provider_operation_id: b4b1df17472d9acd6ba35480a40ff65242392570d55cc35146a2b8d960ac0427
---

# v70原生隔离集成v72验证

结果：冻结v70相干幅度机制已在实际sevc_func C副本中集成，默认生产原source不开启。Host 400 mixed与400 explicit-near，在原有80帧warmup后全PCM与冻结v70wrapper逐样本一致；16run CALL/VOICE raw全PCM一致；nativefrontend/AGC exact、disabled原生基线exact、clip对齐均通过。整数能量exact，near-dot/near-power容差abs.5或relative1e-12，字段已明确区分，不能称floatbitexact。

parity报告SHA bbd483a27dc966535d7c425c14dbaa3d645994c02ba09f2fef0aa61377c05727；全部4416 bindingfresh PASS（次数/去重口径按报告），nativearena [336092,308308] bytes；增27784B，与v69候选arena相同。12cycle切换/reset/两instance/关闭参考成功，frontend5520/AGC5520/VOICE2592/no-referenceCALL840 checks，202 lifecycle identities fresh PASS。lifecycle旧helper JSONkind字面native-v52-opt-in-lifecycle保留，通过实际native_variant version70/integration72、source/overlay/lib hash认定本次v70；不篡改历史报告。

Host .so SHA488d65fb85846ff0c8c7bed0462ac0d54af74f49c576671a610d8b1ea14af2cc，ARM .so SHA f18eb096db6c534e756c007b72f5ae01ad8143c5c4c590e772c0369aa2fe39d7，ARM ELF32/EABI5 hardfloat/BuildIDdb65cb4fcfe914f54e29d18cc59bf1fe9bb0ab73；两构建各197 source/headerfreshPASS。ARM未运行，不表示SSC305资源或真实电话qualification。额外性能binary performance-native-joint-v72已编译尚未运行，不能引用v69数字代替本次CPU。

source覆盖仅EV/native-v70-sevc-func-v72.c SHA dc5bd4148f751e44676f5d12b00be4671ce2a89903bacb5a786cf574e5d18a7b；原生产sevc/src/sevc_func.c SHA1770ad5d025e5078e61f5396c69ff862467d2c6ada115896bad6b5d634cb8c0f不变，native default flag0。新工具joint_native_build/parity与测试独立，不改旧v69冻结工具；BUILD-v72-pre-parity-corrected.json评分前锁源/bin。复制测试旧version67断言在dry之后、actualquality之前改70，208 tests/7.000s通过，算法/bin保持不变并保留原seal及更正说明。

本次效果由REPORT-v70-v71.md记录：400例v70远端单讲输出能量平均下降4.3157644%、v67为2.6516436%；v70最差双讲-.09522275dB接近-.1下限。所有保护通过，但每组far mean>=.5主提升门槛未全通过，持续手机自回声未解决；不称全球最优/产品可用。Host source/parity、ARM构建、ARM执行、设备安装/phone、Provider reviewing/owner分别验收。

用户明确批准累计60h已实际Runtime更新216000s，Token300M保持，deadline2026-10-12T02:56:57Z。ExecutionPolicy要求compact，先checkpoint真实宿主压缩/recheck，再补nativev72 CPU及透明机制诊断。无commit/push/relink app/deploy/restart/cleanup，上层reader/lease/proto不变。

补正：原REPORT-v72-native.md的lifecycle identities计数写为201，实际NATIVE-READBACK-v72.json为202；本副本更正计数。原报告与归档身份保留，不改source/bin/parity或结果。

