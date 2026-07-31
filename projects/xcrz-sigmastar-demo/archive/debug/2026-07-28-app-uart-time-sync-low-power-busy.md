---
id: pcr02-app-uart-time-sync-low-power-busy-20260728
title: PCR02 app_uart 时间同步与低功耗 ACK 槽竞争
kind: debug-record
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/archive/debug/2026-07-28-app-uart-time-sync-low-power-busy.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: current-codex-session
  from: runtime log plus local source inspection and build validation
  source_sha256: 575c66f9ff4ef8ea7628d0bdc97a638be95dd53e372ed78f5d752543eed4a8c6
  temporary_source_retained: false
review_after: '2026-10-28'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- pcr02
- app-uart
- time-sync
- low-power
- ack-slot
validation_refs:
- projects/xcrz-sigmastar-demo/archive/debug/2026-07-28-app-uart-time-sync-low-power-busy.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/archive/debug/2026-07-28-app-uart-time-sync-low-power-busy.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-07-28'
updated_at: '2026-07-28'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-07-28'
manual_validation_pending: true
summary_zh: 记录 0x1A 时间同步与 0x04 低功耗控制争用单一 ACK inflight 槽导致 VS_ERROR_BUSY 的根因、transaction mutex 修复及设备复测边界。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
---

# PCR02 app_uart 时间同步与低功耗 ACK 槽竞争

## 结论

2026-07-28 的 SOC 低功耗现场日志中，`VSAPPUART_SendSleepControl()` 的 ARM 与紧随其后的 DISARM 均返回 `-65540`。该值精确对应 SoC 本地 `VS_ERROR_BUSY`，不是 MCU NACK 或低功耗状态拒绝。

根因是 `app_uart` 只有一个全局同步 ACK inflight 槽。后台 `0x1A` 时间同步通过 `VSAPPUART_SendCommandSyncTimed()` 占用该槽时，前台 `0x04` 低功耗控制通过 `VSAPPUART_SendCommandSync()` 检测到槽已占用并立即返回 BUSY。日志中辅助状态同步成功，而 ARM、DISARM 在亚毫秒间隔内连续 BUSY，符合时间同步 probe 尚未结束的竞争时序。

心跳通知无需 ACK，不占用 inflight 槽；现场片段也没有 OTA 维护态证据，因此两者不是本次 BUSY 的主因。

## 修复

在 `modules/app/src/app_uart/app_uart.c` 增加 tracked transaction mutex，统一串行化以下三类共享槽调用：

- `VSAPPUART_SendCommandSync()`：同步 ACK；
- `VSAPPUART_SendCommandSyncTimed()`：同步 ACK 加 TX 完成时间戳；
- `VSAPPUART_PostCommandAndWaitTx()`：TX 完成等待。

时间同步仍按单个 probe 获取事务锁，业务控制最多等待当前 probe 的 100 ms 超时窗口，不需要等待完整同步 batch，也不改变 OTA maintenance gate、协议帧或 MCU 固件。

同时增加不变量诊断：若取得 transaction mutex 后 ACK/TX-completion 槽仍处于 busy，输出明确的 slot-leak 日志；maintenance 拒绝 tracked command 时也输出独立原因。

## 验证

- `rtk make modules/app_obj_all -j20`：通过。
- `rtk python3 build/check_motor_uart_timestamp_contract.py`：通过，并新增 transaction mutex 静态契约。
- `rtk python3 build/check_soc_reboot_flow.py`：通过。
- `rtk git -C modules/app diff --check`：通过。
- `rtk git diff --check`：通过。

`build/check_soc_low_power_flow.py` 仍因 Broadcom DHD 电源管理源码缺少三个既有静态契约而失败；失败项不位于本次改动范围，不能作为本修复的通过证据。

## 剩余风险

当前只有源码构建和静态契约证据，尚未完成真实设备复测。设备验证应至少重复 20 次 SLEEP 进入/回滚，确认不再出现 `ret=-65540`，并记录 ARM 等待时延；同时观察是否出现新增的 `slot remained busy after transaction lock` 日志。

该记录是 reviewing debug candidate，不代表 release、OTA image 已重生或设备验证已完成。
