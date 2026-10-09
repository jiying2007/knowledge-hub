---
id: provider-llm-agent-189f00d88f7c213c70d4c4e2
title: ADK8.0.3证据JSON与跨仓交付边界验证
kind: validation
domain: projects/llm-agent
path: projects/llm-agent/validation/provider-llm-agent-189f00d88f7c213c70d4c4e2.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: provider-candidate-archive
  from: provider-policy-sha256:a295759999c3c3c2594752350565bbde6af74808af32b9272604f53a36f82736;operation:189f00d88f7c213c70d4c4e2009bcc3f1de5e918b75aab9ffa19624d338943dc
  source_sha256: 97441ddb2b4e81097e66fd34d14f8b42085e4b8c080fd8975ccd0111855ee6ff
  temporary_source_retained: false
review_after: '2027-01-05'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- provider-archive
- validation
validation_refs:
- projects/llm-agent/validation/provider-llm-agent-189f00d88f7c213c70d4c4e2.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/llm-agent/validation/provider-llm-agent-189f00d88f7c213c70d4c4e2.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-10-07'
updated_at: '2026-10-07'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-10-07'
manual_validation_pending: true
summary_zh: 可复用结论：不可信JSON应统一拒绝重复键、非有限值和预算超限；真实入口必须保留原始叶路径，不能先resolve抹去链接；摘要与解码来自一次有界regular descriptor读取。原子输出需预先拒绝目录/FIFO/链接及输入重叠，并显式保持原权限。跨仓provenance不能依赖Hub私有Git路径，知识候选不等于Provider持久化。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
aliases:
- ADK8.0.3证据JSON与跨仓交付边界验证
related:
- projects/llm-agent/README.md
- indexes/obsidian-home.md
- indexes/project-readiness.md
---

# ADK8.0.3证据JSON与跨仓交付边界验证

可复用结论：不可信JSON应统一拒绝重复键、非有限值和预算超限；真实入口必须保留原始叶路径，不能先resolve抹去链接；摘要与解码来自一次有界regular descriptor读取。原子输出需预先拒绝目录/FIFO/链接及输入重叠，并显式保持原权限。跨仓provenance不能依赖Hub私有Git路径，知识候选不等于Provider持久化。

已交付ADK PR179/main3df8f7b821d1194fbe0cc44e013416857d6b64a5/immutable8.0.3；mainCI37580322786九job与发行37580751586实际成功。实际archive86f1f591d9c8f528d2586cd47417edcfb2aa3ffb118e51893c3d53588d1e1ede匹配API/签名/contract，固定cosign与reviewed root验签成功。三Python各98/98与30/30路由、静态/类型/构建/依赖审计通过，14定向及独立源码复审通过。

llm_agent PR188八checks成功并已合并实际main c8db67f15df1cf816e9ad602709bd7a5d6d439c2，本地已fast-forward且与candidate源字节一致，SDK和锁/签名同源。Root9项定向、35intake hardening和74/74 full通过；冻结quick49/52、snapshot稳定/验签/runtime健康通过；剩余dirty-triage/subrepo-state和M5检查为参考基线到期与历史/current资格两类阻塞，未改owner/date/资格。Root main CI37585431963另行观察，不把PR通过预填为Main CI通过。

保留用户十参考目录与独立Codex五处dirty/journal；Codex/live本轮不导入/apply，实际仍8.0.2，健康检查通过。不调用真实模型、不宣称质量/吞吐/token收益；不提升active知识或产品资格。Source/consumer身份与项目/产品资格独立。

负结果：早期JSON普通末值覆盖；真实入口提前resolve/预算前无界hash；输出目录移动与私有权限差异；验证PATH丢失PCRE2及沙箱缓存/进行中快照变化。均留证并修复/恢复后重跑，不用旧结果替代新终态。

后续候选：归档成员/总解压预算与stream读取、跨解释器数字预算、隔离runner受限并发和公平超时、依赖PR版本前移及新鲜复验；真实模型收益评测等待显式解除禁用。父目录/同UID并发和断电/跨文件事务不由现有atomic document工具证明。
