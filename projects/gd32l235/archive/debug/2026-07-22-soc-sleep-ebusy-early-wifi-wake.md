---
id: gd32l235-soc-sleep-ebusy-early-wifi-wake-20260722
title: GD32L235 与 PCR02 SOC SLEEP EBUSY 和提前 WiFi 唤醒初步排查
kind: debug-record
domain: projects/gd32l235
path: projects/gd32l235/archive/debug/2026-07-22-soc-sleep-ebusy-early-wifi-wake.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: source-project-debug-note
  from: workspace://gd32l235/Docs/SOC休眠异常初步排查记录-20260722.md
  source_sha256: 8cc7f2455c9b4328dfcafca6f28e8efddf4b741c3e974ded9a6fa360b7409c2f
review_after: '2026-08-22'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- gd32l235
- pcr02
- sleep
- wifi-wakeup
- needs-fix
related:
- projects/gd32l235/current/soc-low-power-contract.md
- projects/gd32l235/archive/design/2026-07-22-soc-mcu-power-transition-owner-tcpka.md
validation_refs:
- projects/gd32l235/archive/debug/2026-07-22-soc-sleep-ebusy-early-wifi-wake.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/gd32l235/archive/debug/2026-07-22-soc-sleep-ebusy-early-wifi-wake.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-07-22'
captured_at: '2026-07-22'
updated_at: '2026-07-22'
generated_by_ai: true
ai_role: summarized
ai_model_or_tool: Codex
ai_generated_at: '2026-07-22'
manual_validation_pending: true
summary_zh: 记录 SOC SLEEP 写 power state 返回 EBUSY，以及成功休眠后数秒被 MCU WiFi FIRED 提前唤醒的两个独立现象、排查优先级和下一轮联合取证要求；根因尚未确认。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
---

# SOC 休眠异常初步排查记录（2026-07-22）

## 归档说明

- 本文是 2026-07-22 的现场初步排障记录，状态为 `reviewing/needs-fix`；两个现象均未形成根因结论。
- 原始长日志不进入长期正文；后续只追加去敏后的关键时间线、计数器和验证结论。
- 当前低功耗状态与唤醒源契约见[当前低功耗协同契约候选](../../current/soc-low-power-contract.md)，完整设计背景见[电源转换与 TCPKA 归档](../design/2026-07-22-soc-mcu-power-transition-owner-tcpka.md)。
- Review：owner `leiwenjun`；复审日期 2026-08-22；在内核 PM、TCPKA、MCU IRQ 与 PA8 波形对齐前不得提升状态。

## 1. 影响范围与环境

本文只记录两次现场现象、已经确认的事实和初步假设，不保存整段 raw log，不作为根因结论或修复完成证明。

- 状态：`needs-fix`
- 根因状态：未确认
- 共同场景：SOC 请求 `SLEEP`，使用 SOC RTC 定时唤醒，并启用 MCU WiFi/TCP keepalive 唤醒
- 当前原则：两个现象分别建模；只有获得内核 PM、TCPKA 和 MCU 同时序证据后，才判断是否存在共同根因

### 1.1 时间线

- 18:34：写 `/sys/power/state` 返回 `EBUSY`，未进入 SLEEP，随后执行失败回滚。
- 19:55：SOC 真实进入 SLEEP，但约 7 秒后收到 MCU `WIFI/FIRED` 并 resume，早于 180 秒 RTC。

## 2. 现象一：写 `/sys/power/state` 返回 `EBUSY`

### 2.1 基线

- 时间：2026-07-22 18:34
- 配置：`SLEEP`，SOC RTC 为 120 秒，并启用测试 TCP keepalive 服务
- SOC 已完成 IMU/TOF stop、辅助状态同步和 TCPKA arm
- 写 `/sys/power/state` 失败：`errno=16 (Device or resource busy)`
- 随后 IMU/TOF 被重新启动，低功耗事务返回 `suspend_ret=-1`
- HDI 读取到 `hdi_source=2`，对应 IO0；MCU 没有确认 `FIRED`，记录为 `mcu_source=255, mcu_result=2`

### 2.2 已确认判断

- SOC 没有成功进入 SLEEP；传感器重新启动属于失败回滚，不是正常 RTC resume。
- 120 秒 RTC 没有到期，可以排除“RTC 正常唤醒”。
- suspend 失败后读取到的 IO0 可能是 pending 或历史状态，不能单独证明本次由 MCU 唤醒。

### 2.3 初步假设

| 假设 | 排查优先级 | 当前依据 | 待验证证据 |
| --- | --- | --- | --- |
| RTSA/Agora/WiFi 活跃流量形成 kernel pending wakeup | 高 | 休眠窗口仍有 RTC stats、关键帧和 APP connected 日志 | `dmesg`、`wakeup_sources`、WiFi wakeup event 计数 |
| 另一个 PM transition 或 autosleep 占用 | 中 | 内核的 transition mutex/autosleep 路径可返回 `EBUSY` | `/sys/power/autosleep`、同时写 state 的进程 |
| 设备 suspend callback 或 freezer 返回 `EBUSY` | 中 | 音视频、WiFi 和 motion 仍活跃 | `dmesg` 中 failed device/freezer 记录、`suspend_stats` |
| IO0/MCU 瞬态或旧事件干扰 | 低 | HDI 显示 IO0，但 MCU 无 `FIRED` | GD32 `WAKE_ARM/WAKE_FIRE` 与 IO0/PA8 波形 |

