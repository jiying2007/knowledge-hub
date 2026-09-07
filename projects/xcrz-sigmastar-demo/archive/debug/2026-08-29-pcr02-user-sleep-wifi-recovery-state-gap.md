---
related: []
human_reviewed_by: null
human_reviewed_at: null
review_basis: null
incident_id: null
severity: null
affected_version: null
id: pcr02-user-sleep-wifi-recovery-state-gap-20260829
title: PCR02 用户主动休眠下 Wi-Fi 异常恢复与状态机互斥候选
kind: debug-record
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/archive/debug/2026-08-29-pcr02-user-sleep-wifi-recovery-state-gap.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: manual
  from: 2026-08-29 脱敏日志摘要、本地源码审查与最小 ARM 对象构建；未归档原始日志、设备网络信息或现场标识。
  source_sha256: null
review_after: '2026-11-29'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; reviewing debug candidate only, no owner decision, release claim or active promotion
tags:
- pcr02
- low-power
- tcpka
- wifi
- standby
- state-machine
validation_refs:
- projects/xcrz-sigmastar-demo/archive/debug/2026-08-29-pcr02-user-sleep-wifi-recovery-state-gap.md
- rtk make modules/sensor_obj_all NC=1
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: source-and-log-correlation-hil-pending
evidence_refs:
- modules/sensor/wifi/sensor_wifi_service.cpp
- rtk make modules/sensor_obj_all NC=1
created_at: '2026-08-29'
updated_at: '2026-08-29'
generated_by_ai: true
ai_role: summarized
ai_model_or_tool: Codex
ai_generated_at: '2026-08-29'
manual_validation_pending: true
summary_zh: 记录用户主动 SOC 休眠期间 Wi-Fi/TCPKA 异常处理、内部重睡约束、Wi-Fi 恢复阻塞风险和业务 Standby 互斥缺口；尚未完成实机 HIL。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
---

# PCR02 用户主动休眠下 Wi-Fi 异常恢复与状态机互斥候选

## 适用边界

- 项目：PCR02 SigmaStar SSC305。
- 场景：用户显式请求 SOC SLEEP，随后发生 TCP keepalive 超时或 Wi-Fi beacon 丢失。
- 不包含：原始日志、设备地址、网络名称、服务端地址、设备标识、二进制或现场资料。

## 已确认的现象链

1. 用户休眠路径会关闭 IoT 网络模块，随后配置 TCP keepalive 并请求 SOC SLEEP。
2. TCP keepalive timeout 和 Wi-Fi beacon 丢失会产生硬件唤醒边沿；它们不是用户唤醒，应仅作为内部恢复事件处理。
3. 现有低功耗逻辑会压制上述异常唤醒，尝试恢复 Wi-Fi、重新 arm TCP keepalive、重新 arm MCU，然后再次 suspend。
4. 现场证据显示：一次 timeout 后已完成 re-arm；一次 beacon 丢失后仅见 Wi-Fi 恢复开始，缺少后续 re-arm 和 MCU arm 成功记录。此时用户态后台仍可产生部分日志，而远程网络已不可用。
5. 同一时段业务 Standby 状态机可独立进入熄屏、降帧、关闭低码流和 TOF，说明它与用户 SOC Sleep 没有完成互斥。

## 根因假设与代码证据

`SensorWifiService::recoverLinkForLowPower()` 原先在低功耗恢复轮询中调用同步 Wi-Fi 状态查询。该查询需要取得 Wi-Fi API 互斥锁；若 vendor Wi-Fi worker 在 API 调用中停滞，恢复线程可能无法遵守其预期的受限时间，从而阻止低功耗事务走到重新 arm / 重新 suspend。

本地候选修复位于 `modules/sensor/wifi/sensor_wifi_service.cpp`：

- 低功耗恢复不再轮询 vendor 状态 API；改用 Wi-Fi 回调维护的原子链路状态与链路事件序号。
- 不在低功耗恢复路径同步初始化 vendor Wi-Fi API。
- 超时清理使用非阻塞锁尝试，并记录是否实际完成底层 reconnect 取消。

该修复旨在保证异常 Wi-Fi 事件不会无限占用低功耗恢复路径；它不改变 Deep Sleep 的 handoff、TCP keepalive runtime offload 或 MCU 物理断电语义。

## 目标状态机

```text
USER_SLEEP_LOCKED
  ├─ 有效 Netpattern 或明确物理/用户唤醒 → NORMAL_RESUME
  └─ TCPKA timeout / Loss of beacon
       → INTERNAL_WIFI_RECOVERY
          ├─ Wi-Fi 与 TCPKA 恢复 → MCU re-arm → CommitSuspend
          └─ 恢复失败或超时 → 内部 RTC retry → CommitSuspend
```

异常 Wi-Fi 事件不得恢复 MQTT、RTSA、显示或正常 task 状态。用户 SOC Sleep 锁定期间，业务 `Idle -> Standby` 也应被互斥门禁阻止，避免双状态机重复操作显示、视频和传感器。

## 验证与风险

- 已验证：`rtk make modules/sensor_obj_all NC=1` 通过，完成目标 ARM 对象构建。
- 已验证：sensor 子仓 `git diff --check` 通过。
- 未验证：目标设备 HIL、重复 beacon 丢失、TCPKA timeout、Deep Sleep 回归、task 层 Standby 互斥修复。
- 未闭环：task 层源码不在本次 sensor 子仓范围，尚未实现 `user_sleep_locked` / `low_power_transition_active` 的 Standby 入口门禁。
- 回滚：恢复 `modules/sensor/wifi/sensor_wifi_service.cpp` 中本候选的低功耗 Wi-Fi 恢复轮询改动；不涉及设备、image 或 OTA 回滚。

## 结论状态

本条目是 `reviewing` debug-record candidate，不代表 owner 决策、发布批准、量产结论或实机验证闭环。后续必须以匹配制品执行单次 smoke、短循环和 Deep Sleep 回归后再决定是否提升为 validation 或 decision。
