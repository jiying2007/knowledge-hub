---
id: provider-xcrz-sigmastar-demo-572f16a62b72085df28cb410
title: CALL 尾链单模块归因与目标投影 v9
kind: debug-record
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/archive/provider-xcrz-sigmastar-demo-572f16a62b72085df28cb410.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: provider-candidate-archive
  from: provider-policy-sha256:a295759999c3c3c2594752350565bbde6af74808af32b9272604f53a36f82736;operation:572f16a62b72085df28cb410618671560db7cd4be187d5f8d10bb437e725215b
  source_sha256: 9e56e67d74dd7d564823fb84d5a1ed61ce57777551f4b7c0b90393d42a87c1b3
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
- projects/xcrz-sigmastar-demo/archive/provider-xcrz-sigmastar-demo-572f16a62b72085df28cb410.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/archive/provider-xcrz-sigmastar-demo-572f16a62b72085df28cb410.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-10-10'
updated_at: '2026-10-10'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-10-10'
manual_validation_pending: true
summary_zh: 'date: 2026-10-10 status: reviewing decision: replan completion_claim: false product_candidate: none goal: 改善远端持续自回声，同时保护近端双讲与上层音频生命周期。'
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
subject_ref: &id001
  id: xcrz-sigmastar-demo
  type: project
created_subject_ref: *id001
principal_id: null
provider_operation_id: 572f16a62b72085df28cb410618671560db7cd4be187d5f8d10bb437e725215b
---

# CALL 尾链单模块归因与目标投影 v9

date: 2026-10-10
status: reviewing
decision: replan
completion_claim: false
product_candidate: none
goal: 改善远端持续自回声，同时保护近端双讲与上层音频生命周期。

## 结论与边界

本轮完成 AES、NN 单模块输出归因和一个固定增益形状候选的完整24对比较。
三项全局改写均未通过预先声明的门槛，没有接入生产算法。
进一步建立同一原生前端的 clean-near/clean-echo 频谱观察，量化了 NN 的回声抑制和近端损失。
设备持续自回声仍未闭环，Host 投影与公共测试不替代 ARM 资源、最终设备制品身份或电话听感。

保持默认 CALL 1 tap / MU0.4、VOICE 2 taps / MU0.8，BF=0。
本轮没有更改 Sensor/API、reader/订阅/lease、proto、通道业务语义或生产参数。
独立 aispeech 既有 dirty 保留；无 commit/push、设备部署、重启或清理。

## 装置与冻结契约

- Host 同步适配器仅经测试编译的 -include 使用。模式0透明；模式1把 AES 输出替换为原地改写前的最后麦克风 AEC 残差；模式2恢复 NN 上一帧 FIFO；模式3测试固定形状。
- 模块特征、VAD、状态仍按原流程推进。只有 processing/active/desired 都是 CALL、ready 且非 switching/suppress 才改写；退出前恢复三个原生回调。
- 模式3为 Gnew=G+(G-floor)*(1-G)，floor0.2/unity端点固定，无参数扫描。只改写逐点匹配原始 gain*FIFO 的频点，保护 silence/quiet bypass。
- 原生模块功率统计发生在替换之前；改写候选的原生统计不能代表替换后功率。
- 冻结24对、四轨哈希、near_scale、参考峰值延迟和 CALL512对齐。80帧静音预热；不填充 EOF 评分。
- 公共 split SHA256：4274aeeabbc0a2de54f0afcda789d821468f5558b3a7bf5a10f8f9a799a395bb。
- 设备原始16录音均为 VOICE，无独立 clean-near，不补充纯回声或近端保真结论；透明模式仅证明实际库 PCM 不变。

预声明门槛：远端改善均值至少+0.5dB、最差≥-0.1dB；near-only和双讲SI-SDR最差≥-0.1dB；
近端目标投影最差≥-0.2dB，最终及内部削顶不得增加。未通过不扩大原始录音候选质量回归。

## 完整 CALL 配对负结果

表中是候选相对同输入默认基线的差值；正值表示该指标提高。
近端目标投影提高仅表示目标系数更大，不等同于语音更清晰。

| 实验 | 远端 ERLE均值 | near-only SI-SDR均值 | 双讲 SI-SDR均值 / 最差 | 双讲目标投影均值 / 最差 |
|---|---:|---:|---:|---:|
| AES unity | -2.529208 | 0 | -1.347667 / -2.801 | +0.231750 / -0.548 |
| NN unity | -0.479500 | +2.103167 | +1.221042 / -1.824 | +1.636083 / +0.201 |
| 固定 NN 形状 | -0.244458 | +0.227792 | +0.043583 / -0.473 | +0.603708 / +0.187 |

