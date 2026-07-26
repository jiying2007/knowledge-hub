---
id: gd32l235-low-battery-soc-sleep-protection-design-20260722
title: GD32L235 低电量 SOC 休眠保护设计归档
kind: project-archive
domain: projects/gd32l235
path: projects/gd32l235/archive/design/2026-07-22-low-battery-soc-sleep-protection-design.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: source-project-design-document
  from: workspace://gd32l235/Docs/低电量SOC休眠保护设计.md
  source_sha256: 60db2de793d658094ef35a056e09c8a10e7d4cda36740851059162efa325878c
review_after: '2026-08-22'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- gd32l235
- low-battery
- soc-sleep
- power-management
related:
- projects/gd32l235/current/soc-low-power-contract.md
- projects/gd32l235/archive/design/2026-07-22-pa11-charge-soc-power-gate-design.md
- projects/gd32l235/archive/design/2026-07-22-soc-shutdown-confirmation-closure-design.md
validation_refs:
- projects/gd32l235/archive/design/2026-07-22-low-battery-soc-sleep-protection-design.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/gd32l235/archive/design/2026-07-22-low-battery-soc-sleep-protection-design.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-07-22'
captured_at: '2026-07-22'
updated_at: '2026-07-22'
generated_by_ai: true
ai_role: classified
ai_model_or_tool: Codex
ai_generated_at: '2026-07-22'
manual_validation_pending: true
summary_zh: 归档 GD32L235 低电量条件、SOC 退出确认、SLEEP 动作、启动宽限与恢复条件的演进设计；现行协议和代码事实仍以源码仓当前版本为准。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
---

# 低电量 SOC 休眠保护设计

## 归档说明

- 本文是 2026-07-22 从源码仓迁移的历史设计快照，保存 2026-06-04 至 2026-07-22 的方案演进；`status=reviewing`，不作为当前生效规范。
- 当前权威顺序为 MCU/SOC 实现、`workspace://gd32l235/Docs/串口通信协议规范.md`、[当前低功耗协同契约候选](../../current/soc-low-power-contract.md)。当前候选未转为 `active` 前，仍须回到源码核验。
- 文中旧的 PA15“整机保持”推导、旧睡眠状态命名，以及 `0x09` 允许 1B/2B payload 的描述均已被后续实现取代；现行 `0x09` 固定为 3B，不保留旧格式兼容。
- Review：owner `leiwenjun`；复审日期 2026-08-22；重点核对低电量 HIL、PA8 脉冲和 SoC 退出时序。

> 2026-07-22 硬件终态更新（优先于本文旧硬件推导）：PA15 可以独立控制 SoC 电源，PA11 ON 不妨碍 SoC 单独掉电；MCU 与 WiFi 由独立保持路径继续运行。低电量场景仍选择 SLEEP 而不切 SoC 电源，这是产品策略，不是硬件限制。本文后续出现的“PA15 只能释放整机保持/PA11 ON 时不能切 SoC”均按本条修正。

> 2026-06-04 硬件复核补充：EVT2 已取消“充电直接开机”要求，`CHARGING_DET` 到系统总电源 MOSFET 的二极管实际 DNP/拆除。产品规则已确定为“拨动开关关机后不支持充电，也不支持充电触发开机”，因此 `PA11=0 && charging=true` 的运行态必须进入 `SWITCH_OFF_CHARGE_BLOCK`：PB10 禁止充电，不唤醒 SOC；冷态上充电桩不应触发 VCC_SYS/SOC 开机。详见 [PA11 关机、充电与 SOC 上电门控设计归档](2026-07-22-pa11-charge-soc-power-gate-design.md)。

> 2026-07-18 契约更新：匹配 active reason/detail 的 `SOC_CONFIRMED` 是不可撤销点。所有取消条件只在确认前生效；确认后 MCU 必须完成对应 PA8/PA15 动作。POWER_KEY 在确认后遇到 PA11 回 ON 时，先完成至少 100ms PA15 OFF hold，再重新上电。

## 1. 背景与结论

当前硬件中，PA11 是拨动开关状态输入，PA15 是 SoC 电源保持输出。PA15 拉低可以让 SoC 单独掉电，MCU/WiFi 继续运行。

本设计将低电量保护定义为“低电量 SOC 休眠保护”，而不是“低电量掉电”：

```text
低电量且非充电 -> 通知 SOC 应用退出 -> 等待确认或 6s 超时 -> PA8 长脉冲让 SOC sleep
```

拨动开关关机和 DEEP_SLEEP 可以通过 PA15 让 SoC 真实掉电；低电量保护仍按策略使用 SLEEP。

## 2. 目标与非目标

### 2.1 目标

1. 低电量基础条件统一为 `battery_percent <= 2 && !charging`，实际触发必须经过开机宽限、连续采样和电压交叉确认，避免开机瞬态误判。
2. 低电量恢复条件统一为 `battery_percent > 2 || charging == true`。
3. SOC 应用退出必须通过 `CMD_SHUTDOWN_STAGE_NOTIFY` 握手管理。
4. 收到 `PROTOCOL_SHUTDOWN_STAGE_SOC_CONFIRMED` 后结束确认等待，再等待 2s 让 SOC app 完成 deinit 退出，但总等待不超过 `SOC_APP_EXIT_TIMEOUT_MS`。
5. SOC 未确认时，6s 后执行兜底动作。
6. 固定 PA8 / PA15 分工：
   - PA8：只用于 SOC wake/sleep。
   - PA15：只用于 SoC 电源切断/恢复。
