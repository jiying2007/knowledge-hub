---
aliases:
- PCR02 SoC SLEEP 网络冻结与 wakeup_count 两阶段门禁决策候选
related:
- projects/gd32l235/README.md
- indexes/obsidian-home.md
- indexes/project-readiness.md
id: gd32l235-pcr02-soc-sleep-network-freezer-wakeup-count-20260724
title: PCR02 SoC SLEEP 网络冻结与 wakeup_count 两阶段门禁决策候选
kind: decision
domain: projects/gd32l235
path: projects/gd32l235/decisions/soc-sleep-network-freezer-wakeup-count.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: working-tree-implementation-and-local-validation
  from: PCR02 sensor/HDI working-tree diffs, Linux 5.10 PM source, bcmdhd.ko symbols and local build evidence captured 2026-07-24
  source_sha256: 70236024be933ffb7696d0e3bd4b7e1fceafe8d9f44a628936d1971ca850ed0c
  temporary_source_retained: false
review_after: '2026-08-24'
review_status: human-reviewed-accepted
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- gd32l235
- pcr02
- sleep
- wifi
- tcpka
- wakeup-count
- kernel-freezer
- hil-pending
validation_refs:
- projects/gd32l235/decisions/soc-sleep-network-freezer-wakeup-count.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/gd32l235/decisions/soc-sleep-network-freezer-wakeup-count.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-07-24'
updated_at: '2026-07-26'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-07-24'
manual_validation_pending: true
summary_zh: 归档在 task、iot、AI、navigation、Agora 不改动约束下，将 WLAN TX 从休眠硬门禁降为诊断，并由 Linux freezer、bcmdhd suspend 与 wakeup_count 两阶段提交共同保证
  SLEEP 转换；软件构建通过，板级 HIL 待验证。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
---

# PCR02 SoC SLEEP 网络冻结与 wakeup_count 两阶段门禁决策候选

## 结论

在 `task`、`iot`、`AI`、`navigation`、Agora 暂不修改的约束下，不再把 `wlan0/statistics/tx_bytes` 是否持续增长作为 SoC 进入 SLEEP 的硬门禁。普通业务流量可能一直存在，等待全局 TX 静默会把正常运行误判为不能休眠。

最终采用分层职责：

1. sensor 的 `MediaFlowGate` 只停止本模块可控的音视频生产并排空本地 in-flight，不宣称冻结所有应用网络。
2. TCPKA 必须配置和 arm 成功；RTC、IMU/ToF、MCU wake policy 仍按既有事务顺序准备。
3. Linux suspend freezer 负责冻结未修改的用户进程；`bcmdhd` 的 PM notifier 在 freezer 前停止主机 TX 队列并切换 WiFi offload/WoWLAN 状态，同时必须把已有的 BCMSDIO device wakeup-source hold 保持 relaxed 到 `PM_POST_SUSPEND`。
4. HDI 使用 `/sys/power/wakeup_count` 两阶段 token：TCPKA、RTC、传感器和 MCU arm 准备完成后读取，最后一次队列唤醒检查后提交同一值并立即写 `/sys/power/state=mem`。最终提交窗口内发生的新 wake event 会使提交失败并触发完整回滚。
5. WLAN TX 计数只保留一条紧凑诊断，不参与准入判断。

这是一个 `reviewing` 决策候选。软件静态检查、交叉编译和最终链接已通过；真实 SLEEP、WiFi keepalive/RTC 唤醒与竞争回滚仍需板级 HIL，本文不把本地构建等同于硬件验收。

## 背景

旧实现为规避 TCPKA arm 后的提前 WiFi 唤醒，在低功耗路径三次调用 WLAN TX 静默检查。每次最长等待 1500 ms，并要求连续 250 ms 不增长：

- media flow drain 后；
- TCPKA arm 后；
- MCU arm 前。

