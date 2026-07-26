---
maturity: candidate
id: pcr02-imu-tof-high-load-scheduling-triage-20260721
title: PCR02 IMU/TOF 高负载调度尾延迟现场分析
kind: debug-record
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/archive/debug/2026-07-21-pcr02-imu-tof-high-load-scheduling-triage.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: session-derived-debug-summary
  from: 2026-07-20 user-provided sensor log excerpt and read-only ADB runtime capture; device endpoint deliberately not retained
review_after: '2026-10-21'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; reviewing debug evidence only, no active promotion, owner decision, release claim or memory write
tags:
- pcr02
- prog_pcr02
- imu
- tof
- scheduling-latency
- cpu-saturation
- irq-affinity
- sched-rr
- video-preview
- audio-wakeup
- runtime-monitoring
- adb
- build-mismatch
- manual-validation-pending
validation_refs:
- projects/xcrz-sigmastar-demo/archive/debug/2026-07-21-pcr02-imu-tof-high-load-scheduling-triage.md
- rtk bash ~/codex/scripts/final-ready.sh
- 'manual_validation_pending: true'
- 'reason: single runtime window and deployed/local BuildID mismatch; requires matching diagnostic build and repeated worst-case validation'
evidence_strength: single-window-runtime-capture-plus-source-correlation-with-build-mismatch
evidence_refs:
- projects/xcrz-sigmastar-demo/archive/debug/2026-07-21-pcr02-imu-tof-high-load-scheduling-triage.md
- 2026-07-20 current Codex session read-only ADB /proc thread, IRQ, scheduler and memory capture; raw output not retained
- user-provided sensor loop statistics excerpt; raw log not retained
related:
- pcr02-prog-pcr02-high-load-monitoring-20260702
- pcr02-prog-pcr02-runtime-hot-thread-followup-20260710
created_at: '2026-07-21'
updated_at: '2026-07-21'
generated_by_ai: true
ai_role: summarized
ai_model_or_tool: Codex
ai_generated_at: '2026-07-21'
summary_zh: 2026-07-20 对 PCR02 双核 A32 设备进行只读运行态分析。摄像头、编码、音频和 RTC 启动后，IMU 由接近 100Hz 降至约 76–82Hz，TOF 由约 15Hz 降至约 13.5–14.8Hz；传感器 I/O error 为 0。整机 CPU 忙碌约 98.1%，AgoraRTC/RTCCB 为 SCHED_RR 96、CUS3A 为 SCHED_RR 95，而 IMU、TOF、运控、显示和普通媒体线程均为 SCHED_OTHER；媒体及 I2C IRQ 实际集中 CPU0。结论指向 CPU 饱和、实时线程抢占、IRQ 集中以及采集/序列化/发布同线程的叠加尾延迟，而非定时器或单一 I2C 故障。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
manual_validation_pending: true
manual_validation_reason: 需要部署与当前源码 BuildID 一致的诊断包，在 RTC、视频、显示、语音和运控同时运行的最重场景重复采样并验证优化收益
---

# PCR02 IMU/TOF 高负载调度尾延迟现场分析

## Source

- 采集日期：设备日志和运行态证据为 2026-07-20，归档于 2026-07-21。
- 平台：PCR02，SigmaStar SSC305，双核 Cortex-A32。
- 数据来源：用户提供的 sensor loop 统计日志，以及授权设备上的只读 ADB `/proc`、BusyBox `top`、线程 stat、IRQ 和调度策略采样。
- 操作边界：未重启设备，未停止进程，未修改配置、CPU affinity、线程优先级或设备文件。
- 脱敏边界：设备 IP、PID/TID、完整 raw log、二进制和客户资料不进入长期正文。

## Symptom

轻负载阶段：

- IMU `target_hz=100`，可达到 `loop_hz=99.99`、`publish_hz=99.79`。
- TOF 硬件输出约 15Hz，以 20Hz 检查 data-ready，发布约 15.1Hz。

摄像头、编码流、音频、Wi-Fi 和 RTC 等链路启动后：

