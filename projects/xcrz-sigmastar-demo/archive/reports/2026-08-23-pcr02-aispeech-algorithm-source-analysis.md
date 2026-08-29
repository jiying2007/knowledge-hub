---
id: xcrz-sigmastar-demo-pcr02-aispeech-algorithm-source-analysis-20260823
title: PCR02 modules/aispeech 算法级源码分析
kind: project-archive
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/archive/reports/2026-08-23-pcr02-aispeech-algorithm-source-analysis.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
captured_at: '2026-08-23'
last_verified: '2026-08-26'
review_after: '2026-11-23'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; source audit does not authorize runtime replacement, deployment, or production acceptance
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-08-23'
manual_validation_pending: true
memory_candidate: false
tags:
- pcr02
- aispeech
- sevc
- aec
- beamforming
- gsc
- nr
- agc
- vad
- fsmn
- wakeup
- source-audit
- algorithm-analysis
source:
  type: current-workspace-source-audit
  from: workspace://xcrz-sigmastar-demo, modules/aispeech and HDI/QIVW integration static audit on 2026-08-23
  source_sha256: c1d6eaf06e11f8cccbe48e0499b09a7df5996a6f6d7ac27149cb9dffed2da5db
  temporary_source_retained: false
summary_zh: 审计 modules/aispeech 的定点 SEVC 与 FSMN Wakeup，并记录 master 公共 AEC/BF/AES 加 NR/NN+AGC 双尾链、HDI/API 硬边界集成及主机/ARM验证边界。
evidence_strength: source-audit+arm-elf-symbol-audit
evidence_refs:
- modules/aispeech/lib.mk
- modules/aispeech/sevc/include/sevc_config.h
- modules/aispeech/sevc/src/sevc_func.c
- modules/aispeech/sevc/include/sevc_api.h
- modules/aispeech/sevc/src/sevc_api.c
- modules/aispeech/tests/afe_audio_corpus_regression.c
- modules/aispeech/tests/audio/README.md
- modules/aispeech/tests/audio/corpus-manifest.json
- modules/aispeech/tests/audio/corpus.sha256
- modules/aispeech/wakeup/res/resource.c
- modules/hdi/src/hdi_audio/hdi_ai.c
- modules/hdi/src/hdi_plat_ss/ssplat_file.c
- tests/hdi_wav_writer/hdi_wav_writer_test.c
- modules/app/src/app_diag/provider/app_diag_ai_provider.c
- modules/api/src/api_audio_pipe/api_audio.c
related:
- projects/xcrz-sigmastar-demo/archive/reports/2026-07-18-pcr02-audio-wakeup-afe-vad-kws-ipu-evaluation.md
- projects/xcrz-sigmastar-demo/validation/2026-07-18-pcr02-qivw-vad-short-term-implementation-validation.md
---

# PCR02 `modules/aispeech` 算法级源码分析

## 结论与边界

`modules/aispeech` 提供两套端侧定点算法：`SEVC` 多麦声学前端和 `wakeup/wtk` 的 FSMN 唤醒词引擎。它不是通用语音识别系统；它的输出是增强后的单声道 PCM、二值 VAD 和（仅在 Wakeup 链被调用时）唤醒状态/JSON。

2026-08-23初次审计时，PCR02实际链接/部署的是`libs/3rdparty/aispeech/lib/libaispeech.so`，而不是本目录构建产物；这是历史基线，不再是2026-08-26源码候选。当前`pcr02/dep.mk`已纳入`modules/aispeech`，HDI/API与应用顺序构建并静态链接master双尾链实现，旧third-party发布项已移除。该源码制品仍不能替代板端音质、VAD或唤醒精度验证。

现网库为 ARM 32-bit EABI5 ELF，BuildID `cf13ac432f44ad6d3e25dd8a857d9468a06727ca`，导出 `SEVC_API_FeedProcess`。当前源码实现该函数，但公开 `modules/aispeech/sevc/include/sevc_api.h` 未声明它，已构成源码/API 漂移风险。

## 端到端数据流与时基

```text
16 kHz, S16, 2 MIC + echo reference
  -> HDI 每 8 ms 输入 128 samples/channel
  -> 累积为 SEVC 256-sample 内部帧（16 ms）
  -> window + FFT + AEC/AES/BF/GSC/BF-post/NR-or-NN/AGC
  -> 256-sample enhanced mono PCM + VAD
  -> HDI 单声道 reader
  -> 诊断 QIVW（而非 AISpeech wakeup API）
```

HDI 以 16 kHz、16 bit、双麦采集，输入块是 128 samples/channel（8 ms）。SEVC 配置在宽带模式使用 `frameShift=256`（16 ms），故 HDI 缓存两个输入块后才真正执行一次 `SEVC_API_FeedProcess`。其输出以 128-sample 单声道块回填，满足上游 8 ms 节拍，但必然有至少一帧算法缓冲及 STFT 重叠带来的延迟。任何 VAD callback 必须只在该 256-sample 帧产生新结果时发布；若在每个半帧都发布，会制造“旧值/默认值交替”的伪边沿。

诊断 QIVW 门控使用 1280-byte 单声道块（40 ms）、480 ms pre-roll、400 ms tail 和 200 ms VAD stale fail-open。它消费增强 PCM，并以 HDI 的 VAD 事件决定 `on/shadow/off` 下的喂流，不直接调用 `wakeup_new`/`wakeup_feed`。所以当前产品是“AISpeech AFE + 外部 QIVW KWS”，不是“AISpeech AFE + AISpeech KWS”。

## SEVC：算法结构

### 输入、阵列与定点实现

默认配置为 2 MIC + 1 REF、16 kHz、35 mm 麦距、3 beam。PCM 为 16-bit interleaved；API 将输入拆成两路近端麦和一路回放参考。核心路径使用 Q 格式定点数、预计算窗函数和固定内存定位器，目的在于避免逐帧 `malloc`，使 ARM 端时间和内存更可预测。

16 kHz 下声速约 343 m/s，35 mm 双麦最大传播时差约 102 microseconds，即约 1.63 samples。该几何条件只能提供有限空间分辨率：理想非相关噪声下两麦阵列增益约 3 dB，且约 4.9 kHz 以上开始存在空间混叠风险。3 beam 是固定阵列资源的空间候选，不等同于动态声源定位；安装方向、麦克风极性、增益、通道序和遮挡一旦偏离资源假设，BF/GSC 的收益会变为失真或漏唤醒风险。

### 时频变换

`SEVC_Feed` 先对 MIC/REF 做增益预处理，再将当前帧与上帧残留拼接，施加平方根 Hann 窗，执行 FFT。频域处理后的单声道结果经 IFFT、窗重叠相加及后强调恢复时域。该结构的关键性质：

- 频域模块共享同一帧和谱估计，计算复用好；
- 需要跨帧状态（窗重叠、AEC 自适应滤波器、噪声 PSD、AGC 状态）；reset、音频断流、REF 丢失必须显式清状态；
- 任何改变 FFT 长度、采样率或 frame shift 的配置，都必须同时验证资源、窗、模型、阈值和所有时间常数，不能只改一处宏。

### AEC 与 AES

AEC 使用 REF 估计每个 MIC 上的播放回声，输出误差信号；AES 再基于 MIC/误差/echo 与 REF-VAD 进行回声抑制。AEC 成败主要受 REF 真实性和对齐支配：播放前的数字 PCM 必须是实际扬声器路径的合适参考，并按实测声学延迟补偿。当前 HDI 的 `s32RefDelayBufLen=0` 只是实现参数，不是“零延迟已标定”的证明。

当 REF 缺失、音量裁剪、通道拿错或延迟不匹配时，AEC 可能收敛到错误解；强 AES 虽可让人耳觉得更安静，却可能压制关键词元音和共振峰。因此 AEC/AES 的验收不能只看主观静音，必须同时检查双讲、播放人声、关键词 FRR 和残余回声。

### BF、GSC 与后处理

BF 按 35 mm 双麦资源生成多个指向输出；GSC 以 blocking/noise reference 抑制非目标方向分量；BF-post 以噪声 PSD、后验/先验 SNR、语音存在概率等估计频点增益。源码中输出路径的模块顺序为 AEC/AES 后进入 BF/GSC/BF-post，随后进入 NR/NN 和时域重建。

这类“BF + GSC”组合的优势是能同时利用主波束和噪声参考，弱点是对两个麦克风频响/相位一致性非常敏感。两麦设备不应期望远场多说话人分离；它更适合提升目标正前方或预设方向的 SNR。应保存 raw、post-AEC、post-BF、post-NR 四个受控 tap 的短样本，按单变量消融定位问题，禁止一次调 BF、NR、AGC 和 KWS 阈值。

### NR、NN、AGC、VAD

传统 NR 使用频域噪声估计和增益下限抑制稳态噪声；NN 支路使用编译进库的 FSMN 资源预测增益。`lib.mk` 启用 `CONFIG_SEVC_NN_FSMN`，但 HDI 实例创建参数为 `NR=1, NN=0, AGC=1`，即现网意图是传统 NR + AGC，不应把编译到库内的 NN 能力误称为运行中。

AGC 根据 VAD/能量平滑调整输出音量。它可提高小声语音可听度，却会同时放大残余噪声；对 KWS 而言，过快攻击、过强压缩或过低释放时间均可能改变训练时未见的 log-mel 分布。建议将“人耳通话音质”和“KWS 特征稳定性”视为不同优化目标：前者可走完整 AGC/强后处理，后者优先稳定的轻处理分支或至少建立独立 A/B。

`SEVC_API_FeedProcess` 返回的 VAD 在当前实现中依赖 AGC 或 NN 的分支，输出为二值状态而非置信度。二值 VAD 适合门控，不适合精细调参；应保留 probability、VAD source、帧序号和新鲜度等诊断数据。特别是 VAD 不是咳嗽/键盘的语义分类器：瞬态宽带噪声会和语音发生特征重叠，最终误唤醒仍应由 KWS 的 hard-negative 语料和分数阈值控制。

## Wakeup/WTK：本地 FSMN KWS 链

Wakeup 子系统是完整的离线关键词检测器，而不是 SEVC 的 VAD 附属模块。它接收 PCM，完成特征提取和 FSMN 推理，再通过回调输出 `WAIT/WOKEN/ERROR` 与 JSON。

### 特征和模型

- 参数资源设定 300 ms 分析窗、200 ms 帧移、24 维 FBANK、Hamming 窗与 CMN；
- 使用 3 层 FSMN：输入维度 120，隐藏输出维度 32，输出 6 类；每层有 3 帧历史记忆；
- 词典为 `sil/speech/hai/jiao/wei/xiao`，资源中可见的目标短语是“小微小微”；
- 词典、阈值、持续时间惩罚、最大置信搜索与延迟唤醒均编译进 `wakeup/res/resource.c`。