7. 低电量保护不虚假声明掉电，状态命名和日志统一使用 `sleep/protect`，不使用 `poweroff`。
8. 充电认证 SOC 休眠、低电量 SOC 休眠、拨动开关关机共用同一套“SOC 退出等待”框架。

### 2.2 非目标

1. 不通过固件绕过 PA11 拨动开关硬件保持路径。
2. 低电量策略不使用 PA15 切断 SoC 电源。
3. 不改变现有 PA8 长脉冲 sleep、短脉冲 wake 的硬件语义。
4. 不强制 SOC 升级到新协议；新 payload 采用向后兼容格式。

## 3. 硬件与 IO 约束

| IO | 当前用途 | 固件设计约束 |
|---|---|---|
| PA11 | 拨动开关状态输入，1 表示开机，0 表示关机 | 用于判断是否允许真实掉电 |
| PA15 | MCU 开机状态保持输出 | 只释放 MCU 保持路径；PA11 为 1 时不能保证 SOC 掉电 |
| PA8 | SOC 唤醒/休眠控制 | 短脉冲唤醒 SOC，长脉冲让 SOC sleep |

关键约束：

```text
PA11 == 0:
  PA15 释放后，整机可真实掉电。

PA11 == 1:
  PA15 释放后，拨动开关路径仍可能维持 VSYS/SOC 上电。
  此时只能声明为 SOC sleep / low battery protect，不能声明为 SOC power off。
```

## 4. 统一 SOC 退出管理状态机

建议先在 `App/bsp.c` 中落地静态状态机，稳定后再拆成独立模块。

### 4.1 状态定义

```c
typedef enum
{
    SOC_EXIT_IDLE = 0,
    SOC_EXIT_NOTIFY,
    SOC_EXIT_WAIT_CONFIRM,
    SOC_EXIT_WAIT_APP_DEINIT,
    SOC_EXIT_POWER_OFF_HOLD,
    SOC_EXIT_SLEEP_PULSE_ACTIVE,
    SOC_EXIT_SLEEPING,
    SOC_EXIT_WAKEUP_HOLDOFF
} soc_exit_state_t;
```

### 4.2 原因定义

```c
typedef enum
{
    SOC_EXIT_REASON_NONE = 0,
    SOC_EXIT_REASON_POWER_KEY = 1,
    SOC_EXIT_REASON_LOW_BATTERY_SLEEP = 2,
    SOC_EXIT_REASON_CHARGE_SLEEP = 3
} soc_exit_reason_t;
```

### 4.3 完成动作定义

```c
typedef enum
{
    SOC_EXIT_ACTION_NONE = 0,
    SOC_EXIT_ACTION_POWER_OFF_PA15,
    SOC_EXIT_ACTION_SLEEP_SOC_PA8
} soc_exit_action_t;
```

低电量场景使用：

```text
reason = SOC_EXIT_REASON_LOW_BATTERY_SLEEP
action = SOC_EXIT_ACTION_SLEEP_SOC_PA8
```

拨动开关关机场景使用：

```text
reason = SOC_EXIT_REASON_POWER_KEY
action = SOC_EXIT_ACTION_POWER_OFF_PA15
```

充电认证休眠场景使用：

```text
reason = SOC_EXIT_REASON_CHARGE_SLEEP
action = SOC_EXIT_ACTION_SLEEP_SOC_PA8
```

## 5. 协议设计

继续复用现有命令：

```c
CMD_SHUTDOWN_STAGE_NOTIFY
```

现有 stage 枚举继续使用：

```c
PROTOCOL_SHUTDOWN_STAGE_COMMAND_SENT
PROTOCOL_SHUTDOWN_STAGE_SOC_CONFIRMED
PROTOCOL_SHUTDOWN_STAGE_TIMEOUT_FORCE_OFF
PROTOCOL_SHUTDOWN_STAGE_CANCELLED
```

### 5.1 向后兼容 payload

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

低电量保护时：

```text
MCU -> SOC:
payload[0] = PROTOCOL_SHUTDOWN_STAGE_COMMAND_SENT
payload[1] = SOC_EXIT_REASON_LOW_BATTERY_SLEEP
payload[2] = battery_percent

SOC -> MCU:
payload[0] = PROTOCOL_SHUTDOWN_STAGE_SOC_CONFIRMED
payload[1] = SOC_EXIT_REASON_LOW_BATTERY_SLEEP，可选
payload[2] = battery_percent，可选
```

SOC 如果只支持旧格式，只处理 `payload[0]` 也不影响兼容性。

### 5.2 新增发送接口

统一使用参数化接口：

```c
void protocol_send_soc_shutdown_notify(uint8_t stage, uint8_t reason, uint8_t detail);
```

旧 `protocol_send_soc_poweroff()` wrapper 在终态实现中移除，避免继续产生无 reason/detail 的调用路径。协议兼容保留在线上 payload 层：SOC 只回 `payload[0]` 的旧确认仍可被 MCU 接受。

## 6. 低电量 SOC 休眠保护流程

### 6.1 触发与恢复条件

基础条件：

```c
battery_percent <= 2U && RunParam.Charging_Flag == false
```

稳定触发条件：

```text
RunParam.Charging_Flag == false
&& sysTickUptime >= LOW_BATTERY_SOC_STARTUP_GRACE_MS
&& battery_percent <= LOW_BATTERY_SOC_SLEEP_PERCENT 连续满足 LOW_BATTERY_SOC_SLEEP_CONFIRM_COUNT 次
&& battery_voltage_report < LOW_BATTERY_SOC_SLEEP_MAX_VOLTAGE_REPORT
```