- IMU `loop_hz` 多次下降至约 76–82Hz，`publish_hz` 约 74–81Hz。
- IMU 单个 10 秒窗口可出现约 147–184 次 deadline miss、173–235 个 skipped period。
- IMU `max_acquire_us` 可达约 30–78ms，`max_serialize_us` 可达约 22ms，`max_publish_us` 可达约 37ms。
- TOF 发布下降至约 13.5–14.8Hz，`max_acquire_us` 可达约 153ms，`max_publish_us` 可达约 85ms。
- IMU/TOF `io_error=0`，驱动级 `throttled=0`。这里的 `throttled` 是 I/O 错误退避状态，不代表 CPU 温控状态。

## Runtime Evidence

### CPU 与内存

- 约 12.8 秒采样窗口内，双核总 CPU busy 约 `98.1%`。
- load average 快照约 `34.50 / 31.66 / 29.95`，可运行任务约 `23/242`。
- `prog_pcr02` 约 121 个线程。
- `MemAvailable` 约 42MB，未启用 swap；短窗口没有证据表明内存泄漏或块设备 I/O 是首要瓶颈。
- `CmaFree=0` 是媒体缓冲风险信号，但不能单独解释 IMU 周期退化。
- 两个 CPU 均运行在约 1GHz，现场没有明显升频余量。

### 热点线程

线程 CPU tick 增量显示，主要热点包括：

| Thread | Approx. one-core CPU | Layer |
| --- | ---: | --- |
| `AgoraRTC` | 20.2% | RTC |
| `hdi_vi_preview` | 10.6% | raw preview |
| `sensor_disp0` | 10.2% | display/LVGL |
| `CUS3A` | 9.7% | ISP 3A |
| `ai-wakeup-aud` | 9.2% | wakeword audio |
| `hdi_ai_prc0` | 8.9% | HDI audio process |
| `task_poller` | 7.9% | task polling |
| `sensor_tof0` | 6.0% | TOF acquire/publish |
| `nav.poll` | 5.8% | navigation polling |
| `sensor_imu0` | 4.2% | IMU acquire/publish |

前 30 个用户态线程累计约占 1.35 个核心，其余算力还需承担内核、IRQ 和其他进程。

### 调度策略

- `AgoraRTC`：`SCHED_RR`，实时优先级 96。
- `RTCCB`：`SCHED_RR`，实时优先级 96。
- `CUS3A`：`SCHED_RR`，实时优先级 95。
- IMU、TOF、`nav.imu`、`nav.motor`、显示、视频预览和普通音频处理线程均为 `SCHED_OTHER`。

在双核接近满载时，高优先级 RTC/3A 线程会合法抢占普通 sensor 和运控线程。sensor 日志中的 acquire wall time 包含 I2C 调用期间被抢占的时间，因此几十毫秒的 `max_acquire_us` 不能直接解释为纯 I2C 传输耗时。

### IRQ 与跨核压力

约 12.8 秒窗口内的主要 IRQ 速率：

| IRQ | Approx. rate | Effective CPU |
| --- | ---: | --- |
| SDIO/MMC | 2068/s | CPU0 |
| I2C2，IMU | 322/s | CPU0 |
| BDMA | 306/s | CPU0 |
| MSPI | 304/s | CPU0 |
| I2C1，TOF | 242/s | CPU0 |
| ISP | 237/s | CPU0 |
| Function-call IPI | 3061/s | CPU0/CPU1 |

相关 IRQ 的 `smp_affinity_list` 显示 `0-1`，但 `effective_affinity_list` 实际为 CPU0，说明不能假设写 affinity 后一定可迁移。高 Function-call IPI 同时提示跨核调用和唤醒压力明显。

## Source Correlation

当前本地源码与现场现象存在以下高相关设计点：

1. `modules/sensor/common/sensordev_base.cpp`
   - 同一 sensor worker 顺序执行 I2C acquire、校准判断、protobuf serialize 和 ZMQ publish。
   - 使用绝对 deadline 和超期跳周期，周期算法本身方向正确；CPU 不足时会主动跳过过期槽，避免补跑风暴。
