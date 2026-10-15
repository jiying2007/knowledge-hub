---
id: gros-knowledge-entry
title: GROS 知识入口
kind: project-current
domain: projects/gros
path: projects/gros/README.md
project_id: gros
evidence_profile: knowledge-project
scope: project-specific
visibility: team-internal
status: reviewing
searchable: true
owner: leiwenjun
source:
  type: provider-project-registration
  from: request-sha256:37fea76fd45fdb9e7ec7966a83f3b809d7df1ad3c94c3cf0b17a8c380029c5b6
review_after: '2027-01-15'
validation_refs:
- projects/gros/README.md
- registry/projects.json
- registry/repositories.json
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
- rtk bash ~/knowledge-hub/tools/knowledge-final-gate.sh --json --final-profile product --as-of 2026-10-15
summary_zh: 项目身份与知识入口登记；不代表源码验证、owner approval 或产品放行。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
review_status: ai-generated-project-readiness-pending-owner-and-real-validation
content_review_status: pending
evidence_validation_status: pending
evidence_strength: generated-readiness-contract-pending-owner-validation
evidence_refs:
- projects/gros/README.md
- registry/projects.json
- registry/repositories.json
promotion_decision: none; structural readiness asset only, no active promotion or owner decision
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-10-15'
manual_validation_pending: true
decision_owner: unassigned
tags:
- gros
- entry
- ai-generated
- owner-review-pending
- manual-validation-pending
- no-active-promotion
promotion: none
created_at: '2026-10-15'
updated_at: '2026-10-15'
aliases:
- GROS 知识入口
related:
- indexes/obsidian-home.md
- indexes/project-readiness.md
---

# GROS

项目知识入口。登记身份不代表 owner approval、源码验证或产品放行。

<!-- knowledge-hub-project-readiness:start -->
## 成熟度工作台

以下入口是单一 `reviewing` evidence contract 与统一 dashboard；不代表 owner 签收或发布就绪。

- [项目 evidence contract](validation/project-readiness.md)
- [统一 readiness dashboard](../../indexes/project-readiness.md)
<!-- knowledge-hub-project-readiness:end -->
