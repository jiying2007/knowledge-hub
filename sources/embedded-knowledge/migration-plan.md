# embedded-knowledge 迁移计划

## 终态

该 source 必须通过 `sources/embedded-knowledge/` 在 Hub 内可恢复、可搜索、可审计。

正文终态位于 `domains/embedded/*`；旧过渡快照目录已删除，不再兼容。

## 当前批次

- `registry/sources.json` 的 `path` 已收敛到 `sources/embedded-knowledge`。
- 旧外部路径只保留为 `origin_path` 和 tombstone provenance。
- 通过 `source-hard-migration-20260625.jsonl`、decommission manifest 和 inventory 记录正文、附件、runtime input 或 hub-native 边界。
- `registry/sources.json` 的 canonical target 已收敛到 `domains/embedded`。

## 后续批次

- 删除或剪枝外部 source 前，先完成授权账本、回滚路径和最终验证。
- 新增归档、摘要和知识正文必须写入 Hub canonical 目录，不得写回旧 origin。
- 新增 embedded team 知识正文必须按内容类型写入 `domains/embedded/{runbooks,standards,architecture,skills,templates,governance,tools}`，不得写入 archive 快照路径。
- runtime input 只抽取摘要、候选和证据索引；不复制 raw 全文，不把 raw 行提升为 active fact。
