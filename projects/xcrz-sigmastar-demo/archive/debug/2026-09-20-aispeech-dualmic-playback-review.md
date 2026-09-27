---
id: pcr02-aispeech-dualmic-playback-review-20260920
title: AISpeech 双麦播放交互与通话审查
kind: debug-record
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/archive/debug/2026-09-20-aispeech-dualmic-playback-review.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: team-core
source:
  type: project-source
  from: workspace://xcrz-sigmastar-demo/modules/aispeech
  source_sha256: bed2bf0de9020f3ad74bc7c62384a72552a159c0022e72be3c88ed8792b4666f
  temporary_source_retained: false
review_after: '2026-10-20'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- aispeech
- aec
- validation
validation_refs:
- projects/xcrz-sigmastar-demo/archive/debug/2026-09-20-aispeech-dualmic-playback-review.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/archive/debug/2026-09-20-aispeech-dualmic-playback-review.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-09-20'
updated_at: '2026-09-20'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-09-20'
manual_validation_pending: true
summary_zh: 修复AES回声通道错配、NR定点溢出和通话Reset残留，保留声学质量与预编译集成阻塞。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
---

# AISpeech 双麦播放交互与通话审查

Source: modules/aispeech 9ce7a7f 加本次未提交修复；只读核对 HDI、产品链接规则、QIVW 诊断消费者。
Last verified: 2026-09-20
Status: reviewing / needs-fix for product quality; focused source repairs verified.

## 场景与边界

小型移动机器人，35 mm 双麦；语音助手交互与对讲通话。用户确认：播放时“你好小窝”明显比“小窝小屋”难唤醒，安静时基本正常。
未取得带词标签的同步双麦/参考录音、两词 QIVW 分数、现场安装制品身份或设备端点。因此不能确定词级唯一根因，不能声称唤醒率已提高。

## 已证实并修复

1. AEC/AES 通道不一致：AEC 附加 echo 槽为 mic0 - err0，AES 输入却是最后一路 mic/err。改为最后一路的回声估计，保持输入同源。不同增益/相位测试旧实现 7453 个频点不匹配，修复后通过。双麦相同输入掩盖了该问题。
2. NR 后验 SNR 先转 S32 再限幅，低噪声底后的强输入产生负历史量 -562397184。改为 S64 域先限幅，偏置噪声分母也保持宽位宽。默认路径和共享区配置定向测试通过，后者通过 ASan/UBSan。
3. 通话时 AEC 为 1 抽头/步长 0.4，交互为 2 抽头/步长 0.8。Reset 回到交互时未恢复参数、清理未覆盖休眠抽头。改为 Reset 清理前恢复分配时抽头数和交互步长；旧源码隔离回放失败，新源码全抽头清零断言通过。
4. NR 跨帧数组使用共享临时区分配：改用局部持久区。重要纠正：当前 MULTI_CORE 配置会关闭 USE_SHARE_MEM，此问题只在共享配置复现，不能归因于当前产品默认。当前 Host arena 仍为 315604 字节。
5. 评估器未包含配置头，曾报告 AES cap 为 0 而实际已限幅到 1.0；未开启 adaptation telemetry 时还输出非法 JSON -nan。包含真实配置默认值，增加比值有效标记，消除 0/0；jq 校验通过。仍要求库和评估器同宏重建。

## 未直接调参的原因

- AES 双讲判据为残差幅度大于估计回声 1.5 倍、持续两帧；弱近端是否被漏判需真实双麦录音。降低阈值会影响纯回声误判，不能直接作为修复。
- AEC 交互步长 0.8、2 抽头，通话步长 0.4、1 抽头；未继续增大步长或默认启用 DTD freeze。
- NR 默认增益下限 0.75，单阶段最大幅度衰减约 2.5 dB；这是弱语音保护与降噪能力的取舍，不能靠一味降低地板保证唤醒。
- BF 执行但其输出未进入当前 AES/尾链，实际取最后一路 AEC 残差。未擅自切换 BF 路由。
- HDI 默认参考延时 20 samples（16 kHz 下 1.25 ms），需真实扬声器/机壳路径测量，不能从公开录音推导机器人延时。
- SEVC_COMPLETE_RESET 默认仍为 0。首轮完整 PCM reset 等价测试失败；后续修复只覆盖 AEC 参数与全抽头清理，不能宣称所有历史清空。

