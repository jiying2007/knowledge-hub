---
id: gd32l235-smart-reserve-charge-wakeup-20260730
title: GD32L235 智能留电充电唤醒与低电策略归档
kind: project-archive
domain: projects/gd32l235
path: projects/gd32l235/archive/design/2026-07-30-smart-reserve-charge-wakeup.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: committed-source-and-local-validation
  from: workspace://gd32l235 commit db7ccc5ccaa60abd6c695052abebe29ae8d90bd8 plus local validation captured 2026-07-30
  source_sha256: ea6ee6445eb989b4797fbe18834838827810afb44d27731f37de520caa55acdd
  temporary_source_retained: false
review_after: '2026-08-30'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- gd32l235
- pcr02
- low-power
- smart-reserve
- charge-wakeup
- sleep
- deep-sleep
- hil-pending
validation_refs:
- projects/gd32l235/archive/design/2026-07-30-smart-reserve-charge-wakeup.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/gd32l235/archive/design/2026-07-30-smart-reserve-charge-wakeup.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-07-30'
updated_at: '2026-07-30'
generated_by_ai: true
ai_role: summarized
ai_model_or_tool: Codex
ai_generated_at: '2026-07-30'
manual_validation_pending: true
summary_zh: 归档 GD32L235 移除 MCU 2%/3% 自主低电休眠、由 SoC 应用负责 5% 智能留电、SLEEP/DEEP_SLEEP 增加 PA7 充电唤醒、双 profile 软件验证和待完成板级 HIL 的职责与证据。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
---

# GD32L235 智能留电充电唤醒与低电策略归档

## 摘要

本记录归档 2026-07-30 完成的 GD32L235 低功耗职责调整：设备端 5% 智能留电触发、充电状态判断和 APP 电量映射由 SoC 应用负责；MCU 不再按本地 2%/3% SOC 阈值自主发起休眠，只负责原始电量上报、执行 SoC 下发的 SLEEP/DEEP_SLEEP、WiFi 唤醒和充电接入硬件唤醒。

MCU 新增 PA7 充电接入唤醒：SLEEP 使用固定 9 ms PA8 脉冲；DEEP_SLEEP 根据 PA15 断电阶段撤销待断电、锁存充电来源或重新给 SoC 上电。软件契约测试、正常 Release 和 charge-cert profile 均通过，板级 HIL 尚未执行。

本条目是 `reviewing` 历史证据，不是 active 规范、发布签收或硬件验收结论。

## 背景与问题

原 MCU 同时存在两套低功耗触发链：

1. SoC 应用下发 `SLEEP_CONTROL`，MCU 的 `wakeup.c` 状态机执行 SLEEP/DEEP_SLEEP。
2. MCU 在原始 SOC 小于等于 2%、未充电且连续满足条件时，通过旧 `Soc_Exit_Manager` 自主发起 `LOW_BATTERY_SLEEP`；SOC 恢复到 3% 或开始充电时再取消。

两套状态机互不知道对方的完整状态。旧 2% 路径在 SoC 已进入 SLEEP 后可能再次输出约 8 秒 PA8 休眠脉冲；在 DEEP_SLEEP 已拉低 PA15 后，还可能调用 `Power_Set_Keep_On(POWER_KEEP_ON)`，使已经断电的 SoC 意外重新上电。这会与 WiFi/充电唤醒竞争，并破坏最低功耗目标。

因此，本次没有把 MCU 阈值从 2% 改成 5%，而是移除 MCU 的自主电量策略，使低功耗入口只有一个业务 owner。

## 职责决策

### SoC 应用负责

- 判断设备原始 SOC 是否小于等于 5%。
- 判断设备是否处于未充电状态。
- 将设备端 5%～100% 映射为 APP 端 0%～100%。
- 满足智能留电条件时下发 SLEEP/DEEP_SLEEP 控制。
- APP 远程唤醒后的业务恢复、声响和界面恢复。

### MCU 负责

- 上报电量计原始 SOC，不执行 5% 映射。
- 执行 SoC 下发的 SLEEP/DEEP_SLEEP 布防、PA8/PA15 时序和可靠通知。
- 处理 WiFi 唤醒和 PA7 充电接入唤醒。
- 尊重物理电源开关 OFF，不因充电接入强制给 SoC 上电。

### 兼容性边界

