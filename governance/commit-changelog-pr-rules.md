# 中文 Commit、Changelog 与 PR 规范

## 目标

让提交历史、变更说明和 PR 描述成为中文开发人员可读、可审计、可回退的长期资产。

## Commit

格式：

```text
<type>(scope): <中文动词短句>
```

规则：

- `summary` 使用简体中文，必要英文技术标识保留原样。
- `summary` 不超过 50 字，不加句号。
- 常用 `type`：`feat`、`fix`、`refactor`、`docs`、`test`、`chore`。
- `scope` 使用稳定边界，例如 `registry`、`governance`、`pcr02`、`codex`、`patents`。
- 知识资产类提交正文建议包含：背景、变更、验证、registry 影响、风险与回退。

## Changelog

- 标题和条目默认中文。
- 条目按影响分类：新增、变更、修复、迁移、治理、验证、已知风险。
- 知识库变更应引用 registry id，避免只写路径。
- 不写一次性过程日志，只写可复用、可审查的变化。

## PR

PR 标题与 commit subject 同风格。描述建议包含：

- `目的`：为什么需要这次变更。
- `变更范围`：改了哪些知识域、模板、registry 或工具。
- `registry 影响`：新增、更新或退役的 id。
- `验证证据`：命令、结果和 artifact 引用。
- `风险与回退`：如何撤销或降级。
- `开放问题`：需要 owner 或后续任务确认的事项。

涉及知识资产提升时，PR 必须说明 owner、status、review_after、source 和 validation_refs。

## 禁止事项

- 不用英文泛泛标题代替中文结论。
- 不在 changelog 中复制大段外部正文或 raw log。
- 不在 PR 中声明 active，除非来源、owner、状态、review 周期和证据已经确认。
- 不让自动化直接 commit、push、发布或写 memory。

## Review

- owner：`leiwenjun`
- review_after：`2026-09-18`
- validation_refs：`rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics`
