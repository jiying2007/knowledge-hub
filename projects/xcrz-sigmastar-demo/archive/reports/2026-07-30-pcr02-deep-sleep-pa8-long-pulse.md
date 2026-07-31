---
id: pcr02-deep-sleep-pa8-long-pulse-20260730
title: PCR02 DEEP_SLEEP PA8 长脉冲硬件休眠机制实现归档
kind: project-archive
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/archive/reports/2026-07-30-pcr02-deep-sleep-pa8-long-pulse.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
related:
- projects/xcrz-sigmastar-demo/archive/reports/2026-07-22-pcr02-tcpka-low-power-protocol-v1.md
- projects/xcrz-sigmastar-demo/archive/reports/2026-07-28-pcr02-motor-uart-low-power-session-closeout.md
- projects/gd32l235/archive/debug/2026-07-17-battery-rail-drop-mcu-reboot.md
source:
  type: current-codex-session-and-source-validation
  from: 2026-07-30 PCR02 SoC、Sensor 与 GD32L235 MCU 源码、提交状态、本地静态检查和构建证据
  source_sha256: 7a66b72e6721b33427a54f5329b645e051f08e121cc78e9891008854632d6e0a
  temporary_source_retained: false
review_after: '2026-10-30'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- pcr02
- deep-sleep
- pa8
- pa15
- tcpka
- sensor
- gd32l235
- low-power
- cross-repo
validation_refs:
- projects/xcrz-sigmastar-demo/archive/reports/2026-07-30-pcr02-deep-sleep-pa8-long-pulse.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: source-build-validation-hil-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/archive/reports/2026-07-30-pcr02-deep-sleep-pa8-long-pulse.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-07-30'
updated_at: '2026-07-30'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-07-30'
manual_validation_pending: true
summary_zh: 固化 PCR02 DEEP_SLEEP 的正式 PA8 长脉冲硬件休眠机制、PA15 保持供电、9 ms PA8 唤醒、并发边界、跨仓提交状态与主机构建证据；板级 HIL 和 BCMSDIO 综合门禁仍待闭环。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: reviewed
---

# PCR02 DEEP_SLEEP PA8 长脉冲硬件休眠机制实现归档

## 归档目的与结论边界

本文固化 2026-07-30 PCR02 `DEEP_SLEEP` 从“MCU 拉低 PA15 切断整机保持电源”调整为“PA15 保持高电平，MCU 输出 PA8 长脉冲触发 SoC 硬件休眠/内部掉电”的正式实现。

当前可确认：

- MCU 状态机、SoC 应用等待时序、Sensor TCPKA 说明和静态合约已按 PA8 长脉冲机制调整。
- MCU 普通与 wakeup-diag 固件均构建成功。
- PCR02 正式应用和独立 Sensor 测试应用均构建成功。
- `DEEP_SLEEP=0x03`、UART 休眠控制格式和上层 Sensor proto 未改变。
- MCU 实现已进入 `v1.1.40`；SoC 正式应用改动已进入 `dev/pcr02`。

当前不能确认：

- 尚无使用上述最终 MCU/SoC 组合执行的板级 HIL 证据，因此不能把“SoC 已实际停止运行、内部电源域已关闭、WiFi/充电可稳定唤醒”标记为通过。
- 根工程综合低功耗静态脚本仍因 BCMSDIO wake-lock 规则与当前 kernel 源码不一致而失败，不能声明完整提交/发布门禁全绿。
- `modules/sensor` 的两处说明性变更，以及根仓独立测试模块和综合静态脚本，归档时仍未全部纳入已提交源码。

本文不保存设备地址、测试服务器地址、真实 SN、raw 串口日志、二进制、凭证或本机绝对路径。

## 当前正式机制

### 进入时序

`DEEP_SLEEP` 使用以下板级时序：

1. Sensor 停止业务、IMU、TOF 和重型硬件资源，完成安全反初始化。
2. Sensor arm TCPKA，再向 MCU 提交 `DEEP_SLEEP`。
3. MCU 可靠发送 `DEEP_SLEEP ARMED`；收到 SoC 对该通知的成功 ACK 后，等待 100 ms，保证串口发送排空。
4. MCU 保持 PA15 为高电平。
5. MCU 将 PA8 拉高约 8010 ms，触发 SoC 硬件休眠/内部掉电。
6. 长脉冲结束后 MCU 将 PA8 恢复为低电平。
7. WIFI/IMU/TOF 唤醒 EXTI 继续静默 5 s，到期时清除 pending，再按策略启用，避免 SoC 刚进入休眠就被入口阶段的网络或传感器边沿立即唤醒。

PA15 代表整机保持供电，不再作为 `DEEP_SLEEP` 的不可逆动作。这里的“SoC 掉电”指 PA8 长脉冲触发的 SoC 硬件休眠/内部电源域关闭，不等同于 PA15 变低。

