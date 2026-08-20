---
related:
- projects/xcrz-sigmastar-demo/archive/debug/2026-07-13-agora-downlink-audio-starve-tail-loss.md
incident_id: null
severity: major
affected_version: PCR02 source commits b47220e / 3889512 / 08d593f
id: pcr02-sensor-audio-queue-ao-retry-20260731
title: PCR02 Sensor audio queue 满与 MI AO 非对齐重试闭环
kind: debug-record
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/archive/debug/2026-07-31-pcr02-sensor-audio-queue-ao-retry.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: current-codex-session-and-source-validation
  from: PCR02 audio queue/MI AO排障、源码提交与构建验证
  source_sha256: da976d0b2942ffd371c2ede1a6bc37fff3089dbb169ed63165ed1308d5b60f10
  temporary_source_retained: false
review_after: '2026-10-31'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- pcr02
- audio
- sensor
- mi-ao
- queue-backpressure
- pcm-alignment
- cpu-hotloop
validation_refs:
- projects/xcrz-sigmastar-demo/archive/debug/2026-07-31-pcr02-sensor-audio-queue-ao-retry.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/archive/debug/2026-07-31-pcr02-sensor-audio-queue-ao-retry.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-07-31'
updated_at: '2026-07-31'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-07-31'
manual_validation_pending: true
summary_zh: 记录PCR02非对齐PCM触发MI AO失败、retry=0负数无限循环并放大为播放器高CPU与Sensor audio queue饱和的证据链、跨层修复、提交锚点和待完成板端压力验证。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
---

# PCR02 Sensor audio queue 满与 MI AO 非对齐重试闭环

## 摘要

PCR02 语音播放链路曾出现 Sensor audio task queue 深度达到 128、`sensor_audio0` 长时间阻塞、播放器线程高 CPU，以及 MI AO 持续拒绝 15-byte 非对齐 PCM 数据。源码和运行时证据确认，直接放大器是 AO 重试循环在调用方传入 `retry=0` 时发生负数无限循环：首次写失败后计数变为 `-1`，循环条件长期为真。非法输入、错误码丢失、无限等待和缺少入口校验共同使问题扩散到上游队列。

本轮修复覆盖 Sensor 输入、PCM parser/render、memory stream 和 HDI/AO 四层。源码构建和最终应用构建通过；板端最小播放 smoke 正常，仅观察到一次可自动恢复的瞬时 ring 背压。随后已修正该瞬时背压 WARNING 的误报条件。完整压力 HIL 尚待执行。

## 现象与证据链

### 运行时现象

- `sensor_audio0` 处于 futex wait，连续采样时上下文切换计数不变。
- 一个 `api_player0` 线程长期 running，CPU 占用较高，累计 CPU 时间以 system time 为主。
- 连续读取线程 syscall 状态均为 `running`，说明线程未稳定阻塞在可识别系统调用上。
- MI AO 持续报告 PCM 数据大小 15 bytes，不满足 2-byte sample alignment。
- 历史同链路记录曾观察到外层 audio task queue 固定达到深度 128。

### 根因链

1. 上游产生或传入非对齐 PCM packet，例如 15 bytes。
2. MI AO 拒绝该 packet。
3. `SSPLAT_AO_SendPacket()` 原实现对 `retry=0` 使用先执行、后递减的循环；首次失败后计数变为负数，循环不退出。
4. 播放消费者持续重试并消耗 CPU，不能继续稳定消费 memory stream。
5. memory stream 写端和 `sensor_audio0` 产生反压，最终放大为外层队列饱和。
6. AO 和 render 返回值此前被多层丢弃，使失败无法及时终止和定位。

## 修复范围

### HDI / AO

- `modules/hdi/src/hdi_plat_ss/ssplat_ao.c`
  - 每个 packet 使用独立 `remainingRetry`。
  - `retry=0` 只尝试一次；失败立即返回。
  - 不再存在负数无限重试。
- `modules/hdi/src/hdi_audio/hdi_ao.c`
  - 拒绝空数据、超限数据和非 2-byte 对齐数据。
  - 普通 AO 写入使用 1000 ms 有界超时。
  - 传播并记录 `SSPLAT_AO_SendPacket()` 真实错误码。

### API player

- `modules/api/src/api_audio_player/api_player.c`
  - 初始化 PCM parser packet。
  - 严格处理 parser peek/read 状态。
  - 按 `channels * bits / 8` 校验 PCM frame alignment。
  - render 失败终止当前 decode，不再静默吞错。
  - 按 scene 设置 `api_p_rtsa`、`api_p_voice`、`api_p_media` 等线程名。
- `modules/api/src/api_audio_player/stream/mem/api_player_stream_mem.c`
  - memory ring 写满时采用 1000 ms 周期诊断和 5000 ms 最大等待。
  - 超过 5 秒返回失败，避免永久拖死 Sensor worker。
  - 只有累计等待达到 1000 ms 才输出 WARNING；瞬时满环后正常唤醒不再误报。
  - WARNING/ERROR 增加 `wait_ms`、ring 状态和累计读写量。

