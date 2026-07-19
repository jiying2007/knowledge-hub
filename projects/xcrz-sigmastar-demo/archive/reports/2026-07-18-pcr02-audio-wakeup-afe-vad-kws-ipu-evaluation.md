---
title: PCR02 双麦声学前处理、VAD、KWS 与 SigmaStar IPU 方案评估
captured_at: 2026-07-18
last_verified: 2026-07-18
manual_validation_pending: true
manual_validation_reason: 当前结论来自源码、SDK、候选方案和既有串口日志审计；尚未完成同板、同语料、同阈值口径的 AFE/VAD/KWS A/B，也未完成视觉负载下的 IPU KWS 压力测试。
required_followup: 先修复 QIVW FIRST/CONTINUE/LAST 状态机和 200 ms 聚包，再完成三通道原始 PCM 标定、AFE 模块消融、VAD shadow 评估与 KWS DET/FAH 测试。
memory_candidate: false
related:
- projects/pcr02-ssc305/README.md
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
evidence_strength: direct-command+direct-log+official+inference
id: xcrz-sigmastar-demo-audio-wakeup-afe-vad-kws-ipu-evaluation-20260718
kind: project-archive
domain: projects/xcrz-sigmastar-demo
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
review_after: '2026-08-18'
review_status: manual-entry-pending-review
promotion: none
tags:
- pcr02
- audio
- aispeech
- vad
- kws
- qivw
- wake-word
- sigmastar
- ipu
- two-mic
- echo-reference
- source-audit
- manual-validation-pending
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-07-18'
summary_zh: 基于源码、设备日志、SigmaStar S02 SDK 和本地候选方案，归档 PCR02 2 MIC+1 REF、35 mm 条件下 AISpeech VAD、QIVW 喂流与 IPU KWS 的证据、风险、推荐架构和单变量
  A/B 验收方案；板端统一对比仍待验证。
promotion_decision: none; capture does not authorize active promotion or owner decision
---

# PCR02 双麦声学前处理、VAD、KWS 与 SigmaStar IPU 方案评估

## 摘要

本文归档 PCR02 在 2 MIC、1 REF、双麦间距 35 mm、16 kHz 条件下，围绕唤醒词“小窝小窝”的端到端声学与唤醒方案评估。主结论是：当前更优路线不是直接以 SigmaStar IPU 替换 AISpeech，而是先修复生产 QIVW 喂流协议、取消 VAD 对本地 KWS 的硬门控、完成 MIC/REF 标定与 AFE 模块消融；中长期再采用“CPU 声学前端 + SigmaStar S02 IPU 小型专用 KWS”。

本文只作为 `reviewing` 历史归档候选，不代表板端效果已验证、owner 已签收、方案已发布或可以直接替换现网实现。

## 来源与归档边界

- 主责项目：`robot/xcrz_sigmastar_demo`，归档应用、声学模块集成、QIVW 喂流与 KWS 方案事实。
- 关联平台：`pcr02-ssc305`，提供 SSC305、音频接口和 IPU S02 平台能力证据。
- 厂商 SDK：本地 `SGS_IPU_SDK_24091114` 快照；未复制 SDK、模型、二进制或专有实现到 Knowledge Hub。
- 候选方案：`athena-signal`、`ten-vad-edge`、`silero_vad_c`、`vad`、`audio_ai_pipeline`、`sherpa-onnx` 的本地源码快照。
- 外部来源：TEN-VAD、WebRTC Audio Processing Module、sherpa-onnx KWS 和 BC-ResNet 官方仓库、官方文档或论文；仅保存摘要和 URL，不复制长段原文。
- 脱敏：不归档完整聊天、完整串口日志、私有端点、凭证、二进制内容、模型内容、构建 cache 或运行时状态。
- 源码状态边界：相关工作区存在既有未提交和未跟踪内容；本文不将工作区快照等同于正式提交或发布版本。

## 已证实事实

