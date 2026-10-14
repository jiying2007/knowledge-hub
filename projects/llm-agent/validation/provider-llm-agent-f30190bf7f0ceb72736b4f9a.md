---
aliases:
- M5 一次性真实运行失败与ADK依赖修复
related:
- projects/llm-agent/README.md
- indexes/obsidian-home.md
- indexes/project-readiness.md
id: provider-llm-agent-f30190bf7f0ceb72736b4f9a
title: M5 一次性真实运行失败与ADK依赖修复
kind: validation
domain: projects/llm-agent
path: projects/llm-agent/validation/provider-llm-agent-f30190bf7f0ceb72736b4f9a.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: provider-candidate-archive
  from: provider-policy-sha256:a295759999c3c3c2594752350565bbde6af74808af32b9272604f53a36f82736;operation:f30190bf7f0ceb72736b4f9a70719dfcf8d7c2f868016b3e53f27af4d4d33881
  source_sha256: 1e2d3b9c180b4d2eb399dbdc8f71f25aa7fd8f46832ca2f531250e5c8b771d74
  temporary_source_retained: false
review_after: '2027-01-10'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- provider-archive
- validation
validation_refs:
- projects/llm-agent/validation/provider-llm-agent-f30190bf7f0ceb72736b4f9a.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/llm-agent/validation/provider-llm-agent-f30190bf7f0ceb72736b4f9a.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-10-12'
updated_at: '2026-10-12'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-10-12'
manual_validation_pending: true
summary_zh: 'verified_at: 2026-10-12 status: reviewing software_m5_certified: false owner_review: 未执行人类资格审批'
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
subject_ref: &id001
  id: llm-agent
  type: project
created_subject_ref: *id001
principal_id: null
provider_operation_id: f30190bf7f0ceb72736b4f9a70719dfcf8d7c2f868016b3e53f27af4d4d33881
---

# M5 一次性真实运行失败与ADK依赖修复

verified_at: 2026-10-12
status: reviewing
software_m5_certified: false
owner_review: 未执行人类资格审批

缺专用主机时，一次性runner可在本机最小namespace执行。官方SDK2.338.0的pre-job hook普通退出失败不足阻止always步骤，因此采用不可变服务端run/job/runner绑定guard、准确Worker终止与永久hold，宿主终止本namespace。26身份协议、9离线生命周期、1实际namespace否认测试及独立whole-lifecycle Spec/Quality通过；测试不替代真实模型或签名证据。

用户全部授权范围内，software-m5-runtime环境创建并限制main，5项publicpins回读一致。最初SDK config因namespace缺/sbin/ldconfig在注册前失败，registry0与无dispatch已核；增加只读系统依赖后，一次有界续接成功注册runner21并触发唯一run38260430071/attempt1，源基线af92f63dc91b668dd716e763ffe1f9683de7280a。run最终failure：guard、准确源码检出、Python、Cosign和固定tasktrust准备success；Collect在ADK eval帮助导入处缺jsonschema而失败，Sign/Export skipped。实际准确注销runner，registry回读0。

源码检查证明capability-help失败发生在实际模型command构造/执行之前，模型上游请求0；不把失败称为真实模型调用成功、signedruntime或零成本上游请求。根仓pyproject只声明PyYAML，固定ADK声明jsonschema。无auth隔离namespace、同一Python3.11.12复现beforehelp exit1→安装root和准确ADK声明依赖→afterhelp exit0、两个bounded-cost flags存在；安装后生产clean_source和完整ADK identity实际PASS。

源修复仅root runtimeworkflow和两份变更记录：prepare同Python安装root+ADK并运行evalhelp，collect显式绑定ADK_PYTHON_BIN。workflowcompat/docsync/diffcheckPASS、独立Spec/QualityPASS、相关provenance22/22PASS。commit2fdf9eeb094a672683e7b8c153571ee73119db98已推送，PR196已创建，当前PR CI38267668763运行中；本笔记不声明合并或新main签名CI已取得。

https://github.com/jiying2007/llm_agent/actions/runs/38260430071
https://github.com/jiying2007/llm_agent/pull/196

旧af92真实signedrootCI仍作为历史基线保留，不重标新源码。后续source合并后必须取对应fresh完整签名rootCI，再以新的准确runner/run取得一次尚未消耗的上游模型请求证据。模型仍gpt-6.1-sol/medium、最多一次请求，不自动模型重试；humanfield与owner资格仍缺证据。原主仓HEAD/index/diff保护实测PASS，live/auth未改，未归档私有SDK状态、凭据或原始模型输出。
