---
id: provider-xcrz-sigmastar-demo-44d6470b6db5ac82cf2340a8
title: CALL 无真值增益预测完整链验证 v11
kind: debug-record
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/archive/provider-xcrz-sigmastar-demo-44d6470b6db5ac82cf2340a8.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: provider-candidate-archive
  from: provider-policy-sha256:a295759999c3c3c2594752350565bbde6af74808af32b9272604f53a36f82736;operation:44d6470b6db5ac82cf2340a8e8bd2e644a44a6ae9d06e8a50e003c7989aeccbd
  source_sha256: 1abc5c3d008e15d4e347c57505b886d3c4ea8199c265e380a7071ba3e5341b16
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
- projects/xcrz-sigmastar-demo/archive/provider-xcrz-sigmastar-demo-44d6470b6db5ac82cf2340a8.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/archive/provider-xcrz-sigmastar-demo-44d6470b6db5ac82cf2340a8.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-10-10'
updated_at: '2026-10-10'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-10-10'
manual_validation_pending: true
summary_zh: 'logical_task_open: true completion_claim: false stop_condition: replan shipping_approved: false scope: 本地Host算法、公开四轨数据、可回滚测试装置；没有提交、推送、部署或设备重启。'
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
subject_ref: &id001
  id: xcrz-sigmastar-demo
  type: project
created_subject_ref: *id001
principal_id: null
provider_operation_id: 44d6470b6db5ac82cf2340a8e8bd2e644a44a6ae9d06e8a50e003c7989aeccbd
---

# CALL 无真值增益预测完整链验证 v11

logical_task_open: true
completion_claim: false
stop_condition: replan
shipping_approved: false
scope: 本地Host算法、公开四轨数据、可回滚测试装置；没有提交、推送、部署或设备重启。

本轮将v10理想增益机制推进到设备可得量：只读原生NN增益和上一帧post-AES输入/removed-echo功率比，
拟合64系数Q20表。推理编译不包含干净近端标签或训练Gram。
32例已用开发数据的far ERLE平均提升2.290125dB、双讲SI-SDR平均提升1.157719dB，
但file84远端退化1.230dB、file56双讲退化1.386dB，联合门槛失败，因此未采用。
当前只确认这个静态双特征候选不足以安全进入默认链路，不确认设备持续回声根因或已修复。

## 训练前冻结独立数据

来源固定Microsoft AEC-Challenge revision 6c633d0a9d2a143a0e364899b91b06f127315b18；
官方四轨/nearend_scale说明：
https://raw.githubusercontent.com/microsoft/AEC-Challenge/6c633d0a9d2a143a0e364899b91b06f127315b18/datasets/synthetic/README.md
本地meta SHA 6b867aa68f510e4bafc9ffa05202930ffc1bb54bb0cffe66aa1ec3bcc606f3e5，已与pinned远端metadata核对。
按fileid排序，>=200，四个linear/nonlinear×clean/noisy组各6例，每组SER负/非负各3；
排除当前32例所有near/far speaker与source clip，验证集内部speaker跨角色不复用。
选择只使用metadata，未根据音频评分选择；它是本次冻结的本地独立集，不代表正式Challenge成绩或真人产品资格。

ID：202,203,206,210,212,215,220,222,225,231,235,236,247,250,263,277,306,313,321,337,367,375,380,400。
96轨均校验Git LFS OID/size、WAV mono PCM16/16k、完整PCM长度、四轨等长；最终又核96轨SHA。
intake.json SHA f1fcdcb76b2c5486a6a44ccd5003ef40cb007c24a92b16da52958a2799a21bab；
holdout-v11.csv SHA f7429c362fdaee14a2be5c47da789500672e14c5e6f3cd552188ce6045254b34。
开发门槛失败后独立集没有运行baseline/candidate评分，留待新设计冻结后使用。
HTTPS只读两个官方GitHub内容host，无凭据和远端写，不执行下载内容；单轨16MiB、1m采样上限、4worker。
raw WAV和制品只保留本地证据cache；本轮发现父仓尚未忽略该目录，已追加精确ignore并用check-ignore确认。

