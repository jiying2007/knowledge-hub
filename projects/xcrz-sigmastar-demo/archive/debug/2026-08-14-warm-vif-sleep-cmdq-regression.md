---
id: xcrz-pcr02-warm-vif-sleep-cmdq-debug-20260814
title: PCR02 WARM低帧率VIF sleep引发CMDQ异常
kind: debug-record
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/archive/debug/2026-08-14-warm-vif-sleep-cmdq-regression.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: agent-debug-summary
  from: xcrz_sigmastar_demo_dev
  source_sha256: c9ba90ca9ab5f83a12b9e82c81f7e688d53f4b6885d32cf3a2236dc0168d233c
  temporary_source_retained: false
review_after: '2026-09-14'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- debug
- pcr02
- warm
- vif
- cmdq
- 1fps
validation_refs:
- projects/xcrz-sigmastar-demo/archive/debug/2026-08-14-warm-vif-sleep-cmdq-regression.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/archive/debug/2026-08-14-warm-vif-sleep-cmdq-regression.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-08-14'
updated_at: '2026-08-14'
generated_by_ai: true
ai_role: summarized
ai_model_or_tool: Codex
ai_generated_at: '2026-08-14'
manual_validation_pending: true
summary_zh: WARM切入1fps后周期VIF sleep/re-arm与保留媒体图并存，出现CMDQ超时、ISP reset和I2C错误；需禁用该策略做单变量复验。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
---

# PCR02 WARM 进入 1fps 后 VIF sleep/re-arm 引发媒体链路异常

## 现象

设备从 30fps 进入待机并通过显式 WARM 路由切换到 1fps。API 在约 2.59 秒后返回成功，随后媒体内核链路持续出现 CMDQ timeout、ISP reset、输出任务长等待和 Sensor I2C 传输失败。

## 时间线与证据

- WARM 30→1 开始后，ISP Channel 按设计完成 Destroy/Create，切换接口返回成功。
- 低帧率预热的 AE count 在有界窗口内仍为 0，但当前实现只记录 warning 并继续提交 1fps。
- 切换完成后立即启动周期性 VIF sleep/wake re-arm；日志中 VIF sleep enable 约 141 次、Sensor resume 约 132 次。
- 同一窗口累计出现 3 次 `WAIT_TRIG_TIMEOUT`、2 次 `POLLEQ_TIMEOUT`、3 次 ISP Device reset、1 次约 1.71 秒的 `CheckOutputTaskStatus` 和约 460 次 I2C `-7`。
- 日志中没有返回 30fps或设备重启证据，异常持续到采集结束。

## 判断

根因状态为高置信度 suspected，尚需单变量 A/B 复验确认。

最可能的触发点不是 WARM 的 Channel Destroy/Create 本身，而是切换完成后应用的低帧率 VIF sleep/wake coordinator。当前实现每秒执行一次“disable sleep → enable sleep after one frame”，与保留的 RAW/SCL/ISP graph 并存后出现 FIFO、CMDQ 和 Sensor I2C 级联异常。

这与冻结契约“ACTIVE_LOW_1 保持 SoC Active、VIF sleep=false”冲突。该 runtime policy 是 COLD/WARM/HOT 共用路径，因此在完成 A/B 验证前不能只把问题归因于 WARM，也不能据此认为 HOT 可安全规避。

## 负向结论

- `ioctl ... Operation not permitted` 是既有 AE/AWB 诊断噪声，但无法解释后续 CMDQ reset 和 I2C 错误。
- WARM API 返回成功不代表低帧率运行稳定；异常发生在返回成功后的周期 re-arm 阶段。
- 日志未显示 kernel panic 或设备重启，但媒体链路已进入不可接受的自动 reset 状态。

## 最小复验

保持同一固件、同一 WARM 30→1 场景和 RAW demand，仅禁用低帧率 VIF sleep/wake coordinator；验证：

1. 1fps 诊断状态 `vif_sleep=0`；
2. CMDQ error/reset/timeout、`CheckOutputTaskStatus`、VIF FIFO FULL 和 Sensor I2C `-7` 新增计数均为 0；
3. RAW 首帧持续可用，实际 fps 接近 1，30→1→30 双向切换成功；
4. 再分别覆盖 COLD、WARM、HOT，确认问题来自共用 runtime policy 而非单一路由。

## 安全边界

在单变量修复复验完成前，当前低帧率 VIF sleep/wake 策略应视为 `needs-fix`；不得把本日志中的 CMDQ/reset/timeout 当作允许噪声，也不应以 HOT 替代 WARM 作为规避结论。