当 MQTT、Agora、导航或其他网络线程保持工作时，`tx_bytes` 持续增长是正常现象。这套策略最多增加约 4.5 秒准备时间，最终仍可能以“WLAN TX stayed active”拒绝 SLEEP。它无法区分可丢弃的遥测、必须 offload 的 TCPKA 和内核正在处理的真实 wake source，也不是可靠的全局网络事务。

## 约束与非目标

约束：

- 本轮不修改 `task`、`iot`、`AI`、`navigation`、Agora。
- 不修改 TCPKA UART/MCU 协议。
- 不关闭 `wlan0`，不使用全局 iptables 黑洞，不强制忽略内核 suspend 错误。
- 保留用户已有的 sensor、HDI 和应用工作树改动。

非目标：

- 不保证普通 MQTT、Agora 或导航 socket 在 SLEEP 前后无丢包、无超时、无重连。
- 不伪造“所有业务已经 quiesce”的应用层 ACK。
- 不把 WiFi GPIO 的每个事件都当成 TCPKA 业务语义；唤醒原因仍需 MCU/驱动/服务端联合取证。

## 设计依据

### Linux suspend 顺序

本地 Linux 5.10 源码的 `enter_state()` 先执行 `suspend_prepare()` 冻结用户进程，再进入 `suspend_devices_and_enter()` suspend 设备。`/sys/power/wakeup_count` 的内核注释明确规定：

1. 用户态读取并保存 count；
2. 完成用户态准备；
3. 写回相同 count；
4. 写回失败表示期间出现 wake event，不应写 power state；
5. 写回成功后发生的新 wake event 由内核中止 suspend。

因此 `wakeup_count` 是休眠竞争门禁，`tx_bytes` 只是流量观测。本项目把 token
读取点放在 TCPKA、RTC、传感器和 MCU arm 准备完成之后：准备阶段由本次休眠事务
主动产生并已经处理完的网络或设备事件不应否决休眠；读取之后仍由 queued MCU
wake 检查和内核 count 比较共同覆盖最终竞态。

### bcmdhd SDIO wakeup-source

目标内核配置为 `CONFIG_BCMDHD_SDIO=y`，未启用旧
`CONFIG_HAS_WAKELOCK`。源码直接表明：

- `dhd_pm_callback()` 注册为 PM notifier，在 `freeze_processes()` 之前执行；
- `dhd_os_wake_lock()` 的 BCMSDIO 路径最终对 SDIO device 调用
  `pm_stay_awake()`，内核中对应名称为 `mmc1:0001:2`；
- 原 `dhd_os_wake_lock_waive()` 只设置 `waive_wakelock`，没有 relax
  已经 active 的 SDIO wakeup source；
- 原 suspend notifier 在返回前立即 restore，导致 freezer 看到
  `mmc1:0001:2` active 并以 `EBUSY` 中止。

驱动修复仅作用于 BCMSDIO/no-legacy-wakelock 路径：waive 时对已有
device hold 执行 `pm_relax()`，保持 waived 到 `PM_POST_SUSPEND`，然后
按逻辑 `wakelock_counter` 决定是否重新 `pm_stay_awake()`。OOB、RTC 和
MCU 唤醒路径不被绕过。

## 实现

### HDI 两阶段接口

旧的单步接口：

```c
VSHDIOS_Suspend();
```

替换为不保留旧兼容的两阶段接口：

```c
VSHDIOS_PrepareSuspend(&suspend_wakeup_count);
VSHDIOS_CommitSuspend(suspend_wakeup_count);
```

`PrepareSuspend` 从 `/sys/power/wakeup_count` 读取并校验 32 位十进制 token。`CommitSuspend` 先写回 token，只有内核接受后才写 `/sys/power/state=mem`。任一步失败都返回 `VS_FAILURE`，由 sensor 统一执行 RTC、TCPKA、IMU/ToF 和 MCU RUNNING profile 回滚。

该接口有意 fail-closed：目标 Linux 5.10 已提供 `wakeup_count`，缺失、格式异常或竞争变化都不进入 SLEEP。

### sensor 网络策略

