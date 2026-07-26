---
related:
- projects/gd32l235/current/soc-low-power-contract.md
- projects/gd32l235/archive/design/2026-07-22-low-battery-soc-sleep-protection-design.md
- projects/gd32l235/archive/design/2026-07-22-pa11-charge-soc-power-gate-design.md
captured_at: '2026-07-22'
id: gd32l235-soc-shutdown-confirmation-closure-design-20260722
title: GD32L235 与 SOC Shutdown 确认闭环设计归档
kind: project-archive
domain: projects/gd32l235
path: projects/gd32l235/archive/design/2026-07-22-soc-shutdown-confirmation-closure-design.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: source-project-design-document
  from: workspace://gd32l235/Docs/SOC侧Shutdown确认闭环设计.md
  source_sha256: 5785c4142f653cee6d17ae3841ed8fce84373910e29ef42b3357ba1aa9930610
review_after: '2026-08-22'
review_status: human-reviewed-accepted
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- gd32l235
- soc-shutdown
- protocol
- power-management
validation_refs:
- projects/gd32l235/archive/design/2026-07-22-soc-shutdown-confirmation-closure-design.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/gd32l235/archive/design/2026-07-22-soc-shutdown-confirmation-closure-design.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-07-22'
updated_at: '2026-07-26'
generated_by_ai: true
ai_role: classified
ai_model_or_tool: Codex
ai_generated_at: '2026-07-22'
manual_validation_pending: true
summary_zh: 归档 MCU 与 SOC 在 shutdown、sleep 和 power-off 场景中的请求、确认、超时、settle 与最终动作闭环设计。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
---

# SOC 侧 Shutdown 确认闭环设计

## 归档说明

- 本文是截至 2026-07-22 的实现方案与演进记录，不是现行协议的逐字段 SSOT；`status=reviewing`。
- 当前权威顺序为 MCU/SOC 源码、`workspace://gd32l235/Docs/串口通信协议规范.md`、[当前低功耗协同契约候选](../../current/soc-low-power-contract.md)。
- 本文中 `0x09` 的旧长度兼容草案和阶段性代码片段已失效；双方现只接受固定 3B `stage/reason/detail`，reason/detail 必须精确匹配活动事务。
- Review：owner `leiwenjun`；复审日期 2026-08-22；重点验证取消、确认、6s deadline、2s settle 与最终 PA8/PA15 动作。

> 2026-07-22 终态更新（优先于本文旧章节）：PA15 可独立切断 SoC，MCU/WiFi 保持。PA11 OFF 统一进入 `0x09` best-effort 退出闭环；STANDBY/SLEEP 先由 MCU 输出一次 9 ms PA8 脉冲，DEEP_SLEEP 不重新上电。MCU 每 400 ms 重发相同 token 的 `COMMAND_SENT`，6 s 未确认可强制切断 SoC。

> 2026-06-04 硬件复核补充：EVT2 已取消“充电直接开机”要求，`CHARGING_DET` 到系统总电源 MOSFET 的二极管实际 DNP/拆除。产品规则确定为 PA11 OFF 后不支持充电，也不支持充电触发 SOC 开机；固件仍保留 `SWITCH_OFF_CHARGE_BLOCK` 作为运行态和异常板型防护，不走 SOC shutdown/sleep 闭环，且 PB10 禁止充电。详见 [PA11 关机、充电与 SOC 上电门控设计归档](2026-07-22-pa11-charge-soc-power-gate-design.md)。

> 2026-07-18 契约更新：匹配当前 active reason/detail 的 `SOC_CONFIRMED` 是不可撤销点。MCU 只在确认前接受取消；确认后必须完成既定 PA8/PA15 动作。POWER_KEY 场景即使 PA11 已回到 ON，也先完成至少 100ms PA15 OFF hold，再重新上电。

## 1. 背景与目标

MCU 侧低电量 SOC 休眠保护、充电认证 SOC 休眠、拨动开关关机都需要同一套流程：

```text
MCU 通知 SOC 应用退出 -> SOC 完成退出准备后确认 -> MCU 执行 PA8 sleep 或 PA15 OFF
```

MCU 侧设计见：

```text
projects/gd32l235/archive/design/2026-07-22-low-battery-soc-sleep-protection-design.md
```

SOC 应用为：

```text
<sigmastar-repo>
```

本设计目标是补齐 SOC 侧闭环，使 MCU 收到的 `SOC_CONFIRMED` 不是串口刚收到命令时的“早确认”，而是 SOC 应用完成模块退出、日志落盘、资源安全释放后的“真实确认”。

