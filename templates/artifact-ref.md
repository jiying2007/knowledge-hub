---
id:
title:
kind: artifact-ref
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
uri:
size:
sha256:
summary_zh:
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status:
review_status:
evidence_strength:
evidence_refs: []
artifact_type:
generated_by_ai: false
ai_role: none
ai_model_or_tool:
ai_generated_at:
human_reviewed_by:
human_reviewed_at:
review_basis:
---

# 制品引用标题

## 摘要

用中文说明这个制品是什么、来自哪里、为什么只登记引用而不复制正文。

## 制品身份

- uri：
- source_id：
- source_path：
- size：
- sha256：
- artifact_type：

## 权威来源

说明源路径、owner、生成方式、source status 和是否可重新获取。

## 使用边界

说明此制品是验证证据、脚本、日志、二进制、图片还是外部附件；不要把 raw log、SDK、release binary 或大型图片正文写入知识层。

## 验证

```bash
rtk sha256sum <source-path>
rtk wc -c <source-path>
rtk bash tools/knowledge-check.sh --dry-run --json
```

## 风险与限制

说明制品是否包含敏感信息、是否可能过期、是否需要 owner 复核。

## Review

- owner：
- review_after：
- 下一次复核内容：
