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
