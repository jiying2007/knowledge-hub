---
related:
- projects/gd32l235/current/soc-low-power-contract.md
- projects/gd32l235/archive/design/2026-06-16-soc-heartbeat-terminal-state-plan.md
captured_at: '2026-06-17T15:06:46+08:00'
id: gd32l235-soc-heartbeat-reboot-ota-closure-session-20260617
title: GD32L235 与 SOC 心跳、重启和 OTA 闭环会话归档
kind: project-archive
domain: projects/gd32l235
path: projects/gd32l235/archive/session/2026-06-17-soc-heartbeat-reboot-ota-closure-session.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: source-project-session-summary
  from: workspace://gd32l235/Docs/会话归档-GD32L235-SOC心跳重启OTA闭环-20260617.md
  source_sha256: 2eb82cf9cf8b933002a687bbcaf094a0e75efeb67593f7ba4b3ac5cabccf1ad2
review_after: '2026-08-22'
review_status: human-reviewed-accepted
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- gd32l235
- heartbeat
- reboot
- ota
- session
validation_refs:
- projects/gd32l235/archive/session/2026-06-17-soc-heartbeat-reboot-ota-closure-session.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/gd32l235/archive/session/2026-06-17-soc-heartbeat-reboot-ota-closure-session.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-07-22'
updated_at: '2026-07-26'
generated_by_ai: true
ai_role: classified
ai_model_or_tool: Codex
ai_generated_at: '2026-07-22'
manual_validation_pending: true
summary_zh: 保存 MCU、SOC 应用及串口桥接之间心跳状态同步、reboot、OTA handoff 与 PA8 boot guard 闭环的会话级决策和验证证据。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
---

# 会话归档：GD32L235 与 SOC 心跳、重启、OTA 闭环

## 归档说明

- 本文是 2026-06-17 会话快照，记录当时的决策、验证和工作区状态；不作为当前分支状态证明。
- 4B heartbeat、boot guard 与低功耗状态的当前边界应由源码、`workspace://gd32l235/Docs/串口通信协议规范.md` 和[当前低功耗协同契约候选](../../current/soc-low-power-contract.md)共同核验。
- 文中的构建成功、dirty/untracked 状态和提交建议只对捕获时点有效；板级/HIL 仍未完成。
- Review：owner `leiwenjun`；复审日期 2026-08-22；重点检查 OTA handoff、reboot 失败恢复和启动前保护窗口。

## 元信息

- Captured at: 2026-06-17 15:06:46 +0800
- Scope: 当前会话，覆盖 `gd32l235` MCU、`xcrz_sigmastar_demo` SOC 应用、`modules/sensor`、`modules/app`、`app_main`、`app_ota` 的心跳状态同步、SOC reboot、OTA reboot handoff 与 PA8 boot guard 闭环。
- Source: 当前会话中的方案设计、代码落地、协议审计、残留扫描、构建验证和最终闭环复核。
- Sanitization: 已去除长工具输出和无关工作区噪声；仅保留可复用决策、文件路径、验证命令、风险边界和候选记忆。

## 本次完成

### 协议终态

- `UART_MSG_TYPE_HEARTBEAT_NOTIFY / CMD_HEARTBEAT(0x01)` 按终态不兼容版本推进，固定为 4B 完整状态：
  - `seq`
  - `endpoint_state`
  - `status_bitmap`
  - `reset_or_reboot_reason`
- 心跳不再传递版本号；固件版本仍通过 `0x02(获取固件版本)` 查询。
- `endpoint_state` 使用 Bit7..6 表示 `source_role`，Bit5..0 表示 `runtime_state`。
- SOC 与 MCU 两侧 reason 枚举对齐，明确区分：
  - SOC 主动软重启：`SOC_REBOOT_REQUEST / WATCHDOG / UPGRADE / FAULT / USER`
  - 拨动开关/硬件电源类事件：`POWER_KEY_SWITCH_OFF / POWER_KEY_SWITCH_ON` 等

### SOC `sensor` 生命周期

- `SensorSerial::start()` 启动后先发送 `BOOTING + BOOT_GUARD_ACTIVE`，随后发送 `APP_READY` 清除 guard。
- 周期心跳改为 4B `sendHeartbeatNotify()`，用于双方心跳和状态同步。
- 上层应用通过 ZMQ 请求 SOC reboot 时：
  - `sensor` 先发送 `REBOOTING + SHUTDOWN_PENDING + BOOT_GUARD_ACTIVE`
  - 执行业务安全退出
  - 再次通知 MCU
  - `sync()` 后执行 `reboot / busybox reboot`
  - 若 reboot 命令失败，恢复 `APP_READY` 并清除 guard，避免 MCU 永久处于 boot guard。

### SOC `app_ota` 生命周期

- OTA 非脚本接管路径在请求系统 reboot 前通知 MCU：
  - `REBOOTING + SHUTDOWN_PENDING + BOOT_GUARD_ACTIVE`
  - reason 使用 `SOC_REBOOT_UPGRADE`
