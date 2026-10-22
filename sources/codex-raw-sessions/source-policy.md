# codex-raw-sessions Source 策略

## 终态

该 source 必须通过 `sources/codex-raw-sessions/` 在 Hub 内可恢复、可搜索、可审计。

## 当前策略

- `registry/sources.json` 的 `path` 已收敛到 `sources/codex-raw-sessions`。
- 当前知识入口只使用 Hub 内路径。
- 通过 inventory 记录正文、附件、runtime input 或 hub-native 边界。

## 后续维护

- 新增归档、摘要和知识正文必须写入 Hub canonical 目录，不得写回旧 origin。
- runtime input 只抽取摘要、候选和证据索引；不复制 raw 全文，不把 raw 行提升为 active fact。

## 运行态输入专用边界（2026-10-23）

本来源的 `runtime-input-reference-summary-only` 是决定性限制：Hub 只能保留授权的来源引用、去标识化摘要和证据索引，不保存 raw session 全文。上文通用的“新增归档、摘要和知识正文”并不改变此限制，也不授权重新回源下载历史会话或将其内容进入团队 `active`。

访问和提取必须先做独立隐私/ACL/许可审核；无法确认的材料保持 `defer`，不可默认按公开文档处理，也不可用根目录覆盖率证明逐条内容有效。
