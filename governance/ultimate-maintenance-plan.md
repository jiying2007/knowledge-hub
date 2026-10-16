---
title: Knowledge Hub long-term maintenance plan
summary_zh: Knowledge Hub 长期维护计划，约束 registry、index、source、owner gate、review_after、automation 和验证门禁的运营节奏。该 active 条目只作为 Hub
  维护标准，不自动关闭 owner gate、不提升项目事实、不写 memory、不发布远端状态。
tags:
- governance
- maintenance
id: knowledge-hub-ultimate-maintenance-plan
kind: standard
domain: governance
path: governance/ultimate-maintenance-plan.md
scope: team-general
visibility: team-internal
status: active
owner: leiwenjun
review_after: '2026-09-16'
review_status: active-control-plane-accepted
promotion: none
aliases:
- Knowledge Hub long-term maintenance plan
related:
- indexes/obsidian-home.md
---

# Knowledge Hub 长期维护终极方案

## 目标

建立统一知识控制面，长期治理工程知识、项目事实、历史归档、专利材料、Codex 工作流和个人草稿。

## 核心原则

1. 内容正文只维护一份。
2. 所有知识都有 `id`、`owner`、`scope`、`status`、`source` 和 `review_after`。
3. 项目、团队、个人、专利、Codex 会话、外部制品属于不同 domain。
4. Git 默认只保存轻量文本、索引、规则和工具；大文件只保存 URI、size、hash 和摘要。唯一例外是 owner 批准、体量受控且纳入 `artifacts/vault/` 逐文件 size/hash 完整性门禁的不可变附件集。
5. 自动化只能生成报告和候选；提升、删除、发布、写 memory 必须人工确认。

## 当前知识权威与消费层级（2026-08-21 起适用）

**知识权威不是简单的目录优先级。** 不同 subject/scope 的事实权威由已登记的 source、owner、生命周期、证据与明确的消费目标共同决定；跨领域冲突需要按适用范围和来源版本重新核验，不得只比较路径名。

| 范围 | 当前权威 | Hub 内角色 |
|---|---|---|
| 已发布的嵌入式团队标准、runbook | `workspace://embedded-knowledge` | `domains/embedded/` 仅保存 reviewing 提炼稿、候选和历史 provenance；不作为并行团队发布源 |
| PCR02 等项目当前事实、决策与验证 | `projects/<project>/current|decisions|validation/` 的已批准条目 | 项目证据需独立 owner、source、设备/发布/回滚资格；reviewing 仍非 active 事实 |
| 项目或团队历史 | `projects/<project>/archive/` 和 `domains/<domain>/archive/` | 只作历史可追溯性，不能覆盖新的可验证事实 |
| 专利资料与附件 | `domains/patents/`、合规 `artifacts/vault/` | 披露、法律状态、来源许可和公开范围单独审核 |
| Codex 治理与历史 | `domains/codex/` | 历史 session/memory 不自动生成 active 工作流或指令 |
| 个人候选 | `notes/personal/` | 不进入团队 active 检索或发布 |
| `~/.codex/memories` | 辅助回忆来源 | 永不作为唯一规则或工程事实权威 |

Hub 的统一目标是**单一知识控制面和每个适用范围的唯一正文权威**，不是把外部正式团队仓和全部原始材料重新复制一份。已签收的团队发布稿由目标 workspace 消费；Hub 按原始 source/hash、目标修订和发布资格保留引用，不能因索引可检索就自动认定内容已复核。

源控制与正文发布关系以 `governance/source-boundaries.md`、`governance/path-routing.md` 和当前 Registry 为准；本页仅解释原则，不另行维护 source 状态和动态计数。

## 生命周期

```text
capture -> classify -> normalize -> review -> active/archive -> review cycle -> supersede/retire
```

生命周期状态只描述 Hub 内部治理阶段，不等于新增目录层级：

- `capture`：临时输入、会话结论、排障片段或外部材料摘要，只能作为候选。
- `classify`：确认项目、domain、topic、owner、敏感性和是否需要归档。
- `normalize`：按模板补齐中文摘要、证据、边界、验证和回滚信息。
- `review`：进入 owner、source、promotion 或 final gate；AI 只能生成待审材料。
- `active`：通过 review 后成为当前事实、决策、runbook、standard 或 workflow。
- `archive`：保留历史证据、阶段结论、已关闭排障或过期材料。
- `supersede/retire`：由新条目替代或退役；删除只用于重复、缓存、误入和明确废弃草稿。

## 层级沉淀模型

长期知识按“从输入到稳定规则”的层级沉淀，低层材料不得自动升级为高层权威：

| 层级 | Hub 语义 | 典型落点 | 提升门槛 |
|---|---|---|---|
| L1 输入候选 | 临时输入、摘录、会话候选、review queue | `inbox/`、`manifests/*queue*`、候选 worksheet | 分类、去敏、确认是否值得保留 |
| L2 单次会话/事件 | 单次排障、发布、复盘或研究结论 | `projects/<project>/archive/`、`domains/codex/archive/` | 有证据、范围、结论和剩余风险 |
| L3 项目阶段知识 | 项目日报、阶段总结、验证批次、专题归档 | `projects/<project>/validation/`、`projects/<project>/archive/` | 能服务后续同项目工作 |
| L4 领域复用知识 | 跨项目模式、稳定 runbook、反复出现的问题 | `domains/embedded/runbooks/`、`domains/codex/` | 跨项目复用理由和验证证据 |
| L5 当前权威规则 | 当前事实、决策、标准、AGENTS、workflow、skill 候选 | `projects/<project>/current/`、`decisions/`、`standards/`、`governance/` | owner/review/check/final gate 全部闭环 |

约束：

- L1/L2 不能直接变成 L5；必须经过归一化、review、owner 和验证门禁。
- 原始会话、raw log、memory 和外部材料不能作为长期正文直接落盘；只能提炼为摘要、证据索引或候选。
- 不依赖向量数据库、自动热度衰减或自动遗忘来决定权威性；权威性由 registry、owner、status、review_after 和门禁结果决定。
- AI 可以生成候选、报告和差异分析；不得自动签署 owner decision、写 memory、提升 active 或删除历史证据。

## 提升规则

- `personal-note` 可提升为 `project-current`，需要 owner 和来源。
- `project-current` 可关闭为 `project-archive`，需要 source policy、registry/index 和 Evidence Index 说明。
- `project-archive` 可摘要提升为 `embedded/runbook` 或 `embedded/standard`，需要跨项目复用理由和验证证据。
- `codex-session` 可提升为 `codex-workflow`，再经审查进入 skill、workflow recipe 或 AGENTS。

## 退役规则

- 默认不删除历史正文，先标记 `superseded` 或 `archived`。
- 删除仅允许用于重复副本、缓存、大文件误入、明确废弃草稿。
- 删除前必须确认没有 registry、source-policy、index、owner gate、authorization 或 manifest 仍把它作为当前入口。
