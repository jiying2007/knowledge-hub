---
related:
- projects/gd32l235/current/soc-low-power-contract.md
- projects/gd32l235/archive/design/2026-07-22-low-battery-soc-sleep-protection-design.md
- projects/gd32l235/archive/design/2026-07-22-soc-shutdown-confirmation-closure-design.md
captured_at: '2026-07-22'
id: gd32l235-pa11-charge-soc-power-gate-design-20260722
title: GD32L235 PA11 关机、充电与 SOC 上电门控设计归档
kind: project-archive
domain: projects/gd32l235
path: projects/gd32l235/archive/design/2026-07-22-pa11-charge-soc-power-gate-design.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: source-project-design-document
  from: workspace://gd32l235/Docs/PA11关机禁止充电与SOC上电禁止设计.md
  source_sha256: a55b6c43ee09f2f0eac5ea8ea9a563467aa4b94f59ad495869835f37addc2a5e
review_after: '2026-08-22'
review_status: human-reviewed-accepted
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- gd32l235
- pa11
- charge
- soc-power
validation_refs:
- projects/gd32l235/archive/design/2026-07-22-pa11-charge-soc-power-gate-design.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/gd32l235/archive/design/2026-07-22-pa11-charge-soc-power-gate-design.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-07-22'
updated_at: '2026-07-26'
generated_by_ai: true
ai_role: classified
ai_model_or_tool: Codex
ai_generated_at: '2026-07-22'
manual_validation_pending: true
summary_zh: 归档 PA11 用户意图、PA15 SOC 电源控制、关机禁充电及 SOC 上电门控的设计演进与硬件证据；现行接口以源码和协议规范为准。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
---

# PA11 关机禁止充电与 SOC 上电禁止设计

## 归档说明

- 本文是 2026-07-22 迁移的硬件/固件联合设计快照，保留当时的推导过程；`status=reviewing`，不直接代表当前量产硬件结论。
- 当前接口与状态机以 MCU/SOC 源码、`workspace://gd32l235/Docs/串口通信协议规范.md` 和[当前低功耗协同契约候选](../../current/soc-low-power-contract.md)为准。
- 本文引用的 EVT2 原理图、系统框图、IO 说明和 BOM 尚未登记为 Hub artifact；涉及二极管 DNP、PA15 供电边界的硬件断言在 artifact 与板级复核完成前保持 `manual_validation_pending`。
- Review：owner `leiwenjun`；复审日期 2026-08-22；重点补齐硬件 artifact、板型差异和 PA11 OFF 冷态测试证据。

> 2026-07-22 硬件与协议终态更新（优先于本文旧章节）：PA15 可以单独切断 SoC 电源，MCU 与 WiFi 保持供电；PA11 是用户意图输入，不再被解释为“PA11 ON 时 SoC 无法单独掉电”。PA11 稳定 OFF 后必须启动 `0x09` 关机事务。若 SoC 处于 STANDBY/SLEEP，MCU 先输出一次 9 ms PA8 唤醒脉冲再发送 `0x09`；若处于 DEEP_SLEEP，SoC 已掉电，不重新上电。文中“PA11 OFF 时一律禁止 PA8/0x09”和“PA15 只释放 MCU 整机保持”的旧描述均由本条取代。

> 2026-07-18 契约更新：`SOC_CONFIRMED` 是 MCU 退出事务的不可撤销点。确认到达前，PA11 稳定回到 ON 可取消；确认到达后，MCU 必须完成既定 PA8/PA15 动作。POWER_KEY 路径至少保持 PA15 OFF 100ms，再按最新 PA11 稳定状态决定继续掉电或重新上电。

## 1. 背景

最终产品规则需要收敛为：

```text
PA11 拨动开关为 ON 时，允许 SOC 上电、唤醒、运行和受控休眠。
PA11 拨动开关为 OFF 时，SOC 必须被视为禁止上电对象。
PA11 OFF 后上充电桩，不支持充电，也不能由充电桩触发 SOC 或整机开机。
```

本文件基于以下硬件资料重新定义 MCU 侧电源策略：

- `PCR02 EVT2 GD32L235CBT6（LQFP48）单片机IO功能说明.docx`
- `PCR02 EVT2电源树-20251201.pdf`
- `PCR02 EVT2 系统框图-20251201.pdf`
- `PCR02_MAIN_V2.0_20251211.pdf`

## 2. 原理图证据

