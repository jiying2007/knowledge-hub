---
id: provider-xcrz-sigmastar-demo-79733f5904388a2bd972cd0f
title: v32：上一整Feed对齐的shadow DTD逐帧诊断
kind: debug-record
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/archive/provider-xcrz-sigmastar-demo-79733f5904388a2bd972cd0f.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: provider-candidate-archive
  from: provider-policy-sha256:a295759999c3c3c2594752350565bbde6af74808af32b9272604f53a36f82736;operation:79733f5904388a2bd972cd0f31464488a8c870949a3a8fe3245bc08ac9ad0301
  source_sha256: 7fac4d4a65ebd80b8737991bbf7b5c4c45c640add5c99aaf503ea42dc138c84a
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
- projects/xcrz-sigmastar-demo/archive/provider-xcrz-sigmastar-demo-79733f5904388a2bd972cd0f.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/archive/provider-xcrz-sigmastar-demo-79733f5904388a2bd972cd0f.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-10-10'
updated_at: '2026-10-10'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-10-10'
manual_validation_pending: true
summary_zh: 主声学目标未完成，累计预算200M/36h。v31开发完整通过但独立550/831失败，已拒绝。 本轮只增加Host观察：evaluator在Feed前复制shadow DTD值，并仅在--trace-frames时输出。
  不改变生产判据、音频数据、算法库、profile或上层生命周期。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
subject_ref: &id001
  id: xcrz-sigmastar-demo
  type: project
created_subject_ref: *id001
principal_id: null
provider_operation_id: 79733f5904388a2bd972cd0f31464488a8c870949a3a8fe3245bc08ac9ad0301
---

# v32：上一整Feed对齐的shadow DTD逐帧诊断

主声学目标未完成，累计预算200M/36h。v31开发完整通过但独立550/831失败，已拒绝。
本轮只增加Host观察：evaluator在Feed前复制shadow DTD值，并仅在--trace-frames时输出。
不改变生产判据、音频数据、算法库、profile或上层生命周期。

新工具tail_dtd_guard_probe从冻结evaluation/split和输入哈希读取550/831及540/556对照。
原始输出metric四例与冻结v31 actual C严格相同；frame完整唯一，前一AES与NN lookahead对齐，
previous两个hop真值phase不同时排除混合边界。真值仅用于离线归因，不进推理。
不保存raw日志，生成聚合JSON SHA657563ecb1babd2150b4a094b49228b16363d72b5ce614bcac48b665133897a4。
观察二进制SHA5e8a1f4f0d817b2f034cbf84bea34b0f429bacb024aaafa4a31666296055b06c。

550稳定双讲346帧，原guard允许224；其中56帧instant residual/echo>1.5，
95帧similarity>10000。831稳定双讲291帧，允许157；其中41帧instant>1.5，
43帧similarity>10000。计数可交叉，不可相加；高相似度不是近端标签。
现有candidate要求instant/smooth均>1.5且similarity<=10000，允许这些帧是源码判据的实际行为。

固定分布桶显示仅降比值不能证明可靠分离：以smooth<1.0为分布例，550双讲129/346、
远端169/234；831双讲105/291、远端287/325；556远端仅6/447。
这些是分布观察，不是新guard质量评分，不允许挑桶后称独立通过。
shadow guard比NN实际eligible帧更广；支持的NN gain/输出一致性仍会跳过部分频点。

完整107 Python tests PASS 6.107s，无skip；非仓cwd help/dry-run PASS、git diff --check PASS。
新三项控制验证上一帧对齐/边界排除、缺帧/重复帧拒绝、缺失分母不误计。
evaluator新增声明/快照的初始patch匹配到near-only循环，编译前检查定位并移到目标混合循环，
实际编译和四例metric精确一致；不把临时修正视为新的声学实验。

source：tail_dtd_guard_probe.py SHA4560b94fa79cb10d22461e5ef83e1fb48088e0ad55876082f1b2eebc2aca730e；
test SHA8ed294df0bfa7a9786692840b833df6c40d9a48bb17cecdfdfe7730088f6410e；
evaluator SHA2c30c5a38c7fc622a45e5a428db86aab78879ec53e2369aa98f347ac3a6f45a1；
README SHA5e2db4f567647ccdcfd552f92ac390fcd416cc3f574368340c791362ae3d44a7。
精确独立v31失败JSON SHAb7a26351a4adae52e419b2e263e0b97205ed2b1183e4712fdb6aacdf9e4e3dc6。

结论：训练保护通过并不足以保障未见双讲；下一步应针对校正安全性独立设计保护，
保留现有生产路径，对固定新机制先作真实C因果配对，再做完整暴露数据回归及新独立验收。
尚无生产可采用的新候选，不能宣称最优或严重回声已消除；无commit/push/deploy/restart。
Execution Policy在本轮触发context-pressure/compact，需保存接力；预算尚有余量。
