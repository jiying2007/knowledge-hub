---
id: pcr02-dual-a32-system-cpu-optimization-plan-20260721
title: PCR02 双核 A32 整机 CPU 优化规划
kind: debug-record
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/archive/debug/2026-07-21-pcr02-dual-a32-system-cpu-optimization-plan.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: session-derived-plan
  from: 2026-07-21 current Codex session latest-source read-only analysis and archived runtime evidence
  source_sha256: 8cdca9d22a90f5e1ec6670dbc8f8af50792ac95cb470e2c3eceffb0b715652fd
  temporary_source_retained: false
review_after: '2026-10-21'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- pcr02
- cpu-optimization
- dual-core-a32
- camera
- display
- audio
- bridge
- imu
- tof
validation_refs:
- projects/xcrz-sigmastar-demo/archive/debug/2026-07-21-pcr02-dual-a32-system-cpu-optimization-plan.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/archive/debug/2026-07-21-pcr02-dual-a32-system-cpu-optimization-plan.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-07-21'
updated_at: '2026-07-21'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-07-21'
manual_validation_pending: true
summary_zh: 基于最新源码和既有高负载证据，将优化目标从单独保障 IMU/TOF 周期扩展为双核 A32 整机 CPU 预算治理，优先减少媒体转换、显示刷新、重复协议处理、音频轮询、日志和无效唤醒，再评估传感器 FIFO 与调度策略。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
---

# PCR02 双核 A32 整机 CPU 优化规划

## 来源与边界

- captured_at：2026-07-21。
- 来源：当前 Codex 会话对最新父仓及 `modules/hdi`、`modules/api`、`modules/sensor` 源码的只读核对，以及既有 `pcr02-imu-tof-high-load-scheduling-triage-20260721` 运行态归档。
- 平台：SigmaStar SSC305，双核 Cortex-A32。
- 本文是 reviewing 优化候选，不是已验证结论、生产默认配置、owner 决策或发布声明。
- 未保留设备地址、PID/TID、完整日志、二进制、客户资料或凭证。

## 目标调整

此前工作以 IMU 100Hz、TOF 15Hz 的采集和发布时间稳定性为重点。最新范围调整为整机 CPU 预算治理：优先减少无效计算、像素转换、内存复制、协议转换、周期唤醒和锁竞争，为 Camera、Display、Audio、AI、WiFi、Bridge、运控和 Sensor 并发保留调度余量。

IMU/TOF 频率是整机优化后的验收项，不再作为唯一优化对象。线程优先级、CPU affinity 和实时调度只能改善调度顺序，不能降低 CPU 消耗，因此应放在减载之后。

## 当前代码事实

1. Sensor worker 已使用 `steady_clock` 绝对周期、condition-variable deadline 和超期跳周期；生产时序统计默认关闭。
2. IMU 活动 ODR 为 250Hz，软件目标 100Hz，FIFO 未启用；当前寄存器快照模式无法恢复调度停顿期间的中间样本。
3. TOF 硬件 15Hz、软件 20Hz 检查 data-ready，允许丢帧；IMU 与 TOF 分别使用 I2C2、I2C3。
4. Camera 使用单路 640x360 NV12 RAW Preview 物理流，按需派生 LCD_PREVIEW、QR_SCAN、VISION_RGB；该架构边界应保留。
5. 活跃虚拟流仍可能逐帧执行 NV12→RGB888、裁剪缩放、标量 BGR565 转换，并将结果再次复制到 SHM。
6. Display manager 约 25fps 调度，provider 存在 full-refresh 和 framebuffer memcpy 回退路径。
7. Bridge 的 IMU、TOF、Motor 等路径存在 source protobuf parse、Bridge serialize、再 parse 为 Vosen、再次 serialize 的重复工作，并可能在只有一种外部订阅时仍构造两种消息。
8. Audio capture/process/codec 保持低时延周期任务；优化应以事件驱动、按需启停和 buffer 复用为主，不能简单降频。
9. Camera FPS proto 注释为 1～30，sensor 只拒绝 0，而 HDI 实际只接受配置的 high/low；camera open 路径需要幂等或引用计数。

## CPU 优化顺序

### P0：建立整机 CPU 账本

在 BuildID 匹配的设备诊断包上固定负载矩阵：空闲、低 FPS、VISION_RGB、LCD+VISION_RGB、LCD+QR+VISION_RGB，以及 WiFi 重连、RTC、主/低码流、Audio、显示动画、IMU、TOF、运控并发场景。

采集进程和线程 CPU、run queue、voluntary/nonvoluntary context switch、schedstat、IRQ、CPU 频率、Video callback、SHM commit、Display refresh、Audio callback 和 Sensor deadline 指标。通过场景差分确认真实热点，不按源码体量猜测。

### P0：消除不该发生的工作

1. 保持物理 RAW Preview 20fps 契约，为 VISION_RGB、QR_SCAN、LCD_PREVIEW 增加独立消费者频率；在格式转换前跳过不需要的帧。
2. Camera open/close 使用幂等状态或引用计数；相同 FPS 请求 no-op；FPS 只允许 high/low，避免重复 pipeline 重建。
3. Bridge 仅为已订阅 topic 构造消息，移除 serialize→parse 转换，并复用 protobuf/string 容量。
4. 静态显示无变化时停止重绘，只在动画 deadline 或新预览帧到达时刷新。
5. 无 AI、QR、LCD、Audio SHM 或 Bridge 消费者时，相关转换、复制和发布必须停止。

