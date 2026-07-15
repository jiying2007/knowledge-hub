---
id: pcr02-ssc305-canonical-hardcut-20260715
title: PCR02 组级旧入口硬切收口实施记录候选
kind: decision
domain: projects/pcr02-ssc305
path: projects/pcr02-ssc305/decisions/pcr02-canonical-hardcut-20260715.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
review_after: '2026-10-15'
promotion: none
promotion_decision: none; structural canonical hardcut only, no active promotion or owner decision
tags:
- pcr02-ssc305
- canonical-path
- hardcut
- project-routing
- no-compatibility-layer
aliases:
- PCR02 规范入口硬切收口记录
generated_by_ai: true
ai_role: drafted-and-implemented-under-user-direction
ai_model_or_tool: Codex
ai_generated_at: '2026-07-15'
manual_validation_pending: false
review_status: structural-implementation-verified
decision_owner: unassigned
authorization_ref: auth-20260715-pcr02-canonical-hardcut
summary_zh: 记录 projects/pcr02 旧内容入口按真实仓归属一次性硬切到 pcr02-ssc305 与 xcrz-sigmastar-demo；不保留兼容目录、跳转页或双写路由。
related:
- projects/pcr02-ssc305/README.md
- projects/xcrz-sigmastar-demo/README.md
- registry/project-groups.json
- registry/project-routes.json
validation_refs:
- rtk bash tools/knowledge-check.sh --dry-run --json --diagnostics --as-of 2026-07-15
- rtk bash tools/knowledge-link-audit.sh --json --strict
- rtk python3 -m pytest -q
- rtk bash tools/knowledge-regression.sh --json --suite full --as-of 2026-07-15
- rtk bash tools/knowledge-final-gate.sh --json --final-profile product --full-regression --as-of 2026-07-15
- rtk git diff --check
---

# PCR02 组级旧入口硬切收口实施记录候选

## 结论边界

本次按用户 2026-07-15 当前会话“按建议全面优化落地”的明确指令，执行 Knowledge Hub 本仓结构硬切：

- `projects/pcr02-ssc305/` 是 `robot/pcr02_ssc305` SDK、kernel、boot、镜像、OTA、存储、板级硬件和产品集成事实的唯一项目入口。
- `projects/xcrz-sigmastar-demo/` 承接 `robot/xcrz_sigmastar_demo` 应用、诊断、媒体、显示应用层、模块集成和相关会话证据。
- `pcr02` 只保留为 `registry/project-groups.json` 中的 group 标识和检索关系，不再作为 `registry/projects.json` 项目、live route 或正文目录。
- 独立模块仓继续使用各自项目入口；跨仓记录只维护一份正文，通过 `related`、registry 和索引关联，不复制主文档。

本记录是 `reviewing` 实施与审计候选，不等于 owner decision、active promotion、发布授权或源项目事实签收。

## 迁移清单摘要

| 动作 | 数量 | 归属规则 |
|---|---:|---|
| 迁入 `pcr02-ssc305` | 52 | SDK/平台决策、ST77912 kernel/硬件、第三方编译基线、工程归档 |
| 迁入 `xcrz-sigmastar-demo` | 43 | 应用架构、runbook、诊断、媒体、模块联调、计划/报告/应用排障 |
| 删除重复入口 | 5 | 旧根 README 与重复 profile/runbook/decision/validation readiness 四件套 |
| 合计 | 100 | 每个旧目录文件恰好一个处置 |

原 `domain=projects/pcr02` 的 registry 条目保持原 ID、status、owner、review_after 和 promotion 语义；仅按正文或控制资产真实归属更新 `domain`、`path` 和引用。迁移不隐式提升任何条目。

## 无兼容层约束

- 不保留 `projects/pcr02/README.md` 跳转页。
- 不保留 symlink、deprecated route、双写目录或兼容 alias。
- 当前 README、registry、index、governance、工具默认输出和测试只使用最终 canonical path。
- Git 历史、历史 manifest、lifecycle event 和明确 provenance 可以保留旧路径，用于解释事件发生时的真实位置，但不得参与 live 路由。

## 授权与回滚

- 执行授权：`auth-20260715-pcr02-canonical-hardcut`。
- 授权只覆盖 Knowledge Hub 本仓路径迁移、重复资产删除和 live 控制面同步。
- 不授权 active promotion、owner gate 关闭、memory 写入、源项目修改、commit、push、merge、rebase、tag 或 release。
- 回滚必须仅反向恢复本次硬切差异，不得覆盖本轮开始前已有的用户工作区修改。

## 验证状态

当前状态：本次 Knowledge Hub 结构硬切已实施并完成自动化验证，`manual_validation_pending=false`。该字段只表示本记录所述目录、registry、route、index、tooling 和测试契约已经验证，不表示项目 owner、设备、源码、发布制品或现场证据已经签收。

| 验证面 | 结果 | 证据摘要 |
|---|---|---|
| 旧入口清零 | 通过 | `projects/pcr02/` 不存在；100 个旧文件恰好完成 52 个平台迁移、43 个应用迁移和 5 个重复控制资产删除 |
| 项目与 readiness | 通过 | 30/30 项目、30/30 route、120/120 readiness slot，生成漂移为 0；`pcr02` 仅保留为 1 个产品组关系 |
| 路由语义 | 通过 | `robot/pcr02_ssc305` 与 ST77912 查询路由到 `pcr02-ssc305`；`robot/xcrz_sigmastar_demo` 路由到 `xcrz-sigmastar-demo` |
| Hub 一致性 | 通过 | `knowledge-check`、strict link audit、orphan/body coverage、project readiness 与 `git diff --check` 均通过 |
| 单元测试 | 通过 | `88 passed` |
| 完整治理回归 | 通过 | `140/140`，默认 `jobs=4`，失败 ID 为空 |
| 离线恢复 | 通过 | candidate 与 committed HEAD 恢复演练均为 `pass`，无网络、无源项目写入 |
| product final gate | 平台通过 | `gate_status=pass`、`platform_productization_complete=true`、full regression ready；总体仍为 `needs-owner-review`，未声明 release complete 或 terminal maturity |

`needs-owner-review` 是既有真实项目证据、owner gate 和采用成熟度边界，不是本次 canonical hard cut 的技术失败。本记录继续保持 `status=reviewing`、`promotion=none`、`decision_owner=unassigned`，不代签 owner decision，也不提升 active。
