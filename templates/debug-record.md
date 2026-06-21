---
id:
title:
kind: project-archive
domain:
path:
scope:
visibility:
status: draft
owner:
source:
review_after:
created_at:
updated_at:
promotion: none
promotion_decision: none
tags: []
related: []
validation_refs: []
artifact_refs: []
summary_zh:
review_status:
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status:
evidence_strength:
evidence_refs: []
generated_by_ai: false
ai_role: none
ai_model_or_tool:
ai_generated_at:
human_reviewed_by:
human_reviewed_at:
review_basis:
incident_id:
severity:
affected_version:
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
