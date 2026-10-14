---
aliases:
- M5 v2 执行验收契约落地
related:
- projects/llm-agent/README.md
- indexes/obsidian-home.md
- indexes/project-readiness.md
id: provider-llm-agent-dd5146d74604545445b7cf86
title: M5 v2 执行验收契约落地
kind: validation
domain: projects/llm-agent
path: projects/llm-agent/validation/provider-llm-agent-dd5146d74604545445b7cf86.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: provider-candidate-archive
  from: provider-policy-sha256:a295759999c3c3c2594752350565bbde6af74808af32b9272604f53a36f82736;operation:dd5146d74604545445b7cf860be2d92a7fcb1382c7f19ea03dc37df5c35707cf
  source_sha256: 15a1192e9189442427c9becf9b509399e0eef57f0d67e071199f265f74cd4d3f
  temporary_source_retained: false
review_after: '2027-01-11'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- provider-archive
- validation
validation_refs:
- projects/llm-agent/validation/provider-llm-agent-dd5146d74604545445b7cf86.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/llm-agent/validation/provider-llm-agent-dd5146d74604545445b7cf86.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-10-13'
updated_at: '2026-10-13'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-10-13'
manual_validation_pending: true
summary_zh: 2026-10-13，用户明确要求将实际模型身份从 M5 采集、标记及验证中移除。PR200 已合并：source906f66653590fa858f77cba2a81b15695020ac3c，main4b6f548a9d09c21fa4649fa0e03547bc0c9b717e，treea3e27bf7eadd11bc4e834da9aeca1e9aff4264ec。契约文档为
  docs/changes/20261013-m5-execution-v2/contract.md。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
subject_ref: &id001
  id: llm-agent
  type: project
created_subject_ref: *id001
principal_id: null
provider_operation_id: dd5146d74604545445b7cf860be2d92a7fcb1382c7f19ea03dc37df5c35707cf
---

# M5 v2 执行验收契约落地

2026-10-13，用户明确要求将实际模型身份从 M5 采集、标记及验证中移除。PR200 已合并：source906f66653590fa858f77cba2a81b15695020ac3c，main4b6f548a9d09c21fa4649fa0e03547bc0c9b717e，treea3e27bf7eadd11bc4e834da9aeca1e9aff4264ec。契约文档为 docs/changes/20261013-m5-execution-v2/contract.md。

新 runtime-smoke-evidence/v2 与 report schema2：M5 producer 直接调用固定 Codex CLI，不启用身份观察器。移除发布证据中的 reported_models 与 model_observation；requested_model 和 reasoning effort 只表示请求配置。v2 不要求模型身份 header 或名称匹配；rollover 和当前 M5 消费者已同步接入。独立 collector 的 execution-only 开关与 legacy 身份观察选项互斥。

旧 v1 保留原严格语义，用于读取历史证据。新旧schema均纳入签名测量摘要，旧签名不能通过字段改写重用；未知版本和版本混搭拒绝。源码/ADK/manifest/task/prompt、实际执行文件前后摘要、质量、安全、usage类型、任务数量、错误、时效、workflow/main/run/attempt和真实Cosign验签继续强制。旧 signed/failed 证据及原dirty保护基线没有改写。

实际验证：完整root74/74、ADKquick56/56、最终provenance42/42、独立78/78 PASS。完整产品回归后仅新增一个corev2消费者测试，随后定向复验，产品代码未变化。quick50/52仍FAIL：参考当前快照缺失、历史5rc2/promotion/scorecard不匹配。初始Python环境和权限问题已修正后复验，不重标先前错误。

本轮没有真实模型调用。已有自动main CI38381560559 SUCCESS但deep/receipt SKIP，不计完整签名验收；完整CI真实验签另行核验。软件实现、源码发布和CI不能替代v2实际任务执行及field/owner/release资格。历史失败不因新契约而改判成功。

复用决策：默认按真实任务结果和制品来源验收，取消额外实际模型认证要求；promotion_candidate=false，owner_review=false。技术变更按用户定义落地，Provider仅reviewing候选，不产生跨域放行。回退通过正常补丁恢复legacy producer，不覆写历史签名。