## 本次验证

| 验证 | 结果 |
|---|---|
| 三个新增默认构建测试：通道、NR、Reset 权重 | 通过；均有旧实现失败证据 |
| NR 共享区配置 + ASan/UBSan | 通过；旧共享配置第 0 帧失败 |
| 1000 轮交互/通话切换 | 2000 次切换，40013 callbacks，通过 |
| Activity DTD smoke | 通过 |
| 三个改动 C 文件 SigmaStar GCC 11.1 ARM 定向对象编译 | 通过；既有 unused warnings 仍存在 |
| 评估 JSON / AES 配置输出 | jq 通过，cap=1048576，未开启 telemetry 时 ratio_valid=false |
| SLR28 Room001 严格 quality gate | 失败：far ERLE -0.225 dB，post-double 首256ms -11.369 dB；不隐去失败 |
| 公共头 parity | 失败：现有预编译集成面是旧接口，非本次修改引入 |

24 个冻结四轨样本：使用相同输入、scale、基线与候选静态链接评估器。此测试复制相同 mic 到两路，因此主要测 NR 数值修复，对真实双麦通道修复效果没有证明力。

| 指标 | 基线均值 | 修复均值 | 单样本变化范围 |
|---|---:|---:|---:|
| 纯近端 SI-SDR dB | 20.1276 | 20.6592 | +0.014 至 +1.580 |
| 双讲 SI-SDR improvement dB | 6.7240 | 6.7358 | -0.098 至 +0.141 |
| 远端 ERLE dB | 9.1184 | 8.9861 | -0.397 至 -0.016 |
| clipped 总样本数 | 11 | 11 | 一个样本 +1，另一个 -1 |

没有将存在质量取舍的结果包装为全面优化通过。保留确定性缺陷修复供审查，产品声学验收仍 needs-fix。

## 集成阻塞

产品 pcr02.mk 链接 libs/3rdparty/aispeech/lib；pcr02/dep.mk 中 aispeech 源码依赖被注释。
预编译头 SEVC_API_New 为旧7参数，源码/HDI 使用新3参数。预编译静态库未找到 FeedPlanar、TailModeRequest、FrontendStatsGet 定义。
独立仓构建与当前产品制品不一致；没有覆盖预编译库/头、重新链接产品或部署设备。
安装版本尚未核验，因此不能把本次源码缺陷直接等同于现场固件根因。

## 下一步与验收

1. 对齐新源码、公开头、静态库和 HDI 消费者，重建产品并记录 hash/BuildID；旧 image/OTA 不会自动包含后编译 app。
2. 同步保存 mic0/mic1/render reference/output，在相同距离、方位、播放音量、静止/移动条件下录制两词。实际录音只留受控本地，归档只记录脱敏指标。
3. 分别统计原始选定 mic 与处理后输入 QIVW 的两词分数/命中率、无说话误唤醒、各音节起止保留；以此决定 AES/DTD 与 NR 候选。
4. 对讲另测远端单讲回声、近端单讲、双讲、移动路径变化、切换后短时残留，SSC305 CPU p95/p99 和16ms预算。

## 治理与复跑

Claimant/reviewer: 当前主 Agent 实施并定向复核；未宣称独立人工或子代理审查。
Commands: `rtk make -C modules/aispeech/tests run-aec-channel run-nr-state run-nr-shared run-reset-equivalence run-long run-activity-dtd`。
Input snapshot: tests/validation/datasets/aec-challenge-synthetic/evaluation-split-v1.csv，24行固定集，第三方 WAV 不入 Git。
Session evidence: /tmp/aispeech-compare-20260920.json 为可重建的临时指标，不作为长期唯一依据；本文仅保留统计与复跑入口。
Reusable pattern: 双麦后处理必须检查 mic/residual/echo 同源，定点限制必须在窄化前完成，新增跨帧状态不能留在共享 scratch。
Promotion candidate: false；owner_review=pending；尚缺双麦与实际关键词/板级证据，不提升为团队规则。
Next task friction reduced: 新增确定性测试防止回归，并显式区分同麦复制样本与真实双麦。
Rollback: 撤回本次源码补丁后重建同配置库；没有现场部署需要恢复。
Privacy: 无原始录音、端点、密钥或完整会话正文。
