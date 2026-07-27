---
id: pcr02-motor-uart-timestamp-sync-plan-20260726
title: PCR02 MCU/SoC 电机 UART 时间戳同步与实时链路最终方案
kind: project-archive
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/archive/reports/2026-07-26-pcr02-motor-uart-timestamp-sync-plan.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: session-source-code-review-and-design
  from: 2026-07-26 PCR02 SoC 与 GD32L235 MCU 源码只读审查，以及用户确认的同包更新、升级顺序和混合版本业务屏蔽前提
  source_sha256: 505377e30e902fe84959b472e28351d6369e3f7cf9b579f4d6e6f2d47784f761
  temporary_source_retained: false
review_after: '2026-10-26'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- pcr02
- motor
- uart
- timestamp
- time-sync
- gd32l235
- app-uart
- hdi-uart
- protocol-0x16
validation_refs:
- projects/xcrz-sigmastar-demo/archive/reports/2026-07-26-pcr02-motor-uart-timestamp-sync-plan.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/archive/reports/2026-07-26-pcr02-motor-uart-timestamp-sync-plan.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-07-26'
updated_at: '2026-07-26'
generated_by_ai: true
ai_role: summarized
ai_model_or_tool: Codex
ai_generated_at: '2026-07-26'
manual_validation_pending: true
summary_zh: 固化 PCR02 MCU/SoC 电机 UART 时间同步、0x16 破坏性升级、app_uart/hdi_uart 实时链路改造及实施验收计划；当前仅完成设计和源码审查，代码、构建与 HIL 仍待验证。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
---

# PCR02 MCU/SoC 电机 UART 时间戳同步与实时链路最终方案

## 摘要

本文归档 PCR02 电机反馈链路的协议与实施方案。方案以 MCU 和 SoC 同包更新、先升级 MCU、短暂混合版本窗口在业务分发入口屏蔽电机反馈为前提，允许电机反馈命令 `0x16` 直接做不兼容升级。

核心决策是：SoC 使用 `CLOCK_BOOTTIME` 作为统一单调时钟，通过新增命令 `0x1A` 把时钟锚点同步到 GD32L235；MCU 在收到下级电机反馈最后一个 UART 字节时记录左右轮独立采样时间，再通过固定 60 字节的 `0x16` 上报原始 MCU tick、映射后的 SoC 时间、SoC 实际接收时间所需的同步质量字段及电机数据。SoC 同时修改 `hdi_uart` 和 `app_uart` 的通用语义，移除短帧填充等待、原始 FIFO 搬运和成功路径固定延时。

当前状态仅为“设计已完成源码级审查、实施计划已冻结”。尚未修改源码，未执行 MCU/SoC 构建，也未完成板级、逻辑分析仪或 HIL 验证，不得据此声明功能已实现、性能达标、制品可发布或 owner 已签收。

## 背景与发布前提

- MCU 与 SoC 作为一个组合制品发布。
- 固定升级顺序为先 MCU、后 SoC。
- MCU 新版、SoC 旧版的短暂窗口内，电机反馈在业务分发入口被屏蔽。
- 新 SoC 启动并确认新协议后再开放电机反馈。
- 因此新 SoC 不保留旧 `0x16` 的 16/28 字节解析分支。
- 本方案不修改 OTA 协议、MCU Stage0/Stage1、分区、Bootloader 或升级元数据。
- 新源码要进入交付制品，仍必须重新生成 MCU/SoC 二进制并重新打入 image/OTA；后编译 app 不会自动进入已经生成的制品。

如果现有升级流程无法在 MCU 更新前关闭电机反馈业务分发，或更新失败后无法保持关闭，这一前提不成立，应在上线前阻断，而不是回退到协议兼容分支。

## 结论边界

### 已完成

- 审计 MCU 电机反馈解析、UART RX ISR、SoC 协议发送和主循环上报位置。
- 审计 SoC `hdi_uart`、`app_uart` 的收发线程、原始 FIFO、Parser、ACK 和 TX completion 路径。
- 确认仓内 `VSHDIUART_RecvTimeout()` 和 `VSHDIUART_WaitTxDone()` 均只有 `app_uart` 一个代码调用方。
- 确认 MCU 底层 `protocol_send_raw_frame()` 已返回发送结果，而公共 `protocol_send_data()` 当前丢弃该结果。
- 确认新增 `MotorData` 字段若经 bridge 传递，当前 bridge proto 和复制逻辑会丢弃字段。
- 冻结协议字段、时间语义、模块职责、任务依赖和验收门槛。

### 未完成

