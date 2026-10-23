# codex-history Source 策略

## 终态

该 source 必须通过 `sources/codex-history/` 在 Hub 内可恢复、可搜索、可审计。

## 当前策略

- `registry/sources.json` 的 `path` 已收敛到 `sources/codex-history`。
- 当前知识入口只使用 Hub 内路径。
- 通过 inventory 记录正文、附件、runtime input 或 hub-native 边界。

## 后续维护

- 新增归档、摘要和知识正文必须写入 Hub canonical 目录，不得写回旧 origin。
- runtime input 只抽取摘要、候选和证据索引；不复制 raw 全文，不把 raw 行提升为 active fact。

## 运行态输入专用边界（2026-10-23）

这里的“新增归档、摘要和知识正文”不授权导入 Codex raw history 行。该 source 仅保留可审计的来源身份和经授权、最小化的摘要或候选索引；原始对话/历史正文、个人内容、会话令牌、环境路径及账号信息不得自动复制或哈希导出。

摘要可以作为 `reviewing` 候选，但不得凭 source coverage 的历史 `checked_at` 自动晋升 `active`、刷新 `review_after` 或代表 owner 作决定。可复用事实应按当前 canonical item 与来源证据单独复核。
