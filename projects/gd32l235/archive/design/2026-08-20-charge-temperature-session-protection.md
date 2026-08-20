---
id: gd32l235-charge-temperature-session-protection-20260820
title: GD32L235 充电温度保护会话化与 PB10 计时归档
kind: project-archive
domain: projects/gd32l235
path: projects/gd32l235/archive/design/2026-08-20-charge-temperature-session-protection.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: codex-session-summary
  from: local Codex session on 2026-08-20 for GD32L235 charge temperature session protection
  source_sha256: 9f69cca764330b042136cf7db3c3d54578aad8f35ab6f4838b6df692498066cf
  temporary_source_retained: false
review_after: '2026-09-20'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- gd32l235
- charge
- pb10
- temperature-protection
- session-boundary
validation_refs:
- projects/gd32l235/archive/design/2026-08-20-charge-temperature-session-protection.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/gd32l235/archive/design/2026-08-20-charge-temperature-session-protection.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-08-20'
updated_at: '2026-08-20'
generated_by_ai: true
ai_role: summarized
ai_model_or_tool: Codex
ai_generated_at: '2026-08-20'
manual_validation_pending: true
summary_zh: GD32L235 充电温度保护仅约束当前上桩会话，并按 PB10 实际允许充电时间累计 49°C 高温慢充 5 分钟保护。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
---

# GD32L235 充电温度保护会话化与 PB10 计时归档

## 摘要

GD32L235 的充电温度保护按“当前上桩充电会话”生效：离桩时重置本次会话的温度保护状态、硬锁和高温累计时间；重新上桩后按当前温度重新判断，不沿用上一次会话的保护状态。

针对设备上桩后充电状态为 1、但 PB10 未恢复使能而持续耗电的问题，最终实现将 49°C 至 51°C 区间的慢充超时计时依据调整为“PB10 实际允许充电的时间”，不依赖电量计上报的充电电流。温度不低于 49°C 且 PB10 有效输出开启累计达到 5 分钟后，立即进入温度保护并关闭充电。

## 背景与问题

- 现场现象是机器与基站充电极片接触，基站灯保持蓝色，系统充电状态为 1，但充电电流长期为 0，电量持续下降。
- 日志与调试输出显示，离桩后再次上桩时充电使能可能仍受上一充电会话的高温硬锁或满充脉冲状态影响。
- 充电状态只能说明设备检测到上桩，不能等价于 PB10 已实际允许充电；电量计充电电流也可能为 0，不能作为保护累计时间的唯一依据。

## 最终行为

- 充电温度保护仅约束当前上桩充电会话。
- 离桩后重置本会话温度保护状态、高温硬锁、高温累计预算及相关脉冲门控状态；再次上桩重新判断。
- 电池温度处于 49°C 至 51°C 的高温慢充区间时，仅在 PB10 的开关门、上层门、温度门和脉冲门都允许、即 PB10 有效充电输出实际开启期间累计时间。
- 上述有效开启时间累计达到 300 秒后进入停止充电状态，关闭温度允许门并取消满充脉冲，避免 51°C 附近长时间持续充电。
- PB10 被其他门控关闭期间暂停累计；电量计上报 0 mA 不会暂停累计。
- 达到更高的即时保护阈值时，仍按原有即时温度保护路径停止充电，不等待 5 分钟。
- PA12 快慢充档位控制与 PB10 充电允许控制保持职责分离，PA12 状态不能绕过 PB10 温度保护。

## 实现与提交

- 源仓：GD32L235 固件仓。
- 基线版本：v1.1.42，基线提交 `5e7376c`。
- 落地提交：`7e25e4f1fe91c908e48599c8e21717c923e31daa`。
- 提交说明：`fix(charge): 按PB10开启时间限制高温慢充`。
- 主要改动范围：`App/charge.c`、`App/charge.h`、充电说明文档和温度会话安全契约测试。

## 验证证据

- 温度会话安全契约测试通过。
- 充电脉冲门控契约测试通过。
- 电量计恢复契约测试通过。
- `scripts/codex-check.sh --full` 通过。
- 生产构建、合并、打包和包检查通过；生产 App 使用 48116 B / 50 KB。
- 调试构建通过；调试 App 使用 51296 B / 100 KB。
- `git diff --check` 通过。
- 提交已推送至 `origin/master`，远端 `master` 指向 `7e25e4f1fe91c908e48599c8e21717c923e31daa`。

## 风险与后续验证

- 当前证据覆盖静态契约、自动检查和构建打包，尚未记录真实硬件上的 49°C 持续 5 分钟计时测试。
- 建议在量产或等效硬件上验证：49°C 至 51°C 区间 PB10 连续开启 300 秒后关闭、PB10 中途关闭时计时暂停、离桩后累计清零、重新上桩恢复充电判断，以及即时高温阈值仍优先生效。
- 本归档是 `reviewing` 候选，不替代源码、发布清单或产品/硬件 owner 签收。

## 脱敏说明

归档未包含设备标识、私有地址、原始长日志、凭据、固件二进制或运行时缓存，只保留可复用的工程结论、提交标识和验证摘要。
