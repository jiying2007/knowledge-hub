---
related:
- projects/gd32l235/archive/reference/2026-07-20-charge-chain-pdf-text-index.md
- projects/gd32l235/archive/debug/2026-07-17-battery-rail-drop-mcu-reboot.md
human_reviewed_by: null
human_reviewed_at: null
review_basis: null
id: gd32l235-dock-discharge-cw2217-zero-data-initial-analysis-20260720
title: GD32L235 充电桩持续放电与 CW2217 全零数据初步分析
kind: debug-record
domain: projects/gd32l235
path: projects/gd32l235/archive/debug/2026-07-20-dock-discharge-cw2217-zero-data-initial-analysis.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: session-derived-debug-summary
  from: user observations, Serial_mcu_2026-07-18_10_43_24.log, three local PDF sources, schematic and workspace://gd32l235
    source review
review_after: '2026-08-20'
review_status: human-reviewed-accepted
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: archive-only; root cause and fixes require board validation
tags:
- gd32l235
- charging
- sc8922
- cw2217
- battery-pack
- pb10
- ntc
- fuel-gauge
- dock-discharge
validation_refs:
- projects/gd32l235/archive/debug/2026-07-20-dock-discharge-cw2217-zero-data-initial-analysis.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: strong-source-code-match-with-board-root-cause-pending
evidence_refs:
- projects/gd32l235/archive/reference/sc8922-datasheet-text.txt
- projects/gd32l235/archive/reference/cw2217baad-datasheet-text.txt
- projects/gd32l235/archive/reference/cxy18650-2s-7v4-2500mah-approval-20260622-text.txt
- workspace://mcu/Serial_mcu_2026-07-18_10_43_24.log
- workspace://gd32l235/App/cw2217.c
- workspace://gd32l235/App/bsp.c
- workspace://gd32l235/App/charge.h
created_at: '2026-07-20'
updated_at: '2026-07-26'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-07-20'
manual_validation_pending: true
manual_validation_reason: 尚缺 SC8922 PG、VIN、VSYS、VBAT、CHARGE_NTC、PB10、VDD_GAUGE、两节单体电压和真实电池电流的同一时间基准板级证据
summary_zh: 初步判断实际停充与电量计全零是两个可能串联的问题；CW2217 复位或处于 Shutdown 后返回零寄存器，而固件把 I2C 成功的零值当成有效测量并不再初始化，该软件缺口有直接代码证据；SC8922 停充首因仍需在
  24 小时安全定时器、PB10/NTC 控制和输入功率不足之间实测证伪。
primary_language: zh-CN
source_language: mixed
translation_status: summarized-in-chinese
terminology_status: pending-review
---

# GD32L235 充电桩持续放电与 CW2217 全零数据初步分析

## 现象

当前需要解释两个现象：

1. 设备长时间放在充电桩上，前期可以充电，后续仍持续放电直至 0%；可能与温度、充电器状态或电池保护逻辑有关。
2. 设备在充电桩上时，CW2217 前期工作，后续电量、电压、充电电流、工作电流全部为 0，温度为 -40℃。

本记录保存截至 2026-07-20 的初步证据和假设，不声明板级根因已经确认，也不声明修复完成。

## 当前结论摘要

最符合现有证据的工作模型是两个问题串联：

```text
充电桩输入仍被 PA7/CHARGING_DET 检出
  -> SC8922 因安全定时器、NTC/使能或输入功率条件停止实际充电
  -> 系统通过 power-path 继续消耗电池
  -> 低电量时保护板关断，或 VDD_GAUGE 出现掉电/毛刺
  -> CW2217 复位并回到 Shutdown/默认寄存器状态
  -> CW2217 仍可能 ACK I2C，但 VCELL/SOC/TEMP/CURRENT 返回零值
  -> 当前固件把 I2C 成功的全零组合当成有效数据
  -> 对外表现为 0V、0%、0mA、-40℃，同时 bat_ok 仍为 1
```

