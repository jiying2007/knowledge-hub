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

## 全量内容迁移验收（与控制面覆盖分别判定）

- `registry/sources.json` 和 `registry/retired-sources.jsonl` 定义来源归属和处置；`sources/*/inventory.jsonl` 中的根目录级 `covered` 或一次性汇总哈希**不等于源目录逐文件完整证明**。
- **源侧证据：**可访问的每个源应记录可信源修订或快照身份、完整文件列表、每文件字节数与 SHA-256；变更或删除后需要可核查的重扫记录。外部源不可访问时必须保持 `unverified`，绝不推断 `0 missing`。
- **目标侧证据：**每个文件必须有且仅有一个处置：经审核的当前 canonical 正文、历史 archive-only、合规 artifact-ref、只读 reference/summary 或明确 exclude；目标正文应有精确 ID、路径、SHA 和来源证据，且无双 active 权威。
- **审查边界：**全量归类完成不表示所有内容需要全文复制。raw session/history、源代码、日志、凭据与不具发布许可的外部资料继续只存引用或摘要。owner 决定、content review、产品/设备/生产资格与仓库 Terminal 是独立条件。
- **自动化：**`knowledge-orphan-files.sh --all --strict --convergence --json` 只读输出 Hub 内逐文件哈希、冻结集合归属、精确重复正文候选和 source inventory 证据粒度；`Quality` 和每日 `ai-maintenance-sweep` 使用该同一入口，不维护第二份 mutable 状态。AI 可建议保留／合并／拒绝，但没有逐项授权时不得删正文或代签审核。

## 停止条件

- 发现疑似 secret。
- canonical target 违反 authority boundary。
- source inventory 仍有 pending 或不安全 copy-body。
- 旧外部路径被构建、发布或脚本强依赖。
- 缺少 owner/review_after/check/no-check reason。
