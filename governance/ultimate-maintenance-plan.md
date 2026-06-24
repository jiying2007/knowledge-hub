# Knowledge Hub 长期维护终极方案

## 目标

建立统一知识控制面，长期治理工程知识、项目事实、历史归档、专利材料、Codex 工作流和个人草稿。

## 核心原则

1. 内容正文只维护一份。
2. 所有知识都有 `id`、`owner`、`scope`、`status`、`source` 和 `review_after`。
3. 项目、团队、个人、专利、Codex 会话、外部制品属于不同 domain。
4. Git 只保存轻量文本、索引、规则和工具；大文件只保存 URI、size、hash 和摘要。
5. 自动化只能生成报告和候选；提升、删除、发布、写 memory 必须人工确认。

## 权威等级

1. `domains/embedded/standards/`
2. `domains/embedded/runbooks/`
3. `projects/<project>/current/`
4. `projects/<project>/decisions/`
5. `projects/<project>/archive/`
6. `domains/patents/`
7. `domains/codex/`
8. `notes/personal/`
9. `~/.codex/memories`

`~/.codex/memories` 永远不是规则或工程事实权威源。

## 生命周期

```text
capture -> classify -> normalize -> review -> active/archive -> review cycle -> supersede/retire
```

## 提升规则

- `personal-note` 可提升为 `project-current`，需要 owner 和来源。
- `project-current` 可关闭为 `project-archive`，需要迁移记录。
- `project-archive` 可摘要提升为 `embedded/runbook` 或 `embedded/standard`，需要跨项目复用理由和验证证据。
- `codex-session` 可提升为 `codex-workflow`，再经审查进入 skill、workflow recipe 或 AGENTS。

## 退役规则

- 默认不删除历史正文，先标记 `superseded` 或 `archived`。
- 删除仅允许用于重复副本、缓存、大文件误入、明确废弃草稿。
- 删除前必须有 `migrations.jsonl` 或 tombstone 记录。