### 1. 当前生产声学链路

`modules/hdi/src/hdi_audio/hdi_ai.c` 配置为：

- `AI_SS_ALGO_ENABLE=0`；
- `AI_EXTERNAL_SEVC_ENABLE=1`；
- `AI_EXTERNAL_ATHENA_ENABLE=0`；
- 16 kHz、S16、双麦采集，DMIC 接口为 `E_MI_AI_IF_DMIC_A_01`，回声参考为 `E_MI_AI_IF_ECHO_A`；
- HDI period 为 `4 × 10 ms = 40 ms`；
- MIC gain 为约 `+20 dB`，REF gain 为约 `-12 dB`；
- SEVC REF delay buffer 当前配置为 `0`；
- `SEVC_API_New(..., 16000, 1, 0, 1)` 表明运行时启用 NR、关闭 NN、启用 AGC。

`modules/aispeech/sevc/include/sevc_config.h` 配置为 2 MIC + 1 REF、35 mm、3 个 beam。硬件间距与 AISpeech 资源参数一致，没有发现“35 mm 资源选错”的证据。

### 2. 生产 KWS 是 iFlytek QIVW

当前生产唤醒通过 `modules/ai/wakeup_test/chenyf/wakeup_test.cpp` 调用 iFlytek `QIVWAudioWrite`，资源路径为 `wakeupresource.jet`，当前阈值为 `ivw_threshold=0:1200`。仓库中的 AISpeech KWS 不是当前生产路径，也没有确认“小窝小窝”的 AISpeech 专用资源。

### 3. QIVW 状态机存在确定性错误

`g_s32AudioStat` 初始值是 `MSP_AUDIO_SAMPLE_FIRST`，而不是 `MSP_AUDIO_SAMPLE_INIT`。首个有声批次会因此进入 `MSP_AUDIO_SAMPLE_CONTINUE`。既有设备日志直接记录首个 `QIVWAudioWrite` 为 `stat=2`，而 `msp_types.h` 定义 `2` 为 `CONTINUE`。

静音启动时，现有逻辑还可能重复写入 `FIRST`，之后再写 `LAST`。这违反 FIRST/CONTINUE/LAST 的会话边界语义，应在任何 VAD 或 KWS 换型前修复。

### 4. QIVW 实际按约 200 ms 聚包

设备日志显示单次入队 `last_size=1280` bytes，对应 16 kHz、S16、mono 的 40 ms PCM；代码每 5 次回调才调用一次 QIVW，日志写入大小为 6400 bytes，因此喂流粒度约为 200 ms。

同一日志长期显示 `drop=0`、队列深度通常为 1 或 2。当前证据不支持 SHM 传输丢帧或采样率错误是主要原因；“传输层丢帧”是本次被证伪的优先路径。

### 5. AISpeech 新 NR VAD 的初始评估快照未闭环

本节保留首次评估时的历史证据；其“结构/API 未闭环”状态已由下文“NR VAD v2 实现归档增补”更新，不应继续解释为当前源码状态。

首次评估看到的新 `sevc_nr.c` 已加入多频带 SNR、NR gain、attack/release、双阈值 hysteresis、speech onset、hangover、稳态噪声检测和三套 profile。默认 balanced profile 在 16 ms 内部帧下约对应：

- 噪声初始化 80 ms；
- onset 32 ms；
- hangover 128 ms；
- 稳态噪声判定 384 ms。

但当前 `SEVC_NR_S` 定义缺少新源码使用的 VAD 字段，`sevc_nr.h` 缺少 `SEVC_NR_VadGet()` 声明；`libhdi.so` 生成时间早于相关源码修改时间，`make.log` 中也未找到该 VAD 源文件的构建记录。因此不能声明板端已经运行或验证了这版 VAD。

`SEVC_API_FeedProcess()` 当前导出 AGC 平滑后的二值 VAD，而非 NR 原始 probability，并与 AGC 运行标志耦合。后续应独立暴露 probability、binary state、VAD source 和 profile。

