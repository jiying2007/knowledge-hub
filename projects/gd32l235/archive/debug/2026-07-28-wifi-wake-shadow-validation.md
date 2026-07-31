---
id: gd32l235-wifi-wake-shadow-validation-20260728
title: GD32L235 WiFi wake shadow 诊断与验证
kind: debug-record
domain: projects/gd32l235
path: projects/gd32l235/archive/debug/2026-07-28-wifi-wake-shadow-validation.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: current-codex-session
  from: 2026-07-28 Codex session, local Git/source inspection, sanitized serial evidence and build artifact inspection
  source_sha256: b1208109ea68c684ad21f4c04a5dc7a543913985f870dc2d940f52c3835787c3
  temporary_source_retained: false
review_after: '2026-10-28'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- gd32l235
- wifi-wake
- shadow
- sleep
- deep-sleep
- diagnostics
validation_refs:
- projects/gd32l235/archive/debug/2026-07-28-wifi-wake-shadow-validation.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/gd32l235/archive/debug/2026-07-28-wifi-wake-shadow-validation.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-07-28'
updated_at: '2026-07-28'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-07-28'
manual_validation_pending: true
summary_zh: 记录 SLEEP/DEEP_SLEEP WiFi wake shadow 的默认关闭设计、PA8/PA15 物理输出隔离、DISARM 清理和上游 IRQ 根因边界。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
---

# GD32L235 WiFi wake shadow 诊断与验证

## 现象

SoC 已能进入 SLEEP/DEEP_SLEEP 后，主板 MCU 仍周期性收到 WiFi wake edge，并立即通过 SoC 物理唤醒链触发完整启动。典型时序为：

```text
WAKE_ARM ... state=2 policy=0x01 ... guard_ms=5000
WAKE_FIRE ... src=wifi
SOC_WAKE ... duration=9
```

重复事件间隔为数十秒量级，说明需先区分“WiFi 中断确实发生”和“MCU 输出 PA8/PA15 导致 SoC 被唤醒”两个问题。

## 影响范围

- 工程：GD32L235 主板 MCU。
- 分支快照：`master`，基线 `6fd343db...`，工作树为 mixed dirty。
- 场景：SoC SLEEP 与 DEEP_SLEEP，WiFi wake policy 打开且已越过 entry guard。
- 不覆盖 STANDBY 的正式唤醒策略，也不证明 WiFi IRQ 对应的具体 packet/event。

## 设计

新增独立、默认关闭的 `WIFI_WAKE_SHADOW_ENABLED` 诊断能力：

- 只在 SoC 状态为 SLEEP 或 DEEP_SLEEP 时生效；
- 仍要求 WiFi wake policy 允许并越过既有 entry guard；
- 保留 EXTI12 与中断计数，输出 `WAKE_SHADOW` 诊断；
- 不 latch wake，不上报 `FIRED`；
- SLEEP 不驱动 PA8；
- DEEP_SLEEP 不重新拉起 PA15；
- 不屏蔽后续 WiFi edge，便于统计频率；
- shadow 必须与 wakeup diagnostic log 同时开启，否则构建失败。

该模式刻意隔离“输入观测”与“物理输出”，不能替代产品正式唤醒策略。

同时补充低功耗 DISARM：

- sleep control mode `0x00` 调用 `Wakeup_Disarm()`；
- 清除 applied state/policy、in-progress、guard 与 deep power phase；
- mask 相关 EXTI；
- 若 DEEP_SLEEP 电源切换正在进行，恢复 PA15 到安全状态；
- 输出简短 `WAKE_DISARM` 诊断。

## 调试过程

