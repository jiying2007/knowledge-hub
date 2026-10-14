---
aliases:
- CALL AEC 当前优先候选固化决定
related:
- projects/xcrz-sigmastar-demo/README.md
- indexes/obsidian-home.md
- indexes/project-readiness.md
id: provider-xcrz-sigmastar-demo-ea073afae31ad85f25ff4a84
title: CALL AEC 当前优先候选固化决定
kind: validation
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/validation/provider-xcrz-sigmastar-demo-ea073afae31ad85f25ff4a84.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: provider-candidate-archive
  from: provider-policy-sha256:a295759999c3c3c2594752350565bbde6af74808af32b9272604f53a36f82736;operation:ea073afae31ad85f25ff4a8479eb3fac13db73ea59a9d8cbe00fbf06971663f9
  source_sha256: 40a418ab9d2b81e7a011731f0ff43d743e08f99f4322685d9238658721d08fc1
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
- projects/xcrz-sigmastar-demo/validation/provider-xcrz-sigmastar-demo-ea073afae31ad85f25ff4a84.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/validation/provider-xcrz-sigmastar-demo-ea073afae31ad85f25ff4a84.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-10-11'
updated_at: '2026-10-11'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-10-11'
manual_validation_pending: true
summary_zh: 结果：用户要求“在所有已验证方案中，先候选固化一个最优版”，已将v70算法 + v72原生集成固定为call-aec-v70-native-v72-rc1。本次仅本地候选固化，不代表设备采用或生产放行。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
subject_ref: &id001
  id: xcrz-sigmastar-demo
  type: project
created_subject_ref: *id001
principal_id: null
provider_operation_id: ea073afae31ad85f25ff4a8479eb3fac13db73ea59a9d8cbe00fbf06971663f9
---

# CALL AEC 当前优先候选固化决定
结果：用户要求“在所有已验证方案中，先候选固化一个最优版”，已将v70算法 + v72原生集成固定为call-aec-v70-native-v72-rc1。本次仅本地候选固化，不代表设备采用或生产放行。

选择准则先满足现有完整400例逐例保护和原生PCM资格，再最大化同口径远端单讲输出能量降幅。v70均值4.315764%，v67均值2.651644%；指标为逐clip输出能量降幅等权均值，不是ERLE百分比或手机听感合格率。旧方案未全部在400例同口径验证，不能宣称全历史全局最优。v70最差双讲-0.095223dB，接近-0.1dB下限，保护余量较小；保留v67/native v69 Host库与原生基线回退锚点。

此前400 mixed与400 explicit-near在80帧warmup后PCM逐点一致、16raw全PCM一致、整数能量exact、浮点target-dot容差abs.5或relative1e-12、12cycle生命周期通过。此次fresh核对全部4416 PCM/parity binding及202 lifecycle binding、旧与新源码309合并身份。既有完整Python208项通过，无新算法改动，不重复整批评分。

补齐v72真实Host资源：5轮串行交错native baseline/v69/v72，2000frames+80warmup/threadclock，无quality并发。CALL中位baseline207.050μs、v69 250.886μs、v72 248.707μs，v72比baseline约+20.119%。v72 CALL PCMhash3835538952602450135，所有VOICEhash10513963233676980736，五轮稳定；arena336092bytes比baseline增27784bytes。不称SSC305实际CPU，VOICE耗时波动不宣称性能提升。

固化快照含287个项目source/header/tool/build-report/static-library/replay-library及回退成员，压缩包7181948 bytes，逐成员SHA256验证fresh全部通过。tar仅relative regular文件；无raw audio/log/core/凭据原文；manifest逐项固定dirty源码身份，Git HEAD不能替代文件清单。
snapshot SHA ee4e5838bc0a975ef43cf0385baf64ed57e0a6b10d599bb8526112cca773b012
manifest SHA 9f12106ed7cf1b119b786e9cea7eca1c782327672bac11ab44e6b64bc03db794
overlay SHA dc5bd4148f751e44676f5d12b00be4671ce2a89903bacb5a786cf574e5d18a7b
Host replay.so SHA488d65fb85846ff0c8c7bed0462ac0d54af74f49c576671a610d8b1ea14af2cc
ARM replay.so SHA f18eb096db6c534e756c007b72f5ae01ad8143c5c4c590e772c0369aa2fe39d7
ARM BuildID db65cb4fcfe914f54e29d18cc59bf1fe9bb0ab73
PCM report SHA bbd483a27dc966535d7c425c14dbaa3d645994c02ba09f2fef0aa61377c05727
lifecycle SHA247da255fab7733e35e6d0c681abeca8967b48c64e7f88c46fa7d855279159d2

候选静态库libaispeech.a供将来受控重链接；libsevc_replay.so为验证库不是部署应用库。ARM已交叉构建但未执行，外部toolchain/config是复建前提；绝对编译路径迁移需审阅。BUILD_DATE等元数据使复建库SHA可变，须重新锁制品。

采用必须同时用v72 overlay及SEVC_CALL_RESIDUAL_CANDIDATE=1，不能只打开旧生产source的v52机制，也不能叠加Hostwrapper到native候选。生产source SHA1770ad5d025e5078e61f5396c69ff862467d2c6ada115896bad6b5d634cb8c0f未变，default off。业务proto/reader/订阅/lease/持有帧保持既有行为；未重链接应用、部署、重启、commit或push。

负结果/修正：最初复建说明误用不存在的tools.codex_assets包级入口，exit1；更正为实际joint_native_build模块后从/tmp dry-run exit0，69compile plan/writes=false。仅修正文档入口，算法与库未改。

完成声明：本次候选固化完成，持续手机自回声完全解决目标仍未闭环；每组far mean>=0.5dB主提升门槛仍未全通过。真实电话听感、ARM CPU/长跑与产品采用需后续独立验收。此次没有进行新的听感验证或独立owner review，Provider归档仅reviewing。

Codify Decision：reusable_pattern=算法/原生版本分开并逐项锁SHA；promotion_candidate=false；next_task_friction_reduced=true；reduced_by=单包源/库/报告/回退与复建入口；reduction_evidence=287成员tar与SHA fresh核验；do_not_promote_reason=电话目标和ARM执行未闭环；owner_review=awaiting；rollback_path=原生flag0及v67/v69 Host；verification_evidence=manifest/readback/现有绑定报告。

阶段退出：固化包fresh核验、复建dryrun、源码身份保持和diffcheck；父目标open item保留。不创建新目标或重置累计预算，沿用用户批准的300M Token/60h。

