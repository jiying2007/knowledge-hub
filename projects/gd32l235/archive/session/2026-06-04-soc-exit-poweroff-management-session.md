---
related:
- projects/gd32l235/current/soc-low-power-contract.md
- projects/gd32l235/archive/design/2026-07-22-low-battery-soc-sleep-protection-design.md
- projects/gd32l235/archive/design/2026-07-22-soc-shutdown-confirmation-closure-design.md
captured_at: '2026-06-04'
id: gd32l235-soc-exit-poweroff-management-session-20260604
title: GD32L235 与 SOC 退出、休眠和掉电管理会话归档
kind: project-archive
domain: projects/gd32l235
path: projects/gd32l235/archive/session/2026-06-04-soc-exit-poweroff-management-session.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: source-project-session-summary
  from: workspace://gd32l235/Docs/会话归档-GD32L235-SOC退出掉电管理-20260604.md
  source_sha256: 656ae32b124ff3348279f6b820a3587ae39fa7c7cdb38aeac5673117d22079eb
review_after: '2026-08-22'
review_status: human-reviewed-accepted
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- gd32l235
- soc-exit
- sleep
- poweroff
- session
validation_refs:
- projects/gd32l235/archive/session/2026-06-04-soc-exit-poweroff-management-session.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/gd32l235/archive/session/2026-06-04-soc-exit-poweroff-management-session.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-07-22'
updated_at: '2026-07-26'
generated_by_ai: true
ai_role: classified
ai_model_or_tool: Codex
ai_generated_at: '2026-07-22'
manual_validation_pending: true
summary_zh: 保存 MCU 与 SOC 退出确认、低电量 SLEEP、PA11/PA15 电源裁决及跨仓协议协同的会话级决策与验证证据。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
---

# 会话归档：GD32L235 与 SOC 退出/休眠/掉电管理

## 归档说明

- 本文是 2026-06-04 会话快照；其中方案、验证结果和 dirty 状态只对捕获时点有效。
- 当前权威顺序为 MCU/SOC 源码、`workspace://gd32l235/Docs/串口通信协议规范.md`、[当前低功耗协同契约候选](../../current/soc-low-power-contract.md)。
- 文中 PA15“整机电源保持”、旧 `0x09` 长度兼容和早期 PA11 推导已被后续硬件复核与固定 3B 协议取代；保留正文仅用于追溯决策演进。
- Review：owner `leiwenjun`；复审日期 2026-08-22；重点验证 shutdown 单飞、取消/确认竞态和板级 PA8/PA15 时序。

## 元信息

- Captured at: 2026-06-04
- Scope: 当前会话，覆盖 `gd32l235` MCU、`xcrz_sigmastar_demo` SOC 主应用、`modules/sensor` 串口桥接、`modules/app` 串口协议扩展。
- Source: 当前会话中的设计讨论、日志诊断、代码落地和定向验证结果。
- Sanitization: 已去除长原始日志，仅保留可复用结论、文件路径、关键协议状态和验证证据。

## 本次完成

### MCU 侧

- 设计并落地统一 SOC 退出管理思路：`COMMAND_SENT -> 等 SOC_CONFIRMED 或超时 -> confirmed 后 settle -> 执行 PA8 sleep 或 PA15 OFF`。
- 明确 PA8/PA15 分工：
  - PA8：SOC 唤醒/休眠脉冲。
  - PA15：整机电源保持/掉电。
- 低电量保护策略明确为 `percent <= 2 && !charging` 触发，低电量场景采用 SOC 休眠保护而不是虚假整机掉电。
- 低电量开机防误判已补齐：
  - BSP 初始化先同步 `Charge_Get_Status()` 到 `RunParam.Charging_Flag`；非充电初始态保持 `REPORT_STATE_IDLE`，不发送假的 `CHARGE_LEAVE`。
  - 首笔电量读数受 `LOW_BATTERY_SOC_STARTUP_GRACE_MS = 5000U` 保护，不能直接触发 SOC sleep。
  - 低电量触发需要连续 `LOW_BATTERY_SOC_SLEEP_CONFIRM_COUNT = 3U` 次 `percent <= 2`。
  - 电压报告值需小于 `LOW_BATTERY_SOC_SLEEP_MAX_VOLTAGE_REPORT = 66U`，避免百分比误低但电压仍正常时误休眠。
- PA11 快速拨动策略明确为 MCU 持续以硬件 PA11 状态做最终裁决：
  - PA11 拨回 ON 时取消旧 POWER_KEY 请求，保持 PA15 ON。
  - PA15 OFF 动作前必须复核 PA11 仍为 OFF。
  - PA15 OFF 至少保持 100ms；PA11 仍 OFF 时持续保持 OFF，不再重复发 shutdown。
