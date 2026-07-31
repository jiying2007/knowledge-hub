---
id: pcr02-deep-sleep-ack-completion-20260730
title: PCR02 DEEP_SLEEP ARMED ACK 物理发送完成与 PA15 切电诊断
kind: debug-record
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/archive/debug/2026-07-30-deep-sleep-ack-completion.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: engineering-debug
  from: PCR02 source changes and local build validation
  source_sha256: a0c7b82eab72b203c51cf0a9fff42591551034f3fc09dc0acec2148974499943
  temporary_source_retained: false
review_after: '2026-10-28'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- pcr02
- deep-sleep
- uart
validation_refs:
- projects/xcrz-sigmastar-demo/archive/debug/2026-07-30-deep-sleep-ack-completion.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/archive/debug/2026-07-30-deep-sleep-ack-completion.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-07-30'
updated_at: '2026-07-30'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-07-30'
manual_validation_pending: true
summary_zh: 记录 DEEP_SLEEP ARMED ACK 物理发送完成机制、MCU PA15 切电诊断和板端判定矩阵。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
---

# PCR02 DEEP_SLEEP：ARMED ACK 物理发送完成与 PA15 切电诊断

## 问题

Sensor 独立 DEEP_SLEEP 测试中，MCU 返回 ARMED 后 SoC 仍持续运行。原 SoC 逻辑仅在收到 ARMED 后固定等待 100 ms，不能证明响应 MCU 命令的 ACK 已经完成 UART 物理发送；MCU 侧也缺少 ACK 匹配和 PA15 切换的直接诊断证据。

## 源码改进

- App UART 为 `SLEEP_STATE_NOTIFY` 的响应 ACK 增加精确的物理发送完成跟踪，使用 `seq + cmd + generation` 区分目标 ACK。
- Sensor 在收到 ARMED 后等待对应 ACK 完成 `VSHDIUART_WaitTxDone`，成功后才允许低功耗流程继续；超时或驱动失败时安全终止，不再使用固定 100 ms 延时。
- Sleep-state 解码结果携带帧序号作为进程内元数据，不改变 UART wire protocol。
- MCU 的 wakeup 诊断构建增加 `DEEP_ACK` 与 `DEEP_CUT` 日志，记录 ACK 序号、状态机阶段及 PA15 切换前后电平；普通构建不包含这些诊断字符串。

## 验证证据

- `make modules/app_obj_all -j20`：通过。
- `make app_sensor_test -j20`：通过。
- `build/check_public_headers.sh`：通过。
- `build/check_soc_low_power_flow.py --source-root <pcr02-compile-tree>/SourceCode`：通过。
- MCU 普通构建与 `WAKEUP_DIAG_LOG_ENABLED` 诊断构建均通过，`fwtool.py check --scope build` 通过。
- `Tools/tests/check_wakeup_diagnostics.py`：通过。
- 普通 MCU ELF 不含 `DEEP_ACK`，诊断 ELF 包含 `DEEP_ACK` 和 `DEEP_CUT`。

## 板端判定

板端仍需验证，不能仅凭构建结果宣称硬件问题已修复：

1. SoC 未打印 ACK 物理发送成功：检查 UART `TIOCSERGETLSR`/`WaitTxDone` 支持。
2. SoC 打印成功但 MCU 无 `DEEP_ACK`：检查 ACK 接收、校验和序号匹配。
3. MCU 有 `DEEP_ACK` 但无 `DEEP_CUT`：检查 wakeup 状态机和延迟任务。
4. `DEEP_CUT` 显示 PA15 未变低：检查 GPIO 配置或引脚占用。
5. `DEEP_CUT` 显示 PA15 已由高变低但 SoC 仍运行：转查板级供电路径、外部反灌或 PA15 与 SoC 电源使能的连接。

## 边界

- 该记录不包含现场服务器地址、设备身份或原始日志。
- 既有 image/OTA 不会自动包含后编译的 App；板测和发布前必须重新生成、部署并核对制品身份。
- MCU 诊断固件接近应用分区上限，仅用于直接烧录排障，不作为 OTA 发布制品。

## 2026-07-30 板端证据更新

同一序号的完整软件链已在板端出现：

```text
SoC: MCU low power ARMED ACK physically transmitted: mode=3, seq=63
MCU: DEEP_ACK ... seq=63 ok=1 mode=3 result=0 phase=1
MCU: DEEP_CUT ... phase=2 pa15=1->0
```

五秒后 SoC 仍在运行。由此可以排除 ACK 未发送、MCU 未匹配 ACK、DEEP_SLEEP
状态机未进入切电阶段。当前 `Power_Get_Keep_Status()` 使用
`gpio_output_bit_get()`，只读取 `GPIO_OCTL` 输出锁存值；`pa15=1->0` 不能证明
PA15 焊盘电压或 SoC 电源轨实际下降。

下一步按单变量实验确认：

1. 同一时间基准测量 PA15 焊盘与 SoC 主电源轨。
2. `DEEP_CUT` 后将物理开关由 ON 切到 OFF；若 SoC 立即掉电，说明开关路径与
   PA15 路径形成硬件“或”保持。
3. 若 PA15 焊盘仍为高，检查 GPIO 模式、引脚映射和板级连接。
4. 若 PA15 焊盘为低但 SoC 电源轨不降，检查电源控制拓扑或外部反灌路径。