FSMN 用有限历史帧替代循环网络的长递归状态，适合无 FPU 或 CPU 紧张的嵌入式端：模型参数可量化为 int8/int16，推理时延稳定、内存固定。但它也将采样率、FBANK 维数、窗长、前端增益、CMN 策略和关键词发音绑定为训练/资源契约。更换关键词、麦克风、语言或强行切换 24/40 mel 维都不是普通配置改动，需要重新训练或重新导出对应资源。

### 状态机与接口

`wakeup_new -> wakeup_start -> wakeup_feed* -> wakeup_end/reset -> wakeup_delete` 是基本生命周期；可注册关键词、特征和（编译开启时）VAD 回调。多通道 API 只在 `WAKEUP_NCHANNEL` 编译时可用，而当前 `lib.mk` 未开启该宏。唤醒 VAD 同样因 `WKP_VAD_DISABLE` 被定义而禁用，不能假定该子系统会产生可用 VAD 回调。

源码宏同时启用了 24/40 FBANK、400/480 Hamming 等互斥或重叠候选，最终实现依赖条件编译优先级决定生效项。应将“目标 profile”收敛为一份显式配置，避免不同编译环境得到不同的声学特征。

## 算法与产品方案评估

### 当前方案的合理性

在 SSC305 的 CPU 预算下，定点 STFT + 双麦 AFE 是低风险基线：它将复杂声学处理放在可预测的 ARM C 代码中，保持 QIVW 输入为 16 kHz 单声道。QIVW 门控有 pre-roll、tail 和 stale fail-open，避免 VAD 链失效时永久断流。该组合比把大模型直接塞入 NPU 更容易先闭环音频通路。

### 不可忽略的限制

1. 35 mm 双麦无法替代更大阵列或视觉/语义说话人选择；空间收益有物理上限。
2. AEC、BF、NR 和 AGC 都会改变 KWS 特征，不能仅按“降噪更强”决定参数。
3. VAD 硬门控会截断弱起始辅音；pre-roll 必须覆盖 VAD onset，且 shadow 结果要先于 on 模式决策。
4. 本地 AISpeech Wakeup 的可见资源是“小微小微”，不证明它能识别产品目标词，也不证明其授权、训练流程和量产资源已经具备。
5. 当前源码目录与预编译 `.so` 的构建和 API 不一致；替换库前必须完成 ABI、符号、资源和同语料 A/B。

## 推荐验证与演进

1. **建立可追溯基线**：记录现网 `.so` BuildID/hash、导出符号、公共头、HDI 最终 ELF 与输入/输出格式；明确模块源码、生成库、受管 third-party 库、image/OTA 是不同制品阶段。
2. **先做硬件标定**：用三通道原始 PCM 验证 MIC0/MIC1/REF 的顺序、极性、增益、裁剪与实际 REF delay；未通过前不要调模型阈值。
3. **做 AFE 消融矩阵**：raw、AEC、AEC+BF、再加 NR、再加 AGC；每格用同一关键词正样本、电视人声、音乐、键盘、咳嗽、风噪、双讲和播放场景测 ERLE/SNR、FRR/FAH、p95 延迟、CPU/RSS。
4. **门控先 shadow 后 on**：校验事件频率约为 62.5 次/s、无 stale fail-open 异常和预录词首丢失；再用 on 模式评估节流收益与漏唤醒代价。
5. **若替换 KWS**：本地 FSMN 先旁路影子运行，与 QIVW 比较检测错误；达到独立 DET/FAH/功耗门槛后才允许灰度。不要直接由 VAD 判定唤醒。
6. **若接管源码构建**：补齐缺失 `uda` 目录策略、API 声明、依赖图和导出符号校验；先重建模块库，再受控同步到链接目录并重链最终 app，最后才考虑 image/OTA。

## 验证记录与归档门禁

- 静态证据：检查了算法宏、SEVC 数据流和接口、Wakeup 资源、HDI/QIVW 调用链、PCR02 链接清单，以及 ARM `.so` 的 ELF/动态符号。
- 未执行：本次未编译、未覆盖 third-party 库、未创建 image/OTA、未部署设备、未进行 HIL 或 DET/FAH 测试。
- Gate：`reviewing / source-audit-only`。本文件可作为算法与集成边界的检索材料；不得提升为运行效果、发布批准或量产结论。

## 2026-08-23 产品约束增补：35 mm 双麦移动机器人、通话与讯飞双唤醒词

### 产品判定

产品为小型移动机器人，不应把耳机、手机或远场单麦的默认配置直接当作目标方案。它同时具有三个彼此冲突的声学目标：全双工通话要压低扬声器回声并保持上行自然度；移动底盘、风扇、碰撞和电机带来非平稳自噪声；“你好小窝”“小窝小窝”的关键词又要求保存词首、元音和音调相关的谱形。最强的系统结论是采用双输出路径，而不是让同一份强处理 PCM 同时服务通话和 KWS。

```text
MIC0/MIC1 + 数字播放参考
  -> 通道/极性/增益/REF-delay 标定
  -> AEC
     -> KWS 路径：BF/轻抑制 -> 固定环形缓存 -> 连续 QIVW 喂流
     -> 通话路径：BF/GSC/后处理/NR/AGC -> 上行编码
  -> 诊断 tap：raw、post-AEC、post-BF、post-NR
```

KWS 路径默认不采用硬 VAD 截断。VAD 可以控制低功耗状态或在 `on` 模式下减少 QIVW 输入，但必须保留足够 pre-roll，且 VAD stale 时 fail-open。理由是弱起始辅音很可能在 VAD 确认前出现；对关键词而言，一次被截断的词首比多送几十毫秒静音更危险。通话路径可采用更强 NR/AGC，因为其优化目标是可懂度和听感，而 KWS 路径的优化目标是与训练/注册时特征分布一致。

### 35 mm 阵列的可迁移资产与不可迁移项

`aispeech-earbuds` 中存在 `LUDA_*_2mic_35mm_home_3EntBeam` 资源和 35 mm BF resource，证明该代码库考虑过相同几何量级；并同时保留 15/18/20/25/29/30/33/35 mm 多个资源。这是“麦距属于模型/资源契约”的直接证据，而不是可直接复制系数的许可。

机器人与耳机在麦克风型号、壳体反射、麦孔位置、扬声器相对位置、底盘振动、近讲距离和目标方向分布上均不同。35 mm 只解决阵列时差标定的一部分；复制耳机 BF/GSC 权重可能在正前方有效、在机器人实际安装方向失效。必须先测 MIC pair 的幅相响应、极性、通道顺序、直达声 TDOA、扬声器到 MIC 的回声路径以及机械噪声谱，再决定是否使用 35 mm resource 作为初始候选。

耳机工程的 near-field profile 为 2 MIC + 1 REF，包含 AEC、BF、传统 NR 和 NN，而不启用 AGC；far-field profile 则为 1 MIC、无 AEC/BF，主要使用 NN。两者都不等于机器人目标。尤其 phone profile 是 3 MIC + 1 REF、29 mm、3 beam，不能下沉为双麦配置。对当前机器人，更合理的起点仍是 2 MIC + 1 REF、16 kHz、512 FFT、3 beam 的现有 SEVC 配置，再以消融实验决定是否保留 GSC、AES、NN 和 AGC。

### 讯飞自定义唤醒词与 AISpeech 本地唤醒的边界

当前产品关键词由讯飞 QIVW 自定义资源识别，产品词为“你好小窝”“小窝小窝”。耳机参考工程的 `lite-wakeup` 是另一套本地 FSMN 引擎，资源中可见 `resource.c_ni_hao_xiao_le` 与 `resource.c_xiao_wei_xiao_wei` 等示例。前者的音素词典含 `ni/hao/xiao/le`，与“你好小窝”的最后音节不同；后者是“小微小微”，也不是“小窝小窝”。所以这些文件只能用于理解资源形态、特征和后处理，不能当作产品词的替换模型，也不能据此推断讯飞词的阈值。

本地 WTK 方案为定点 FBANK + CMN + FSMN + 词典序列判决：示例资源使用 24 维 FBANK、300 ms 窗、200 ms 步，3 层 FSMN、120 维输入、32 维隐藏表示、6 个输出符号。FSMN 的有限历史记忆让它适合流式嵌入式推理，但关键词、音素词典、前端、阈值和时长惩罚必须共同训练/导出。对讯飞 QIVW，保持其官方自定义词资源为唯一生产判决器；AISpeech 本地 KWS 只应在获得“你好小窝/小窝小窝”合法训练资源和完整导出链后作为 shadow challenger。

### 训练仓的价值与当前缺口

`aispeech-training` 提供 FSMN、GRU、LSTM、Transformer 等序列模型以及 PyTorch 到 Kaldi nnet 的导出工具。FSMN 训练实现支持可配置左/右记忆阶数、stride、残差/高速连接和 `relu6`，适合构造因果或小 look-ahead 的流式 KWS。它说明可以训练小模型，但尚未证明“训练 checkpoint -> WTK `resource.c`/定点权重 -> SSC305 运行库”的自动可复现路径已存在；耳机工程的 `res2src` 与训练仓的 PyTorch→Kaldi 导出属于不同阶段。该中间转换、定点量化、CMN/FBANK 一致性、关键词 decoder 和 regression corpus 都必须纳入交付链。

建议本地 KWS 若立项，优先设计为 3 类/多状态小型流式 FSMN：silence/background、speech/filler、keyword states（两条关键词各自的状态序列），而不是直接把通话 VAD 当 KWS。训练正样本应覆盖至少不同说话人、声调、语速、距离、方位、机器人运动/静止、播放中/非播放中、房间混响和低电量风扇状态；hard-negative 至少包括相近音节、机器人提示音、电视/音乐人声、儿童声、咳嗽、敲击和电机瞬态。train/dev/test 必须按说话人、房间和录制批次隔离，禁止同一录音的增强版本跨集合泄漏。

### 推荐的阶段化算法决策

1. **近期量产主线**：保留讯飞 QIVW 为关键词决策器，修正/保持 FIRST-CONTINUE-LAST 流语义，采用 20--40 ms 连续 chunk；以 shadow 模式先观察 VAD 门控收益。
2. **声学前端基线**：AEC 是通话与播放时唤醒的必要能力；BF 以 35 mm 标定资源为候选；GSC/AES/强 NR/AGC 逐一消融。不要在无原始三通道证据时同步修改多个模块。
3. **双路径收敛**：上行通话可接受较强处理；KWS 默认走 post-AEC + 温和 BF/NR，维持词首和谱包络。若共享一路 PCM，优先为 KWS 保护特征，并另行评估通话听感。
4. **本地 FSMN 的进入条件**：完成关键词数据集、量化/资源转换、ARM bit-exact 回归、QIVW parallel shadow 和 DET 测试后，才可讨论替换或热备；不是仅凭训练代码和示例 resource 即可进入产品。

