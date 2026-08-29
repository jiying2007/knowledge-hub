---
id: gd32l235-pcr02-thermal-charge-motor-maintenance-v116-20260822
title: PCR02 温度、充电接触、电机供电及维护模式 v1.16 设计归档
kind: project-archive
domain: projects/gd32l235
path: projects/gd32l235/archive/design/2026-08-22-pcr02-thermal-charge-motor-power-maintenance-v1.16.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: project-design-doc
  from: gd32l235 Docs design baseline 0224a343c36b468fa2d03a103aa67912fbad1877, captured 2026-08-22
  source_sha256: a2bfbbf3db4fe1a64a0022a48dcbc6911b13ecc52cadc12dfa4959360e97feee
review_after: '2026-09-22'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- gd32l235
- pcr02
- charge-interlock
- motor-power
- motor-ota
- motor-calibration
- motion-epoch
validation_refs:
- projects/gd32l235/archive/design/2026-08-22-pcr02-thermal-charge-motor-power-maintenance-v1.16.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/gd32l235/archive/design/2026-08-22-pcr02-thermal-charge-motor-power-maintenance-v1.16.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-08-22'
updated_at: '2026-08-22'
generated_by_ai: true
ai_role: summarized
ai_model_or_tool: Codex
ai_generated_at: '2026-08-22'
manual_validation_pending: true
summary_zh: PCR02 v1.16 冻结 PB10/PA12、电机供电、温度状态机、运动事务和 OTA/校准维护设计，APP 安全停机通过单一入口保证 motion_epoch 单推进。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
---

# PCR02 温度、充电接触、电机供电及维护模式详细设计与实施计划

## 1. 文档状态

- 设计版本：v1.16
- 归档日期：2026-08-22
- 设计基线：`gd32l235` commit `0224a343c36b468fa2d03a103aa67912fbad1877`
- 当前状态：详细设计基线冻结，代码实现、独立复审、HIL 和量产验证待完成
- 适用范围：PCR02 主板 MCU App 的充电温度、PB10/PA12、主动出桩、电机供电、运动事务、电机 OTA、霍尔校准和安全停机
- 非目标：不修改 Stage0/Stage1，不改变主板 OTA 分区，不替代 BMS，不宣称现有代码已经符合本设计

本文是当前实现和验证需要共同遵守的工程契约。线协议的现行定义仍以《串口通信协议规范》和《主板MCU串口通信与转发协议规范》为准。

## 2. 设计结论

本设计将安全保护、充电接触防打火、上桩电机节能和电机维护流程统一为 MCU 内部状态机，同时保持现有量产协议和主要产品行为：

- `0x12` 保持 4 字节速度载荷和默认无 ACK，不增加业务序号或周期运动租约；
- `0x13` 保持现有 ACK，使用完整载荷和 `motion_epoch` 去重；
- `0x35`、`0x36`、`0x37`、`0x38` 线协议不变；
- 正常充电继续由 MCU 根据温度自动选择 2A/1.25A；
- 电机 OTA 的命令、分片、重试、超时、ACK、错误码和左右目标路由不变；
- 霍尔校准 `0x18/0x19` 的命令、状态格式、任务超时和正常执行流程不变；
- 普通双零、普通电机停机、`STOPPED` 和上桩空闲断电不禁止 PB10 充电；
- 硬温度、传感器、掉电等不可变安全边界优先于充电、运动、OTA 和校准。

## 3. 职责与安全优先级

| 对象 | SOC 主责 | MCU 主责 |
| --- | --- | --- |
| 电池充电 | 业务许可、APP 状态 | PB10、PA12、温度与接触互锁 |
| 电池放电 | 暂停业务、待机、提示 | 关闭电机、IR 等可控负载 |
| 电机温度 | 70/60°C、-10/-5°C 业务保护 | 80/70°C、-20/-15°C 灾难级兜底 |
| 上桩节能 | 维持业务状态 | 电机空闲断电和按需唤醒 |
| 电机 OTA | 固件及阶段控制 | 供电保持、协议转发和安全终止 |
| 霍尔校准 | 发起和查询 | 供电保持、异步执行和安全终止 |

MCU 不替代 BMS。若 MCU 无法切断电池主回路，电池放电保护只能关闭电机、IR 等 MCU 可控负载，电芯最终保护由 BMS 完成。

安全优先级：

