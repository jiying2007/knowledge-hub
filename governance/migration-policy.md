# Source 策略（Source Policy）

## 策略

- 先登记 source，再决定终态处置。
- 每个 registered source 必须有 `sources/<source_id>/README.md`、`inventory.jsonl`、`coverage.md` 和 `source-policy.md`。
- 旧外部路径只允许写入 `registry/sources.json.origin_path` 作为 provenance，不得作为 active entry、默认查询入口、fallback 或新增归档目的地。
- 可维护正文只保留一份 canonical body；raw session、history、source code、binary、log、secret-like config 和大附件只能登记摘要、引用、artifact-ref、archive-only 或 exclude。
- source policy、registry、index、manifest 和 Evidence Index 必须能解释终态处置。

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
