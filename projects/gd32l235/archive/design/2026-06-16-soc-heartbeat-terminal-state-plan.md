---
related:
- projects/gd32l235/current/soc-low-power-contract.md
- projects/gd32l235/archive/session/2026-06-17-soc-heartbeat-reboot-ota-closure-session.md
captured_at: '2026-06-16'
id: gd32l235-soc-heartbeat-terminal-state-plan-20260616
title: GD32L235 与 SOC 心跳状态同步终态方案归档
kind: project-archive
domain: projects/gd32l235
path: projects/gd32l235/archive/design/2026-06-16-soc-heartbeat-terminal-state-plan.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: source-project-design-document
  from: workspace://gd32l235/Docs/SOC心跳状态同步终态方案与落地计划.md
  source_sha256: 61b503b2293374f72e4ec9a2c18ed1572a86c824ef8cfddb47cfc3640bedaa22
review_after: '2026-08-22'
review_status: human-reviewed-accepted
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- gd32l235
- heartbeat
- state-sync
- uart-protocol
validation_refs:
- projects/gd32l235/archive/design/2026-06-16-soc-heartbeat-terminal-state-plan.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/gd32l235/archive/design/2026-06-16-soc-heartbeat-terminal-state-plan.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-07-22'
updated_at: '2026-07-26'
generated_by_ai: true
ai_role: classified
ai_model_or_tool: Codex
ai_generated_at: '2026-07-22'
manual_validation_pending: true
summary_zh: 归档 MCU 与 SOC 采用 4B heartbeat 完整状态、版本查询分离、状态位图与重启原因对齐的终态方案和落地计划。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
---

# SOC 心跳状态同步终态方案与落地计划

## 归档说明

- 本文是 2026-06-16 的计划快照；“终态”仅描述当次方案目标，不表示 Hub `active` 状态。
- 4B heartbeat 的不兼容契约仍应由当前 MCU/SOC 实现和 `workspace://gd32l235/Docs/串口通信协议规范.md` 核验；跨低功耗状态的关系见[当前低功耗协同契约候选](../../current/soc-low-power-contract.md)。
- 文中落地路径、工作区状态和待办均为历史信息，不应直接用于判断当前提交状态。
- Review：owner `leiwenjun`；复审日期 2026-08-22；重点核对 4B ABI、boot guard 和重启/OTA 状态恢复。

## 元信息

- captured_at: 2026-06-16
- topic: gd32l235-soc-heartbeat-state-sync
- source:
  - `gd32l235`
  - `gd32l235_app_boot_v1`
  - `<sigmastar-repo>/modules/app`
  - `<sigmastar-repo>/modules/sensor`
- decision: 采用不兼容终态升级，`UART_MSG_TYPE_HEARTBEAT_NOTIFY/CMD_HEARTBEAT(0x01)` 固定为 4B 完整状态，不再传递版本号。

## 背景

历史 SOC 侧曾存在协议语义不一致：旧 heartbeat 发送接口发送 `1B packet_id`，但解析端按 `3B major/mid/minor` 解析，`SensorSerial::onHeartbeatCallback()` 又把 heartbeat 发布成 MCU APP 版本。MCU 侧 `HeartBeat_Event()` 同样曾发送 `3B` 固件版本号。

终态方案将版本号收敛到 `GET_FW_VERSION(0x02)`，将 `HEARTBEAT(0x01)` 专用于双方心跳、在线检测和最小状态同步。

## 接口契约

`CMD_HEARTBEAT / UART_MSG_TYPE_HEARTBEAT_NOTIFY = 0x01`

| 字段 | 长度 | 说明 |
|---|---:|---|
| `seq` | 1B | 发送端递增序号，溢出回绕 |
| `endpoint_state` | 1B | Bit7..6=`source_role`，Bit5..0=`runtime_state` |
| `status_bitmap` | 1B | 发送端当前最小状态 |
| `reset_or_reboot_reason` | 1B | 最近一次 reset/reboot/硬电源事件原因；允许保持最近一次原因 |

兼容策略：
- 不保留旧格式兼容窗口。
- `len != 4` 为非法 heartbeat。
- `3B` 版本心跳不再被解释为版本；版本读取必须使用 `0x02`。

错误语义：
- heartbeat 本身 `Need ACK=0`，错误不会强制应答。
- 接收端仍应记录 `INVALID_PAYLOAD/OUT_OF_RANGE/STATE` 诊断，便于联调定位。

