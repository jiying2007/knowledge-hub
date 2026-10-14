---
id: provider-knowledge-hub-790b8730417b16701123ff50
title: Knowledge Provider 发布核验
kind: audit
domain: governance
path: governance/product/archive/provider-knowledge-hub-790b8730417b16701123ff50.md
scope: team-general
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: provider-candidate-archive
  from: provider-policy-sha256:a295759999c3c3c2594752350565bbde6af74808af32b9272604f53a36f82736;operation:790b8730417b16701123ff50edb059a25fdc8369b21368d182ec3531ba5d5bd8
  source_sha256: 528b79a502f9b218b3c8ba207e3b359a9f69f31160a590683121778064435760
  temporary_source_retained: false
review_after: '2027-01-11'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- provider-archive
- audit
validation_refs:
- governance/product/archive/provider-knowledge-hub-790b8730417b16701123ff50.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- governance/product/archive/provider-knowledge-hub-790b8730417b16701123ff50.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-10-13'
updated_at: '2026-10-13'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-10-13'
manual_validation_pending: true
summary_zh: 状态：Hub 已获得最终精确批准并合并，master push CI 与签名证据均通过；Codex 已合并并完成受管应用。提交、推送、合并、应用及发布核验已收口。产品成熟度与保留本机许可引起的严格检查差异仍单独保持 NEEDS_REVIEW。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
subject_ref: &id001
  id: knowledge-hub
  type: project
created_subject_ref: *id001
principal_id: null
provider_operation_id: 790b8730417b16701123ff50edb059a25fdc8369b21368d182ec3531ba5d5bd8
---

# Knowledge Provider 发布核验

状态：Hub 已获得最终精确批准并合并，master push CI 与签名证据均通过；Codex 已合并并完成受管应用。提交、推送、合并、应用及发布核验已收口。产品成熟度与保留本机许可引起的严格检查差异仍单独保持 NEEDS_REVIEW。

- Hub PR： https://github.com/jiying2007/knowledge-hub/pull/143
- Hub 最终 HEAD：`db25fcc5574f3272487c45c953dd4ca7d3b22430`。
- 技术 CI： https://github.com/jiying2007/knowledge-hub/actions/runs/38328150760 ，工程与供应链、Python 3.10、系统 Python 3.8、官方 MCP、Quality gate 全部成功。
- 独立复审：无 blocker、major、minor；最近修复定向测试 62 项通过。发布树此前全量 1975 项通过，远端完整工程门禁已复验成功。
- CI 证据中 platform、engineering、compliance、restore、quality evidence binding 通过；product 的非终态仍为 needs-review，项目证据、内容候选与长期采用成熟度尚未全部就绪，不能声明产品放行。
- Codex PR： https://github.com/jiying2007/codex/pull/51 ，已合并；merge SHA `fb14ede0dea41188341c61999131d93a6acc3e19`。
- Codex 受管应用：按 team-collab build、doctor、plan、dry-run、apply 执行，只覆盖 managed-files.json，删除 0；配置、AGENTS、profile 哈希保持一致。
- 应用后检查：345 单测及四 profile smoke 通过，doctor 0 errors/0 warnings；严格检查最终因 rules/default.rules 多一条既有本机许可而 exit 1，保持 NEEDS_REVIEW，未覆盖权限或弱化漂移策略。
- 现场 A123X：公开 Provider resolve 为 resolved；Git commit 缺失不伪造源码验证状态。
- 两处原工作区已有 tracked dirty diff 哈希与发布前相同。
- 活动回执：Provider activity-capture 返回 pass/applied=true，receipt `4c8525f23f85d9efe9359cbc9f5800e44e858aee5b7a03c2ce8f832f27fc6554`。此活动记录不代表长期知识提升或产品 active。

用户已明确授权推进。Codex 受托通过账号 jiying2007 发布评论 https://github.com/jiying2007/knowledge-hub/pull/143#issuecomment-6135780193 ，安全 CI 38330133208 与原检查重跑均通过；以 match-head-commit 完成合并，master 为 bf794b97782c23ed2b1198e99a4d8fa71785c701 。隔离合并树与已批准树差异为零。

master push CI： https://github.com/jiying2007/knowledge-hub/actions/runs/38330245298 ，全部成功，包括 Python 3.10–3.14、system 3.8/3.9、官方 MCP、工程、合规、异地恢复和 Quality gate。

签名证据： https://github.com/jiying2007/knowledge-hub/actions/runs/38331132037 ，OIDC/Sigstore 身份与签名 predicate 验证成功，source_revision 精确绑定 bf794b97782c23ed2b1198e99a4d8fa71785c701；attestation https://github.com/jiying2007/knowledge-hub/attestations/55244007 ，仓库托管层 terminal closure pass，产品 gate 仍为 needs-review。

合并树中 A123X 归档经公开 Provider 使用完整预期 SHA256 复核为 VERIFIED/persisted=true，reviewing/promotion=none。

`SECURITY-CHANGE-APPROVE sha256:769c444498feade8c19994edfdb51847428272dfb41024084e3d1a0d300ed779 db25fcc5574f3272487c45c953dd4ca7d3b22430`

批准边界：用户原授权绑定 35b4fef；当前 HEAD 经 Ruff 修复已变化。安全工作流 .github/workflows/security-critical-change-review.yml 拒绝缺少精确 SHA 和 fingerprint 的批准。不能将旧授权静默替代为新精确批准，也不能 admin 绕过。