- 删除 `LOW_BATTERY_SOC_SLEEP_PERCENT`、`LOW_BATTERY_SOC_RECOVER_PERCENT`、启动宽限、确认计数、电压过滤和 `GD32L235_LOW_BATTERY_SOC_SLEEP_PROTECT`。
- 删除 `Low_Battery_SocSleep_Event()`、低电确认计数、低电休眠活跃状态及其在通用 `Soc_Exit_Manager` 中的特殊分支。
- 保留 `PROTOCOL_SHUTDOWN_REASON_LOW_BATTERY_SLEEP = 0x02`，避免破坏已有线协议枚举。
- 保留通用 `SOC_EXIT_ACTION_SLEEP_SOC_PA8`，因为 charge-cert profile 的认证休眠仍使用该动作。

## 充电唤醒实现

PA7 EXTI 中断只更新充电状态并锁存 `Wakeup_Charge_Flag`。主循环清除标志后，再次确认 `Charging_Flag == true` 且 `Charge_Get_Status() == CHARGE_DETECTED`，随后进入 `Wakeup_Handle_Charge()`；中断中不执行 PA8/PA15 或可靠协议状态机。

新增协议唤醒源：

```text
PROTOCOL_WAKEUP_SOURCE_CHARGE = 0x07
```

充电接入行为：

| SoC 状态或阶段 | MCU 行为 |
| --- | --- |
| RUNNING | 不驱动 PA8/PA15，报告 SoC 无需唤醒 |
| STANDBY | 不作为本次智能留电的充电唤醒目标，不驱动 PA8/PA15 |
| SLEEP | 撤销入口保护、关闭模块唤醒 EXTI，输出固定 9 ms PA8 并可靠上报 `CHARGE/FIRED` |
| DEEP_SLEEP `WAIT_ARM_ACK/WAIT_CUT` | 撤销待执行的 PA15 断电，保持 PA15 ON，输出 9 ms PA8 |
| DEEP_SLEEP `OFF_SETTLE` | 锁存 CHARGE，等待至少 100 ms OFF settle 完成后拉高 PA15 |
| DEEP_SLEEP `OFF_WAIT_WAKE` | 立即拉高 PA15并可靠上报 `CHARGE/FIRED` |
| DEEP_SLEEP `POWERING_ON` | 不重复操作 PA15 |
| 物理电源开关 OFF | 丢弃充电唤醒，不强制启动 SoC |

PA7 CHARGE 是 SLEEP/DEEP_SLEEP 的强制硬件唤醒源，不占用 `wake_mask` 中 WIFI/IMU/TOF 的三个位，也不受这三类模块 5 秒入口静默保护限制。

## 代码审查闭环

初始实现的 `Wakeup_Handle_Charge()` 缺少 SoC 状态门禁，因此正常 RUNNING 状态下插入充电桩也可能输出 PA8。提交前行为审查将其判定为 major，并补充以下约束：

- 只有 `PROTOCOL_SOC_STATE_SLEEP` 或 `PROTOCOL_SOC_STATE_DEEP_SLEEP` 才能进入充电唤醒动作。
- 状态门禁必须发生在设置 `s_wake_in_progress`、操作 PA15 或调用 `SOC_Wakeup()` 之前。
- 契约测试验证 RUNNING 不产生 PA8/PA15 动作。

修复后重新执行完整 Release 和 charge-cert 验证。

## 软件验证证据

### 正常 Release

执行目录：`workspace://gd32l235`

```text
rtk bash -lc "BUILD_DIR=build/codex-gcc-ninja scripts/codex-check.sh --full"
```

- 日期：2026-07-30
- 退出码：0
- 结果：全部仓库测试、Release 构建、package 和 `fwtool check --scope all` 通过。
- App Flash：45,508 / 51,200 bytes，88.88%。
- App RAM：14,392 / 24,576 bytes，58.56%。

### charge-cert profile

执行目录：`workspace://gd32l235`

```text
rtk python3 Tools/Firmware/fwtool.py build --generator ninja --build-dir build/codex-charge-cert --build-type Release --charge-cert-profile --fresh
rtk python3 Tools/Firmware/fwtool.py package --build-dir build/codex-charge-cert --output-dir build/codex-charge-cert/package --package-name gd32l235_charge_cert
rtk python3 Tools/Firmware/fwtool.py check --scope all --build-dir build/codex-charge-cert --package-dir build/codex-charge-cert/package --package-name gd32l235_charge_cert
```

