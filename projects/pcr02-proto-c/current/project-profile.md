---
id: pcr02-proto-c-readiness-profile-20260713
title: PCR02 Proto C App 项目画像候选
kind: project-current
domain: projects/pcr02-proto-c
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
review_after: '2026-10-13'
review_status: human-reviewed-accepted
promotion: none
tags:
- pcr02-proto-c
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
decision_owner: unassigned
summary_zh: 记录 PCR02 Proto C App 的 registry 身份、仓库边界、已有 Hub 证据和权威边界；只作 reviewing 工作台，不声明源码或发布事实。
promotion_decision: none; structural readiness asset only, no active promotion or owner decision
path: projects/pcr02-proto-c/current/project-profile.md
project_id: pcr02-proto-c
readiness_slot: profile
aliases:
- pcr02-proto-c profile
- pcr02-proto-c-profile
related:
- projects/pcr02-proto-c/README.md
- projects/pcr02-proto-c/current/runbooks/maintenance-entry.md
- projects/pcr02-proto-c/decisions/project-boundary-decision-candidate.md
- projects/pcr02-proto-c/validation/project-readiness.md
---

# PCR02 Proto C App 项目画像候选

> 本页是 AI 生成的 reviewing 控制资产，只复述 registry 身份和 Hub 已有证据。它不是当前源码、owner decision、设备状态或发布状态证明。

## 项目标识

| 字段 | 值 |
|---|---|
| project_id | `pcr02-proto-c` |
| 类型 | `git-repository` |
| repo boundary | `application` |
| 所属组 | `pcr02` |
| registry 状态 | `registered` |
| 本地源码映射 | `machine-local / not tracked` |
| Hub 已登记条目 | `4`；reviewing=4 |

## 仓库边界

| repo_id | remote key | workspace ref | lifecycle |
|---|---|---|---|
| `pcr02-proto-c` | `embedded/app/proto_c` | `workspace://pcr02-proto-c` | `first-party` |

`workspace://` 是跨机器逻辑引用，不代表本机源码存在。使用 `knowledge-workspace-discover.sh --plan` 按 exact remote 只读发现，结果只写入未跟踪的 `local/workspaces.json`；绝对路径和动态 HEAD 不进入本页。

## 已有 Hub 证据

- [PCR02 Proto C App readiness validation](../validation/project-readiness.md)：`reviewing` / `validation`
- [PCR02 Proto C App 权威与维护边界决策候选](../decisions/project-boundary-decision-candidate.md)：`reviewing` / `decision`
- [PCR02 Proto C App 维护入口](runbooks/maintenance-entry.md)：`reviewing` / `runbook`
- [PCR02 Proto C App 项目画像候选](project-profile.md)：`reviewing` / `project-current`

## 当前权威边界

- 当前源码、分支、版本、构建和发布事实：源项目及其可复现验证证据。
- 长期摘要、决策记录、验证索引和跨项目方法：Knowledge Hub canonical Markdown 与 registry。
- `status`、`owner`、`review_after`、promotion 和 authorization：registry/gate，不由目录名、Obsidian Graph 或本页文字推断。
- 当前 `decision_owner=unassigned`，`manual_validation_pending=true`；未完成 owner 和真实环境验证前保持 `reviewing`。

## Related

- [维护 runbook](runbooks/maintenance-entry.md)
- [边界决策候选](../decisions/project-boundary-decision-candidate.md)
- [readiness validation](../validation/project-readiness.md)
- [项目入口](../README.md)