### 2.1 PA11 / PA15 / PA8 的 IO 定义

| 信号 | 方向 | 作用 | 设计含义 |
|---|---|---|---|
| PA11 | 输入 | 开关机拨动开关状态检测，1 表示开机，0 表示关机 | SOC 是否允许工作的最高门禁 |
| PA15 | 输出 | SoC 电源保持 | 可独立切断或恢复 SoC 电源，不影响 MCU/WiFi 保持 |
| PA8 | 输出 | 控制 SOC 工作模式，1 为 SOC 开机/唤醒，0 为 SOC 休眠 | 只做 SOC wake/sleep，不是整机电源总开关 |
| PB7 | 输出 | WIFI 模块内部供电控制，0 打开，1 关闭 | PA11 OFF 时应关闭或保持低功耗 |
| PB10 | 输出 | 电池充电使能 | PA11 OFF 时必须关闭，且不能被温度保护或 SOC 命令重新打开 |

### 2.2 系统框图中的拨动开关路径

系统框图说明：

```text
用户通过 SWITCH 实现开关机。
SWITCH 同时接在总 MOSFET 和 MCU IO 口上。
SWITCH ON 时，通过二极管拉低总 MOSFET 栅极，Vsys 上电，MCU 开始工作。
MCU 启动后检测 SWITCH 为 ON，通过二极管继续拉低总 MOSFET 栅极。
SWITCH OFF 时，MCU 检测到状态后通知 SOC 关机，收到回应或超时后撤去拉低总 MOSFET。
```

该说明证明：拨动开关路径和 MCU 保持路径是硬件“或”的关系。

### 2.3 硬件反馈：EVT2 取消充电直接开机路径

`PCR02_MAIN_V2.0_20251211.pdf` 第 3 页“系统供电总开关”原理图中画有 `CHARGING_DET` 参与总 MOSFET 导通的二极管路径：

```text
CHARGING_DET   --|<|--
KEY_PWRON_KEEP --|<|--  -> PQ4 -> Q9110 gate -> BATT_DCIN 到 VCC_SYS
PWR_KEY        --|<|--
```

硬件反馈确认：

```text
charging 的那路二极管实际没贴。
设计初期曾考虑“充电直接开机”。
EVT2 已取消该要求，EVT2 后面的板子都把该二极管拆掉。
```

因此 EVT2 及后续正常贴片板上，系统总电源 MOSFET 的有效导通来源应收敛为：

```text
KEY_PWRON_KEEP 有效
或 PWR_KEY / PA11 拨动开关路径有效
```

`CHARGING_DET` 只应作为充电桩检测信号使用，不应再被视为系统上电许可。

这是本次设计修正后的核心硬件证据：产品规则“PA11 OFF 后不支持充电，也不支持充电触发开机”在 EVT2 后续板型上是硬件语义自洽的。

## 3. 修正后的硬件结论

### 3.1 PA15 OFF 加 PA11 OFF 应能阻断充电桩直接开机

当 PA11 为 OFF 时，MCU 可以拉低 PA15，释放 `KEY_PWRON_KEEP`。

在 EVT2 及后续正常贴片板上，`CHARGING_DET` 的总电源导通二极管未贴，因此上充电桩不应再通过该路径打开总 MOSFET。

因此：

```text
PA11 OFF + PA15 OFF + 上充电桩，不应触发 VCC_SYS / SOC 直接开机。
PA11 OFF 后是否允许充电和 SOC 上电，统一由 PA11 产品语义决定，而不是 charging。
```

仍需保留一个工程边界：如果存在早期样板、返修板或贴片差异，`CHARGING_DET` 二极管实际被贴上，则该板会退化为“充电可硬件拉起 VCC_SYS”的旧风险。上板验收必须用波形或串口启动日志确认当前板型 BOM。

### 3.2 SOC 物理不上电的保证来源从“固件兜底”变为“硬件 DNP + 固件门禁”

SOC 的 RTC 域由 `3V3_RTC` 供电，原理图中 SOC 侧存在：

```text
AVDD33_RTC -> 3V3_RTC
PAD_RTC_IO0 / PAD_RTC_IO1 / PAD_RTC_IO4 / PAD_RTC_IO5
```

结合电源树，SOC RTC/PM 管脚会参与 SOC 主电源 rail 的使能。因此，最终产品语义需要两层保证：

