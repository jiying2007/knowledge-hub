---
id: provider-xcrz-sigmastar-demo-a3664b37ed8cf10fff847628
title: CALL 短时相位特征与失败分层 v12
kind: debug-record
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/archive/provider-xcrz-sigmastar-demo-a3664b37ed8cf10fff847628.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: provider-candidate-archive
  from: provider-policy-sha256:a295759999c3c3c2594752350565bbde6af74808af32b9272604f53a36f82736;operation:a3664b37ed8cf10fff84762838e5973f9bd8c95448288f1b96cf0c3f91a3e224
  source_sha256: 72836e6195071abd379b8597b332ed2e20d9fede5b33bc1031baa333599bc4ce
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
- projects/xcrz-sigmastar-demo/archive/provider-xcrz-sigmastar-demo-a3664b37ed8cf10fff847628.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/archive/provider-xcrz-sigmastar-demo-a3664b37ed8cf10fff847628.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-10-10'
updated_at: '2026-10-10'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-10-10'
manual_validation_pending: true
summary_zh: 'logical_task_open: true completion_claim: false stop_condition: replan shipping_approved: false root_cause_status:
  unknown scope: 本地Host单一候选及透明观察；没有commit/push/部署/设备重启，业务生命周期不变。'
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
subject_ref: &id001
  id: xcrz-sigmastar-demo
  type: project
created_subject_ref: *id001
principal_id: null
provider_operation_id: a3664b37ed8cf10fff84762838e5973f9bd8c95448288f1b96cf0c3f91a3e224
---

# CALL 短时相位特征与失败分层 v12

logical_task_open: true
completion_claim: false
stop_condition: replan
shipping_approved: false
root_cause_status: unknown
scope: 本地Host单一候选及透明观察；没有commit/push/部署/设备重启，业务生命周期不变。

本轮按v11接力建议增加短时带符号相关量，冻结一个256系数表。它在已拟合数据上比v11局部误差
进一步下降1.504%，但完整CALL仍有最差双讲和远端退化，故未采用。开发失败后没有打开独立集，
没有修同一表或扫描参数。新增透明观察确认两类失败：若干样本在NN频谱处已经损失近端，
另有样本NN频谱SI-SDR改善而最终PCM退化。当前不能据此断言设备AEC或AGC根因。

## 冻结设计和信息门槛

X为原生NN对应上一帧post-AES FIFO；E为同帧、同一最后麦克风的AEC removed-echo估计。
AEC进入callback时保存current E，原有完整调用返回后更新previous；NN用previous E与FIFO。
原8×8 gain/ratio格点不变，新增4个短时相关量格点，8×8×4共256系数，Q20 floor0.2..1。
每bin对|X|²、|E|²、Re(X conj(E))做固定alpha=1/8的EMA：
phase=(1+2*cross/(power_x+power_e+1))/2，夹紧[0,1]。
该量含幅度关系，不等于纯相位角或传统平方相干度。只使用设备可得量，未读取clean-near或独立echo真值。
transition/no-reference清全部EMA，quiet/不匹配原生gain输出时清当前bin，Reset清全部状态。
输出改写仍要求stable CALL、refVad/refVadLast及原生gain×FIFO匹配，原AEC/AES/NN状态照常推进。

八个trilinear Q40权重的和恰为2^40；乘积<=2^60，最多7个Q40截断单位补到末权重；
表项固定209715..1048576，最终增益仍在原floor..unity，不用128位整数。
Host phase状态为257×3个double=6168字节，表1024字节；wrapper和训练统计额外占内存。
未做ARM定点移植/CPU资格，不把Host状态规模当作设备实时能力。

训练仅用原24+8例，两者都为已拟合开发数据；保持原scale/ref对齐/CALL512/VOICE256/80静音prewarm。
32观察器全部原指标与默认相同，eligible/native error/target power亦与v11相同。
固定1024步bounded projected gradient，步长1/largest eigenvalue，初值原生gain格点；未扫描参数。
将v11 64系数沿phase复制到256格点，局部误差与旧表rel_tol1e-8一致，证明新基准确实包含旧表。
预设新局部误差至少再下降1%才进入完整链：
old error 3.860436510341288e18；new error 3.8023893976314163e18；
ratio0.9849635883003119，额外下降1.503641%。256格均有观测，projected residual max0.0004344297，
未宣称精确收敛。这是已拟合数据的额外表达/拟合能力，尚未证明未见泛化或相位特征独立因果收益。
冻结模型SHA e45d92e861e5b83b2cba5c0c8d85e608f8afd4c432bbe9b469f75cece793f4d9。

