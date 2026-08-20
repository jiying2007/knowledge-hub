---
id: xcrz-pcr02-warm-current-workload-cmdq-debug-v2-20260815
title: PCR02 WARM当前业务负载CMDQ异常V2
kind: debug-record
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/archive/debug/2026-08-15-warm-current-workload-cmdq-regression-v2.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: agent-debug-summary
  from: xcrz_sigmastar_demo_dev
  source_sha256: fa5cfb68b21e50c707ce877d6371fae47146578a3eee9f5e82849effa25d21ec
  temporary_source_retained: false
review_after: '2026-09-15'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- debug
- pcr02
- warm
- vif-sleep
- cmdq
- 1fps
- supersedes-candidate
validation_refs:
- projects/xcrz-sigmastar-demo/archive/debug/2026-08-15-warm-current-workload-cmdq-regression-v2.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/archive/debug/2026-08-15-warm-current-workload-cmdq-regression-v2.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-08-15'
updated_at: '2026-08-15'
generated_by_ai: true
ai_role: summarized
ai_model_or_tool: Codex
ai_generated_at: '2026-08-15'
manual_validation_pending: true
summary_zh: 当前产品待机场景WARM切入1fps并保留DS2_RAW后出现CMDQ超时、ISP reset和I2C错误；根因需用VIF sleep与AE门禁单变量A/B确认，不能直接外推HOT必然失败。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
---

# PCR02 WARM 进入 1fps 后媒体链路异常（当前业务负载）

## 结论边界

2026-08-14 串口日志确认：产品应用从 30fps 进入待机，通过显式 WARM 路由切换到 1fps，并保留 DS2_RAW 后，媒体内核链路发生 CMDQ timeout、ISP reset、输出任务长等待和 Sensor I2C 错误。该现象不是允许噪声，当前 WARM 产品场景应标记为 `needs-fix`。

根因尚未完成单变量复验。现有证据支持“WARM Channel rebuild、AE 预热未完成、当前 RAW/SCL 负载与低帧 VIF sleep/re-arm 的交互”这一高风险假设，但不足以把 VIF sleep/re-arm 单独认定为根因。

## 复现时间线

- 产品进入待机，发起 WARM 30→1；WARM executor 完成 ISP Channel Destroy/Create。
- 低帧预热 AE count 为 `0/11` 并超时；实现将其作为 warning，继续设置 1fps并向业务返回成功，耗时约 2.59 秒。
- 业务保留 DS2_RAW，关闭 LOW_ENC；随后启动 1000ms VIF sleep/re-arm。
- 日志窗口累计出现：
  - VIF sleep enable 约 141 次；Sensor resume 约 132 次；
  - 3 次 `WAIT_TRIG_TIMEOUT`；
  - 2 次 `POLLEQ_TIMEOUT`；
  - 3 次 ISP Device reset；
  - 1 次约 1.71 秒的 `CheckOutputTaskStatus`；
  - 约 460 次 Sensor I2C `-7`。
- 未见 kernel panic、设备重启或返回 30fps；异常持续到日志采集结束。

## 假设矩阵

| 假设 | 当前判断 | 证据与反证 | 最小验证 |
| --- | --- | --- | --- |
| WARM Channel rebuild 后低图未达到可安全 re-arm 状态 | 高 | AE count 仍为 0，随后出现 FIFO/CMDQ 级联；但 API 已返回成功 | 保持业务负载，只将 AE timeout 改为硬失败或延后 runtime policy |
| VIF sleep/re-arm 与 WARM + DS2_RAW/SCL 图交互触发 | 高 | 异常发生在周期 re-arm 阶段，且 wake/sleep 与错误持续共现 | WARM 同场景仅关闭 VIF sleep/re-arm 做 A/B |
| VIF sleep/re-arm 单独必然有缺陷 | 被反证为“不充分” | 2026-07-31 HOT/both 专项曾在同一策略下通过 5/20/3×10 轮且增量内核日志干净 | 用当前产品二进制和业务负载复跑 HOT，不能复用旧 HIL 结论 |
| AE/AWB `Operation not permitted` 导致 CMDQ reset | 低 | 该打印在正常基线存在，不能解释后续 reset/I2C 级联 | 无需单独修复，继续作为诊断噪声过滤 |

## HOT 与公共策略边界

HOT 和 WARM 进入 1fps 后都会调用低帧 runtime policy，但 HOT 不销毁 ISP Channel/IQ。历史 HOT 专项 HIL 的通过结果说明，共用 runtime policy 不足以证明 HOT 必然失败；本次日志也没有直接执行 HOT。

因此：

- 当前 WARM 产品负载已确认失败；
- HOT 在旧受控 HIL 下有通过证据，但在当前产品负载/当前二进制下仍需重新验证；
- 不得从本次 WARM 日志直接推导“HOT 必然失败”，也不得未经复测直接将 HOT 作为生产规避方案。

## 最小修复与验证顺序

1. 固定当前产品二进制、待机流程、DS2_RAW demand 和日志窗口。
2. WARM A/B：唯一变量为低帧 VIF sleep/re-arm 开关；要求 CMDQ/reset、`CheckOutputTaskStatus`、FIFO FULL 和 I2C `-7` 新增计数为 0。
3. 若关闭后通过，再检查 AE warmup `0/11` 是否仍出现，并决定是否把 timeout 升级为失败门禁。
4. 使用同一产品负载分别复跑 COLD/WARM/HOT 30→1→30，不使用旧 HIL 数据替代当前验证。
5. 验证 RAW 持续输出、实际 fps、首帧/IDR、PTS 单调、runtime graph equality 和退出清理。

## 关联与替代候选

- 反证来源：`projects/xcrz-sigmastar-demo/archive/reports/2026-07-31-pcr02-vi-fps-vif-sleep-optimization.md`。
- 本记录建议替代此前过度归因公共 runtime policy 的候选：`projects/xcrz-sigmastar-demo/archive/debug/2026-08-14-warm-vif-sleep-cmdq-regression.md`。
- 两份旧记录均保留历史 provenance；是否变更状态由 owner/归档治理决定，本记录不自动删除或提升任何知识。

## Provenance 与脱敏

- captured_at：2026-08-15
- source：2026-08-14 产品串口日志、当前源码调用链、2026-07-31 HOT 专项 HIL 脱敏归档
- raw log retained：no
- secrets/endpoints/device identity：not archived
- memory candidate：no
- gate：`reviewing / current WARM workload needs-fix / root-cause A/B pending`
