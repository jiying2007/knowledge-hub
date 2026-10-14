---
id: provider-xcrz-sigmastar-demo-9ce2d728807eff6bc0ff07ec
title: CALL 选择性频谱增益机制验证 v10
kind: debug-record
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/archive/provider-xcrz-sigmastar-demo-9ce2d728807eff6bc0ff07ec.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: provider-candidate-archive
  from: provider-policy-sha256:a295759999c3c3c2594752350565bbde6af74808af32b9272604f53a36f82736;operation:9ce2d728807eff6bc0ff07ec53a2f941fbc07992ec05dd8fed34b3e9d85ab72d
  source_sha256: 39f7c2448fd911590600dd8c301ee61c1783cbdc5f8ca96f6664381480b2174f
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
- projects/xcrz-sigmastar-demo/archive/provider-xcrz-sigmastar-demo-9ce2d728807eff6bc0ff07ec.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/archive/provider-xcrz-sigmastar-demo-9ce2d728807eff6bc0ff07ec.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-10-10'
updated_at: '2026-10-10'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-10-10'
manual_validation_pending: true
summary_zh: 'date: 2026-10-10 status: reviewing decision: Host理想机制有联合收益，继续研究无真值判据。 completion_claim: false shipping_approved:
  false product_candidate: none goal_statement: 改善远端持续自回声，保护近端双讲及既有reader/订阅/lease。'
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
subject_ref: &id001
  id: xcrz-sigmastar-demo
  type: project
created_subject_ref: *id001
principal_id: null
provider_operation_id: 9ce2d728807eff6bc0ff07ec53a2f941fbc07992ec05dd8fed34b3e9d85ab72d
---

# CALL 选择性频谱增益机制验证 v10

date: 2026-10-10
status: reviewing
decision: Host理想机制有联合收益，继续研究无真值判据。
completion_claim: false
shipping_approved: false
product_candidate: none
goal_statement: 改善远端持续自回声，保护近端双讲及既有reader/订阅/lease。

## 本轮结论

带原生参考VAD边界保护的理想频谱增益，在24例开发集和额外8例观察集全部取得远端和双讲改善。
32例独立near-only的全部原指标完全不变，内部及最终削顶不增加。
这证明在当前原生AEC/AES及CALL后链中，选择性增益存在可利用的改善空间。
它仍使用clean-near真值，不是设备算法，没有直接接入产品，也未证明设备持续自回声已经解决。

不带参考保护的第一轮同样改善全部远端，但file18双讲下降1.578dB、near-only最差下降2.738dB；
局部频谱误差下降不能替代完整链质量。增加保护只使用原生当前/上一帧refVad，没有扫描阈值。
设备端无真值判据、独立holdout、ARM资源、最终制品及电话听感仍待完成。

## 冻结契约与实现

主链AEC/AES、NN特征/VAD/状态继续原流程，实验只替换NN输出频谱，完整后链正常运行。
X是NN旋转前的上一帧FIFO，N是相同原生前端提取的上一帧clean-near FFT。
每频点实数增益为 Re(X*conj(N))/|X|²，夹紧至原生floor0.2..1，并量化为Q20。
这只是局部连续实数约束MSE解；定点舍入有界，不是完整链SI-SDR最优解。

Host适配器必须同时启用TAIL_TRUTH、oracle模式1、ablation模式0，且模型右上下文1、Q20、
双麦/单参考、257bins、BF0。干净目标来自额外分析实例，不改变主实例输入或AEC权重。
主评分和独立near-only实例都真实执行该机制；guard模式的near-only全部因refVad关闭而保留默认输出。

reference-guard要求原生refVad和refVadLast都激活，覆盖当前/上一帧参考状态；
稳定CALL且ready、非switching/suppress才替换。VOICE、预热、无参考与参考边界走原路径。
真值仅用于Host增益上限，不进入该reference gate或设备代码。

冻结24例四轨、near_scale、参考峰值对齐、80帧静音预热和CALL512点评分，不填充EOF。
额外8例仅取本地已有且不在24例中的全部fileid：56/58/61/69/71/76/84/117；
scale来自原meta.csv，全部为非线性噪声组，未按结果选择。
这8例的历史暴露未知，只是额外观察集；32例都不能声明正式挑战验证或未见最终holdout。

## 完整CALL结果

以下为相同输入候选相对默认基线变化，正值表示改善：

