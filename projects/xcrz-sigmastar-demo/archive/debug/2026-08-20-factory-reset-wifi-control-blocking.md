---
related: []
human_reviewed_by: null
human_reviewed_at: null
review_basis: null
incident_id: null
severity: null
affected_version: null
id: pcr02-factory-reset-wifi-control-blocking-20260820
title: PCR02恢复出厂WiFi控制阻塞优化
kind: debug-record
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/archive/debug/2026-08-20-factory-reset-wifi-control-blocking.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: manual
  from: 本次源码分析、现场日志与定向构建证据
  source_sha256: 2ac1a69b133b7de95805111872a589982dcbc531b60f61c3e0f7e6c1ac0065fc
review_after: '2026-11-18'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- pcr02
- wifi
- factory-reset
- shutdown
validation_refs:
- projects/xcrz-sigmastar-demo/archive/debug/2026-08-20-factory-reset-wifi-control-blocking.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/archive/debug/2026-08-20-factory-reset-wifi-control-blocking.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-08-20'
updated_at: '2026-08-20'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-08-20'
manual_validation_pending: true
summary_zh: 记录恢复出厂时WiFi清网与阻塞连接竞争导致约30秒请求超时，以及Sensor快速清网、reboot栅栏和HDI原子接口约束的修复与待板测项。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
---

# 排障记录标题

## 现象

说明用户可见症状、错误码、时间和频率。

## 影响范围

说明项目、设备、版本、模块，以及是否影响量产或现场。

## 环境

说明硬件、固件、配置、工具和输入数据。

## 时间线

| 时间 | 操作或观察 | 结果 |
| --- | --- | --- |
|  |  |  |

## 证据

记录日志摘要、命令摘要、artifact 引用和 hash；不写 raw 大文件正文。

## 假设与排除

| 假设 | 验证动作 | 结果 | 状态 |
| --- | --- | --- | --- |
|  |  |  |  |

## 根因

确认根因；未确认时写“未确认”。

## 修复或规避

说明已执行动作、适用范围和副作用。

## 验证

说明复现前后对比、命令和通过/失败判据。

### 离线待验证（可选）

仅在现场或离线排障先记录、后补验证时保留此块；未验证内容必须留在假设、风险或后续动作中。

```yaml
manual_validation_pending: true
manual_validation_reason:
required_followup: rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
owner:
review_after:
```

## 后续动作

说明是否提升为 runbook、validation、decision，或仅归档。
