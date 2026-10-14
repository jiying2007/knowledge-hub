---
id: provider-xcrz-sigmastar-demo-b58cc806a8318bce5e657055
title: CALL AEC：v62/v63 固定有界修正与 v64 独立验证
kind: debug-record
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/archive/provider-xcrz-sigmastar-demo-b58cc806a8318bce5e657055.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: provider-candidate-archive
  from: provider-policy-sha256:a295759999c3c3c2594752350565bbde6af74808af32b9272604f53a36f82736;operation:b58cc806a8318bce5e657055ec17c2aaafd78679a80cc5129e47401c425fe8a6
  source_sha256: 99811224f93c45874e5fec6141deabb33d6dd51fe18063a27f89a47e0ab3f352
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
- projects/xcrz-sigmastar-demo/archive/provider-xcrz-sigmastar-demo-b58cc806a8318bce5e657055.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/archive/provider-xcrz-sigmastar-demo-b58cc806a8318bce5e657055.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-10-11'
updated_at: '2026-10-11'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-10-11'
manual_validation_pending: true
summary_zh: 日期：2026-10-11。结论：推荐保留 v63 为本轮完整验证候选；持续电话回声未解决，逻辑目标仍打开。v63不代表全局最优或产品放行。 v62 使用 original native NN + 3/16*(frozen
  v52-native)，v63为5/16；原生AGC驱动保持原native输出、NN/AEC/AES/DTD内部轨迹不改。新算法只有Host独立wrapper，不包含H额外投影、raw-reference硬筛选或clean target推理。原v52
  guard/model继续冻结。新八个测试/工具源，不改native/source默认、上层协议/订阅/reader/lea
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
subject_ref: &id001
  id: xcrz-sigmastar-demo
  type: project
created_subject_ref: *id001
principal_id: null
provider_operation_id: b58cc806a8318bce5e657055ec17c2aaafd78679a80cc5129e47401c425fe8a6
---