| 实验 / 数据 | far ERLE均值 / 最差 | 双讲SI-SDR均值 / 最差 | near-only SI-SDR最差 | 双讲目标投影均值 / 最差 |
|---|---:|---:|---:|---:|
| 无guard理想增益，24例 | +10.122042 / +3.674 | +5.649208 / -1.578 | -2.738 | +1.679625 / +0.281 |
| reference-guard，24例 | +9.497958 / +4.779 | +4.706542 / +0.267 | 0 | +1.254833 / +0.368 |
| 同一reference-guard，额外8例 | +9.554500 / +2.503 | +4.862000 / +3.250 | 0 | +1.545500 / +0.569 |

guard模式32例的所有explicit_near原指标与默认完全相同，而非只比较表中的SI-SDR。
最终clipped、IFFT、overlap和output_gain及其near-only计数逐样本核对，无增加。
预声明联合门槛保持：far均值≥+0.5dB/min≥-0.1；near-only/DT SI-SDR min≥-0.1；
目标投影min≥-0.2；内部及最终削顶不增加。guard模式两个集合均通过，输出shipping_approved=false。

file18：加guard后双讲从-1.578转为+0.267dB；这是完整策略差异，不能据此断言AGC根因。
file27：guard后far改善7.170dB、双讲改善5.944dB、目标投影提高2.634dB。
当前收益使用干净近端信息，不应预期无真值估计器能直接达到同样幅度。

## 负结果与因果边界

无guard实验24例局部频谱误差都下降，误差比为0.063846..0.296304，但仍有完整链退化，
因此拒绝以局部MSE单指标驱动产品优化。
远端在原floor下已全部显著改善，没有证据支持取消floor；模式2仅跑数学/装置控制，
未运行floor=0质量实验，也没有扫描floor或VAD阈值。

原生AGC有动态压缩、VAD控制和增益平滑；T2_gain=+6dB不是恒定输出增益。
它可能改变局部频谱误差与完整链质量的关系，但本轮未做独立AGC因果替换，不能称AGC为根因。
保持当前NN计算和原生AGC，让完整链直接决定实验是否有收益。

## 新鲜验证与制品

| 检查 | 结果 | 层级 |
|---|---|---|
| Oracle identity，完整24对 | 全部原指标完全相同，混合及near-only均真实计算oracle统计 | Host装置 |
| 原floor/zero-floor/identity/guard四模式ASan/UBSan | 独立上一帧源/目标、无参考、Reset及PCM通过；各两轮800feeds | Host契约 |
| 数学控制 | 非正交目标、负投影、unity、零输入、INT32边界；20000随机×2floor对独立解析解和粗网格 | Host数学 |
| 既有ablation四模式及真值控制 | 全部通过，FFT线性121.307dB | Host回归 |
| Python全套 | 46项通过，无skip；6项新oracle身份/质量/削顶/异常负控制 | 工具/传输 |
| guard O2/ASan完整24对 | 48行records完全相同，含频谱和oracle累计量 | Host交叉核验 |
| 非仓库cwd help/dry-run | 退出0，qualified=true，writes=false | CLI |
| fresh-default-v10-bound | 69单元、177源码头身份；92个算法源码头与v9相同 | 默认源码/Host |
| 默认so/a | 与v9逐字节相同 | 默认Host制品 |
| 当前透明stage探针 | 与v9二进制逐字节相同，绑定既有16录音PCM identity证据 | 原始重放身份 |
| 最后缩进调整后guard重编 | 与v10-final评价器逐字节相同 | 实验源码身份 |
| git diff --check | 退出0 | 源码空白 |

ASan/UBSan只插桩测试代码，vendor静态库没有插桩。
默认SEVC_COMPLETE_RESET=0保留overlap；改变输出的诊断模式Reset后前两hop可受旧输出历史影响，
之后VOICE必须完全一致，identity仍比较每一帧。不更改生产Reset语义。
分析实例额外使用原生arena，观察器另有Host堆分配，不计入产品MemSize；它们不是ARM资源候选。

本轮只改tests及tools内Host诊断、评价器和数据split元信息。
默认CALL1tap/MU0.4、VOICE2taps/MU0.8、BF0及Sensor/API/proto和reader/订阅/lease不变。
已有dirty、库变更及删除现场均保留；无commit/push/部署/重启。

默认so SHA256：1f0dbcbda5db2f377d8eba1b0a161c7f6ccdfb4a7513a1def39dd61f892a73fe。
默认a SHA256：cc9561d29c93d00948eb90c1a59b0a0f28f8d59a01ca3895107c798a9a807532。

