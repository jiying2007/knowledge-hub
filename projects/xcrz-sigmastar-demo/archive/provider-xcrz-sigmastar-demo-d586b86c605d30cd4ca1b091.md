---
id: provider-xcrz-sigmastar-demo-d586b86c605d30cd4ca1b091
title: CALL AEC v70/v71：更强候选、400例验证与原始录音
kind: debug-record
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/archive/provider-xcrz-sigmastar-demo-d586b86c605d30cd4ca1b091.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: provider-candidate-archive
  from: provider-policy-sha256:a295759999c3c3c2594752350565bbde6af74808af32b9272604f53a36f82736;operation:d586b86c605d30cd4ca1b0910b4094be0dfd2ec3b37c6353b14b01d0f0ba8e1f
  source_sha256: b101c372fa70455b5518b7cb19728a61aaa453098755011f648f5a44659b768f
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
- projects/xcrz-sigmastar-demo/archive/provider-xcrz-sigmastar-demo-d586b86c605d30cd4ca1b091.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/archive/provider-xcrz-sigmastar-demo-d586b86c605d30cd4ca1b091.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-10-11'
updated_at: '2026-10-11'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-10-11'
manual_validation_pending: true
summary_zh: 结论：v70相干幅度联合修正在预定逐例保护下，比v67更强。376例回归和新增24例首次验证全部通过；仍没有达到所有组mean far>=0.5dB，持续手机端自回声完全解决尚未证明。v70列入更积极的候选，v67保留为更保守的选择，不宣称全局最优，不开启生产默认配置。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
subject_ref: &id001
  id: xcrz-sigmastar-demo
  type: project
created_subject_ref: *id001
principal_id: null
provider_operation_id: d586b86c605d30cd4ca1b0910b4094be0dfd2ec3b37c6353b14b01d0f0ba8e1f
---

# CALL AEC v70/v71：更强候选、400例验证与原始录音
结论：v70相干幅度联合修正在预定逐例保护下，比v67更强。376例回归和新增24例首次验证全部通过；仍没有达到所有组mean far>=0.5dB，持续手机端自回声完全解决尚未证明。v70列入更积极的候选，v67保留为更保守的选择，不宣称全局最优，不开启生产默认配置。

| 冻结候选 | 回归376远端输出能量降低 | 新24首次验证 | 合计400 | 400最差双讲变化 |
|---|---:|---:|---:|---:|
| v67 | 2.567246% | 3.973874% | 2.651644% | -0.057470dB |
| v70 | 4.178358% | 6.468470% | 4.315764% | -0.095223dB |

这些百分比是逐clip远端单讲输出能量降幅的等权算术均值，不是ERLE百分比或手机听感合格率。v70双讲最差fid1285，接近-.1门槛，保护余量小于v67，不能认为v70全面支配v67。376例最差far-.002640dB fid236，target-.089622dB fid1088；新增24最差双讲-.086134dB。所有逐例far/DT>=-.1,target>=-.2、显式near全部metricexact、原生frontend/AGC轨迹exact、clip不增均通过。17回归组每组energy降幅>=1%，每组meanfar>=.5主门槛未全通过。

机制：已有因果指数平滑pm/pe/cr/ci，r=clamp((cr²+ci²)/(pm*pe+1),0,1)，a=sqrt(min(1,pe/pm))，w=floor(.5*(1+r)*a*1048576)，原生与冻结v52输出凸组合，最大强度1；count>=8/所有状态与中间量有限，异常回退0；uint64两端能量上限和native .2幅度floor，失败回退原生。沿用父DTD/相位/参考/AGC，无新增NN/AEC/全局NN功率/标签/未来truth。唯一公式在PLAN-v70-joint.md冻结，BUILD-v70-pre-score.json先锁source/bin后评分，未按新样本调参。上层协议、reader、lease及持有帧不变，无设备写。

新v71数据：Microsoft AEC Challenge exact revision6c633d0a9d2a143a0e364899b91b06f127315b18，meta SHA6b867aa68f510e4bafc9ffa05202930ffc1bb54bb0cffe66aa1ec3bcc606f3e5，train partition、四组各6、SER正负各3，排全部17组376 id及speaker/sourceclips；SELECTION-v71.json/PLAN-v71-validation.md下载评分前冻结。96轨SHA/size/mono16k16/frame数复验通过；split SHA2439a5ecde7694c2d0f8514a762d7769afa8037ab340b23355bf5f3214cfd4d6。只对本工程fit独立，NN pretraining独立性unknown，不是官方challenge资格。新24两候选96trace/192input bindingfresh，376先前2293去重bindingfresh。v71现在已经暴露，下批必须排全部400。

两轮device raw 16run CALL/VOICE离线：VOICE16全PCMexact；CALL quiet/near/motion/near-motion8全PCMexact；所有native bridge与冻结library一致且clip不增。far索引3/7/11/15 output energy change -.935606/-1.172825/-.712627/-.642278dB，明显强于v67的-.524658/-.646776/-.409684/-.369883。raw无clean目标，不称ERLE/DT fidelity或真人听感合格；没有本轮设备安装。

数值验证：20k full-int32凸组合/uint64 floor，加0/1、NaN/Inf/overflow/非法weight、两实例/第三拒绝、identity PCM、CALL参考丢失、VOICE/Reset/AGC/资源清理，ASAN/UBSAN通过（旧静态库未全插桩）。完整Python208 tests通过7.000s，原生builder复制测试的旧67断言已在任何native质量重放前纠正到70，原生source/bin/机制未改；保存原preseal与corrected seal。非仓库cwd新工具help/dry-run writesfalse，父仓/子仓diff--check通过。

补齐v69原生Host资源：5round serial交错 nativebaseline/v67wrapper/v69native，2000frames80warmup/threadclock，无quality并发。CALL中位207.032/239.755/247.633us，v69对native+19.611%；VOICE109.580/106.887/107.779us波动，不能宣称VOICE性能提升。v69与wrapper PCM hash CALL5388518921190214564/VOICE10513963233676980736完全一致；arena336092 vs308308，增27784B。RESOURCES-NATIVE-v70.json保存实际15次stdout。此资源只属于v69/v67，不能冒充v70/v72或SSC305性能。

v70的原生隔离集成v72另有PLAN-v72-native.md与BUILD-v72-pre-parity-corrected.json；本报告不依赖正在进行的v72全400PCM结果。生产默认sevc_func.c SHA1770ad5d025e5078e61f5396c69ff862467d2c6ada115896bad6b5d634cb8c0f保持不变，default off；不commit/push/relink应用/install设备。源实现、Host、ARM构建、ARM运行、手机听感、Provider reviewing/owner决定分别验收。

下一步：完成v72原生PCM资格/实际资源；需要更强机制时新独立假设与SHA冻结，优先保护1285及新样本，不通过常数扫参掩盖双讲损伤。最终phone echo目标仍open1。

