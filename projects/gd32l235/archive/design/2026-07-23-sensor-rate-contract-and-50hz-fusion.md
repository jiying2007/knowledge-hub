---
id: gd32l235-pcr02-sensor-rate-contract-50hz-fusion-20260723
title: PCR02 SoC 与 GD32L235 传感器频率契约及 50 Hz 融合方案
kind: project-archive
domain: projects/gd32l235
path: projects/gd32l235/archive/design/2026-07-23-sensor-rate-contract-and-50hz-fusion.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: working-tree-analysis-and-user-confirmed-contract
  from: workspace://gd32l235 and workspace://pcr02-ssc305 current working trees plus user-confirmed motor MCU 50 Hz contract,
    captured 2026-07-23
  source_sha256: 65fe87aa4655a9fcc365cbe437d4d06c4cb0be44ad87c23089056fab64de3e76
  temporary_source_retained: false
review_after: '2026-08-23'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- gd32l235
- pcr02
- sensor-rate
- motor-50hz
- fusion
- hil-pending
validation_refs:
- projects/gd32l235/archive/design/2026-07-23-sensor-rate-contract-and-50hz-fusion.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/gd32l235/archive/design/2026-07-23-sensor-rate-contract-and-50hz-fusion.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-07-23'
updated_at: '2026-07-23'
generated_by_ai: true
ai_role: summarized
ai_model_or_tool: Codex
ai_generated_at: '2026-07-23'
manual_validation_pending: true
summary_zh: 归档 PCR02 SoC 与 GD32L235 的传感器采样、轮询和发布频率，确认电机 MCU 输入 50 Hz 与当前 GD32→SoC 非固定频上报的契约缺口，并提出原始频率保留、导航层 50 Hz 融合时间轴及板测验收候选。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
---

# PCR02 SoC 与 GD32L235 传感器频率契约及 50 Hz 融合方案

## 摘要

本记录归档 2026-07-23 对 PCR02 SoC `modules/sensor` 与 GD32L235 MCU `App` 当前工作树进行的跨端源码核对，并纳入 owner 在会话中确认的硬约束：左右电机 MCU 各以 50 Hz 向 GD32L235 上报反馈。

核心结论是：所有物理传感器不应强制使用同一个采样频率；应统一频率术语、统计口径和下游时间轴。电机链路需要由 GD32L235 将两侧 50 Hz 输入整形成固定 50 Hz 的 `0x16` 底盘综合上报；IMU、ToF、红外、红外测距、环境光和电池继续保留原生频率。导航或聚合层可采用 50 Hz 公共时间轴，并用 `new_sample`、时间戳和 `age_ms` 区分新样本与保持值。

本条目是 `reviewing` 历史设计候选，不是 active 协议、已合入实现、发布签收或板级 HIL 通过结论。

## 来源与权威边界

- captured_at：2026-07-23（Asia/Hong_Kong）
- last_verified：2026-07-23
- MCU source：`workspace://gd32l235` 当前未提交工作树
- SoC source：`workspace://pcr02-ssc305` 当前未提交工作树
- 用户确认契约：左右电机 MCU 的反馈上报频率为 50 Hz
- MCU 协议：`workspace://gd32l235/Docs/串口通信协议规范.md`
- MCU 关键实现：`workspace://gd32l235/App/bsp.c`、`App/motor_protocol.c`、`App/ir_charge_station.c`、`App/ir_detect_dist.c`
- SoC 关键实现：`workspace://pcr02-ssc305/modules/sensor/imu/imu.cpp`、`tof/tof.cpp`、`serial/sensor_serial.cpp`、`ir/irlight.cpp`
- HDI 关键实现：QMI8658、VL53L8CX、ADC 和 VI/AE 相关驱动

若本文与后续已提交源码、正式协议或板级测量冲突，以已确认版本的源码、协议和 HIL 证据为准。本文不绑定一个确定 commit identity。

## RUNNING 状态频率矩阵

| 数据源 | 原始采样或输入频率 | 中间处理频率 | 当前对下游发布行为 | 建议契约 |
| --- | ---: | ---: | --- | --- |
| 左电机 MCU | 50 Hz | GD32 收帧触发 | 参与组合上报 | 输入固定 50 Hz |
| 右电机 MCU | 50 Hz | GD32 收帧触发 | 参与组合上报 | 输入固定 50 Hz |
| `0x16` 底盘综合数据 | 两侧各 50 Hz | 任一侧更新后尝试发送 | 受 10 ms 限流和相同 payload 去重影响，不保证固定 50 Hz | GD32 到 SoC 固定 50 Hz |
| IMU | QMI8658 硬件 250 Hz | SoC 轮询 100 Hz | 成功时最高 100 Hz | 原始 topic 保持 100 Hz |
| ToF | Active 15 Hz；低功耗 3 Hz | SoC 20 Hz 检查 data-ready | Active 约 15 Hz | 保持约 15 Hz |
| 红外近卫矩阵 | 边沿捕获和 6 ms 编码帧解码 | GD32 每 30 ms 生成批量快照 | 约 33.3 Hz，包含空状态快照 | 保持约 33.3 Hz |
| 红外测距 | 每个报告聚合 4 个 ADC 样本 | GD32 每 100 ms 启动一轮 | 约 10 Hz | 保持 10 Hz |
| 电池计量 | GD32 每 1 s 启动完整采样 | 分步读取电压、电量、温度和电流 | 变化触发；不变时约 11 至 12 s 保活 | 1 Hz 采样、事件发布 |
| 充电桩上下座 | GPIO 或状态变化 | 变化立即处理 | 事件上报，并每 5 s 保活 | 事件驱动 |
| 环境光 ADC | 无独立 ODR | SoC worker 100 ms 唤醒，约每 500 ms 读 ADC | 约 2 Hz | 保持 2 Hz |
| ISP 软件环境光 | 受摄像头默认约 30 fps 约束 | 约 30 ms 检查 | 状态变化触发 | 事件驱动 |

