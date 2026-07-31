---
id: gd32l235-dock-detected-without-net-charging-analysis-20260731
title: GD32L235 在桩检测有效但未发生净充电的当前结论
kind: debug-record
domain: projects/gd32l235
path: projects/gd32l235/archive/debug/2026-07-31-dock-detected-without-net-charging-analysis.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: current-session-code-and-history-analysis
  from: 2026-07-31 user question, workspace://gd32l235 current master code review, and existing 2026-07-20 debug archive
  source_sha256: aa43c5252d2711c4dcf87792d9298716d758c02ecc9a43558a90e2991713cc5d
  temporary_source_retained: false
review_after: '2026-08-31'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- gd32l235
- charging
- dock-detected
- net-charge-current
- sc8922
- cw2217
validation_refs:
- projects/gd32l235/archive/debug/2026-07-31-dock-detected-without-net-charging-analysis.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/gd32l235/archive/debug/2026-07-31-dock-detected-without-net-charging-analysis.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-07-31'
updated_at: '2026-07-31'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-07-31'
manual_validation_pending: true
summary_zh: 当前PA7充电桩检测仅代表输入存在，不等价于电池正向充电；PA11、上层许可、温度保护等可确定性造成上座但禁充，历史日志亦出现上座持续有效而SOC下降，SC8922板级首因和统计发生率仍待验证。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
---

# GD32L235 在桩检测有效但未发生净充电的当前结论

## 背景

用户询问 GD32L235 当前是否存在设备位于充电桩、能够监测到“充电状态”，但电池没有实际充电的场景或概率。本记录对 2026-07-31 当前 `master` 代码语义和既有历史排障证据进行归档，不声明 SC8922 板级根因已经确认。

## 结论

存在，而且需要区分“充电桩检测有效”和“电池正在获得正向净充电电流”。

- 当前 `Charge_Get_Status()` 只读取 PA7 `CHARGING_DET`。
- 协议 `CMD 0x32` 的定义是充电桩上座/离座检测，不是实际充电确认。
- PA7 为高时，PB10 仍可能因为 PA11 关机门禁、SOC 上层禁充、温度保护或充电通知脉冲而关闭。
- PA7 为高且 PB10 允许，也不能排除 SC8922 因安全定时器、NTC、VIN 欠压、输入限流或输入功率不足而停止充电；输入功率小于系统负载时，电池还可能通过 power-path 净放电。
- 因此不能从 `charging=1` 或 `CMD 0x32 payload=1` 推导电池正在充电。

建议采用以下判据：

```text
PA7=1：只能证明充电桩/输入存在。
PA7=1 + PB10允许 + 可信电池电流为正：才能判定正在实际充电。
PA7=1 + 可信电池电流为负：判定在桩但净放电。
```

## 已确认的软件场景

### PA11 门禁关闭

`Bsp_ApplySwitchChargePolicy()` 在 PA11 稳定状态为关闭时调用 `Charge_Set_SwitchAllowed(CHARGE_DISABLE)`。此时 PA7 仍可保持为高，但 PB10 最终输出被禁止。

### SOC 上层禁充

协议 `CMD_CHARGE_ENABLE_CONTROL (0x35)` 只控制上层充电许可因子。SOC 下发禁止后，PA7 上座状态不受影响，PB10 会被切断。

### 温度保护

当前代码在电池温度达到低温或高温保护阈值时清除温度许可并关闭 PB10。普通 profile 当前代码阈值为 `-3/0°C` 低温切断/恢复和 `49/46°C` 高温切断/恢复；认证 profile 为 `43/40°C` 高温切断/恢复。保护触发不改变 PA7 上座检测。

### 满电通知脉冲

满电通知通过 PB10 执行 10 次 `200 ms on + 200 ms off` 波形，期间存在短时断充。这属于预期瞬态，不足以单独解释数小时持续掉电。

## 既有现场证据

既有归档 `2026-07-20-dock-discharge-cw2217-zero-data-initial-analysis.md` 记录：

- 稳定运行段约 38.4 小时；
- PA7/`charging` 在稳定段一直为 1；
- SOC 约在运行 26.717 小时后开始持续下降；
- 随后约 3.9 小时从 100% 单调下降到 0%。

该记录证明现场曾出现“上座检测持续有效但没有维持净充电”的现象，但旧日志缺少 SC8922 PG、VIN、VSYS、VBAT、CHARGE_NTC、PB10 实际电平及真实双向电池电流，不能确认停充首因。

## CW2217 观测风险

当前运行期读取仍主要以 I2C 事务成功作为有效条件。若 CW2217 复位或处于 Shutdown 后继续 ACK、但电压/SOC/温度/电流寄存器返回全零，固件可能发布 `0V/0%/0mA/-40°C`，且不会仅因全零组合自动触发重新初始化。

因此实际充电判定需要先确认 CW2217 样本可信，不能把异常的 `0mA` 直接当作真实停充证据。

## 概率边界

- PA11 关闭、SOC 禁充或温度保护属于确定性触发条件；条件成立时必然可能出现“上座但不充电”，不是随机概率。
- 长时间在桩后持续掉电已有至少一份现场日志证据，不是纯理论风险。
- 当前缺少设备总量、版本分布、运行时长和复现次数，不能给出百分比、PPM 或 MTBF 等统计概率。
- SC8922 24 小时安全定时器、PB10/CHARGE_NTC、输入功率不足和 NTC 异常仍是待板级证伪假设。

## 建议验证

故障复现时在同一时间基准记录：

- PA7/CHARGING_DET；
- PB10 命令、GPIO 输出寄存器和引脚实测电平；
- SC8922 PG、VIN、VSYS、VBAT、CHARGE_NTC；
- 电池真实双向电流；
- 两节单体电压；
- VDD_GAUGE；
- CW2217 CONFIG、UPDATE_FLAG、IC_STATE、FW_VERSION 和原始测量寄存器。

单变量恢复实验：先只切换 PB10，再只重上电 VIN。PB10 操作恢复时优先排查 MCU 许可链和 CHARGE_NTC；只有 VIN 重上电恢复时优先排查 SC8922 安全定时器或输入故障锁存。

## 证据与来源

- Source repository: `workspace://gd32l235`
- Source branch: `master`
- Source verification date: 2026-07-31
- Code evidence: `App/charge.c`, `App/charge.h`, `App/bsp.c`, `App/cw2217.c`, `Docs/串口通信协议规范.md`
- Historical evidence: `projects/gd32l235/archive/debug/2026-07-20-dock-discharge-cw2217-zero-data-initial-analysis.md`
- Source type: current-session-code-and-history-analysis
- Captured at: 2026-07-31 Asia/Hong_Kong

## 状态与边界

- 状态：`reviewing`
- 人工/板级验证：待完成
- 已确认：PA7 上座检测不等价于实际正向充电；存在明确的软件禁充路径。
- 未确认：现场长时停充的 SC8922/板级首因及统计发生率。
- 不包含 raw log、凭证、设备序列号或二进制制品。
