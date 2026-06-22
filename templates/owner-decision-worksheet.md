---
id:
title:
kind: owner-decision-worksheet
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
worksheet_id:
source_id:
source_path:
decision_owner:
decision_status: owner-fill-required
decision_date:
owner_question:
target_candidates: []
required_owner_fields: []
must_not: []
verification_cwd:
---

# Owner 签核表标题

> 本表是人工 owner decision 的工作表，不是已签收结论。不得把本表当成 owner decision，不得代填 `reviewed_by`，不得关闭 owner gate。
> 填写前先按 `templates/README.md` 的“字段填写矩阵”核对：只读候选值可以预填，真实 `owner_decision`、`target_decision`、`reviewed_by`、`reviewed_at` 和签收证据只能由真实 owner 提供。

## 背景

说明为什么需要 owner 决策。

## 待签核问题

用一句话写清要确认的状态、范围或提升动作。

## 工作表字段

- `worksheet_id`：对应 owner gate 的工作表 ID。
- `source_id` / `source_path`：被签收的来源，不代表可直接复制正文。
- `owner_question`：owner 需要回答的核心问题。
- `target_candidates`：允许的目标位置或处理方式；不得手写候选外目标。
- `required_owner_fields`：正式 owner JSONL 必填字段。
- `must_not`：签收也不能越过的硬边界。
- `verification_cwd`：相对验证命令的执行目录。

## 候选结论

| 候选 | 适用范围 | 证据 | 风险 |
| --- | --- | --- | --- |
|  |  |  |  |

## 必填证据

- source：
- validation_refs：
- artifact_refs：
- owner review：
- rollback_policy：

## Owner 决策

本段只记录候选，不代表已签收。正式 owner JSONL 至少需要填写：

- `owner_decision`
- `target_decision`
- `reviewed_by`
- `reviewed_at`
- `review_after`
- `source_status`
- `source_sha256`
- `source_size`
- `evidence_refs`
- `status_reason`

从 owner gate 导出和校验：

```bash
rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id <source-id> --worksheet-id <worksheet-id> --forms-jsonl
rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id <source-id> --worksheet-id <worksheet-id> --validate-forms '<owner-decisions.jsonl>' --json
rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id <source-id> --worksheet-id <worksheet-id> --validate-forms '<owner-decisions.jsonl>' --landing-audit --json
```

`routing_owner` 只负责分派，不等于真实 `reviewed_by`；AI、脚本和 Codex 不得代签。

## 生效条件

说明何时进入 active、reviewing、archived 或 superseded。

## 回滚条件

说明撤销、降级或 supersede 的触发条件。

## Review 周期

- owner：
- review_after：
- 下一次复核内容：
