# Sources

外部或旧知识源的人读边界说明放在这里。

这里不是旧 source 正文存放区，也不是兼容旧入口。终态下每个
`sources/<source_id>/` 目录只保留 Hub 内 source 控制面四件套：

- `README.md`
- `inventory.jsonl`
- `coverage.md`
- `migration-plan.md`

这些文件用于恢复 source 身份、覆盖状态、迁移证据和退役策略；正文、
附件和历史快照必须落在对应 canonical target、artifact vault、registry
或 migration manifest 中。

权威账本仍是：

- `registry/sources.json`
- `indexes/by-source.md`
- 最新 source coverage closeout

不要在这里复制 raw log、binary、源码包、raw session 或大附件正文。