恢复条件：

```c
battery_percent >= LOW_BATTERY_SOC_RECOVER_PERCENT || RunParam.Charging_Flag == true
```

已落地宏：

```c
#define LOW_BATTERY_SOC_SLEEP_PERCENT              2U
#define LOW_BATTERY_SOC_RECOVER_PERCENT            3U
#define LOW_BATTERY_SOC_STARTUP_GRACE_MS           5000U
#define LOW_BATTERY_SOC_SLEEP_CONFIRM_COUNT        3U
#define LOW_BATTERY_SOC_SLEEP_MAX_VOLTAGE_REPORT   66U
#define SOC_APP_EXIT_TIMEOUT_MS                    6000U
#define SOC_CONFIRMED_APP_DEINIT_WAIT_MS           2000U
```

`LOW_BATTERY_SOC_RECOVER_PERCENT` 使用 3%，避免电量计在 2% 附近抖动导致反复 sleep/wake。`LOW_BATTERY_SOC_SLEEP_MAX_VOLTAGE_REPORT` 对应当前 `battery_info.volt_mv` 上报口径，代码中该值经过 `voltage *= 2; voltage /= 100` 换算，`66` 约等于 6.6V 报告值，不是裸 mV。该交叉确认用于避免电量计刚启动时百分比偏低但电压仍正常时误触发 SOC sleep。

### 6.2 状态流程

```text
IDLE
  |
  | !charging
  | && uptime >= 5s
  | && battery_percent <= 2 连续 3 次
  | && voltage_report < 66
  v
NOTIFY
  - 发送 CMD_SHUTDOWN_STAGE_NOTIFY
  - stage = COMMAND_SENT
  - reason = LOW_BATTERY_SLEEP
  - detail = battery_percent
  - 记录 start_tick
  v
WAIT_CONFIRM
  |
  +-- 收到 SOC_CONFIRMED
  |     -> EXECUTE_ACTION
  |
  +-- 6s 超时
  |     -> EXECUTE_ACTION
  |
  +-- charging == true 或 battery_percent > 2
        -> CANCELLED

EXECUTE_ACTION
  - PA15 保持 ON
  - PA8 长脉冲让 SOC sleep
  - 标记 low_battery_soc_sleeping = true
```

### 6.3 退出低电量保护

退出条件：

```text
charging == true
或
battery_percent >= LOW_BATTERY_SOC_RECOVER_PERCENT
```

退出动作：

```text
1. 发送 CANCELLED。
2. 清除 low_battery_soc_sleeping。
3. PA15 保持 ON。
4. 通过 PA8 短脉冲唤醒 SOC。
5. 回到 IDLE。
```

如果处于 `WAIT_CONFIRM` 阶段插入充电座，应立即取消低电量保护，不再执行 SOC sleep。

## 7. 拨动开关关机流程

拨动开关关机是当前硬件下的真实掉电路径。

```text
PA11 从 1 变 0
  |
  v
发送 CMD_SHUTDOWN_STAGE_NOTIFY
stage = COMMAND_SENT
reason = POWER_KEY
  |
  v
等待 SOC_CONFIRMED 或 6s 超时
  |
  +-- SOC_CONFIRMED -> committed settle -> Power_Set_Keep_On(POWER_KEEP_OFF)
  |                     -> POWER_OFF_HOLD 至少 100ms
  |                     -> PA11 已 ON 时 hold 后重新上电
  |
  +-- 6s 超时 -> 最终复核 PA11
                    |
                    +-- PA11 仍为 0 -> Power_Set_Keep_On(POWER_KEEP_OFF)，进入 POWER_OFF_HOLD
                    |
                    +-- PA11 已回到 1 -> CANCELLED，Power_Set_Keep_On(POWER_KEEP_ON)
```

`POWER_OFF_HOLD` 要求：

```text
1. PA15 OFF 后至少保持 SOC_POWER_OFF_HOLD_MS，当前为 100ms。
2. hold 期间持续保持 PA15 OFF，不允许重新发起 POWER_KEY shutdown。
3. 100ms 后如果 PA11 仍为 0，继续保持 PA15 OFF，不回 IDLE。
4. 100ms 后如果 PA11 回到 1，恢复 PA15 ON 并回 IDLE。
```

如果等待过程中 PA11 又变回 1：

```text
1. 发送 CANCELLED。
2. Power_Set_Keep_On(POWER_KEEP_ON)。
3. 回到 IDLE。
```

拨动开关关机可以声明 SoC 真实掉电；PA15 切断 SoC 电源后 MCU/WiFi 仍保持运行。

### 7.1 PA11 快速反复拨动保护

PA11 是拨动开关输入，用户可能快速执行 `ON -> OFF -> ON` 或 `OFF -> ON -> OFF`。固件不能只在关机触发时读一次 PA11，否则旧的 SOC 退出等待或旧的 6s 超时可能在用户已经拨回 ON 后继续执行 PA15 OFF，造成“拨动开关已打开，设备却休眠或掉电”的现象。

快速拨动处理原则：

