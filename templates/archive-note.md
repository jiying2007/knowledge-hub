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
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status:
review_status:
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

# 归档说明标题

## 摘要

用中文说明归档对象、归档原因、适用项目或范围。

## 原始来源

- source_id：
- source_path：
- source_status：
- source_hash：

## 归档边界

说明本文是历史证据、archive-only、superseded 还是 rejected；不要把历史结论写成当前 active 事实。

## 证据

- date：
- cwd：
- command：
- exit_code：
- result_summary：
- artifact_refs：

### 离线待验证（可选）

仅在归档记录先落盘、验证命令稍后补跑时保留此块；归档状态不得因此升级为 active fact。

```yaml
manual_validation_pending: true
manual_validation_reason:
required_followup: rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
owner:
review_after:
```

## 当前状态

说明是否仍可参考、是否被替代、是否需要 owner 复核。

## Superseded By

- superseded_by：
- replacement_path：
- replacement_registry_id：

## 风险与限制

说明过期条件、未验证点、敏感信息边界和不应复用的场景。

## Review

- owner：
- review_after：
- 下一次复核内容：
