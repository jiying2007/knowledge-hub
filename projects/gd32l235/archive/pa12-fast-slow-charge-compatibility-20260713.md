---
id: gd32l235-pa12-fast-slow-charge-compatibility-20260713
title: GD32L235 PA12 快慢充控制与硬件兼容性归档
kind: project-archive
domain: projects/gd32l235
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
review_after: '2026-08-13'
review_status: manual-entry-pending-review
promotion: none
tags:
- gd32l235
- charge
- pa12
- hardware-compatibility
- test-readiness
generated_by_ai: true
ai_role: summarized
ai_model_or_tool: Codex
ai_generated_at: '2026-07-13'
manual_validation_pending: true
summary_zh: GD32L235 PA12 快慢充控制实现、提测前检查、充电温度保护冲突检查，以及试产 PA12 悬空与量产硬件支持的兼容性结论。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
promotion_decision: none; capture does not authorize active promotion or owner decision
---

# GD32L235 PA12 快慢充控制与硬件兼容性归档

## 摘要

本次在 GD32L235 固件中新增主板 MCU 控制的快慢充切换逻辑：设备进入充电时默认快充，温度达到 45°C 时切换慢充，温度降低到 38°C 时恢复快充。快慢充控制脚为 PA12，输出 1 表示快充，输出 0 表示慢充；硬件默认慢充。温度阈值已做成可配置参数，便于后续测试小幅调整。

本归档只记录本次软件实现、提测前检查、充电温度保护冲突检查，以及试产/量产硬件兼容性结论。它不是 owner 已签收的量产决策，也不替代真实硬件验证。

## 实现边界

- PA12 作为快慢充控制输出，软件初始化时先置慢充。
- 默认阈值为慢充进入 45°C、快充恢复 38°C，形成温度回差，避免临界温度抖动。
- 新增阈值配置接口，协议命令 `CMD_CHARGE_FAST_TEMP_CONFIG = 0x38`，payload 为 `fast_recover(int8)`、`slow_enter(int8)`。
- 充电边沿更新使用最近一次电池温度，不再用固定 38°C 触发，避免高温插入充电时短暂进入快充。
- `CMD_CHARGE_CURRENT_LEVEL = 0x36` 在充电中被拒绝，避免上位机/SoC 手动电流档位命令绕过 MCU 温度自动控制。

## 与既有逻辑关系

- PA12 快慢充控制与 PB10 充电使能/温度保护职责分离。
- PB10 充电温度保护仍负责是否允许充电；PA12 只负责充电电流档位。
- 温度保护触发时，PB10 可关闭充电；PA12 保持慢充/快充状态本身不应绕过温度保护。
- 已检查 WiFi 相关 GPIO：WiFi SDIO_EN 使用 PB12，Wakeup WiFi 使用 PC12，未发现 PA12 复用冲突。

## 试产与量产硬件兼容性

- 用户确认试产硬件 PA12 是悬空。
- 在试产硬件上，固件把 PA12 配置为推挽输出并拉高/拉低，因外部悬空，理论上不会影响其他外设，也不会产生快慢充硬件动作。
- 试产机器可以验证软件状态机、温度回差、协议配置和日志路径，但不能验证真实充电电流是否随 PA12 切换。
- 量产硬件支持 PA12 快慢充控制，真实快慢充电流切换必须在量产硬件或等效硬件上验证。
- 若存在 PA12 并非悬空的试产改板、飞线板或特殊样机，需要单独按原理图/实测确认，不能套用“悬空兼容”结论。

## 已完成验证

- `rtk git diff --check`：通过。
- `rtk bash scripts/codex-check.sh --full`：普通 profile 通过。
- 普通 profile App flash 使用量：46848B / 50KB，约 91.50%。
- charge-cert profile 已完成 configure、build、package，但 `fwtool check --scope all` 未通过 flash headroom 门禁。
- charge-cert profile App flash 使用量：47604B / 50KB，约 92.98%；剩余 headroom 3596B，低于 4096B guard。

## 提测结论

- 普通 profile 可进入提测，测试重点包括：进入充电默认快充、45°C 切慢充、38°C 恢复快充、配置阈值生效、充电中 `0x36` 被拒绝、温度保护仍能关闭充电。
- 试产硬件只能验证软件行为，不能作为 PA12 实际电流切换验收依据。
- 若提测范围包含 charge-cert profile，需要先处理 flash headroom 不足，或明确本轮提测不包含 charge-cert profile。

## 后续建议

- 量产硬件上用示波器或逻辑分析仪确认 PA12 在充电、45°C、38°C、退出充电时的电平变化。
- 同步测量实际充电电流，确认 PA12=1 对应快充、PA12=0 对应慢充。
- 做一次温度保护交叉测试：高温保护关闭充电时，确认 PB10 行为优先且 PA12 不会造成充电绕过。
- 若未来同一固件需要覆盖更多硬件版本，可考虑增加硬件能力配置或板型开关，用于显式禁用 PA12 控制。

## 脱敏说明

本归档未包含密钥、凭证、原始长日志、NAS 路径细节或二进制制品；只记录可复用的工程结论、验证命令摘要和剩余风险。