```text
PA11 原始输入持续采样，但只有连续稳定后才生成 OFF/ON 事件。
PA11 稳定为 0 只能发起关机意图。
PA11 稳定为 1 必须取消尚未收到 SOC_CONFIRMED 的关机意图并保持 PA15=ON。
未确认事务走超时动作前，必须最后一次复核 PA11 稳定状态仍为 0；已确认事务不再取消。
如果已经进入 PA15 OFF hold，必须先满足最小 OFF 保持时间，再按最新稳定 PA11 状态恢复或继续保持。
上电/启动阶段若 PA11 首次采样为 0，仅在状态尚未稳定时允许 `Power_Init()` 在 OFF/ON 防抖总窗口内临时保持 PA15；稳定确认为 0 后立即进入 OFF hold。该确认窗口不允许通过 PA8 唤醒 SOC，也不构成 charging 或 PB10 充电许可。
PA11=0 时，低电量 SOC sleep、普通 WIFI/IMU/TOF 唤醒、standby wakeup、充电认证退出唤醒都不能重新拉高 PA15 或产生 PA8 唤醒脉冲。
SOC 主动发起的 sleep/standby 不能绕过 PA11：命令接收和实际进入 STOP/STANDBY 前后都必须复核 PA11，若 PA11 已为 0，则转入 POWER_KEY 关机或 SWITCH_OFF_CHARGE_BLOCK 策略。
PA11=0 的启动早期，Bsp_Init 应跳过 IR/TOF/电机等 SOC 相关外设上电动作；若 MCU 已处于运行态且检测到 charging，则进入 SWITCH_OFF_CHARGE_BLOCK，PB10 禁止充电。EVT2 后续板冷态 PA11 OFF 上充电桩不应触发 MCU/VCC_SYS 上电。
```

建议拨动开关关机子状态：

```text
NORMAL
  |
  | PA11 连续稳定为 0
  v
POWER_KEY_OFF_DEBOUNCE
  |
  | PA11 仍为 0
  v
WAIT_SOC_EXIT
  - PA15 保持 ON
  - 不主动通过 PA8 唤醒 SOC
  - 发送 CMD_SHUTDOWN_STAGE_NOTIFY
  - reason = POWER_KEY
  - 记录 start_tick
  |
  +-- PA11 稳定变回 1
  |     -> CANCELLED，PA15 ON
  |
  +-- SOC_CONFIRMED
  |     -> COMMITTED_SETTLE
  |
  +-- 6s 超时
        -> PRE_POWER_OFF_CHECK

COMMITTED_SETTLE
  - 不再接受 PA11/CANCELLED 撤销
  - 2s settle，且总等待不超过 6s
  -> PA15 OFF hold 至少 100ms
  -> 若 PA11 已稳定 ON，则重新上电

PRE_POWER_OFF_CHECK
  |
  +-- PA11 == 0
  |     -> PA15 OFF，真实掉电
  |
  +-- PA11 == 1
        -> CANCELLED，PA15 ON
```

建议防抖策略：

| 方向 | 建议防抖 | 说明 |
|---|---:|---|
| ON -> OFF | 200ms | 防止抖动误触发关机 |
| OFF -> ON | 200ms | 防止反复拨动时原始毛刺绕过状态机；ON 事件在安全边界取消或恢复 |

建议增加关机请求代际计数，避免旧确认或旧超时误作用于新状态：

```c
static uint8_t s_soc_exit_generation;
static uint8_t s_soc_exit_active_generation;
```

每次启动 SOC 退出请求时递增并记录当前 generation；取消关机或启动新请求时再次递增。SOC 确认和超时执行动作前必须检查当前状态、reason 和 generation 仍然有效。当前实现中，`POWER_KEY` 和 `CHARGE_SLEEP` 会把本次 generation 作为 `payload[2]` 的 request token 发送给 SOC，SOC 确认时原样带回；MCU 收到带 detail 的确认时必须同时匹配 reason 和 detail。低电量场景继续使用 `payload[2]` 传 battery percent，仍依靠当前 active state、reason 和取消后回到 `IDLE` 来过滤旧确认。

PA15 控制硬约束：

```text
未收到 SOC_CONFIRMED、仅由超时触发的 Power_Set_Keep_On(POWER_KEEP_OFF) 前必须同时满足：
1. 当前 reason == POWER_KEY；
2. 当前 action == SOC_EXIT_ACTION_POWER_OFF_PA15；
3. 当前 PA11 读数 == 0；
4. 当前请求未被 PA11 回 ON、charging、或新请求 generation 取消；已确认事务不适用本取消条件；
5. 当前状态仍处于本次关机请求的 PRE_POWER_OFF_CHECK/EXECUTE_ACTION。
```

低电量 SOC sleep 和充电认证 sleep 路径不允许调用 `Power_Set_Keep_On(POWER_KEEP_OFF)`。

## 8. 充电认证 SOC 休眠流程

充电状态下不触发低电量 SOC 休眠保护，充电认证逻辑独立触发 SOC sleep。

```text
进入充电状态
  |
  v
MCU 上报充电状态
  |
  v
发送 CMD_SHUTDOWN_STAGE_NOTIFY
stage = COMMAND_SENT
reason = CHARGE_SLEEP
  |
  v
等待 SOC_CONFIRMED 或 6s 超时
  |
  v
PA15 保持 ON
PA8 长脉冲让 SOC sleep
MCU + WIFI 保持工作
```

如果 SOC 很快确认，例如 500ms 内确认，MCU 应再等待 2s settle 后进入 PA8 长脉冲；如果 6s 总 deadline 先到，则不等满 2s。

退出充电状态后：

```text
1. 退出充电认证 SOC sleep 状态。
2. PA8 短脉冲唤醒 SOC。
3. PA15 保持 ON。
```

## 9. 主流程集成状态

### 9.1 BSP 周期事件

已落地：

```c
static void Soc_Exit_Manager_Event(void);
static void Low_Battery_SocSleep_Event(const BATTERY_INFO_T *battery_info);
```

