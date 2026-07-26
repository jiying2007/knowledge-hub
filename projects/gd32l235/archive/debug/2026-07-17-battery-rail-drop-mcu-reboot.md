---
human_reviewed_by: null
human_reviewed_at: null
review_basis: null
incident_id: null
severity: intermittent-reboot
affected_version: v1.1.37 诊断工作区；v1.1.35 对照待上板
related: []
id: gd32l235-battery-rail-drop-mcu-reboot-20260717
title: GD32L235 电池供电跳变与 MCU 循环重启排障记录
kind: debug-record
domain: projects/gd32l235
path: projects/gd32l235/archive/debug/2026-07-17-battery-rail-drop-mcu-reboot.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: session-derived-debug-summary
  from: 2026-07-17 user-provided board observation and logs plus workspace://gd32l235 source review
  source_sha256: dbf0d6f236f97b15b79d72f139702db9214e2d01f5081277311e99de38845e5d
review_after: '2026-10-17'
review_status: human-reviewed-accepted
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- gd32l235
- battery
- power-integrity
- por-reset
- pa15
- intermittent-reboot
validation_refs:
- projects/gd32l235/archive/debug/2026-07-17-battery-rail-drop-mcu-reboot.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: moderate-board-observation-and-source-review-root-cause-pending
evidence_refs:
- projects/gd32l235/archive/debug/2026-07-17-battery-rail-drop-mcu-reboot.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
- 用户提供的连续 Stage1/App 启动日志摘要
- 硬件排查观察到电池供电电压跳变、MCU 掉电后电压恢复并重新启动
- Stage1/main.c 复位源与清除后寄存器诊断
- App/power.c 与 App/bsp.c 的 PA11/PA15、低电量和负载上电路径只读核对
- v1.1.35 到 v1.1.37 的相关源码差异核对
created_at: '2026-07-17'
updated_at: '2026-07-26'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-07-17'
manual_validation_pending: true
manual_validation_reason: 尚缺电芯、BMS/VCC_SYS、MCU 3V3、PA15、PA11、PC14 的同一时间基准波形，以及同板同电池 v1.1.35/current A/B 结果
summary_zh: 记录 GD32L235 电池供电跳变、POR/V12/EPR 复位与循环重启的当前证据；纯软件复位和低电量直接掉电已降级，最强假设为软件负载阶跃触发边缘供电，但根因仍待同步波形与同板 A/B 闭环。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
---

# GD32L235 电池供电跳变与 MCU 循环重启排障记录

## 现象

- 设备运行时 MCU 有概率重新进入 Stage1 和 App 启动流程。
- 已观察到电池供电电压发生跳变：电压下降导致 MCU 掉电，负载退出后电压恢复，MCU 随后重新开机。
- 启动日志可以完整到达 `[APP] run`，此前采样中 `PA11=1`、`PA15=1`，随后再次出现 Bootloader 日志。
- 本记录只保存日志摘要、源码证据和后续判据，不复制完整 raw 串口日志、固件二进制或本机 cache。

## 影响范围

- 项目：GD32L235 Firmware。
- 启动链：Stage0 -> Stage1 -> App。
- 可能涉及：电池/电芯、BMS、连接器、总电源 MOSFET、VCC_SYS、MCU 3V3、PA11/PA15 电源保持、电机 MCU 供电、IR/Wi-Fi/SOC 负载和充电控制。
- 当前无法确认是否影响所有硬件批次、所有电池或仅边缘样机。

## 环境与版本边界

- 当前源码基线：`v1.1.37`，工作区包含尚未提交的 UART 有界轮询恢复和启动/掉电诊断打印。
- 对照基线：`v1.1.35`。
- 普通固件配置：`GD32L235_CHARGE_CERT_PROFILE=OFF`、`GD32L235_DEBUG_UART_PRINTF=ON`、`GD32L235_RTT_ENABLED=OFF`。
- 本记录不把本地工作区状态视为已发布、已合并或量产事实。

## 时间线

| 日期 | 操作或观察 | 结果 |
| --- | --- | --- |
| 2026-07-17 | 连续观察 Stage1/App 启动日志 | 多次到达 `[APP] run` 后重新进入 Stage1 |
| 2026-07-17 | 增加复位源、APP 存活和 PA15 关闭前诊断 | 普通版与 charge-cert 构建/检查通过，待实机抓取新日志 |
| 2026-07-17 | 硬件排查电池供电 | 观察到供电电压跳变导致 MCU 掉电，掉电后电压恢复并重新启动 |
| 2026-07-17 | 核对 v1.1.35 至当前的电源、低电量、充电与外设路径 | 排除纯软件 reset 和低电量逻辑直接关闭 MCU；保留“软件负载触发边缘供电”假设 |