### 6. 35 mm 双麦的物理能力有限

35 mm 阵列在 16 kHz 下的最大双麦时差约为 102 微秒，即约 1.63 samples；空间混叠边界约为 4.9 kHz。两麦 delay-and-sum 在理想非相关噪声下的阵列增益约为 3 dB，不能期待仅靠双麦获得数量级提升。

源码中没有发现运行时从三个 beam 中动态选择最佳 beam；主输出和 blocking 输出按固定顺序进入后级。因此 MIC 顺序、极性、分数延时、结构遮挡、用户方位和资源假设方向都需要板端标定。

### 7. SSC305 的 IPU SDK 能力匹配，但 KWS 集成未就绪

`SGS_IPU_SDK_24091114` 文档标记 `S02.0.5_verified_24091114 (iford) for 305, 308`。S02 release note 覆盖 ONNX/TFLite 转换、DepthwiseConv、1D Depthwise、LSTM/GRU、S16/F32 raw tensor 和量化修复，具备运行小型 KWS 网络的基础能力。

厂商 `volc_demo.cpp` 展示了 `IaaKws`、`kws_c32m.img`、`kws.graph`、`kws.dict` 和运行时 keyword array，说明存在厂商 IPU KWS 路线。但示例的 1280-sample 输出缓冲被四次按 400 samples 读取，最后一次会读到 1599，越界 320 samples；示例还获取了 `input_len` 却没有按返回长度组织输入。当前 SourceCode 中也未找到完整 `AudioKwsProcess.h` 和配套 KWS library，不能作为直接投产代码。

## 推断与建议

以下内容是基于源码和日志的工程推断，不是板端效果事实：

1. 当前漏唤醒和高延迟的最优先原因是 QIVW 状态错误、200 ms 聚包和 VAD 硬门控，而不是 VAD 模型先进程度不足。
2. `s32RefDelayBufLen=0`、MIC `+20 dB` 和 REF `-12 dB` 未经测量，AEC 失配、clipping 或参考信号幅度不足可能显著影响后级 KWS。
3. “窝”包含持续元音，balanced profile 的约 384 ms 稳态噪声机制可能对拉长元音、儿童声或远场低能量说法产生风险，需要专门语料验证。
4. 面向人耳“更干净”的强 NR/AES/AGC 可能改变 KWS 所需谱形，因此 KWS 与云端 ASR 应采用不同处理强度。

## 方案决策

### 短期推荐

1. 保留 AISpeech AEC/BF/NR 作为当前 AFE 基线。
2. 把 QIVW 初始状态改为 INIT，严格按 FIRST、CONTINUE、LAST 发送。
3. 在确认 QIVW 支持的输入长度后，把 200 ms 聚包改成 20–40 ms 连续喂流。
4. 本地 KWS 不由 VAD 硬切；若因功耗必须门控，保留 300–500 ms pre-roll 和 500–800 ms hangover。
5. 补齐 AISpeech VAD 结构/API，clean rebuild `libhdi.so`，记录源码、二进制和资源 hash。
6. 将 TEN-VAD INT8 MNN 作为 CPU shadow challenger；`ten-vad.mnn` 实际是 CSV，真正模型是 `ten-vad-int8.mnn`。

### 中长期推荐

采用：

```text
MIC0/MIC1/REF
  → 同步、极性、增益、REF delay 标定
  → AEC
     ├─ KWS 轻处理路径：BF/轻 NR → ring buffer → 连续 KWS
     ├─ ASR 路径：完整 SEVC/AGC → VAD endpoint/upload gate
     └─ 诊断 taps：raw、post-AEC、post-BF、post-NR
```

KWS 模型建议 CPU 计算 log-mel，IPU 运行 INT8 DS-CNN 或 TC-ResNet 类静态卷积网络；优先使用静态 4D tensor、Conv2D/DepthwiseConv，减少 transpose、复杂广播和多分支 fan-out。BC-ResNet 只作为精度与规模参考，不直接照搬其广播结构。