### 验收指标

KWS 必须分开报告每个词的 FRR、FAH（每小时）、关键词结束到事件的 p50/p95 延迟、按距离/方位/运动/播放条件分桶的结果，以及 VAD gate 的 feed ratio 和 fail-open 次数。通话必须报告 ERLE、双讲稳定性、近端语音失真、端到端延迟、CPU/RSS 和长时帧丢失。只有同一声学前端、同一语料、同一阈值下的 QIVW `off/shadow/on` A/B 才能量化 VAD 门控是否值得保留。

## 2026-08-23 SEVC 优化增补：回声残留与带噪唤醒低

### 静态代码定位：先修参考契约，不先调“降噪强度”

当前 HDI 明确关闭了 SigmaStar 自带 AEC（`AI_SS_ALGO_ENABLE=0`），而启用了外部 SEVC（`AI_EXTERNAL_SEVC_ENABLE=1`）。因此板端是否消回声主要取决于 SEVC，以及送入 SEVC 的 `pktEchoData` 参考信号。每次 SEVC 调用将两路近端 MIC 和一路 `pktEchoData` 拷入 256-sample（16 ms）帧；`s32RefDelayBufLen` 固定为 0。源码快照的 SEVC 默认又是 `SEVC_AEC_TAPS=1`、AEC/AES/BF/GSC/BF-post/NR/AGC 开启，而 HDI 创建参数为 `NR=1, NN=0, AGC=1`。

这给出两个高优先级风险，但不构成已在板端复现的结论：

1. `pktEchoData` 必须是与扬声器实际播放高度相关、采样率/声道/音量路径一致的数字参考；其名称不能证明这一点。若它是错误 DMA 通道、经过不同增益/重采样路径的信号，或在静音时被置零，AEC 无法收敛。
2. 零软件延迟和 1 tap 不是移动机器人扬声器--机壳--麦克风声学路径已经对齐的证据。DAC、功放缓冲、扬声器、壳体反射与采集 FIFO 产生的总延迟/混响可能超过当前自适应器的可覆盖范围。

因此，禁止以调低 QIVW 门限、加重 NR/AES 或提高 AGC 来掩盖回声问题。它们通常会同时抑制“你/好/小/窝”的弱音素，造成 FRR 上升，并在双讲时削弱近端人声。

### P0：可重复的三通道证据与判别准则

在不改变业务功能的诊断版本中，为同一时钟域保存短时、脱敏 PCM：MIC0、MIC1、`pktEchoData`、SEVC post-AEC、post-BF/NR/AGC，以及最终送入 QIVW 的单声道。不要将这些原始音频纳入 Git 或归档正文。每段记录 sample rate、frame index、播放音量、机器人状态和算法开关。

使用宽带扫频、MLS 或语音/音乐播放作远端激励，执行以下判别：

| 检查 | 成功标准 | 失败后的首要动作 |
| --- | --- | --- |
| REF--MIC 互相关 | 峰值稳定、可重复，且对应合理总延迟 | 检查 REF 取点、声道、极性、重采样与播放 FIFO |
| 对齐扫描 | 在互相关峰附近扫描整数 sample 延迟，残余回声能量最低点明显 | 将实测延迟引入 REF 环形缓冲；处理播放启动/切歌时 reset |
| ERLE | 单讲播放时按频段计算 `10log10(P_mic/P_error)`，并保存时间曲线 | 检查参考真实性、滤波器长度/步长和削波 |
| 双讲保护 | 近端说词叠加播放时，关键词频带及主观近端语音不被持续压低 | 检查 double-talk 检测、AES 与 GSC 侵蚀 |
| KWS 语料 | 同一 QIVW 词资源、同一阈值下，比较 raw/post-AEC/post-BF/post-NR/AGC 的 FRR/FAH | 定位第一个导致 FRR 恶化的模块，撤回或减弱该模块 |

先冻结一套“播放单讲、近端单讲、双讲、静音、机器人运动、风扇、电机、碰撞”录音矩阵；否则调参结果不可比较。音量档位也必须分桶，因功放非线性和扬声器饱和会生成非线性回声，线性 AEC 无法完全抵消。

### P1：AEC/AES 的优化顺序

1. **校验参考点与对齐。** REF 应尽可能取自送往扬声器的数字 PCM，并在增益、混音、限幅和采样率变换之后与物理播放路径相一致；不能用“播放前、另一采样率或另一声道”的近似数据替代。以互相关和 ERLE 选择 `s32RefDelayBufLen` 的起始值，而不是假定 0。固定延迟不足以覆盖抖动时，再评估滑动 delay estimator 或播放状态变化时的重新对齐。
2. **建立收敛状态机。** 播放开始、播放采样率/音量突变、REF 中断、AI overflow/underflow 后应 reset 或冻结自适应状态，并在一小段收敛期内不给出“回声已消除”的判断。避免旧滤波器把上一段播放路径学习结果带到新路径。
3. **仅在对齐后评估 AEC tap/步长。** 静态源码 `SEVC_AEC_TAPS=1` 是首先需要与供应商/现网 `.so` 版本核对的容量边界。若实际声学冲激响应长于该设置的能力，应优先采用与现网 ABI 匹配的多 tap/长回声路径配置或供应商资源；不能只任意放大 `MU`。步长过大常导致双讲发散，过小则跟踪不到机器人运动/音量变化。
4. **再调 AES，而非先调 AES。** AES 是残余回声抑制器，适合处理 AEC 未覆盖的残留；其低增益下限过激会吃掉关键词共振峰。以 ERLE、双讲近端失真和两条词的 FRR 联合选择抑制上限/下限；不能只依据静音时波形变小。

### P2：35 mm 双麦 BF/GSC 的正确用法

`sevc_bf.c` 固定引入名为 `phone_2mic_35mm_*` 的 BF 数据。其 35 mm 几何与产品一致，但 phone 声学模型不是机器人壳体标定；它应是初始候选而不是事实上的量产参数。

建议固定 AEC 后，按如下消融顺序选择空间处理：`post-AEC` -> `+BF` -> `+GSC` -> `+BF-post`。每次只改变一个模块。BF 对正面目标、横向噪声应有增益；若任意方位都出现关键词变钝、两麦差分异常或目标方向 FRR 上升，先检查 MIC 通道顺序、极性、幅相一致性和实际安装朝向。GSC 对两麦失配最敏感，双讲/播放下也可能把目标语音当干扰，故它不是“始终开启”的前提；若 `+GSC` 相对 `+BF` 没有统计收益，应关闭或改为通话专用路径。

35 mm 阵列无法从根本上分离低频同向电机噪声；应通过结构隔振、麦孔风噪控制、马达 PWM/风扇状态联动和针对性训练/噪声抑制共同处理。不要把机械噪声问题全部转化为更强的谱减法。

### P3：为 KWS 保留特征，而非复制通话链

当前单实例调用明确启用传统 NR 与 AGC、关闭 NN。NR/AGC 对通话可能有益，却会让 QIVW 看到与其注册/调优条件不同的动态范围和谱包络。建议将参数决策按输出目标分开：

- **KWS 候选输入：** `post-AEC` 或 `post-AEC+已验证 BF`，使用温和 NR；优先关闭或限制强 AGC、强 AES、GSC 和 BF-post，保持连续 16 kHz 单声道与既有 pre-roll/tail。
- **通话候选输入：** 在上述基础上继续评估 GSC、BF-post、NR、AGC，以 ERLE、双讲失真与可懂度验收。
- **实现策略：** 先用离线 taps 找到最佳 KWS stage；若它与通话最佳 stage 不同，再评估双 SEVC 实例或在 AEC/BF 后导出独立分支。双实例会增加 CPU/RSS 和资源/线程安全风险，必须先在 SSC305 实测实时率和长稳，不能仅据 PC 结果上线。

切换到 SEVC NN 不是单纯将 `NN=0` 改为 `1`：必须提供与实际库版本、16 kHz、特征、量化和资源格式一致的 NN 模型，并重新验证内存、CPU、关键词 FRR/FAH。传统 NR 与 NN 在 `sevcCfgReinit` 中互斥；严禁两者同时宣称生效。

### 参数实验设计与上线门槛

按如下顺序测试，任何一格出现明显双讲失真、FRR 上升或实时率不足即停止向下叠加：

1. REF/延迟正确的 AEC baseline（无 BF/GSC/NR/AGC）；
2. baseline + AES；
3. +BF；
4. +GSC；
5. 分别加入 BF-post、传统 NR、AGC；
6. 在资源和导出链齐全后，单独比较 NN 与传统 NR；
7. 仅将胜出组合接入 QIVW shadow，再进入 on 模式。

每一项都按“你好小窝”和“小窝小窝”分别报告 FRR、FAH/h、p95 检出延迟、播放单讲 ERLE、双讲近端语音 MOS/客观失真代理、CPU/RSS、丢帧率；按 0.5/1/2/3 m、正面/侧面、静止/行驶、扬声器音量、风扇/电机状态分桶。建议预先设定门槛：新方案必须不降低任一关键词的目标工作点 FRR，同时满足播放/双讲 ERLE 下限、FAH 上限和实时率余量，才允许灰度。

### 实施优先级

- **本周：** 打开受控 tap，完成 REF/MIC 相关性、延迟与削波检查；使用当前预编译 `.so` 的 BuildID 记录结果。
- **随后：** 固定延迟与 REF 后做 AEC/AES、BF/GSC、NR/AGC 的离线消融，先解决回声残留再调 QIVW。
- **最后：** 根据最佳 KWS stage 决定单/双支路；只有在本机资源模型和 ARM 回归齐全时才试 NN 或本地 FSMN KWS。

本节仍为源码和算法设计建议，未在设备上采样、测 ERLE 或执行 QIVW 评测；状态维持 `reviewing / source-audit-only`。

## 2026-08-24 产品双输出设计：KWS/ASR 轻处理，通话强处理

### 方案结论

以 `modules/aispeech` 为产品 SEVC 源码，推荐采用“一套公共 AEC/BF 核心、两个独立后处理输出”，不建议量产时运行两套完整 SEVC：

```text
MIC0 + MIC1 + playback REF
  -> 通道校准 / REF delay / STFT
  -> 公共 AEC（持续自适应、双讲保护）
  -> 公共 35 mm BF
       |-> LIGHT：保守 AES + 温和 NR + 独立 IFFT/OLA + limiter
       |            |-> QIVW KWS（常开、连续流、pre-roll）
       |            `-> ASR（唤醒后上传、独立 endpoint）
       `-> STRONG：GSC + 强 AES + BF-post + NR-or-NN + AGC
                    `-> 通话上行