```text
系统掉电/关机
> 电机/电池硬温度、传感器故障
> 急停和安全隔离
> 主动出桩接触保护
> OTA/校准维护保持
> 普通停机
> 上桩空闲节能
> 普通业务请求
```

## 4. 模块和 GPIO 唯一写入者

| 输出 | 唯一写入模块 |
| --- | --- |
| PB10 充电使能 | `ChargeDockInterlock` |
| PA12 充电电流档位 | `ChargeCurrentManager` |
| `MOTOR_PWR_EN` | `MotorPowerManager` |
| IR 电源 GPIO | `IrPowerManager` |

其他模块只能提交请求、cap、锁、停机原因或维护保持。BSP、ISR、协议 handler 和温度恢复路径不得旁路仲裁器写 GPIO。

主要模块：

- `ChargeDockInterlock`：PA7 去抖、下降沿立即断 PB10、PB10 仲裁和主动出桩预断充；
- `ChargeCurrentManager`：PA12 唯一写入、自动快慢充和所有电流 cap 仲裁；
- `ChargeConfigManager`：`0x37/0x38` 校验、默认/待生效/锁存配置；
- `ThermalGuard`：充电温度、电机温度、电池放电和传感器新鲜度；
- `MotorPowerManager`：电机上电、断电、稳定等待、空闲断电和 OTA Boot 紧急硬切；
- `MotorStopManager`：APP 运行态 `StopAndVerify`、安全隔离、`motion_epoch` 和停止确认；
- `MotionCommandGate`：运动缓存、出桩门禁和 `0x13` 完整请求去重；
- `MotorMaintenanceManager`：OTA/校准维护状态、电源保持和维护终止；
- `IrPowerManager`：IR 请求、安全锁和恢复后重新授权。

## 5. PB10 与 PA7 接触互锁

PB10 允许开启：

```text
dock_stable
&& PA11允许
&& soc_charge_requested
&& soc_online
&& charge_temperature_allowed
&& battery_sample_fresh
&& 无系统关机准备
&& 无系统掉电准备
&& 无主动出桩锁
&& 无充电安全锁
&& PA7仍为在桩状态
```

充电安全锁至少包括 `PRE_STOP/HARD_LOCK`、温度样本无效或超时、电池放电温度锁、SOC 离线和产品定义的禁止充电故障。

普通双零、普通 `StopAndVerify`、`STOPPED`、电机 MCU 空闲断电、OTA/校准维护保持本身不禁止 PB10。

上桩流程：

1. PB10 初始化为低；
2. PA7 上升后进入 `DOCK_DEBOUNCE`；
3. 连续有效达到 `T_INSERT_STABLE_MS`；
4. 取得新鲜温度；
5. 先完成 PA12 仲裁；
6. 再评估 PB10；
7. 条件全部满足后开启 PB10。

PA7 原始下降沿只能调用 IRQ-safe 的 `ChargeDockInterlock_OnRawDockFallingEdge()`。该接口立即关闭 PB10、取消充电脉冲并锁存离桩状态；去抖只影响上报，不能延迟断充。

## 6. PA12 电流仲裁

```text
pa12_output = min(
    normal_auto_request,
    thermal_current_cap,
    boot_current_cap,
    config_current_cap,
    sensor_current_cap,
    charge_path_cap)
```

任一 cap 要求 1.25A 时，PA12 不得输出 2A。

默认快慢充门限：

```text
F_RECOVER = 38°C
F_SLOW    = 45°C
```

首次有效温度低于 `F_SLOW` 时自动 2A，否则 1.25A。后续 FAST 在 `T>=F_SLOW` 时转 SLOW，SLOW 在 `T<F_RECOVER` 时恢复 FAST。

PB10 开启顺序固定为：

```text
charge_path_cap = PREPARE_AUTO
→ ChargeCurrentManager_Reevaluate()
→ PA12稳定
→ PB10开启
```

`0x36` 保持量产语义：未检测充电时可以预置档位，检测到充电时拒绝；它不构成持续的 SOC 快充许可。

## 7. 充电温度配置和状态机

默认值：

```text
L_STOP    = -3°C
L_RECOVER =  0°C
R         = 47°C
S         = 49°C
P         = S + 2°C = 51°C
H         = S + 3°C = 52°C
```