## 单一候选与边界

X是NN输出对应的上一帧post-AES FIFO，E是同帧AEC从最后一个麦克风移除的回声估计。
AEC进入callback时快照E_current，原有完整回调返回后才更新E_previous；NN callback用E_previous。
两特征为native NN gain与|X|²/(|X|²+|E|²+1)，8×8 bilinear，64个系数。
整数特征使用共同右移限幅，四个basis权重和恰为2^40，Q20 gain固定[209715,1048576]。
仅stable CALL且refVad/refVadLast均成立、原NN输出确实等于gain×FIFO时替换NN输出；
transition/no-ref/quiet及无法匹配的原生旁路保持原输出；AEC/AES/NN状态照常推进。
20个启动转换NN回调单独计transition_skipped，不误算为原生参考guard帧。

训练只使用原24例加原补充8例，后二者在本轮同属已拟合开发数据，不能称为验证集。
两个split SHA为4274aeeabbc0a2de54f0afcda789d821468f5558b3a7bf5a10f8f9a799a395bb与
4302542ff66039de7e01c9e56914a84e5b1f8603fbf89c456b647564ece433a6。
能量加权Gram/RHS，初值identity格点，固定1024步projected gradient，步长1/largest eigenvalue；
不扫描floor、VAD、grid、迭代数或验证集；模型冻结后才评分开发完整链。
64格均有观测，projected gradient residual max 0.0001170901，未宣称精确收敛。
局部error ratio 0.814218；这个18.6%的局部误差下降不能替代最终SI-SDR与双讲保护。
模式1观察器在32组配对中全部原指标完全相同；模式2编译时拒绝TAIL_TRUTH，没有clean-near或Gram存储。

## 完整CALL结果

CALL512/VOICE256延迟、既定reference peak对齐、nearend_scale、80静音prewarm、原生AGC和OLA均保持。
没有把原始VOICE录音假称为设备CALL处理数据，也没有替无真值录音构造oracle质量分数。

| 相对同一默认基线 | 原24例 | 原补充8例 |
|---|---:|---:|
| far ERLE平均/最差 dB | +2.259958 / +0.302 | +2.380625 / -1.230 |
| DT SI-SDR平均/最差 dB | +1.118 / -0.464 | +1.276875 / -1.386 |
| DT target projection平均/最差 dB | +0.021292 / -0.661 | +0.014375 / -0.629 |
| near-only全部原指标 | 完全相同 | 完全相同 |
| 内部/最终削顶 | 无增加 | 无增加 |
| 联合门槛 | false | false |

预设far mean>=+0.5/min>=-0.1；near-only及DT SI-SDR min>=-0.1；target min>=-0.2；clip不增加。
24例DT退化超过门槛：7、18；8例：56、58。far退化超过门槛：84。
target退化超过门槛：24例7/16/18/21/43/46/48/63/99，8例56/58/71。
失败后没有修模型或打开holdout，生产默认没有选这个表；没有进行候选ARM资源或声学HIL。

## 新鲜验证

- 54项Python检查全部通过，无skip：intake四项、fit/gate四项、既有传输/身份/负控制。
- predictor mode1/2 ASan+UBSan：20k定点basis边界、独立echo/FIFO时序、无ref PCM、Reset/VOICE及错误历史负控制通过。
- 推理启用TAIL_TRUTH的编译负控制按预期拒绝。
- O2/sanitized完整24对的48行records完全相同，含模型/计数/原指标；vendor库不插桩。
- 共享适配器既有oracle四模式、ablation四模式、truth FFT控制通过，FFT线性121.307dB。
- 69单元默认Host新构建，178源码头项；164个非tests来源项与v10完全相同，so/a逐字节相同。
- 当前透明stage二进制与v10相同，继续绑定既有16录音identity；没有虚构重复新跑或新的设备CALL质量验证。
- tests/Makefile新增run-tail-predictor-contracts，显式传入冻结模型目录；工具非仓库help/dry-run通过。
- 父仓与独立aispeech仓git diff --check通过；已有dirty/库删除/原始录音保留。