- 如果 `reboot / busybox reboot` 失败，`app_ota` 会重新初始化 UART，并发送 `APP_READY` 恢复 MCU 状态。
- SOC 脚本接管路径在 fork/exec 前发送 `REBOOTING + BOOT_GUARD_ACTIVE`。
- fork 失败、wait 失败、脚本异常退出、脚本非 0 返回时，`app_ota` 恢复 `APP_READY`。
- 用户明确约束：`ota_upgrade.sh / ota_end.sh` 不能修改，脚本成功接管默认成功。因此脚本返回 0 后按外部 reboot handoff 成功处理，不再从 app_ota 内追责脚本内部 `reboot_system || true`。

### MCU 接收与 PA8 抑制

- MCU `CMD_HEARTBEAT` 只接受 4B payload，并校验 `source_role == SOC`。
- MCU 根据 SOC heartbeat 的 `BOOT_GUARD_ACTIVE` bit 维护 `RunParam.Soc_Boot_Guard_Flag`。
- `Wakeup_Event()` 在 `Soc_Boot_Guard_Flag != 0` 时清除 WIFI/IMU/TOF wake flags，不产生 PA8 `SOC_Wakeup()` 脉冲。
- `Wakeup_Soc_Flag` 分支不直接产生 PA8 脉冲，主要服务 SOC 显式唤醒/关机状态处理；不能把它等同于 WIFI/IMU/TOF 外设中断唤醒。
- MCU 自身 heartbeat 也升级为 4B，role 为 MCU，runtime state 为 RUNNING。

### 命名与残留清理

- 旧命名 `VSAPPUART_SendRHeartbeatControl` 已替换为 `VSAPPUART_SendHeartbeatNotify`。
- `sendMucHeart` 已替换为 `sendHeartbeatNotify`。
- 旧 `HeartbeatControl` 结构、旧 SOC reboot 状态名和旧 reason 名称已清理。

## 关键决策

1. **heartbeat 终态不兼容升级**  
   不保留旧空 payload、`1B seq` 或 `3B version` 心跳兼容逻辑，避免双方状态机长期混用。

2. **heartbeat 只做最小状态同步，不承载版本号**  
   版本查询继续走专用命令，心跳只传输 seq、角色/运行态、状态位图和 reset/reboot reason。

3. **SOC reboot 软重启与拨动开关硬重启必须区分**  
   SOC reboot 是 Linux/SOC 主动软重启，MCU 和 PA15 不掉电；拨动开关硬重启属于硬件电源路径，reason 与状态机独立。

4. **REBOOTING 必须有恢复路径**  
   只要进程仍然存活并且 reboot 命令失败，SOC 必须恢复上报 `APP_READY`，清除 `SHUTDOWN_PENDING / BOOT_GUARD_ACTIVE`。

5. **OTA 脚本接管成功由外部契约定义**  
   在脚本不可修改的约束下，app_ota 的责任边界是脚本 handoff 前通知 MCU、脚本失败分支恢复 APP_READY；脚本 0 返回后的真实 reboot 由脚本/系统集成保证。

## 涉及文件 / 模块

### MCU

- `App/protocol.h`
- `App/protocol_handlers/system_handler.c`
- `App/bsp.c`
- `App/bsp.h`
- `workspace://gd32l235/Docs/串口通信协议规范.md`
- [SOC 心跳状态同步终态方案归档](../design/2026-06-16-soc-heartbeat-terminal-state-plan.md)

### SOC / Sigmastar

- `include/app/app_uart_packet.h`
- `modules/app/include/app_uart_packet.h`
- `modules/app/src/app_uart/app_uart_packet.c`
- `modules/app/src/app_diag/provider/app_diag_uart_provider.c`
- `modules/sensor/serial/sensor_serial.h`
- `modules/sensor/serial/sensor_serial.cpp`
- `modules/sensor/main/sensor_entry.cpp`
- `modules/proto/sensor_ctrl.proto`
- `app_main/app_main.c`
- `app_ota/app_ota.c`

## 验证记录

- `rtk make app_ota_app_all -j20`：通过。
- `rtk make modules/sensor_obj_all -j20`：通过。
- `rtk make app_main_app_all -j20`：通过。
- `rtk make modules/app_obj_all -j20`：通过。
- `rtk python3 Tools/Firmware/fwtool.py build --generator ninja --build-dir build/gcc-ninja`：通过，Ninja 显示 no work to do。
- MCU 仓库 `rtk git diff --check`：通过。
- Sigmastar 仓库 `rtk git diff --check`：通过。
- 残留扫描无命中：
  - `VSAPPUART_SendRHeartbeatControl`
  - `VSAPPUART_MsgHeartbeatControl_t`
  - `sendMucHeart`
  - `HeartbeatControl`
  - `SOC_REBOOT_BEGIN`
  - `SOC_REBOOT_BOOTING`
  - `SOC_REBOOT_APP_READY`
  - `POWER_KEY_HARD_BOOT_AFTER_ON`