摄像头帧率、麦克风 16 kHz 音频采样和 QR 解码帧率属于媒体处理链，不与运动或距离传感器共用数值相同的 Hz 契约。

## 电机 50 Hz 契约缺口

已确认的目标链路是：

```text
左电机 MCU --50 Hz--+
                     +-- GD32L235 --固定 50 Hz-- SoC sensor/motor
右电机 MCU --50 Hz--+
```

当前 GD32L235 实现没有独立的 20 ms 周期聚合器：左右电机解析任务在各自收到新帧后分别调用 `motor_send_data_to_soc()`；发送函数只通过 `MOTOR_REPORT_MIN_INTERVAL_MS=10` 限制最高发送频率，并在 `MOTOR_DATA_REPORT_ONLY_LATEST=1` 时跳过相同 payload。

由此产生以下行为：

- 两侧反馈近似同时到达时，综合上报通常接近 50 Hz；
- 两侧反馈错相约 10 ms 时，综合上报可能接近 100 Hz；
- 静止且 payload 不变时，综合上报可能低于 50 Hz；
- 任一侧反馈超过 50 ms 未更新时，当前实现停止综合上报；
- SoC `SensorSerial` 收到一帧即发布一帧，不再做固定周期整形。

因此，仅把最小发送间隔从 10 ms 改成 20 ms，只能把上限约束到 50 Hz，不能生成稳定的 20 ms 周期，也不能消除相同 payload 去重导致的降频。

## 建议的 MCU 实现契约

GD32L235 应将电机接收和 SoC 发布解耦：

1. 左右电机 UART 解析任务只更新各自最新值、接收计数和接收 Tick。
2. 独立的 20 ms 周期任务检查左右数据有效性和新鲜度。
3. 两侧均有效且未超过 stale timeout 时，每周期组装一次 `0x16` 底盘综合快照。
4. 若契约要求固定 50 Hz，即使 payload 未变化也必须发送；内容去重只能用于日志，不能抑制周期快照。
5. 任一侧超时后不得继续把旧值伪装成新数据；应停止发送或通过后续协议扩展显式携带 validity。

建议使用具名配置：

```text
MOTOR_INPUT_RATE_HZ             = 50
MOTOR_SOC_REPORT_PERIOD_MS      = 20
MOTOR_FEEDBACK_STALE_TIMEOUT_MS = 50
```

UART 为 115200、8-N-1。`0x16` 的 28 字节扩展 payload 加约 10 字节协议开销后，固定 50 Hz 占用约 19 kbit/s，约为 UART 线速的 16.5%。红外批量上报约再占 5.7 kbit/s；正常流量下不存在明显的物理带宽阻塞，但仍需验证 TX 队列峰值、背压和控制帧抢占。

## 统一频率模型

“频率统一”应定义为统一描述模型，而不是统一数值。每个数据源至少应声明：

| 字段 | 含义 |
| --- | --- |
| `source_rate_hz` | 硬件或上游 MCU 产生新样本的频率 |
| `poll_rate_hz` | 当前处理器检查或读取数据的频率 |
| `publish_rate_hz` | 对下一级承诺的发布频率 |
| `mode` | `Periodic`、`DataReady`、`PollLatest` 或 `EventDriven` |
| `stale_timeout_ms` | 超过多久未更新即视为失效 |
| `timestamp_source` | 设备时间、MCU Tick 或 SoC 接收时间 |
| `low_power_rate_hz` | 低功耗频率或 OFF |

当前电机目标 profile 可表达为：

```text
source_rate_hz    = 50
publish_rate_hz   = 50
mode              = PeriodicSnapshot
period_ms         = 20
stale_timeout_ms  = 50
```

## 50 Hz 导航融合时间轴

电机固定 50 Hz 后，可以作为底盘导航的公共时间基准，但不改变原始 topic 的原生频率：

