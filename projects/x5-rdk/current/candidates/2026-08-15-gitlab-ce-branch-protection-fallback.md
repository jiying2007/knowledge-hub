---
related:
- projects/x5-rdk/README.md
- indexes/obsidian-home.md
- indexes/project-readiness.md
maturity: null
security_classification: null
human_reviewed_by: null
human_reviewed_at: null
review_basis: null
id: x5-rdk-gitlab-ce-branch-protection-fallback-20260815
title: X5 GitLab CE 多仓分支保护降级方案
kind: project-current
domain: projects/x5-rdk
path: projects/x5-rdk/current/candidates/2026-08-15-gitlab-ce-branch-protection-fallback.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: manual
  from: 来自 X5 多仓分支迁移与保护规则实施的脱敏工程总结
  source_sha256: 68775bd5dc006985341ca28b46ed04a033e262dacbdea74efdb8973dea650896
review_after: '2026-11-15'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- x5
- gitlab
- branch-governance
- runbook
validation_refs:
- projects/x5-rdk/current/candidates/2026-08-15-gitlab-ce-branch-protection-fallback.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/x5-rdk/current/candidates/2026-08-15-gitlab-ce-branch-protection-fallback.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-08-15'
updated_at: '2026-08-15'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-08-15'
manual_validation_pending: true
summary_zh: GitLab CE 不支持群组级保护规则时，以逐项目精确规则实现 X5 多仓分支治理，并用全量回读、失败回滚和无强推门禁闭环。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
aliases:
- X5 GitLab CE 多仓分支保护降级方案
---

# X5 GitLab CE 多仓分支保护降级方案

## 摘要

当部署版本不提供群组级 protected branch 时，不应放弃统一治理，也不应以模糊通配符替代。可将一条逻辑策略展开为逐项目、精确分支名的保护规则，并以项目清单、回读对账和失败回滚保持闭环。

## 适用范围

- 多仓 SDK 已有明确项目清单，目标分支为 `vs/dev-x5/v1.1.2` 或后续同规范版本分支。
- 适用于 GitLab CE 能提供项目级 protected branch API、但缺少所需群组级能力的环境。
- 不替代项目成员权限、合并审批、CODEOWNERS、Runner 和发布门禁。

## 权威来源

- 工程 SSOT：`x5-integration` 的分支治理文档与迁移验证收据。
- 仓库集合 SSOT：固定版本 `x5-manifest`。
- 本文是脱敏方法总结，不保存私有端点、项目数字 ID、令牌或原始 API 日志。

## 执行协议

1. 从固定 manifest 和治理仓生成目标项目集合，禁止手工维护第二份项目列表。
2. 迁移窗口使用临时 bootstrap 规则：仅维护者可推送和合并，禁止 force push。
3. 完成目标分支创建、提交点校验和旧引用清理后，切换为最终规则：直接 push 关闭，维护者可合并，force push 始终关闭。
4. 对每个项目回读分支名、push/merge 级别和 force-push 状态；成功数必须等于期望项目数。
5. 任一项目失败即停止收口。保留已成功项目的回读证据，并按项目精确恢复上一条规则，不做批量删除。

## 验收门禁

- 项目集合与固定 manifest 一致，无漏项或额外项目。
- 每个项目只存在目标精确规则，不以 `vs/*` 等宽泛规则替代。
- 最终状态禁止直接 push 与 force push；合并权限符合治理文档。
- 规则变更前后均记录脱敏摘要、操作者角色、时间和项目计数。
- 新增 SDK 或新仓库时，由同一生成与回读流程重新展开，不复制旧计数。

## 风险与回退

- GitLab 版本或许可证变化后应优先复核是否可恢复群组级 SSOT，避免长期维护重复规则。
- API 返回成功不等于策略生效，必须逐项目回读。
- 删除保护规则会短暂扩大写权限；回退应采用“创建或更新目标规则后再清理旧规则”的顺序。

## Review

- owner：leiwenjun
- review_after：2026-11-15
- 下一次复核：GitLab 实际版本、权限矩阵、项目集合生成方式及最终规则全量回读证据。