- 未修改任何 MCU 或 SoC 源码。
- 未生成协议 golden vectors 或新增自动化测试。
- 未执行 MCU/SoC 构建。
- 未测量 UART P99 延迟、同步误差和 50 Hz 抖动。
- 未确认最终算法消费者是否直接消费 `MotorData`，还是经过 bridge/vosen。
- 未执行 1000 次循环或 2 小时 soak。

## 统一时钟域

SoC 统一使用 `CLOCK_BOOTTIME`，单位为微秒。算法、UART TX/RX 时间戳和 MCU 映射全部使用该时钟域，避免 `CLOCK_REALTIME` 校时跳变影响控制时序。

MCU 使用现有 32 位 `_micros()`。SoC 向 MCU提交以下锚点：

```text
anchor_mcu_tick_us
anchor_soc_boottime_us
sync_id
uncertainty_us
valid_ms
```

MCU 映射公式：

```c
sample_soc_us =
    anchor_soc_boottime_us +
    (int32_t)(sample_mcu_tick_us - anchor_mcu_tick_us);
```

同步有效期固定为 15 秒。32 位微秒 tick 约 71.6 分钟回绕一次，有符号差值在 15 秒有效期内无跨半周期歧义。MCU reset、SoC reset 或低功耗造成 MCU tick 不连续时必须使同步失效。

## `0x1A` 时间同步协议

所有多字节字段沿用现有协议的大端序。

### PROBE Request：4 字节

| 偏移 | 字段 | 类型 | 约束 |
| ---: | --- | --- | --- |
| 0 | version | `u8` | 固定为 1 |
| 1 | op | `u8` | 固定为 `0x01` |
| 2 | sync_id | `u16` | 本轮同步编号 |

MCU 在收到请求最后一个 UART 字节的 RX ISR 中记录 `mcu_rx_end_tick_us`。

### PROBE ACK：8 字节

| 偏移 | 字段 | 类型 |
| ---: | --- | --- |
| 0 | version | `u8` |
| 1 | op | `u8 = 0x81` |
| 2 | sync_id | `u16` |
| 4 | mcu_rx_end_tick_us | `u32` |

SoC TX 线程在 UART `TEMT` 首次成立时记录 `soc_tx_end_boottime_us`。单次样本：

```text
offset_us = soc_tx_end_boottime_us - mcu_rx_end_tick_us
```

PROBE ACK 只负责带回 MCU 时间；ACK 排队和调度延迟不进入 offset。`0x1A PROBE` 必须绕过现有按 `(seq, cmd)` 复用的 ACK cache，每次重新生成 ACK。

### COMMIT Request：20 字节

| 偏移 | 字段 | 类型 |
| ---: | --- | --- |
| 0 | version | `u8 = 1` |
| 1 | op | `u8 = 0x02` |
| 2 | sync_id | `u16` |
| 4 | anchor_mcu_tick_us | `u32` |
| 8 | anchor_soc_boottime_us | `u64` |
| 16 | uncertainty_us | `u16` |
| 18 | valid_ms | `u16` |

### COMMIT ACK：6 字节

| 偏移 | 字段 | 类型 |
| ---: | --- | --- |
| 0 | version | `u8 = 1` |
| 1 | op | `u8 = 0x82` |
| 2 | sync_id | `u16` |
| 4 | status | `u8` |
| 5 | reserved | `u8 = 0` |

COMMIT 按 `sync_id` 幂等处理。

### 同步策略

- SoC 启动后执行 8 次 PROBE，排除超时、ID 不匹配和异常样本后取稳定 offset 中位数。
- 稳态每 5 秒执行一轮，每轮低优先级发送 3 次 PROBE。
- 同步命令不得抢占停止、零速和正常电机速度命令。
- `uncertainty <= 2000 us` 视为有效。
- `uncertainty > 5000 us` 必须判定无效。
- 同步状态为 `UNSYNCED`、`SYNCED`、`EXPIRED`。

## `0x16` 电机反馈 V1

新 SoC 只接受 `cmd=0x16`、`payload_len=60`、`version=1`。旧 16/28 字节 payload 明确拒绝。

