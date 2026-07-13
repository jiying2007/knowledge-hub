---
id: pcr02-readiness-profile-20260713
title: PCR02 项目画像候选
kind: project-current
domain: projects/pcr02
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
review_after: '2026-10-13'
review_status: ai-generated-project-readiness-pending-owner-and-real-validation
promotion: none
tags:
- pcr02
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
summary_zh: 记录 PCR02 的 registry 身份、仓库边界、已有 Hub 证据和权威边界；只作 reviewing 工作台，不声明源码或发布事实。
promotion_decision: none; structural readiness asset only, no active promotion or owner decision
path: projects/pcr02/current/project-profile.md
project_id: pcr02
readiness_slot: profile
aliases:
- pcr02 profile
- pcr02-profile
related:
- projects/pcr02/README.md
- projects/pcr02/current/runbooks/maintenance-entry.md
- projects/pcr02/decisions/project-boundary-decision-candidate.md
- projects/pcr02/validation/project-readiness.md
---

# PCR02 项目画像候选

> 本页是 AI 生成的 reviewing 控制资产，只复述 registry 身份和 Hub 已有证据。它不是当前源码、owner decision、设备状态或发布状态证明。

## 项目标识

| 字段 | 值 |
|---|---|
| project_id | `pcr02` |
| 类型 | `product-group` |
| repo boundary | `group` |
| 所属组 | `pcr02` |
| registry 状态 | `registered` |
| 本地源码映射 | `machine-local / not tracked` |
| Hub 已登记条目 | `95`；archived=78, reviewing=17 |

## 仓库边界

| repo_id | remote key | workspace ref | lifecycle |
|---|---|---|---|
| `pcr02-ssc305` | `robot/pcr02_ssc305` | `workspace://pcr02-ssc305` | `first-party` |
| `xcrz-sigmastar-demo` | `robot/xcrz_sigmastar_demo` | `workspace://xcrz-sigmastar-demo` | `first-party` |
| `pcr02-api` | `embedded/module/api` | `workspace://pcr02-api` | `first-party` |
| `pcr02-app` | `embedded/module/app` | `workspace://pcr02-app` | `first-party` |
| `pcr02-hdi` | `embedded/module/hdi` | `workspace://pcr02-hdi` | `first-party` |
| `pcr02-sensor` | `vosen/modules/sensor` | `workspace://pcr02-sensor` | `first-party` |
| `pcr02-daemon` | `embedded/app/daemon` | `workspace://pcr02-daemon` | `first-party` |
| `pcr02-cli` | `embedded/app/cli` | `workspace://pcr02-cli` | `first-party` |
| `pcr02-cmd-server` | `embedded/app/cmd_server` | `workspace://pcr02-cmd-server` | `first-party` |
| `pcr02-proto-c` | `embedded/app/proto_c` | `workspace://pcr02-proto-c` | `first-party` |
| `pcr02-wifi` | `embedded/module/wifi` | `workspace://pcr02-wifi` | `first-party` |
| `pcr02-mp4` | `embedded/module/mp4` | `workspace://pcr02-mp4` | `first-party` |
| `app-ota` | `embedded/app/app_ota` | `workspace://app-ota` | `first-party` |
| `app-product-test` | `embedded/app/app_product_test` | `workspace://app-product-test` | `first-party` |
| `app-tool` | `embedded/app/app_tool` | `workspace://app-tool` | `first-party` |
| `app-main` | `embedded/app/app_main` | `workspace://app-main` | `first-party` |

`workspace://` 是跨机器逻辑引用，不代表本机源码存在。使用 `knowledge-workspace-discover.sh --plan` 按 exact remote 只读发现，结果只写入未跟踪的 `local/workspaces.json`；绝对路径和动态 HEAD 不进入本页。

## 已有 Hub 证据

- [Diag UT 硬切进展](../archive/plans/2026-05-13-diag-ut-hard-switch-progress-plan.md)：`archived` / `project-archive`
- [Diag 测试使用指南](runbooks/diag-usage-guide.md)：`archived` / `project-current`
- [Engineering archive PCR02 archive corpus 2026-06-19](../archive/engineering-archive)：`archived` / `project-archive`
- [HDI API APP 模块功能总览](architecture/hdi-api-app-functional-overview.md)：`archived` / `project-current`
- [IR 补光与光敏控制优化计划](../archive/plans/2026-05-08-irlight-optimization-plan.md)：`archived` / `project-archive`
- [PCR02 /customer ro SD 升级阶段归档 2026-05-26](../archive/engineering-archive/pcr02/session/pcr02_customer_ro_sd_upgrade_20260526.md)：`archived` / `project-archive`
- [PCR02 AGENTS owner ready package 2026-06-20](../../../artifacts/manifests/pcr02-agents-owner-ready-package-20260620.md)：`archived` / `audit`
- [PCR02 ASAN owner ready package 2026-06-20](../../../artifacts/manifests/pcr02-asan-owner-ready-package-20260620.md)：`archived` / `audit`

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
