---
id: gd32l235-power-off-hold-late-on-restart-gap-20260804
title: GD32L235 APP_EXITED(OFF) 后拨回 ON 的硬恢复缺口
kind: debug-record
domain: projects/gd32l235
path: projects/gd32l235/archive/debug/2026-08-04-power-off-hold-late-on-restart-gap.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: session-derived-debug-summary
  from: user board observation + workspace://gd32l235 + workspace://xcrz-sigmastar-demo/daemon source audit
  source_sha256: 798fbe011810244a6bdeb179f7fa190358043fcb03dffcfa9a7c9831d3934907
  temporary_source_retained: false
review_after: '2026-09-04'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- gd32l235
- power-key
- app-exited
- pa15
- pa8
- uart-handoff
validation_refs:
- projects/gd32l235/archive/debug/2026-08-04-power-off-hold-late-on-restart-gap.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/gd32l235/archive/debug/2026-08-04-power-off-hold-late-on-restart-gap.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-08-04'
updated_at: '2026-08-04'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-08-04'
manual_validation_pending: true
summary_zh: 定位 APP_EXITED(OFF) 已使 MCU 拉低 PA15 后再拨回 ON 的缺口：daemon 可能已失去运行条件，而 MCU 无 FAST 证据仍直接等待 APP_READY，导致硬恢复延迟或无法及时重启。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
---

# GD32L235 APP_EXITED(OFF) 后拨回 ON 的硬恢复缺口

## 现象与范围

- Captured at: 2026-08-04（Asia/Hong_Kong）。
- Source: 用户板级现象、`workspace://gd32l235` MCU 状态机、`workspace://xcrz-sigmastar-demo/daemon` UART handoff 实现与契约测试。
- Repro sequence: 拨动开关由 ON 到 OFF；应用完成安全退出；MCU/daemon 已按 OFF 目标完成 `APP_EXITED(flags=0)`；随后用户拨回 ON。现场表现为 SOC 似乎掉电但未及时重启。
- Sanitization: 不保存原始串口日志、二进制、设备标识、凭据或私有端点。

## 软件证据链

1. daemon 收到 OFF `TARGET_STATE` 后发送 `APP_EXITED(flags=0)`，并继续在最多 5 秒窗口内监听后续目标；因此“daemon 因 OFF 目标主动退出监听”已被代码证伪。
2. MCU 收到 `APP_EXITED(flags=0)` 且开关仍稳定 OFF 时，`Bsp_SocExit_OnAppExited()` 立即进入 `SOC_EXIT_POWER_OFF_HOLD`；`Soc_Exit_Manager_EnterPowerOffHold()` 立即拉低 PA15。
3. PA11 仍为 OFF 时，PA15 拉低可能让 daemon 与整个 SOC 一起失去运行条件。此后即使用户拨回 ON，daemon 也可能无法再接收新的 ON `TARGET_STATE`，更不可能发送带 FAST 标志的 `APP_EXITED`。
4. MCU 在 `SOC_EXIT_POWER_OFF_HOLD` 中检测到稳定 ON 后，当前实现调用 `Soc_Exit_Manager_EnterFastAppReadyWait()`，直接等待 `APP_READY`，没有验证本轮收到过 FAST 标志，也没有先执行 PA8 8010 ms 硬恢复。
5. 因此在 daemon 已随 SOC 掉电的分支，MCU 会进入一个没有实际启动者的 30 秒 `BOOT_WAIT_READY`；只有超时后才尝试 PA8 长脉冲回退，造成“掉电但不重启”或显著延迟。

## 测试缺口

现有模型覆盖了“OFF APP_EXITED 后 daemon 仍活着，随后收到 ON 并返回 FAST”的路径，但没有覆盖“OFF APP_EXITED 已切断 SOC，后续没有 FAST 回应”的真实时序。模型还把 `POWER_OFF_HOLD + ON + 500 ms` 直接建模为 `BOOT_WAIT_READY`，固化了错误假设。

## 建议修复边界

- 快速 `BOOT_WAIT_READY` 只能由当前 generation、显式携带 `FAST_RESTART_STARTED` 的 `APP_EXITED` 进入。
- `POWER_OFF_HOLD` 检测到 ON 但没有 FAST 证据时，应恢复 PA15，并进入既有 PA8 8010 ms 硬恢复路径，而不是直接等待 `APP_READY`。
- stable ON 后不应继续在主循环中无条件重复拉低 PA15。
- 若要扩大免 8 秒体验窗口，可在 APP_EXITED(OFF) 后增加短暂、明确的“最终 OFF 提交宽限期”，宽限期内保持 daemon 供电并允许 ON 覆盖；一旦真正切断 SOC，后续 ON 必须走硬恢复。
- 新增回归用例：OFF -> SOC_CONFIRMED -> APP_EXITED(no FAST) -> PA15 OFF -> ON -> 无后续 APP_EXITED，必须进入 `RESTART_SLEEP_PULSE`，不能进入裸 `BOOT_WAIT_READY`。

## 验证状态与风险

- Software root cause: confirmed by source control flow。
- Board-level rail/waveform: pending；仍需联合观测 PA11、PA15、PA8、daemon 日志和新的 APP_READY。
- Negative finding: daemon 的 OFF 分支保持监听，不是主动提前结束；失败条件是 MCU 在监听窗口内切断其运行载体，以及后续无 FAST 证据仍进入快速等待。
- Fix status: needs-fix；本记录只做诊断，未修改源码。
- Memory candidate: no。
