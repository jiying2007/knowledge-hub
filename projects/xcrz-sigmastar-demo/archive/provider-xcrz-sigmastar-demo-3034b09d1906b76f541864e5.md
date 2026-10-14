---
id: provider-xcrz-sigmastar-demo-3034b09d1906b76f541864e5
title: CALL AEC 独立稳定性与完整尾链复验 v6
kind: debug-record
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/archive/provider-xcrz-sigmastar-demo-3034b09d1906b76f541864e5.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: provider-candidate-archive
  from: provider-policy-sha256:a295759999c3c3c2594752350565bbde6af74808af32b9272604f53a36f82736;operation:3034b09d1906b76f541864e5c6294a4b7dbb689e0bbf451fa41f2153dade9227
  source_sha256: bf8665ab03474a128d9efcc15d52f2f94b827fe271270a60a005a5952a693a46
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
- projects/xcrz-sigmastar-demo/archive/provider-xcrz-sigmastar-demo-3034b09d1906b76f541864e5.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/archive/provider-xcrz-sigmastar-demo-3034b09d1906b76f541864e5.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-10-10'
updated_at: '2026-10-10'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-10-10'
manual_validation_pending: true
summary_zh: 'source: 当前用户授权的本地优化、冻结四轨评价集、两轮设备原始录音和实际Host算法。 captured_at: 2026-10-10 last_verified: 2026-10-10 topic: call-aec-stability-and-tail-compatibility
  completion_claim: false logical_task_open: true stage_result: 原型内部稳定性提升；完整CALL候选拒绝；默认恢复通过；持续明显远端自回声仍needs-fix。 scope: 项目本地Host实验与测试工具；无部署、restart、ARM效果放行、'
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
subject_ref: &id001
  id: xcrz-sigmastar-demo
  type: project
created_subject_ref: *id001
principal_id: null
provider_operation_id: 3034b09d1906b76f541864e5c6294a4b7dbb689e0bbf451fa41f2153dade9227
---

# CALL AEC 独立稳定性与完整尾链复验 v6

source: 当前用户授权的本地优化、冻结四轨评价集、两轮设备原始录音和实际Host算法。
captured_at: 2026-10-10
last_verified: 2026-10-10
topic: call-aec-stability-and-tail-compatibility
completion_claim: false
logical_task_open: true
stage_result: 原型内部稳定性提升；完整CALL候选拒绝；默认恢复通过；持续明显远端自回声仍needs-fix。
scope: 项目本地Host实验与测试工具；无部署、restart、ARM效果放行、commit或push。
sanitization: 仅工程结论、指标、制品hash和复跑指针；不包含原始音频、完整日志、凭据或设备端点。

## 结论与边界

v5的普通MDF在真实语音中出现内部削顶。本轮在独立线性阶段验证了全谱最大分母归一化、前后台滤波、弱激励提升门槛修复和零回声模型回退。最终原型在冻结24对和16设备录音上，前台/后台残差均无内部削顶，独立阶段保护明显改善。

同源接回当前AES/NN/AGC后，完整CALL依旧明显弱于原生CALL。不能把独立稳定性或已知IR校准升级为产品效果。候选不采用，实验hook全部撤回，上层reader/订阅/lease、profile切换约定和既有产品优化保持原样。

当前16组实际采集全为VOICE；CALL指标来自真实算法Host离线重放。设备原始数据没有独立干净近端目标。公共24对保留原split、四轨hash、nearend_scale和原生评价器参考延迟，未修改输入、参考delay20或BF。

## 单变量实验与控制

所有独立原型保持hop256、FFT512、四分区64ms、MIC延迟16点。FFT正向不缩放、逆向1/N；时域误差有效后半块，更新梯度投影至前半块支持区。使用本地独立实现，没有复制外部实现或新增运行依赖。

| 实验 | 公共24对内部削顶点 | 远端线性抑制平均dB | 双讲SI-SDR相对未处理mic最差改善dB |
|---|---:|---:|---:|
| 逐频点归一化 MU.2/REG0 | 29930 | -1.183113 | -29.273458 |
| 全谱最大分母 MU.2 | 0 | 1.690777 | -1.298411 |
| 全谱分母+前后台 MU.2 | 前后台均0 | 1.295179 | 0.000000 |
| 相同前后台 MU.8 | 前后台均0 | 2.136336 | -0.691867 |
| MU.8+零回声模型回退 | 前后台均0 | 2.204573 | 0.058618 |