1. 初始多轮 `WAKE_FIRE src=wifi` 与 `SOC_WAKE` 证明 MCU 物理唤醒链生效，但 SoC 重启后难以连续观察异常包。
2. 首版 shadow 目标是“不输出 PA8”，现场仍需同时确认 DEEP_SLEEP 下不能重新拉 PA15。
3. 收敛为 SLEEP/DEEP_SLEEP 共用 shadow 分支，并在分支内禁止 PA8、PA15、FIRED、wake latch 和 EXTI mask。
4. ISR 仅做轻量 pending/计数，GPIO、策略、时间和格式化日志移到非 ISR 路径，避免诊断本身放大时序。
5. 加入构建开关依赖、静态契约和 DISARM 清理，确保诊断模式默认不进入产品固件。

## 证据

现场 shadow 日志：

```text
WAKE_ARM ... state=2 policy=0x01 ... guard_ms=5000
WAKE_SHADOW ... st=2 n=1 irq=1 w=1 p8=0 p15=1
```

该记录证明：

- WiFi IRQ 在 guard 后真实到达；
- shadow 分支接受并计数；
- PA8 未输出；
- PA15 保持当时状态，未由 shadow 重新拉起；
- SoC 物理 wake 未由这次 MCU shadow 事件发出。

源码静态契约覆盖：

- shadow 独立 default-OFF；
- diagnostics 依赖；
- SLEEP/DEEP_SLEEP 状态范围；
- guard 之后、wake commit 之前执行；
- shadow 分支禁止 PA8/PA15/FIRED/latch/mask；
- DISARM mode 0x00 和安全清理。

归档前执行 `rtk env PYTHONDONTWRITEBYTECODE=1 python3 Tools/tests/check_wakeup_diagnostics.py` 通过；相关文件 `git diff --check` 通过。

## 假设与排除

| 假设 | 验证 | 结果 |
| --- | --- | --- |
| SoC 自身 RTC 导致所有重复启动 | shadow 保留 WiFi IRQ 但阻断 MCU 输出后可继续观察，不必立即唤醒 SoC | 可分离，尚需长时间对照 |
| 只阻断 PA8 即覆盖所有低功耗状态 | DEEP_SLEEP 的 PA15 电源路径仍可能触发启动 | 排除；shadow 同时禁止 PA15 reassert |
| shadow 应吞掉 EXTI | 需求是观察事件频率和模式 | 排除；保留 EXTI 和计数 |
| `WAKE_SHADOW` 已证明异常包根因 | 日志只证明 MCU 收到 WiFi edge | 排除；packet/firmware event 尚未关联 |

## 根因状态

已确认 SoC 的重复物理唤醒由 MCU 在 WiFi wake edge 后执行 PA8/PA15 输出链触发；shadow 可以隔离这条输出链。

尚未确认 WiFi edge 的上游根因。候选包括预期 TCP keepalive timeout/数据、firmware event、链路变化或异常中断；必须与 DHD wakeind、TCPKA 状态和服务端流量时间线关联后再定论。

## 风险

- shadow 默认关闭是安全边界；若误用于产品 release，会吞掉期望的 WiFi 唤醒。
- mixed dirty 工作树还包含 motor timestamp、版本、充电/温度等其他改动，不能把整个 diff 当作 shadow patch。
- 当前只有静态测试和有限现场日志，没有 1000 次循环或 soak。
- shadow 不解决上游 WiFi IRQ，只提供无干扰观测窗口。

## 后续动作

1. 在 shadow 固件下连续记录至少 30 分钟，统计 edge 间隔、计数与 TCPKA 周期关系。
2. 将 MCU `WAKE_SHADOW` 时间与 SoC DHD firmware event/wakeind、AP 日志和服务端数据时间对齐。
3. 找到上游原因后，明确哪些 WiFi event 应输出 PA8/PA15，哪些应丢弃或仅统计。
4. 正式 release 前确认 `GD32L235_WIFI_WAKE_SHADOW_ENABLED=OFF`，并保留静态门禁。
5. 提交时独立拆出 shadow/DISARM 与 motor timestamp 等改动。

## 状态

本记录为 reviewing debug candidate。它保存诊断设计、已验证输出隔离和剩余根因边界，不代表 shadow 应进入产品默认配置。