厂商 `IaaKws` 在厂商补齐头文件、库、授权、自定义关键词生成流程并修复示例后，可作为最快 IPU POC。若厂商方案无法达到“小窝小窝”的 FRR/FAH 目标，再进入自研 S02 KWS。

## 候选方案定位

| 方案 | 长期定位 | 边界 |
| --- | --- | --- |
| AISpeech SEVC | 当前 AFE 主基线 | 需完成标定、模块消融和可追溯构建 |
| SigmaStar IAA AEC/APC | 板端厂商 AFE 对照组 | 不等同于完整 35 mm 双麦 BF |
| WebRTC APM | AISpeech AEC 不达标时的成熟 fallback | 需移植、CPU 评估，且无现成 35 mm BF |
| Athena Signal | 离线 AFE reference | 缺少 SSC305 ARM 实时证据 |
| TEN-VAD | 最优 CPU shadow VAD challenger | 初期不用于硬门控 KWS |
| libfvad | 传统轻量基线 | 只作下限参考 |
| 本地 Silero/vad2 | 不建议产品化 | 当前代码、依赖、架构或许可未闭环 |
| QIVW | 修复后的短期 KWS 主方案 | 阈值 1200 必须通过 DET/FAH 扫描验证 |
| sherpa-onnx KWS | CPU open-vocabulary golden reference | 无 SigmaStar backend |
| SigmaStar IaaKws | 条件式快速 IPU POC | 依赖不完整且示例有越界 |
| 自研 S02 KWS | 中长期最优可控方案 | 需要训练数据、量化和系统调度投入 |
| RKNN embedding KWS | 只借鉴 ring-buffer 架构 | Rockchip 二进制不能移植到 S02，500 ms shift 过大 |

## 2026-07-18 NR VAD v2 实现归档增补

### 状态结论

针对板端“人声极难触发、咳嗽和键盘声相对容易触发”的新反馈，AISpeech NR 链路已形成一版不依赖 NN 的 NR VAD v2 源码候选，并完成 ARM 模块级构建和二进制审计。

当前可以确认的是：

- NR VAD v2 源码和独立 `libaispeech` module library 已构建通过；
- AGC 使用 fast VAD，QIVW/外部读取使用 slow wake VAD，避免一个状态同时承担增益控制与唤醒门控；
- 固定状态内存增量为 40 bytes，不新增 FFT、heap 或逐帧动态内存；
- 新生成库尚未同步到应用实际链接的 third-party AISpeech 库，HDI 也尚未接出 diagnostics，因此设备当前不能视为已运行该候选；
- 没有同板 A/B 证据证明人声 FRR、咳嗽/键盘误触发、QIVW CPU 或总 CPU 已改善。

Gate 为：源码与 module library `pass`；app 集成和设备效果 `needs-integration-and-device-validation`。

### 问题背景与适用边界

此前固定出现约 `79 ms speech + 1 ms silence` 的海量边沿，根因是 HDI 在每个 128-sample 半帧后上报 VAD，而 SEVC 每累计 256 samples 才产生一次新结果。该伪边沿问题与声学分类能力是两类问题：前者修复事件节拍，后者仍需改进 NR VAD 特征和状态机。

后续设备反馈表明，修正节拍后 NR VAD 仍偏向瞬态能量，低能量或远场人声的 probability 不足，而咳嗽、敲击等宽带瞬态更容易越过阈值。NN VAD 的观察效果较好，但不能简单切换为 `NR=0/NN=1/AGC=1`：当前 AFE、AGC、VAD 输出语义、资源配置和 QIVW 门控存在耦合，直接切换会改变声学前端和资源基线，且没有完成板端资源与回归验证。