这些线性分数的对照是输入mic，不是原生完整CALL；不可与完整尾链效果变化混用。file0逐频点版本内部削顶24502点；全谱版本0点，其最差双讲退化从-29.273降至-.332dB。全谱分母使步长与时域投影相容、避免弱频点的大更新，实验支持此机制影响原型稳定性，没有据此认定产品回声根因。

前台不直接随每帧梯度变化。后台持续学习，当前及平滑误差同时改善10%、持续8帧才提升，恶化时回退后台；提升使用一帧交叉淡变。初版固定1e4能量差门槛使弱参考前台停滞，末段线性抑制17.85dB；门槛降到1PCM平方量级后为31.27dB。MU.8在控制条件收敛更快，但公共file21前台只提升一次后失效，远端线性-.369dB、双讲-.692dB，因此再增加与零回声模型的能量比较及一帧回退淡变。最终file21远端线性+.173dB。

最终24对target投影绝对值最小-.351654dB；相对输入mic投影变化最小-.111290dB。工具分别报告两者，避免把输入自身的标定/混合偏差算作算法损伤。所有24对另外独立运行全零参考近端流，延迟后的PCM精确传递。

11组已知真值控制覆盖白噪声、窄带、弱参考、突发及相应双讲，非线性、路径改变、无参考。最终前后台均零内部削顶。白噪声控制末段76.89dB、弱参考41.27dB、非线性27.01dB；这些是生成控制，不代表真实设备效果。路径变化首800ms从MU.8未保护的-.524dB到回退保护的+1.203dB，仍需后续真实动态验证。弱参考双讲从38.36到5.09dB，说明能量回退也会损失消回声收益，不能只报告防发散。

独立C数学校准：全谱MU.2为32.962623dB，最终MU.8前后台/回退为73.548951dB，FFT往返误差5.55111512313e-17，削顶0。原型state最终111704字节，没有ARM CPU/stack资格。

