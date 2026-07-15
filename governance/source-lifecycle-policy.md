# Source 生命周期策略（Source Lifecycle Policy）

## 策略

- 先登记 source，再决定唯一处置结果。
- 每个 current 或 retired source 必须有 `sources/<source_id>/README.md`、`inventory.jsonl`、`coverage.md` 和 `source-policy.md`。
- 旧外部路径只允许写入 source registry 的 `origin_path` 作为 provenance；current source 位于 `registry/sources.json`，已关闭来源位于 `registry/retired-sources.jsonl`，不得作为 active entry、默认查询入口、fallback 或新增归档目的地。
- 迁移过程账本、dry-run、applied、classification 和 source inventory 从 current item registry 退出后，只能进入 `registry/retired-process-ledger.jsonl`；它们不再作为知识正文、默认搜索入口或 owner gate 关闭依据。
- 可维护正文只保留一份 canonical body；raw session、history、source code、binary、log、secret-like config 和大附件只能登记摘要、引用、artifact-ref、archive-only 或 exclude。
- source policy、registry、index、manifest 和 Evidence Index 必须能解释当前唯一处置结果。

## source-policy 必填信息

- source id 和 Hub source control 路径。
- 当前 canonical target、artifact target 或 exclude/reference 原因。
- owner、review_after、check 或 no-check reason。
- raw copy-body safety 判断。
- 验证命令和 Evidence Index。

## 停止条件

- 发现疑似 secret。
- canonical target 违反 authority boundary。
- source inventory 仍有 pending 或不安全 copy-body。
- 旧外部路径被构建、发布或脚本强依赖。
- 缺少 owner/review_after/check/no-check reason。
