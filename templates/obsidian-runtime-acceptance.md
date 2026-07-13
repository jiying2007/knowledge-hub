---
id:
title:
kind: audit
domain: governance
path: local/obsidian-runtime-acceptance.json
scope: team-general
visibility: personal-local
status: reviewing
owner:
source:
review_after:
created_at:
updated_at:
promotion: none
promotion_decision: none; local GUI acceptance does not authorize lifecycle changes
tags: [obsidian, local-gui, runtime-acceptance]
summary_zh:
review_status: manual-entry-pending-review
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
evidence_strength: local-gui-runtime-evidence
evidence_refs: []
generated_by_ai: false
ai_role: none
ai_model_or_tool:
ai_generated_at:
human_reviewed_by:
human_reviewed_at:
review_basis:
---

# Obsidian 本机运行态验收模板

本模板用于人工验收，不进入 registry，不改变 Knowledge Hub 生命周期。实际记录保存在忽略提交的
`local/obsidian-runtime-acceptance.json`。

```json
{
  "schema_version": 1,
  "obsidian_version": "<version>",
  "validated_at": "YYYY-MM-DD",
  "validated_by": "<human>",
  "bases_rendered": true,
  "properties_visible": true,
  "backlinks_working": true,
  "moc_navigation_working": true,
  "screenshot_refs": [
    "<local-or-controlled-artifact-ref>"
  ]
}
```

验收必须在真实 Obsidian GUI 中完成。Graph/Backlinks/Bases 只证明阅读与发现能力，不提供 owner decision、
active promotion、Sync、Publish 或外部写入授权。