- `rtk bash ~/codex/scripts/final-ready.sh`：pass；额外提示的是 `~/codex` 资产仓存在无关治理类脏改动。

## 未决风险

1. **未做板级/HIL 验证**  
   当前证据是代码审计、构建和残留扫描；PA8 是否无早期唤醒脉冲、SPI NAND 是否不受干扰，还需要示波器/逻辑分析仪和串口日志联合验证。

2. **SOC 用户态启动前仍有窗口**  
   `sensor/app_ota` 发出第一包 `BOOTING + BOOT_GUARD_ACTIVE` 之前，仍依赖硬件默认态和 MCU 既有启动保护兜底。

3. **OTA 脚本成功路径是外部契约**  
   在“不修改脚本、默认接管成功”的约束下，如果脚本返回 0 但现场没有实际 reboot，当前 app_ota 不会恢复 APP_READY；这应作为脚本/系统集成风险，而不是当前协议实现缺口。

4. **工作区存在未跟踪/忽略文件**  
   Sigmastar 仓库中 `modules/app`、`modules/sensor` 属于 `.gitignore` 忽略目录；`app_main/app_main.c`、`app_ota/app_ota.c`、`app_ota/ota_upgrade.sh`、`app_ota/ota_end.sh` 当前是未跟踪文件。后续提交或打包必须单独处理纳入方式。

## 建议后续验证矩阵

| 场景 | 期望 |
|---|---|
| SOC 普通启动 | MCU 先收到 `BOOTING + BOOT_GUARD_ACTIVE`，随后收到 `APP_READY` 并清 guard |
| SOC 上层 ZMQ reboot | MCU 收到 `REBOOTING + SHUTDOWN_PENDING + BOOT_GUARD_ACTIVE`，WIFI/IMU/TOF 不产生 PA8 唤醒脉冲 |
| SOC reboot 命令失败 | SOC 恢复 `APP_READY`，MCU 清除 boot guard |
| OTA 非脚本恢复 reboot | app_ota 先通知 `REBOOTING`；若 reboot 命令失败，恢复 `APP_READY` |
| OTA SOC 脚本 handoff | app_ota 在 fork/exec 前通知 `REBOOTING`；脚本成功按外部接管成功处理 |
| OTA 脚本 fork/wait/非 0 失败 | app_ota 恢复 `APP_READY` |
| boot guard 期间 WIFI/IMU/TOF 中断 | MCU 清对应 wake flag，不执行 `SOC_Wakeup()` PA8 脉冲 |
| 拨动开关硬重启 | reason 使用 POWER_KEY/SWITCH 类，不混入 SOC_REBOOT 类 |

## Memory Candidates

| Scope | Candidate | Evidence | Risk | Confidence | Write Route |
|---|---|---|---|---|---|
| project:gd32l235+pcr02 | PCR02 的 SOC/MCU heartbeat 终态为 4B 不兼容协议：`seq, endpoint_state, status_bitmap, reset_or_reboot_reason`；版本号不走心跳，改由版本查询命令获取。 | `workspace://gd32l235/Docs/串口通信协议规范.md`、本归档验证记录 | medium | high | 项目归档；如需长期规则，人工确认后写项目 AGENTS |
| project:gd32l235 | MCU 只接受 role=SOC 的 4B heartbeat 来更新 `Soc_Boot_Guard_Flag`；boot guard 期间只抑制 WIFI/IMU/TOF 触发 PA8，不把 `Wakeup_Soc_Flag` 等同为外设唤醒。 | `App/protocol_handlers/system_handler.c`、`App/bsp.c` | medium | high | 项目归档或项目 memory candidate |
| project:xcrz_sigmastar_demo | SOC 进入 `REBOOTING` 后必须有恢复闭环：reboot 成功由重启后 `BOOTING -> APP_READY` 闭环；reboot 命令失败且进程存活时必须恢复 `APP_READY`。 | `modules/sensor/main/sensor_entry.cpp`、`app_ota/app_ota.c` | medium | high | 项目归档 |
| project:xcrz_sigmastar_demo | OTA 脚本不可修改时，app_ota 的边界是 handoff 前通知 MCU、失败分支恢复 APP_READY；脚本 0 返回后的实际 reboot 是外部集成契约。 | 用户约束“ota脚本不能修改，默认接管成功”、`app_ota/app_ota.c` | high | high | archive-only，避免误提升为通用规则 |
| workflow:multi-repo | 本项目同时涉及 MCU 仓库和 Sigmastar 仓库；Sigmastar 的 `modules/app`、`modules/sensor` 被 `.gitignore` 忽略，提交/打包前必须用显式路径和 `check-ignore` 复核。 | 本会话 `git status`、`check-ignore` 结果 | low | high | workflow memory candidate |

## Gate Result

- Archive Candidate: pass
- Memory Candidate: report-only，未写入 `~/.codex/memories`
- Secret/Sensitive Content: 未包含密钥、访问令牌、完整日志或私有凭证
