---
id: aispeech-comprehensive-review-20260921
title: AISpeech五方向全面推进与分层门禁
kind: debug-record
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/archive/debug/2026-09-21-aispeech-comprehensive-review.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: team-core
source:
  type: project-source
  from: workspace://xcrz-sigmastar-demo/modules/aispeech
  source_sha256: 2d6bfd378b68e30a6f789c58735ab82be33e2334795022bc01dcfc8aed5c25c8
  temporary_source_retained: false
review_after: '2026-10-21'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- aispeech
- validation
validation_refs:
- projects/xcrz-sigmastar-demo/archive/debug/2026-09-21-aispeech-comprehensive-review.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/archive/debug/2026-09-21-aispeech-comprehensive-review.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-09-21'
updated_at: '2026-09-21'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-09-21'
manual_validation_pending: true
summary_zh: 输出BF VAD NRNN AEC五项离线推进，记录负结果与设备端点阻塞，默认已恢复
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
---

# AISpeech 五方向全面推进：离线结果与设备门禁

本轮按用户“全部推进”执行输出余量、BF资源、VAD契约、NR/NN归因、AEC/AES五条工作线。
算法源码和产品默认未修改，本轮新增测试/观测入口，保留所有既有dirty。
源码身份：AISpeech 9ce7a7f87b4835816e68df7fade6d43ebb3d47a1，
HDI b34d16ccd732d23be766b9c2b2b05016ac877008，APP 0447b7dd898de5a1d6b46c60d1a2118dbbba50b4。
这些HEAD均叠加工作区已有改动，不是可直接发布的干净基线。

## 1 输出余量

8样本、每样本3路径×2幅度×2噪声，默认与headroom候选各96项。
headroom宏只影响sevc_func.c，直接重编该单元和观测器覆盖静态库成员，无布局变化。
样本4原幅度无噪声：output_gain clip106→0，SI-SDR20.971→19.965dB；
样本25同场景SI-SDR最差下降3.207dB。32对交互组合6项回落超过0.01dB。
CALL和CALL旁路AGC结果不变。候选的限幅收益不抵消逐帧增益调制回归，不晋升默认。
sevc_func.c与观测器直接ASan/UBSan，样本4完整12项退出0。

补充独立固定outGain=1.0候选：完整库和评估器同宏SEVC_OUT_GAIN=32768构建。
32个交互组合电平低约1.86～1.94dB，SI-SDR变化-0.001～+0.933dB；
输出增益阶段限幅均0，但样本25加噪声仍有1个overlap限幅。CALL控制路径全部指标相同。
它是较低固定输出电平对照，不是已验证中文唤醒方案。默认仍1.25，limiter仍0。

## 2 BF资源和真实消费者

当前AES音频入口为pLastAec，NR的SPP参数为NULL；GSC/BF_POST默认0。
BF三波束与SPP未被上述音频路径使用，但BF功率诊断会变化，不能宣称全系统所有字段相同。
BF1和BF0严格串行clean/rebuild完整库，评估器同宏；共享x86源目录对象不并行构建。
- Host memory315620→308308，减少7312字节。
- 1000帧混合模式/Reset指纹均16985685392395738340。
- 各模式2000帧，INTERACTION指纹10513963233676980736，CALL指纹5134122061793485912，两变体相同。
- 8样本96项音频观测及分级clip计数全部相同（192行对照），未比较BF功率遥测为不变。
- x86_64上3轮交错复跑：INTERACTION线程CPU均值BF1约102.825～119.139us，BF0约93.954～94.799us；
  CALL分别213.929～215.332us和204.309～208.987us。墙钟p99有抖动/重叠，不能宣称目标板收益。
默认BF仍1。候选可进入板端资源/遥测验收，尚未证明SSC305截止时间、CPU或RAM实际部署收益。

## 3 VAD契约与消费者

API：INTERACTION为NONE/valid0；CALL就绪后为NN_AGC代理；过渡/预热不输出有效近端状态。
连续256帧全零输入，237帧状态有效，其中170帧speech代理为1。这是模型代理局部观察，
不是广义误报率，不能当校准语音概率用于硬门控。
HDI仅为有效NN_AGC发送CALL事件。APP唤醒diag显式选择VOICE，并在无VAD或stale时fail-open。
所以当前gate=on不等于近端门控实际生效；该fallback避免未知状态直接丢音频。
APP diag和app_test消费者目前没有核验source/profile/generation。当前生产者边界限制了来源，
但接入其他来源或跨代消费前仍需补校验，不能把已有atomic快照视为完整生命周期契约。
本轮固化README语义并复跑API契约，不新增未经标注语音数据验证的检测器，不修改应用分支。

## 4 NR/NN弱尾段归因