S 可配置，P/H 只能由 S 派生，且 `H<=T_CHARGE_HARD_ABS_MAX_C`。参数至少满足：

```text
L_STOP < L_RECOVER
R < S
P = S + 2°C
H = S + 3°C
```

状态优先级：

```text
HARD_LOCK
> PRE_STOP
> RECOVERY_SLOW
> LOW_PROTECT
> HOT_SLOW / HOT_QUALIFY
> NORMAL
```

- `NORMAL`：`T>=S` 进入 `HOT_QUALIFY`，`T>=P` 进入 `PRE_STOP`，`T>=H` 立即硬锁；
- `HOT_QUALIFY`：趋势窗口不足为“趋势未就绪”；只有明确下降才进入 `HOT_SLOW`；
- `HOT_SLOW`：仅 1.25A，按 PB10 实际开启时间累计最多 5 分钟；温度回落到 S 以下不清零本次上桩预算；
- `PRE_STOP/HARD_LOCK`：进入时锁存完整 R/S/P/H；宽松配置不能放松已有锁，更严格配置可以立即收紧；
- `RECOVERY_SLOW`：`T<effective_R`、趋势不升连续 60 秒后进入，强制慢充观察 120 秒；达到 `effective_S` 返回预停充，达到 `effective_H` 升级硬锁。

锁存规则：

```text
effective_R = min(lock_R, current_R)
effective_S = min(lock_S, current_S)
effective_P = effective_S + 2°C
effective_H = effective_S + 3°C
```

MCU 重启进入 `BOOT_UNKNOWN`：PB10 默认低、PA12 强制慢充、固定使用编译期签核默认配置完成趋势准备、60 秒安全观察和 120 秒慢充观察。启动期间仅允许立即应用更严格配置；宽松配置保存为 pending，进入 `NORMAL` 后再生效。

## 8. `0x37/0x38` 配置治理

```text
接收配置
→ 长度/范围校验
→ 参数交叉校验
→ 绝对边界校验
→ 保存候选
→ 判断立即或延迟生效
→ 重新评估状态机
```

规则：

- 更严格配置立即生效；
- 更宽松配置不能解除 `PRE_STOP/HARD_LOCK/RECOVERY_SLOW`；
- 无效、越界或矛盾配置不改变现有配置；
- 重启恢复签核默认配置；
- `0x38` 必须满足 `F_RECOVER<F_SLOW<=min(S,T_FAST_CHARGE_ABS_MAX_C)`；
- 降低 S 导致旧 `F_SLOW>S` 时接受更严格的新 S，并强制慢充/内部钳制，不能因旧 `0x38` 拒绝新 S。

## 9. 主动出桩与运动门禁

移动意图包括 `0x12` 任一非零、`0x13` 和其他实际可能导致移动的业务命令。

在桩收到移动意图：

1. 锁存 `departure_latched`；
2. 立即关闭 PB10 并取消充电脉冲；
3. 缓存最新运动命令；
4. 启动 `T_PRE_MOVE_OFF_MS`；
5. 若电机已断电，同时启动电机上电；
6. 预断充和电机上电并行；
7. PB10 已关闭、预断充等待完成且电机 READY 后才下发运动。

出桩失败必须清缓存，并调用 `StopAndVerify_Request(DEPARTURE_FAILED, SAFETY)`；PB10 保持关闭。

手动拿起无法预知，只能依靠 PA7 下降沿立即关 PB10，不能承诺机械触点分离前电流已经归零。

## 10. 上桩空闲断电

```text
dock_stable
&& stop_state == STOPPED
&& 无运动缓存
&& 无运动意图
&& 无maintenance_power_hold
&& 空闲时间达到MOTOR_DOCK_IDLE_OFF_MS
```

首次双零启动计时；重复双零/急停不得重置计时。OTA/校准期间暂停空闲断电。温度恢复不自动给电机上电。

## 11. `0x12` 与 `0x13`

`0x12` 保持无 ACK、速度变化时下发和单槽 `latest-wins`。安全隔离后旧邮箱通过 `motion_epoch` 失效。

`0x13` 最终事务指纹：

```text
seq
+ cmd
+ target
+ payload_len
+ 完整payload逐字节
+ motion_epoch
```

