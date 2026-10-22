# pcr02-project-knowledge Source 策略

## 终态

该 source 必须通过 `sources/pcr02-project-knowledge/` 在 Hub 内可恢复、可搜索、可审计。

## 当前策略

- `registry/sources.json` 的 `path` 已收敛到 `sources/pcr02-project-knowledge`。
- 当前知识入口只使用 Hub 内路径。
- 通过 inventory 记录正文、附件、runtime input 或 hub-native 边界。

## 后续维护

- 新增归档、摘要和知识正文必须写入 Hub canonical 目录，不得写回旧 origin。
- runtime input 只抽取摘要、候选和证据索引；不复制 raw 全文，不把 raw 行提升为 active fact。

## 规范正文与来源控制分离（2026-10-23）

该目录只存 source inventory、coverage、policy 与历史 provenance。上文“写入 Hub canonical 目录”必须依据当前 `registry/project-routes.json` 和 `registry/items.jsonl` 选择唯一项目正文路径，不表示把第二份正文复制进 `sources/pcr02-project-knowledge/`，更不表示旧外部 `knowledge/` 路径恢复为权威。

新内容先按来源、时间、项目归属和正文哈希进行受治理候选复核；历史 `absorbed`、`covered` 或 owner 建议不能自动证明当前外部源码可达、已获 owner 批准或产品验证完成。