机制参考仅使用[SpeexDSP 1.2.1官方mdf.c](https://raw.githubusercontent.com/xiph/speexdsp/SpeexDSP-1.2.1/libspeexdsp/mdf.c)，retrieved_at=2026-10-10：该实现描述前后台滤波及可变学习率。本轮独立原型只验证部分保护，不声称完整算法迁移；没有复制源码、引入依赖或归档外部原文。

## 设备线性阶段与完整CALL

独立probe首先按七文件schema/seq/PTS/epoch/实际usedREF验证16组，直接使用mic1和usedREF，全16组前后台内部削顶0。保持quiet1..29s、其它4..26s及无EOF补样本。

| 设备远端顺序 | 独立线性mic能量抑制dB | 完整CALL总抑制相对原生变化dB |
|---|---:|---:|
| rpm240 far | 7.619448 | -12.947361 |
| rpm240 far-motion | 6.233177 | -13.774030 |
| rpm480 far | 7.281172 | -13.149593 |
| rpm480 far-motion | 5.969263 | -11.545641 |

独立线性设备指标包含背景噪声等，不能称纯AEC ERLE。完整指标包含AES/NN/AGC的共同结果。不同阶段的通过项分开；本轮没有定位完整链路损失的具体算法归因。

完整接入使用延迟mic、residual经同一原生sqrt-Hann/FFT，echo=mic-residual，低两频点保持原约定，同源进入已有AEC callback/AES/NN/AGC，VOICE保持原主链。CALL评分延迟528点=33ms，默认512点=32ms；arena420020比默认308308多111712字节，全部Host实验。

| 公共24对完整版与原生CALL配对变化 | 平均dB | 最差dB |
|---|---:|---:|
| 远端ERLE | -2.921333 | -7.967 |
| 双讲SI-SDR改善 | -1.986875 | -13.156 |
| 显式纯近端SI-SDR | +.064167 | -.284 |
| 双讲target投影增益 | +.018625 | -1.434 |

公共完整版24对前后台内部削顶均0、最终削顶0；设备16CALL内部输出残差削顶0、最终削顶0。设备16VOICE PCM与原生精确相同。无参考完整CALL接口153600点与显式延迟mic后的native完整CALL逐点一致，PCM SHA256 `a87dece603fc9f1af69becb66490c3c897a38e5e890e9e4883cf4cbf6aacc004`。这些不足以通过回声质量，候选拒绝。

## 改动、恢复与验证

保留tests的原型可选保护、独立C PCM probe、5个真值/实际传输回归，以及三个tools.codex_assets入口：mdf_stability_probe、mdf_control_probe、mdf_capture_probe。三个入口均在非模块cwd验证help/dry-run，不写输出。PCM transport拒绝空/超限/非完整块/截断/多余payload。所有新工具仅生成JSON元数据和指标，不保存新增音频或权重。

临时接入sevc_func/types、bridge/evaluator已撤回。本地mdf-host-source-v6保留接入及原型快照，供核查实验身份，不进入Provider正文。当前产品无法凭旧SEVC_TEST_MDF宏重建该后端；缺导出会被工具拒绝。

fresh-default-v6：69编译单元、170来源项无漂移，空候选宏；43 SEVC/bridge绑定项与v5相同。默认shared `1f0dbcbda5db2f377d8eba1b0a161c7f6ccdfb4a7513a1def39dd61f892a73fe`、static `cc9561d29c93d00948eb90c1a59b0a0f28f8d59a01ca3895107c798a9a807532`，均与v5相同。16输入配对/32默认PCM与v5完全相同，31Python回归通过，两仓diff--check通过。没有新增ARM或HIL；API/HDI/Sensor生命周期本轮未修改。

## 证据索引

证据基目录为项目本地 `.cache/aispeech-offline-evidence/call-residual-resume-20261009/`，只作为本次可复跑工程指针，耐久结论通过Provider归档为reviewing候选。

- 最终线性24对 `mdf-linear-zero-guard-public24-v6.json` SHA256 `27156ac654bacb65f83b77f3ba10817ae032d25a51234db9b727139f4a1667ed`。
- 最终11控制 `mdf-controls-zero-guard-v6.json` SHA256 `b91e3bb4874ad8d8bc9e48b8a29f7ee700334b54f44e051d49de80bd31ba349f`。
- 16设备线性 `mdf-linear-captures-v6.json` SHA256 `9aea5628fee39e45adcafda0ce030cf1fe230fcf6abf3024a9d48248bc32f254`。
- 完整候选build `mdf-zero-guard-full-v6/build.json` SHA256 `0df5a35efd71a7371a6b13ab0141cceb58f0db22d3e7470ebdd803e9c1f9c064`；shared `a05d14b6c615198ee8cefc3186b7f9bbfe7c4dbd1dc2bb9fad8ab1d62d5764e9`。
- 完整公共 `supervised-mdf-zero-guard-full-v6.json` SHA256 `df53ab724a0d0b33176eca2c5d23598f2842ebf202d0a6a67263aa86f0ab5928`。
- 完整设备 `mdf-zero-guard-full-replay-v6/results.json` SHA256 `7924254bd9db4058f753bd9957beeb82f093b66d3e3f222fc748c0a8ea77f339`。
- 完整无参考 `mdf-interface-full-v6.json` SHA256 `cc47561f4085d8d6ace5688db21e0e4fab522ace91b8f0ff685ee6dc5d4e0d91`。
- 默认build `fresh-default-v6/build.json` SHA256 `3018e1a46fe42771ceefb34c68fc6ae78fa5bc56329f38f71ebc482b0e361544`。
- 默认重放 `fresh-default-v6-replay/results.json` SHA256 `43e12b97eff6e88bb27c93d3fb3708c9aebf3cdd31dc1f6b4cd717c63b19600a`。
- 原split SHA256 `4274aeeabbc0a2de54f0afcda789d821468f5558b3a7bf5a10f8f9a799a395bb`。
- 过程负结果对应mdf-linear-public24-v6、mdf-linear-two-path-public24-v6、mdf-linear-two-path-mu800-public24-v6及各控制JSON，不覆盖v2-v5证据。

## 下一阶段

stop_condition_result: replan
open_items: 有效主链消回声收益、近端双讲保护、ARM资源、设备听感仍未闭环。

先沿实际原生SEVC链路分开测线性、AES、NN及AGC的增益和target投影，定位新残差为何无法保留完整尾链收益；再考虑在原生滤波器内加入权重保护或受控候选选择，保留原生主链回退。使用相同数据和完整原生CALL质量门禁。不得重复直接替换AEC后仅凭内部稳定、控制IR、远端总衰减或输出削顶宣称成功。
