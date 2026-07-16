---
id: knowledge-hub-readiness-profile-20260713
title: Knowledge Hub 项目画像候选
kind: project-current
domain: governance
scope: team-general
visibility: team-internal
status: reviewing
owner: leiwenjun
review_after: '2026-10-13'
review_status: human-reviewed-accepted
promotion: none
tags:
- knowledge-hub
- project-readiness
- profile
- ai-generated
- owner-review-pending
- manual-validation-pending
- no-active-promotion
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-07-13'
manual_validation_pending: true
decision_owner: leiwenjun
summary_zh: 记录 Knowledge Hub 的 registry 身份、仓库边界、已有 Hub 证据和权威边界；只作 reviewing 工作台，不声明源码或发布事实。
promotion_decision: none; owner boundary attested, no active promotion or evidence-ready claim
path: governance/product/current/project-profile.md
project_id: knowledge-hub
readiness_slot: profile
aliases:
- knowledge-hub profile
- knowledge-hub-profile
related:
- README.md
- governance/product/current/runbooks/maintenance-entry.md
- governance/product/decisions/project-boundary-decision-candidate.md
- governance/product/validation/project-readiness.md
---

# Knowledge Hub 项目画像候选

> 本页是 AI 生成的 reviewing 控制资产，只复述 registry 身份和 Hub 已有证据。它不是当前源码、owner decision、设备状态或发布状态证明。

## 项目标识

| 字段 | 值 |
|---|---|
| project_id | `knowledge-hub` |
| 类型 | `knowledge-control-plane` |
| repo boundary | `control-plane` |
| 所属组 | `knowledge-hub` |
| registry 状态 | `registered` |
| 本地源码映射 | `machine-local / not tracked` |
| Hub 已登记条目 | 由 `knowledge-health-summary.sh --json` 实时计算；不在当前画像中固化计数 |

## 仓库边界

| repo_id | remote key | workspace ref | lifecycle |
|---|---|---|---|
| `knowledge-hub` | `jiying2007/knowledge-hub` | `~/knowledge-hub` | `first-party` |

`workspace://` 是跨机器逻辑引用，不代表本机源码存在。使用 `knowledge-workspace-discover.sh --plan` 按 exact remote 只读发现，结果只写入未跟踪的 `local/workspaces.json`；绝对路径和动态 HEAD 不进入本页。

## 已有 Hub 证据

- [AI 生成内容标注规范](../../ai-generated-content-labeling.md)：`active` / `standard`
- [Knowledge Hub long-term maintenance plan](../../ultimate-maintenance-plan.md)：`active` / `standard`
- [Knowledge Hub root](../../../README.md)：`active` / `architecture`
- [Knowledge Hub 全局路径路由规则](../../path-routing.md)：`active` / `standard`
- [Owner Review 规范](../../owner-review-rules.md)：`active` / `standard`
- [Registry 中文可读性与证据字段扩展](../../../registry/schema.md)：`active` / `standard`
- [中文 Commit Changelog PR 规范](../../commit-changelog-pr-rules.md)：`active` / `standard`
- [中文可读性规范](../../chinese-readability.md)：`active` / `standard`

## 当前权威边界

- 当前源码、分支、版本、构建和发布事实：源项目及其可复现验证证据。
- 长期摘要、决策记录、验证索引和跨项目方法：Knowledge Hub canonical Markdown 与 registry。
- `status`、`owner`、`review_after`、promotion 和 authorization：registry/gate，不由目录名、Obsidian Graph 或本页文字推断。
- 当前 `decision_owner=leiwenjun`，owner boundary 已通过 hash-bound attestation；`manual_validation_pending=true`，真实环境验证未闭环前保持 `reviewing`。

## Related

- [维护 runbook](runbooks/maintenance-entry.md)
- [边界决策候选](../decisions/project-boundary-decision-candidate.md)
- [readiness validation](../validation/project-readiness.md)
- [项目入口](../../../README.md)