调用位置：

```text
Read_Battery_Info()
  - 启动阶段读取一次 battery_info
  - 调用 Low_Battery_SocSleep_Event(&battery_info)
  - 受 5s 开机宽限保护，不能第一笔读数直接触发 sleep

Report_Battery_Info_Event()
  - 读取 voltage/capacity/temperature/current 后
  - 更新 battery_info.percent 后
  - 调用 Low_Battery_SocSleep_Event(&battery_info)

Bsp_Loop 或主事件循环
  - 周期调用 Soc_Exit_Manager_Event()
```

### 9.2 SOC 确认回调

已落地：

```c
void Bsp_SocExit_OnSocConfirmed(uint8_t reason, uint8_t detail, bool has_detail);
```

`App/protocol_handlers/system_handler.c` 收到：

```text
CMD_SHUTDOWN_STAGE_NOTIFY
payload[0] = PROTOCOL_SHUTDOWN_STAGE_SOC_CONFIRMED
```

后调用该函数。

兼容策略：

```text
如果 payload 没有 reason，则接受确认。
如果 payload 带 reason，优先要求与当前等待 reason 匹配。
如果 payload 带 detail，则同时要求 detail 与当前请求匹配。
POWER_KEY 和 CHARGE_SLEEP 场景的 detail 使用 MCU 本次请求 token，降低旧确认误匹配概率。
如果 payload[0] 是 CANCELLED，且 reason/detail 与当前 active request 匹配，则取消当前 shutdown，保持 PA15 ON，不执行 PA8 sleep / PA15 OFF。
```

### 9.3 执行动作伪代码

```c
static void Soc_Exit_Manager_ExecuteAction(void)
{
    switch (s_soc_exit.action)
    {
        case SOC_EXIT_ACTION_SLEEP_SOC_PA8:
            Power_Set_Keep_On(POWER_KEEP_ON);
            SOC_Sleep();
            s_soc_exit.state = SOC_EXIT_IDLE;
            break;

        case SOC_EXIT_ACTION_POWER_OFF_PA15:
            if (Bsp_PowerSwitch_IsStableOff())
            {
                Power_Set_Keep_On(POWER_KEEP_OFF);
            }
            else
            {
                /*
                 * PA11 is still ON. Do not claim real power-off.
                 * Keep or restore normal state according to product policy.
                 */
                Power_Set_Keep_On(POWER_KEEP_ON);
            }
            s_soc_exit.state = SOC_EXIT_IDLE;
            break;

        default:
            s_soc_exit.state = SOC_EXIT_IDLE;
            break;
    }
}
```

低电量场景不走 `SOC_EXIT_ACTION_POWER_OFF_PA15`，因此不会出现 PA11 为 ON 时“看似掉电、实际未掉电”的虚假状态。

## 10. 命名与日志规范

低电量相关命名避免使用：

```text
low_battery_poweroff
force_poweroff
soc_poweroff
```

推荐使用：

```text
low_battery_soc_sleep
low_battery_protect
soc_exit_for_low_battery_sleep
```

推荐日志：

```text
low battery protect: request soc app exit percent=%u
low battery protect: soc confirmed, enter soc sleep
low battery protect: timeout, enter soc sleep
low battery protect: recovered, wake soc
power key off: soc confirmed, release PA15
power key off: timeout, release PA15
power key off: cancelled by switch on
```

## 11. 最终行为表

| 场景 | 条件 | SOC 退出等待 | PA8 | PA15 | 状态声明 |
|---|---|---|---|---|---|
| 低电量保护 | `percent <= 2 && !charging` | 确认后 2s settle，6s 总兜底 | 长脉冲 sleep | 保持 ON | SOC 休眠保护 |
| 低电量恢复 | `percent > 2 || charging` | 取消等待 | 短脉冲 wake | 保持 ON | 恢复 SOC 工作 |
| 拨动开关关机 | `PA11 == 0` | 确认后 2s settle，6s 总兜底 | 不使用 | OFF | 整机真实掉电 |
| 拨动开关取消关机 | 等待中 `PA11 == 1` | 取消等待 | 按需 wake | ON | 正常工作 |
| 充电认证休眠 | `PA11 == 1 && charging == true` | 确认后 2s settle，6s 总兜底 | 长脉冲 sleep | ON | SOC 休眠，MCU+WIFI 工作 |
| 充电退出 | `PA11 == 1 && charging == false` | 无 | 短脉冲 wake | ON | 恢复 SOC 工作 |
| 关机禁止充电 | `PA11 == 0 && charging == true` | 不通知 SOC | 不使用 | OFF | SWITCH_OFF_CHARGE_BLOCK，PB10 禁止充电 |

## 12. 落地计划

### 阶段 1：协议确认接收

改动范围：

- `App/protocol.h`
- `App/protocol.c`
- `App/protocol_handlers/system_handler.c`
- `App/bsp.h`
- `App/bsp.c`

任务：

1. 增加 shutdown reason 定义。
2. 新增 `protocol_send_soc_shutdown_notify(stage, reason, detail)`。
3. 移除旧 `protocol_send_soc_poweroff()` wrapper，所有路径必须显式传 stage/reason/detail。
4. 处理 SOC 回传的 `PROTOCOL_SHUTDOWN_STAGE_SOC_CONFIRMED`。
5. 新增 `Bsp_SocExit_OnSocConfirmed(reason, detail, has_detail)`。

验收：

```text
SOC 回 SOC_CONFIRMED 后，MCU 能识别并结束确认等待；随后等待 2s settle，但总时长不超过 6s。
旧 payload 长度为 1 的确认仍可兼容。
```