删除三次 `waitForWifiTxQuiet()` 及 1500 ms timeout/250 ms quiet window。低功耗准备开始时只读取一次 TX baseline，MCU arm 前读取当前值并输出：

```text
SOC_SLEEP_NET phase=pre_mcu_arm active=... tx_delta=... reset=... gate=kernel_freezer
```

计数器缺失时输出：

```text
SOC_SLEEP_NET phase=pre_mcu_arm counter=unavailable gate=kernel_freezer
```

两种情况均继续转换；真正硬门禁是 TCPKA/RTC/传感器/MCU 的返回值、queued wake check、`wakeup_count` 提交和内核 device suspend。

### bcmdhd notifier 策略

`PM_SUSPEND_PREPARE` 执行 WiFi suspend/offload 设置后，不再立即恢复
BCMSDIO device wakeup-source hold；无论真正 resume 还是 suspend abort，
`PM_POST_SUSPEND` 都会恢复逻辑 wakelock 状态。这样 freezer 可以停止仍在
运行的用户线程，同时不要求 sensor 猜测所有 socket 是否已经静默。

### 时序

```text
MediaFlowGate quiesce
  -> clear stale RTC
  -> arm TCPKA when configured
  -> arm SoC RTC when requested
  -> prepare IMU/ToF
  -> log WLAN TX activity (diagnostic only)
  -> MCU arm ACK
  -> read latest wakeup_count token
  -> consume queued MCU wake
  -> commit wakeup_count token
  -> write mem
  -> bcmdhd PM notifier: stop host TX / configure offload / relax SDIO hold
  -> kernel freezer
  -> device suspend
  -> PM_POST_SUSPEND: restore logical SDIO wake hold
```

若 MCU 已上报 `FIRED`，在 commit 前中止并返回来源；若 kernel token 变化或写 `mem` 失败，执行既有完整回滚。

## 变更位置

- `workspace://pcr02-ssc305/modules/sensor/main/sensor_entry.cpp`
- `workspace://pcr02-ssc305/modules/hdi/include/hdi_os.h`
- `workspace://pcr02-ssc305/modules/hdi/src/hdi_os/hdi_os_exec.c`
- `workspace://pcr02-ssc305/include/hdi/hdi_os.h`
- `workspace://pcr02-ssc305/build/check_soc_low_power_flow.py`
- `workspace://pcr02-ssc305/kernel/drivers/net/wireless/bcmdhd/dhd_linux.c`

MCU 本轮没有新增协议或行为改动；继续使用此前已经落地的 arm boundary、queued wake result 和紧凑 `WAKE_DROP/WAKE_FIRE/SOC_WAKE` 机制。

## 软件验证证据

负向回归先证明旧实现不满足新契约：

```text
rtk python3 build/check_soc_low_power_flow.py
[FAIL] missing PrepareSuspend/CommitSuspend
[FAIL] ordinary WLAN traffic must be diagnostic-only
```

实现后以下检查通过：

```text
rtk python3 build/check_soc_low_power_flow.py
rtk bash build/check_public_headers.sh
rtk make modules/hdi_obj_all -j20
rtk make modules/sensor_obj_all -j20
rtk make modules/hdi_lib_all -j20
rtk make modules/sensor_lib_all -j20
rtk make pcr02_app_all -j20 NC=1
rtk make ARCH=arm CROSS_COMPILE=arm-linux-gnueabihf-sigmastar-11.1.0- \
  M=drivers/net/wireless/bcmdhd modules -j20
rtk git diff --check
```

动态库符号核对：

```text
libhdi.so: VSHDIOS_PrepareSuspend, VSHDIOS_CommitSuspend 已导出
libsensor.so: 对两个新符号的引用存在且最终应用链接成功
```

## 板级 HIL 已获得的证据

首次板测把 token 放在设备准备之前读取。后续 TCPKA arm、IMU/ToF stop 和 WLAN
流量使内核 wakeup event count 发生变化，最终写回旧 token 返回
`EINVAL`。同一次测试同时确认：