## 已确认的证据

### 1. 复位来源

典型 Bootloader 摘要：

```text
[BL] reset raw=0x0C800000 v12=1 epr=1 por=1 sw=0 fwdg=0 wwdg=0 lp=0
```

- `V12RSTF/EPRSTF/PORRSTF` 被置位，与供电跌落或外部复位链路一致。
- `SWRSTF=0`、`FWDGTRSTF=0`、`WWDGTRSTF=0`，不支持软件复位或看门狗复位作为当前主因。
- 已新增 `reset after_clear`，用于确认每次启动后复位来源位确实清除，避免把历史累计标志误判为本次来源；实机结果待补。

### 2. PA11/PA15 硬件和软件边界

- PA11 是拨动开关状态输入，PA15 是 MCU 的 `KEY_PWRON_KEEP` 保持输出。
- 产品硬件说明中，拨动开关路径和 MCU 保持路径对总 MOSFET 是“或”关系；PA11/物理开关仍为 ON 时，PA15 单独释放不应切断 VCC_SYS。
- `Power_Init()` 在启动早期直接按 PA11 原始状态设置 PA15。
- 运行态 PA11 以 20 ms 周期采样，连续 OFF 200 ms 后才启动 POWER_KEY 关机事务；执行 PA15 OFF 前还会复核 PA11 稳定状态。
- 已新增 `[APP] pa15 off ...`，且打印发生在 PA15 拉低之前，用于识别固件主动释放电源保持的路径。

### 3. 低电量路径

- 低电量保护需要启动宽限、连续低电量确认和电压交叉确认。
- 低电量动作是通过 PA8 请求 SOC 休眠，PA15 保持 ON。
- 因此，电量计误判可能让 SOC 误休眠，但按当前设计不会直接切断 MCU/VCC_SYS。

### 4. 软件可控制的负载

APP 启动后会打开或保持多项负载：

- PB7 低有效，保持 Wi-Fi 模块内部供电。
- PC13 打开 IR 接收供电。
- PC14 对电机 MCU 电源执行 30 ms 断电、重新上电并等待 50 ms 稳定。
- 随后探测两个电机 MCU，并发送进入运行态命令。
- SOC 运行后还可能下发电机速度、IR 和其他业务控制。

这些动作可能形成电流阶跃。若电池内阻、BMS、连接器、总 MOSFET 或 DC/DC 余量不足，软件可能作为触发器造成供电跌落；MCU 掉电后负载消失，电压恢复，拨动开关硬件路径重新上电，形成循环。

### 5. v1.1.35 之后的相关差异

- `App/power.c` 的 PA11/PA15 基础控制没有变化。
- 电机 MCU 电源循环、启动探测和运行态命令在 v1.1.35 已存在，因此不是 v1.1.35 后新增的启动负载，但在供电余量退化时仍可能成为触发条件。
- v1.1.35 后新增的自动快/慢充和满充 PB10 脉冲只应在 PA7 检测到充电且满足温度/电量条件时工作；纯电池模式且 `charging=0` 时优先级较低。
- IR 距离采样实现有变化，但 IR 供电打开行为不是新引入；IR 调试镜像默认未启用，因为 RTT 默认关闭。
- UART 有界轮询和诊断打印会增加少量 CPU/UART 活动和时序延迟，不足以解释健康供电上的明显电池电压跳变；在极端临界电源上只能视为微小扰动，不应作为根因结论。

## 假设矩阵

| 假设 | 当前概率 | 证据或验证动作 | 当前状态 |
| --- | --- | --- | --- |
| 电池/BMS/连接器/电源链余量不足，软件负载阶跃触发掉电 | 高 | 供电电压跳变、POR/V12/EPR、掉电后电压恢复；需同步波形和隔离负载 | 最强工作假设，未确认 |
| PA11 异常变低后固件主动释放 PA15 | 中 | 查看 `[APP] pa15 off`、最后一条 `alive` 和 PA11/PA15 波形 | 待验证 |
| PC14 电机 MCU 上电或后续电机命令触发过流/压降 | 中高 | 单变量关闭 PC14 或断开电机电源，对比重启率 | 待验证 |
| PA7 误判充电，触发 PA12 快充或 PB10 脉冲 | 低到中，取决于 `charging` | 电池模式确认 PA7=0、`charging=0`，观察 PB10/PA12 | 条件相关 |
| 电量计误判直接关闭 MCU | 低 | 源码确认低电量只走 PA8 sleep、PA15 ON | 已排除为直接掉电机制 |
| UART DMA/同步发送或软件 reset 直接重启 MCU | 低 | 复位源 `sw=0`、看门狗位为 0，且有真实供电跳变 | 已排除为首要机制 |