### 唤醒时序

- WIFI 或 CHARGE 在 `DEEP_SLEEP` 完成后触发时，MCU 输出约 9 ms PA8 高脉冲。
- MCU 输出 `WAKE_FIRE`，并可靠发送 `WAKEUP_RESULT FIRED`。
- SoC 恢复运行后 ACK 唤醒结果、清理 TCPKA suspend/session，并同步 RUNNING 状态。

诊断日志的预期顺序为：

```text
DEEP_ACK ... phase=1
DEEP_SLEEP_PULSE ... phase=2 pa8=0->1 pa15=1 duration_ms=8010
DEEP_SLEEP_ENTER ... phase=4 pa8=0 pa15=1 guard_ms=5000
```

## 并发与失败边界

### 充电接入

- PA8 长脉冲开始前检测到有效充电接入：撤销待执行的 `DEEP_SLEEP`，恢复 RUNNING 策略并输出 9 ms PA8 唤醒脉冲。
- PA8 长脉冲期间检测到充电接入：锁存 CHARGE 来源，保持长脉冲完整结束，再立即输出 9 ms PA8 唤醒脉冲。
- SoC 已进入硬件休眠后检测到充电接入：按正常 CHARGE 唤醒处理。

### PA11 物理开关 OFF

PA11 OFF 的优先级高于 `DEEP_SLEEP`。若在 100 ms 等待或 PA8 长脉冲期间确认稳定 OFF，MCU 必须：

1. 立即拉低 PA8；
2. 撤销 `DEEP_SLEEP` 状态机、入口保护和模块唤醒 mask；
3. 转入既有 PA11 关机流程；
4. 后续 PA15 只由物理关机流程控制。

这避免 `DEEP_SLEEP` 的 PA15 保持动作与物理关机并发竞争。

### 失败恢复

- ARMED 可靠通知失败：MCU 撤销 `DEEP_SLEEP`、拉低 PA8 并保持 PA15 为高，回到 RUNNING 安全策略。
- Sensor/SoC 在提交 ARMED 后设置 12 s 失效保护，覆盖 100 ms 排空、8010 ms 长脉冲和板级转换裕量。
- 12 s 后进程仍运行：判定硬件休眠转换失败，Sensor 发送 APP_READY/DISARM 恢复 MCU RUNNING，清理资源并以失败退出。

## 术语决定

本机制是 PCR02 当前正式的 `PA8 长脉冲硬件休眠机制`，不是兼容、旧版或 legacy 路径。文档和日志不得使用“旧版低电”“旧 2%”或“legacy PA8 sleep”等表述。

允许提及历史来源仅用于解释设计演进，但不得把历史条件写成当前运行时分支或兼容语义。

## Supersedes 候选

本文仅替代以下历史文档中的 `DEEP_SLEEP` 电源语义，不替代其 TCPKA payload、DNS、revision、WiFi firmware session 或 STANDBY/SLEEP 内容：

- `projects/xcrz-sigmastar-demo/archive/reports/2026-07-22-pcr02-tcpka-low-power-protocol-v1.md`
  - “DEEP_SLEEP 由 MCU 切断 SoC 电源”
  - “WiFi 唤醒时拉高 PA15 重新上电”
  - “DEEP_SLEEP 冷启动”
  - “ARMED 后可立即切断 PA15”
- `projects/xcrz-sigmastar-demo/archive/reports/2026-07-28-pcr02-motor-uart-low-power-session-closeout.md`
  - WiFi shadow 中“DEEP_SLEEP 不恢复 PA15”的描述应理解为“不驱动 PA8 唤醒”，而非 PA15 rail 当前处于关闭状态。

原文保留为 historical provenance；在 owner 完成内容复核前，本条目仅作为 `reviewing` supersedes candidate。

## 主要源码与提交状态

### GD32L235 MCU

- 实现提交：`eb696e37f890942f82dabba26cbb2c712ee02059`，`fix(power): 使用PA8长脉冲进入深度休眠`
- 发布提交：`06f375a03d0133362dc366593f5a6da72647432e`，`chore(release): 发布1.1.40固件`
- 发布标记：`v1.1.40`
- 归档时状态：`master` 与 `origin/master` 一致，工作区干净。

关键文件：

- `App/wakeup.c`
- `Tools/tests/check_wakeup_diagnostics.py`
- `Tools/tests/check_charge_wakeup_contract.py`
- `Docs/串口通信协议规范.md`
- `Docs/IO功能说明.md`

### PCR02 SoC 应用

- 正式应用提交：`d40b24846d825b4ba42148c808f5a961cef058c3`
- 提交摘要：`fix(sensor): 修正MCU深度睡眠的PA8长脉冲等待时序及日志信息`
- 归档时状态：`dev/pcr02` 与 `origin/dev/pcr02` 一致。
- 变更：正式应用将 `DEEP_SLEEP` 看门狗从 5 s 延长至 12 s，并更新 PA8/PA15 日志语义。