1. 硬件层：`CHARGING_DET -> 系统总 MOSFET` 的二极管 DNP/拆除，充电桩不能直接打开 VCC_SYS。
2. 固件层：只要 MCU 已经运行，就必须把 PA11 作为最高门禁，PA11 OFF 时禁止 PA15 keep、PA8 wake、PB10 充电。

在这两层同时满足时，可以按产品语义声明：

```text
PA11 OFF 后，上充电桩不支持充电，也不支持充电触发 SOC 开机。
```

其中“不支持充电”还需要一个硬件默认态条件：PA11 OFF 冷态下 MCU 不会被 charging 拉起，PB10 固件也不会运行，因此充电禁止不能只依赖 MCU 输出。必须确认以下任一条件成立：

- 充电芯片/充电回路的 EN 默认态为禁充，PB10 只有被 MCU 主动拉到允许态后才充电；
- 或充电回路依赖 VCC_SYS/MCU 上电后才具备充电条件；
- 或 PA11/总电源路径从硬件上同时切断了充电回路许可。

如果 PB10 在 MCU 未上电高阻态下会被外部电阻默认拉到充电允许态，则“PA11 OFF 冷态不充电”不能由当前固件保证，需要调整硬件默认拉阻或 charger EN 逻辑。

如果验收中仍出现 PA11 OFF + 上充电桩触发 SOC boot log，应优先检查板级贴片、`CHARGING_DET` 到总 MOSFET 的实际连通、SOC RTC/PM rail 使能波形，而不是继续用 MCU 侧补丁掩盖。

### 3.3 charging 不能再作为 SOC 上电或充电许可

旧逻辑中曾存在“PA11 为 ON 或 charging 为 true 就允许 PA15 保持和 SOC 唤醒”的判断方式。在新产品规则下，这类逻辑必须调整。

新的裁决原则是：

```text
PA11 决定 SOC 是否允许工作，也决定是否允许充电。
Charging_Flag 只表示充电桩检测状态，不决定 SOC 是否允许上电，也不决定 PB10 是否允许充电。
```

## 4. 最终产品状态定义

建议 MCU 侧按 PA11 和 charging 联合裁决产品状态：

| PA11 | Charging | 产品状态 | SOC 策略 | MCU 策略 |
|---|---|---|---|---|
| 1 | 0 | RUN | 允许上电/唤醒/业务运行 | PA15 ON，正常外设 |
| 1 | 1 | RUN 或 CHARGE_CERT_SLEEP | 允许受控运行或认证休眠 | PA15 ON，按充电策略处理 |
| 0 | 0 | OFF | 禁止唤醒；若 SOC 在线则关机握手后 PA15 OFF | PA15 OFF hold |
| 0 | 1 | SWITCH_OFF_CHARGE_BLOCK | 禁止 MCU 主动唤醒 SOC；不发 SOC sleep/wake | PB10 禁止充电，PA15 OFF；EVT2 后续板通常不会因充电冷态进入该状态 |

### 4.1 SWITCH_OFF_CHARGE_BLOCK 定义

`SWITCH_OFF_CHARGE_BLOCK` 是针对 `PA11 == 0 && Charging_Flag == true` 的专门状态。

在 EVT2 后续正常贴片板上，PA11 OFF 冷态上充电桩不应给 MCU/VCC_SYS 上电，因此通常不会从全关机冷态进入该状态。该状态仍需要保留，用于以下窗口：

- 设备已经由 PA11 ON 启动，随后在充电期间拨动到 OFF；
- PA11 抖动或快速反复拨动期间，MCU 仍在运行；
- 早期样板或异常贴片导致 charging 仍能拉起系统；
- 调试供电或外部供电让 MCU 处于运行态。

该状态下：

1. PA15 必须保持 OFF，不允许因为 charging 拉高 PA15。
2. 除 STANDBY/SLEEP 退出所需的一次 9 ms wake pulse 外，PA8 保持非唤醒态；DEEP_SLEEP 不发脉冲。
3. 发送并每 400 ms 重发 `CMD_SHUTDOWN_STAGE_NOTIFY/COMMAND_SENT`，最多等待 6 s。
4. 不进入充电认证 SOC 休眠流程。
5. 仅在已同步状态为 STANDBY/SLEEP 时执行一次 `SOC_Wakeup()`，用于完成 best-effort 安全退出。
6. 不启动或恢复依赖 SOC 的外设链路。
7. PB7/WIFI、IR、TOF、IMU、MOTOR 等按最小功耗策略关闭或保持低功耗。
8. PB10 必须输出禁止充电。
9. 温度保护、电量计读取、充电状态检测可以继续运行，但不能重新打开 PB10。
10. PA11 从 0 变为 1 后，才允许退出 `SWITCH_OFF_CHARGE_BLOCK` 并进入正常 SOC 上电/充电策略。

