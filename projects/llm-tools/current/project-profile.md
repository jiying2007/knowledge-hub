---
id: llm-tools-readiness-profile-20260713
title: LLM Tools 项目画像候选
kind: project-current
domain: projects/llm-tools
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
review_after: '2026-10-13'
review_status: human-reviewed-accepted
promotion: none
tags:
- llm-tools
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
summary_zh: 记录 LLM Tools 的 registry 身份、仓库边界、已有 Hub 证据和权威边界；只作 reviewing 工作台，不声明源码或发布事实。
promotion_decision: none; owner boundary attested, no active promotion or evidence-ready claim
path: projects/llm-tools/current/project-profile.md
project_id: llm-tools
readiness_slot: profile
aliases:
- llm-tools profile
- llm-tools-profile
related:
- projects/llm-tools/README.md
- projects/llm-tools/current/runbooks/maintenance-entry.md
- projects/llm-tools/decisions/project-boundary-decision-candidate.md
- projects/llm-tools/validation/project-readiness.md
---

# LLM Tools 项目画像候选

> 本页是 AI 生成的 reviewing 控制资产，只复述 registry 身份和 Hub 已有证据。它不是当前源码、owner decision、设备状态或发布状态证明。

## 项目标识

| 字段 | 值 |
|---|---|
| project_id | `llm-tools` |
| 类型 | `git-repository` |
| repo boundary | `tooling` |
| 所属组 | `agent-tools, embedded-tools` |
| registry 状态 | `registered` |
| 本地源码映射 | `machine-local / not tracked` |
| Hub 已登记条目 | `9`；archived=5, reviewing=4 |

## 仓库边界

| repo_id | remote key | workspace ref | lifecycle |
|---|---|---|---|
| `llm-tools` | `embedded/tools/llm_tools` | `workspace://llm-tools` | `first-party` |

`workspace://` 是跨机器逻辑引用，不代表本机源码存在。使用 `knowledge-workspace-discover.sh --plan` 按 exact remote 只读发现，结果只写入未跟踪的 `local/workspaces.json`；绝对路径和动态 HEAD 不进入本页。

## 已有 Hub 证据

- [llm_tools Windows 构建机 Runbook 候选归档](../archive/release/2026-07-09-windows-builder-runbook.md)：`archived` / `project-archive`
- [llm_tools v1.0.0 发布记忆审计历史 2026-05-19](../archive/release/2026-05-19-llm-tools-v1-release-memory-review.md)：`archived` / `project-archive`
- [llm_tools 三仓治理与单提交发布历史 2026-05-17](../archive/release/2026-05-17-llm-tools-three-repo-governance-session.md)：`archived` / `project-archive`
- [llm_tools 发布治理归档 2026-05-16](../archive/release/2026-05-16-llm-tools-release-governance.md)：`archived` / `project-archive`
- [llm_tools 正常迭代策略历史记录 2026-05-17](../archive/release/2026-05-17-llm-tools-normal-iteration-policy.md)：`archived` / `project-archive`
- [LLM Tools readiness validation](../validation/project-readiness.md)：`reviewing` / `validation`
- [LLM Tools 权威与维护边界决策候选](../decisions/project-boundary-decision-candidate.md)：`reviewing` / `decision`
- [LLM Tools 维护入口](runbooks/maintenance-entry.md)：`reviewing` / `runbook`

## 当前权威边界

- 当前源码、分支、版本、构建和发布事实：源项目及其可复现验证证据。
- 长期摘要、决策记录、验证索引和跨项目方法：Knowledge Hub canonical Markdown 与 registry。
- `status`、`owner`、`review_after`、promotion 和 authorization：registry/gate，不由目录名、Obsidian Graph 或本页文字推断。
- 当前 `decision_owner=leiwenjun`，owner boundary 已通过 hash-bound attestation；`manual_validation_pending=true`，真实环境验证未闭环前保持 `reviewing`。

## Related

- [维护 runbook](runbooks/maintenance-entry.md)
- [边界决策候选](../decisions/project-boundary-decision-candidate.md)
- [readiness validation](../validation/project-readiness.md)
- [项目入口](../README.md)
