# PCR02 source-docs 正文剪枝账本 2026-06-25

本账本记录对 `projects/pcr02/archive/source-docs/` 的终态剪枝。

## 决策

- 删除旧 source 迁移正文副本，不再保留 `projects/pcr02/archive/source-docs/`。
- 不把旧 `docs/`、`knowledge/`、`tools/`、`scratch/`、项目根散落文本和旧 agent 规则作为新增知识入口。
- 保留必要治理证据：`sources/<source_id>/`、`registry/sources.json`、`registry/sources.json`、`registry/items.jsonl`、hard migration manifest、owner decision manifest 和本剪枝账本。
- `engineering-archive` 的终态正文不在 `source-docs`，保留于 `projects/pcr02/archive/engineering-archive/`。

## 边界

- 本账本不是正文备份。
- 需要查询历史来源时，只能通过 source control、registry、manifest 和 Git 历史追溯。
- 后续新会话、新归档、新排障记录不得写回 `source-docs` 或旧外部路径。