| 偏移 | 字段 | 类型 |
| ---: | --- | --- |
| 0 | version | `u8` |
| 1 | timing_flags | `u8` |
| 2 | report_seq | `u16` |
| 4 | sync_id | `u16` |
| 6 | sync_uncertainty_us | `u16` |
| 8 | left_sample_tick_us | `u32` |
| 12 | right_sample_tick_us | `u32` |
| 16 | left_sample_boottime_us | `u64` |
| 24 | right_sample_boottime_us | `u64` |
| 32 | left_speed_rpm | `i16` |
| 34 | right_speed_rpm | `i16` |
| 36 | left_total_cnt | `i32` |
| 40 | right_total_cnt | `i32` |
| 44 | left_fault | `u8` |
| 45 | right_fault | `u8` |
| 46 | left_temperature_c | `i8` |
| 47 | right_temperature_c | `i8` |
| 48 | left_battery_voltage_cv | `u16` |
| 50 | right_battery_voltage_cv | `u16` |
| 52 | left_phase_current_ca | `u16` |
| 54 | right_phase_current_ca | `u16` |
| 56 | left_bus_current_ca | `u16` |
| 58 | right_bus_current_ca | `u16` |

`timing_flags`：

- bit0：`TIME_SYNC_VALID`
- bit1：`LEFT_VALID`
- bit2：`RIGHT_VALID`
- bit3：`LEFT_NEW`
- bit4：`RIGHT_NEW`
- bit5：`TIMESTAMP_IS_GD32_RX_END`
- bit6～7：保留，发送端置 0

同步无效时保留 MCU 原始 tick，映射后的两个 SoC 时间置 0，`sync_uncertainty_us` 置 `0xffff`，并清除 `TIME_SYNC_VALID`。

现有帧开销为 10 字节，因此新帧总长为 70 字节。115200、8N1 下单帧线时约 6.08 ms，50 Hz 占用约 35 kbit/s，即链路带宽约 30.4%。

## MCU 采样时间戳与上报

时间戳语义固定为“GD32 收到一帧下级电机反馈最后一个 UART 字节的时间”。如果下级电机协议不提供内部采样时间，GD32 无法恢复电机控制器 ADC 或控制周期的绝对采样时刻。

左右电机 UART ISR 分别维护轻量帧边界跟踪器、单调 RX byte position 和 4 项固定 marker 环。marker 内容为 `{frame_end_position, rx_end_tick_us}`。ISR 不执行 CRC、业务解析、动态分配或日志输出。

主循环校验完整电机反馈后，通过 frame end position 匹配时间戳。marker 溢出、匹配失败或 CRC 错误时必须把该侧时间标记为无效，不得绑定上一帧时间。

上报策略：

- 解析任务只更新最新样本、采样 tick、generation 和 valid。
- 统一 `motor_report_task` 位于左右解析任务之后。
- 距上次成功上报达到 18 ms 且左右都有新数据时立即发送。
- 达到 20 ms deadline 时发送当前最新数据，不继续等待另一侧。
- 单侧超过 50 ms 未更新则清除该侧 `VALID`。
- 删除基于 payload 内容的去重逻辑，静止时仍保持 50 Hz。
- `protocol_send_data()` 改成返回 `bool`。
- 只有成功进入 SoC UART TX ring 后才递增 `report_seq`、更新时间和消费 `NEW`。
- 发送失败只保留一个最新待发送快照，每隔至少 1 ms 重试，不积压历史报告。

## SoC `hdi_uart` 通用语义

`VSHDIUART_RecvTimeout()` 改成等待首次可读、只执行一次成功 read、立即记录 `CLOCK_BOOTTIME` 并返回实际字节数，不再等待填满调用者 capacity。

`VSHDIUART_WaitTxDone()` 在首次观察到 `TEMT` 时立即记录 `CLOCK_BOOTTIME`。轮询间隔目标为 100～200 us；如果平台只能提供毫秒级 delay，同步 uncertainty 下限按 1 ms 计算。

两套公共/模块镜像头文件同步修改，不保留兼容包装接口。

## SoC `app_uart` 链路

最终线程角色为 TX、RX+stream decode 和 data dispatch：

- RX 线程使用固定内存增量状态机处理拆包、粘包、噪声、坏 CRC、非法长度和连续多帧。
- 完整帧记录该次 read 完成时的 `rx_boottime_us`。
- ACK 在 RX 线程快速匹配 inflight transaction。
- 普通数据帧进入完整帧消息队列。
- sensor/business callback 只在 dispatch 线程执行，不能阻塞 RX 线程。
- 删除 raw FIFO、Peek/memmove 和成功路径固定 1 ms delay。
- `0x16` 使用一个 latest slot、一个队列 marker 和 generation；dispatch 拥塞时覆盖成最新帧，不积压历史电机数据。
- 建议完整帧队列深度为 16，使用现有固定内存消息池。

时间同步使用一次发送、同时跟踪 ACK 与 TX physical completion 的通用 timed transaction。注册两套状态后只入队一次，发送失败或超时同时清理，不能通过调用两个发送接口造成 PROBE 重发。