```

公共 AEC/BF 避免重复 FFT、回声估计和波束计算，并保证两路使用同一 AEC 收敛状态。LIGHT/STRONG 必须各自拥有 AES/NR/NN/AGC、增益平滑、IFFT overlap-add 和输出缓存等可变状态，不能串行复用同一个后处理实例。

### 当前实现基线与新实现缺口

当前 HDI 将 SEVC 最终单声道 PCM 写入现有音频 pipe；Sensor `AudioFrameHub` 再发布为 `shm/audio/pcm`，格式为 16 kHz、mono、S16LE。归档 AI voice 源码显示 QIVW KWS 与唤醒后的 WebSocket ASR 都订阅此通道，所以“KWS 与 ASR 共用 LIGHT”与现有产品结构一致。

当前 `shm/audio/pcm` 仅能表达一类最终 PCM，`libaispeech.so` 也只允许构造时选择 NR/NN/AGC，且不导出 earbuds 的 middle callback；AEC/BF/GSC/AES/BF-post 主要由编译配置决定。这些只能作为迁移前基线，不能约束新接口。新实现必须在 `modules/aispeech` 内建立明确的 profile、状态所有权和输出契约，并同步替换 HDI、Sensor 和消费者；不能靠新增第二个回调或沿用旧通道缺省语义拼接出轻/强差异。

两套完整 `SEVC_API_New` 可用于原型 A/B，但不推荐量产：它重复 FFT/AEC/BF、增加 SSC305 CPU/RSS，两套 AEC 还会独立收敛；而现有 API 也只能让两实例在 NR/NN/AGC 上有差异。

### aispeech-earbuds 的迁移边界

- near-field profile 是 2 MIC + 1 REF、AEC、BF、NR/NN、AGC/AES 默认关闭，体现 LIGHT 的保真优先思路；但它是 28 mm、2 beam、佩戴式近讲，参数不可复制。
- phone profile 具有 AEC、BF、GSC、BF-post、NN、AES、AGC，功能组合可参考 STRONG；但它是 3 MIC + 1 REF、29 mm、384 frame shift，同样不可复制。
- earbuds 的 35 mm Home/3-beam 和当前 phone 35 mm BF resource 只能作为候选。机器人麦型号、壳体、麦孔和安装方向必须重新实测选型或标定。
- earbuds 有 wind-noise 能力可作后续参考，但当前产品仓没有同等已集成接口，不纳入第一阶段。

### 推荐 profile

| 模块 | 公共核心 | LIGHT：KWS/ASR | STRONG：通话 |
| --- | --- | --- | --- |
| MIC/REF 增益、延迟 | 实测标定 | 共享 | 共享 |
| AEC | 常开，维持同一状态 | 共享 error/echo estimate | 共享 error/echo estimate |
| BF | 35 mm 资源实测选型 | 共享主波束 | 共享主波束和 blocking output |
| GSC | 不进入公共核心 | 初始关闭 | 校准通过后开启 |
| AES | 共享只读 echo estimate | 保守增益下限 | 较强并保护双讲 |
| BF-post | 不进入公共核心 | 初始关闭或弱模式 | 开启并检查音乐噪声 |
| NR/NN | 运行时互斥 | 初期传统温和 NR | 通话专用 NR 或匹配 NN |
| AGC | 不进入公共核心 | 默认关闭，只用 limiter | 开启并按通话响度调节 |
| VAD | 只输出状态/诊断 | KWS 不硬门；ASR 独立 endpoint | 可用于 DTX，不能停止 AEC |

当前源码把 AEC/AES/BF/GSC/BF-post/NR/NN/AGC 都编译为能力，HDI 实例选择 NR=1、NN=0、AGC=1。目标实现应把“编译能力”和“输出 profile 的运行 mask”分开。

### SEVC 源码改造位置

推荐在 `sevcBfCbFunc` 得到 BF 主输出和 blocking output 后分叉：

1. 公共路径保留 preprocess、FFT、REF-VAD、AEC、BF；
2. 复制 BF 主频谱到 LIGHT 独立工作区，运行 light AES/NR 和独立 synthesis；
3. STRONG 保留 blocking output，继续 GSC、strong AES、BF-post、NR/NN、AGC 和独立 synthesis；
4. LIGHT 每帧必产出；STRONG 由 `call_active` 按帧启停，未通话时不消耗后处理 CPU；
5. 开启/关闭 STRONG 只 reset 强后处理状态，不 reset 公共 AEC。

AES 依赖 AEC 的 mic/error/echo 频谱。两个分支应共享只读估计，但必须使用两个 AES 增益/平滑状态；NR、BF-post、AGC、IFFT/OLA 同样必须独立。

### 破坏式新 API 与数据面

本次代码更新不做旧实现兼容，不保留旧 ABI，不增加 `V2`、兼容 wrapper、旧符号别名或双轨 fallback。旧 `SEVC_API_*` 调用面及其隐式配置语义直接退出产品代码；HDI、Sensor、KWS/ASR 和通话消费者在同一变更集中迁移到唯一的新接口。若整包无法一次升级，则本次变更不得以兼容层方式拆分上线。

新接口按“能力声明、实例构造、逐帧处理、诊断、销毁并清零”重新定义；profile 只能在构造时确定，活动实例禁止原位修改模块组合：

```c
typedef enum {
    AISPEECH_PROFILE_VOICE = 1, /* KWS + ASR */
    AISPEECH_PROFILE_CALL  = 2, /* call uplink */
} AISPEECH_PROFILE_E;

AISPEECH_HANDLE *AISPEECH_Create(const AISPEECH_CREATE_CONFIG_S *config);
int AISPEECH_Process(AISPEECH_HANDLE *handle,
                     const AISPEECH_INPUT_FRAME_S *input,
                     AISPEECH_OUTPUT_FRAME_S *output);
int AISPEECH_GetDiagnostics(AISPEECH_HANDLE *handle,
                            AISPEECH_DIAGNOSTICS_S *diagnostics);