```text
NavigationSensorFrame @ 50 Hz
  motor        本周期新数据
  imu          最近两个样本、预积分结果或最新样本
  tof          最近值 + age_ms
  ir_matrix    最近值 + age_ms
  ir_distance  最近值 + age_ms
  light        最近值 + age_ms
  battery      当前状态 + age_ms
```

每个字段至少携带或派生：

```text
valid
new_sample
source_timestamp
receive_timestamp
age_ms
sequence
```

低频数据在 50 Hz 快照中只是保持最近值，必须设置 `new_sample=false` 并保留正确的 `age_ms`，不能把重复值计为新采样。

IMU 原始 topic 继续保持 100 Hz。每个 20 ms 导航周期通常对应两个 IMU 软件样本，优先保留两个样本或执行预积分；只取最新样本会丢失部分动态信息。ToF、红外矩阵、红外测距、环境光和电池不应为了对齐时间轴而伪造额外原始发布。

## 时间戳边界

当前 SoC 在接收 `0x16` 后使用主机时间生成 motor topic 时间戳，表示 SoC 接收时间，不是电机 MCU 原始采样时间。固定 20 ms 上报可以降低到达抖动，但不能消除 UART 排队和双电机错相。

第一阶段可继续使用接收时间。若导航对时间对齐要求提高，可在兼容旧 16/28 字节格式的协议扩展中增加 `sample_tick_ms`、`left_age_ms` 和 `right_age_ms`；不得直接破坏旧 SoC 解析。

## 验收标准候选

### 电机链路

- 左右电机 MCU 分别在 10 s 内产生 `500 ± 1` 个有效反馈帧。
- 两侧健康时，GD32L235 在 10 s 内向 SoC 发送 `500 ± 1` 个 `0x16` 综合帧。
- 正常负载下 99% 上报间隔位于 18 至 22 ms，且不得出现超过 40 ms 的间隔。
- 任一侧超过 50 ms 未更新后，不得继续把旧数据标记为新数据。
- 明确选择“静止时仍固定 50 Hz”或“静止时降频”之一；若目标是固定频率，则相同 payload 不得抑制周期帧。

### 其他 MCU 数据

- 红外矩阵 10 s 内约 333 帧。
- 红外测距 10 s 内约 100 帧。
- 电池每秒启动一次完整采样，上报继续遵循变化阈值和保活策略。
- 充电桩状态变化立即上报，静态状态每 5 s 保活。
- 记录 UART TX 队列峰值、发送失败、周期延迟、解析丢帧和 stale 次数。

### SoC 与融合层

- `sensor/motor` 在正常运动和静止场景均符合选定的 50 Hz 契约。
- IMU 原始 topic 保持目标 100 Hz，ToF 保持约 15 Hz。
- 50 Hz 融合快照正确标识 `new_sample`、`valid` 和 `age_ms`。
- 覆盖静止、运动、堵转、单电机断连、UART 背压、充电及低功耗恢复场景。

## 任务分级

1. 电机 MCU 到 SoC 固定 50 Hz：契约缺陷修复；若导航依赖稳定里程计节拍，建议 P1。
2. 统一频率描述、统计和 50 Hz 导航快照：增强与技术债务，建议 P2。

## 当前验证状态

- 已完成两端源码静态核对和历史运行日志旁证。
- 已确认 GD32L235 当前工作树中的电机直接触发发送、10 ms 限流、相同 payload 去重、红外 30 ms 批量快照、红外测距 100 ms 周期、电池 1 s 采样和充电状态 5 s 保活行为。
- 未修改 MCU 或 SoC 源码，未运行两端构建。
- 未执行板级频率计数、UART 波形、调度抖动、背压、丢帧或导航融合 HIL。
- MCU 和 SoC 工作树均包含既有未提交改动；本文不声明可提交、可合并或可发布。

## 风险与限制

- owner 确认的电机 50 Hz 是需求契约；仍需用对应电机固件版本和 UART 计数验证实际设备行为。
- GD32L235 协议文档出现周期 reporter 诊断字段，但当前电机路径仍为解析后直接发送；实现和文档需要在落地时对齐。
- SoC `modules/sensor` 在当前源码仓中处于忽略路径，修改前需确认真实源码 SSOT 和交付方式。
- 历史导航日志只能作为旁证，不替代当前版本板测。
- 本条目不得被提升为团队通用传感器标准；其结论仅适用于 PCR02 与 GD32L235 当前架构。

## 后续动作

1. 在 GD32L235 建立 20 ms 电机周期聚合任务，并同步协议说明和静态检查。
2. 在 SoC 为 MCU topic 补充实际接收频率、间隔、丢帧和 stale 统计。
3. 板测完成 10 至 30 分钟频率矩阵，覆盖正常、压力、单侧断连和低功耗恢复。
4. 只有板测与 owner 复核完成后，才考虑将稳定契约抽取到 `current/`；本归档在此之前保持 `reviewing`。

## 脱敏说明

本文未包含私有网络端点、UID、token、密钥、原始串口日志、二进制固件、客户资料或运行时缓存。源码引用使用 `workspace://` 逻辑标识，不保留个人绝对路径。