## 2. 当前 SOC 侧链路

当前相关代码路径：

| 模块 | 路径 | 当前职责 |
|---|---|---|
| 应用入口/出口 | `pcr02/main.cpp` | 初始化各模块，监听 `POWEROFF` key event，退出主循环并 deinit |
| 应用生命周期 | `pcr02/core/application.cpp` | `app_startup()`、`app_shutdown()`、`app.deinitialize()` |
| 串口协议收发 | `modules/app/src/app_uart` | 解析 MCU 串口协议，当前能解析 `UART_MSG_TYPE_SHUTDOWN_STAGE_NOTIFY` |
| 实际串口业务桥接 | `modules/sensor/serial` | 收到 shutdown notify 后发布 `POWEROFF` key event |

当前链路：

```text
MCU:
  CMD_SHUTDOWN_STAGE_NOTIFY
    |
    v
SOC app_uart:
  VSAPPUART_ShutdownStageNotify()
  解析 payload[0] = stage
    |
    v
sensor/serial:
  SensorSerial::onShutdownCallback()
  publishKeyEvent(POWEROFF)
    |
    v
pcr02/main.cpp:
  watchPoweroffKeyEvent()
  g_shutdown_requested = true
    |
    v
主循环退出
  stop/deinit modules
  app_shutdown()
  app.deinitialize()
```

当前缺口：

1. `VSAPPUART_MsgShutdownStageNotify_t` 只保存 `u8Stage`，没有 reason/detail。
2. `SensorSerial::onShutdownCallback()` 只发布 `POWEROFF`，没有把 reason 传给应用退出流程。
3. SOC 侧没有看到发送 `PROTOCOL_SHUTDOWN_STAGE_SOC_CONFIRMED` 给 MCU 的接口。
4. `main.cpp` 完成退出后没有回包给 MCU，MCU 只能靠 6s 超时兜底。
5. `sensor_module.deinit()` 如果先关闭 app_uart，退出完成后就无法再给 MCU 发送确认。

## 3. 协议约定

继续使用 MCU 与 SOC 共有命令：

```text
CMD_SHUTDOWN_STAGE_NOTIFY / UART_MSG_TYPE_SHUTDOWN_STAGE_NOTIFY = 0x09
```

### 3.1 Stage

| 值 | 名称 | 方向 | 含义 |
|---:|---|---|---|
| `0x01` | `SWITCH_OFF_DETECTED` | MCU -> SOC | 可选，检测到拨动开关 OFF |
| `0x02` | `COMMAND_SENT` | MCU -> SOC | MCU 请求 SOC 应用退出 |
| `0x03` | `SOC_CONFIRMED` | SOC -> MCU | SOC 应用已完成退出准备 |
| `0x04` | `TIMEOUT_FORCE_OFF` | MCU -> SOC 或日志 | MCU 超时兜底 |
| `0x05` | `CANCELLED` | MCU -> SOC | 本次退出取消 |

### 3.2 Reason

建议 SOC/MCU 共用：

| 值 | 名称 | 含义 |
|---:|---|---|
| `0x00` | `NONE` | 旧协议或未知 |
| `0x01` | `POWER_KEY` | 拨动开关关机 |
| `0x02` | `LOW_BATTERY_SLEEP` | 低电量 SOC 休眠保护 |
| `0x03` | `CHARGE_SLEEP` | 充电认证 SOC 休眠 |

### 3.3 Payload

旧格式：

```text
payload[0] = stage
```

新格式：

```text
payload[0] = stage
payload[1] = reason，可选
payload[2] = detail，可选
```

兼容规则：

```text
payload_len >= 1:
  必须解析 stage。

payload_len >= 2:
  解析 reason。

payload_len >= 3:
  解析 detail。

payload_len == 1:
  reason = NONE，detail = 0，兼容旧 MCU/SOC。
```

## 4. SOC 侧总体流程

### 4.1 MCU 请求 SOC 退出

```text
MCU -> SOC:
  UART_MSG_TYPE_SHUTDOWN_STAGE_NOTIFY
  payload[0] = COMMAND_SENT
  payload[1] = reason
  payload[2] = detail
```

SOC 收到后：

```text
app_uart 解析 stage/reason/detail
  |
  v
sensor_serial 保存 shutdown request
  |
  v
发布 shutdown request / POWEROFF event 给 main.cpp
  |
  v
main.cpp 进入有原因的退出流程
```