AES unity 的24例远端全部变差；固定形状的24例远端也全部变差。
NN unity 的部分近端指标有收益，但远端均值下降、最差双讲退化，不能全局取消 NN。
各实验最终 clipped 差值均为0；这不能替代质量资格。

## 同窗频谱真值投影

公共评价器另启动一个仅分析的原生前端，把 clean-echo 与按冻结 scale 舍入后的 clean-near
分别输入两个麦克风，ref为0，只读取增益前的原生 pMicBins。
原生 FFT 分解控制信噪比121.307dB，验证同一前端的混合频谱近似两目标频谱之和。

AES输入/输出只用其实际处理的相同帧；NN输入/输出均对齐上一帧。
两 hop 场景切换进入 unknown。双目标2x2 Gram投影去除近端与echo相关项；
缺失目标、高相关目标、输入输出窗口不一致或观察器改变默认指标时拒绝评分。
这些结果排除了 AGC 与 overlap，属于目标线性投影，不是声学 ERLE；
输出中与两个目标不相关的残差单独记录，不能把投影衰减当成全部残余回声消除。

| 模块和阶段 | 近端投影变化均值 | 回声投影变化均值 | 解释 |
|---|---:|---:|---|
| AES远端单讲，24例 | 无近端目标 | -3.954285dB | 全部回声投影降低 |
| NN远端单讲，24例 | 无近端目标 | -2.785927dB | 全部回声投影降低 |
| AES双讲，24例 | -0.425463dB | 不用均值作稳定抑制结论 | 有极小/符号抵消系数 |
| NN双讲，24例 | -2.118526dB | -5.059838dB | 24例两个目标均衰减 |

fileid27双讲，AES匹配窗115帧：近端-0.600603dB、echo-1.980453dB。
NN匹配窗165帧：近端-5.475345dB、echo-8.053679dB。
NN改善了该窗 echo/near 投影比例约2.578334dB，同时造成明显近端衰减，不能把NN直接关闭。

AES fileid0 的echo投影从-0.0011514到+0.0074858，dB绝对值比显示+16.260159dB，
但系数极小且发生符号抵消；这不证明总回声功率被放大16dB。
所有绝对系数、残差和输入目标相关性均保留在JSON，不据这一投影比值作算法缺陷判断。

## 新鲜验证

| 检查 | 结果 | 证据层级 |
|---|---|---|
| 模式0/1/2/3实际库契约，ASan/UBSan测试代码 | 4模式通过，各3轮CALL/VOICE/Reset、900feeds；独立FIFO、无参考及非法回调负控制 | Host装置 |
| 固定形状Q20全域 | 835862个增益值，范围/单调/端点通过 | Host数学 |
| 原生前端目标分解、NN上一帧、边界归桶 | 121.307dB、非正交2目标恢复、边界检查通过 | Host观察器 |
| Python全套 | 40项通过，无skip，含6项新投影负控制 | 工具/实际传输 |
| 透明公共24对 | 所有既有默认指标完全相同 | Host完整链 |
| 频谱观察 O2 与 ASan/UBSan | 48行 records 完全相同，包括原有指标和所有投影累计量 | Host交叉验证 |
| 原始16录音透明观察 | 观察/无观察/冻结输出PCM完全相同 | Host原始重放 |
| 非仓库cwd CLI help/dry-run | 退出0、24对、不写文件 | 工具入口 |
| fresh-default-v9-bound | 69编译单元、176源码头绑定项；默认动态/静态库与v8逐字节相同 | Host默认制品 |
| v8/v9默认源码身份 | 92个AEC/base/SEVC源码头项目完全相同，新项仅两个诊断头 | 源码身份 |
| 四模式当前源码重编 | 与对应v9-final评价器逐字节相同，避免重复跑同一质量实验 | 测试制品 |
| git diff --check | 退出0 | 空白检查 |

ASan/UBSan仅覆盖测试代码，链接vendor库未插桩。
默认 SEVC_COMPLETE_RESET=0 保留overlap历史；改变输出模式在Reset后前两hop仍受旧历史影响，
之后VOICE必须完全一致。透明模式仍比较每一帧。不把这一既有语义改成完整Reset。

## 制品绑定

默认动态库SHA256：1f0dbcbda5db2f377d8eba1b0a161c7f6ccdfb4a7513a1def39dd61f892a73fe。
默认静态库SHA256：cc9561d29c93d00948eb90c1a59b0a0f28f8d59a01ca3895107c798a9a807532。