- 旧 `protocol.c` post action power off 已改为调用 `Bsp_SocExit_StartPowerKeyShutdown()`，不再直接拉低 PA15；当前 PA15 OFF 只允许在 `bsp.c` SOC exit 状态机内执行。
- SOC 应用退出总等待从 5s 调整到 6s；收到 SOC_CONFIRMED 后 settle 从 1s 调整到 2s，当前宏为：
  - `SOC_APP_EXIT_TIMEOUT_MS = 6000U`
  - `SOC_CONFIRMED_APP_DEINIT_WAIT_MS = 2000U`
- 因本轮行为变更发生在 `v1.1.21` 正式发布之后，MCU app patch 版本已提升到 `1.1.22`，避免新行为继续复用已发布版本号。

### SOC 主应用

- `pcr02/main.cpp` 增加 MCU shutdown request 的 reason/detail 保存和确认回包。
- SOC 退出确认点移动到关键业务模块退出、日志 flush、`sync()` 之后，并在 `sensor_module.deinit()` 之前发送 `SOC_CONFIRMED`，保证串口仍可用。
- 外部 `SIGTERM` / `SIGINT` 退出时不发送 `SOC_CONFIRMED`；若存在 MCU shutdown request，则发送 `CANCELLED`，避免 MCU 执行 PA8/PA15 动作。
- 针对 MCU 在 SOC deinit 中取消的情况，退出尾部消费 `CANCELLED` 后不再发送 `SOC_CONFIRMED`。

### SOC 串口协议与桥接

- `app_uart` 的 shutdown notify payload 扩展为：
  - `payload[0] = stage`
  - `payload[1] = reason`
  - `payload[2] = detail`
- 保持旧 payload 长度 1 兼容：旧格式 reason/detail 默认为 0。
- 新增 SOC -> MCU 的 shutdown stage 回包接口，支持 `SOC_CONFIRMED` 与 `CANCELLED`。
- `modules/sensor/serial` 增加 shutdown 单飞锁：
  - 已有 active shutdown 时，重复 `COMMAND_SENT` 不再发布 POWEROFF，不覆盖 active reason/detail。
  - 收到匹配的 `CANCELLED` 时记录取消并清除 pending。
  - key event 线程遇到取消后的过期 POWEROFF 时忽略并继续运行。

### 设计文档

- 新增/更新：
  - `projects/gd32l235/archive/design/2026-07-22-low-battery-soc-sleep-protection-design.md`
  - `projects/gd32l235/archive/design/2026-07-22-soc-shutdown-confirmation-closure-design.md`
- 文档同步了 6s 总超时、2s settle、PA11 快速拨动、SOC 侧单飞与取消策略。

## 关键决策

1. **低电量场景不做虚假掉电**  
   低电量且非充电时，目标是 SOC 休眠保护：PA8 长脉冲让 SOC sleep，PA15 保持 ON。真正整机掉电只用于拨动开关关机等硬件关机场景。

2. **SOC_CONFIRMED 必须代表“应用退出准备完成”**  
   不能在串口回调刚收到 `COMMAND_SENT` 时确认。SOC 应在关键模块退出、日志 flush、`sync()` 后再回包。

3. **CANCELLED 优先级高于晚到 CONFIRMED**  
   MCU 已取消时，SOC 不能再发送 `SOC_CONFIRMED`。若已经确认完成，则由 MCU 的 reason/detail 和 PA11 复核兜底。

4. **POWER_KEY shutdown 必须单飞**  
   快速 OFF/ON/OFF 时，SOC 侧不允许重复 `COMMAND_SENT` 重入退出流程；MCU 侧以最新硬件 PA11 状态裁决 PA15。

5. **总等待不是固定等待**  
   MCU 总 deadline 为 6s。SOC 早确认后仍等待 2s settle；若总 deadline 先到，则不等满 settle。

## 验证记录

- 已执行定向静态检查：
  - `rtk git -C <gd32l235-repo> diff --check -- App/bsp.h`
  - 历史检查：`rtk rg -n "5s|1s|5秒|1秒|5000U|1000U" Docs/低电量SOC休眠保护设计.md Docs/SOC侧Shutdown确认闭环设计.md`（源文件现已迁入 Hub）
  - `rtk git ... diff --check` 针对 SOC `main.cpp`、`sensor_serial.cpp/.h`、设计文档等改动执行过。
- 未执行编译验证；编译和上板验证由人工操作。
- `final-ready.sh` 曾通过命令检查，但提示当前会话线程过长，建议收口后新开会话继续。