CRC 只能用于快速索引，最终命中必须比较完整 payload。事务状态为 `EMPTY/PENDING/FORWARDED/INVALIDATED`。失效事务在 `T_ACK_DEDUP_WINDOW_MS` 内保留完整指纹墓碑；旧重传只能返回现有 `STATE/BUSY`，不得重新执行。去重窗口只表示合法重传缓存时间，不表示业务命令绝对新旧。

新速度、新位置、停止、急停、模式切换、保护、电机断电、维护模式切换、SOC 离线和出桩失败都会使已有位置事务失效。

分发顺序：

```text
停止/急停安全动作
→ 维护模式识别
→ 0x13完整请求去重
→ 通用ACK缓存
→ MotionCommandGate
→ 电机协议转发
```

## 12. StopAndVerify 单一入口

APP 运行态所有普通和安全停机只能调用：

```text
StopAndVerify_Request(reason, OPERATIONAL | SAFETY)
```

分流规则：

```text
无活动事务：
    StartNewStopTransactionAtomic(reason, requested_isolation)

已有OPERATIONAL事务且收到SAFETY：
    EnterSafetyIsolationAtomic(reason)

已处于SAFETY：
    仅合并原因和严重度
```

`StartNewStopTransactionAtomic()` 在同一个原子事务中：

- 推进 `motion_epoch` 恰好一次；
- 设置请求的隔离级别；
- 初始化 `stop_request_tick`、左右反馈基准和 deadline；
- 发送左右 APP stop；
- 进入 `WAIT_CONFIRM`。

如果新事务直接请求 SAFETY，不得再额外调用 `EnterSafetyIsolationAtomic()`。

已有普通事务升级 SAFETY 时，`EnterSafetyIsolationAtomic()` 推进 epoch 恰好一次、清除运动关联状态，但不得重置原反馈基准、`stop_request_tick` 或 deadline。已处于 SAFETY 时重复原因不得推进 epoch。

所有 APP 温度、传感器、SOC 离线、急停、出桩失败调用方只能直接调用 `StopAndVerify_Request(reason, SAFETY)`，不得先隔离再停机，也不得直接写 `motion_epoch`。

## 13. motion_epoch 和停止确认

`motion_epoch` 只能由 `MotorStopManager` 私有原语 `MotionEpochAdvanceAndInvalidateAtomic()` 写入。允许调用它的只有新停机事务创建和已有普通事务升级安全隔离两个内部动作。

| 场景 | epoch 推进次数 |
| --- | ---: |
| 空闲建立普通停机 | 1 |
| 空闲建立 APP 安全停机 | 1 |
| 普通停机升级安全隔离 | 1 |
| 已处于安全隔离，重复原因 | 0 |
| 重复双零/急停 | 0 |
| OTA Boot 首次安全隔离 | 1 |
| OTA Boot 已安全隔离，重复原因 | 0 |

左右电机分别确认停止：反馈 tick 必须晚于请求 tick；连续不少于 `MOTOR_STOP_CONFIRM_SAMPLES` 个不同反馈帧；相邻间隔不超过 `T_STOP_FEEDBACK_MAX_GAP_MS`；速度、电流和通信均有效。任一条件失败清零连续计数；任一侧在 `T_STOP_CONFIRM_MS` 内未确认即硬切。

反馈计数器至少为 `uint32_t`，使用无符号回绕安全差值，不得用普通 `seq>base`。重复帧可刷新链路在线，但不得计入停止确认。

## 14. 电机 OTA 维护模式

现有 OTA 流程保持：

```text
0x2E 入Boot
→ 0x21 Begin
→ 0x27 Segment Info
→ 循环0x23 Write Chunk
→ 0x24 Verify
→ 0x26 Commit
→ 0x22 Reboot
```

建立 OTA 会话后设置 `maintenance_power_hold=true`。若电机因上桩空闲断电，必须先上电并等待 UART READY，再进入现有 OTA handler；上电等待不能侵占原 OTA 协议 timeout。

OTA Boot 模式：

- 不发送 APP stop、速度、位置或模式帧；
- 不创建 APP `StopAndVerify`；
- 不等待 APP 反馈；
- 普通双零丢弃，普通运动返回或记录 Busy/State；
- APP 反馈缺失是 Boot 预期状态，不能单独触发硬切。

硬温度、传感器失效、掉电和急停调用 `MotorMaintenanceManager_AbortOtaImmediate()`：关闭 OTA 发送门，停止后续发送，调用 `EnterSafetyIsolationAtomic()` 推进 epoch 一次，然后由 `MotorPowerManager_EmergencyCut()` 直接拉低 `MOTOR_PWR_EN`。不得发送 APP stop，不得等待当前 OTA 原子事务完成。