### 4.2 SOC 完成退出后确认

确认不能在 `SensorSerial::onShutdownCallback()` 刚收到串口命令时发送，因为此时应用还没有退出，Flash、日志、线程、模块资源都未完成收尾。

确认应在 `main.cpp` 完成关键退出动作后发送：

```text
停止业务模块
停止 AI/navigation/iot/task/bridge
FlushLogs
sync()
发送 SOC_CONFIRMED 给 MCU
短暂等待串口发送完成
最后关闭 sensor serial/app_uart
```

SOC -> MCU：

```text
UART_MSG_TYPE_SHUTDOWN_STAGE_NOTIFY
payload[0] = SOC_CONFIRMED
payload[1] = reason
payload[2] = detail，可选
```

## 5. app_uart 修改方案

修改范围：

```text
include/app/app_uart_packet.h
modules/app/src/app_uart/app_uart_packet.c
```

### 5.1 扩展接收结构

当前结构：

```c
typedef struct __attribute__((packed))
{
    VS_U8 u8Stage;
} VSAPPUART_MsgShutdownStageNotify_t;
```

建议扩展为：

```c
typedef struct __attribute__((packed))
{
    VS_U8 u8Stage;
    VS_U8 u8Reason;
    VS_U8 u8Detail;
    VS_U8 u8PayloadLen;
} VSAPPUART_MsgShutdownStageNotify_t;
```

`u8PayloadLen` 用于判断 SOC 收到的是旧格式还是新格式。该结构只在进程内使用，不直接作为线上的 payload ABI，因此可以扩展。

### 5.2 扩展解析函数

`VSAPPUART_ShutdownStageNotify()` 建议改为：

```c
VERIFY_TRUE(u16Length >= 1U, VS_ERROR_INVALID_SIZE);

pstMsg->u8Stage = pu8Payload[0];
pstMsg->u8Reason = (u16Length >= 2U) ? pu8Payload[1] : 0U;
pstMsg->u8Detail = (u16Length >= 3U) ? pu8Payload[2] : 0U;
pstMsg->u8PayloadLen = (u16Length > 0xFFU) ? 0xFFU : (VS_U8)u16Length;
```

显示函数增加 reason/detail 日志：

```text
shutdownStage=%u reason=%u detail=%u payloadLen=%u
```

### 5.3 新增发送接口

建议在 `app_uart_packet.h` 声明：

```c
VS_S32 VSAPPUART_SendShutdownStageNotify(VS_U8 u8Stage, VS_U8 u8Reason, VS_U8 u8Detail);
```

实现：

```c
VS_S32 VSAPPUART_SendShutdownStageNotify(VS_U8 u8Stage, VS_U8 u8Reason, VS_U8 u8Detail)
{
    VS_U8 au8Payload[3];

    au8Payload[0] = u8Stage;
    au8Payload[1] = u8Reason;
    au8Payload[2] = u8Detail;

    return _UART_SendSimpleRequest(0x00U,
                                   UART_MSG_TYPE_SHUTDOWN_STAGE_NOTIFY,
                                   au8Payload,
                                   sizeof(au8Payload),
                                   UART_ACK_TIMEOUT_MS,
                                   2U,
                                   NULL);
}
```

如果 `_UART_SendSimpleRequest()` 对 `0x09` 的方向或 ACK 语义不合适，需要按当前 app_uart 的发送封装规则调整，但线上 payload 仍保持 `[stage, reason, detail]`。

## 6. sensor_serial 修改方案

修改范围：

```text
modules/sensor/serial/sensor_serial.h
modules/sensor/serial/sensor_serial.cpp
```

### 6.1 增加 shutdown request 数据

建议定义：

```cpp
struct ShutdownRequest {
    uint8_t stage{0};
    uint8_t reason{0};
    uint8_t detail{0};
    uint8_t payload_len{0};
};
```

`SensorSerial` 中保存最近一次请求：

```cpp
std::atomic<uint8_t> shutdown_reason_{0};
std::atomic<uint8_t> shutdown_detail_{0};
std::atomic<bool> shutdown_notify_pending_{false};
std::atomic<bool> shutdown_in_progress_{false};
std::atomic<bool> shutdown_cancelled_{false};
```

`shutdown_in_progress_` 是 SOC 侧的单飞锁。一次 `COMMAND_SENT` 被接受后，直到收到并消费匹配的 `CANCELLED`，或者进程退出重启前，SOC 不再接受新的 `COMMAND_SENT`。这可以避免快速反复拨动 PA11 时，新旧 request token 交叉覆盖，导致 SOC 退出流程重入。

