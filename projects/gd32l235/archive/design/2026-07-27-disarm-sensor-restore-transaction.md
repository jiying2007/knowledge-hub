---
captured_at: '2026-07-27'
last_verified: '2026-07-27'
related:
- projects/gd32l235/current/soc-low-power-contract.md
- projects/gd32l235/archive/design/2026-07-22-soc-mcu-power-transition-owner-tcpka.md
- projects/gd32l235/archive/debug/2026-07-22-soc-sleep-ebusy-early-wifi-wake.md
id: gd32l235-pcr02-disarm-sensor-restore-validation-20260727
title: GD32L235 与 PCR02 SoC DISARM 和传感器恢复事务归档
kind: project-archive
domain: projects/gd32l235
path: projects/gd32l235/archive/design/2026-07-27-disarm-sensor-restore-transaction.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: working-tree-implementation-and-local-validation
  from: workspace://gd32l235 and workspace://pcr02-ssc305 source diffs plus local validation captured 2026-07-27
  source_sha256: a7f6cfe732fa63863e10ebaa3c38dd8ddea6ec54cd6fa437fff73d468d0a977c
  temporary_source_retained: false
review_after: '2026-08-27'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- gd32l235
- pcr02
- low-power
- disarm
- sensor-restore
- imu
- tof
- hil-pending
- needs-fix
validation_refs:
- projects/gd32l235/archive/design/2026-07-27-disarm-sensor-restore-transaction.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/gd32l235/archive/design/2026-07-27-disarm-sensor-restore-transaction.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-07-27'
updated_at: '2026-07-27'
generated_by_ai: true
ai_role: summarized
ai_model_or_tool: Codex
ai_generated_at: '2026-07-27'
manual_validation_pending: true
summary_zh: 归档 GD32L235 与 PCR02 SoC 的 DISARM 同步屏障、IMU/ToF 恢复事务、Sensor worker 假恢复根因与修复、双端软件验证及仍待 DHD、格式工具和 HIL 闭环的风险。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
---

# GD32L235 与 PCR02 SoC DISARM 和传感器恢复事务归档

## 摘要

本记录归档 2026-07-27 在 GD32L235 MCU 与 PCR02 SoC 工作树完成的低功耗恢复事务优化：把 `0x04/0x00` 从保留的 `INVALID` 改为幂等 `DISARM`；SoC 在恢复 IMU/ToF 前必须先取得 MCU 命令 ACK；只有 MCU 已撤销布防且两个传感器均恢复运行后，SoC 才同步 RUNNING 快照。

提交前审查还发现并修复了一项传感器生命周期缺陷：底层 `stop()` 失败时 worker 已退出但状态可能仍为 `START`，旧 `start()` 会返回成功却不重建 worker。修复后 `START && !m_running` 独立触发 worker 重建，并由静态回归断言保护。

MCU 完整构建、SoC app/sensor 模块构建和定向回归通过；DHD 内核综合低功耗门禁、clang-format 工具兼容和板级 HIL 尚未闭环。因此本条目保持 `reviewing`，不是 release-ready、active 规范或硬件验收结论。

## 归档边界

- 当前状态与权威入口仍是 `projects/gd32l235/current/soc-low-power-contract.md`、MCU/SoC 当前源码和 MCU 串口协议规范。
- 本文记录一次未提交工作树上的设计、修复和本地验证批次，只作 project archive。
- 不保存完整串口日志、私有网络 endpoint、UID、凭证、cache、二进制或构建产物。
- 本文不代替 Git commit identity、owner 签收、板级测试、发布 manifest 或回滚验收。

## 状态契约与非目标

四状态语义保持不变：

| SoC 状态 | IMU | ToF | 主要唤醒源 |
| --- | --- | --- | --- |
| RUNNING | ACTIVE | ACTIVE | 无需 MCU 唤醒 |
| STANDBY | WAKE_ARMED | WAKE_ARMED | MCU WiFi、IMU、ToF |
| SLEEP | OFF | OFF | MCU WiFi、SoC RTC |
| DEEP_SLEEP | OFF | OFF | MCU WiFi，随后 MCU 给 SoC 重新上电 |

本轮不改变固定 9 ms PA8 脉冲，也不改变 5 秒全局低功耗入口保护：