### 阶段 2：统一 SOC 退出状态机

改动范围：

- `App/bsp.c`
- `App/bsp.h`

任务：

1. 新增 `soc_exit_state_t`、`soc_exit_reason_t`、`soc_exit_action_t`。
2. 新增 `Soc_Exit_Manager_Start()`。
3. 新增 `Soc_Exit_Manager_Event()`。
4. 统一 6s 超时。
5. 支持确认后 2s settle，再执行动作；总等待不超过 6s。
6. 支持取消。
7. 支持关机请求 generation，取消后旧确认和旧超时不能继续执行动作。
8. `SOC_EXIT_ACTION_POWER_OFF_PA15` 执行前强制复核 PA11。
9. `SOC_EXIT_ACTION_SLEEP_SOC_PA8` 使用非阻塞 PA8 长脉冲状态，不直接调用阻塞版 `SOC_Sleep()`。

验收：

```text
等待 SOC 退出时：
- 收到确认后等待 2s settle，再执行 action；若 6s 总 deadline 先到，则立即执行 action。
- 未收到确认 6s 后执行 action。
- 取消条件触发后不再执行 action。
- PA11 回到 1 后，旧 POWER_KEY 请求不能再执行 PA15 OFF。
- PA8 sleep 脉冲期间主循环仍能处理 PA11 回 ON、充电插入和串口事件。
```

### 阶段 3：低电量 SOC 休眠保护

改动范围：

- `App/bsp.c`
- `App/bsp.h`

任务：

1. 在 `Report_Battery_Info_Event()` 电量读取成功后判断低电量。
2. `percent <= 2 && !charging` 触发 `LOW_BATTERY_SLEEP`。
3. `percent > 2 || charging` 取消或恢复。
4. 执行动作为 `SOC_EXIT_ACTION_SLEEP_SOC_PA8`。
5. PA15 全程保持 ON。
6. 日志和变量命名使用 `sleep/protect`。
7. 使用非阻塞 PA8 长脉冲，不直接调用阻塞版 `SOC_Sleep()`。

验收：

```text
低电量非充电时，SOC 退出确认或 6s 超时后进入 SOC sleep。
低电量路径不调用 Power_Set_Keep_On(POWER_KEEP_OFF)。
低电量 PA8 长脉冲期间，插入充电或 PA11 变化仍能被状态机处理。
```

### 阶段 4：充电认证休眠复用状态机

改动范围：

- `App/bsp.c`

任务：

1. 将当前固定等待 SOC 退出的逻辑改为复用统一状态机。
2. reason 使用 `CHARGE_SLEEP`。
3. action 使用 `SLEEP_SOC_PA8`。
4. PA15 保持 ON。
5. 保持当前非阻塞 PA8 长脉冲方式，不退回阻塞版 `SOC_Sleep()`。

验收：

```text
充电认证中 SOC 确认后等待 2s settle，再进入 PA8 长脉冲；但不超过 6s 总 deadline。
SOC 不确认时，6s 后进入 PA8 长脉冲。
PA8 长脉冲期间主循环不被 8s 阻塞。
```

### 阶段 5：拨动开关关机迁移

改动范围：

- `App/bsp.c`
- `App/protocol_handlers/system_handler.c`

任务：

1. PA11 关机流程使用统一状态机。
2. reason 使用 `POWER_KEY`。
3. action 使用 `POWER_OFF_PA15`。
4. PA11 在 confirmed 前恢复为 1 时取消关机。
5. confirmed 是不可撤销点；confirmed 后完成 PA15 OFF hold，再根据 PA11 决定是否重新上电。
6. 未确认超时路径在 PA15 OFF 前最后复核 PA11。
7. 增加 ON/OFF 非对称防抖，确认前 ON 取消优先。

验收：

```text
PA11 为 0 时，SOC 确认或 6s 超时后 PA15 OFF。
PA11 在 confirmed 前恢复为 1 时，关机取消，PA15 ON。
PA11 快速 OFF->ON 且尚未 confirmed 时，旧确认和旧超时都不能再拉低 PA15。
PA11 在 confirmed 后恢复为 1 时，MCU 完成至少 100ms PA15 OFF hold，再重新上电。
```

## 13. 验证计划

| 用例 | 输入条件 | 期望结果 |
|---|---|---|
| 低电量 SOC 确认 | `percent=2`，非充电，SOC 回确认 | MCU 等 2s settle 后 PA8 长脉冲，PA15 保持 ON；总等待不超过 6s |
| 低电量 SOC 超时 | `percent=2`，非充电，SOC 不回确认 | 6s 后 PA8 长脉冲，PA15 保持 ON |
| 低电量等待中充电 | 等待确认时 `charging=true` | 取消低电量保护，不触发 PA8 sleep |
| 低电量恢复 | `percent` 从 2 到 3 | 退出保护，PA8 wake SOC |
| 低电量路径防虚假掉电 | `PA11=1`，低电量保护 | 不调用 PA15 OFF，不声明 power off |
| 拨动开关关机确认 | `PA11=0`，SOC 回确认 | MCU 等 2s settle 后 PA15 OFF，至少保持 100ms；总等待不超过 6s；PA11 仍为 0 时持续保持 OFF |
| 拨动开关关机超时 | `PA11=0`，SOC 不回确认 | 6s 后 PA15 OFF，至少保持 100ms；PA11 仍为 0 时持续保持 OFF |
| 拨动开关取消 | confirmed 前 `PA11=1` | 取消关机，PA15 ON |
| confirmed 前取消后旧确认到达 | PA11 先 0 后 1，MCU 已取消，旧 SOC 确认随后到达 | 忽略旧确认，PA15 保持 ON |
| 快速 OFF->ON 后超时 | PA11 先 0 后 1，旧 6s 超时到达 | 忽略旧超时，PA15 保持 ON |
| 快速 OFF->ON->OFF | 第二次 OFF 稳定 | 生成新请求，只允许新请求执行 PA15 OFF |
| confirmed 后 PA11 回 ON | SOC 已确认且 PA11 当前为 1 | 完成至少 100ms PA15 OFF hold，再重新上电 |
| 充电认证确认 | 进入充电，SOC 回确认 | MCU 等 2s settle 后 PA8 长脉冲，PA15 ON；总等待不超过 6s |
| 充电认证超时 | 进入充电，SOC 不回确认 | 6s 后 PA8 长脉冲，PA15 ON |
| 旧协议兼容 | SOC 只回 `payload[0]` | MCU 仍接受确认 |

