---
as_of: '2026-07-22'
aliases:
- GD32L235 与 PCR02 SoC 低功耗协同当前契约候选
related:
- projects/gd32l235/README.md
- indexes/obsidian-home.md
- indexes/project-readiness.md
- projects/gd32l235/archive/design/2026-07-22-soc-mcu-power-transition-owner-tcpka.md
- projects/gd32l235/archive/debug/2026-07-22-soc-sleep-ebusy-early-wifi-wake.md
id: gd32l235-soc-low-power-contract
title: GD32L235 与 PCR02 SoC 低功耗协同当前契约候选
kind: project-current
domain: projects/gd32l235
path: projects/gd32l235/current/soc-low-power-contract.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: manual
  from: 当前 MCU/SOC 源码与 workspace://gd32l235/Docs/串口通信协议规范.md
  source_sha256: 73988fdebe08174c6a92f8bc6ec877f2fa73087bc72533eab451064e6b7f8b57
  temporary_source_retained: false
review_after: '2026-08-22'
review_status: human-reviewed-accepted
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- gd32l235
- pcr02
- low-power
- wake-source
- uart-protocol
validation_refs:
- projects/gd32l235/current/soc-low-power-contract.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/gd32l235/current/soc-low-power-contract.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-07-22'
updated_at: '2026-07-26'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-07-22'
manual_validation_pending: true
summary_zh: 汇总 GD32L235 MCU 与 PCR02 SoC 的 RUNNING、STANDBY、SLEEP、DEEP_SLEEP 状态职责、唤醒源、RTC、串口同步及诊断边界；reviewing 期间以源码和协议规范为权威。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
---

# GD32L235 与 PCR02 SoC 低功耗协同当前契约候选

## 状态与权威边界

本文汇总 MCU 与 SoC 当前低功耗协同边界，状态为 `reviewing`，不替代源码。出现冲突时按以下顺序核验：

1. MCU 与 SoC 当前分支的实际实现；
2. `workspace://gd32l235/Docs/串口通信协议规范.md`；
3. 本候选和关联历史归档。

旧名称 STR 不再使用，统一称为 `SLEEP`。协议不保留旧模式或旧 payload 兼容。

## 四状态契约

| SoC 状态 | SoC 行为 | WiFi | IMU | ToF | 合法唤醒源 | MCU 动作 |
| --- | --- | --- | --- | --- | --- | --- |
| RUNNING (`0x00`) | SoC 与应用正常运行 | ACTIVE | ACTIVE | ACTIVE | 无 | 丢弃运行态模块边沿，不输出 PA8 |
| STANDBY (`0x01`) | SoC 待机并保留内存上下文 | KEEPALIVE | WAKE_ARMED | WAKE_ARMED | WiFi、IMU、ToF | 输出 9 ms PA8 脉冲 |
| SLEEP (`0x02`) | SoC 进入系统休眠，可选 RTC 定时唤醒 | KEEPALIVE | OFF | OFF | WiFi；SoC RTC 独立有效 | WiFi 触发 9 ms PA8；RTC 由 SoC 自行恢复 |
| DEEP_SLEEP (`0x03`) | SoC 完成退出后由 MCU 拉低 PA15，SoC 掉电 | KEEPALIVE | OFF | OFF | 仅 WiFi | 拉高 PA15，完成冷启动 |

约束：

- RTC 是 SoC 自身 RTC，只用于 `SLEEP`；`rtc_wakeup_seconds=0` 表示禁用，必须清除旧 alarm。
- WiFi keepalive 配置和 firmware suspend 由 SoC `tcpka.cpp` 负责；MCU 只校验同步策略并处理 WiFi 唤醒线。
- RUNNING 下 IMU/ToF data-ready 和 WiFi 边沿不能转换为 SoC 唤醒。
- STANDBY 下 IMU/ToF 切为 wake-armed；SLEEP/DEEP_SLEEP 下必须停止并关闭。
- DEEP_SLEEP 是真实掉电，不是 suspend-to-RAM；恢复是完整冷启动。

## 状态同步与事务