void AISPEECH_DestroyAndWipe(AISPEECH_HANDLE **handle);
```

以上仅表达契约，不冻结最终 C 命名。`config` 必须显式包含 profile、采样格式、MIC/REF 拓扑、资源身份和 arena 所有权；禁止从旧全局宏、旧默认值或上一次实例继承场景参数。输出 frame 必须包含 PCM、samples、sample rate、source frame sequence、单调 PTS、`profile`、`generation`、`discontinuity`，以及 `vad_source/warmup/ref_valid/aec_converged/clipping` flags。诊断至少包含 REF delay、ERLE proxy、double-talk、MIC/REF/output clipping、阶段耗时、drop count、结构版本和大小。

数据面不继续复用旧通道语义。新实现建立唯一受 owner 控制的上行发布契约；采用并行方案时可发布 VOICE/CALL 两个显式端点，采用互斥方案时可使用单端点加 `profile + generation`，但不能让旧消费者通过缺省行为猜测当前音频类型。生产者切换代际后，消费者必须丢弃旧 generation 的排队帧和迟到回调。

### 产品状态机

| 状态 | KWS/LIGHT | ASR/LIGHT | Call/STRONG | 规则 |
| --- | --- | --- | --- | --- |
| WAITING | 常开 | 不上传 | 关闭 | 有播放时公共 AEC 继续 |
| PRE_ACTIVE | 常开并保留 pre-roll | 等 ALLOW_TALK | 关闭 | 提示音必须进入 REF |
| ACTIVE | 常开 | 上传、独立 endpoint | 关闭 | TTS 前结束当前 utterance |
| PLAYING | 常开用于唤醒打断 | 默认暂停 | 关闭 | 唤醒后先停 TTS，再进 PRE_ACTIVE |
| CALL | 按策略保留 | 默认不上传 | 开启 | 全双工，AEC 永不中断 |
| DISABLED | 不响应或仅诊断 | 不上传 | 仅显式通话可开 | 明确隐私语义 |

CALL 应作为独立 owner/正交状态，不要粗暴塞入 ACTIVE/PLAYING。语音助手和通话必须有唯一音频路由 owner，决定 ASR 上传与 STRONG enable。ASR endpoint 与 KWS VAD 分离：KWS 连续喂流并保留当前 480 ms pre-roll；ASR 在 ACTIVE 创建 utterance，并保留 200--500 ms 前滚和可调尾静音。

### 分阶段落地

1. **阶段 0，证据基线**：固定源码/资源 hash 和 `.so` BuildID；建立 MIC0/MIC1/REF/post-AEC/post-BF/final taps；完成 REF delay、增益、极性、相位和削波校准。
2. **阶段 1，先把单输出调成 LIGHT**：保留 AEC+BF，GSC 初始关闭，AES/NR 保守，AGC 关闭并加 limiter；KWS/ASR 的产品功能语义保持不变，但调用接口同步迁移到新契约。先证明 KWS FRR/FAH 与 ASR CER/WER 不退化。
3. **阶段 2，公共核心双分支**：一次性切换到唯一的新 API、独立 light/strong 状态、新 HDI 输出契约和 call 数据面；验证启用 STRONG 不改变 LIGHT 输出和时序。
4. **阶段 3，通话接入**：call owner 控制 STRONG，验证接听/挂断、TTS 打断、REF 中断、网络恢复和低功耗恢复。
5. **阶段 4，高级算法**：传统 NR 基线完整后才比较 FSMN NN；风噪仍为主因时再引入 WN 或机器人专用训练模型。

### 验收门禁

- KWS：两个词分别统计 FRR、FAH/h、p50/p95 延迟；
- ASR：命令准确率或 CER/WER、首包延迟、endpoint 截断率、空请求率；
- 通话：分频段 ERLE、双讲保持、近端失真、远端响度、p95 时延；
- 系统：LIGHT/STRONG CPU、RSS、最大帧耗时、deadline miss、SHM drop 和 24 h 状态泄漏；
- 场景：0.5/1/2/3 m、正侧背方向、静止/行驶、风扇/电机/碰撞、电视/音乐/人声、TTS 音量、单讲/双讲。

最重要的门禁是：启用或调整 STRONG 后，LIGHT 必须逐帧不变或落在声明的数值容差内。通话优化不得改变 KWS/ASR 输入分布。

### 当前风险

- `modules/aispeech` 当前未纳入 Git 跟踪，编码前需要建立可评审、可回滚的源码身份；
- 产品部署仍从 third-party 路径取 `.so`，源码、库、app、image/OTA 必须用 hash/BuildID 贯通；
- AI voice 实现主要存在于归档 tar，正式修改前需恢复为受管模块并核对版本；
- 历史 QIVW 有无 pre-roll 的 VAD 硬门控版本，不能回退覆盖当前 fail-open/pre-roll 方案。

本节是设计候选，尚未编码、重建、部署或执行板端 HIL；状态维持 `reviewing`。

## 2026-08-24 性能约束增补：可并行、互斥后处理与双实例切换

### 约束修正

SSC305 性能较弱时，不预设必须采用“单 SEVC 实例、LIGHT/STRONG profile 互斥”。正确决策顺序是先测并行双输出；不满足实时预算时，再在以下降级方案中选择。LIGHT 与 STRONG 在 CALL 状态是否需要同时存在，是产品策略而不是算法默认：若通话中不要求 KWS/ASR，允许稳态只运行 STRONG；切换窗口可允许短时、受控重叠。

### 四档实现与推荐顺序

| 方案 | 稳态计算 | 内存 | AEC 连续性 | 切换风险 | 适用条件 |
| --- | --- | --- | --- | --- | --- |
| A. 公共 AEC/BF + LIGHT/STRONG 同时输出 | 最高，但低于双完整实例 | 两套后处理状态 | 最好 | 最低 | CPU/热预算通过，通话中仍需 KWS/ASR |
| B. 公共 AEC/BF + 后处理二选一 | 约一条链 | 两套或可复用后处理状态 | 最好 | 低 | CPU 不够并行，CALL 中可停 KWS/ASR；首选降级 |
| C. 两个完整 SEVC 实例，任一时刻只 feed 一个 | 约一条完整链 | 接近两倍 | 非活动实例会陈旧 | 中高 | 内存足够、希望 profile 完全隔离、暂不重构公共核心 |
| D. 单实例销毁并重建 | 最低 | 最低 | 会冷启动 | 最高 | CPU、内存都不足时的最后方案 |

推荐选择树：A 通过板端实时/热/内存门禁则使用 A；A 失败且 CALL 中不要求 KWS/ASR，优先 B；公共核心重构周期不可接受而内存足够时使用 C；只有内存也无法容纳两个 context 才选择 D。

方案 B 是性能与体验的最佳折中：AEC/BF 一直运行，只执行当前场景的后处理；模式切换不重置公共 AEC。LIGHT 和 STRONG 的后处理对象可都驻留内存但仅一个计算，或按内存预算对非活动对象释放。前者切换快，后者省内存但增加初始化时延。

方案 C 不能直接用当前构造参数得到完全不同的 profile，因为现有 API 只区分 NR/NN/AGC，GSC/AES/BF-post 仍受编译宏控制。新构造契约必须完整描述 module mask/profile，或构建两个符号隔离的 profile library。两个实例可以同时驻留但稳态只 feed 当前实例；目标实例切入前使用有界原始缓存或短时双 feed 预热，提交后立即停止旧实例。陈旧实例再次切入前必须重新判断噪声/AEC/VAD 状态并预热，不能直接把历史 ready 当作当前 ready。

### 统一实现边界：代码硬升级、不兼容、无旧实现残留

四档架构继续保留，由板端性能数据选择；“硬升级”约束的是本次源码和产品调用面的迁移方式，不把运行时架构强制收敛为方案 D。新实现不复用旧接口、旧控制流和旧缺省语义，不维持旧 ABI；严禁新增 `V2` 兼容层、旧 API wrapper、旧/新算法 fallback，或保留运行时开关回到旧实现。HDI、Sensor、KWS/ASR、通话消费者与部署库必须作为同一不兼容版本整体升级。

“无残留”包含两层：源码层不得残留可达的旧实现；运行时不得让上一个 route/generation 的帧、回调和消费者状态泄漏到新 route。架构明确拥有的长期状态不是残留，例如方案 A/B 的公共 AEC/BF、方案 A 的两个活动后处理、方案 B 可驻留但不运行的两套后处理状态、方案 C 的两个完整实例。这些状态必须有明确 owner、生命周期、reset/stale 规则，不能依赖旧代码兼容语义。

| 状态域 | A/B 公共核心 | C 双完整实例 | D 销毁重建 | 切换约束 |
| --- | --- | --- | --- | --- |
| STFT/AEC/BF | 明确共享并连续 | 每实例独立 | 当前实例独占 | 只有 A/B 允许跨场景共享 |
| AES/NR/NN/AGC/VAD/IFFT/OLA | 每 profile 独立 | 每实例独立 | 重建 | 禁止不同 profile 串用可变状态 |
| 输入累积、PCM/REF、输出队列 | route 私有 | route 私有 | 实例私有 | COMMIT 后清除旧 generation |
| QIVW pre-roll、ASR utterance、通话队列 | 消费者私有 | 消费者私有 | 消费者私有 | EOS 后销毁，不跨 generation 恢复 |
| 预热环形缓存 | 仅事务期存在 | 仅事务期存在 | 可不用 | 不发布，COMMIT/ABORT 后清零 |
| 参数、资源、诊断快照 | profile + generation | instance + generation | instance + generation | 旧 generation 快照立即失效 |

### 运行时硬切换事务

路由切换必须在 256-sample、16 ms SEVC 帧边界原子提交，并使用递增 `generation`：

```text
PREPARE -> WARMUP -> READY -> QUIESCE/EOS -> COMMIT -> WIPE_TRANSITION
                       \-> ABORT（仅 COMMIT 前）