## 下发链路

电机控制命令 `0x12` 的 wire payload 保持不变：

- STOP/零速最高优先级。
- 非零速度命令高优先级。
- 速度命令保持单槽 latest-wins，不积压历史速度。
- 待发项记录 `generated_boottime_us`。
- 已被更新命令替代的旧速度不发送。
- 超过一个控制周期的旧非零速度命令不补发。
- 时间同步命令低于电机控制命令。
- 去掉 TX 队列 timeout 后附加的固定 1 ms delay。
- 统计 generated→enqueue、enqueue→write、write→TEMT 延迟，但不逐帧刷日志。

控制命令的原则是尽快应用最新值，延迟的旧命令应丢弃，不在未来补执行。

## Proto 与算法约束

`MotorData` 预留字段：

```protobuf
uint64 left_sample_boottime_us  = 18;
uint64 right_sample_boottime_us = 19;
uint64 receive_boottime_us      = 20;
uint32 timing_flags             = 21;
uint32 sync_id                  = 22;
uint32 sync_uncertainty_us      = 23;
```

`header.sequence` 使用 `report_seq`。如果算法经过 bridge/vosen 消费，`BridgeMotorData`、`BridgeVosenMotorData` 必须使用相同字段号并显式复制，避免字段静默丢失。

算法使用规则：

1. 同步有效、单侧有效且 source time 非零。
2. `source_time <= receive_time + uncertainty`。
3. `receive_time - source_time <= 50 ms`。
4. 条件满足时使用 source time；receive time只用于延迟和质量门禁，不与 source 求平均。
5. 同步短暂无效时使用最近有效数据估出的 transport delay；没有历史估计时使用 receive time，并明确标记 fallback。
6. 按 20 ms 时间轴重采样。
7. 两个有效采样点之间线性插值。
8. 末端只允许最多 20 ms hold 或有限外推。
9. 40～50 ms 后进入 stale。
10. 累计编码器计数不做低通滤波。

## 升级窗口门禁

1. MCU 更新前关闭 motor feedback 业务分发。
2. 更新 MCU。
3. 混合版本窗口内旧 SoC 不得把新 `0x16` 送入算法或控制业务。
4. 更新并启动新 SoC。
5. 新 SoC 确认 `version=1/len=60`，完成 `0x1A` 同步或显式进入 fallback。
6. 开放 motor feedback。
7. SoC 更新失败时门禁保持关闭。

这是一项发布流程前提，不是旧协议兼容逻辑。

## 实施计划

```text
T0 协议冻结
 ├─ T1 MCU 时间同步与采样戳 → T2 MCU 0x16 上报
 └─ T3 HDI 语义修改 → T4 app_uart 链路 → T5 Proto/Bridge → T6 算法
                       两条链汇合
                              ↓
                         T7 联调/HIL
                              ↓
                         T8 制品门禁
```

| 任务 | Owner 角色 | 依赖 | 估时 | 交接条件 |
| --- | --- | --- | ---: | --- |
| T0 协议和 golden vectors | 协议 | 无 | 2 h | `0x1A/0x16`、大小端、错误帧和边界向量冻结 |
| T1 MCU 同步与 RX 时间戳 | MCU | T0 | 6 h | 同步状态机、ISR marker、回绕测试通过 |
| T2 MCU 50 Hz `0x16` | MCU | T1 | 6 h | 60 字节映射、左右时间和失败重试正确 |
| T3 HDI UART 语义 | SoC HDI | T0 | 3 h | API/头文件一致，定向构建通过 |
| T4 app_uart 与 timed transaction | SoC App | T3 | 8 h | 增量解帧、ACK fast path、dispatch、同步 worker 完成 |
| T5 Sensor/Proto/Bridge | SoC Sensor/Proto | T4 | 6 h | 字段 18～23 到达最终消费者前一层 |
| T6 算法接入 | 算法 | T5 | 4 h | 重采样、插值、fallback、stale 单测通过 |
| T7 跨仓联调/HIL | 集成 | T2、T6 | 8 h | 延迟、频率、回绕、重启和 soak 证据完成 |
| T8 构建与组合制品 | 发布 | T7 | 4 h | 两仓门禁和制品身份核对完成 |

总工程量约 47 小时。T0 完成后 MCU 与 SoC 两条链可并行，关键路径约 35 小时，不含设备排队时间。

## 验收标准