### Sensor 子仓与独立测试

- `modules/sensor` 基线：`d77e7fae0a6fc0b66f572717315c42e0c6ed2eac`
- 归档时仍有两处未提交说明性变更：
  - `docs/tcpka_keepalive_protocol.md`
  - `hardware/tcpka.cpp`
- 根仓 `app_sensor_test/` 整体仍为 untracked，包含 12 s 看门狗和独立 `DEEP_SLEEP` 测试说明。
- 根仓 `build/check_soc_low_power_flow.py` 仍为 untracked，包含 PA8 长脉冲静态合约及既有 BCMSDIO 门禁。

这些未提交项不得从 MCU/SoC 已发布状态推断为已经进入主线或发布制品。

## 验证证据索引

| 验证 | 结果 | 结论边界 |
| --- | --- | --- |
| MCU 全部 `Tools/tests/check_*.py` | 退出码 0 | 静态合约通过，包括禁止 `DEEP_SLEEP` 使用 `POWER_KEEP_OFF`、PA8 状态顺序、充电和 PA11 并发 |
| MCU 普通 Release 构建 | 成功；App Flash 45,772 B / 50 KB，RAM 14,392 B / 24 KB | 普通发布配置可编译、链接并满足分区 |
| MCU wakeup-diag 构建 | 成功；App Flash 50,180 B / 50 KB，RAM 15,464 B / 24 KB | 新诊断字符串和日志分支可编译，仍在分区内 |
| `make -B app_sensor_test_app_all pcr02_app_all` | 退出码 0 | 独立 Sensor 测试与正式 PCR02 应用编译成功 |
| MCU、SoC 定向文件、Sensor 子仓 `git diff --check` | 退出码 0 | 本次文本差异无空白错误 |
| `final-ready.sh` | 退出码 0 | Codex 完成前记录成功；不替代板级验证 |
| `build/check_soc_low_power_flow.py` | 退出码 1 | 仅报告 11 项 BCMSDIO wake-lock/SDIO suspend 字面门禁失败；PA8/DEEP_SLEEP 新检查未失败 |

MCU 构建中仍存在供应商 `gd32l23x_rcu.c` 的既有 tautological-compare warning；本次没有新增该 warning，也未在此归档中宣称供应商告警已清零。

## 板级 HIL 验收

发布前至少完成以下验证：

1. 使用匹配的 MCU `v1.1.40` 和包含 SoC `d40b2484` 的应用制品。
2. 执行独立 Sensor `DEEP_SLEEP` 测试，确认：
   - PA15 始终为高；
   - PA8 高脉冲约 8010 ms；
   - SoC 控制台、应用和 ADB 在 12 s 失效保护前停止运行；
   - 不出现 `SoC is still running after DEEP_SLEEP PA8 sleep-transition watchdog`。
3. PA8 长脉冲结束后至少等待 5 s，再测试 WIFI 唤醒，确认 9 ms PA8 脉冲、`WAKE_FIRE` 和唤醒来源回报。
4. 分别测试充电在长脉冲前、长脉冲中和硬件休眠后的行为。
5. 在 100 ms 等待和 PA8 长脉冲期间分别拨动 PA11 OFF，确认 DEEP_SLEEP 被撤销并由既有物理关机流程接管。
6. 保存脱敏的 MCU 日志、SoC 日志、PA8/PA15 波形或等价板级证据，以及最终 MCU/SoC 制品标识。

## 未闭环项

1. 完成上述板级 HIL，生成独立 validation 条目。
2. 明确 BCMSDIO 修复所在的最终 kernel 源码基线，并让 `build/check_soc_low_power_flow.py` 与实际实现一致；在此之前综合门禁不得标记为通过。
3. 审查并提交 `modules/sensor` 的两处说明性变更。
4. 决定根仓是否正式纳管 `app_sensor_test/` 和 `build/check_soc_low_power_flow.py`；不得把整个 untracked 目录无审查加入提交。
5. owner 复核本条目的 supersedes 范围，再决定是否更新历史归档的状态或关联索引；不得删除历史记录。

## Provenance、脱敏与治理

- `captured_at`：2026-07-30。
- `last_verified`：2026-07-30。
- 来源：当前 Codex 会话、上述 Git 提交、工作区只读状态、定向静态检查和本地构建结果。
- 已脱敏：设备地址、服务器地址、真实 SN、raw log、二进制、凭证和本机绝对路径均未保存。
- 原始会话和临时构建目录未归档。
- memory candidate：否。
- AGENTS candidate：否。
- promotion：无；本条目保持 `reviewing`，不自动提升为 current fact、owner decision、memory 或团队通用规范。