2. `modules/sensor/tof/tof.cpp`
   - TOF 硬件输出 15Hz，但软件以 20Hz 检查 data-ready；正常就会产生约 5 次/秒的额外状态读取。
3. `modules/sensor/lib.mk`
   - `SENSOR_TIMING_STATS_ENABLE ?= 1`，与生产版本默认关闭诊断统计的预期不一致。
4. `modules/hdi/src/hdi_drv/hdi_imu/qmi8658/qmi8658.h`
   - QMI8658 active ODR 为 250Hz，FIFO 当前未启用。
5. `modules/api/src/api_video_pipe/api_video.c`
   - raw preview 可在同一回调中执行 LCD NV12→BGR565、QR crop/scale、Vision NV12→RGB888，再复制到 SHM。
6. `modules/hdi/src/hdi_audio/hdi_ai.c`
   - capture/process/codec 使用多个 10ms 周期 task，可进一步改为数据到达事件驱动。
7. `modules/sensor/hardware/hardware_api.cpp`
   - 现场短时间内多次记录 camera pipeline opened；需要确认 resume 和 DVR media resume 是否真正幂等或具备引用计数。

### Binary Boundary

现场 `/customer/bin/prog_pcr02` 与本地 `out/arm/app/prog_pcr02` 的 MD5 和 GNU BuildID 均不一致。运行态 CPU、调度和 IRQ 结论可信；上述源码映射属于高相关推断，不能当作设备二进制的逐行精确证明。

## Diagnosis

当前最符合证据的因果链为：

```text
视频/RTC/3A/显示/语音并发
  → 双核 CPU 接近饱和
  → RT96/95 线程抢占普通 sensor/运控线程
  → 媒体和 I2C IRQ 集中 CPU0，跨核 IPI 增加
  → acquire 调用内和 publish/serialize 阶段出现长尾
  → sensor 绝对周期检测到超期并跳槽
  → IMU 发布降至约 76–82Hz，TOF 降至约 13.5–14.8Hz
```

因此主要矛盾不是 `LoopSleepMs`、cond 精度或单次 heap 分配，而是调度预算和关键路径耦合。

## Recommended Optimization Order

### P0

1. 拆分 IMU acquisition 与 serialize/publish：
   - acquisition 线程只做 I2C、采样时间戳和固定容量 SPSC ring/latest slot 写入。
   - protobuf 和 ZMQ 放到普通优先级发布线程。
   - 拆分并验证有界执行后，再评估最低档 `SCHED_RR`；不能直接把包含 protobuf/ZMQ 的当前 worker 整体提升为 RT。
2. TOF 采用可丢帧 latest-only：
   - 轮询由 20Hz 降至 15Hz；若固定相位导致 ready 命中不稳定，可试 16Hz。
   - 容量 1，覆盖旧帧，不补发、不积压。
3. raw preview 减载：
   - 只转换有订阅者的输出。
   - LCD/QR/vision 按业务降低 FPS，避免三个输出同时 20fps 软件转换。
   - 优先让 SCL 输出目标尺寸/格式；LCD 标量 YUV→RGB565 改为硬件或 NEON/libyuv 路径。
4. 音频链路事件化：
   - process/codec 由采集到帧事件唤醒，减少 10ms 无数据轮询。
   - RTC 活跃时按产品要求暂停或降级 wakeword，或至少启用 VAD gate。
5. 显示自适应刷新：
   - 动画维持 20–25fps，静态场景降至 5–10fps。
   - dirty rectangle、请求合并和 latest-only flush。
6. camera pipeline resume 增加幂等状态或 refcount，仅在 `0→1` 和 `1→0` 做真实 resume/suspend。
7. 量产默认设置 `SENSOR_TIMING_STATS_ENABLE=0`，诊断包显式打开。

### P1