## 当前根因状态

根因未确认，状态为 `needs-fix`。

当前最符合证据的因果模型是：

```text
软件打开电机/IR/Wi-Fi/SOC 等负载
  -> 电流阶跃触发边缘电池/BMS/VCC_SYS/3V3 跌落
  -> MCU 发生 POR/V12/EPR 复位并停止驱动负载
  -> 电压恢复
  -> 拨动开关硬件路径重新给系统上电
  -> APP 再次打开负载，循环重现
```

该模型同时包含硬件供电余量问题和软件触发条件，不能在缺少同步波形与 A/B 实验时单独归责软件或硬件。

## 已执行的诊断增强

- Stage1：记录复位源清除前后的 `RCU_RSTSCK`。
- APP：每 1000 ms 输出一次 `alive`，包含 PA11 原始/稳定状态、PA15、charging、电量有效性、电量、SOC exit 状态和原因。
- APP：所有 BSP 内 PA15 OFF 路径在实际拉低前输出 `pa15 off`。
- PA15 OFF 前同步串口打印约增加 7-10 ms 诊断延迟；这是调试代价，不代表产品终态时序已经签收。

## 软件验证记录

| 验证 | 结果 | 边界 |
| --- | --- | --- |
| 12 项启动、UART、SOC、电机、电量与 Bootloader 定向测试 | PASS | 离线契约测试，不替代实机供电验证 |
| `rtk bash scripts/codex-check.sh --full` | PASS | 普通版 fresh build/package/check |
| charge-cert fresh build + `fwtool.py check --scope build` | PASS | 只证明该配置可构建和满足构建门禁 |
| ELF 字符串检查 | PASS | 三条新增诊断字符串进入目标镜像 |
| `rtk git diff --check` | PASS | 工作区 diff 格式检查 |

构建通过不能证明电源问题已修复，当前没有“修复完成”声明。

## 下一轮最小板级实验

### 1. 同步波形

以 MCU 3V3 下降沿触发，同时采集：

1. 电芯端电压。
2. BMS 输出或 `BATT_DCIN/VCC_SYS`。
3. MCU 3V3/VDD。
4. PA15；下一轮切换 PA11 或 PC14。

判据：

- 电芯随电流明显下跌：电芯内阻、低电量或连接问题。
- 电芯稳定而 BMS 输出突然断开：BMS 过流/欠压保护或连接器。
- VCC_SYS 稳定而 3V3 下跌：MCU DC/DC/LDO、去耦或局部负载。
- PA15 先下降再掉电：检查固件关机和 PA11。
- VCC_SYS/3V3 先下降、PA15 后失效：供电先出问题，PA15 只是随掉电失效。

### 2. 单变量 A/B

1. 同一固件更换已知正常电池。
2. 同一电池暂时关闭 PC14 或断开电机驱动电源。
3. 纯电池模式确认 PA7=0、`charging=0`，观察 PB10/PA12。
4. 同一块板和电池分别运行 v1.1.35 与当前固件。

### 3. 日志判据

保留从最后一条 `alive` 到下一次 Bootloader 的连续日志：

```text
[APP] alive ...
[APP] pa15 off ...      # 若存在
[BL] reset raw=...
[BL] reset after_clear=...
```

若最后一条 `alive` 为 `pa11=1/pa15=1`、没有 `pa15 off`，随后出现新一轮 POR/V12/EPR，并且波形显示 VCC_SYS/3V3 先跌落，可基本排除正常软件关机路径。

## 归档边界

- 本条目是项目级 `reviewing` debug-record，不是已确认根因、发布结论或 active 规则。
- 不授权刷机、提交、发布、硬件改版、owner decision 或 active promotion。
- 不写入 memory，不复制完整 raw 日志或固件二进制。
- 后续同步波形或同板 A/B 若推翻当前工作假设，应新建或更新带证据的记录，并显式标注 supersedes 关系，不静默把推测改成事实。

## Archive Gate

- Source：2026-07-17 用户提供的板级现象、串口日志摘要和 `workspace://gd32l235` 当前源码只读核对。
- Topic：`debug-notes` / `gd32l235-power-integrity`。
- Sanitization：PASS；无 secret、token、凭证、客户材料、完整 raw 日志或二进制。
- Provenance：用户现场观察 + 当前源码 + v1.1.35 对照核查 + 本地构建验证。
- Memory Candidate：no。
- Gate Result：`needs-fix/reviewing`，根因和实机修复尚未闭环。