因此本候选限定为“继续优化现有 NR 链路 VAD”，不把它解释为 NN VAD 替代方案，也不把通用 VAD 当作咳嗽/键盘专用分类器。咳嗽具有真实语音相似谱形，仅依赖 VAD 不保证完全拒绝，最终仍需由 KWS 分数和 hard-negative 语料控制误唤醒。

### 设计决策

1. **中频优先的 8-band 固定点评分**：由等权 SNR 平均改为权重 `{2, 4, 5, 5, 4, 3, 2, 1}`，同时统计 active bands、persistent bands、mid bands、mid-band ratio 和 frame transient。目标是增加连续语音中频结构的贡献，降低单次宽带敲击对总分的支配。
2. **瞬态惩罚**：当能量变化大、持续频带不足或中频占比不足时下调候选分数。该规则只减少短促脉冲的优先级，不承诺区分所有咳嗽和语音。
3. **候选阶段保护 noise PSD**：fast VAD、至少两个 active bands 或低阈值 probability 任一满足时，先冻结快速噪声学习，避免弱语音前 1--2 帧被吸收到 noise PSD 后分数自锁在低位。
4. **延长稳定噪声确认**：noise-safe、balanced、speech-safe profile 分别使用 64、96、128 帧稳定确认。进入受控噪声适配后使用 profile 的 SPP 上限更新，不再立即清空全部 VAD 状态。
5. **双时间尺度状态**：fast AGC/NR VAD 用较短 onset 和 hangover，slow wake VAD 使用更严格的频带持续性、较长确认和保持。AGC 不再依赖外部唤醒门控状态，QIVW 则读取更保守的 slow state。
6. **可观测性优先**：新增 `SEVC_API_VadDiagnosticsGet()`，导出 instant/smooth/transient/mid ratio、active/persistent/mid bands、AGC/wake state 和 noise-update state，便于板端记录真实分布后调参。

### 默认 noise-safe 参数

| 项目 | 默认值 | 16 kHz、256-sample 帧下的含义 |
| --- | ---: | --- |
| fast high / low | 16% / 12% | AGC/NR 双阈值 |
| wake high / low | 18% / 12% | 外部唤醒门控双阈值 |
| fast onset / hangover | 2 / 10 帧 | 约 32 ms / 160 ms |
| wake onset / hangover | 6 / 12 帧 | 约 96 ms / 192 ms |
| persistent-band 确认 | 3 帧 | 约 48 ms 的频带持续性 |
| stable-noise 确认 | 64 帧 | 约 1.024 s 后才允许受控适配 |

这些是待板测的初始值，不是量产阈值。QIVW 如启用硬门控，仍应保留 pre-roll 和 tail；不能用缩短 ring buffer 的方式抵消 VAD onset 延迟。

### API、ABI 与资源影响

- `SEVC_API_FeedProcess()` 的 C 签名和 0/1 返回 ABI 不变，但 NR 路径的返回语义调整为 slow wake state，属于需要集成方确认的行为变化。
- `SEVC_API_VadProbabilityGet()` 继续返回二值门控前的平滑 Q24 probability。
- 新增 `SEVC_API_VadDiagnosticsGet()`；未调用时不增加逐帧日志或外部缓存。
- `SEVC_NR_S` 从 92 bytes 增至 132 bytes，固定增加 40 bytes，仍低于 1 KiB 预算。
- 新逻辑复用 NR 已有 FFT、noisy power、noise PSD 和 gain；源码负搜索未发现新增 heap、FFT 或逐帧动态分配路径。

### 验证证据