### 6.2 扩展 onShutdownCallback

当前行为：

```cpp
serial.publishKeyEvent(proto::sensor_info::KeyEventInfo_KeyCode_POWEROFF);
```

建议行为：

```text
1. 解析 VSAPPUART_MsgShutdownStageNotify_t。
2. 只对 COMMAND_SENT 触发应用退出。
3. 保存 reason/detail，并设置 `shutdown_notify_pending_`。
4. 发布 shutdown request 给 main.cpp。
5. 兼容旧路径，可继续发布 POWEROFF key event。
```

快速拨动下必须增加两个保护：

```text
1. 收到 COMMAND_SENT 时：
   - 若 shutdown_in_progress_ 为 false，记录 reason/detail，置 true，并发布 POWEROFF。
   - 若 shutdown_in_progress_ 为 true，只打印 duplicate ignored，不再发布 POWEROFF，不覆盖 active reason/detail。

2. 收到 CANCELLED 时：
   - 若 reason/detail 与 active request 匹配，清除 pending，置 shutdown_cancelled_=true。
   - 若应用还没有真正进入退出，main.cpp 消费 cancelled 后继续运行，并释放 shutdown_in_progress_，允许后续新的有效 COMMAND_SENT。
   - 若应用已经进入不可逆 deinit，退出尾部消费 cancelled 后不发送 SOC_CONFIRMED，改发 CANCELLED 或直接退出，由 supervisor 重新拉起应用。
```

注意：

```text
onShutdownCallback() 不发送 SOC_CONFIRMED。
它只是接收请求和通知应用退出。
main.cpp 必须通过 consumeShutdownRequest() 消费 pending 请求，不能直接读取“上一次 reason/detail”，避免旧 reason 或非 MCU POWEROFF 事件被误确认。
```

### 6.3 新增确认发送接口

建议在 `SensorSerial` 增加：

```cpp
bool sendShutdownConfirmed(uint8_t reason, uint8_t detail);
bool sendShutdownCancelled(uint8_t reason, uint8_t detail);
bool consumeShutdownRequest(uint8_t *reason, uint8_t *detail);
bool consumeShutdownCancelled(uint8_t *reason, uint8_t *detail);
```

`consumeShutdownRequest()` 使用 `shutdown_notify_pending_.exchange(false)` 判断本次 `POWEROFF` 是否来自 MCU shutdown notify。只有消费到 pending 时，`main.cpp` 才设置 `g_shutdown_confirm_needed=true` 并在退出末尾回 `SOC_CONFIRMED`。

实现调用 app_uart 新接口：

```cpp
bool SensorSerial::sendShutdownConfirmed(uint8_t reason, uint8_t detail)
{
    if (!inited_.load()) {
        return false;
    }

    const auto ret = VSAPPUART_SendShutdownStageNotify(kShutdownStageSocConfirmed, reason, detail);
    if (ret != VS_SUCCESS) {
        SENSOR_LOG_ERROR("send shutdown confirmed failed: reason={}, detail={}, ret={}", reason, detail, ret);
        return false;
    }
    return true;
}
```

### 6.4 不要混用 sendMucSleeep

`SensorSerial::sendMucSleeep()` 是 SOC 主动请求 MCU sleep control 的旧业务接口，不等价于“SOC 应用已退出确认”。

本设计中：

```text
SOC_CONFIRMED:
  表示 SOC 应用退出准备完成。

sendMucSleeep:
  表示 SOC 请求 MCU 进入某种 sleep mode。
```

两者不能互相替代。

GD32L235 新协议固件仍保留 `CMD_SLEEP_CONTROL` 的主动休眠能力，供 SOC APP 在业务场景中主动请求 MCU/SOC 进入 sleep/standby。为避免上电初期状态未稳定时误睡，MCU 对 `SLEEP/STANDBY` 增加基础门禁：

- `sysTickUptime < SOC_SLEEP_CONTROL_STARTUP_GUARD_MS` 时拒绝；
- 电量计未初始化完成时拒绝；
- SOC 退出/掉电状态机忙时拒绝。

如果是 MCU 侧低电量保护、充电认证休眠或拨动开关关机触发的 SOC 应用退出，必须走 `CMD_SHUTDOWN_STAGE_NOTIFY`；SOC APP 只有在完成退出准备后才能回 `SOC_CONFIRMED`。`sendMucSleeep()` 不能作为 `SOC_CONFIRMED` 使用。