新增sevc_tail_gain_attribution.c，在原阶段回调前读取能量/NN实际应用增益，之后调用原回调。
参考全零，断言AES旁路；NR读末路AEC残差，NN断言R=1并读轮转前FIFO，输入输出对齐。
每段排除前4帧，避免FFT/右上下文边界噪声主导弱尾段。NR的floor字段为nan（未测）。
8样本×NR/NN×无噪声/噪声共32个路径，探针开关的PCM指纹逐项一致。
探针ASan/UBSan及严格编译通过；其他库非全体instrument。缺输入返回2，短于15帧拒绝。

样本18尾段：无注入噪声NN -0.1291dB；噪声结束后NN -13.9794dB，
落在0.20增益下限的频点承载100.000%输入能量。NR对应约-0.3571/-0.2700dB。
这把该段衰减定位到NN阶段，仍不是每个真实音节的标注或全部模型根因。

反事实诊断--reset-nn-after-noise利用已知噪声注入边界，在FFT重叠清除后Reset NN：
样本18尾段变为-1.6833dB，支持历史状态参与；但样本4变成-9.4360dB（原-0.8427），
样本43变成-9.9263dB（原-1.5123）。禁止把这个oracle重置作为运行时修补。
模型特征历史/CMN/滤波历史均在Reset范围，尚不能唯一归因于其中某一项。

NR四种数值配置、shared scratch、NR/NN过渡与Reset回归通过；不盲降floor或扩大抑制。

## 5 AEC/AES及设备准备

新鲜通过：参考延迟已知偏移/上界/静音/长度、AEC残差回声配对、CALL Reset、
AES默认/释放候选状态、Activity DTD、1000轮双向切换（switches2000、callbacks40013）。
严格声学run-aec-quality失败后，另行执行Room002，未因第一项失败漏测第二项：
| 场景 | far ERLE dB | 按现有口径远端DTD active比例 | 门槛 | 结果 |
|---|---:|---:|---:|---|
| Room001 | 11.604 | 6.164% | <=5% | fail |
| Room002 | 24.908 | 6.849% | <=5% | fail |
两者双讲recall=1，其他本次适用gate指标未越限。该比例包含hold状态，
Room001有1个raw active和8个hold active，Room002为1和9；不要把它直接当独立语音VAD误报。
双讲后恢复为24/4帧是离线观察，不是设备恢复保证。不放宽门槛，也不据此强行缩短AES保持。

设备环境PCR02_ADB_SERIAL和PCR02_ADB_ENDPOINT均未设置，已异步请求当前端点，未收到。
未连接设备、未部署、未采集现场音频。设备状态是blocked_missing_endpoint，不是设备失联。
按已有PCR02 runbook准备：
1. 提供端点后先只读preflight，核boot_id/进程/安装BuildID和hash/日志健康/standby与watchdog。
2. 确认已安装诊断接口，再读取diag.hdi.ai.profile.get.run：p95/p99、deadline_miss、
   discontinuities、ref_delay_samples、echo_path_notify/apply/fail/pending；这些字段源码入口已核验。
3. 同步mic0/mic1/render/处理后PCM，验证静止/移动/播放音量变化/双讲；参考delay禁止reader活跃时改。
4. 单次smoke通过后才扩大短循环和长稳；设备恢复及制品身份按现有runbook留证。
本文不授权设备push/restart或修改参考延迟，产品媒体分支整合仍是独立门禁。

## 恢复与交付

BF及outGain变体结束后完整重建默认Host库和评估器。默认指纹16985685392395738340、memory315620。
默认库SHA256 576b9195e472059b62a31c0a247788d7685a45e1da0d19081df43d7781e418c7。
新测试文件sevc_stage_performance.c、sevc_tail_gain_attribution.c，以及VAD静音观测/Makefile/README增量。
未改产品算法宏默认、没有commit/push/merge或镜像/OTA。既有dirty全部保留。
完整数字结果/tmp/aispeech-comprehensive-results-20260921.json，计划/tmp/aispeech-comprehensive-plan-20260921.md。
本轮仅测试源码新增，无ARM算法逻辑变化；没有伪称新产品链接或Board/HIL完成。
独立性：主代理自审+控制组/探针开关/重复计时；无外部独立审查或完整中文听感。
Runtime Control idle/null goal缺会话制品，按planning skill单列not_applicable。
reusable_pattern: 五方向分别门禁、控制变量和原始/保持状态归因；promotion_candidate: false。
do_not_promote_reason: 板端/中文/应用契约未闭环；owner_review: pending。
rollback_path: 本轮仅测试/文档增量；默认库已恢复，不回退既有修复。
next_task_friction_reduced: 可直接续接设备身份核验及针对NN历史的有界实验；reduced_by: 性能/阶段归因工具与五项证据表。
reduction_evidence: 指纹一致、负结果、严格gate和设备前置清单。