- WLAN TX 增长只输出 `SOC_SLEEP_NET` 诊断，没有再次成为硬门禁；
- TCPKA 和 MCU profile 已成功 arm；
- token 提交失败后，TCPKA、IMU/ToF 和 MCU RUNNING profile 均完成回滚；
- 失败根因是 token 读取范围过宽，而不是 TCPKA 或 MCU 拒绝休眠。

修复后静态门禁明确要求：

```text
MCU arm ACK
  -> read latest wakeup_count
  -> consume queued MCU wake
  -> commit wakeup_count
```

第二次板测确认晚读取 token 已生效：`wakeup_count` 提交成功并进入
`PM: suspend entry (deep)`。随后 bcmdhd PM notifier 完成 TX queue stop 和
offload 设置，但 freezer 立即因 `Last active Wakeup Source:
mmc1:0001:2` 中止，`/sys/power/state` 返回 `EBUSY`。这条负向证据把剩余
失败收敛到 BCMSDIO device wakeup-source waiver，而不是 token、TCPKA、
MCU arm 或传感器准备。

## 板级 HIL 待验证

1. 刷入新 `bcmdhd.ko` 后，普通网络业务仍有周期流量时能够通过 freezer 并真正进入 SLEEP；不得再次出现 `Last active Wakeup Source: mmc1:0001:2` 的准备阶段 abort。
2. 从 SLEEP 请求到 `suspend entry` 的准备时延不再包含三段 quiet wait；记录 `SOC_SLEEP_NET`、MCU arm、kernel suspend 的同一时基。
3. 持续制造 WiFi 或 RTC wake event，验证 `wakeup_count` 竞争时 commit 失败并完整恢复 TCPKA、RTC、IMU/ToF 和 MCU RUNNING profile。
4. TCPKA 正常时，WiFi keepalive 能唤醒并上报 `WIFI/FIRED`；无网络事件时由 SoC RTC 在设定时间唤醒。
5. suspend/resume 后普通业务允许重连，但不得出现永久断网、WiFi suspend mode 未 disarm 或重复 wake storm。
6. 采集 `dmesg`、`/sys/kernel/debug/wakeup_sources`、`/sys/power/suspend_stats` 与 MCU `WAKE_FIRE/SOC_WAKE`，区分用户态回滚、设备 suspend 失败和真实 resume。

## 风险与回滚

- 普通应用未显式 quiesce，冻结瞬间可能有 socket 数据尚未获得应用层确认；这属于本约束下接受的 at-most-reconnect 语义。
- `wakeup_count` 读取会等待当前 active wakeup source 收敛；这是内核安全门禁，不应被强制绕过。若现场长期停在读取阶段，应定位具体 wakeup source，而不是恢复全局 `tx_bytes` 门禁。
- bcmdhd 修复改变 PM notifier 生命周期，必须验证成功 suspend/resume、freezer abort 回滚、WiFi 重连和 TCPKA 唤醒；模块编译通过不能替代板级验证。
- 回滚时可恢复旧的单步 HDI API和 sensor 调用，但不应恢复三次全局 WLAN quiet hard gate；若需要更强业务一致性，应由上层未来增加显式 `NetworkGate`/module ACK。

## 来源、时间与边界

- captured_at：2026-07-24（Asia/Hong_Kong）
- last_verified：2026-07-24
- source：PCR02 sensor/HDI 与 bcmdhd 未提交工作树、本地 Linux 5.10 PM 源码、本地构建输出及脱敏板测结论
- related：
  - `projects/gd32l235/archive/debug/2026-07-22-soc-sleep-ebusy-early-wifi-wake.md`
  - `projects/gd32l235/archive/design/2026-07-22-soc-mcu-power-transition-owner-tcpka.md`
  - `projects/gd32l235/current/soc-low-power-contract.md`
- 排除：原始串口长日志、设备 SN、私有 IP/endpoint、token、凭证和二进制制品均未复制进正文
- Git 边界：相关工作树含用户已有未提交修改；本文不对应已提交 commit，不声明可发布或已通过板级验收