`PA11 == 0 && charging == true` 是例外：该场景按 MCU `SWITCH_OFF_CHARGE_BLOCK` 处理，不向 SOC 发 `COMMAND_SENT`，不要求 SOC 回 `SOC_CONFIRMED`，也不通过 PA8 触发 SOC sleep/wake，PB10 保持禁止充电。

## 7. main.cpp 修改方案

修改范围：

```text
pcr02/main.cpp
```

### 7.1 保存退出原因

当前只有：

```cpp
std::atomic<bool> g_shutdown_requested{false};
```

建议增加：

```cpp
std::atomic<uint8_t> g_shutdown_reason{0};
std::atomic<uint8_t> g_shutdown_detail{0};
```

`main.cpp` 主循环必须直接轮询 `SensorSerial::consumeShutdownRequest()`，不能只依赖 `POWEROFF` key event。当前 key event topic 可能同时被 task 模块订阅，存在被其它模块先消费的风险；因此 MCU shutdown request 的主触发链路必须是 `sensor_serial pending -> main loop consume -> g_shutdown_requested=true`。

如果消费成功，则保存 reason/detail，并标记退出末尾需要回 `SOC_CONFIRMED`：

```text
pending=true:
  g_shutdown_reason = reason
  g_shutdown_detail = detail
  g_shutdown_confirm_needed = true
```

`watchPoweroffKeyEvent()` 继续作为兼容路径。如果它收到 `POWEROFF`，也尝试消费 pending；消费成功则走同一条 MCU shutdown 流程。如果没有 pending，说明该 `POWEROFF` 可能来自其它路径或旧事件，SOC 应用仍可按原逻辑退出，但不要回 `SOC_CONFIRMED`：

```text
pending=false:
  g_shutdown_confirm_needed = false
  只退出应用，不向 MCU 回 shutdown confirmed
```

这样可以避免两个问题：一是“读取上一次 reason/detail”导致旧确认误触发 MCU 后续动作；二是 key event 被其它模块消费后 main 永远收不到退出事件。后续若要更强语义，可以新增 shutdown request topic 或扩展 sensor key event payload，让 main.cpp 直接拿到结构化 reason/detail。

如果 SOC 应用是由外部 `SIGTERM` / `SIGINT` 触发退出，例如手工 `kill -TERM` 或 supervisor 停应用，则不能向 MCU 回 `SOC_CONFIRMED`。若此时存在 pending 或已消费的 MCU shutdown request，应发送：

```text
payload[0] = CANCELLED
payload[1] = reason
payload[2] = detail
```

MCU 收到匹配的 `CANCELLED` 后取消当前 active shutdown，保持 PA15 ON，不执行 PA8 sleep / PA15 OFF。

如果 `watchPoweroffKeyEvent()` 收到 POWEROFF，但 `consumeShutdownRequest()` 失败，必须继续检查 `consumeShutdownCancelled()`：

```text
consumeShutdownRequest() == false
consumeShutdownCancelled() == true
  说明这是 COMMAND_SENT 后又被 MCU 取消留下的过期 POWEROFF key event。
  main.cpp 只打印日志并继续运行，不进入 shutdown。
```

这条规则专门处理 PA11 快速 OFF->ON 的竞态：`COMMAND_SENT` 已经让 sensor_serial 发布了 POWEROFF，但 MCU 随后根据 PA11 回到 ON 发送 `CANCELLED`。SOC 不能再被这个过期 key event 带入退出。

### 7.2 调整退出顺序

当前 main.cpp 退出顺序中 `sensor_module.deinit()` 在 `app.app_shutdown()` 前，可能导致 app_uart 被关闭后无法发送 `SOC_CONFIRMED`。

建议调整为：

```text
stopKeyEventMonitor()
stop_ai_voice_thread()
stop_ai_vision_thread()
navigation_Module_deinit()
bridge_module.deinit()
iot_module.deinit()
task_module.deinit()

app.app_shutdown()
app.deinitialize()

common::FlushLogs()
sync()

SensorSerial::instance().sendShutdownConfirmed(reason, detail)
短暂等待发送完成，例如 50~100ms

sensor_module.deinit()
spdlog::shutdown()
_exit(0)
```

关键点：

```text
sensor serial/app_uart 必须保留到发送 SOC_CONFIRMED 之后。
```

### 7.3 app.is_power_down() 的处理

当前：

```cpp
if (app.is_power_down()) {
    LOG_INFO("Power down requested, entering wait loop...");
    common::FlushLogs();
    while (true) {
        std::this_thread::sleep_for(std::chrono::seconds(1));
    }
}
```

