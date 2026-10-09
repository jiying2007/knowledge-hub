---
id: provider-codex-94a9746ffadd3a7353d0c589
title: session-wrap 原始许可证恢复与运行验证
kind: validation
domain: codex
path: domains/codex/validation/provider-codex-94a9746ffadd3a7353d0c589.md
scope: team-general
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: provider-candidate-archive
  from: provider-policy-sha256:a295759999c3c3c2594752350565bbde6af74808af32b9272604f53a36f82736;operation:94a9746ffadd3a7353d0c58983ea7c728239125a80ab33480c85b79eb783b06c
  source_sha256: c761448a3a022a50d4cb421298ee05d614541f5ebc31378187ea6d844ece53f7
  temporary_source_retained: false
review_after: '2027-01-04'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- provider-archive
- validation
validation_refs:
- domains/codex/validation/provider-codex-94a9746ffadd3a7353d0c589.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- domains/codex/validation/provider-codex-94a9746ffadd3a7353d0c589.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-10-06'
updated_at: '2026-10-06'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-10-06'
manual_validation_pending: true
summary_zh: 根因由Git历史证明：4149902从4.0.0升级4.0.1时删除原LICENSE但未复制到新目录。恢复同一技能历史blob92e9a1f563eff8d239932bf8bfe1e9328299cec3，不推断版权或改授权，SKILL.md与版本保持原样。source、build、live
  LICENSE SHA256均44ba154a1fc0ead85f111db232a1839b15ceea0cea0941a725a87846dbf80c97。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
aliases:
- session-wrap 原始许可证恢复与运行验证
related:
- indexes/obsidian-home.md
---

# session-wrap 原始许可证恢复与运行验证

根因由Git历史证明：4149902从4.0.0升级4.0.1时删除原LICENSE但未复制到新目录。恢复同一技能历史blob92e9a1f563eff8d239932bf8bfe1e9328299cec3，不推断版权或改授权，SKILL.md与版本保持原样。source、build、live LICENSE SHA256均44ba154a1fc0ead85f111db232a1839b15ceea0cea0941a725a87846dbf80c97。

Codex PR45全部9项托管检查通过后已合并，main cada8d26ae956ad11891fcb36fe8f8e7d72d9ef5。实际源仓ff同步并保留五tracked用户修改与journal，未将用户改动纳入提交；增删行与同步前备份一致，journal hash保持。备份与stash未清理。

实际source-to-live完整通过：team-collab build767 managed；repo/build/live/governance doctor均0错误0警告，74项技能检查0错误0警告；应用后344项测试通过，四profile smoke通过，最终check exit0。plan仅复制LICENSE与更新受管清单，保留475项；无删除、无配置/auth/session修改。plan输出与keep路径回读均匹配，配置hash未变。live diff0/missing0，drift changed0/stale0/unmanaged0。

build tree SHA25637f9dfadf42a337ad6d668f868ad4aeaecf4f1cfc5ca6e28fc1e2517b93c18a2；plan SHA256afa92b0bd370a5dff6fbc622288fe98951cd7263e8dea4e3700c874454787e06；live managed state SHA256ce0666280dfc6c86348a92421de479815cc77d6a96a1b2b7cb5815a8c220d763。

资格边界：本次只是原始随附许可证遗漏修复及运行一致性，不产生新的法律授权、owner审查、产品资格或真实模型收益证明。原单条LICENSE告警关闭，无真实模型调用。
