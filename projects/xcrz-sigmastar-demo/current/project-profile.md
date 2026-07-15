---
id: xcrz-sigmastar-demo-readiness-profile-20260713
title: XCRZ SigmaStar Demo 项目画像候选
kind: project-current
domain: projects/xcrz-sigmastar-demo
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
review_after: '2026-10-13'
review_status: ai-generated-project-readiness-pending-owner-and-real-validation
promotion: none
tags:
- xcrz-sigmastar-demo
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
summary_zh: 记录 XCRZ SigmaStar Demo 的 registry 身份、仓库边界、已有 Hub 证据和权威边界；只作 reviewing 工作台，不声明源码或发布事实。
promotion_decision: none; structural readiness asset only, no active promotion or owner decision
path: projects/xcrz-sigmastar-demo/current/project-profile.md
project_id: xcrz-sigmastar-demo
readiness_slot: profile
aliases:
- xcrz-sigmastar-demo profile
- xcrz-sigmastar-demo-profile
related:
- projects/xcrz-sigmastar-demo/README.md
- projects/xcrz-sigmastar-demo/current/runbooks/maintenance-entry.md
- projects/xcrz-sigmastar-demo/decisions/project-boundary-decision-candidate.md
- projects/xcrz-sigmastar-demo/validation/project-readiness.md
---

# XCRZ SigmaStar Demo 项目画像候选

> 本页是 AI 生成的 reviewing 控制资产，只复述 registry 身份和 Hub 已有证据。它不是当前源码、owner decision、设备状态或发布状态证明。

## 项目标识

| 字段 | 值 |
|---|---|
| project_id | `xcrz-sigmastar-demo` |
| 类型 | `git-repository` |
| repo boundary | `primary` |
| 所属组 | `pcr02` |
| registry 状态 | `registered` |
| 本地源码映射 | `machine-local / not tracked` |
| Hub 已登记条目 | 截至 2026-07-15 为 `51`；archived=37, reviewing=14；后续以 `registry/items.jsonl` 动态查询为准 |

## 仓库边界

| repo_id | remote key | workspace ref | lifecycle |
|---|---|---|---|
| `xcrz-sigmastar-demo` | `robot/xcrz_sigmastar_demo` | `workspace://xcrz-sigmastar-demo` | `first-party` |

`workspace://` 是跨机器逻辑引用，不代表本机源码存在。使用 `knowledge-workspace-discover.sh --plan` 按 exact remote 只读发现，结果只写入未跟踪的 `local/workspaces.json`；绝对路径和动态 HEAD 不进入本页。

## 已有 Hub 证据

- [项目总体设计](architecture/project-overview-design.md)和[详细设计](../decisions/project-detailed-design.md)：应用与模块结构候选。
- [ASAN 调试指南](runbooks/asan-debug-guide.md)、[构建部署指南](runbooks/project-build-and-deploy-guide.md)和[调试工具指南](runbooks/project-debug-tools-guide.md)：应用侧维护入口。
- [Camera RAW_PREVIEW 架构候选](../decisions/camera-raw-preview-virtual-stream-architecture-20260711.md)与[Video/Audio 共享内存说明](runbooks/video-audio-shm-usage.md)：媒体和应用集成知识。
- [应用排障与会话归档](../archive/README.md)：诊断、显示、媒体、模块联调和历史会话证据。
- [XCRZ SigmaStar Demo readiness validation](../validation/project-readiness.md)、[权威边界决策候选](../decisions/project-boundary-decision-candidate.md)和[维护入口](runbooks/maintenance-entry.md)：结构控制资产，保持 `reviewing`。

## 当前权威边界

- 当前源码、分支、版本、构建和发布事实：源项目及其可复现验证证据。
- 长期摘要、决策记录、验证索引和跨项目方法：Knowledge Hub canonical Markdown 与 registry。
- `pcr02` 只是产品组 ID；不得作为独立 project/domain/path 重新写入内容。
- `status`、`owner`、`review_after`、promotion 和 authorization：registry/gate，不由目录名、Obsidian Graph 或本页文字推断。
- 当前 `decision_owner=unassigned`，`manual_validation_pending=true`；未完成 owner 和真实环境验证前保持 `reviewing`。

## Related

- [维护 runbook](runbooks/maintenance-entry.md)
- [边界决策候选](../decisions/project-boundary-decision-candidate.md)
- [readiness validation](../validation/project-readiness.md)
- [项目入口](../README.md)