目前 `Application::is_power_down_` 没看到被设置为 true 的入口。建议不要依赖这个标志完成 MCU 确认闭环。

本设计建议：

```text
由 main.cpp 的 shutdown reason 决定是否发送 SOC_CONFIRMED。
发送 SOC_CONFIRMED 后，SOC 进程可以退出；后续 MCU 会继续等待 2s 让 SOC app 完成 deinit 退出，然后按 reason 执行 PA8 sleep 或 PA15 OFF；但 MCU 从发送 COMMAND_SENT 起的总等待不超过 6s。
```

## 8. 与 MCU 侧联动关系

### 8.1 低电量 SOC 休眠保护

MCU 不会在开机首笔电量读数上立即发送低电量休眠请求。当前 MCU 侧已增加开机 5s 宽限、3 次连续低电量采样和电压报告值交叉确认；只有稳定满足低电量且非充电条件后，SOC 才会收到 `LOW_BATTERY_SLEEP`。

```text
MCU:
  stage=COMMAND_SENT
  reason=LOW_BATTERY_SLEEP
  detail=battery_percent
    |
SOC:
  收到后退出应用
  FlushLogs + sync
  stage=SOC_CONFIRMED
  reason=LOW_BATTERY_SLEEP
  detail=battery_percent
    |
MCU:
  等 2s settle，但总等待不超过 6s
  PA8 非阻塞长脉冲 sleep
  PA15 保持 ON
```

### 8.2 充电认证 SOC 休眠

```text
MCU:
  stage=COMMAND_SENT
  reason=CHARGE_SLEEP
  detail=request_token
    |
SOC:
  退出应用后回 SOC_CONFIRMED
  原样带回 request_token
    |
MCU:
  PA8 非阻塞长脉冲 sleep
  PA15 保持 ON
```

### 8.3 拨动开关关机

```text
MCU:
  stage=COMMAND_SENT
  reason=POWER_KEY
  detail=request_token
    |
SOC:
  退出应用后回 SOC_CONFIRMED
  原样带回 request_token
    |
MCU:
  将本次事务标记为 committed
  等待 2s settle（总等待不超过 6s）
  PA15 OFF hold 至少 100ms
  PA11 已 ON 时在 hold 后重新上电
```

如果 PA11 在等待 `SOC_CONFIRMED` 期间拨回 ON：

```text
MCU 取消本次 POWER_KEY 请求。
SOC 晚到的 SOC_CONFIRMED 应被 MCU 忽略。
```

一旦 MCU 已接收匹配的 `SOC_CONFIRMED`，事务不再接受 PA11 或 `CANCELLED` 撤销；PA11 的最新状态只决定 POWER_KEY 最小 OFF hold 结束后继续掉电还是重新上电。

## 9. 并发与取消策略

SOC 侧建议只维护一个 active shutdown request。

规则：

```text
1. 收到 COMMAND_SENT 后，如果当前没有 active request，记录 reason/detail 并请求退出。
2. 如果已经有 active request，再收到任何 COMMAND_SENT，必须忽略，不能刷新 detail，不能再次发布 POWEROFF。
3. 如果已经在退出中，再收到 CANCELLED：
   - 若 reason/detail 匹配 active request，清除 pending 并记录 cancelled。
   - 若应用还未开始实际退出，消费 cancelled 后继续运行。
   - 若已经进入不可逆退出阶段，退出尾部不发送 confirmed，改发 CANCELLED 或直接退出。
4. 如果已经完成退出准备并发送 SOC_CONFIRMED，事务进入不可撤销阶段；后续由 MCU 等待 2s settle 后执行既定 PA8/PA15 动作，总等待不超过 6s。
```

对 `POWER_KEY` 快速反复拨动：

```text
MCU 是确认前取消和 PA15 动作执行的最终裁决方。
SOC 侧只负责真实退出和发送 confirmed。
如果 MCU 在 SOC 退出完成前取消，SOC 不能再发送 confirmed；如果 confirmed 已经发出，MCU 不再取消本次事务。
```

## 10. 落地计划

### 阶段 1：app_uart 支持扩展 payload 和确认发送

改动：

- `include/app/app_uart_packet.h`
- `modules/app/src/app_uart/app_uart_packet.c`

任务：

1. 扩展 `VSAPPUART_MsgShutdownStageNotify_t`。
2. 解析 `stage/reason/detail/payload_len`。
3. 增加 `VSAPPUART_SendShutdownStageNotify()`。
4. 保持旧 payload 长度 1 兼容。