SOC 离线采用受控终止：禁止下一条 OTA；若已有一条 Write/Commit/Verify 在途，仅允许其在既有有界 timeout 内结束，不增加 timeout 或重试预算；之后进入一次安全隔离并切断电机供电，不自动续传。

HIL 必须证明 Boot 状态无 PWM/驱动输出和保持转矩，且关闭 `MOTOR_PWR_EN` 能消除驱动能力。若不能证明，需要独立驱动使能、功率关断或制动硬件。

## 15. 霍尔校准维护模式

`0x18/0x19` 现有协议保持。收到合法 `0x18` 后建立校准维护保持；若电机已空闲断电，先上电等待 READY，再执行现有 stop、settle 和 calibration begin。校准 timeout 从真正发出校准命令后计算。

校准期间禁止空闲断电和普通运动进入 UART；`0x19` 正常查询。发生急停、硬温度、传感器故障或 SOC 离线时取消校准，并调用 `StopAndVerify_Request(reason, SAFETY)`；未确认停止再由 `MotorPowerManager` 硬切。恢复后不得自动重启旧校准。

## 16. 电机温度、电池放电和 IR

电机温度：SOC 主策略为高温 70/恢复 60°C、低温 -10/恢复 -5°C；MCU 兜底为高温 80/恢复 70°C、低温 -20/恢复 -15°C。

APP 模式触发时调用 `StopAndVerify_Request(MOTOR_THERMAL, SAFETY)`；OTA Boot 调用专用立即终止。温度恢复只解除锁，不自动上电。

电池放电候选阈值为高温 58/恢复 50°C、低温 -18/恢复 -10°C。最终值必须由 BMS 范围、NTC 安装位置和实测温差签核。触发后关闭 PB10、IR、电机和其他可控高负载。

IR 输出必须叠加 `ir_rearm_required`。保护触发时关闭 IR 并锁存旧请求代次；保护恢复后必须收到新的 SOC 开灯请求，不能自动恢复旧请求。

## 17. SOC 离线

保持现有心跳判定，不要求 SOC 周期刷新 `0x12`。APP 模式离线时关闭 PB10，并调用 `StopAndVerify_Request(SOC_OFFLINE, SAFETY)`；校准模式取消校准后走同一入口；OTA Boot 按受控终止处理。

当前量产最坏离线识别约 30 秒，必须由产品书面接受，不能宣称为 500 ms 失联停机。

## 18. 实施计划

### 阶段 0：基线与契约测试

- 固定实现基线和现有量产协议测试；
- 增加 GPIO 唯一写入者静态检查；
- 增加 `motion_epoch` 唯一写入点检查；
- 为 `0x12/0x13`、OTA、校准和充电现有行为建立回归基线；
- 不修改业务功能。

完成标准：现有测试保持通过，新静态契约先能识别当前旁路写入点。

### 阶段 1：GPIO 仲裁收口

- 引入 `ChargeDockInterlock`、`ChargeCurrentManager`、`MotorPowerManager`、`IrPowerManager`；
- 收口 PB10、PA12、`MOTOR_PWR_EN` 和 IR GPIO；
- 保留现有正常时序参数，不在本阶段调整阈值；
- 把现有电机温度恢复直接上电改为提交仲裁请求。

完成标准：实际 GPIO 写操作只存在于唯一控制模块，量产基础行为回归通过。

### 阶段 2：充电接触和温度状态机

- 实现 PA7 上桩稳定确认和下降沿立即断 PB10；
- 实现 PB10 开启前 PA12 仲裁；
- 实现 `BOOT_UNKNOWN`、高温完整配置锁存和热态预算；
- 实现 `0x37/0x38` 联合校验和 pending 配置；
- 确保普通电机停机不影响 PB10。

完成标准：充电状态转换、配置故障注入和接触时序测试通过。

### 阶段 3：电机供电、运动门禁和 StopAndVerify

- 实现上桩空闲断电、按需上电和首条运动缓存；
- 实现主动出桩并行上电/预断充；
- 实现 `0x13` 完整 payload 去重和失效墓碑；
- 实现 `StopAndVerify_Request()` 单一入口；
- 实现 epoch 单推进、左右反馈确认和超时硬切。