```

`PREPARE/WARMUP` 的具体动作由方案决定：A 只检查目标输出健康；B 预热目标后处理但不改变公共 AEC/BF；C 用至少 500 ms、约 48 KB 的 2 MIC + 1 REF 原始环形缓存或 200--500 ms 有界双 feed 预热目标实例；D 只能停止旧实例后创建并冷启动新实例。预热 PCM 不得发布给业务，过渡缓存必须在 COMMIT 或 ABORT 后可靠清零。

VOICE -> CALL：停止创建新 ASR utterance并结束当前请求；确认 REF/输入连续；准备目标链；在帧边界发送旧 generation 的 EOS、原子切换 route 并发布新 generation 的 BOS；再按产品策略暂停 KWS/ASR。CALL -> VOICE：结束通话上行；准备 VOICE 链；在帧边界切换；新建 QIVW session 和 ASR 控制状态，并从新 generation 重新建立业务 pre-roll。

COMMIT 前目标未 READY 时可以 ABORT，旧 route 继续工作；COMMIT 后不允许回到旧 generation，也不允许输出旧队列或未初始化 PCM。COMMIT 后故障进入有界静音和显式 `ERROR`，由上层重新发起一次完整切换事务。状态机至少包含 `VOICE`、`SWITCHING_TO_CALL`、`CALL`、`SWITCHING_TO_VOICE`、`ERROR`；切换中只有被事务明确授权的预热 feed，业务侧不得消费过渡音频。

公共核心方案切换不能 reset 公共 AEC/BF；只切 route 并按方案处理 profile 私有状态。方案 A 若保持两路业务同时活动，则不销毁任一活动链，但两个输出必须使用独立端点/队列和显式 profile。方案 B 停止旧后处理计算后，可保留其私有状态以便下次受控预热，也可按内存预算 reset/release。方案 C 的非活动实例状态必须标记 `stale`，不得跳过 READY 门禁。方案 D 每次切换都执行销毁、可靠清零、重建和冷启动。

可靠清零应使用不会被编译器优化掉的专用 wipe（平台支持时使用 `explicit_bzero`，否则使用经验证的 volatile 实现），并在 free 或复用前执行。必须覆盖被释放的 SEVC caller-owned arena、工作区、HDI 临时 buffer、事务预热环形缓存、旧 generation 的 pre-roll/SHM slot/消费者队列和诊断快照。仍被当前架构 owner 明确持有的公共或非活动实例状态不应伪装成已清零，但必须通过 profile、generation、active/stale 标志阻止越界访问。仅调用当前 `SEVC_API_Delete` 或普通 `free` 不能作为无残留证据。

### `dev/vad` 分支算法审计

`origin/dev/vad` 的提交 `158c6ed` 在 NR 路径增加 VAD v2，主要能力包括：

- 使用 NR noisy power/noise PSD、NR gain、8 个频带的 SNR、持续频带数、中频占比和瞬态偏差构造 Q24 概率；
- 16 kHz 使用 FFT bins `[10, 109)`，约覆盖 312.5--3375 Hz，符合语音主频段，但高频辅音信息占比较少；
- 分离快速 AGC VAD 与慢速 wake gate，避免同一 hangover 同时服务 AGC 和唤醒门控；
- 提供 `SEVC_API_VadProbabilityGet` 和诊断快照；
- 修复 master 中 NR 模式把 `fVadStatus` 固定为 AGC 阈值、导致 AGC 使用错误 VAD 的问题；
- 提供 noise-safe、balanced、speech-safe 三档编译 profile，默认选择 noise-safe。

以 16 ms 帧计，noise-safe/balanced/speech-safe 的 wake onset 名义值分别为 6/5/4 帧，即约 96/80/64 ms，hangover 分别约 192/256/320 ms；实际还叠加概率平滑延迟。当前 480 ms QIVW pre-roll 足以覆盖该确认延迟，因此 KWS 可优先 noise-safe，但仍不能把 wake gate 当作无 pre-roll 的硬门。

NR VAD 有三种不同消费者语义：

- `wake state`：可作为 QIVW feed gate 的 shadow/节流信号，必须 pre-roll、tail、stale fail-open；
- `smooth probability`：供 ASR endpoint 在应用层建立独立 onset/offset/hangover，不直接使用 wake 二值状态；
- `AGC VAD`：仅驱动 AGC/NR speech protection，不能向上解释为 KWS 或 ASR endpoint。

### `dev/vad` 与模式切换的关键风险

1. VAD 在 `SEVC_NR_Feed` 内计算，看到的是进入 NR 的频谱。切换 GSC、AES、BF-post 或 NR 参数会改变输入分布，LIGHT/STRONG 的同一阈值不保证等价。理想方案是在公共 post-AEC+BF tap 计算共享 VAD；短期至少按 `profile_id` 分别标定阈值。
2. NR reset 后前 5 帧约 80 ms 用于噪声初始化，VAD 输出为 0。硬切换后必须把该时段标记为 `warmup` 并隔离，不能作为 ASR/KWS/AGC 判决，也不能用旧 generation 的 pre-roll 填充。
3. stable-noise 允许更新需要 64/96/128 帧，约 1.024/1.536/2.048 s。新建或已 reset 的实例必须从新鲜帧重新学习；方案 C 的驻留实例只能在 staleness 门禁通过时延续 noise PSD，否则也必须 reset 并重新预热。该完整收敛时间是否全部静音，由离线和 HIL 对 KWS/ASR/通话质量的门禁决定。
4. 当 NN 启用时，API 优先返回 NN VAD；NR 与 NN 模式的 probability 和 diagnostics 语义不同。输出必须提供 `vad_source={NR,NN,NONE}`，禁止消费者静默混用阈值。`dev/vad` 中“NR VAD v2”只表示算法演进来源，不能进入稳定产品 API 名称。
5. 当前 profile 由 `NR_VAD_PROFILE` 编译宏选择，无法表达新实例的完整配置。若 LIGHT/STRONG 使用不同 VAD 参数，应在构造时绑定实例级只读参数；活动实例禁止运行时改 profile，也不能通过重载旧库保留兼容路径。
6. 诊断 getter 直接读取引擎字段；若处理线程和读取线程不同，需要在处理后生成带 `frame_seq/version/size` 的一致性快照，避免撕裂读取。
7. 该分支提交未包含自动化测试文件；在离线 corpus、ARM 定点回归和 HIL 完成前只能视为候选。

建议把诊断结构升级为版本化结构，增加 `struct_size`、`version`、`frame_seq`、`profile_generation`、`vad_source`、`warmup`、`stale`。HDI 每个新 SEVC 帧只发布一次 VAD，现有约 62.5 Hz 事件节拍保持不变。

### 性能决策门禁

必须在视觉、网络、TTS/通话编码等真实并发负载下测量，而不是只测 SEVC demo。每种方案报告：平均/p95/p99/最大单帧耗时、16 ms deadline miss、CPU、RSS、内存高水位、温升、SHM drop 和 24 h 稳定性。

建议初始门禁为 p99 算法耗时不超过 16 ms 帧预算的 60%，给调度抖动和其他业务保留至少 40% 余量；最终阈值由整机性能预算确认。A 若不满足则评估 B，禁止仅凭平均 CPU 判断并行可用。

切换专项验收包括：切换耗时、静音窗和首个有效输出、音频缺口/重复帧、AEC/NR/VAD warm-up、QIVW/ASR 恢复时间、通话首包、连续 1000 次切换、播放/双讲中切换、每个事务阶段的故障注入，以及旧 generation 帧/回调/状态零泄漏。失败只能进入显式 `ERROR`，验收中必须证明不存在回退旧算法链。所有结果按 `generation` 对齐。

本增补修正了“必须单实例互斥”的过度约束：最终实现由性能数据决定，优先顺序为并行双输出、共享公共核心后处理互斥、双完整实例按需切换、单实例重建。`dev/vad` 仍为 reviewing 候选，未声明已通过产品验证。

## 2026-08-24 源码落地增补：统一新契约与 D 档安全基线

### 落地范围与架构边界

本轮已在源码中落地方案 D“单实例销毁、可靠清零、重建”作为无板端性能证据时的安全执行基线，但没有据此删除 A/B/C。四档架构继续作为性能选型空间；后续 A/B/C 应复用本轮唯一的新 API、profile、generation、诊断和 owner 契约，不能再增加新版本接口或恢复旧兼容层。

当前源码身份：

- `modules/aispeech` 基线为 `origin/dev/vad=158c6ed`，本地实现分支为 `codex/pcr02-front-end-r1`；
- 父仓基线为 `819d2ffe380eb8e363c0395c15d6e4f11020ffe0`；
- 最终验证应用为 `out/arm/app/prog_pcr02`，BuildID `689e8affe255e2aa24462964a170cd4983a46474`，SHA-256 `4d929c003fc1a2f2ea9694186e5f7bbf32aa8d7f3e755c67e70176715c7581b8`，ELF magic `7f454c46`；
- 以上均为 working-tree/source candidate，未自动 commit、部署、生成 image 或 OTA。

### 破坏式新接口

旧 `SEVC_API_*` 和本轮中间命名 `AISPEECH_SEVC_*` 均已退出 PCR02 可达源码及构建制品，不存在 `V2`、旧 wrapper、typedef/宏别名或运行时 fallback。产品级边界命名为 AFE，是因为该模块同时服务 KWS、ASR 和通话，不应把上层契约固化为某一个 SEVC 内核实现。`AISP_` 与仓内既有供应商命名体系一致。公共头文件为 `aisp_afe.h`，新库只提供：

```text
AISP_AFE_MemorySize
AISP_AFE_Create
AISP_AFE_Process
AISP_AFE_GetDiagnostics
AISP_AFE_Reset
AISP_AFE_DestroyAndWipe
```

VAD 来源枚举固定为 `AISP_AFE_VAD_SOURCE_{NONE,NR,NN}`。接口使用稳定能力语义，不暴露内部算法代际；未来 NR 算法替换或迭代仍保持 `NR`，只有真正改变消费者语义或 ABI 时才修改接口版本。

构造配置显式包含 `api_version/struct_size/profile/vad_profile/generation/sample_rate/module_mask/resource/arena`。逐帧输入输出显式携带 `generation/frame_seq/pts/ref_valid/discontinuity/warmup`；旧 generation、非单调 frame sequence、无效 REF 和 discontinuity 都 fail closed，不继续产生业务 PCM。

诊断快照包含 `profile/module_mask/vad_source/instant/smooth/transient/mid_ratio/agc_vad/wake_vad/stable_noise_count/warmup/stale`。HDI VAD 回调已从单个 `U8` 改为结构化事件，携带 `generation/frame_seq/profile/vad_source/smooth_probability/wake/agc/warmup`：

- KWS 只消费 `wake_state`，warmup 时强制按非活动处理并继续依赖 pre-roll；
- ASR endpoint 可以消费 `smooth_probability`，不再被迫复用 wake 二值状态；
- AGC VAD 保持独立，仅服务增益和 speech protection。

### 当前 VOICE/CALL profile

| Profile | 默认模块 | VAD profile | 产品消费者 |
| --- | --- | --- | --- |
| VOICE/LIGHT | AEC + AES + BF + NR | noise-safe | KWS + ASR |
| CALL/STRONG | AEC + AES + BF + GSC + BF-post + NR + AGC | balanced | 通话上行 |

GSC、BF-post、AGC 已从“只有配置字段”改为实例运行时门禁：VOICE 不分配/不执行 GSC 和 BF-post，CALL 才分配并执行。VOICE/CALL arena 实测 host 大小分别约 104428 B 和 149060 B，证明 profile 已形成不同内存与计算路径，而不是只改变标签。

源码审计同时发现并修正：原 `sevcBfCbFunc -> sevcGscCbFunc -> AES` 链中，AES 使用最后一路 AEC error 而没有使用 callback 传入的 BF/GSC 频谱，导致 BF/GSC 结果没有真正进入最终语音。现在 AES 的 error 输入使用当前 BF/GSC 输出，echo estimate 仍来自 AEC。该修正符合目标拓扑，但会改变输出分布，必须通过 corpus 和 HIL 才能判定音质收益，不能凭代码推导为产品优化完成。

### 硬切换与无残留实现

API/HDI 的当前切换事务为：

```text
close all PCM/AAC readers and channels
  -> request VOICE/CALL
  -> destroy old engine
  -> volatile wipe arena + MIC/REF/output buffers
  -> generation++
  -> create target profile in the same max-sized arena
  -> rebuild from new audio
  -> mute NR warmup output
  -> reopen producer/consumer path