### P1：降低像素转换和内存带宽

1. 分别测量 VISION_RGB、LCD_PREVIEW、QR_SCAN 的转换成本。
2. 优先使用 libyuv NEON 或 SigmaStar SCL/GFX，替换 LCD 标量像素循环。
3. 评估 producer 直接写入 frame-pool/SHM writable buffer，减少归一化 buffer 到 SHM 的第二次大帧复制。
4. 检查 Display 是否实际进入 single-fb direct；若持续走 full-frame memcpy 回退，优先解决回退原因。
5. Display partial refresh 必须与残影、撕裂、双屏同步一起 A/B，不为省 CPU 破坏视觉正确性。
6. Audio 保持 10ms 时延契约，通过 buffer pool、事件唤醒、VAD gate、无消费者停发和移除回调内日志降低成本。

### P1：减少唤醒、线程和锁竞争

合并低频 timer/poller；关闭生产诊断；日志热路径只计数、低频汇总；WiFi 已连接状态降低扫描频率；无消费者时不做 protobuf 构造；排查多个 10ms/20ms/100ms 周期线程能否事件化。

### P1/P2：Sensor 连续性和调度

完成整机减载后再评估 QMI8658 FIFO。FIFO用于保存调度停顿期间的硬件样本和批量 I2C，不保证降低最终 100Hz protobuf 发布成本。不能直接开启现有参考宏，必须补齐批量 API、逐样本时间戳、overflow、suspend 时关闭 FIFO/启用 AMD、resume 时反向恢复等闭环。

nice、affinity、SCHED_RR 必须最后 A/B。不能把包含 protobuf/ZMQ 的当前完整 worker 直接提升为高优先级 RT；也不能只提升 IMU 而忽略 nav.motor、Audio、RTC、3A 和 IRQ 的优先级关系。

## 建议任务包

| ID | 优先级 | 内容 | 估算 |
| --- | --- | --- | ---: |
| C0 | P0 | BuildID 对齐和整机线程级 CPU/唤醒基线 | 3h |
| C1 | P0 | 虚拟视频流独立频率、转换前丢帧 | 4～6h |
| C2 | P0 | Camera open/close/FPS 幂等与契约收敛 | 3h |
| C3 | P0 | Bridge 按订阅转换，移除重复 protobuf | 3～4h |
| C4 | P0 | Display 静态休眠和动画 deadline 驱动 | 5～8h |
| C5 | P1 | Camera NEON/硬件转换和减少 SHM 复制 | 6～8h 原型 |
| C6 | P1 | Audio buffer pool、事件化和按需处理 | 4～6h |
| C7 | P1 | 生产日志、诊断和周期线程治理 | 3～5h |
| C8 | P1 | IMU FIFO、批量采样和采样时间戳 | 6～8h |
| C9 | P2 | nice、affinity、SCHED_RR A/B | 3～4h |
| C10 | P0 | 整机压力和低功耗回归 | 6h |

## 验收候选

- 相同最重稳定业务场景下，总 CPU 相对基线至少下降 15%；完整阶段目标 20%～30%。
- 双核总容量中持续保留可观调度余量；绝对门槛由 C0 基线固化。
- runnable 线程、无效唤醒和上下文切换相对基线下降至少 20%。
- 无消费者时三路虚拟视频转换次数为 0；AI 10fps 时 VISION_RGB 不固定转换 20fps。
- 静态眼睛场景不持续 25fps 整屏刷新；残影、撕裂和双屏同步不回归。
- Audio 无 underrun/overrun，录音、播放、VAD 和 RTC 时延不回归。
- IMU 60秒窗口逻辑频率 99～101Hz或样本缺口可检测；TOF 稳态约 14～15Hz并允许明确丢帧。
- WiFi重连、Camera打开、编码启动等瞬时场景不造成持续单核打满。
- suspend/resume、MCU IMU Any-Motion 和 TOF 目标距离唤醒语义不回归。

## 风险与回退

- 降低虚拟流频率可能影响 AI、QR 和预览体验；所有频率必须配置化并按场景回退。
- Display partial refresh 可能重新引入视觉问题；失败时保留 full refresh，但静态场景停止重复提交。
- 零拷贝会引入 frame lifetime 风险；生命周期证据不足时保留一次复制。
- Audio 周期事件化可能改变时延；出现 underrun、VAD或RTC回归时回退原周期路径。
- Affinity 可能加重 IRQ/跨核 IPI；只有 A/B 指标改善才可成为默认值。
- 本规划需要与源码 BuildID 匹配的设备重复验证，未经验证不得提升为 current 或生产规则。

## 关联

- `pcr02-imu-tof-high-load-scheduling-triage-20260721`：既有 CPU 饱和、RT线程抢占、IRQ集中和传感器周期退化证据。
- `pcr02-camera-raw-preview-virtual-stream-architecture-20260711`：单物理 RAW Preview 与三路虚拟流边界。