## 完整链结果

| 相对默认基线 dB | 原24例 | 原补充8例 |
|---|---:|---:|
| far ERLE平均/最差 | +2.1165 / +0.476 | +2.157875 / -0.852 |
| DT SI-SDR平均/最差 | +1.165917 / -1.197 | +1.377125 / -1.247 |
| DT target projection平均/最差 | +0.038375 / -0.669 | +0.03975 / -0.599 |
| near-only全部原指标 | 完全相同 | 完全相同 |
| 内部/最终clip | 无增加 | 无增加 |
| 联合门槛 | false | false |

门槛保持far mean>=+0.5/min>=-0.1、near-only/DT SI-SDR min>=-0.1、target min>=-0.2、clip不增加。
DT失败：7/18/56/58；far失败：84。平均收益不能抵消这些逐例退化，生产未采用。
独立24例96轨仍未评分；未进入候选ARM资源、原始录音反事实质量或设备资格。

## 透明频谱观察

模式2编译拒绝TAIL_TRUTH。模式3是同一冻结表的Host观察装置，需要truth frontend，但增益计算不读标签。
32例模式3与模式2全部原指标和predictor统计相同；AEC、AES及NN input的频谱累计量均与训练观察器相同，
NN输出的DT目标窗口/Gram也相同，之后才比较NN频谱SI-SDR、近端MSE和near/echo投影。
这些频谱量排除AGC/OLA，最终PCM的窗口/合成不同；因此仅作分层线索，不能直接归因为AGC。

| fileid | NN近端MSE比值 | NN频谱SI-SDR变化 dB | 最终PCM双讲SI-SDR变化 dB |
|---|---:|---:|---:|
| 7 | 1.150594 | -0.180799 | -0.136 |
| 18 | 0.983399 | +0.368205 | -1.197 |
| 56 | 1.256973 | -1.352331 | -1.247 |
| 58 | 1.108277 | -0.294553 | -0.178 |
| 84 | 0.737707 | +2.060811 | +2.441 |

7/58的echo投影被压低约6.69/6.36dB，同时near投影损失约0.69/0.59dB，NN阶段已有保护不足。
56的near投影下降0.494dB而echo投影增加1.608dB，不能把最终损失全部归给后链。
18的NN频谱指标改善仍无法保证最终质量；其echo投影增加0.838dB，near投影下降0.171dB。
下一步需匹配同一时域窗口再区分IFFT/AGC/OLA，不以当前频谱比较直接宣布后链责任。
84双讲改善而远端退化，继续要求分场景及最差指标，而不是只看平均或总体MSE。

归因工具的重复调用负控制发现浅拷贝会修改输入probe元数据，已改为独立dict副本；
上游/input/model/metric/truth变更及重复调用控制均通过。修复不改变本轮真实数据归因JSON，
final版与初版SHA相同；空输出/精确投影不编造有限SI-SDR。

## 新鲜验证与边界

- 60项Python检查通过，无skip；新phase维度/EMA/数值及归因身份/退化负控制，旧工具兼容通过。
- run-tail-phase-contracts：模式1/2/3 ASanUBSan通过，20k随机整数边界、独立EMA时间展开、
  同相/反相/正交、echo FIFO、无ref PCM、Reset/VOICE及错误历史控制均覆盖。
- 模式2+truth、模式3无truth及64/256表混用三个编译负控制均拒绝。
- O2/sanitized完整24对48records完全相同；vendor库没有sanitizer插桩。
- 当前推理二进制与评分前冻结的二进制逐字节相同，最后源码重编重新绑定，无额外质量调参。
- 旧v11预测器两模式、oracle四模式、ablation四模式、truth FFT121.307dB均通过。
- 旧v11及新v12模型非仓库dry-run重算SHA均相同，非仓库help/归因dry-run通过。
- 默认Host69编译单元、179来源项新鲜构建；164个非tests来源项与v11相同，默认so/a逐字节相同。
- 透明stage二进制与v11相同，绑定既有16原始录音identity；没有宣称新设备CALL数据或无真值质量分。
- 父仓/aispeech子仓git diff --check通过；旧dirty、预编译库删除、raw录音和已冻结证据保留。

上述是算法装置和Host证据；没有电话听感、设备部署身份或ARM实时证据，CALL持续回声仍为needs-fix。