| Command | Exit Code | Result Summary | Evidence Path | Layer |
| --- | ---: | --- | --- | --- |
| `rtk make -j4 DEP=modules/aispeech modules/aispeech_lib_all NC=1` | 0 | `sevc_nr.c`、`sevc_func.c`、`sevc_api.c` 完成 ARM 编译并生成 static/dynamic module 库；新增路径无编译 warning。 | PCR02 workspace | Module build |
| 6 个变更 C/header 的 `rtk clang-format --dry-run --Werror` | 0 | 目标修改区间通过格式门禁。 | PCR02 workspace | Source format |
| ARM `nm -D -S` | 0 | dynamic module 库导出 `SEVC_API_VadDiagnosticsGet`、`SEVC_NR_AgcVadGet` 和 `SEVC_NR_VadProbabilityGet`。 | generated `libaispeech.so` | Binary audit |
| ARM `objdump` on `SEVC_NR_LocMemSizeGet` | 0 | 固定内存立即数为 `132 (0x84)`。 | generated `libaispeech.so` | Memory audit |
| `rtk cmp -s` generated vs third-party library | 1 | 预期负结果：应用链接目录仍是旧库，新候选尚未进入最终 app。 | local artifacts | Integration boundary |

本地验证制品 SHA256：dynamic `9cee377785126a4bdfed2d31378939631d7fab1047ea615a81c708b8501f9e52`；static `75bdb6a2de0a7a644622fefc2f7d83c4b6a385b3a5410ee5851cf62b6f38d270`。这些 hash 仅绑定本次本地 module build，不是发布或设备部署基线。

### 集成阻塞与下一步

1. 按明确文件清单同步 AISpeech 公共头和新 static/dynamic library 到应用受管链接目录，clean rebuild 最终 app，并重新记录最终 ELF、库 hash 和符号；不得用整目录覆盖混入无关制品。
2. HDI 当前 VAD callback 的 userdata 仍为 `NULL`。应接入 diagnostics snapshot，并在 `app_main` 保留每个真实 VAD edge 输出，同时用周期统计报告 probability、bands、transient、noise-update、feed ratio 和 stale/fail-open；禁止恢复半帧重复上报。
3. 使用相同 PCM/声场依次测试 `off`、`shadow`、`on`。先在 shadow 模式验证事件节拍、状态和分数，再启用 QIVW 硬门控，避免 VAD 问题与 KWS 问题相互掩盖。
4. 同一批“小窝小窝”正样本和静音、连续环境噪声、键盘、敲击、咳嗽、电视人声、设备提示音负样本，记录 FRR、FAH、关键词结束到唤醒 p95、QIVW feed ratio、QIVW CPU、总 CPU、RSS 和 24 小时 drop。
5. 正常 256-sample 事件节拍应约为 62.5 次/秒；若再次出现约 125 次/秒或固定半帧翻转，应先回查 HDI 调用契约，而不是调 VAD 阈值。
6. 若人声仍低于 wake high threshold，优先依据 diagnostics 对比 `smooth`、`mid ratio` 和 persistent bands，再单变量调整权重或 wake threshold；若键盘只表现为高 transient、低 persistent bands，则优先调整瞬态惩罚或持续性，不应同时改多个参数。

### 回退边界

- 在 app 集成前，回退等价于继续使用现有 third-party AISpeech 库；不需要改变设备数据格式。
- 集成后若设备指标回退，先切到 QIVW `shadow/off` 保持连续喂流，再恢复上一版受管 AISpeech 库并重新链接；不得仅替换运行库而不核对公共头和最终 ELF。
- 本增补没有执行 install、image、OTA、设备写入、commit、push 或发布操作。

### 增补归档证据

- Source：2026-07-18 当前工程会话的 AISpeech 源码修改、ARM module build、符号/反汇编、制品 hash 和集成路径审计。
- Topic：`pcr02-aispeech-nr-vad-v2-implementation`。
- Archive Candidate Path：`projects/xcrz-sigmastar-demo/archive/reports/2026-07-18-pcr02-audio-wakeup-afe-vad-kws-ipu-evaluation.md`。
- Sanitization：未复制原始音频、完整串口日志、网络配置、凭证、二进制正文、模型、构建 cache 或运行时状态。
- Provenance：项目源码、模块构建输出和 `projects/xcrz-sigmastar-demo/validation/2026-07-18-pcr02-qivw-vad-short-term-implementation-validation.md`。
- Verification：源码与 module library 通过；app 集成、板端 A/B、资源降幅和长期稳定性待验证。
- Memory Candidate：no；未提升到 memory、AGENTS、current 或 decision。
- Gate Result：archive candidate 可更新；效果/发布结论为 `needs-integration-and-device-validation`。