## 14. 风险与回退

| 风险 | 影响 | 控制措施 |
|---|---|---|
| SOC 不回确认 | 保护动作延迟 | 6s 超时兜底 |
| SOC 外部 SIGTERM 退出应用 | 误触发 sleep/poweroff | SOC 发送 CANCELLED，MCU 取消 active shutdown |
| 电量 2% 附近抖动 | 反复 sleep/wake | 恢复阈值使用 3%，低电量触发使用 3 次连续采样 |
| 开机电量计百分比误判偏低 | 低于 2% 被误判为需要 SOC sleep，表现为无法开机 | 启动 5s 宽限、3 次连续低电量确认、电压报告值小于 66 才允许触发 |
| PA11 为 ON 时误称掉电 | 状态不真实 | 低电量只做 SOC sleep，不走 PA15 OFF |
| PA11 快速 OFF->ON 后旧超时拉低 PA15 | 用户已开机但设备被未确认的旧关机流程关闭 | confirmed 前 PA11 回 ON 立即取消；超时动作前复核；generation 防旧动作 |
| PA11 已 OFF 时软件路径重新拉起 SOC | SOC 启动到一半再被 PA15 OFF 掉电 | PA11=0 时，Power_Init/Bsp_Init 不因为 charging 保持 PA15，POWER_KEY 不主动 PA8 wake，低电量/普通唤醒/standby/充电认证路径直接拒绝或进入 SWITCH_OFF_CHARGE_BLOCK |
| SOC 主动 sleep/standby 后拨动开关关机 | MCU 低功耗中无法及时处理 PA11 OFF | sleep/standby 命令入口和 post action 执行前后复核 PA11，PA11=0 时转 POWER_KEY 关机或 SWITCH_OFF_CHARGE_BLOCK |
| PA11 OFF 启动早期外设被短暂上电 | 关机路径不安静，可能带来外设脉冲 | Bsp_Init 在 PA11=0 后关闭 PA8/PA15/WIFI/IR/MOTOR；非充电提前进入 OFF hold，充电进入 SWITCH_OFF_CHARGE_BLOCK 且 PB10 禁止充电 |
| PA11 OFF 上充电桩仍出现 VCC_SYS/SOC 早期上电 | 当前板可能误贴 charging 直开机二极管，或 SOC RTC/PM 存在其他上电路径 | 先做 BOM/实物和波形确认；固件侧继续保证不主动唤醒 SOC、不打开 PB10 |
| PA11 OFF 冷态仍有充电电流 | MCU 不上电时 PB10 固件无法驱动，charger EN 可能硬件默认允许 | 确认 PB10/charger EN 默认拉阻和充电电流；产品要求不充电时硬件默认态必须禁充 |
| SOC 旧确认晚到 | 旧确认误触发当前动作 | 只在 `WAIT_SOC_EXIT && reason/generation 匹配` 时接受确认 |
| PA11 机械抖动 | 误触发关机或误取消 | ON->OFF 使用较长防抖，OFF->ON 使用较短防抖并以取消优先 |
| 旧 SOC 协议无 reason | 确认匹配不足 | payload 长度为 1 时兼容接受 |
| 充电和低电量同时发生 | 状态冲突 | charging 优先，取消低电量保护 |

回退策略：

```text
1. 保留 payload 长度 1 的旧确认兼容。
2. 低电量 SOC sleep 可由宏开关隔离。
3. 若状态机异常，可临时关闭 `GD32L235_LOW_BATTERY_SOC_SLEEP_PROTECT`，但不恢复旧无 reason/detail wrapper。
```

## 15. 最终隐患复核

### 15.1 已通过设计规避的风险

1. **虚假掉电**
   - 低电量路径只做 `PA8 sleep`，PA15 保持 ON。
   - 只有 `POWER_KEY + PA11==0` 才允许 `PA15 OFF`。

2. **拨动开关打开后的事务边界**
   - confirmed 前 PA11 回到 1 立即取消 `POWER_KEY` 请求。
   - 未确认超时动作前最后复核 PA11，generation 防止旧确认、旧超时作用于新状态。
   - confirmed 后事务不可撤销；先完成最小 PA15 OFF hold，再按最新 PA11 状态重新上电或继续掉电。

3. **SOC 退出快但 MCU 固定等待**
   - 收到 `SOC_CONFIRMED` 后等待 2s settle，再执行动作。
   - 6s 只作为兜底，不是固定等待。

