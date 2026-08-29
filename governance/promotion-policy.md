# 提升策略（Promotion Policy）

## 提升层级（Promotion Levels）

```text
personal -> project-current -> project-archive -> embedded-candidate -> team-published-runbook -> team-published-standard
codex-session -> codex-workflow -> skill/workflow/AGENTS candidate
```

Hub 统一按 L1 到 L5 沉淀：

- L1 输入候选：只做分类、去敏和价值判断。
- L2 单次会话/事件：记录单次结论、证据和风险。
- L3 项目阶段知识：服务同项目后续复用。
- L4 领域复用知识：沉淀跨项目 runbook、模式和工作流。
- L5 当前权威规则：当前事实、决策、标准、AGENTS、workflow 或 skill 候选。

嵌入式 L4/L5 使用双层落点：`domains/embedded/` 保存 reviewing 候选、提炼稿和 provenance；人工复核、去敏、目标仓全量门禁通过后，发布正文进入 `workspace://embedded-knowledge`。团队成员消费的已发布正文以目标团队仓为准，Hub 不把候选状态解释为团队发布。

任何 L1/L2 材料都不得自动提升为 L5；必须先有 owner、来源、验证、review_after、secret scan 和对应门禁结果。

## 必填条件（Requirements）

- 明确复用场景。
- 有来源路径。
- 有验证证据。
- 有 owner。
- 有 review_after。
- 已通过 secret scan。
- 已记录团队目标路径、source SHA256、目标成熟度和回滚。
- 只提炼稳定结论，不复制整篇历史材料。

## 拒绝原因（Rejection Reasons）

- 只有一次性上下文。
- 未验证。
- 过度项目特定。
- 涉及个人隐私或敏感信息。
- 已有同等 team knowledge。
