---
aliases:
- Codex 模型身份载体兼容与负诊断修复
related:
- projects/llm-agent/README.md
- indexes/obsidian-home.md
- indexes/project-readiness.md
id: provider-llm-agent-71087f273dfb302d5f589d3b
title: Codex 模型身份载体兼容与负诊断修复
kind: validation
domain: projects/llm-agent
path: projects/llm-agent/validation/provider-llm-agent-71087f273dfb302d5f589d3b.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: provider-candidate-archive
  from: provider-policy-sha256:a295759999c3c3c2594752350565bbde6af74808af32b9272604f53a36f82736;operation:71087f273dfb302d5f589d3b381d302d97343a86abc126f7b03da6dad08a9892
  source_sha256: 09860484001f341375590a8bdcccdf6b8ed26a3c2a3cbc4c90d6b9554fa87fa8
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
- projects/llm-agent/validation/provider-llm-agent-71087f273dfb302d5f589d3b.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/llm-agent/validation/provider-llm-agent-71087f273dfb302d5f589d3b.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-10-13'
updated_at: '2026-10-13'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-10-13'
manual_validation_pending: true
summary_zh: reviewing；软件修复已经本地落地，历史真实 run 38355568555 继续 FAIL/BLOCKED，当前没有新增真实调用或 release 资格。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
subject_ref: &id001
  id: llm-agent
  type: project
created_subject_ref: *id001
principal_id: null
provider_operation_id: 71087f273dfb302d5f589d3b381d302d97343a86abc126f7b03da6dad08a9892
---

# Codex 模型身份取证兼容修复与边界

reviewing；软件修复已经本地落地，历史真实 run 38355568555 继续 FAIL/BLOCKED，当前没有新增真实调用或 release 资格。

问题分层：上游 HTTP200/流完成是保存的负诊断事实；资格观察器未识别预期模型身份而拒绝。只凭历史摘要无法确认当时身份载体。源码对照确认一项独立兼容缺项：固定官方 Codex rust-v0.159.2 会从 SSE 事件顶层 headers fallback 读取模型身份，不仅限于 response.metadata；本仓旧观察器却限于 metadata。官方代码还明确测试不采信 response.model。这不是模型请求配置出错的已确认结论。

官方源码 codex-rs/codex-api/src/sse/responses.rs，Git blob c01b13f1fe63d5065babac0d96cf1d74e4a4dbb4，SHA256 6c7b6e9d121c03658954b759d5febf71667f673a9647bcd41f674fa7ecd63f65。已实际取得完整源码并独立核对摘要/相关实现和测试，不以搜索摘要作为证据。

本地隔离分支 codex/m5-carrier-repair-20261013，基线23aeb9a760e2e0e13740e1cdba913cb684158fcb。修改 observer、negative producer、两项测试文件及 repair-note；ADK97cf和Codexd12子仓保持exact未修改。原用户dirty与旧取证工作树、实体制品、SDK日志、凭据、live与所有历史计量保持。

修复：采信 created/in_progress/completed/metadata 的服务端顶层header；保留header来源/responseID/完成态/唯一精确模型与冲突拒绝。其他event的模型header只记录存在布尔位，生成文本和 response.model 不能授予身份。模型header缺失仍阻断。固定六布尔位和 failure_kind 枚举诊断，区分载体出现/未支持、字段存在与缺身份/冲突/未完成等；不保存自由header、正文、密钥或日志。

schema：旧输入仍输出failure-summary/v1；新identity_diagnostics明确输出v2，旧严格读者必须显式更新才可消费，不能盲目复用旧临时negative helper。正测量协议与真实签名验证要求保持。

验证：修复前最小顶层header回归失败，修复后定向55/55，独立reviewer使用ResourceWarning-as-error复跑55/55；root74/74；ADK quick56/56；diff-check通过。快速门禁50/52仍FAIL，仅参考仓current快照缺失和历史5.0.0-rc.2 M5声明/scorecard不匹配两个既有项；不报全仓全绿或可提交/合并。审查中数组递归来源丢失的minor已修复，top/nested数组诊断位分别验证，不影响身份规则。

root完整suite运行中的早期无关测试先于minor补丁，受影响runtime-smoke/consumer阶段与独立55定向在最终补丁后验证；没有因已通过测试复跑真实模型。新本地修复尚未commit/push/merge，旧main和历史运行没有获得新软件身份。

reusable_pattern=对照固定客户端协议修补受信carrier，并用布尔位/固定枚举形成可诊断但不授予资格的负记录；promotion_candidate=false；owner_review=false；do_not_promote_reason=尚未发布且无修复版真实模型/usage/签名/field或owner验收；reduced_by=确证漏读修复与负诊断精确化；reduction_evidence=前后回归、官方源码摘要、L3回执与独立审查；rollback_path=保留隔离工作树，以23aeb为回退参照，不碰原dirty。

真实闭环仍需：正式审阅和发布补丁后，在单独明确授权的一次有界真实运行中观察实际受信模型carrier；若服务确实不提供所需身份，应保持阻断或通过受治理的新协议定义证据来源，不能伪造header/usage、反向签旧失败或把配置当实际模型。field/operator/owner/G21/G22独立验收继续BLOCKED。