### Sensor 输入

- `modules/sensor/main/sensor_entry.cpp`
  - 在 ZMQ、downlink SHM 和 AI SHM 三个入口校验 PCM metadata 与 payload alignment。
  - 非法 PCM 在进入外层 audio task queue 前被拒绝。
  - 日志保留 source、sequence、scene、采样参数、payload bytes 和 frame bytes，不记录语音内容。

## Ring 容量判断

当前 memory ring 为 10240 bytes。对于 24 kHz、16-bit、mono PCM：

- 数据率为 48000 bytes/s；
- 10240 bytes 对应约 213 ms；
- parser 每次读取 2048 bytes，对应约 42.7 ms；
- ring 可容纳 5 个 parser frame。

板端只出现一次瞬时背压并自动恢复，后续播放正常，因此本轮不扩大 ring。直接扩容可能掩盖消费者停滞并增加旧音频积压；只有压力回归证明正常负载下长期告警或可听断音时，才优先评估 20480 bytes，并同步验证播放延迟和 STOP 清空语义。

## 源码与制品锚点

三个独立源码仓当前提交：

- HDI：`b47220e3751240ff155cd2142ee7ebe3853c44c0`
- API：`38895125f80190c01147461a2c48058add07cc14`
- Sensor：`08d593f8cb2e14d42c887dd747c67d38e28aff23`

当前最终应用候选：

- size：9511800 bytes
- MD5：`8aff804702506c758425758510266220`
- BuildID：`25d3c874ee32406ae77a846da645077960a752bc`
- build time：2026-07-31 20:20:55 +0800

制品身份只用于本次候选追踪；app、image 和 OTA 是不同阶段，后编译 app 不会自动进入既有 image/OTA。

## 验证证据

源码和构建验证：

```text
rtk make modules/hdi_obj_all -j20       PASS
rtk make modules/api_obj_all -j20       PASS
rtk make modules/sensor_obj_all -j20    PASS
rtk make pcr02 -j20                     PASS
三个源码子仓 git diff --check           PASS
rtk bash ~/codex/scripts/final-ready.sh PASS
```

最终 ELF 已确认包含新增的 PCM alignment、AO failure、memory stream timeout、`wait_ms` 和 scene thread-name 诊断字符串。

板端最小 smoke：

- `api_p_voice` 正常启动；
- 出现一次 memory ring 瞬时背压后自动恢复；
- 后续播放正常；
- 未观察到 memory stream 5 秒 timeout 的证据。

该 smoke 发生在瞬时 WARNING 降噪修复前；最新候选仍需重新部署，确认短时满环不输出 WARNING，并核对 `wait_ms >= 1000` 才产生真实阻塞告警。

## 2026-08-05 旧库触发 SOC_REBOOT 卡死复现

### 现场现象与时间线

设备使用 2026-07-30 生成的 API 库运行时，收到 SOC_REBOOT 请求后进入应用关闭流程，但未执行到 SoC 软件复位。现场只保留脱敏摘要，不归档完整 raw log、进程号或设备身份。

| 时间 | 观察 | 结果 |
| --- | --- | --- |
| 14:26:34 | Sensor 接受并预留 SOC_REBOOT | 请求进入协调关闭流程 |
| 14:26:35 | App 开始 `sensor_module.deinit_before_soc_reboot` | 外层关闭步骤不再完成 |
| 14:26:37 | `sensor_prep0` 异步释放视频源并打印 `VideoCapture deinitialized` | 仅证明异步视频准备线程完成，不证明主线程已越过音频 worker 退出门禁 |
| 14:38 后 | IrLight 仍持续输出状态，应用进程仍存在 | 主线程尚未执行到 `IrLight::deinit()`，SoC 未复位 |

### 线程证据摘要

只读 `/proc/<pid>/task/*/{comm,wchan}` 和 `top` 采样显示：

- 主线程 `prog_pcr02` 位于 futex wait，符合等待子线程退出的状态。
- `sensor_audio0` 仍存在并位于 futex wait；正常收到 `stopAudioWorker()` 的停止标志和条件变量通知后，该线程应退出并被 join。
- 两个 `api_player0` 实例中，一个正常阻塞在 poll，另一个处于用户态 runnable，单核 CPU 占用约 46%。
- `sensor_in0`、`sensor_devctrl` 和 `sensor_out0` 已消失，说明关闭流程已越过前三个 Sensor 工作线程的 join。
- 内核未导出可用的 `/proc/<tid>/stack` 内容，因此没有现场用户态调用栈；结论依赖线程状态、CPU 行为、源码关闭顺序和版本时间线联合收敛。