该模型中，“固件接受 CW2217 全零数据且不重新初始化”已有直接代码证据；“SC8922 为什么停止充电”和“CW2217 的实际掉电触发点”仍是待验证推断。

## 资料来源

三份资料的可搜索全文和原 PDF 身份见：

- [GD32L235 充电链三份 PDF 派生全文索引](../reference/2026-07-20-charge-chain-pdf-text-index.md)
- [SC8922 datasheet 派生全文](../reference/sc8922-datasheet-text.txt)
- [CW2217BAAD datasheet 派生全文](../reference/cw2217baad-datasheet-text.txt)
- [CXY18650-2S 电池承认书派生全文](../reference/cxy18650-2s-7v4-2500mah-approval-20260622-text.txt)

## 日志时间线摘要

对 `Serial_mcu_2026-07-18_10_43_24.log` 最后一次稳定启动段的初步解析结果：

- 稳定运行约 38.4 小时。
- PA7/`charging` 在稳定段一直为 1。
- `bat_ok` 初始化成功后一直为 1。
- SOC 在运行约 7.208 小时后进入最终持续 100% 阶段。
- SOC 约在 26.717 小时后开始持续下降。
- 随后约 3.9 小时从 100% 单调下降到 0%。
- 早期曾出现多次 SOC 充到 100%、下降、再回到 100% 的周期。
- 旧日志没有逐次 PB10 边沿、SC8922 PG、CHARGE_NTC、VDD_GAUGE 或真实电池电流，不能据此确认停充时的具体硬件状态。

PA7/`CHARGING_DET=1` 只能证明充电桩输入电压检测存在，不等价于 SC8922 正在向电池提供净充电电流。

## 资料中可确认的器件机制

### SC8922

- 支持 2/3 节电池升压充电和 power-path。
- 系统负载优先使用输入电源；输入能力不足时，电池可通过 Q3 补充系统负载，因此设备插在充电桩上仍可能净放电。
- 正常充电终止后，当电池电压降到目标电压约 96% 以下时应自动恢复充电。电量穿过该门限仍持续下降，不能只用普通 EOC 解释。
- 充电安全定时器约为 24 小时。若充电周期未正常完成而超时，芯片会进入 Shutdown，资料描述需要 VIN 重新上电后恢复。
- NTC 过冷或过热会停止充电；PG 高阻同时可能表示 EOC、VIN UVLO 或 NTC 异常，单一 PG 电平仍需结合 VIN、NTC 和电池电流判断。
- 输入限流、VINREG 或适配器能力不足会降低充电电流，严重时系统可能持续从电池补电。

### CXY18650-2S 电池包与保护板

- 2S、7.4V、2500mAh，2MOS，10K 1%、B=3435 NTC。
- 单节过充检测典型约 4.28V，解除典型约 4.08V。
- 单节过放检测典型约 2.90V，解除典型约 3.00V。
- 保护板静态工作电流典型约 7µA、最大约 12µA，不足以在数小时内把 2500mAh 电池耗尽。
- 过放或过流保护后可能需要移除负载或接入充电器恢复。
- 推荐充电温度为 0～45℃。

因此，保护板过放关断可以解释低电量末端的电源消失和 CW2217 掉电，但不能解释从接近满电开始持续放电的首发原因。两节电芯不一致时，某一节可能先达到过放门限，必须测量单体电压。

### CW2217

- 上电后默认处于 Shutdown，需要主机通过 CONFIG Restart/Active 流程启动测量。
- `VERSION=0xA0` 在 Shutdown 和 Active 状态均可能成立，不能单独作为运行健康判据。
- VCELL、SOC、CURRENT 等测量寄存器在未有效工作时可能为 0。
- 温度换算为 `T = -40 + TEMP_RAW / 2`，所以 `TEMP_RAW=0` 精确映射为 -40℃。
- UPDATE_FLAG 在 POR 后会清除，可作为掉电/重启诊断信息之一。
- VDD 高于约 2.4V 后可进行 I2C 通信，低于约 2.2V 时停止通信；实际边界仍需在板上测量。