- `0x16` payload 固定 60 字节，旧长度在新 SoC 明确拒绝。
- MCU 上报周期 P99 为 18～22 ms。
- GD32 电机帧 RX-end 到 SoC callback P99 不超过 10 ms。
- SoC UART 最后字节进入用户态到完成解帧 P99 不超过 2 ms。
- 电机命令 generated 到 MCU handler P99 不超过 5 ms。
- 稳态同步 uncertainty P99 不超过 2 ms，超过 5 ms 自动失效。
- 任一侧超过 50 ms 不更新必须 stale。
- MCU/SoC 重启或休眠后不使用旧锚点，目标在 1 秒内重新同步。
- 1000 次短循环无 ring/queue 泄漏或 ACK 串扰。
- 2 小时 soak 无持续队列增长或 report sequence 异常。
- 混合版本窗口没有电机反馈进入业务 callback。

协议与流解码测试至少覆盖逐字节到达、粘包、噪声前缀、半帧续传、坏 CRC、非法长度、旧 `0x16` 长度、ACK/TX-done 完成顺序交错、重复 PROBE seq、MCU tick 回绕、左右轮异步到达和 `0x16` dispatch 拥塞覆盖。

## 源码证据范围

SoC：

- `modules/hdi/src/hdi_hw/hdi_uart.c`
- `modules/app/src/app_uart/app_uart.c`
- `modules/app/src/app_uart/app_uart_packet.c`
- `modules/sensor/serial/sensor_serial.cpp`
- `modules/proto/sensor_info.proto`
- `modules/proto/bridge_info.proto`
- `modules/bridge/main/bridge_entry.cpp`

MCU：

- `App/protocol.c`
- `App/protocol.h`
- `App/motor_protocol.c`
- `App/motor_protocol.h`
- `App/usartx.c`
- `App/main.c`
- `App/bsp.c`

这些路径仅表示本轮只读审查范围，不表示代码已经按本文修改。

## 验证记录

- date：2026-07-26
- cwd：`workspace://xcrz-sigmastar-demo`
- source：当前 SoC 与 GD32L235 MCU 工作区的源码级只读审查，以及用户确认的同包更新、升级顺序和混合窗口屏蔽前提
- command：`rtk bash ~/knowledge-hub/tools/knowledge-context.sh ... --task-type archive --json`
- exit_code：0
- result_summary：Knowledge Hub 路由到 `projects/xcrz-sigmastar-demo`，未发现同主题当前条目；workspace source evidence 被报告为 stale，因此本文不把工作区 HEAD 登记状态当作当前权威，只保留本轮明确读取的源码观察
- command：`rtk bash ~/codex/scripts/final-ready.sh`
- exit_code：0
- result_summary：会话交付门禁通过；这不等价于 MCU/SoC 构建或 HIL 通过

### 离线待验证

```yaml
manual_validation_pending: true
manual_validation_reason: 设计尚未实现，缺少编译、板级延迟、同步误差和 soak 证据
required_followup:
  - rtk bash scripts/codex-check.sh --full
  - rtk make modules/hdi_obj_all -j20
  - rtk make modules/app_obj_all -j20
  - rtk make modules/proto_script_start
  - rtk make modules/proto_obj_all modules/sensor_obj_all modules/bridge_obj_all -j20
  - rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
owner: leiwenjun
review_after: 2026-10-26
```

## 风险与限制

- MCU 时间戳是 GD32 接收下级电机帧的结束时间，不是电机控制器内部采样时间。
- Linux 用户态 `read` 完成时间包含内核调度延迟；第一版不做线时反推，是否补偿由 HIL 数据决定。
- 70 字节、50 Hz 占用约 30.4% UART 带宽，必须通过优先级和 latest-wins 防止反馈阻塞控制命令。
- 算法真实消费者路径尚待确认；如果经过 bridge，必须完成字段透传。
- 混合版本屏蔽是破坏性升级成立的硬前提。
- SoC 工作区存在既有变更，实施前必须做重叠文件审计，不能清理或覆盖无关内容。
- 本文不得提升为团队通用 UART 规范；它是 PCR02 项目特定设计。

## Provenance 与脱敏

- captured_at：2026-07-26
- topic：`motor-uart-timestamp-sync`
- source type：session source-code review and user-confirmed design decisions
- 已脱敏：不保留设备端点、内网地址、凭证、raw log、二进制、客户信息或完整聊天记录
- memory candidate：否
- promotion：none
- owner decision：未生成

## Review

- owner：leiwenjun
- review_after：2026-10-26
- 下一次复核：协议实现 diff、golden vectors、MCU/SoC 定向构建、板级延迟与同步 uncertainty、算法消费者路径、1000 次循环和 2 小时 soak
