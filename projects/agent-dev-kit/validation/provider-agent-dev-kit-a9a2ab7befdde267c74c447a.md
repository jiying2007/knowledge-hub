---
aliases:
- ADK 官方来源维护验证候选
related:
- projects/agent-dev-kit/README.md
- indexes/obsidian-home.md
- indexes/project-readiness.md
id: provider-agent-dev-kit-a9a2ab7befdde267c74c447a
title: ADK 官方来源维护验证候选
kind: validation
domain: projects/agent-dev-kit
path: projects/agent-dev-kit/validation/provider-agent-dev-kit-a9a2ab7befdde267c74c447a.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: provider-candidate-archive
  from: provider-policy-sha256:a295759999c3c3c2594752350565bbde6af74808af32b9272604f53a36f82736;operation:a9a2ab7befdde267c74c447aaa0fd0ac64c54bbbc247d342d0251c0a9ea76145
  source_sha256: 3e8b6304e680419b929d74967ef2808f180cec85561719d5a39e975212c57d36
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
- projects/agent-dev-kit/validation/provider-agent-dev-kit-a9a2ab7befdde267c74c447a.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/agent-dev-kit/validation/provider-agent-dev-kit-a9a2ab7befdde267c74c447a.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-10-13'
updated_at: '2026-10-13'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-10-13'
manual_validation_pending: true
summary_zh: 日期 2026-10-13；scope=canonical ADK source-maintenance；status=reviewing；组件发布/root adoption/M5 qualification=false。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
subject_ref: &id001
  id: agent-dev-kit
  type: project
created_subject_ref: *id001
principal_id: null
provider_operation_id: a9a2ab7befdde267c74c447aaa0fd0ac64c54bbbc247d342d0251c0a9ea76145
---

# ADK 官方来源维护验证候选

日期 2026-10-13；scope=canonical ADK source-maintenance；status=reviewing；组件发布/root adoption/M5 qualification=false。

已实际读取 OpenCode agents/skills、五项 Anthropic 既有官方依据、OWASP 官方落地页及发布说明。沿用90天窗口更新已复核来源至2027-01-11；纠正Claude skill description是官方推荐字段、ADK本地保持更强name/description约束。OWASP指南下载两次timeout，当前证据仅复核taxonomy-only ASI01-ASI10，不声称全文、安全控制有效性或认证。

最终生产源码8.0.6：full98/98，quick56/56，strict/version/official governance/release静态检查PASS。独立Spec/QualityPASS；full回执SHA256 a8934325c0edf05bf4d207940a76298cc0de2e6015cf3eb6666ff45c4cef32e0。非语义末尾空行问题经原始Git检查定位、独立复审修复；当前源码生产文件与full回执对应版本不变，没有伪称重跑。

源码PR https://github.com/jiying2007/agent-dev-kit/pull/184；初版commit825601d26a7dec1fe8bb648201b933874397e589；修正后head c604d39ee25dddf60f095bc8c1a1395455379ff9。旧CI38332218011在format步骤失败，新CI38332545647的三个contract/static-security/deterministic jobs已PASS，三个regression仍运行。PR未合并、新tag/Release/签名promotion未证实，不把本笔记当远端交付成功。

本轮原主仓HEAD/index/dirty已实际fingerprint保护；原root expiry消费者未提交候选保留。真实M5取证额外上游请求仍0，总计最多1次gpt-6.1-sol medium授权保留，无自动模型重试。历史runtime run38260430071模型命令前失败，无signedruntime；用户授权不生成humanfield/owner资格。

下一独立验收：exacthead CI通过与PRmerge→exactmain签名promotion/immutableRelease→root clean隔离工作树准确导入与完整signedCI→唯一真实模型测量/独立验签。humanfield/owner仍未提供，整体M5不可关闭。未改live配置、认证或memories，未归档raw日志。
