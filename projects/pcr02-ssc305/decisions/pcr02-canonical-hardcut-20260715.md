---
aliases:
- PCR02 项目组规范入口边界
authorization_ref: auth-20260715-pcr02-canonical-hardcut
related:
- projects/pcr02-ssc305/README.md
- projects/xcrz-sigmastar-demo/README.md
- registry/project-groups.json
- registry/project-routes.json
id: pcr02-ssc305-canonical-hardcut-20260715
title: PCR02 项目组规范入口边界决策候选
kind: decision
domain: projects/pcr02-ssc305
path: projects/pcr02-ssc305/decisions/pcr02-canonical-hardcut-20260715.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: user-directed-hub-maintenance
  from: current-session canonical project-group boundary consolidation
review_after: '2026-10-15'
review_status: human-reviewed-accepted
content_review_status: accepted
evidence_validation_status: pending
promotion: none
promotion_decision: none; canonical project-group boundary candidate only, no active promotion or owner decision
tags:
- pcr02-ssc305
- canonical-path
- project-boundary
- project-routing
- single-source-of-truth
validation_refs:
- projects/pcr02-ssc305/decisions/pcr02-canonical-hardcut-20260715.md
- rtk bash tools/knowledge-check.sh --dry-run --json --diagnostics --as-of 2026-07-15
- rtk bash tools/knowledge-final-gate.sh --json --final-profile product --regression-suite full --as-of 2026-07-15
- rtk bash tools/knowledge-link-audit.sh --json --strict
- rtk python3 -m pytest -q
- rtk bash tools/knowledge-regression.sh --json --suite full --as-of 2026-07-15
- rtk git diff --check
evidence_strength: reviewing-validation-pending
evidence_refs:
- projects/pcr02-ssc305/decisions/pcr02-canonical-hardcut-20260715.md
- rtk bash tools/knowledge-check.sh --dry-run --json --diagnostics --as-of 2026-07-15
- rtk bash tools/knowledge-final-gate.sh --json --final-profile product --regression-suite full --as-of 2026-07-15
created_at: '2026-07-15'
updated_at: '2026-07-19'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-07-15'
manual_validation_pending: false
decision_owner: unassigned
summary_zh: 定义 PCR02 项目组唯一当前知识入口与仓库归属：SSC305 平台事实进入 pcr02-ssc305，应用事实进入 xcrz-sigmastar-demo，pcr02 仅作为项目组关系标识。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
---

# PCR02 项目组规范入口边界决策候选

## 结论边界

本决策候选定义 PCR02 项目组在 Knowledge Hub 中的唯一当前边界：

- `projects/pcr02-ssc305/` 是 `robot/pcr02_ssc305` SDK、kernel、boot、镜像、OTA、存储、板级硬件和产品集成事实的唯一项目入口。
- `projects/xcrz-sigmastar-demo/` 承接 `robot/xcrz_sigmastar_demo` 应用、诊断、媒体、显示应用层、模块集成和相关会话证据。
- `pcr02` 只作为 `registry/project-groups.json` 中的 group 标识和检索关系，不是 `registry/projects.json` 项目、live route 或正文目录。
- 独立模块仓继续使用各自项目入口；跨仓记录只维护一份正文，通过 `related`、registry 和索引关联，不复制主文档。

本记录是 `reviewing` 实施与审计候选，不等于 owner decision、active promotion、发布授权或源项目事实签收。

## 结构职责

| 入口 | 唯一职责 |
|---|---|
| `projects/pcr02-ssc305/` | SDK、kernel、boot、镜像、OTA、存储、板级硬件、平台决策与工程归档 |
| `projects/xcrz-sigmastar-demo/` | 应用架构、诊断、媒体、显示应用层、模块集成、计划与应用排障 |
| `projects/pcr02-*` 独立模块 | 各自 Git 仓对应的项目事实、决策、验证与归档 |
| `pcr02` group | 跨项目检索、成员关系和产品组导航，不承载正文 |

每条正文只维护一个 canonical path；跨项目关系通过 `related`、registry 和索引表达。结构整理不改变条目的 status、owner、review_after 或 promotion 语义。

## 唯一入口契约

- README、registry、index、governance、工具输出和测试只引用上述 canonical project entry。
- `registry/project-routes.json` 只包含当前项目 route；group 关系不生成正文 route。
- 不创建跳转正文、symlink、双写目录或备用 alias 路由。
- Git history、已封存 manifest 和 lifecycle event 只作 provenance，不参与默认检索、路由、正文新增或 owner gate。

## 授权与回滚

- 执行授权：`auth-20260715-pcr02-canonical-hardcut`。
- 授权只覆盖 Knowledge Hub 本仓 canonical 边界整理和 live 控制面同步。
- 不授权 active promotion、owner gate 关闭、memory 写入、源项目修改、commit、push、merge、rebase、tag 或 release。
- 回滚必须只恢复本决策对应的 Hub 边界差异，不得覆盖本轮开始前已有的用户工作区修改。

## 验证状态

当前状态：本决策描述的目录、registry、route、index、tooling 和测试契约已经自动验证，`manual_validation_pending=false`。该字段不表示项目 owner、设备、源码、发布制品或现场证据已经签收。

| 验证面 | 结果 | 证据摘要 |
|---|---|---|
| canonical 唯一性 | 通过 | project registry、route registry、当前索引与默认工具输出只暴露 canonical project entry；`pcr02` 仅为 group 关系 |
| 项目与 readiness | 通过 | 30/30 项目、30/30 route、120/120 readiness slot，生成漂移为 0；`pcr02` 仅保留为 1 个产品组关系 |
| 路由语义 | 通过 | `robot/pcr02_ssc305` 与 ST77912 查询路由到 `pcr02-ssc305`；`robot/xcrz_sigmastar_demo` 路由到 `xcrz-sigmastar-demo` |
| Hub 一致性 | 通过 | `knowledge-check`、strict link audit、orphan/body coverage、project readiness 与 `git diff --check` 均通过 |
| 单元测试 | 通过 | 当前测试集全部通过 |
| 完整治理回归 | 通过 | `140/140`，默认 `jobs=4`，失败 ID 为空 |
| 离线恢复 | 通过 | candidate 与 committed HEAD 恢复演练均为 `pass`，无网络、无源项目写入 |
| product final gate | 平台通过 | `gate_status=pass`、`platform_productization_complete=true`、full regression ready；总体仍为 `needs-owner-review`，未声明 release complete 或 terminal maturity |

`needs-owner-review` 表示真实项目证据和采用成熟度尚待 owner 闭环，不是当前 canonical 边界的技术失败。本记录继续保持 `status=reviewing`、`promotion=none`、`decision_owner=unassigned`，不代签 owner decision，也不提升 active。