## 未决风险

1. **SOC confirmed 后仍有 `sensor_module.deinit()`**  
   日志显示 `Shutdown confirmed sent` 后仍会进入 `sensor_module.deinit()`，其中 camera/ISP/TOF/IMU 等释放可能超过 2s。若实测 2s 仍不够，根治方向是让 SOC 保留最小串口发送能力，把 `SOC_CONFIRMED` 再后移到更接近进程退出的位置。

2. **多个仓库存在既有脏文件**  
   SOC 主仓和 `modules/sensor` 有大量既有 dirty/untracked 文件，后续提交前需要按仓库分别检查，避免把无关库文件、产物或临时文件纳入 commit。

3. **未做 HIL 验证**  
   需要真实板级验证 PA11 快速拨动、PA15 OFF 保持、PA8 sleep 脉冲、SOC confirmed/cancelled 回包时序。

4. **SOC supervisor 行为需要继续观察**  
   如果 SOC 应用退出后被 daemon 拉起，而 MCU 还未执行 PA8/PA15，可能出现日志重启片段。需要结合 MCU 时序确认是否符合预期。

## 建议验证矩阵

| 场景 | 期望 |
|---|---|
| 开机首笔电量误报 0~2%，电压报告值仍正常 | MCU 不立即触发低电量 SOC sleep；至少等待 5s、3 次连续低电量且电压报告值低于 66 |
| PA11 OFF，SOC 正常确认 | MCU 收 confirmed 后等待 2s settle；PA11 仍 OFF 时 PA15 OFF 并至少保持 100ms |
| PA11 OFF 后快速 ON | MCU 发送 CANCELLED；SOC 不回 confirmed；PA15 保持 ON |
| PA11 OFF->ON->OFF | SOC 不重入旧请求；MCU 以 active token 和最新 PA11 状态裁决 |
| SOC 不回 confirmed | MCU 6s 兜底；POWER_KEY 场景执行前仍复核 PA11 |
| 低电量非充电 | 启动稳定后，连续 3 次 `<=2%` 且电压报告值低于 66，SOC 退出确认或 6s 超时后 PA8 sleep，PA15 ON |
| 充电认证 | SOC 退出确认或 6s 超时后 PA8 sleep，PA15 ON，MCU+WIFI 继续工作 |
| 外部 kill -TERM | SOC 不回 confirmed；如有 pending request，发送 CANCELLED |

## Memory Candidates

| Scope | Candidate | Evidence | Risk | Confidence | Write Route |
|---|---|---|---|---|---|
| project:gd32l235 | GD32L235 的 SOC 退出管理以 `COMMAND_SENT -> SOC_CONFIRMED/CANCELLED/timeout -> settle -> PA8/PA15` 为统一框架；PA8 只做 SOC 唤醒/休眠，PA15 控制 SoC 独立供电。 | 本会话设计与 `projects/gd32l235/archive/design/2026-07-22-low-battery-soc-sleep-protection-design.md`；原“整机保持”表述已被后续硬件复核取代 | medium | high | archive-only；当前事实回到源码与当前契约候选核验 |
| project:pcr02_soc | SOC 应用 `xcrz_sigmastar_demo` 的 shutdown confirmed 不能在串口回调早确认，必须在关键模块退出、flush、sync 后发送；外部信号退出不回 confirmed。 | 本会话 SOC 侧实现和日志诊断 | medium | high | 项目归档 |
| lesson:embedded-shutdown | 机械拨动开关类关机必须把硬件输入作为最终裁决，并支持取消旧请求；软件 confirmed 只能加速流程，不能替代最终硬件复核。 | PA11 快速拨动导致旧请求继续 shutdown 的排障 | medium | high | archive-only 或 lesson memory |
| workflow:multi-repo | PCR02 项目中 `modules/sensor`、`modules/app` 与 SOC 主仓是独立仓库，提交和验证必须分仓处理，避免遗漏或误纳入无关脏文件。 | 本会话多仓状态检查 | low | high | project memory candidate |

## 后续建议

1. 上板验证 6s/2s 时序是否覆盖 `sensor_module.deinit()` 的最长耗时。
2. 若仍提前 PA8/PA15，优先调整 SOC confirmed 发送点，而不是继续无上限增加 MCU settle。
3. 分仓整理 commit：
   - MCU：设计文档和当前宏状态。
   - SOC 主仓：协议头、main.cpp、sensor module 接口变更。
   - modules/sensor：shutdown 单飞、取消、过期 POWEROFF 处理。
   - modules/app：app_uart shutdown payload/发送接口。