```c
#define WAKEUP_ENTRY_GUARD_MS 5000U
```

## `0x04/0x00 DISARM` 同步屏障

旧协议把 `0x04 mode=0x00` 视为 `INVALID`。新契约不保留该兼容语义：

```text
0x04 / 0x00 = DISARM
0x04 / 0x01 = STANDBY
0x04 / 0x02 = SLEEP
0x04 / 0x03 = DEEP_SLEEP
```

MCU 收到 DISARM 后，在返回命令 ACK 前完成：

1. 将 applied SoC state 收敛为 RUNNING；
2. 清除 applied wake mask 和 wake-in-progress；
3. 清除 5 秒入口保护；
4. 取消待执行的 DEEP_SLEEP 断电阶段和 deadline；
5. 清除锁存唤醒源；
6. 关闭 WiFi/IMU/ToF 唤醒 EXTI；
7. 若 DEEP_SLEEP 断电事务尚未结束，恢复 SoC keep-on。

SoC 把该 ACK 当作恢复屏障：

```text
低功耗返回、过渡期唤醒或 suspend 失败
  -> 发送 DISARM 并等待 ACK
  -> 确认/等待 wake source
  -> 恢复 IMU/ToF
  -> 两个传感器都运行后同步 RUNNING
```

DISARM 失败时不得恢复连续采样，也不得向 MCU 同步虚假的 `RUNNING + ACTIVE/ACTIVE/ACTIVE` 快照。

## IMU/ToF 恢复和一次自愈

正常恢复按原进入方式选择：

- STANDBY：`resume()`；
- SLEEP：`start()`。

首次恢复失败时允许一次有界 `stop() + start()` 自愈。两个传感器分别记录结果，只有 `imu && tof` 为真时才允许同步 RUNNING。

### worker 假恢复根因

`SensorDevBase::stopImpl()` 会先执行 `stopWorkerAndJoin()`，再调用底层 `doStop()`。若 `doStop()` 失败：

- worker 已退出；
- `m_running == false`；
- `m_currentState` 可能仍为 `START`。

旧 `start()` 只在 `INIT/STOP` 状态分支内启动 worker。当状态仍为 `START` 时，它会直接返回成功，但没有重新创建采集线程。

修复把硬件状态转换和 worker 存活不变量拆开：

```cpp
if (m_currentState == SensorDevState::INIT
    || m_currentState == SensorDevState::STOP) {
    m_targetState = SensorDevState::START;
    doStart();
}

if (m_currentState == SensorDevState::START
    && !m_running.load(std::memory_order_acquire)) {
    if (!startWorkerLocked()) {
        m_targetState = SensorDevState::STOP;
        doStop();
        return false;
    }
}
```

因此，失败的 stop transition 不再产生“返回成功但采集线程未运行”的假恢复。

## 默认日志和性能边界

以下高频诊断默认关闭，并且不与 `GD32L235_CHARGE_CERT_PROFILE` 联动：

```c
#define BSP_CHARGE_DIAG_LOG_ENABLED 0
#define CHARGE_DIAG_LOG_ENABLED     0
#define WAKEUP_DIAG_LOG_ENABLED     0
```

运行态 ToF 15 Hz data-ready 不应转换为 PA8 唤醒。MCU 仅按限频策略记录 `WAKE_DROP`，真正执行唤醒时记录紧凑的 `WAKE_FIRE` 和 `SOC_WAKE`。

## 验证证据

### MCU

命令：

```text
rtk bash scripts/codex-check.sh --full
```

结果：

- 静态契约检查通过；
- Stage0、Stage1、App 全量构建通过；
- package/check 通过；
- App FLASH：45,652 / 51,200 bytes（89.16%）；
- App RAM：14,392 / 24,576 bytes（58.56%）；
- 只有既有供应商 `gd32l23x_rcu.c` 的 allowlisted warning。

### SoC

命令和结果：

| 命令 | 退出码 | 结果 |
| --- | ---: | --- |
| `rtk make modules/app_obj_all -j20` | 0 | app 模块通过 |
| `rtk make NC=1 modules/sensor_obj_all -j20` | 0 | sensor 模块通过 |
| MCU/app/sensor `rtk git diff --check` | 0 | 通过 |
| 两份 `app_uart_packet.h` 比较 | 0 | 完全一致 |
| Sensor worker 恢复定向断言 | 0 | 通过 |
| `rtk bash ~/codex/scripts/final-ready.sh` | 0 | 通过 |

