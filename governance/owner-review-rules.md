# Owner Review 规范

## 目标

Owner review 用于确认知识条目的权威状态、适用范围和生效条件，避免草稿、会话记录、推断或项目临时材料误变成 active 事实。

## 适用场景

- 将 `draft` 或 `reviewing` 提升为 `active`。
- 将源项目 docs 迁移为 Knowledge Hub 正文。
- 将外部资料吸收为团队规范或 runbook。
- 将会话记录、排障记录、owner worksheet 中的结论提升为当前事实。
- 决定条目是 active、archived、superseded、rejected 还是 archive-only。

## Owner 必答问题

- 这个条目的 owner 是谁。
- 这个条目的适用项目、模块、版本和环境是什么。
- 这个条目是否是当前有效事实。
- 证据是否足够，证据路径是什么。
- 是否存在更权威的 source。
- 何时 review_after。
- 如果出错，如何回退或 supersede。

## 签核结果

建议使用以下状态：

| 状态 | 含义 |
| --- | --- |
| `approved-active` | 可登记为 active |
| `approved-reviewing` | 可保留 reviewing，等待进一步证据 |
| `archive-only` | 只作历史材料，不进入当前事实 |
| `superseded` | 已被新条目替代 |
| `rejected` | 不纳入长期知识 |
| `blocked` | 缺 owner、证据或状态判断 |

## 禁止事项

- 不把 owner 未确认的项目特定材料提升到团队标准。
- 不把 memory candidates 当作项目事实。
- 不把 `.session`、handoff、raw log 或 release binary 写成 active 正文。
- 不在缺少 source、review_after 或证据时声明 active。

## Review

- owner：`leiwenjun`
- review_after：`2026-09-18`
- validation_refs：`tools/knowledge-check.sh --dry-run`