### 4.2 可承诺项和不可承诺项

固件可以承诺：

```text
PA11 OFF 时，MCU 不主动拉高 PA15 维持系统电源。
PA11 OFF 时，MCU 不主动通过 PA8 唤醒 SOC。
PA11 OFF + charging 时，MCU 进入 SWITCH_OFF_CHARGE_BLOCK，不触发 SOC 休眠/唤醒协议，不打开 PB10 充电。
任何 SOC 上电允许动作都必须先复核 PA11 == 1。
```

固件不能承诺：

```text
未确认 BOM 的早期板或异常贴片板上，PA11 OFF + 上充电桩一定不会有 VCC_SYS。
SOC RTC/PM 外围如果存在其他独立电源路径，MCU 固件无法单独阻断。
```

## 5. MCU 侧设计规则

### 5.1 PA11 是 SOC 上电最高门禁

建议提供统一 helper，所有 SOC 上电/唤醒/保持路径都必须使用：

```c
static bool Bsp_SocPowerAllowed(void)
{
    return !Bsp_PowerSwitch_IsStableOff();
}

static bool Bsp_SwitchOffChargeBlocked(void)
{
    return Bsp_PowerSwitch_IsStableOff() && RunParam.Charging_Flag;
}
```

含义：

- `Bsp_SocPowerAllowed()` 只看 PA11，不看 charging。
- `Bsp_SwitchOffChargeBlocked()` 表示 MCU 已经处于运行态，但当前 PA11 OFF 且检测到 charging，产品策略禁止 SOC 和充电。EVT2 后续板不依赖该状态阻断冷态充电开机，但运行态仍必须处理。

### 5.2 PA15 控制规则

PA15 只允许在这些情况下为 ON：

| 条件 | PA15 |
|---|---|
| PA11 == 1 | ON |
| PA11 == 0 且等待 SOC 退出，且 SOC 已在线需要安全退出 | 临时 ON，直到确认或超时 |
| PA11 == 0 且 SWITCH_OFF_CHARGE_BLOCK | OFF |
| PA11 == 0 且 SOC 不在线或退出超时 | OFF |

启动阶段在 PA11 状态尚未稳定时，`Power_Init()` 最多在 OFF/ON 防抖总窗口内临时保持 PA15，避免单次低电平毛刺造成误掉电；一旦稳定确认为 OFF，立即进入 OFF hold。该临时保持只用于输入确认，不构成 charging 许可，也不允许 PA8 唤醒 SOC 或 PB10 开启充电。

严禁：

```text
RunParam.Charging_Flag == true -> PA15 ON
```

### 5.3 PA8 控制规则

PA8 只做 SOC wake/sleep。

PA8 执行动作前必须复核：

```text
PA11 == 1
```

例外：无。

也就是说：

- PA11 OFF 时，不发 PA8 wake。
- PA11 OFF 时，不发 PA8 sleep。
- PA11 OFF + charging 时，不走充电认证 sleep pulse，不允许 PB10 充电。

原因是 PA8 sleep pulse 本身要求 SOC 参与；若产品要求 SOC 禁止上电，不能为了让 SOC sleep 而先让 SOC 进入可响应状态。

### 5.4 SOC 协议规则

`CMD_SHUTDOWN_STAGE_NOTIFY` 继续用于三类“SOC 应用退出后再执行硬件动作”的场景：

| reason | 使用条件 | 允许条件 |
|---|---|---|
| POWER_KEY | PA11 从 ON 变 OFF，且 SOC 已在线或需要安全退出 | 可临时保持 PA15 等 SOC 退出 |
| LOW_BATTERY_SLEEP | PA11 ON、非充电、低电量稳定满足 | PA8 sleep，PA15 ON |
| CHARGE_SLEEP | PA11 ON、充电认证 profile 需要 SOC 退出应用 | PA8 sleep，PA15 ON |

`PA11 OFF + charging` 不使用 `CHARGE_SLEEP`，而是进入 `SWITCH_OFF_CHARGE_BLOCK`。

