---
related:
- projects/gd32l235/archive/design/2026-07-22-pa11-charge-soc-power-gate-design.md
human_reviewed_by: null
human_reviewed_at: null
review_basis: null
incident_id: null
severity: null
affected_version: null
id: gd32l235-power-key-exit-restart-convergence-20260803
title: GD32L235 POWER_KEY 退出中拨回 ON 的重启收敛
kind: debug-record
domain: projects/gd32l235
path: projects/gd32l235/archive/debug/2026-08-03-power-key-exit-restart-convergence.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: manual
  from: 本次会话代码审查、测试与用户提供的板级现象构成项目内调试来源。
  source_sha256: 2ac1a69b133b7de95805111872a589982dcbc531b60f61c3e0f7e6c1ac0065fc
review_after: '2026-09-03'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- gd32l235
- power-key
- soc-exit
- restart-convergence
- pa8
- pa15
validation_refs:
- projects/gd32l235/archive/debug/2026-08-03-power-key-exit-restart-convergence.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/gd32l235/archive/debug/2026-08-03-power-key-exit-restart-convergence.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-08-03'
updated_at: '2026-08-03'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-08-03'
manual_validation_pending: true
summary_zh: 拨动开关在 SOC 应用退出期间由 OFF 拨回 ON 时，旧逻辑会过早取消关机事务，导致 SOC 保持供电但应用不重启；当前软件以发送 POWER_KEY 为提交点，并在 PA11 为 ON 时通过 PA8 长按关机后再唤醒来收敛到新 APP_READY，板级波形仍待验证。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
---

# GD32L235 POWER_KEY 退出中拨回 ON 的重启收敛

## 现象

PA11 拨动开关初始为 ON，SOC 应用正常运行。用户先拨到 OFF，MCU 发起应用退出；在应用尚未完全退出时又拨回 ON。旧状态机会取消 MCU 侧关机事务并保持 PA15 为高，但 SOC 应用可能已经进入不可逆退出阶段，最终表现为 SOC 仍有电、应用停止且不自动重启，通常需要再次下桩/上桩或重新拨动才能恢复。

用户补充的板级现象是：PA11 保持 ON 时，即使 MCU 将 PA15 拉低，也似乎无法切断 SOC 电源。

## 影响范围

- 项目：GD32L235 固件。
- 模块：拨动开关消抖、SOC 退出事务、PA8 唤醒/长按、PA15 SOC 保持供电。
- 触发窗口：SOC 已接收 `POWER_KEY` 退出命令，但尚未完成退出时，开关由 OFF 返回 ON。
- 影响：SOC 可能停留在“有电但应用不运行”的中间态。
- 版本边界：本记录基于 2026-08-03 工作区代码，不据此声明任何已发布版本或量产设备均已修复。

## 根因

旧逻辑把“当前目标重新变为 ON”和“已经发送的退出命令仍可撤销”等同处理：在 `SOC_EXIT_WAIT_CONFIRM` 阶段收到 ON 后，直接报告 `CANCELLED`、保持 PA15 高并将事务复位为 `IDLE`。但 `POWER_KEY` 一旦到达 SOC，SOC 应用可能已经开始退出，MCU 无法通过本地取消恢复该应用，因此事务提前结束，系统没有继续收敛到新的 `APP_READY`。

同时，基于当前硬件路径和用户观察，PA11 与 PA15 是 SOC 供电保持的硬件 OR 路径。PA11 为 ON 时，单独拉低 PA15 不能保证形成 SOC 断电窗口。因此不能把“PA15 拉低后再拉高”作为此场景的冷启动手段。

第二项属于待板级波形确认的硬件结论。它修正/取代既有设计归档 `2026-07-22-pa11-charge-soc-power-gate-design.md` 中“PA11 为 ON 时 PA15 可独立切断 SOC”的假设；旧记录保留作为历史，不静默覆盖。

## 修复决策

- OFF 稳定后先保留 300 ms 本地宽限期；在 `POWER_KEY` 尚未发送前拨回 ON，可以安全取消。
- `POWER_KEY` 一旦可能到达 SOC，就把退出事务视为已提交；后续 ON 或 SOC 返回 `CANCELLED` 均不再取消本地事务。
- 最终目标为 OFF：完成退出确认后将 PA15 拉低并保持关机。
- 最终目标为 ON：PA15 保持高，通过 PA8 输出约 8010 ms 长脉冲，触发 SOC 硬件睡眠/内部关机；随后执行约 9 ms 正常唤醒脉冲，并等待新的 `APP_READY`。
- 30 s 内未收到新的 `APP_READY` 时，只重试一次 PA8 长按重启；再次超时进入 `BOOT_FAILED`，避免无限循环。
- 状态和动作语义收敛为明确的目标事务，包括 `SOC_EXIT_ACTION_POWER_KEY_TARGET` 与 `SOC_EXIT_RESTART_SLEEP_PULSE_ACTIVE`。

## 软件验证

以下验证在 2026-08-03 工作区完成并通过：

- `rtk python3 Tools/tests/check_application_power_target_convergence.py`
- `rtk python3 Tools/tests/check_application_soc_exit_commit.py`
- 关机和离线相关回归测试
- `rtk git diff --check`
- `rtk env BUILD_DIR=build/codex-power-target-convergence bash scripts/codex-check.sh --quick`

Quick 检查最终结果为 `codex-check: PASS (quick)`，覆盖完整测试、构建和打包检查。普通构建 App FLASH 为 46744 B/50 KB（91.30%），RAM 为 14400 B/24 KB（58.59%）；认证构建 App FLASH 为 49280 B/50 KB（96.25%），RAM 为 14416 B/24 KB（58.66%）。

曾有一次 quick 检查因使用显式扁平 `--output-dir` 生成包，而检查脚本要求默认嵌套包路径而失败；恢复默认包布局后重跑通过。该失败用于确认打包门禁行为，不是固件逻辑失败。

## 板级待验证

在真实板卡以同一时间基准观测：

- PA11 在整个重启事务中保持 ON；
- PA15 保持高；
- PA8 先出现约 8010 ms 长脉冲，随后出现约 9 ms 唤醒脉冲；
- SOC 日志显示长按后完成内部关机/重启；
- MCU 最终收到一次新的 `APP_READY`。

若该板 SOC 对 PA8 长按不执行内部关机，则软件无法仅靠 PA15 提供替代断电路径；后续需要独立 SOC RESET 信号或 SOC 侧可靠 reboot 能力。完成上述 HIL 前，不声明板级问题已修复。

## 证据与来源

- Source repository：`workspace://gd32l235`
- Source verification date：2026-08-03
- Code：`App/bsp.c`、`App/bsp.h`
- Tests：`Tools/tests/check_application_power_target_convergence.py`、`Tools/tests/check_application_soc_exit_commit.py`
- Docs：`Docs/串口通信协议规范.md`、`Docs/IO功能说明.md`
- Related historical record：`projects/gd32l235/archive/design/2026-07-22-pa11-charge-soc-power-gate-design.md`
- Captured at：2026-08-03 Asia/Hong_Kong

## 状态与治理边界

- 状态：`reviewing`
- 软件验证：已通过当前工作区自动测试、构建和打包门禁。
- 人工/板级验证：待完成。
- 推广状态：未提升为 active decision 或 runbook。
- 脱敏：不包含 raw log、二进制、凭证、设备序列号或个人信息。
- Memory candidate：否；该结论是项目专用硬件/固件状态机记录，不应写入通用长期记忆。