## 证据索引

| 文件 | SHA256 |
|---|---|
| fresh-default-v12-bound/build.json | 6e61bd3c2238c6af1ba3edf3a62d5bda0c38156579d40a55d3010efb6d7fc34b |
| 默认so | 1f0dbcbda5db2f377d8eba1b0a161c7f6ccdfb4a7513a1def39dd61f892a73fe |
| 默认a | cc9561d29c93d00948eb90c1a59b0a0f28f8d59a01ca3895107c798a9a807532 |
| model.json | e45d92e861e5b83b2cba5c0c8d85e608f8afd4c432bbe9b469f75cece793f4d9 |
| model.h | 54daa4889fada80e77c7f3296716cbf13478c9d67e910a4a47fd85af2ecbf839 |
| training24 | 04b701780ec6b3b067fedf480e1d7d208ef93b8d5d53c849536b80d049f516ac |
| training8 | 45a6e51ecbf474e926ba52c8a97f2c4acfe0d9b6599b737539420fb64c2285ed |
| candidate24 | 0ad80dc700227314879dac307f09c3b53f0cac5487a5feb2f416fc7c939cf6b7 |
| candidate8 | 7d0096d0a2cd84073596fbe8d8b60f1d7f4917f5cb09aebcb79853ceafb71bfa |
| qualified24 | 87f3b1ded7a388fb2ad218423ef631f773861489e2afd5f0d4c8db4d91180966 |
| qualified8 | 5c8ecb2db733f50ebc4dff7cf938f007fdcf49c302c4508fed60c7a3b634fd33 |
| observed24 | 67a443ec72d7235a0e1fe72833de178d2f36aad361a1df790bae2ea0b5c5b086 |
| observed8 | ebe2ff47b98bfa11652517d0782a24245cc34d9cc2ed577dcd4403b932551822 |
| attribution24-final | 3fb04611ff48b6b4c73670894161007f1e09a156883f14bd0e6001c63a72e74b |
| attribution8-final | d2e323807281176154e6aa44da836904aa88516d0555f68fc5558627ee64fb68 |
| candidate24-sanitized | 9238c4a1ba782ed53e91dbf5faca2cb66288da345a13073b896f06a8935ea2ea |
| inference-bound binary | b0a942c56fbd5e62c132a4905708d8e5be390eea04d16ac5c1a923cae8b65dc1 |

代码身份：phase_feature.h 3d6ec6458e3e881d5a90b4ad0128e3f257a551a472a589ab97bece1cc021ee0a；
predictor_probe.h 0dfc5df94b462ebdb1ad3a7c7cf61b96b2a59d99f23a77a71740d539112dfbd8；
predictor_regression.c 6b1a27ae07f09ef479ad23403310640fc3cc1fec88898cf693d50ab718e9e364；
ablation_adapter.h da80eb00c42a9de992d512e860d1241dd657b15992673da5ff1084a77911fa92；
fit/check工具 69ab5fae0fe15cdf39e1893717dc93b38731cf2695ae33845afa5747cb4d28cb；
attribution工具 a86f75c3e34ed10841dc38e3cd65e2d08e25a5c5e598588cf39593da8b79cee3。

## 重排假设及复用边界

v11/v12连续两个有限映射未能保护最差双讲，停止继续同类EMA/grid/floor扫描。
下一阶段优先把训练目标转向逐例近端失真保护，且先匹配file18的时域窗口，
分开检查NN-IFFT、AGC和OLA；先做装置与因果对照，再决定新候选，不重复已否决全局AGC去增益。
reusable_pattern: 因果EMA+嵌套模型控制+无真值推理隔离+透明归因。
promotion_candidate: false
next_task_friction_reduced: 已分离两类失败并固定输入/model及已有passing控制。
reduced_by: 可复跑工具和身份负控制，避免再次把局部MSE或不同窗口指标当最终收益。
reduction_evidence: 32透明观察identity、60检查和归因表。
do_not_promote_reason: 未通过完整链联合门槛、独立集/ARM/设备资格缺失。
owner_review: 未进行。
rollback_path: 默认生产链未选候选；保留不可变v11与新v12证据。
verification_evidence: 本文证据索引及HANDOFF。

主观功能未由独立听感验证，不作产品完成/提交/发布声明。Runtime目标call-residual-protected未满足，
继续active/open_items=1；本轮仅Host研究阶段收口，后续重排而非假装设备回声完成。