SOC 主动发送 `CMD_SLEEP_CONTROL` 时，MCU 接收和实际执行前也必须复核 PA11：

```text
PA11 == 1 -> 按原业务策略允许 sleep/standby
PA11 == 0 -> 拒绝或转入 POWER_KEY 关机策略，不执行 SOC sleep/standby
```

### 5.5 充电管理规则

最终产品规则确定为“拨动开关关机后不支持充电，也不支持充电触发开机”，因此 PB10 最终输出必须增加 PA11 产品门禁：

```text
PB10 最终输出 = PA11 允许充电 && 上层允许 && 温度保护允许
```

其中：

```text
PA11 == 1 -> PA11 允许充电
PA11 == 0 -> PA11 禁止充电
```

SOC 串口命令 `CMD_CHARGE_ENABLE_CONTROL` 只能修改“上层允许”因子，不能绕过 PA11 产品门禁。

## 6. 和现有低电量 / 充电认证设计的关系

### 6.1 低电量 SOC 休眠保护

低电量 SOC 休眠只允许在：

```text
PA11 == 1
&& charging == false
&& battery_percent <= 2
&& 启动宽限、连续采样、电压交叉确认均满足
```

低电量保护仍是：

```text
通知 SOC 退出 -> 等 SOC_CONFIRMED 或 6s 超时 -> PA8 sleep -> PA15 ON
```

PA11 OFF 时，低电量逻辑不介入；系统进入 OFF 或 SWITCH_OFF_CHARGE_BLOCK。

### 6.2 充电认证 SOC 休眠

充电认证 SOC 休眠只允许在：

```text
PA11 == 1
&& charging == true
&& GD32L235_CHARGE_CERT_PROFILE enabled
```

PA11 OFF + charging 时，不执行：

```text
发送 CMD_SHUTDOWN_STAGE_NOTIFY
等待 SOC_CONFIRMED
PA8 长脉冲 SOC sleep
离座 PA8 wake
```

### 6.3 拨动开关关机

PA11 从 1 到 0 时：

1. 如果 SOC 已在线，MCU 可临时保持 PA15 ON，通知 SOC 应用退出。
2. `SOC_CONFIRMED` 到达前，PA11 稳定回到 1 时取消关机并保持 PA15 ON。
3. 收到 `SOC_CONFIRMED` 后事务进入不可撤销阶段，继续等待 2s settle，但总等待不超过 6s，然后执行 PA15 OFF。
4. 未收到确认而走 6s 超时兜底时，执行动作前仍复核 PA11；已经回到 1 则取消。
5. PA15 OFF 至少保持 100ms；不可撤销阶段内 PA11 回到 1 时，最小 OFF 保持结束后重新上电。

如果 SOC 不在线或处于启动早期，POWER_KEY 关机不主动 PA8 wake，避免“拨到关 -> SOC 被唤醒启动到一半 -> 再掉电”。

## 7. 需要修改的代码点

### 7.1 `bsp.c`

1. 增加 `Bsp_SocPowerAllowed()` / `Bsp_SwitchOffChargeBlocked()`。
2. `Soc_Exit_Manager_SetKeepBySwitch()` 只由 PA11 和 active POWER_KEY shutdown 决定 PA15，不再由 charging 决定。
3. `Bsp_Init()` 早期同步 charging 后：
   - PA11 OFF + charging -> 进入 SWITCH_OFF_CHARGE_BLOCK 初始化路径；
   - PA11 OFF + 非 charging -> 进入 OFF hold；
   - 只有 PA11 ON 才继续完整外设初始化和 SOC 相关动作。
4. `Power_Key_Status_Det_Event()` 中 PA11 OFF 优先级高于 charging。
5. `Wakeup_Event()` 中 PA11 OFF 时直接拒绝，不因 charging 例外。
6. `EXTI7_IRQHandler()` 中充电插入时：
   - PA11 ON -> 原充电认证或充电上报策略；
   - PA11 OFF -> SWITCH_OFF_CHARGE_BLOCK，不唤醒 SOC，不发 shutdown notify，不允许 PB10 充电。
7. `Charge_Certification_RequestSocSleep()` 和 `Charge_Certification_SocControl_Event()` 增加 PA11 ON 门禁。
8. `Low_Battery_SocSleep_Event()` 增加 PA11 ON 门禁。

### 7.2 `main.c`

启动左右电机、SOC wake、常规外设初始化的条件改为：