## 3. 现象二：SLEEP 后数秒内真实 resume

### 3.1 基线

- 时间：2026-07-22 19:55
- 配置：`SLEEP`，SOC RTC 为 180 秒，同一 TCP keepalive 目标
- 底层输出 `Resume`、DDR resume 等启动信息，说明 SOC 真实进入并退出了 suspend
- 从触发到应用恢复约 7 秒，明显早于 180 秒 RTC
- SOC 收到 `MCU wake result: source=1, result=0`；当前协议中分别对应 `WIFI` 和 `FIRED`

### 3.2 已确认判断

- 该现象与现象一不同：本次不是写 state 失败，而是成功休眠后被提前唤醒。
- RTC 尚未到期，可以排除“RTC 正常到期”。
- MCU 上报了 WiFi `FIRED`，但仍需区分真实新边沿、布防前高电平、残留 EXTI pending 和延迟可靠消息。

### 3.3 初步假设

| 假设 | 排查优先级 | 当前依据 | 待验证证据 |
| --- | --- | --- | --- |
| TCPKA arm 后立即收到服务端数据、连接异常或被配置为 wake 的网络事件 | 高 | `Tcpka: armed` 后数秒即 resume，MCU 上报 WiFi `FIRED` | TCPKA wake reason、服务端收发记录、GD32 WiFi IRQ 时间 |
| WiFi wake GPIO 在布防前已高或残留 EXTI pending | 高 | 当前旧日志无法观察布防瞬间 raw/pending | GD32 `WAKE_ARM raw/pending` 和 `WAKE_FIRE edge_t/raw/pending` |
| 旧的可靠 `0x07(WIFI, FIRED)` 延迟上报 | 中 | `0x07` 会可靠重试，但它本身不能解释物理 resume | `CMD+SEQ`、MCU edge count、PA8 波形和 SOC ACK 时间 |

## 4. 两个现象的关系

当前不能合并为一个根因：

```text
现象一：SOC 未进入 SLEEP，内核返回 EBUSY
现象二：SOC 成功进入 SLEEP，随后由某个物理事件 resume
```

WiFi/网络活动可能同时参与两个现象，但这仍是待验证的共同假设。

## 5. GD32 新增取证日志

本次仅增强诊断，不改变唤醒策略、PA8 脉冲宽度或 UART 协议：

```text
WAKE_ARM t=... state=2 policy=0x01 rev=... raw=0x.. pending=0x..
WAKE_FIRE t=... src=wifi soc_state=2 policy=0x01 count=... edge_t=... raw=... pending=...
SOC_WAKE t=... count=... duration=...
```

- `WAKE_ARM` 的 `raw/pending` 在 MCU 清 EXTI pending、应用唤醒 mask 前采集。
- bit0/bit1/bit2 依次表示 WiFi/IMU/ToF。
- ISR 只记录 `edge_t/raw/pending/count`，不执行 `printf`。
- `WAKE_FIRE` 在主循环输出最近一次 IRQ 快照，可判断 WiFi 是否产生了新的有效边沿。

## 6. 根因

尚未确认。现象一是 suspend entry 失败，现象二是成功 suspend 后的提前 resume；当前证据不足以证明二者同源。

## 7. 修复或规避

- 已落地 MCU 诊断增强：布防时记录 `WAKE_ARM raw/pending`，触发时记录 `WAKE_FIRE count/edge_t/raw/pending`，ISR 只采样不打印。
- 在根因确认前不修改 WiFi 唤醒策略、不屏蔽物理唤醒源，也不把 IO0 的单次读数直接认定为本次 wake source。

## 8. 验证

- `rtk python3 Tools/tests/check_wakeup_diagnostics.py`：通过，确认压缩日志字段和 ISR 无格式化输出。
- MCU/SOC 软件最小构建与静态检查已覆盖协议改动；真实 SLEEP、TCPKA、PA8 波形和 RTC 到期行为仍待 HIL 联合验证。

## 9. Review

- Owner：`leiwenjun`
- Review after：2026-08-22
- 状态提升门禁：两个现象分别得到可复现步骤、同一时基证据和明确根因；否则保持 `reviewing/needs-fix`。

## 10. 后续动作

SOC 侧在每次写 `/sys/power/state` 前后采集：

```text
/sys/power/autosleep
/sys/kernel/debug/wakeup_sources
/sys/power/suspend_stats
dmesg 中本次 suspend entry/abort/resume 窗口
```

MCU 侧对齐：

```text
WAKE_ARM
WAKE_FIRE
SOC_WAKE
0x05 ARMED、0x07 FIRED 的 CMD/SEQ/ACK 时间
```

TCPKA/服务端侧对齐 arm 后首个 RX、FIN、RST、timeout 和 wake reason。若 `WAKE_ARM` 已显示 WiFi `raw=1` 或 `pending=1`，优先处理布防前状态；否则优先检查 arm 后的新网络事件。