### 与源码和版本时间线的映射

`SensorEntry::deinitBeforeShutdownConfirm()` 先停止 SHM 音频输入，再调用 `stopAudioWorker()`。后者清除任务、设置停止标志、广播条件变量，随后无超时 `join()` `sensor_audio0`。现场仍存在 `sensor_audio0`，说明它没有停留在正常任务队列等待路径，而是阻塞在任务执行的下层调用中。

设备使用的 2026-07-30 API 库早于提交 `38895125f80190c01147461a2c48058add07cc14`（2026-07-31 20:15 +0800），因此不包含以下保护：

1. PCM parser packet 初始化和 parser 状态严格校验；
2. PCM frame alignment 校验与 render 错误传播；
3. memory stream 写满后的 5000 ms 最大等待；
4. 按 scene 区分的播放器线程名。

旧版 memory stream 在 ring 满时使用 `VS_TIMEOUT_INFINITY`。结合一个 `api_player0` 用户态忙循环、另一个播放器实例正常 poll，可形成高置信因果链：异常播放器实例不能稳定消费 memory stream，`sensor_audio0` 写满后无限等待，主线程再阻塞于 `stopAudioWorker().join()`，后续 Sensor deinit 和 `VSHDIOS_Reboot()` 均无法执行。

2026-07-30 15:31 的提交 `33b422a2aaf1c40fb0e18ac9e2ec74b0667796c9` 已增加请求同步和 5000 ms 有界播放器线程销毁，但现场仅能确认“使用 2026-07-30 库”，不能确认该库生成于当天提交前还是提交后。本次卡点位于 Sensor audio worker 退出阶段，不依赖是否已包含该有界销毁修复。

### 结论与证据边界

- 根因状态：`high-confidence / repair-validation-pending`。
- 已支持：旧 API player 异常消费与无限 memory-stream 写等待能够阻断 `sensor_audio0` 退出，并进一步阻断 SOC_REBOOT。
- 已排除：`VideoCapture deinitialized` 不是主线程已完成 Sensor safe deinit 的证据；它来自并行的 `sensor_prep0`。
- 未完成：现场 `libapi.so` 的 MD5/BuildID 尚未绑定，未取得用户态 backtrace，也未用包含 `3889512` 的制品执行同条件修复后复验。

### 修复后复验门禁

1. 部署并核对包含 `33b422a`、`3889512` 及对应 HDI/Sensor 修复的 app 和动态库身份；运行中进程必须重启后才会加载新库。
2. 在流式音频活跃和播放器背压条件下触发 SOC_REBOOT，确认 `api_p_voice`/`api_p_rtsa` 无持续高 CPU。
3. 确认 `sensor_audio0` 能有界退出，`sensor_module.deinit_before_soc_reboot` 完成，并实际观察 boot identity 变化。
4. 先执行单次 smoke，再执行 5～10 次短循环；出现 core、致命 dmesg、状态泄漏或制品身份漂移时停止扩大。
5. 修复后证据闭环前，本记录保持 `reviewing / latest-device-validation-pending`，不得提升为发布就绪结论。

## 负结果与边界

- 无法使用 GDB 获取现场用户态 backtrace，根因通过 `/proc` 线程状态、CPU/system time、syscall 采样、MI AO 日志和源码循环共同收敛。
- 仓库没有可直接运行的 audio player/memory stream 单元测试，本轮以定向构建、静态逻辑核验和板端最小 smoke 代替。
- 顶层仓库包含大量既有 dirty 生成库和无关改动；本轮源码分别在 HDI、API、Sensor 独立仓提交，顶层生成物不作为源码提交证据。
- 尚未完成 10～1000 次连续播放、CPU 高负载、双连接、STOP 后立即新 TTS、image/OTA 和长时间 soak。

## 后续验证

1. 部署 BuildID 匹配的最新 app，确认 MI AO 非对齐错误不再持续增长。
2. 正常播放时瞬时满环不应输出 WARNING；真实 WARNING 的 `wait_ms` 必须至少为 1000。
3. 确认 `api_p_voice`/`api_p_rtsa` 无持续高 CPU，`sensor_audio0` 上下文切换持续推进。
4. 确认 audio queue high-watermark 不再达到 128，memory stream 不出现 5000 ms timeout。
5. 覆盖正常 TTS、播放中 wakeup、STOP 后立即新 TTS、10 次短循环，再逐级放大到 100～1000 次和 soak。

## 归档门禁

- Source：当前 Codex 会话、源码提交、构建结果和用户提供的脱敏板端观察。
- Sanitization：通过；未包含音频内容、设备端点、凭证、完整 raw log、core 或二进制。
- Provenance：current-codex-session-and-source-validation。
- Memory Candidate：no；该结论保持为 PCR02 项目专用记录，不提升为全局规则。
- Gate Result：`reviewing / latest-device-validation-pending`。