```text
PA11 == 1
```

不能再使用：

```text
PA11 与 charging 的或条件
```

### 7.3 `protocol.c`

SOC 主动 sleep/standby 请求：

1. 接收阶段：PA11 OFF 时拒绝或转 POWER_KEY 关机策略。
2. 实际进入 STOP/STANDBY 前：复核 PA11。
3. 从 STOP/STANDBY 回来后：如果 PA11 已 OFF，不再恢复 SOC，转关机或 SWITCH_OFF_CHARGE_BLOCK。

### 7.4 `protocol_handlers/system_handler.c`

`CMD_SLEEP_CONTROL` 和 shutdown 相关 handler 中：

- PA11 OFF 不因 charging 例外。
- PA11 OFF + charging 进入 SWITCH_OFF_CHARGE_BLOCK，不执行 SOC sleep/standby，不允许 PB10 充电。

### 7.5 文档同步

需要同步更新：

- [低电量 SOC 休眠保护设计归档](2026-07-22-low-battery-soc-sleep-protection-design.md)
- [SOC Shutdown 确认闭环设计归档](2026-07-22-soc-shutdown-confirmation-closure-design.md)
- `workspace://gd32l235/Docs/串口通信协议规范.md`（源码仓当前规范）
- `README.md` 的 Release/功能说明仅在发版时更新版本号，不因中间修复频繁升级。

## 8. 分阶段落地计划

### 阶段 1：文档和行为边界固化

目标：

- 固化 EVT2 后续板 `CHARGING_DET` 总电源导通二极管 DNP/拆除的硬件证据。
- 将 `PA11 OFF + charging` 明确定义为 `SWITCH_OFF_CHARGE_BLOCK`。
- 明确产品语义由“硬件 DNP + PA11 固件门禁”共同保证，旧贴片风险需要板级确认。

验收：

- 设计文档明确目标、非目标、硬件证据、固件可承诺项和不可承诺项。
- 旧文档不再描述“PA11 OFF 且非充电才是最高关机门禁”。

### 阶段 2：统一 PA11 门禁

目标：

- 所有 SOC wake/sleep/power keep 路径改为先检查 PA11。
- charging 不再直接允许 PA15 ON 或 SOC_Wakeup。

验收：

- 全仓搜索不存在“PA11 与 charging 的或条件”作为 SOC/PA15 允许条件。
- PA11 OFF 时所有 PA8 动作被拒绝或跳过。
- PA11 OFF + charging 不进入充电认证 SOC sleep，且 PB10 保持禁止充电。

### 阶段 3：SWITCH_OFF_CHARGE_BLOCK 初始化路径

目标：

- `Bsp_Init()` 和 `main.c` 在 PA11 OFF + charging 时只做最小状态处理。
- 不启动 SOC 依赖外设。
- 不允许 PB10 充电。

验收：

- PA11 OFF + 上充电桩，MCU 不发 SOC wake pulse。
- PA11 OFF + 上充电桩，MCU 不发送 `CMD_SHUTDOWN_STAGE_NOTIFY`。
- PA11 OFF + 上充电桩，PB10 保持禁止充电。

### 阶段 4：快速拨动和 SOC 未运行快速关机

目标：

- PA11 OFF 时不主动唤醒 SOC。
- SOC APP 未运行时，拨动开关关机可快速 PA15 OFF，不等待完整 SOC 退出。
- PA11 运行态判断使用防抖后的稳定状态，原始 GPIO 只用于采样，不直接驱动 SOC 退出、PA8 唤醒或 PA15 掉电动作。
- 未收到 `SOC_CONFIRMED` 的取消/超时路径在 PA15 OFF 前最后复核 PA11；已确认事务不再取消。

验收：

- PA11 OFF->ON 发生在确认前时，旧确认和旧超时不能再 PA15 OFF。
- PA11 OFF->ON 发生在确认后时，完成至少 100ms PA15 OFF hold 后重新上电。
- PA11 快速 OFF/ON/OFF 时，只有连续稳定后的最新状态能驱动事务收敛。
- PA11 OFF 且 SOC 不在线时，不出现“先唤醒 SOC 再掉电”。
- PA15 OFF 至少保持 100ms。

### 阶段 5：上板验证

建议验证项：