| 证据 | SHA256 |
|---|---|
| fresh-default-v10-bound/build.json | 53b39544416c8997e3a61ef31e1d63fdc590022cf0737eb35ef673dfc2476834 |
| tail-oracle-identity24-final-v10.json | 7abe6aaaf8cd29a303a20d1947703e824c78a636bf7f0710cbcabf799ae25378 |
| tail-oracle-floor24-final-v10.json | 02005656fcbc5661c60a8ebf45bd67d6ad6ac3ef4961147b583c174d20b76dd6 |
| tail-oracle-guard24-final-v10.json | 45a8a20a27d866517ea89f1410f5fa7771ad7eb9fa2d7532b51028ee07bf4c2a |
| tail-oracle-guard-extra8-final-v10.json | c471e0c133354e15471e1dc3d9f8a158599fe18e81197f9037759c106edef789 |
| tail-oracle-guard24-sanitized-v10.json | bebce86480d5898cd0ba773edea092e0b175e2dbde5f2b35b60bfafaf36de8b9 |
| tail-oracle-qualified-v10.json | 1808bfa0531a60ba958c6539d967c96d6bbc8cb3ff1ca42705922de6ddb83bd7 |
| supplemental-eight-v1.csv | 4302542ff66039de7e01c9e56914a84e5b1f8603fbf89c456b647564ece433a6 |

24例split SHA256继续为4274aeeabbc0a2de54f0afcda789d821468f5558b3a7bf5a10f8f9a799a395bb。
配对JSON绑定每轨input hash、实际baseline/candidate二进制及split。
质量门禁JSON绑定identity/candidate/supplemental三个输入文件hash，不替代原记录。

| 测试实现 | SHA256 |
|---|---|
| tests/sevc_tail_ablation_adapter.h | 41b8a7075f1db72121f8ae461ec65d8cab392e9c753519db89cb97e784e7077b |
| tests/sevc_tail_oracle_gain.h | 6bea3235061babe5a6e5954ddc90b36170ff53a15277594801e0ebfe2f3bf964 |
| tests/sevc_tail_oracle_regression.c | 089431a44be88458bf6c7dbae41f6c98a21ae4c461e2425c41d6d81c1bbbeaf8 |
| tests/sevc_aec_challenge_evaluator.c | dbf5d31be05eed7142045cac8ef071fc3edba482f03331f7e897344de172a3ca |
| tools/codex_assets/tail_oracle_metrics.py | 95ef03de8adcbec573567d2060abc4c7cdd7973bd222c1826d95c45078892a84 |
| tests/test_tail_oracle_metrics.py | 80f4203c4594645e72446263b89b15e7809d695c61ed4478c9be28342395c6c4 |

复跑：isolated_build新目录；make -C tests -o host-lib HOST_LIB=<库> run-tail-oracle-contracts；
公共评价器使用固定库宏和CALL mode1、-include适配器、TAIL_TRUTH1、TAIL_ORACLE1。
identity另加TAIL_ORACLE_IDENTITY1；guard另加TAIL_ORACLE_REF_GUARD1。
同一supervised_compare分别使用evaluation-split-v1.csv和supplemental-eight-v1.csv；
tail_oracle_metrics绑定identity、guard和supplemental后验证联合门槛。
并行作业只读同一库/二进制，各自新JSON；无设备或共享可写资源。

## 下一阶段与完成边界

milestone_close: 当前Host机制验证已完成。
logical_task_open: true
open_items: 无真值选择性增益估计器、独立holdout、ARM资源、设备制品和电话听感。
replan_reason: 从理想真值机制转入可部署判据，需要先验证设备可得量的辨识能力。
先保留原生reference边界保护，观察NN/AES及AEC残差相关的设备可得频谱量与理想增益的关系；
另行冻结独立数据后才训练或设定判据。不能把当前32例拟合又作为最终验收，也不能直接使用NN VAD当可靠双讲判据。
不重复v2-v9已失败全局增益、权重冻结、AGC去增益、MIC/REF延迟或MDF整链替换。

Knowledge归档只含可复用机制、负结果、哈希和边界，不含raw音频/日志/会话。
owner_review: pending
promotion_candidate: none
do_not_promote_reason: 仍依赖设备不可得真值，缺无真值估计器/独立验证/ARM/HIL。
rollback_path: Host宏默认关闭；保留不可变v9及本轮配对证据，不改生产默认。
Runtime仅检查本地conformance；call-residual-protected生产目标仍未满足，不清空open_items。