完成标准：APP 空闲直接安全停机、普通停机升级安全隔离、重复原因三类 epoch 断言全部通过。

### 阶段 4：OTA/校准维护适配

- 引入 `MotorMaintenanceManager`；
- OTA/校准建立持久电源保持；
- 保留现有 handler 分发顺序和协议参数；
- OTA Boot 屏蔽 APP 帧并实现专用立即硬切；
- 实现 SOC 离线 OTA 受控终止；
- 校准安全事件继续使用 APP `StopAndVerify`。

完成标准：现有 OTA、校准全流程回归通过，维护期间空闲断电和普通运动不能干扰协议。

### 阶段 5：放电、IR 和诊断

- 接入电池放电兜底；
- 实现 IR 请求代次和恢复后重新授权；
- 增加本地状态、原因、epoch、维护阶段和配置日志；
- 本期不修改 `0x16` 位语义，不强制引入 `0x39/0x3A`。

完成标准：温度、传感器、SOC 离线和维护并发故障注入通过。

### 阶段 6：HIL 和量产放行

- 示波器验证 PA7/PB10、PA12/PB10、主动出桩、电流归零和电机上电波形；
- 验证 APP StopAndVerify 和硬切断；
- 验证 OTA Boot 无转矩及紧急硬切延迟；
- 验证关闭 `MOTOR_PWR_EN` 后无驱动能力；
- 完成 BMS/NTC 阈值签核；
- 固化所有候选时序参数；
- 完成独立代码审查和量产回归。

完成标准：所有量产 blocker 有证据关闭，才允许发布。

实施顺序必须按阶段推进。共享 GPIO 仲裁、`motion_epoch` 和协议分发属于共享契约，禁止拆成互相独立的并行实现。

## 19. 验收矩阵

必须覆盖：

1. PA7 抖动和下降沿立即关闭 PB10；
2. PB10 开启前 PA12 已稳定；
3. 主动出桩 PB10 关闭早于运动下发；
4. 普通双零完成停机和电机空闲断电后 PB10 仍可充电；
5. 高频 `0x12` 压力和单槽 latest-wins；
6. `0x13` 完整载荷、CRC 碰撞、seq/反馈/tick 回绕；
7. APP 空闲直接安全事件 epoch 只加一；
8. 普通停机升级安全隔离 epoch 只加一且不重置 deadline；
9. 已处于 SAFETY 的重复原因不推进 epoch；
10. 左右电机独立停止确认和单侧失联硬切；
11. OTA 完整流程、空闲唤醒、Boot 帧隔离和安全硬切；
12. 校准完整流程、空闲唤醒和安全中止；
13. `0x37/0x38` 收紧、放宽、冲突、重启和锁存；
14. `BOOT_UNKNOWN`、趋势窗口、热态预算和样本失效；
15. SOC 离线、IR 重新授权和电池放电故障注入。

## 20. 量产 blocker

- PB10 接触及电流归零波形未验证；
- PA12/PB10 输出顺序未验证；
- 主动出桩预断充时序未固化；
- APP 停机确认和硬切波形未验证；
- OTA Boot 无转矩及紧急硬切延迟未验证；
- `MOTOR_PWR_EN` 关闭后无驱动能力未验证；
- BMS/NTC 阈值未签核；
- SOC 最坏约 30 秒离线识别尚需产品书面接受；
- 代码实现和独立复审尚未完成。

## 21. 验证命令与证据边界

实现后至少运行：

```text
rtk bash scripts/codex-check.sh --full
rtk git diff --check
```

涉及 `App/protocol.c`、`App/motor_protocol.c`、协议 handler、UART、启动时序或 OTA 转发时，必须运行匹配的 `Tools/tests/check_application_*.py` 契约测试及完整 OTA/校准回归。

自动化构建或测试通过不等于 HIL、BMS/NTC、owner 或量产放行通过。所有证据必须记录对应 commit、硬件版本、参数版本和测试环境。

## 22. 归档与演进关系

本设计扩展了既有的“充电温度保护会话化与 PB10 计时”结论，新增接触互锁、PA12 仲裁、电机供电、运动事务、OTA/校准维护和安全停机契约。既有已实现行为和提交证据继续有效；本设计中尚未实现的内容不能反向解释为当前固件已经具备。
