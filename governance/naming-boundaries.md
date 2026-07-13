---
title: 中英文命名边界
summary_zh: 定义中文标题、英文路径、registry id、tag、术语和模板字段的命名边界，防止混用、旧名残留和检索漂移。该 active 规范只约束命名维护，不改变既有项目事实或 owner decision。
tags:
- governance
- naming
- zh-cn
- registry
id: knowledge-hub-naming-boundaries
kind: standard
domain: governance
path: governance/naming-boundaries.md
scope: team-general
visibility: team-internal
status: active
owner: leiwenjun
review_after: '2026-09-18'
review_status: human-reviewed-accepted
promotion: none
aliases:
- 中英文命名边界
related:
- indexes/obsidian-home.md
---

# 中英文命名边界

## 目标

在中文可读性和机器稳定性之间建立清晰边界：人读内容默认中文，机器字段保持稳定英文枚举和 ASCII 路径。

## 机器字段

以下字段保持英文和稳定枚举：

- `id`
- `kind`
- `domain`
- `path`
- `scope`
- `visibility`
- `status`
- `source`
- `created_at`
- `updated_at`
- `review_after`

`id` 和 `path` 使用 ASCII、kebab-case 或现有仓库约定，避免脚本、链接和跨平台路径出错。

## 人读字段

以下内容默认中文：

- `title`
- `summary_zh` / `title_zh`
- 正文标题和小节标题。
- 结论、证据摘要、风险、下一步。
- 迁移说明、review 说明、owner worksheet。
- changelog 和 PR 描述。

需要保留英文时，提供中文解释或中文摘要。

## 推荐补充字段

长期条目可使用：

- `title_zh`
- `summary_zh`
- `source_language`
- `primary_language`
- `translation_status`
- `terminology_status`
- `glossary_refs`

这些字段用于增强可读性和复核，不替代 registry required fields。

## 历史字段读取边界

- 现有 PCR02 历史文档中的 `doc_type`、`knowledge_type`、`maturity` 只允许作为迁移审计、历史读取或负向回归输入识别。
- `summary` 等旧字段只允许作为历史材料读取辅助；新条目必须使用 `summary_zh`、`title_zh` 和中文摘要正文。
- 新模板优先使用 `kind`、`status`、`scope`、`visibility`。
- 新模板、registry 新条目、工具默认输出和新消费方不得继续生成或依赖旧字段。历史字段不得与 registry 字段冲突；冲突时以 registry 为准。

## Review

- owner：`leiwenjun`
- review_after：`2026-09-18`
- validation_refs：`rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics`