## 单变量验证计划

1. **喂流协议**：只修状态机；再只改 200 ms 为 20/40 ms；再对比连续 KWS、VAD 硬门和 VAD+pre-roll。
2. **硬件标定**：保存同步 mic0/mic1/ref，检查 clipping、RMS、极性、通道顺序、频响；用 chirp/MLS 互相关扫描 REF delay，并以 ERLE 与双讲失真确定 gain/delay。
3. **AFE 消融**：raw best MIC、AEC、AEC+BF、AEC+BF+NR、full AISpeech、SigmaStar IAA、WebRTC、Athena offline。
4. **VAD shadow**：比较 AISpeech profiles、TEN-VAD 阈值、libfvad modes 和标准 Silero reference；记录 probability、onset miss、尾音覆盖和 false-active。
5. **KWS DET**：同一 PCM 下扫描 QIVW 阈值，并对比 sherpa、IaaKws、自研 S02；使用 FRR、FAH、关键词结束到触发延迟，不使用普通 accuracy 代替。
6. **系统压力**：YOLO/PIDNet 并发下测试 KWS/IPU p50、p95、p99、视觉 FPS、24 小时 drop 和内存增长；IPU device/channel 生命周期应集中管理。

## 语料与建议门槛

- 基础正样本至少 100 人 × 10 次自然说法，按 speaker 分离 train/dev/test；结合距离、角度、SNR、回声和混响扩展到至少 5000 条评估 utterance。
- 工程 hard negative 至少 100 小时，发布阶段建议累计 500 小时以上。
- 重点覆盖“小窝”“小沃”“小喔”“小我小我”“晓我晓我”、儿童声、方言、电视/音乐、产品扬声器自身播放和远端通话。
- 建议初版门槛：FAH 不高于 0.05 次/小时；0.5–1 m 安静 FRR 不高于 3%；3 m 安静 FRR 不高于 8%；目标噪声/回声 FRR 不高于 12%；关键词结束到触发 p95 不高于 500 ms；24 小时音频队列 drop 为 0。
- 100 小时负样本零误唤醒时，按 Poisson rule of three，95% 置信上界仍约为 0.03 FA/h；100 小时只构成最低工程验证量。