| 用例 | 输入 | 期望 |
|---|---|---|
| PA11 OFF，未充电 | 上电或复位 | PA15 OFF hold，不发 PA8 wake |
| PA11 OFF，冷态上充电桩 | `CHARGING_DET=1` | VCC_SYS/SOC 不应被充电桩直接拉起；无 SOC boot log |
| PA11 OFF，冷态上充电桩 | 测 PB10/charger EN/充电电流 | PB10 未被 MCU 驱动时 charger 默认禁充；无充电电流 |
| PA11 OFF，运行态上充电桩或充电中拨到 OFF | `Charging_Flag=1` | 进入 SWITCH_OFF_CHARGE_BLOCK，不发 PA8 wake，不发 SOC shutdown notify，PB10 禁止充电 |
| PA11 OFF，上充电桩 | 观察 VCC_SYS | EVT2 后续板应保持不上电；若上电，检查二极管是否误贴或存在其他 PM 路径 |
| PA11 OFF，上充电桩 | 观察 SOC 串口 | 不应出现 boot log；若出现，优先归因板级贴片/PM 路径异常 |
| PA11 ON，上充电桩 | charging=true | 按正常充电或认证策略处理 |
| PA11 ON->OFF | SOC 在线 | 通知 SOC 退出，确认后 settle，最终 PA15 OFF |
| PA11 ON->OFF | SOC 未在线 | 不主动 PA8 wake，快速或超时 PA15 OFF |
| PA11 OFF->ON | `SOC_CONFIRMED` 前 | 取消关机，PA15 ON，允许 SOC 继续运行 |
| PA11 OFF->ON | `SOC_CONFIRMED` 后 | 完成至少 100ms PA15 OFF hold，再重新上电 |
| PA11 OFF + charging -> PA11 ON | 用户打开拨动开关 | 退出 SWITCH_OFF_CHARGE_BLOCK，允许 SOC 正常启动和充电 |

## 9. 风险和需硬件确认项

| 风险 | 影响 | 建议 |
|---|---|---|
| 早期板或异常贴片仍装了 charging 二极管 | PA11 OFF 上充电桩时系统仍会有电 | 做 BOM/实物确认，测 `CHARGING_DET` 到总 MOSFET 控制路径 |
| PB10/charger EN 在 MCU 未上电时默认允许 | PA11 OFF 冷态仍可能给电池充电 | 确认 EN 默认拉阻和充电电流；必要时硬件改为默认禁充 |
| SOC RTC/PM 存在其他自动开主电源路径 | PA11 OFF 上充电桩仍可能出现 SOC boot log | 需要测 `PAD_RTC_IO4/IO5`、SOC 主电源 EN 波形 |
| 充电认证旧需求要求 MCU+WIFI 工作 | 与“PA11 OFF 禁止 SOC/禁止充电”冲突 | 以 PA11 产品规则优先；认证模式只在 PA11 ON 时启用 |
| charging 被旧代码当作 SOC 允许条件 | 拨动开关 OFF 时仍可能启动 SOC | 全仓替换为 PA11 门禁 |
| PA11 抖动 | 确认前旧请求 late action 导致误掉电 | generation/token + 确认前最终复核；确认后按不可撤销事务完成最小 OFF hold |
| SOC APP 未运行 | 关机等待过长或唤醒 SOC 到一半 | 增加 SOC offline 快速关机路径，不主动 PA8 wake |

## 10. 最终结论

1. EVT2 及后续板已取消“充电直接开机”要求，`CHARGING_DET` 到系统总电源 MOSFET 的二极管实际 DNP/拆除。
2. 因此 PA11 OFF + PA15 OFF + 上充电桩，在正常 EVT2 后续贴片板上不应触发 VCC_SYS/SOC 开机。
3. “PA11 OFF 冷态不充电”还依赖 PB10/charger EN 的硬件默认态为禁充；MCU 未上电时固件无法主动拉 PB10。
4. 固件终态仍必须把 `PA11` 作为 SOC 上电最高门禁，不能把 `charging` 作为 SOC 上电许可或 PB10 充电许可。
5. `PA11 OFF + charging` 的运行态正确软件行为是 `SWITCH_OFF_CHARGE_BLOCK`：禁止 PB10 充电，不主动唤醒 SOC，不执行 SOC sleep/wake 协议。
6. 如果实测仍出现 PA11 OFF 上充电桩触发 SOC boot，应按硬件异常或板型差异排查：二极管是否误贴、PM/RTC 是否有其他开主电路径、PA11/PA15 波形是否符合预期。