“0V、0%、0mA、-40℃”这组同步出现的数据，更像 CW2217 没有处于有效测量状态，而不是电池物理量同时真实为零。

## 软件代码证据

### 首次初始化有状态检查

`App/cw2217.c` 的非阻塞初始化流程会检查：

- VERSION 是否为 `0xA0`；
- CONFIG 是否为 Active；
- UPDATE_FLAG 是否存在；
- 电池 profile 是否匹配；
- 必要时写入 profile，并执行 Restart、Sleep、Active 和 Ready 等待。

### 运行期不再确认芯片仍然 Active

初始化成功后，`App/bsp.c` 的 `Battery_EnsureInitialized()` 只要看到 `Battery_Init_OK_Flag=true` 就直接返回。后续没有周期检查：

- CONFIG 是否仍为 Active；
- UPDATE_FLAG 是否因 POR 被清除；
- IC_STATE 是否 Ready；
- FW_VERSION 是否符合 Active 状态；
- 多个测量寄存器是否构成不可能的全零组合。

### 全零值会被当成读取成功

- VCELL 原始值为 0 时仍返回读取成功。
- SOC 原始值为 0 时换算成 0%，仍返回成功。
- TEMP 原始值为 0 时换算成 -40℃，仍返回成功。
- CURRENT 原始值为 0 时换算成 0mA，仍返回成功。
- 采样结束后调用 `Battery_MarkReadSuccess()`，因此 `bat_ok` 可继续保持为 1。

当前只有 I2C 事务返回失败并累计到阈值后，才会清除初始化标志并重新初始化。若 CW2217 仍能 ACK I2C、但处于 Shutdown 并返回零寄存器，这一路径不会触发。

初始化流程本身还存在一个较弱的条件：`CHECK_DATA` 只要 VCELL I2C 读取成功就可进入 DONE，即使原始数据为 0。该条件也应在后续修复中加强。

## 假设矩阵

| 假设 | 问题 1：停充后放电 | 问题 2：全零/-40℃ | 当前状态 |
| --- | ---: | ---: | --- |
| SC8922 24 小时安全定时器 Shutdown | 高 | 间接高 | 高优先级待证伪 |
| PB10/CHARGE_NTC 未恢复、极性或外围异常 | 高 | 间接中 | 高优先级待证伪 |
| 充电桩功率不足、VIN 掉压、power-path 补电 | 高 | 间接中 | 高优先级待证伪 |
| SC8922 NTC 温度保护 | 中高 | 低 | 需要温控和 NTC 电压复测 |
| 电池保护板从满电主动切断 | 低 | 中 | 不像首发原因 |
| 电池保护板在低电量过放关断 | 低 | 高 | 可能是末端事件 |
| CW2217 掉电/复位后处于 Shutdown | 不解释停充 | 高 | 高概率触发模型，待测 VDD_GAUGE |
| 固件接受全零寄存器且不重初始化 | 不解释停充 | 极高 | 代码直接支持 |
| 真实环境温度为 -40℃ | 低 | 极低 | 基本排除 |
| 保护板 7～12µA 静态耗电 | 极低 | 无 | 排除为数小时放空原因 |
| 普通 EOC 后自然放电 | 极低 | 无 | 穿过约 96% 未回充，与独立 EOC 机制冲突 |

## 温度与 PB10 的安全边界

原理图显示 PB10/`MCU_EN_CHARGE` 通过 MOS 管影响 `CHARGE_NTC`，不是一个独立的 charger EN 状态输入。SC8922 资料说明 NTC 引脚拉到接近地时可关闭 NTC 检测。

如果实板装配和极性确认 PB10 的允许充电状态同时旁路 SC8922 硬件 NTC，则存在以下风险：

- 电池承认书推荐充电上限为 45℃；
- 普通固件默认高温停充阈值为 60℃；
- 硬件 NTC 若被旁路，MCU 可能成为唯一温度保护；
- CW2217 温度无效时，软件又可能把 -40℃当成合法低温值。