1. SoC 发送固定 8B `0x0B` FULL 模块快照。
2. SoC 发送固定 6B `0x0D` 唤醒策略；两帧 `revision` 必须相同。
3. SoC 发送带 ACK 的 `0x04(mode)`；MCU 只在快照完整且精确匹配时原子布防。
4. MCU 可靠发送 `0x05(mode, ARMED)`；SoC 收到并成功 ACK 后才允许真正进入低功耗。
5. MCU 通过可靠 `0x07(source, result)` 回传非 RTC 唤醒结果；SoC 必须以 RTC/HDI 与 MCU 结果共同确认唤醒源。
6. MCU 在复位、快照缺失、revision 冲突或策略缺失时通过可靠 `0x0E` 请求重同步。

`0x05`、`0x07`、`0x0E` 均按 `CMD + SEQ` 可靠重试。`0x0B/0x0D` 不接受增量、旧长度或宽松状态组合。

## Shutdown 契约

`0x09` payload 固定为 3B：`stage + reason + detail`。MCU 和 SoC 均拒绝旧的 1B/2B 格式，reason/detail 必须精确匹配活动事务。

- 匹配的 `SOC_CONFIRMED` 是不可撤销点。
- 确认前允许本地取消；确认后 MCU 必须完成既定 PA8/PA15 动作。
- MCU 每 400 ms 重发相同事务，整体 deadline 为 6 s。
- PA11 在 STANDBY/SLEEP 中转 OFF 时，MCU 先以 PA8 唤醒 SoC 再启动退出事务；DEEP_SLEEP 下 SoC 已掉电，不为关机请求重新上电。

## 唤醒源与诊断

- `WAKE_ARM`：每次成功布防一条，记录 state/policy/revision 及布防前 raw/pending。
- `WAKE_DROP`：RUNNING 或策略禁止时按来源限频记录，最多每秒一条。
- `WAKE_FIRE`：仅在实际执行 PA8/PA15 动作时记录，并携带 IRQ count/edge/raw/pending。
- `SOC_WAKE`：仅在 PA8 脉冲结束时记录一条；DEEP_SLEEP 的 PA15 上电不伪装为 PA8 pulse。
- ISR 只采样，不做字符串格式化或串口打印。

SoC resume 后必须获得确认的 wake source：SoC RTC 记为 TIMER；非 RTC 唤醒必须与 MCU `0x07(..., FIRED)` 对齐。来源未确认时允许恢复运行，但低功耗事务应返回失败，不把 `OTHER` 记为成功来源。

## 默认诊断开关

`BSP_CHARGE_DIAG_LOG_ENABLED` 和同类高频 charge diagnostics 默认值均为 `0`，且不得与 `GD32L235_CHARGE_CERT_PROFILE` 联动。需要现场取证时显式开启，完成后恢复关闭。

## 证据索引

- MCU 协议：`workspace://gd32l235/Docs/串口通信协议规范.md`
- MCU 状态机：`workspace://gd32l235/App/wakeup.c`
- MCU 协议定义：`workspace://gd32l235/App/protocol.h`
- MCU shutdown：`workspace://gd32l235/App/protocol_handlers/system_handler.c`、`workspace://gd32l235/App/bsp.c`
- SoC 报文：`workspace://xcrz_sigmastar_demo/modules/app/include/app_uart_packet.h`、`workspace://xcrz_sigmastar_demo/modules/app/src/app_uart/app_uart_packet.c`
- SoC 低功耗：`workspace://xcrz_sigmastar_demo/modules/sensor/main/sensor_entry.cpp`、`workspace://xcrz_sigmastar_demo/modules/sensor/serial/sensor_serial.cpp`
- 设计归档：`projects/gd32l235/archive/design/2026-07-22-soc-mcu-power-transition-owner-tcpka.md`

## 验证状态与风险

- 已通过 MCU `0x09` 固定 3B 定向静态测试，以及 SoC `modules/app_obj_all`、`modules/sensor_obj_all` 最小构建。
- 七份历史文档已迁入 archive 并标明历史边界；不再从源码仓维护重复正文。
- 真实板级 STANDBY/SLEEP/DEEP_SLEEP、RTC、TCPKA、PA8/PA15 波形和 wake-source 对齐仍待 HIL。
- 当前源码仓含未提交改动；本候选不能替代 commit identity、发布 manifest 或硬件验收记录。

## Review

- Owner：`leiwenjun`
- Review after：2026-08-22
- Promotion：none
- 提升门禁：MCU/SoC 提交身份明确，四状态 HIL 矩阵通过，唤醒源与 PA8/PA15 波形证据完成，并由 owner 复核。
