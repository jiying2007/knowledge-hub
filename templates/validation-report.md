---
id:
title:
kind: validation
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
target_version:
test_environment:
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
---

# 验证报告标题

## 验证目标

说明要证明什么，不证明什么。

## 验证对象

说明 commit、build、固件、工具、设备或配置。

## 环境

说明主机、板卡、工具链、依赖、运行模式和限制。

## 验证命令

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
| --- | --- | --- | --- | --- | --- |
| `rtk ...` |  | 中文摘要。 |  | Knowledge Hub / Project / Tool / Device |  |

补充说明：

- date：
- cwd：
- scope：

### 离线待验证（可选）

仅在验证报告先记录、命令证据稍后补跑时保留此块；结论应写“不可判定”或“待验证”，不得写通过。

```yaml
manual_validation_pending: true
manual_validation_reason:
required_followup: rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
owner:
review_after:
```

## 结果矩阵

| case | 期望 | 实际 | 状态 | 证据 |
| --- | --- | --- | --- | --- |
|  |  |  |  |  |

## 证据

记录日志路径、artifact URI、size、sha256、截图或报告引用。

## 结论

说明通过、失败、部分通过或不可判定。

## 剩余风险

说明未覆盖项、环境限制和阻塞项。

## 后续动作

说明 owner、截止时间和下一步验证。