| 本地证据名 | SHA256 |
|---|---|
| fresh-default-v9-bound/build.json | 6f8c8d0c652f25025731c90f3eda0befb46a057d60e67e59e403acf1c447fe9e |
| tail-ablation-identity24-v9-final.json | 0a27714496039b873e5073915ccfee006b8e424e86cfa88f356afe6e387db1a0 |
| tail-ablation-1-public24-v9-final.json | a633bb9e2c565bfcd31047036e88d9f338447c80a5c69f639463ab464796ec92 |
| tail-ablation-2-public24-v9-final.json | 5a0396299bba988bb4ecb1b7600d403d193320484cbc0a841566c2dc5eb390fc |
| tail-ablation-3-public24-v9-final.json | 3009240eafee19550031265715b48025f02146543e1748b04c18e7221ff89c6c |
| tail-spectral-truth-public24-v9.json | f8d7e589f0fb3193f9bab38f57b6a71aed8610d3c85f71de03452d16c648c8ad |
| tail-spectral-truth-public24-sanitized-v9.json | d198b60cd21950bdf95b9660131f7e9faa4c755855acacd8b7991abb700efd79 |
| tail-spectral-truth-metrics-bound-v9.json | ffc9dbdb119ed3e773df25ce1b71d6e4f889c42e2e05a45ae5d4643cd057bcbe |
| tail-ablation-identity-captures-v9.json | fbfbdb2e9bc55123da428b7734af7a4c1151c13815b366461142af772639114f |

测试实现身份另行绑定，因为isolated build不把测试C/Python当产品编译单元：

| 文件 | SHA256 |
|---|---|
| tests/sevc_tail_ablation_adapter.h | 9f9288172e9f1d064c49659ec3178512e9a45f9f4705fdb40172517b194dcab4 |
| tests/sevc_tail_ablation_regression.c | 5d3b10fe72d9bfa7d7642f8906c6c864158085141bed6641300c767ae4e9af1e |
| tests/sevc_tail_truth_probe.h | d5fef21f10d6eff2c11b3a083ca774d69d0032ca7c5d86682ed87c5996b12b8a |
| tests/sevc_tail_truth_regression.c | 073b020cd4e4f3c8686aed09c86ab80dde79d0f9d7c4588b44a541a40a7fcee6 |
| tests/sevc_aec_challenge_evaluator.c | ff6cfd1275f949aac23a202d21ea264faf5c35b798891c6fa196ecd2b644f4bd |
| tests/test_tail_truth_metrics.py | 1e24bd4f3ef392da9e0f327deac944f92de642617a7cc9bd995d30196fba757c |
| tools/codex_assets/tail_truth_metrics.py | d41918d64e897a90ca942c17589c61b6994b5e4982c4f84257c0cb80a977f76f |

可复跑入口：isolated_build --output新目录；make -C tests -o host-lib HOST_LIB=<新库> run-tail-ablation-contracts run-tail-truth-contracts；
supervised_compare以同一split绑定实际baseline/candidate二进制；tail_truth_metrics从配对JSON生成新投影文件。
评价器用固定库宏AISPEECH_FIXED/NN_FSMN/SEVC_MULTI_CORE/SEVC_COMMUNICATION；
CALL另加SEVC_TEST_TAIL_MODE=1和-include tests/sevc_tail_ablation_adapter.h。
频谱观察另加SEVC_TEST_TAIL_TRUTH=1、模式0；模式1/2/3一次只选一个。

## 下一阶段

replan：先在冻结原生AEC残差上验证选择性抑制的理想上限，而非再次放宽全局增益。
理想上限可使用公共真值，但必须标成Host不可部署；完整CALL仍以近端/双讲/远端联合门槛判定。
若理想选择都不能带来完整链收益，停止该机制；若有稳定收益，再设计不依赖clean truth的判据，
以独立holdout验证，不能在当前24例扫描阈值。
继续保留 v2-v8 负结果，不重复AEC权重冻结、AGC去增益、MIC/REF延迟扫描或MDF整链替换。

logical_task_open: true
open_items: 有效生产候选、独立保真回归、ARM资源、设备制品/电话听感。
Knowledge: 仅经Provider归档reviewing候选，不提交raw音频、原始日志或会话，不代表owner review或产品放行。
Runtime: final门禁与实际算法/产品资格分别判断；成功条件call-residual-protected仍未满足。