验收：

```text
SOC 能解析 MCU 发送的 1/2/3 字节 shutdown payload。
SOC 能发送 [SOC_CONFIRMED, reason, detail] 给 MCU。
```

### 阶段 2：sensor_serial 传递 reason 并提供确认接口

改动：

- `modules/sensor/serial/sensor_serial.h`
- `modules/sensor/serial/sensor_serial.cpp`

任务：

1. `onShutdownCallback()` 保存 stage/reason/detail。
2. 只对 `COMMAND_SENT` 触发应用退出。
3. 新增 `sendShutdownConfirmed()`。
4. 新增 `sendShutdownCancelled()`。
5. 新增 `consumeShutdownRequest()`，用 pending 标志把主循环退出与本次 MCU shutdown notify 绑定。
6. 新增 `consumeShutdownCancelled()`，用于处理 MCU 取消和过期 POWEROFF key event。
7. 增加 `shutdown_in_progress_` 单飞锁，退出中重复 `COMMAND_SENT` 不再触发二次退出。
8. 保持旧 `POWEROFF` key event 路径兼容。

验收：

```text
收到 COMMAND_SENT 后 main.cpp 能进入退出流程。
退出流程末尾能通过 SensorSerial 回 SOC_CONFIRMED。
```

### 阶段 3：main.cpp 调整退出确认点和 deinit 顺序

改动：

- `pcr02/main.cpp`

任务：

1. 保存 shutdown reason/detail。
2. 完成业务模块退出、日志 flush、sync 后发送 SOC_CONFIRMED。
3. 调整 `sensor_module.deinit()` 到发送确认之后。
4. 确保发送确认后有 50~100ms 发送完成窗口。

验收：

```text
MCU 发送 shutdown notify 后：
- SOC 应用退出；
- SOC 在退出完成后回 SOC_CONFIRMED；
- MCU 能提前结束 confirmed 等待，并在 2s settle 后执行动作；总等待不超过 6s。
```

### 阶段 4：联合验证

任务：

1. MCU 低电量 reason=LOW_BATTERY_SLEEP。
2. MCU 充电认证 reason=CHARGE_SLEEP。
3. MCU 拨动开关 reason=POWER_KEY。
4. 验证 SOC confirmed 回包时机。
5. 验证 MCU 收到 confirmed 后执行对应 PA8/PA15 动作。

## 11. 验证用例

| 用例 | 输入 | SOC 期望 | MCU 期望 |
|---|---|---|---|
| 旧协议兼容 | payload 仅 `[COMMAND_SENT]` | 触发退出，reason=NONE | 可按旧确认接受 |
| 低电量休眠 | `[COMMAND_SENT, LOW_BATTERY_SLEEP, percent]` | 退出后回 `[SOC_CONFIRMED, LOW_BATTERY_SLEEP, percent]` | PA8 sleep，PA15 ON |
| 充电认证休眠 | `PA11=1` 且 `[COMMAND_SENT, CHARGE_SLEEP, token]` | 退出后回 `[SOC_CONFIRMED, CHARGE_SLEEP, token]` | PA8 sleep，PA15 ON |
| PA11 OFF 充电禁止 | `PA11=0 && charging=true` | 运行态/浅休眠执行 best-effort 退出，DEEP_SLEEP 不参与 | MCU 禁止 PB10；必要时 9 ms 唤醒后发送 `0x09`，最终 PA15 OFF |
| 拨动开关关机 | `[COMMAND_SENT, POWER_KEY, token]` | 退出后回 `[SOC_CONFIRMED, POWER_KEY, token]` | confirmed 后完成 PA15 OFF hold；PA11 已 ON 则 hold 后重新上电 |
| 快速 OFF->ON，SOC 未开始 deinit | POWER_KEY 后 MCU 取消 | SOC 消费 CANCELLED，忽略过期 POWEROFF，不回 confirmed | PA15 ON，允许后续新请求 |
| 快速 OFF->ON，SOC 已进入 deinit 但未 confirmed | POWER_KEY 后 MCU 取消 | SOC 退出尾部不回 confirmed，改回 CANCELLED 或退出后由 supervisor 拉起 | PA15 ON，不执行旧 PA15 OFF |
| 快速 OFF->ON，SOC 已 confirmed | MCU 已提交事务 | SOC 不再发送 CANCELLED 撤销 | MCU 完成至少 100ms PA15 OFF hold，再重新上电 |
| 快速 OFF->ON->OFF | 第二个 POWER_KEY token 到达 | SOC 若仍在第一次退出中，忽略重复 COMMAND_SENT | MCU 以最新硬件 PA11 状态和 active token 做裁决 |
| SOC 退出慢 | SOC 超过 6s 才 confirmed | late confirmed 可发送 | MCU 已超时执行，忽略或记录 late confirmed |
| app_uart 先 deinit 风险 | sensor serial 过早关闭 | 发送 confirmed 失败 | 测试应失败，需调整 deinit 顺序 |

