---
id: pcr02-ssc305-readiness-profile-20260713
title: PCR02 SSC305 SDK 项目画像候选
kind: project-current
domain: projects/pcr02-ssc305
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
review_after: '2026-10-13'
review_status: human-reviewed-accepted
promotion: none
tags:
- pcr02-ssc305
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
summary_zh: 记录 PCR02 SSC305 SDK 的 registry 身份、仓库边界、已有 Hub 证据和权威边界；只作 reviewing 工作台，不声明源码或发布事实。
promotion_decision: none; owner boundary attested, no active promotion or evidence-ready claim
path: projects/pcr02-ssc305/current/project-profile.md
project_id: pcr02-ssc305
readiness_slot: profile
aliases:
- pcr02-ssc305 profile
- pcr02-ssc305-profile
related:
- projects/pcr02-ssc305/README.md
- projects/pcr02-ssc305/current/runbooks/maintenance-entry.md
- projects/pcr02-ssc305/decisions/project-boundary-decision-candidate.md
- projects/pcr02-ssc305/validation/project-readiness.md
---

# PCR02 SSC305 SDK 项目画像候选

> 本页是 AI 生成的 reviewing 控制资产，只复述 registry 身份和 Hub 已有证据。它不是当前源码、owner decision、设备状态或发布状态证明。

## 项目标识

| 字段 | 值 |
|---|---|
| project_id | `pcr02-ssc305` |
| 类型 | `git-repository` |
| repo boundary | `primary` |
| 所属组 | `pcr02` |
| registry 状态 | `registered` |
| 本地源码映射 | `machine-local / not tracked` |
| Hub 已登记条目 | 截至 2026-07-15 为 `55`；archived=42, reviewing=13；后续以 `registry/items.jsonl` 动态查询为准 |

## 仓库边界

| repo_id | remote key | workspace ref | lifecycle |
|---|---|---|---|
| `pcr02-ssc305` | `robot/pcr02_ssc305` | `workspace://pcr02-ssc305` | `first-party` |

`workspace://` 是跨机器逻辑引用，不代表本机源码存在。使用 `knowledge-workspace-discover.sh --plan` 按 exact remote 只读发现，结果只写入未跟踪的 `local/workspaces.json`；绝对路径和动态 HEAD 不进入本页。

## 已有 Hub 证据

- [项目组规范入口边界决策候选](../decisions/pcr02-canonical-hardcut-20260715.md)：平台、应用、独立模块与产品组关系的唯一当前边界。
- [第三方库编译优化基线](runbooks/thirdparty-build-optimization-baseline.md)：SSC305 工具链和构建边界候选。
- [IMSSV06C11 三方 SDK 审计](../archive/source-audit/pcr02_imssv06c11_three_way_sdk_audit_20260715.md)：摄像头、SPI NAND 和时钟路径来源审计。
- [工程历史归档](../archive/engineering-archive/README.md)：OTA、存储、硬件、启动链和平台验证历史语料。
- [PCR02 SSC305 SDK readiness validation](../validation/project-readiness.md)、[权威边界决策候选](../decisions/project-boundary-decision-candidate.md)和[维护入口](runbooks/maintenance-entry.md)：结构控制资产，保持 `reviewing`。

## 当前权威边界

- 当前源码、分支、版本、构建和发布事实：源项目及其可复现验证证据。
- 长期摘要、决策记录、验证索引和跨项目方法：Knowledge Hub canonical Markdown 与 registry。
- `pcr02` 只是产品组 ID；不得作为独立 project/domain/path 重新写入内容。
- `status`、`owner`、`review_after`、promotion 和 authorization：registry/gate，不由目录名、Obsidian Graph 或本页文字推断。
- 当前 `decision_owner=leiwenjun`，owner boundary 已通过 hash-bound attestation；`manual_validation_pending=true`，真实环境验证未闭环前保持 `reviewing`。

## Related

- [维护 runbook](runbooks/maintenance-entry.md)
- [边界决策候选](../decisions/project-boundary-decision-candidate.md)
- [readiness validation](../validation/project-readiness.md)
- [项目入口](../README.md)