- QMI8658 FIFO：现场 30–78ms 调度停顿已经证明 FIFO 对保留物理样本有价值。
  - 使用小 watermark 和 stream mode，100Hz 批量读取。
  - 运控实时通道取批次中最新样本；需要积分的消费者可处理完整批次。
  - 每个 FIFO 样本必须有硬件时间戳或按 250Hz ODR 重建时间，不能整批共用读取时刻。
  - FIFO 解决样本连续性和 I2C 批量效率，不能替代 CPU 减载，也不能把历史样本快速补发成实时数据。
- 若算法允许，将 TOF 8×8 降为 4×4，以减少 I2C 和解析量；这是协议/算法语义变更，必须单独确认。
- raw latest-only SHM buffer frames 可从 5 评估降至 2–3，减少内存和缓存占用。

### Affinity Boundary

- 先减载并拆分纯 acquisition thread，再做绑核 A/B。
- 比较 IMU 固定 CPU1 与留在 CPU0 两种方案的 wake latency、IPI、deadline miss 和 motor jitter。
- 不批量移动 IRQ；SigmaStar 中断控制器当前可能把 effective affinity 固定在 CPU0。
- `nav.motor` 的安全周期优先级必须高于普通发布和显示，不能只提升 IMU 而忽略运控线程。

## Negative Findings

- IMU/TOF 没有 I/O error 证据。
- 没有短窗口内存泄漏或 swap 证据。
- 没有块设备 I/O 打满证据。
- 现有绝对 deadline 和超期跳周期逻辑没有出现补跑风暴。
- TOF 驱动已关闭 ambient、SPAD、signal、sigma、reflectance 和 motion 等未使用输出，只保留 distance 与 target status；继续裁剪字段的收益有限。
- 单纯增加轮询频率、增大队列或只替换 sleep/cond 无法在 98% CPU busy 下恢复稳定 100Hz。

## Validation Contract

后续必须在以下最重业务组合下验证：Wi-Fi、RTC、main/low 编码、raw preview/vision、显示动画、wakeword、IMU 100Hz、TOF 15Hz 和运控同时运行。

建议验收指标：

- 双核稳态 CPU busy 低于 85%，保留至少约 15% 调度余量。
- IMU 60 秒窗口：`loop_hz >= 99`、`publish_hz >= 98`、`wake_late_p99 < 2ms`、`max_interval < 20ms`，deadline miss 接近 0。
- TOF 不补帧、不积压，latest publish 稳态约 14–15Hz，overwrite/drop 可观测。
- `nav.motor` 周期和尾延迟不得因 IMU 调度优先级调整而恶化。
- 每项优化单独做开关 A/B，记录线程 CPU、IRQ/s、IPI/s、deadline miss 和 sensor interval 分布。
- 使用与本地源码 BuildID 一致的设备诊断包重复至少两轮，再把结论提升为验证记录或 current runbook 更新。

## Evidence Template

- Source: 2026-07-20 user-provided sensor log excerpt and read-only ADB runtime capture.
- Topic: `pcr02-imu-tof-high-load-scheduling-triage`.
- Archive Candidate Path: `projects/xcrz-sigmastar-demo/archive/debug/2026-07-21-pcr02-imu-tof-high-load-scheduling-triage.md`.
- Sanitization: pass；未保留设备 endpoint、PID/TID、raw log、binary、secret 或 customer material。
- Provenance: 当前 Codex 会话；关联 2026-07-02 和 2026-07-10 的历史高负载归档。
- Verification: 只读运行态采样完成；`final-ready` 通过；匹配 BuildID 的改动后实机验证待完成。
- Memory Candidate: no。
- Gate Result: pass；正文、registry、索引、覆盖和检索门禁通过，结论生命周期仍保持 reviewing，等待匹配构建和重复最重场景验证。

## Boundary

- 本条目是 project-specific reviewing debug evidence，不是 owner decision、release gate 或 active rule。
- 不把阶段性调度参数静默提升为生产默认值。
- 不包含完整聊天记录、raw log、设备地址或设备二进制。
- 若后续补丁和重复验证通过，可新增 validation record；不直接覆盖本条历史证据。