- 日期：2026-07-30
- 退出码：0
- 结果：构建、package 和全范围检查通过。
- App Flash：48,304 / 51,200 bytes，94.34%。
- App RAM：14,408 / 24,576 bytes，58.63%。

### 定向和完成前门禁

```text
rtk python3 Tools/tests/check_charge_wakeup_contract.py
rtk python3 Tools/tests/check_wakeup_diagnostics.py
rtk git diff --check
rtk bash ~/codex/scripts/final-ready.sh
```

以上命令均通过。GD32 官方外设库的 `-Wtautological-compare` 仍是仓库 allowlist 内的既有警告，没有新增未知告警。

## 负向证据

首次在共享 `build/gcc-ninja` 运行完整门禁时，链接器已经报告正常 App 容量，但紧随其后的 `objcopy` 找不到 ELF。只读取证发现该目录同时被另一条 Debug UART/Wakeup Diag 构建重新配置：本次命令要求诊断开关为 OFF，而目录最终缓存和 `build_latest.log` 显示为 ON，且生成的 App 容量与本次日志不一致。

磁盘空间和 inode 正常，使用独立目录 `build/codex-gcc-ninja` 后完整门禁稳定通过。结论是共享构建目录并发写入，不是本次固件源码编译缺陷。后续并行 profile 验证必须使用不同 build-dir。

## Git 证据

- GD32L235 commit：`db7ccc5ccaa60abd6c695052abebe29ae8d90bd8`
- 提交标题：`feat(power): 支持充电唤醒并移除MCU低电休眠`
- 本次功能提交完成时已推送到 `gd32l235/origin/master`，当时本地 HEAD 与远端一致。
- 归档写入前复核：主线已继续前进到 `06f375a03d0133362dc366593f5a6da72647432e`（tag `v1.1.40`），`db7ccc5` 仍位于主线历史中；因此本文以 `db7ccc5` 作为本次功能实现证据，不将其表述为当前 HEAD。
- MCU 聚合仓 gitlink 本地 commit：`39e65cc4cf218481f1533703e85ceb9124e3ecf6`
- 聚合根仓没有配置 remote，因此 gitlink 提交未发布到远端。

## 板级 HIL 待验证

软件门禁不能替代以下硬件验收：

1. SLEEP 状态插入充电桩，只产生一次约 9 ms PA8，SoC 恢复正常运行、眼睛屏和业务功能。
2. DEEP_SLEEP 在 `WAIT_CUT`、`OFF_SETTLE` 和 `OFF_WAIT_WAKE` 三个阶段插入充电桩，分别验证撤销断电、满足 OFF settle 后上电和立即 PA15 上电。
3. RUNNING 和 STANDBY 插入充电桩不产生 PA8/PA15 误动作。
4. 物理开关 OFF 时插入充电桩不强制启动 SoC。
5. WiFi 与 CHARGE 近同时到达时只执行一次有效唤醒，可靠通知的 source/result 与实际动作一致。
6. 使用示波器或逻辑分析仪记录 PA7、PA8、PA15、UART 和 SoC 启动时序。

在上述 HIL 完成并由 owner 复核前，本条目保持 `reviewing`、`manual_validation_pending=true`，不得提升为 active 或硬件通过结论。

## 来源、时间与脱敏边界

- captured_at：2026-07-30（Asia/Hong_Kong）
- last_verified：2026-07-30
- source：`workspace://gd32l235` commit `db7ccc5ccaa60abd6c695052abebe29ae8d90bd8`
- related：`gd32l235-pcr02-power-transition-owner-tcpka-20260722`
- provenance：Codex 根据用户确认的职责边界、已提交源码、协议文档、契约测试和本地构建证据整理
- 未归档：原始串口日志、构建二进制、package ZIP、私有服务地址、token、凭证和完整聊天记录

## 当前状态与后续动作

- 当前状态：软件实现与自动化验证完成，板级 HIL 待完成。
- 本记录补充 2026-07-22 低功耗协同归档中的唤醒源矩阵：SLEEP/DEEP_SLEEP 现在除 WIFI 外还支持 CHARGE；不退役或覆盖该归档的其他结论。
- 下一步：按 HIL 清单形成统一时间基准的 GPIO/UART 波形与设备行为证据。
- HIL 通过后更新 `evidence_validation_status`，但 owner 复核前仍不得自动提升 active。

## Memory Candidate

`no`。本结论已落入项目 Knowledge Hub 归档，不写入 `~/.codex/memories`，也不自动修改 AGENTS、skill 或 workflow。