```

活动 reader/channel 下调用 `VSAPIAUDIO_AiSetSpeechProfile` 或直接调用 HDI profile API会返回 `VS_ERROR_BUSY`。这防止旧 ringframe、reader handle 和业务 PCM 跨切换边界。COMMIT 后创建失败保持无引擎错误态，不恢复旧 profile。

可靠清零同时覆盖 AISpeech caller-owned arena、HDI MIC/REF/output buffer、部分初始化失败的存储和释放路径；使用 volatile wipe，不能被普通优化删除。原 HDI 缓存 `FrameBuffer/FrameOut` 静态指针的方式已删除，避免实例重建后继续引用旧 arena。

### 构建链收口

PCR02 现在把 `modules/aispeech` 声明为内部依赖，HDI 直接包含源码公共头，应用从内部静态库链接 AISpeech。`pcr02/dep.mk` 已移除旧 third-party `libaispeech.so` 发布项；最终 `prog_pcr02` 没有 `libaispeech.so` 的 `DT_NEEDED`，不存在“源码已改、产品仍加载旧库”的双轨。

物理 third-party 文件仍留在仓内供其他未迁移产品使用，但不在 PCR02 可达构建和发布路径中；本轮没有跨产品删除供应商制品。

### 已完成验证

- AISpeech host 静态构建通过；
- AISpeech ARM glibc 11.1.0 静态/动态构建通过；
- `modules/hdi`、`modules/api`、`modules/app` 对象和库构建通过；
- `pcr02_app_all` 链接通过；
- host contract 覆盖 generation、非单调 sequence、REF、warmup、VOICE/CALL module mask、reset 和 caller-owned arena wipe；
- host 连续 1000 次 VOICE/CALL create/process/destroy，每次销毁后 arena 全零；
- AISpeech/HDI/API/App/父仓 `diff --check` 通过；
- PCR02 可达源码和最终 ELF 的旧 `SEVC_API_*` 负搜索通过；
- PCR02 可达源码、AISpeech 静态/动态库中 `AISPEECH_SEVC_*`、`NR_V2`、`sevc_api.h` 负搜索通过；静态归档曾因增量构建保留旧 `sevc_api.user.arm.o`，删除旧成员并从空归档重建后复验为零；
- 最终 ELF 确认新 AISpeech 静态进入应用，且无旧动态库依赖。

host 2000 帧相对基线和架构边界：

| Profile/Mode | Arena/Memory | avg | p95 | p99 | max |
| --- | ---: | ---: | ---: | ---: | ---: |
| VOICE candidate | 104428 B | 51.61 us | 79.97 us | 92.68 us | 140.28 us |
| CALL | 149060 B | 75.52 us | 77.60 us | 85.30 us | 107.94 us |
| 双完整实例并行上界 | 253488 B | 106.37 us | 125.82 us | 133.93 us | 150.77 us |
| D 档销毁重建，不含 warmup | 149060 B arena | 116.44 us | 140.44 us | 168.80 us | 202.53 us |

CALL host 内存约比 VOICE 高 43%。双完整实例数据是 A 的保守计算/内存上界，不是公共 AEC/BF 并行实现；D 档约 0.17 ms 的对象重建 p99 远小于约 80 ms NR VAD warmup，说明冷切体验主要由状态收敛决定。以上数据只用于证明 profile 分流和发现 host 回归，不代表 SSC305 性能，不能用于越过 9.6 ms p99 门禁。

### 控制状态、板端可观测性与输入连续性

profile 请求是异步提交。HDI/API 现提供原子状态快照：`desired/active/generation/ready/warmup/last_error`。owner 在重开 reader 后，必须等待 `desired==active && ready==1 && warmup==0 && last_error==0`，才能启用 KWS/ASR 或通话消费者；只看到 set profile 返回成功不能解释为目标链已 READY。

每个 generation 独立维护 1 ms耗时直方图，暴露 `frame_count/last/max/approx_p95/approx_p99/16ms_deadline_miss`。切 profile、reset 或重建会清零，禁止跨 generation 混算。该直方图是上板 A/B/C/D 决策的最小工具，不替代整机 CPU/RSS/温升统计。

HDI 还检查 128-sample 输入的 8 ms PTS节拍，容差初值为 4 ms。发生 discontinuity 时，不继续沿用旧 AEC/OLA/NR：同 profile generation++、reset、清 MIC/REF/output 缓存、重新 warmup，并累加 `discontinuity_count`。4 ms阈值仍需板端验证，避免驱动 PTS正常抖动造成误 reset。

### LIGHT 参数候选与合成回归

新构造配置显式支持 `aes_gain_floor_q20/nr_gain_floor_q20/output_gain_q15`，活动实例禁止原位修改。2026-08-25最终低风险LIGHT候选为：AES floor 0.20、NR floor 0.75、输出1.25×（Q15=40960）、REF delay=20 samples；BF/phone MAIN、VAD和CALL强链保持不变。1.60×曾作为短期增益试验，但整机反馈显示AEC后残留也被同步放大，因此已撤销为默认值。

确定性合成回归结果：

| Profile | 场景 | 输入/输出衰减 | clip |
| --- | --- | ---: | ---: |
| VOICE candidate | far-only | 58.71 dB | 0 |
| VOICE candidate | near-only | 9.09 dB | 0 |
| VOICE candidate | double-talk | 6.39 dB | 0 |
| CALL | far-only | 48.52 dB | 0 |
| CALL | near-only | 29.13 dB | 0 |
| CALL | double-talk | 20.00 dB | 0 |

历史试验中，VOICE输出增益由1.25提高到1.60后，near-only和double-talk输出分别提高约2.15/2.14 dB，所有场景仍无削波，但该固定后增益同样放大残留回声，不能改善AEC本身。因此默认回退到1.25；CALL结果完全不变。合成tone/noise只能证明影响边界和防明显回归，不能替代QIVW、ASR、ERLE和主观验证。

### REF delay 标定与离线 corpus 工具

此前 HDI 的 `s32RefDelayBufLen` 固定为 0，这是回声残留的独立高优先级风险：如果播放链到 loopback REF、扬声器到 MIC 的等效延迟未对齐，AEC 参数调强不能修复时序错误。

当前实现新增 0--1600 samples（16 kHz 下 0--100 ms）REF delay 控制。缓冲按最大 delay 一次分配；只有所有 AI reader/channel 完全关闭时允许修改。修改后同 profile generation++、reset、清 MIC/REF/output、重新 warmup，状态快照回读 `ref_delay_samples`。禁止通话或 KWS/ASR 活动中原位移动 REF。

`modules/aispeech/tests/sevc_ref_delay_scan.c` 对 MIC0/MIC1 平均与 REF 做一阶差分归一化互相关，扫描 0--1600 samples并输出 delay、毫秒、相关系数和极性；相关系数绝对值低于 0.05 时拒绝给出候选。注入 321 samples、反相的 self-test 恢复为 `321 / 20.062 ms / correlation=-1.0`。扫描结果只是候选，必须围绕候选做 ERLE、双讲和近端失真 sweep。

`sevc_offline_eval.c` 读取 `MIC0/MIC1/REF` 3ch S16LE，按产品 VOICE/CALL 配置输出 mono PCM 和逐帧 diagnostics CSV。10 帧 zero-input smoke 生成 5120 B mono 和 11 行 CSV（含 header）。`make -C modules/aispeech/tests run` 统一执行 API contract、1000 次生命周期、profile benchmark、合成信号回归和 delay self-test。

### 两组设备 corpus 工程回归

`modules/aispeech/tests/audio` 原有三套文件名，但无前缀 `audio_in.wav/audio_in_echo.wav` 与 80 组逐字节相同，已删除重复副本。当前只保留 80/100 两组唯一设备采集；产品目标音量为 80，因此 80 是主回归输入，100 只作过载压力。它们没有唤醒、转写、近端 clean target 或场景标签，不能用于 FRR/FAH、CER/WER、ERLE、MOS 或量产验收。

输入基线：

| Corpus | Samples/channel | Tail | REF delay/polarity | REF full-scale samples | Container |
| --- | ---: | ---: | --- | ---: | --- |
| 80 | 1074560 | 128 | 23 samples / normal | 0 | valid WAV header |
| 100 | 1107957 | 245 | 17 samples / inverted | 74 | RIFF/data length exceeds actual file；block_align=1024 |

100组两个WAV的header声明约11 MB，实际PCM data均为4431828 bytes，且仍按双通道S16LE完整对齐。回归加载器不修改原始PCM，只把这一已知`truncated_header/block_align`纳入输入契约。REF与HDI一致只使用`pktEchoData` channel 0。80语料相关峰仍记录为23 samples；新整机far-only复测为20 samples，owner已批准runtime-default统一使用20，raw delay=0保留为反事实对照。仅处理完整256-sample帧，尾部记录但不补零。

`afe_audio_corpus_regression`固化原始data FNV-1a、格式/样本数、REF delay/极性/相关性区间/满幅计数，以及每组raw delay=0/runtime-default delay=20 × VOICE/CALL的原始PCM、warmup静音后PCM、所有公开output/diagnostics字段和warmup/wake/AGC指纹：

| Corpus/Path/Profile | Raw PCM | Muted PCM | Diagnostics | Frames / warmup / wake / AGC |
| --- | --- | --- | --- | --- |
| 80/raw/VOICE | `a40981ec0bee4b28` | `bc0c79557069a51e` | `28cfb1c211b25e6f` | 4197 / 5 / 4035 / 4113 |
| 80/raw/CALL | `7adba1861a7fcecc` | `87dbcbe0dd252ac8` | `7d87b3153cdae8cf` | 4197 / 5 / 3996 / 4124 |
| 80/runtime-default/VOICE | `a6f54734e5fa544d` | `89438ee1836d3f0b` | `15e8ef7420f14576` | 4197 / 5 / 4122 / 4150 |
| 80/runtime-default/CALL | `dd1f2457ed8bc20d` | `5020f41aa5fdaf61` | `6c1d9c1e37bd9985` | 4197 / 5 / 3880 / 4088 |
| 100/raw/VOICE | `f95a9389d33f47ec` | `b59d76053b68d850` | `a8bc3a3299b73e29` | 4327 / 5 / 4227 / 4193 |
| 100/raw/CALL | `183ba9a07736b2eb` | `864fd127cb788168` | `4f5d5abfdd43c63d` | 4327 / 5 / 3321 / 3665 |
| 100/runtime-default/VOICE | `2fb1254a18bb1f64` | `3827892c5454c0bf` | `c2e9e29b9a394db3` | 4327 / 5 / 4183 / 4178 |
| 100/runtime-default/CALL | `ee8c5d5a504caa29` | `3724c94ac158a3aa` | `bb2f489c490138b4` | 4327 / 5 / 3065 / 3426 |

黄金值只用于发现同一 host 定点实现的行为漂移，必须在差异分析和评审后手工更新。`corpus.sha256`是四个完整WAV资产身份的唯一SHA-256来源，`run-corpus/run-all`在算法处理前强制校验；`--print-baseline`只放宽输出黄金比较，仍强制输入FNV、delay、极性、相关性和削顶契约。同长度单bit损坏分别被checksum exit 2和print-baseline exit 1拒绝。测试入口每次清理 x86 objects、删除 archive 并从当前工作树重建，输出 archive SHA-256，避免复用固定 `/tmp` 旧库。长度不匹配、低相关、重复旧文件和缺文件均为显式负路径；ASan复验确认原 MIC/REF 长度不匹配越界已经关闭。

原始 WAV 的 capture owner、隐私和分发 review 尚未完成，已通过 `.gitignore` 排除，并在 `corpus-manifest.json` 标记 `git_commit_allowed=false`。普通 `make run` 只执行无外部资产的 host 门禁；本地显式 `run-corpus/run-all` 才使用录音。共享/CI 应从受治理 artifact vault 注入，不得把本地文件存在解释为提交授权。

### WAV dump writer修复

整机录音曾稳定复现三类容器错误：MIC/REF/AFE多个文件共用全局`g_header`，导致`dataLen`跨文件累计；PCM `blockAlign`固定写成1024，而stereo/mono S16正确值分别为4/2；far-only最终输出还存在40 ms尾部差，无法在损坏header基础上区分dump停止次序与算法缺帧。

2026-08-25已删除共享header。写入逻辑先校验全部packet，再为当前文件独立追加payload，以该文件实际size计算`dataLen/riffLen`并回写44-byte header。已有非空文件追加前必须读取并严格匹配完整header；同句柄格式变化、非法pktCount、NULL/zero payload和不支持AAC均fail closed，不生成或追加半截WAV。PCM stereo/mono的`blockAlign`固定由声道数和16-bit样本宽度计算。

Host测试交错写入stereo MIC、stereo REF和mono AFE，验证各自header、byte rate、长度和实际size独立一致；同时覆盖4类负路径。`modules/hdi_obj_all`、`modules/hdi_lib_all`和`pcr02_app_all`串行通过。该修复不改变PCM算法或REF delay=20；VOICE gain随后因残留回声放大问题独立回退为1.25。当时尚未获得设备重录，runtime门禁要求ffprobe无`corrupt input packet`且三路长度差不超过一个8 ms输入块。

随后新增far-only整机录音完成运行复验：MIC、REF和AFE三路均为29.200 s；stereo/mono `blockAlign`分别为4/2；RIFF/data声明与实际文件size逐字节一致；ffprobe和完整decode无`corrupt input packet`，旧40 ms尾差未复现。REF channel 0物理相关峰为19 samples、correlation=-0.621325；raw dump位于HDI delay缓冲前，因此与runtime default 20并不冲突。新录音全带far-only抑制约17.65 dB，300--3400 Hz语音带抑制约20.84 dB，输出peak=-10.65 dBFS且无削顶。该录音曾由host显式delay20/gain1.6复现，但它同时暴露了残留回声随固定后增益放大的风险，因此只保留为历史证据，不能代表当前gain1.25候选。录音未保存设备installed BuildID，故容器和行为证据通过，但制品身份仍为needs-review，当前候选仍需重新整机录制。

### 构建失败制品门禁

### AEC多分区负结果与语音打断唤醒假设

2026-08-25针对`SEVC_AEC_TAPS=1/2/4`做了同输入单变量复验。参考仓车载配置虽然使用4 taps，但同时启用了不同的AEC EMD、预加重和约束组合；当前PCR02路径不能只复制taps宏。测试输入为同一份29.2 s整机far-only MIC0/MIC1/REF，REF按运行默认精确延迟20 samples，VOICE保持gain=1.25、AES floor=0.20、NR floor=0.75。

| TAPS / μ | 输出RMS | 输出Peak | 合成VOICE far-only | 判定 |
| --- | ---: | ---: | ---: | --- |
| 1 / 0.4 | -45.62 dBFS | -12.77 dBFS | 58.71 dB | 稳定基线 |
| 2 / 0.4 | -35.96 dBFS | -9.44 dBFS | 0.05 dB | 明显退化 |
| 2 / 0.2 | -35.20 dBFS | -5.09 dBFS | -2.05 dB | 门禁失败 |
| 4 / 0.4 | -26.00 dBFS | 0.00 dBFS | 9.20 dB | 发散/削波 |
| 4 / 0.1 | -35.74 dBFS | -12.20 dBFS | 24.39 dB | 稳定但明显退化 |

因此源码最终恢复`TAPS=1/μ=0.4`。TAPS=2/4只作为被证伪候选保留；继续多tap必须先补分区约束、双讲保护、权重范数/发散诊断和post-AEC tap，再重新建立产品黄金值。验证过程中还发现`sevc_offline_eval`对空输入返回0帧成功，现已改为明确exit 1，避免生成假A/B证据。

产品观察为：安静环境“你好小窝”唤醒率高；语音打断/消回声场景下降，但同场景“小窝小窝”仍高。这个条件差异降低了“唤醒资源完全不支持该词”的概率。当前高优先级假设是播放起始或残余回声阶段，低能量词首“你好”被AEC/AES损伤，而重复“小窝”可依靠后半段冗余通过；其次是自定义QIVW资源缺少post-AFE残余回声域训练样本。现有KWS gate有480 ms pre-roll且FIRST/CONTINUE语义完整，暂不支持“VAD无pre-roll硬截词首”作为首要根因。下一轮应按关键词分别采集QIVW返回的keyword id/score、说话起点相对播放起点、raw/post-AEC/post-AES/final词首能量，再决定调整AFE双讲保护、资源训练或词级阈值；不能直接降低当前全局`ivw_threshold=0:1450`。

验证中证伪了“目标文件存在即可视为 app 构建成功”：把 `modules/hdi_obj_all`、`modules/hdi_lib_all` 和 `pcr02_app_all` 作为同一 `make -j8` 并行目标时，应用可能读取正在重写的 `libhdi.a`，GNU ld 以 signal 11 退出，并留下约 259 MB、前 16 字节全零但 mtime较新的 `prog_pcr02`。普通增量 make 可能误判该文件最新。

恢复路径为先完成静态库 producer，再使用 `rtk make -B pcr02_app_all -j1` 强制重建；最终必须同时检查退出码、ELF magic、BuildID 和动态依赖。后续禁止并行共享静态库 producer 与 app linker。

### 尚未闭环的产品证据

### 2026-08-25 分支收敛：master统一VOICE/CALL参数与流程

开发分支实现已独立提交为`codex/pcr02-front-end-r1@0576f37`，保留破坏式`AISP_AFE_*`、双profile、VAD diagnostics和完整host回归证据。随后按owner新决定切回`master@8939678`，在主分支重新收敛为单一产品AFE，不把开发分支双profile整包合入master。

master候选的公共流程为`AEC -> 35mm BF -> AES`，尾部只允许两个完整模式：`INTERACTION_NR`运行传统NR、floor0.75和固定gain1.25，供KWS/ASR；`CALL_NN_AGC`运行Communication FSMN NN、floor0.20和NN VAD驱动AGC，AGC后固定gain1.0，只供通话。公共TAPS=1、AEC μ=0.4、AES floor=0.25保持一致，GSC/BF-post/CNG/EQ关闭。该设计假定NN对宠物声音损失可接受，但宠物声音仍是HIL验收门禁。

主分支旧`SEVC_API_New/MemSizeGet`中的resource及NR/NN/AGC任意选择参数已删除，新增的`SEVC_API_TailModeRequest/TailStatusGet`只接受上述两个合法尾链。NR、NN和AGC在同一实例中同时分配，稳态只执行当前尾链；目标尾链先处理20帧/320 ms且禁止输出，当前尾链继续每帧输出，随后在16 ms边界硬提交。切换只reset目标/旧尾链，不reset公共AEC/BF/AES；预热中撤销请求会保持旧route。

实现审计同时修复三项上游问题：Communication模型没有8 kHz窄带资源但FSMN代码无条件引用phone NB符号，现已固定API只接受16 kHz并条件化窄带代码；Communication增益下限变量错误地被排除编译，现与phone共用；`SEVC_NN_Reset/SEVC_AGC_Reset`原为空且NR reset不完整，现清理FSMN/CMN历史、NN频谱/增益/VAD、AGC DRC/buffer和NR功率状态。NR Feed原硬编码0.5 floor，现真正使用产品实例0.75配置。

x86和ARM静态构建通过，host caller-owned arena为303996 B。可回放smoke覆盖非法模式、CALL预热中撤销、每帧单输出、无削波和1000轮双向切换，最近结果为`rounds=1000 callbacks=40012 generation=2001 switches=2000`。该结果不是SSC305性能或产品音质证据。

2026-08-26已完成父仓源码集成：AISpeech新增`SEVC_API_FeedPlanar`，HDI直接提交MIC0/MIC1/REF planar帧，并以`SEVC_API_TailModeRequest/TailStatusGet`把VOICE映射到`INTERACTION_NR`、CALL映射到`CALL_NN_AGC`；API继续以VOICE/CALL场景语义暴露close -> set -> reopen硬边界。切换只清空HDI staging PCM，不销毁实例、不reset公共AEC/BF/AES；目标尾链未READY期间HDI输出静音，提交帧已经输出目标尾链PCM，不携带旧profile残留。

AISpeech、HDI、API ARM static/dynamic库与`pcr02_app_all`顺序构建通过，1000轮host双向切换保持`generation=2001/switches=2000/callbacks=40012`。PCR02已移除旧third-party AISpeech链接目录和release `.so`项，最终应用无`libaispeech.so`动态依赖；当前BuildID为`dfa09e905d98fe07304aff85f33fb52c50abe373`，SHA-256为`0c19fe408849527cb62d58cce2aaa4ae4418e97e024871ecc97f8a61c11b0802`。这完成了source integration，不等于设备HIL、音频指标、image或OTA闭环。

主分支没有可供KWS/ASR使用的NR-VAD结构化诊断，HDI不得伪造VAD事件；当前诊断门控保持fail-open。真实通话owner在仓内仍未定位，必须由产品层实际接听/挂断流程调用API并等待`desired==active && ready==1 && warmup==0 && last_error==0`后启用消费者。本地设备WAV保持未跟踪且不得提交。

- `aispeech-training` 仍不能直接产出当前 SEVC 定点 NN resource：主 FSMN 实现依赖私有 `fsmn` 包和 CUDA；`pytorch2kaldi` 只输出文本 Kaldi nnet；未找到 int8/Q20、rbin、SEVC resource header 或 ARM golden 导出链。当前CALL使用仓内既有meeting/Communication资源作为候选，不把它宣称为机器人或宠物匹配模型；量产仍需通话、宠物声音和SSC305 HIL。
- 仓内没有稳定的通话 owner 实现，当前只提供 API/HDI 控制点和受 BUSY 保护的诊断入口；真实接听/挂断 owner 仍需执行 close -> set profile -> reopen。
- 未提供 SSC305 设备端点和现场授权，本轮未部署或执行板端单次、短循环、1000 次和 soak。
- 未提供 MIC0/MIC1/REF、近端/远端/双讲 corpus，因此 BF/GSC->AES 修正、VAD阈值、KWS FRR/FAH、ASR CER/WER/endpoint、ERLE和音质仍为待验证。
- A/B/C 尚未获得板端 CPU/RSS/热预算证据，不能从 host 结果确定最终生产架构。
- app 后编译没有进入已有 release/image/OTA；未重生制品前不得声明发布完成。

因此当前结论为 `source-pass candidate / product-HIL-pending`，而不是量产或发布闭环。

### 2026-08-26 owner事务与诊断闭环增补

API新增`VSAPIAUDIO_AiWaitSpeechProfileReady(profile, timeout_ms)`，超时范围限制为0--5000 ms。真正切换profile时仍要求所有PCM/AAC reader关闭；活动管线请求同一个已READY profile则幂等成功。标准事务固定为`close readers -> set profile -> reopen reader -> wait ready -> reset consumer ring`，等待过程中若desired被其他请求替换、SEVC返回错误或超时，会明确失败，不能把`set`成功误解为目标PCM已经可用。

现有QIVW诊断owner在打开reader前显式请求VOICE，reader重开后等待VOICE READY，随后reset ring以丢弃预热静音和旧队列帧。`API_MEDIA` owner新增`diag.api.media.speech_profile.{set,get,wait}.run`，可配合audio stop/start在设备上验证CALL切换；诊断入口不是RTC业务owner。仓内仍未找到Agora/RTC接听与挂断实现，真实产品owner必须调用相同事务。

fresh验证依次通过AISpeech 1000轮/2000次切换、API/App object、AISpeech/HDI/API/App static+dynamic library和PCR02 app链接。最终应用BuildID为`8178a06583196baa14209952707b7edba0583b1d`，SHA-256为`7ed7772fb5f681184cf3b812cb51b320675a2ccf76f28abfb81b550af35c7f17`。`libapi.so`导出set/get/wait，`libapp.so`包含QIVW owner引用和三条profile诊断命令。最终PCR02当前未启用APP diag runtime，故不能用最终ELF中是否保留这些gc-section判断库级接口有效性。

### 2026-08-26 AISpeech公共头依赖边界修正

HDI不得直接把`modules/aispeech/sevc/include`或`modules/aispeech/base/include`加入编译路径。当前HDI只依赖`libs/3rdparty/aispeech/include`；`sevc_api.h`已改为仅依赖`stdint.h`的自包含公共契约，不再泄漏`AISP_TSL_types.h`及`S16/U32/VOID`私有类型。源码头与libs公共头逐字节一致，公共头check/sync脚本覆盖AISpeech特殊映射。

clean HDI重建生成的depfile明确指向`libs/3rdparty/aispeech/include/sevc_api.h`，私有include路径负搜索无命中。公共头分别以C11/C++17、`-Wall -Wextra -Werror`独立编译通过；AISpeech 1000轮、ARM AISpeech/HDI和最终app顺序构建通过。最终app BuildID更新为`7be74d8ee245744cd72dbb145d2206272eeb0740`，SHA-256为`86b076c53532a1fc550a61aad1b2d8a5be94db991c3fd2fdda6b84eab7a4eb6f`。