4. **低电量与充电认证冲突**
   - charging 优先。
   - charging 为 true 时取消低电量保护，进入充电认证逻辑。
   - BSP 初始化阶段会先读取 `Charge_Get_Status()` 同步 `RunParam.Charging_Flag`；若未检测到充电，只保持 `REPORT_STATE_IDLE`，不产生假的 `CHARGE_LEAVE` 上报。

5. **开机电量误判导致无法开机**
   - `Read_Battery_Info()` 的首笔读数受 `LOW_BATTERY_SOC_STARTUP_GRACE_MS` 保护，不能直接触发低电量 SOC sleep。
   - 周期 `Report_Battery_Info_Event()` 持续判断，只有启动稳定后连续 3 次 `<=2%` 且电压报告值低于 66 才触发。
   - 如果正在充电或后续恢复到 3% 及以上，会取消低电量保护并唤醒 SOC。

6. **PA8/PA15 职责混用**
   - PA8 只做 SOC wake/sleep。
   - PA15 只做整机电源保持释放。
   - 低电量和充电认证不允许调用 PA15 OFF。

### 15.2 已落地门禁与仍需验证的风险

1. **PA8 长脉冲不能阻塞主循环**
   - 当前 `SOC_Sleep()` 内部使用长 `delay_1ms(8010)`。
   - 已落地状态机中不直接调用阻塞版 `SOC_Sleep()`，而是用 `SOC_EXIT_SLEEP_PULSE_ACTIVE` 非阻塞保持 PA8 高电平，到 `SOC_SLEEP_PULSE_MS` 后再拉低。
   - 仍需上板验证 PA8 脉冲宽度和 SOC sleep 行为是否与硬件预期一致。

2. **PA11 采样周期和防抖必须足够快**
   - 已落地 `POWER_KEY_SAMPLE_PERIOD_MS = 20U`。
   - OFF 防抖为 200ms，ON 防抖为 200ms；SOC 退出状态机只消费防抖后的稳定 PA11 状态。
   - PA15 已进入 OFF hold 时，不被 ON 毛刺立即打断；满足 `SOC_POWER_OFF_HOLD_MS` 后再按最新稳定 PA11 状态恢复或继续保持。
   - 仍需上板验证快速 OFF/ON/OFF 时不会被旧 confirmed、旧 timeout 或 PA11 原始毛刺关机。

3. **协议确认缺少 reason 时存在误确认可能**
   - 为兼容旧 SOC，payload 长度为 1 的确认会被接受。
   - 接受旧确认时必须限定当前只有一个 active SOC exit 请求。
   - 若未来并发请求增加，必须要求 SOC 回 reason 或 request id。

4. **充电状态抖动可能导致 sleep/wake 反复**
   - charging 优先是正确的，但充电座接触抖动会反复取消/触发。
   - 建议 charging enter/leave 也做稳定判定，或设置最小 holdoff。

5. **低电量恢复阈值按稳定性优先**
   - 当前已落地恢复阈值 3%，避免 2% 附近反复 sleep/wake。
   - 若后续规格强制要求严格 `>2%`，需要同步调整 `LOW_BATTERY_SOC_RECOVER_PERCENT` 和验证矩阵。

6. **PA15 OFF 的安全门禁必须集中**
   - 旧 `protocol.c` post action 已改为 `Bsp_SocExit_StartPowerKeyShutdown()`，不再直接拉低 PA15。
   - 当前 `Power_Set_Keep_On(POWER_KEEP_OFF)` 只允许出现在 `bsp.c` 的 `SOC_EXIT_ACTION_POWER_OFF_PA15` 与 `SOC_EXIT_POWER_OFF_HOLD` 状态中。
   - PA15 OFF 前复核 `Bsp_PowerSwitch_IsStableOff()`，且 OFF 后至少保持 `SOC_POWER_OFF_HOLD_MS = 100U`。

### 15.3 最终风险结论

该计划在设计层面已经解决两个主要隐患：

```text
1. 低电量不再虚假声明掉电；
2. PA11 快速拨回 ON 后，旧关机流程不能继续拉低 PA15。
```

剩余主要风险集中在上板验证：

```text
1. PA8 非阻塞长脉冲是否能稳定让 SOC sleep；
2. PA11 快速 OFF/ON/OFF 时状态机是否能按最终硬件状态裁决；
3. 充电座接触抖动是否需要额外 holdoff。
```

当前代码门禁与设计一致，最终计划没有结构性冲突。

## 16. 当前宏开关

为了降低导入风险，当前保留：

```c
#define GD32L235_LOW_BATTERY_SOC_SLEEP_PROTECT 1
```

启用后才执行低电量 SOC 休眠保护。充电认证 profile 可以独立保留：

```c
#define GD32L235_CHARGE_CERT_PROFILE
```

两者关系：

```text
charging == true:
  充电认证逻辑优先。

charging == false && battery_percent <= 2:
  低电量 SOC 休眠保护生效。
```

## 17. 最终结论

最终方案采用“统一 SOC 退出状态机 + 低电量 SOC 休眠保护”：

```text
低电量:
  SOC 退出确认/6s 超时 -> PA8 sleep -> PA15 保持 ON -> 声明 SOC 休眠保护

拨动开关关机:
  SOC 退出确认/6s 超时 -> PA15 OFF -> 声明整机真实掉电

充电认证:
  SOC 退出确认/6s 超时 -> PA8 sleep -> PA15 保持 ON -> MCU + WIFI 工作
```

该方案与当前硬件一致，不会虚假声明掉电，同时让低电量保护、充电认证休眠和拨动开关关机共享同一套 SOC 应用退出握手机制。