## Evidence Index

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
| --- | ---: | --- | --- | --- | --- |
| `rtk rg -n "AI_SS_ALGO_ENABLE|AI_EXTERNAL_SEVC_ENABLE|FRAME_NUMBER|s32RefDelayBufLen|SEVC_API_New" modules/hdi/src/hdi_audio/hdi_ai.c` | 0 | 确认生产 AFE 开关、40 ms period、REF delay=0 和 NR/NN/AGC 运行标志。 | `workspace://xcrz-sigmastar-demo/modules/hdi/src/hdi_audio/hdi_ai.c` | Project Source | current source snapshot |
| `rtk rg -n "SEVC_BF_MIC_DISTANCE|SEVC_BF_BEAM_COUNT|SEVC_MIC_CHAN|SEVC_REF_CHAN" modules/aispeech/sevc/include/sevc_config.h` | 0 | 确认 2 MIC、1 REF、35 mm、3 beam。 | `workspace://xcrz-sigmastar-demo/modules/aispeech/sevc/include/sevc_config.h` | Project Source | AISpeech configuration |
| `rtk rg -n "MSP_AUDIO_SAMPLE_FIRST|QIVWAudioWrite|ivw_threshold|每5帧" modules/ai/wakeup_test/chenyf/wakeup_test.cpp` | 0 | 确认 QIVW 状态机、5 帧聚包和阈值 1200。 | `workspace://xcrz-sigmastar-demo/modules/ai/wakeup_test/chenyf/wakeup_test.cpp` | Project Source | production KWS path |
| `rtk rg -n "QIVWAudioWrite count|last_size=1280|drop=0" <local-serial-log>` | 0 | 首次写入 stat=2、每次写 6400 bytes、入队 1280 bytes、长期 drop=0。 | local-only serial log reference; raw log not copied | Device Log | capture 2026-07-15 |
| `rtk rg -n "SEVC_NR_VadGet|fVadSmooth|afVadBandSmooth" modules/aispeech/sevc` | 0 | 新 VAD 源码使用了结构体中不存在的字段，且头文件缺少 API 声明。 | `workspace://xcrz-sigmastar-demo/modules/aispeech/sevc` | Project Source | VAD readiness blocker |
| `rtk rg -n "sevc_nr|libhdi|libai" make.log` | 1 | 构建日志中未发现新 VAD 源文件或相关库构建记录；作为负结果保留。 | `workspace://xcrz-sigmastar-demo/make.log` | Project Build Evidence | negative path |
| `rtk sed -n '1400,1485p' ReleaseNote.txt` | 0 | 确认 S02.0.5 及 Depthwise/LSTM/GRU/量化修复。 | local vendor SDK `SGS_IPU_SDK_24091114/ReleaseNote.txt` | Vendor SDK | SSC305 IPU capability |
| `rtk rg -n "IaaKws_GetInputSamples|output_buff|i \* 400|IaaKws_Run" <volc_demo.cpp>` | 0 | 确认厂商 IaaKws 路线及示例最后一轮越界 320 samples。 | PCR02 platform sample `volc_demo.cpp` | Vendor Sample | IaaKws POC blocker |

## 外部参考

- TEN-VAD：<https://github.com/TEN-framework/ten-vad>，检索日期 2026-07-18；仅作为模型接口与部署能力参考，官方性能不能代替 PCR02 板测。
- WebRTC Audio Processing Module：<https://webrtc.googlesource.com/src/%2Bshow/refs/heads/main/modules/audio_processing/g3doc/audio_processing_module.md>，检索日期 2026-07-18。
- sherpa-onnx KWS：<https://k2-fsa.github.io/sherpa/onnx/kws/index.html>，检索日期 2026-07-18。
- BC-ResNet：<https://arxiv.org/abs/2106.04140>，检索日期 2026-07-18；只作为高效 KWS 网络研究参考。

## 当前状态与复核条件

- 归档状态：`reviewing`、`manual_validation_pending=true`。
- 可复用内容：源码事实、已发现的喂流缺陷、候选方案定位、实验设计和指标口径。
- 不可复用为事实的内容：任何“某方案已经更好”的性能结论、建议阈值、板端 CPU/IPU 占用和最终 FRR/FAH。
- 复核条件：完成状态机和聚包修复，保存可回放三通道 PCM，完成同语料 AFE/VAD/KWS A/B，并补充视觉并发下的 IPU 压力证据。
- Promotion：none；不得自动提升到 current、decision、AGENTS 或 memory。

## Archive Evidence

- Source：2026-07-18 当前会话的源码、厂商 SDK、候选方案与设备日志审计。
- Topic：`audio-wakeup-afe-vad-kws-ipu-evaluation`。
- Sanitization：完整日志、二进制、模型、凭证、私有端点和工作区过程噪声未复制。
- Provenance：项目源码、设备日志摘要、厂商 SDK release note、官方外部资料。
- Verification：已完成源码检索、日志关键字段核对、文件时间和构建日志反向核验；板端统一 A/B 待补。
- Memory Candidate：no；未写入 memory，也未产生 AGENTS 候选。
- Gate Result：作为 `reviewing` archive candidate 可落盘；作为板端效果或发布结论为 `needs-fix`。