# CALL AEC：v62/v63 固定有界修正与 v64 独立验证
日期：2026-10-11。结论：推荐保留 v63 为本轮完整验证候选；持续电话回声未解决，逻辑目标仍打开。v63不代表全局最优或产品放行。
## 结果与选择
v62 使用 original native NN + 3/16*(frozen v52-native)，v63为5/16；原生AGC驱动保持原native输出、NN/AEC/AES/DTD内部轨迹不改。新算法只有Host独立wrapper，不包含H额外投影、raw-reference硬筛选或clean target推理。原v52 guard/model继续冻结。新八个测试/工具源，不改native/source默认、上层协议/订阅/reader/lease。
两个候选相同352/16组实际整数PCM轨迹逐例保护通过。352均已评分；其中v64新24在源码/制品冻结后首次验证，排除前328的speaker/sourceclip。推理不使用干净目标。train分区只证明相对本项目拟合独立；NN预训练独立未知，非官方challenge资格。
|方案|原328平均输出能量改善|新24首次改善|合并352改善|352最差双讲SI-SDR差|
|---|---:|---:|---:|---:|
|v62|1.4959497372%|1.6893971337%|1.5091393324%|-0.0446290020 dB|
|v63|2.4391784937%|2.7437566785%|2.4599451881%|-0.0796023881 dB|
所有组均>=1%候选门槛；far最差分别-0.0110228208/-0.0188995573dB，target最差-0.0290891233/-0.0485235988dB；所有近端单讲原指标完全一致、削顶不增加、原生AGC driver/gain和frontend轨迹不变。保护门槛仍为far/DT最差>=-0.1，target>=-0.2dB，未放松。v63最差DT距门槛约0.0204dB，不称任意输入安全。
完整每组far均值>=0.5dB未通过。这里energy是逐音频片段等权百分比平均，不是纯回声量或主观听感。
v52/v59此前304通过但新增v60 644双讲约-0.343dB失败，不能再称全328安全。v61首56保护通过但每组收益<1%，已拒绝扩大。v46及其他旧方案未在新352完整同口径比较，不声明全历史全局最优。
## 设备原始录音重放与资源
16原始录音×VOICE/CALL分别native/candidate；native桥接与冻结库PCM逐点一致。v62、v63都16份VOICE逐点不变；quiet/near/motion/near-motion共8份CALL逐点不变；stage/output clipping保护通过。不重复延迟、不合成warmup/EOF评分帧。
v63四远端原录音总输出能量变化-0.307896/-0.395145/-0.243643/-0.220370dB；v62对应-0.190175/-0.242068/-0.151495/-0.136759dB。原数据没有独立近端/回声真值，这些不证明ERLE/双讲保真/远端电话听感。生成试听WAV，但本轮没有人工/远端电话听感验收。
五轮交错每项80warmup/2000帧，线程时间，无质量任务并发；后轮Host CALL native/v62/v63中位209.229/240.684/242.354us/帧。v63相对native约+15.83%，相对v62约+0.69%；VOICE范围重叠，不能称资源完全不变或加速。Host与SSC305分别报告，无新ARM运行。
arena308308字节；Host parent额外state31064、每新wrapper64、两个wrapper owner slot16；不把arena当全部实际内存。模型SHA仅绑定v52基础表，独立v62/v63 source/binary绑定实际系数。v63raw/perf二进制文件名含v62是构建模板后缀，实际强度由v63独立header/SHA确定，未冒充v52规范输出。
## 验证与可重放身份
187项Python测试exit0，无跳过；两个wrapper各20000全int32边界ASAN/UBSAN、2instances/第三owner拒绝、CALL/ref-loss/VOICE/Reset/nativeAGC/identityPCM/owner释放PASS。Sanitizer覆盖新wrapper/headers，旧static库内部未重新插桩。
每候选32例恒等original metrics+metadata逐项精确；各1636500个would-change bins证明hook被实际触发。Werror编译、/tmphelp/dry写入false、wrongversion/strength/metadata/cardinality/trajectory负例PASS。
收口新鲜回读74个source/binary绑定、3nativebuild各185source/header、1408个trace binding、2816个输入binding PASS；trace/input为绑定次数，并非去重文件数。父仓和AISpeech diff --check均exit0。
主仓HEAD99b5f958ffefd93c2cf939b0b28f91f48dde9b57，独立AISpeech HEAD9ce7a7f87b4835816e68df7fade6d43ebb3d47a1；既有dirty保留。默认SEVC_CALL_RESIDUAL_CANDIDATE=0，无产品默认/库/设备变更，没有commit/push/部署。
新24来源Microsoft/AEC-Challenge exact6c633d0a9d2a143a0e364899b91b06f127315b18；split SHA026645b46b8a90290f6b79aa7fc3684b94ebce651d83b7216f85a930ebd09e2c；intake SHAc7622c4e542442dbd24d5bfb07dd6ce89ce8bd79b9b697f3734ae44897a973d7。96WAV LFS SHA/size/mono16k16/frame数验证，speaker/sourceclip与328及新组内部均独立。
SELECTION-v64原摘要excluded_ids误沿用常量304；实际评分前assert与immutable intake均328且disjoint验证通过。原摘要保持冻结，SELECTION-v64-ERRATUM单独登记字段纠错；输入、选样和候选参数均未改，不覆盖原记录。
## 证据与继续
REGISTRY-v62-v63-352.json为新完整矩阵；AGGREGATE-v62-328/AGGREGATE-v63-328、RESOURCES-CAPTURE-v62-v63、BUILD-v62/63-development、PLAN-v62/63/v64、SELECTION-v64/ERRATUM均本地受控证据。
不能启用已知双讲失败的native v52标志。tests/README旧304结论是历史范围，应在下一源码阶段补新边界说明；本次Context维护要求出现后不继续改产品源码。
下一步先将v63作为保护/收益基准，对644及高残留/近端目标样本核验逐频NN gain/相位/原生输出与v52修正贡献，冻结可验证的新机制再测试；不继续简单常数扫描。仍需完整目标、ARM性能及实际电话持续听感证据。
User AGENTS要求Execution Policy；当前已要求checkpoint后Host上下文压缩，逻辑goal保持active。累计250M Token/48h沿用，无重置，deadline2026-10-11T14:56:57Z。Provider正文仅脱敏结论与证据身份，不含raw/WAV/bin/trace。
