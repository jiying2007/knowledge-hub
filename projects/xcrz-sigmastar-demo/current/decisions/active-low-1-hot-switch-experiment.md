---
id: pcr02-active-low-1-hot-switch-experiment-20260728
title: PCR02 ACTIVE_LOW_1 HOT切换实验决策
kind: decision
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/current/decisions/active-low-1-hot-switch-experiment.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: team-core
source:
  type: project-validation
  from: xcrz-sigmastar-demo
  source_sha256: d4f87a115d3d5a1b7e3f7cddc48f3cd9754fa33b732a89a793a8597ac50163ab
  temporary_source_retained: false
review_after: '2026-08-28'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- pcr02
- ssc305
- hdi-vi
- hot-switch
validation_refs:
- projects/xcrz-sigmastar-demo/current/decisions/active-low-1-hot-switch-experiment.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/current/decisions/active-low-1-hot-switch-experiment.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-07-28'
updated_at: '2026-07-28'
generated_by_ai: true
ai_role: summarized
ai_model_or_tool: Codex
ai_generated_at: '2026-07-28'
manual_validation_pending: true
summary_zh: SSC305物理1/30fps默认保持COLD；HOT实验保留ISP Device、Channel和IQ，30到1显著缩短，1到30仍受物理1fps数据面安全排空主导。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
aliases:
- PCR02 ACTIVE_LOW_1 HOT切换实验决策
related:
- projects/xcrz-sigmastar-demo/README.md
- indexes/obsidian-home.md
- indexes/project-readiness.md
---

# PCR02 ACTIVE_LOW_1 HOT 切换实验决策候选

- captured_at: 2026-07-28
- source_project: xcrz-sigmastar-demo
- source_commit_hdi: 6de2b9a
- source_commit_app_test: 0e6844d
- source_commit_root_artifact: 4d1f0249

## 决策

物理 1fps/30fps 的生产默认继续使用 COLD rebuild。新增
`HDI_VI_EXPERIMENTAL_HOT_SWITCH=1` 作为进程级 opt-in 实验：

- 完整停止 VENC/RAW/LDC/SCL 下游和 ISP output port；
- Stop VIF source gate，解绑 VIF→ISP；
- 保留 ISP Device、已经 Stop 的 ISP Channel 和 IQ；
- 设置 Sensor FPS，重绑 VIF→ISP，Start 同一 Channel；
- 严格按目标 demand 重建下游 graph；
- 失败先经 Destroy/Create Channel 恢复，仍失败再执行完整 COLD 恢复。

HOT 不代表运行中直接 SetFps/rebind，也不改变 planner 默认 capability。

## 验证结论

- host pipeline contract test：PASS。
- 目标 ARM HDI library 与快速 HIL 工具构建：PASS。
- HOT RAW-only：30→1 API 约 0.353 秒，1→30 API 约 2.209 秒。
- HOT MAIN+SUB+RAW：30→1 API 约 0.537 秒，1→30 API 约 2.283 秒。
- 对照 WARM MAIN+SUB+RAW：约 1.120/2.262 秒。
- 对照 COLD MAIN+SUB+RAW：约 2.157/3.386 秒。
- HOT/WARM/COLD 均通过 RAW、首 IDR、严格单调 PTS 与 exact demand 断言；复跑后无新增
  `CheckOutputTaskStatus`、reset 或 timeout。

## 根因归属

HOT 显著缩短 30→1，因为跳过 ISP Channel rebuild、IQ reload 和低图 AE warmup。

HOT 没有显著缩短 1→30。RAW-only 分段显示：

- RAW task stop/depth reset 为微秒级；
- SCL2 StopPort 约 0.933 秒；
- source→SCL unbind 约 1.000 秒；
- ISP Stop/Start Channel 为几十微秒；
- SCL deinit 约 0.235 秒。

因此 1→30 的主要下界是物理 1fps data-plane 的安全排空，而不是 ISP deinit 或 RAW worker poll。

## 已否决路径

1. 提前 RAW pre-quiesce：等待转移到上游 unbind，总时间不变。
2. 先 SetFps(30) 等 AE：1.5 秒内只增加一帧，未改变旧图 cadence。
3. RAW-only 低图直连 ISP port1：API 曾降至约 1.55～1.57 秒，但 ISP crop 与现有 SCL
   full-FOV scale 输出不等价；显式原生 Preview 尺寸在高图创建失败，并产生 VIF 约 0.52 秒
   长耗时告警，代码已完整撤回。

## 风险与后续门禁

HOT 只获得受控性能实验资格。进入生产默认前仍需 24 小时长稳、温循、低照/高曝光、
retained IQ 图像一致性、故障注入和功耗验证。平台未提供明确 packet flush/cancel 契约前，
不得主动释放在途 buffer，也不得并发调用同一 SCL Channel 的未声明线程安全 API。

## Provenance

结论来自项目内结构化 HIL 输出、分段诊断指标、主机 contract test、目标 ARM 构建和内核告警负向扫描。
未归档设备地址、挂载路径、原始日志、凭证或运行时缓存。