回归断言先在旧结构上得到：

```text
sensor start: worker recovery must be independent of the INIT/STOP hardware transition
```

修复后该失败项消失，证明门禁能够覆盖本次根因。

## 负向证据与未闭环项

### DHD 综合低功耗门禁

`rtk python3 build/check_soc_low_power_flow.py` 仍失败于三个当前内核基线条件：

1. `dhd_pm_callback` 缺少 `CONFIG_HAS_WAKELOCK/BCMSDIO` 条件分支；
2. 缺少无 wakelock 且启用 BCMSDIO 的对应分支；
3. wake-lock waive 缺少 `dhd_bus_dev_pm_relax(pub)`。

DISARM、恢复顺序和 Sensor worker 回归没有再失败。该结果只能说明本轮应用/传感器修复通过定向门禁，不能声明 SoC 整体 suspend 链已经通过。

### 格式工具

当前 clang-format 13 不支持顶层 `.clang-format` 的：

```yaml
SpaceBeforeParens: Custom
```

因此 sensor 只能用 `NC=1` 完成编译，格式门禁尚未得到有效证据。

### HIL

尚未完成：

- STANDBY 下 IMU/ToF 分别唤醒；
- 5 秒保护期内边沿不唤醒；
- 唤醒后 DISARM、wake-source、传感器恢复和 RUNNING 同步的同一时基证据；
- SLEEP 的 RTC/WiFi 唤醒；
- suspend 失败和 wakeup_count 变化时回滚；
- PA8/PA15 波形；
- MCU/SoC 不同版本组合的安全失败。

## 兼容、部署与回退

`0x04/0x00 INVALID -> DISARM` 是有意的不兼容协议变更：

- MCU 和 SoC 必须同批部署；
- 新 SoC 遇到旧 MCU 时，DISARM 会失败，SoC 必须保持传感器未恢复并拒绝同步 RUNNING；
- 回退必须同时回退 MCU 与 SoC，不能单边回退；
- 该安全失败设计不等于混合版本已经通过实机测试。

## 工作树和提交边界

本次验证时的源码身份：

| 仓库 | 分支 | HEAD |
| --- | --- | --- |
| GD32L235 MCU | `master` | `6fd343d` |
| SoC `modules/app` | `master` | `912429a` |
| SoC `modules/sensor` | `master` | `9f5a5aa` |
| SoC 顶层 | `dev/pcr02` | 以当前工作树为准 |

所有实现仍是未提交工作树改动，未执行 commit、push、merge、tag 或发布。MCU 版本号和充电高温阈值属于独立改动，不应混入低功耗协议提交；SoC 顶层也包含其他源码与生成库变更，只允许按明确路径暂存。

## 后续动作

1. 明确 MCU 提交目标是 `master` 还是本地 `dev/low_power`，再进行路径级暂存。
2. 修复或明确 DHD 三项内核门禁。
3. 使用兼容项目配置的 clang-format 完成 sensor 格式验证。
4. 按 STANDBY/SLEEP/DEEP_SLEEP HIL 矩阵采集同一时基的 MCU、SoC、GPIO 和电源证据。
5. MCU/SoC 同批提交和部署，记录精确 commit、固件/应用 BuildID 或 hash。
6. HIL 和 owner 复核前保持 `reviewing + manual_validation_pending`，不得提升 active 或声明 release-ready。

## Provenance 与脱敏

- Source：当前会话确认的设计目标、MCU/SoC 工作树源码差异和本地验证命令。
- captured_at：2026-07-27（Asia/Hong_Kong）。
- last_verified：2026-07-27。
- 未归档：完整聊天、原始串口日志、网络 endpoint、设备标识、token、凭证、cache、binary 和构建产物。
- Memory candidate：no；本记录不静默写入 Codex memory 或 AGENTS。

## Review

- Owner：`leiwenjun`
- Review after：2026-08-27
- Promotion：none
- 状态提升门禁：DHD 门禁、格式工具、四状态 HIL、双端精确提交身份和回退验证全部闭环。