超时语义：
- 稳定运行期建议 5s 周期。
- 启动/重启窗口建议 SOC 侧 1s 周期，进入 `APP_READY` 后回到 5s。
- 连续 3 个周期未收到为 warning，连续 6 个周期未收到为 offline。
- GD32L235 以最后一次有效 runtime state 选择周期：`APP_READY` 使用 5s，其余状态使用 1s；因此 offline 门限分别为 30s 和 6s。
- 从未收到有效 heartbeat 时直接视为 offline；长度、role 或 runtime state 非法的 heartbeat 不刷新在线时间。
- offline 后清除 SOC boot guard，最后一次 runtime state 仅保留作诊断，不再作为 `APP_READY` 在线证据。

## 软重启与硬重启边界

SOC reboot 软重启：
- SOC APP/Linux 重启，MCU 与 PA15 保持供电。
- SOC heartbeat 上报 `REBOOTING -> BOOTING -> APP_READY`，并在 `REBOOTING/BOOTING` 期间置 `boot_guard_active`。
- 若 SOC reboot 命令执行失败且进程仍存活，SOC 必须恢复上报 `APP_READY`，清除 `shutdown_pending` 与 `boot_guard_active`。
- MCU 在 SOC `boot_guard_active` 期间抑制 WIFI/IMU/TOF 触发的 PA8 唤醒脉冲。

拨动开关硬重启：
- PA11 OFF 触发 `SHUTDOWN_STAGE_NOTIFY(0x09)`。
- SOC 完成业务退出后回 `SOC_CONFIRMED`。
- MCU 等待 app deinit 窗口后拉低 PA15。
- PA11 ON 后，MCU heartbeat 上报 `POWER_KEY_SWITCH_ON`。

## gd32l235 落地计划

1. 更新 `App/protocol.h`：新增 4B heartbeat ABI、runtime state、status bit、reset/reboot reason。
2. 更新 `App/bsp.h`：固化 1s/5s heartbeat 周期与连续 6 周期 offline 门限，并保存 SOC boot guard 状态。
3. 更新 `App/protocol_handlers/system_handler.c`：`CMD_HEARTBEAT` 仅接受 4B 完整状态，有效帧统一交给 BSP 刷新 runtime state、boot guard 和最后接收时间。
4. 更新 `App/bsp.c`：`HeartBeat_Event()` 发送 4B MCU 状态；维护 SOC heartbeat valid/last tick，超时后判 offline 并清 boot guard；PA11 硬关机/硬上电写入 reason。
5. 更新 `workspace://gd32l235/Docs/串口通信协议规范.md`：固化终态接口。

## SOC 侧同步计划

SOC 侧不属于本仓写入范围，需在 `<sigmastar-repo>` 中同步：

1. `VSAPPUART_MsgHeartbeatNotify_t` 改为 `seq/endpoint_state/status_bitmap/reset_or_reboot_reason`。
2. `VSAPPUART_HeartbeatNotify()` 只接受 `len == 4`。
3. `VSAPPUART_SendHeartbeatNotify()` 发送 4B SOC 状态。
4. `SensorSerial::onHeartbeatCallback()` 更新 link state，不再调用版本发布。
5. `SensorSerial::onSoftResetCallback()` 区分 SOC soft reboot、factory reset、reset key 事件。

## 验证用例

1. MCU 周期 heartbeat payload 为 4B，字段为 `seq + MCU|runtime_state + status_bitmap + reason`。
2. MCU 接收 `len != 4` heartbeat 时返回 invalid payload 诊断，不更新 SOC peer 状态。
3. SOC heartbeat 设置 `boot_guard_active` 时，MCU 清除 WIFI/IMU/TOF wake flags，不产生 PA8 唤醒脉冲；SOC 在 `BOOTING/REBOOTING` 期间必须置该位。
4. PA11 OFF 进入 shutdown handshake 并通过 `0x09` 表达流程阶段；PA11 ON 后 heartbeat reason 上报 `POWER_KEY_SWITCH_ON`。
5. `GET_FW_VERSION(0x02)` 仍返回 `major/minor/patch`，版本查询与 heartbeat 解耦。
6. 从未收到 heartbeat、非 `APP_READY` 超过 6s、`APP_READY` 超过 30s 时均判 offline；新的有效 heartbeat 可恢复 online。

## 风险与回退

- 这是不兼容协议变更，SOC 与 MCU 必须同批升级；任一侧仍使用 1B 或 3B heartbeat 都会被另一侧拒绝。
- 若联调阶段必须临时兼容旧格式，应另开临时分支，不进入主线终态实现。
- PA8 抑制依赖 SOC 在早期启动窗口正确发送带 `boot_guard_active` 的 heartbeat；SOC 早期进程尚未启动前，仍需靠硬件默认态和 MCU 启动保护兜底。

## 归档门禁

- Sanitization: 未包含密钥、凭证、完整日志或外部私有内容。
- Verification: 以本次代码实现和构建/检查结果为准。
- Memory Candidate: no。