## 证据身份

| 文件 | SHA256 |
|---|---|
| fresh-default-v11-bound/build.json | fb7512941c1b7ccbd7156f3a0eb3fa2c39362cc48e124463fc178f720e8d1428 |
| 默认libsevc_replay.so | 1f0dbcbda5db2f377d8eba1b0a161c7f6ccdfb4a7513a1def39dd61f892a73fe |
| 默认libaispeech.a | cc9561d29c93d00948eb90c1a59b0a0f28f8d59a01ca3895107c798a9a807532 |
| tail-predictor-model-v11/model.json | 098d6c0dc80b5469e72216da4f65efdf64321e3445d5187d138d1645e8b97934 |
| 生成model.h | 38f2bfd13ecb292c213255d60927f7461c72c3575402de093d3a4e3228ee9442 |
| tail-predictor-training24-final-v11.json | 71fa3a6395524763b2073c532bf446ae57524b0db0970bafec120dc5b8f92771 |
| tail-predictor-training8-final-v11.json | 722df3c112d6f51b356a5b74eff4445a9203f09eb440a59150ae85b94b7d7c0d |
| tail-predictor-candidate24-v11.json | 0a0bf5c846633b7bc890e88d9cb8d6e06d81af528c9e57e741f1fa2129acd9fe |
| tail-predictor-candidate8-v11.json | a3d8a72a2a4b3cc4f84750aec1da69d8a66c5c4a0dbda05a9ec8c998ab0af42f |
| tail-predictor-candidate24-sanitized-v11.json | e5d15461322c2ba7d3f8bcdfcbd196d1215fbb682aafe045fa21d53bcd18272b |
| tail-predictor-qualified24-final-v11.json | 79b551cef8914783ad310ae3dfdb30c6cb63d9fa5539a10f9ee086b50ee8925f |
| tail-predictor-qualified8-final-v11.json | 5b43c9b5ce28e76e111d84386591df7feb581a7bf6db6454664b1b2bfce59699 |
| inference binary | 743cacede03857daf11efaf34a256f77bf30f51a75c83c1a2ff398e1ea72d3c0 |
| training binary | 8e7be6ce092ee530eeda3ffb8d0c96623180055448a6fd4aaffc6f312489c27e |
| transparent stage binary | a7a52bd65e3ce791e8e9d4493d739d6119a264afabc401af01166f2d7a3a54ab |

代码绑定：predictor_probe.h 3e16bba070b8c3b33a9441f1e901c28b2f65e326b4e17acb49494cbcb11c5800；
predictor_regression.c 8518001f3abbff9c4a43a9b8acb56442ebd220b58065d4bf0e3abb8729527428；
tail_ablation_adapter.h 811be0638822334d8e368b8428a8c1b3827139fa494f21c42afbe6e6d3d47205；
challenge_evaluator.c acb4f10c77c23724cd08a2b213d3767a1599d192a65c58db9cf29ffeb48d53cc；
aec_holdout_intake.py 340b8d27fdb0439d7984d24faaaf60fda1d44e8df627b5924898b62a121fe28f。
fit/gate工具及测试最新身份由HANDOFF绑定，不把初期未通过计数合同/错误tail宏的输出作为接受证据。

## 下一阶段

v10上限仍提示按频点保护近端有收益，v11说明这张静态双特征表即使已拟合32例也不足。
下一步先核实时间/相位相关信息能否区分需要保护的近端频点和残余回声，再冻结一个新候选；
需要独立验收且最差双讲保护通过才能扩展ARM资源/设备身份/听感。上述解释是待验证假设，
不是已证明的AEC/AGC根因，不直接盲调NN VAD、全局增益或把truth投入设备。
reader/订阅/lease/proto及Sensor/API业务切换保持既有契约；短暂断流授权不扩大为业务变更。
Runtime目标call-residual-protected未满足，继续active/open_items=1；本轮仅Host研究阶段收口。