这目前是原理图与资料推断，必须通过 PB10 高低状态下的 CHARGE_NTC 电压、SC8922 行为和实际装配确认，不能直接写成已确认硬件事实。

## 建议的板级复测

### 连续充电复现

从 30%～50% SOC、25℃环境开始，连续运行 30～48 小时，每秒记录：

- PA7/CHARGING_DET；
- PB10 命令、GPIO 输出寄存器和引脚实际电平；
- CHARGE_NTC 电压；
- SC8922 PG；
- VIN、VSYS、VBAT；
- 电池实际双向电流；
- 两节单体电压；
- VDD_GAUGE；
- CW2217 I2C 返回码和原始寄存器。

CW2217 至少记录 `VERSION 0x00`、`VCELL 0x02-0x03`、`SOC 0x04-0x05`、`TEMP 0x06`、`CONFIG 0x08`、`INT_CONF 0x0A`、`SOC_ALERT/UPDATE_FLAG 0x0B`、`CURRENT 0x0E-0x0F`、`IC_STATE 0xA7` 和 `FW_VERSION 0xAB`。

### 故障现场的单变量操作

发现电池开始净放电后先保持现场：

1. 记录全部信号至少 1 分钟。
2. 只切换 PB10，不动 VIN；观察实际充电电流是否恢复。
3. PB10 恢复原状态后，只拔插充电桩/VIN；观察充电是否恢复。

判据：

- 只切 PB10 即恢复：优先检查 PB10/CHARGE_NTC 状态机、极性和外围。
- PB10 不恢复、VIN 重上电立即恢复：强支持 SC8922 安全定时器或输入故障锁存。
- VIN 重上电也不恢复：检查 NTC、输入功率、保护板、功率器件和电芯。
- VIN 存在但电池电流持续为负：确认 PA7 只是输入存在，实际处于补电或停充。

### CW2217 故障注入

仅在调试样机上：

1. MCU 由充电桩保持运行时短暂切断 VDD_GAUGE，随后恢复。
2. 观察现有固件是否出现 `0V/0%/0mA/-40℃/bat_ok=1`。
3. 只断开 BAT_NTC，确认是否仅温度异常而其他寄存器不全零。
4. 人为制造 SDA/SCL 硬故障，确认现有 I2C 失败重初始化路径与“ACK 但零寄存器”不同。

## 建议的软件整改方向

以下是建议，不代表已实现：

1. 周期检查 CONFIG、UPDATE_FLAG、IC_STATE 和 FW_VERSION。
2. 将 VCELL/SOC/CURRENT/TEMP 原始值同步全零定义为无效签名。
3. 区分“I2C 失败”“I2C 成功但芯片未 Active”“芯片 Active 且测量有效”三种状态。
4. 无效样本不得作为真实 0V、0% 或 -40℃发布；温度无效时应进入安全停充状态。
5. 触发非阻塞重新初始化，并记录复位原因、原始寄存器和恢复耗时。
6. 加强初始化 `CHECK_DATA`，不能仅以 VCELL I2C 读取成功作为完成条件。
7. 继续记录 PB10 每次物理翻转、原因、脉冲序号和最终恢复电平。

## 根因状态

根因未确认，当前状态为 `reviewing/manual-validation-pending`。

已由代码直接支持的结论只有：当前固件会接受 CW2217 的全零寄存器组合并保持初始化成功状态，因此无法从 `bat_ok=1` 推导电量计仍在有效测量。

SC8922 的 24 小时安全定时器、PB10/CHARGE_NTC、输入功率不足、VDD_GAUGE 掉电和保护板末端关断仍需上述板级证据闭环。

## Review

- owner：leiwenjun
- review_after：2026-08-20
- 下一次复核：补充故障时序波形、CW2217 原始寄存器、单变量 PB10/VIN 恢复实验和两节单体电压。
