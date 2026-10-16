---
title: AI 生成内容标注规范
summary_zh: 规定 AI 生成、AI 摘要、AI 分类和人工/受托复核字段的标注方式，确保内容来源、复核状态和提升边界可追溯。该 active 规范不允许伪造人工复核、不把 AI 复核等同 owner decision。
tags:
- governance
- ai-provenance
- human-review
- zh-cn
id: knowledge-hub-ai-content-labeling-rules
kind: standard
domain: governance
path: governance/ai-generated-content-labeling.md
scope: team-general
visibility: team-internal
status: active
owner: leiwenjun
review_after: '2026-09-18'
review_status: human-reviewed-accepted
promotion: none
aliases:
- AI 生成内容标注规范
related:
- indexes/obsidian-home.md
---

# AI 生成内容标注规范

## 目标

AI 可以辅助分类、摘要、翻译、重写和草拟，但 AI 输出不能自动成为事实、规则或 active 条目。本文约束 AI provenance 和人工复核要求。

## 推荐字段

AI 参与过的条目建议记录：

- `generated_by_ai`
- `ai_role`
- `ai_model_or_tool`
- `ai_generated_at`
- `human_reviewed_by`
- `human_reviewed_at`
- `review_basis`
- `evidence_refs`

`ai_role` 建议值：

- `none`
- `drafted`
- `summarized`
- `translated`
- `rewritten`
- `classified`
- `extracted`

## 提升条件

AI 生成或加工的内容进入 active、团队标准、AGENTS、skill 或 workflow 前，必须满足：

- 有 source。
- 有 evidence_refs。
- 有 human_reviewed_by。
- 有 review_basis。
- 有 owner。
- 有 review_after。
- 已通过 secret scan。
- 没有把 project-specific 内容提升为团队标准。

## 人工/受托内容审核的正文版本绑定

- **新增当前正文的人工审核记录**应同时保存经过真实审阅的 `human_review_content_sha256`，并与当前文件字节的 SHA-256 相等；reviewer、时间、证据和审核理由不能替代正文身份。
- 历史有审核字段、但缺少该哈希的条目只证明**存在历史审核记录**，不能单凭这些字段证明当前正文仍对应当时审核的版本。机器应分开统计“历史有审核字段”和“当前正文哈希已绑定”。
- 对仍为 `active` / `reviewing` 的 AI 条目，缺少哈希或正文发生漂移应生成只读复核异常，交由真实审核证据确认；不要批量生成签名、自动填写哈希、延期 review_after 或提升 active。历史 `archived` 条目按归档完整性而非当前发布标准分层处理。
- 历史已有人工审核字段、但缺少当前正文 SHA 的条目维持 `human-review-current-body-unbound` 人工复核队列（P1）；不得视为当前版本已审核。它仍阻断 product terminal（`product_blocking_final_gate=true`），但不冒充运行或数据损坏故障。真正缺少人工审核字段的 active 条目及已绑定 SHA 但正文漂移的 active 条目仍保持 P0 阻断。
- 受托 AI 复核须有真实、可重放的请求证明和独立校验证据；`request_proof=unverified` 只能保持未验证，不得转换为已签收。

## Memories 边界

`~/.codex/memories` 只能作为辅助召回来源。来自 memories 的内容必须标注为辅助来源，不能作为唯一 source，也不能直接写入当前项目事实。

## 禁止事项

- 不把 AI 摘要当作原始证据。
- 不把 AI 归纳出的推断写成已验证结论。
- 不静默写入 `~/.codex/memories`。
- 不让自动化无人审查地提升、发布、提交或删除。

## Review

- owner：`leiwenjun`
- review_after：`2026-09-18`
- validation_refs：`rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics`
