---
aliases:
- Carrier 修复发布与真实模型身份缺证复验
related:
- projects/llm-agent/README.md
- indexes/obsidian-home.md
- indexes/project-readiness.md
id: provider-llm-agent-05d6a436bf36f2625ab93bf0
title: Carrier 修复发布与真实模型身份缺证复验
kind: validation
domain: projects/llm-agent
path: projects/llm-agent/validation/provider-llm-agent-05d6a436bf36f2625ab93bf0.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: provider-candidate-archive
  from: provider-policy-sha256:a295759999c3c3c2594752350565bbde6af74808af32b9272604f53a36f82736;operation:05d6a436bf36f2625ab93bf0ca07e759c6ea920b7816da7a5d3aac5491874988
  source_sha256: 678d71a76926c3311438644933164e0635c764c82c22f36cafaf68bae1e624a9
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
- projects/llm-agent/validation/provider-llm-agent-05d6a436bf36f2625ab93bf0.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/llm-agent/validation/provider-llm-agent-05d6a436bf36f2625ab93bf0.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-10-13'
updated_at: '2026-10-13'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-10-13'
manual_validation_pending: true
summary_zh: 2026-10-13，本次用户授权落实 carrier 软件修复、正常 SCM 发布、完整 main CI 验签，以及新增一次 GPT-6.1-Sol medium 单任务真实取证。工程源码发布与 CI 签名已验收；真实模型身份和领域资格仍
  BLOCKED。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
subject_ref: &id001
  id: llm-agent
  type: project
created_subject_ref: *id001
principal_id: null
provider_operation_id: 05d6a436bf36f2625ab93bf0ca07e759c6ea920b7816da7a5d3aac5491874988
---

# Carrier 修复发布与真实身份缺证闭环

2026-10-13，本次用户授权落实 carrier 软件修复、正常 SCM 发布、完整 main CI 验签，以及新增一次 GPT-6.1-Sol medium 单任务真实取证。工程源码发布与 CI 签名已验收；真实模型身份和领域资格仍 BLOCKED。

修复已通过 PR199 合并，main exact 180def98dc831b4a450f459cab2c75e80f5db3cf/tree f846e2ed000761a50f751ab6eeee4e74e5ac3ffe。观察器支持官方 native client 的可信 SSE 顶层 headers carrier，保留响应完成、response id、唯一 expected model 与 conflict 拒绝；失败诊断 v2 只增加 carrier 布尔值和固定失败枚举，不输出 raw header/body/credential。源码 root74/ADK56/target55通过；quick50/52的既有参考快照和历史候选问题没有重标通过。

完整 forced CI38365238826/attempt1：七 jobs SUCCESS，签名 envelope f234ced9829148063564c68214a0a7d738008202e1ddc0469eee4929e2d95f45，payload e589946ed7ef17fe84480ac64432921a24b2f27efa67133e50baafcb126b7363。主代理和独立审查者均使用固定实体 Cosign3.1.3 与 trusted root 实际离线验签通过。该结论只证明源码交付和 CI 来源。

唯一真实 runtime38366969401/attempt1/head180def：前置 Python、Cosign、task/trust SUCCESS；Collect FAILURE；脱敏负摘要保存与上传 SUCCESS；Sign/正制品 SKIPPED。runner25确认注销，registry0。进程 exit0不覆盖 workflow FAILURE，没有自动模型重试。

唯一 negative artifact11797079433，SHA256 c5722b4eb3ef7fd826aeb4c80f0c8098c95e97ac1246f21e541eb184eb662d9c，strict schema llm-agent-runtime-failure-summary/v2。观察到 HTTP200、response completed、prepared/claimed各1、model count0。http model header/alias、SSE response headers、可信顶层 headers、受观测但不采信的其他 SSE header carrier 的 presence 全 false；response.model 字段 presence true；failure_kind=missing-model-header。other-or-missing MIME 不是该诊断的直接拒绝原因。

该 negative 未签名，其计数不是服务端或计费认证。它把此前的 carrier 歧义收敛为本次所有已覆盖 header carrier 未提供模型身份；不能声称检查了服务端所有未知返回位置。response.model 字段仅 presence 不认证字段值、actual model 或 usage；配置 requested_model 也不认证实际模型。不得补造 header、usage、签名或把过去失败改成功。

下一步外部契约：服务端或受信代理应提供由实际模型路由生成并原样透传的 openai-model 身份；HTTP采用 openai-model，可信 SSE response.headers/顶层 headers 支持 openai-model 或 x-openai-model，并和同 response id及完成事件绑定。HTTP x-openai-model 当前仅作 presence诊断、不采信模型值。不能从请求配置或普通输出拼出该 header。离线回放可验证兼容性；新鲜实际取证应先修正并核实该服务端契约，再使用新的明确有界额度，不自动重试已消费请求。

M5/G21/G22、independent pilot、field/operator、human owner 和 release 均未通过；真实 CI 签名、单任务、聊天授权和 Git身份不能替代这些资格。原root HEAD/index/tracked-diff保护基线保留，isolated worktree保留，不清理其他现场。

Codify Decision：reusable_pattern=exact-source+固定密码学与正负分层；promotion_candidate=false；next_task_friction_reduced=定位服务端模型身份 carrier缺证；reduced_by=严格v2脱敏诊断；reduction_evidence=本次唯一实际negative；do_not_promote_reason=实际header身份/真人领域证据缺失；owner_review=false；rollback_path=通过新正常补丁回退carrier兼容改动，不改旧失败；verification_evidence=actual main signed CI、runtime v2 artifact、independent result review。不读取或写入Hub内部活动目录、不推断subject；耐久结论仅经Provider形成reviewing候选。
