---
title: 中文术语表规范
summary_zh: 定义 Hub 内中文术语、英文技术标识和中英边界的维护规则，避免同义词漂移、翻译口径冲突和检索噪音。该 active 规范只提供术语控制面，不替代证据、registry 字段或项目 owner 签收。
tags:
- governance
- zh-cn
- glossary
- terminology
id: knowledge-hub-glossary-rules
kind: standard
domain: governance
path: governance/glossary.md
scope: team-general
visibility: team-internal
status: active
owner: leiwenjun
review_after: '2026-09-18'
review_status: human-reviewed-accepted
promotion: none
aliases:
- 中文术语表规范
related:
- indexes/obsidian-home.md
---

# 中文术语表规范

## 目标

术语表用于统一长期知识资产中的中文表达，避免同一概念出现多个叫法。术语表不是普通笔记，只有跨文档可复用、可复核的术语才进入本规范。

## 条目字段

每个术语条目建议包含：

| 字段 | 含义 |
| --- | --- |
| `term_zh` | 推荐中文术语 |
| `term_en` | 英文术语或缩写 |
| `preferred_zh` | 正文中优先使用的中文表达 |
| `allowed_aliases` | 允许的别名 |
| `forbidden_terms` | 不建议继续使用的叫法 |
| `definition_zh` | 中文定义 |
| `domain` | 适用领域 |
| `scope` | 团队通用、项目特定或个人草稿 |
| `source` | 来源或依据 |
| `owner` | 维护负责人 |
| `status` | `draft`、`reviewing`、`active` 等 |
| `review_after` | 下一次复核日期 |
| `examples` | 推荐用法示例 |

## 使用规则

- registry 和模板可以引用术语表，但不能用术语表替代证据。
- 项目临时叫法不能直接提升为团队术语。
- PCR02 project-specific 术语默认留在 `projects/pcr02/`，不得直接进入 `domains/embedded/standards/`。
- 同一术语有冲突时，优先保留更小范围的项目术语，并记录差异。

## 示例

| term_zh | term_en | preferred_zh | scope | status |
| --- | --- | --- | --- | --- |
| 地址消毒器 | ASAN | ASAN 地址消毒器 | team-general | reviewing |
| 制品引用 | artifact-ref | artifact-ref 制品引用 | team-general | active |
| 只读报告模式 | report-only | report-only 只读报告模式 | team-general | active |

## Review

- owner：`leiwenjun`
- review_after：`2026-09-18`
- validation_refs：`rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics`
