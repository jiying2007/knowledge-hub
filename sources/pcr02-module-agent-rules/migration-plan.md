# pcr02-module-agent-rules 迁移计划

## 终态

该 source 必须通过 `sources/pcr02-module-agent-rules/` 在 Hub 内可恢复、可搜索、可审计。

## 当前批次

- `registry/sources.json` 的 `path` 已收敛到 `sources/pcr02-module-agent-rules`。
- 旧外部路径只保留为 `origin_path` 和 tombstone provenance。
- 通过 hard migration manifest、decommission manifest 和 inventory 记录正文、附件、runtime input 或 hub-native 边界。
- 源项目保留根目录及独立子仓 `AGENTS.md` 作为本地 Codex 运行控制文件；这些文件由源项目 Git 管理，不作为 Hub 知识正文双写。
- Hub source-docs 中历史 `AGENTS.md` 正文副本已剪枝，后续只保留 `artifacts/manifests/pcr02-agent-rules-body-prune-20260625.jsonl` 作为 hash/provenance。

## 后续批次

- 删除或剪枝外部 source 前，先完成授权账本、回滚路径和最终验证。
- 新增归档、摘要和知识正文必须写入 Hub canonical 目录；源项目 `AGENTS.md` 只维护本地运行控制规则。
- runtime input 只抽取摘要、候选和证据索引；不复制 raw 全文，不把 raw 行提升为 active fact。