POWER_KEY 在 RUNNING 中直接发送 `COMMAND_SENT`；在 STANDBY/SLEEP 中先发一次 9 ms PA8 脉冲再发送。DEEP_SLEEP 或确认 SoC 已离线时不重新上电，直接保持 PA15 OFF。heartbeat offline 仍用于快速断电，但不能把已同步的 STANDBY/SLEEP 误判为无需唤醒。

PA11=0 时，MCU 侧必须把“最终切断 SoC、禁止充电”作为最高优先级：charging 不能阻止 PA15 OFF，PB10 保持关闭；唯一允许的 PA8 动作是 STANDBY/SLEEP 为处理 `0x09` 所需的一次 9 ms 脉冲。普通 WIFI/IMU/TOF 和充电认证唤醒继续被拒绝。

SOC 主动发送 `CMD_SLEEP_CONTROL` 时也不能绕过 PA11。MCU 在命令接收阶段和实际执行 `STOP/STANDBY` 前后都复核 PA11；若 PA11 已为 OFF，MCU 不进入 sleep/standby，而是转入 POWER_KEY 关机或 SWITCH_OFF_CHARGE_BLOCK 策略。PA11=OFF 的启动早期，MCU 会跳过 IR/TOF/电机等 SOC 相关外设上电动作；非充电时只保持最小状态后进入 PA15 OFF hold，充电时进入 SWITCH_OFF_CHARGE_BLOCK。

## 12. 风险与控制

| 风险 | 影响 | 控制措施 |
|---|---|---|
| SOC 在串口回调里过早 confirmed | MCU 提前 sleep/power off，应用未安全退出 | confirmed 只能在 main.cpp 退出末尾发送 |
| sensor_module 先 deinit | app_uart 被关闭，confirmed 发不出去 | sensor serial 保留到 confirmed 之后 |
| reason 无法传到 main.cpp | MCU 无法区分低电量、充电、关机确认 | 扩展 shutdown request 数据或 topic |
| 旧 payload 无 reason | 兼容性和准确性不足 | payload_len=1 时 reason=NONE，只允许单 active request |
| 非 MCU POWEROFF 误确认 | 可能让 MCU 提前执行 PA8/PA15 动作 | main.cpp 只在 consume pending 成功时发送 SOC_CONFIRMED |
| SOC 退出超过 6s | MCU 超时兜底 | SOC 仍发送 late confirmed，MCU 记录但不执行旧动作 |
| 外部 SIGTERM 退出应用 | 误触发 MCU sleep/poweroff | 不发送 SOC_CONFIRMED；如有 pending request，发送 CANCELLED |
| 快速拨动导致取消 | SOC 可能已开始退出 | confirmed 前由 SOC 处理 CANCELLED 并抑制 confirmed；confirmed 后 MCU 按不可撤销事务完成动作 |
| 快速拨动导致重复 COMMAND_SENT | SOC reason/detail 被覆盖，退出流程重入 | SOC 单飞锁忽略重复 COMMAND_SENT，不覆盖 active request |
| 过期 POWEROFF key event | MCU 已取消但 SOC 仍被 key event 拉进 shutdown | key event 线程先消费 cancelled，命中过期事件时继续运行 |

## 13. 最终结论

SOC 侧必须补齐“真实退出完成后确认”闭环：

```text
app_uart:
  支持 stage/reason/detail，提供 SOC_CONFIRMED 发送接口。

sensor_serial:
  接收 shutdown request，传递 reason/detail，提供 sendShutdownConfirmed()。

main.cpp:
  在业务模块退出、日志 flush、sync 之后，且 sensor serial 仍可用时，发送 SOC_CONFIRMED。
```

该设计与 MCU 侧方案配合后，MCU 的 6s 只作为总兜底；SOC 正常退出完成后，MCU 继续等待 2s settle，再执行 PA8 sleep 或经过 PA11 复核后执行 PA15 OFF。
