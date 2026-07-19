# pcr02-project-knowledge 覆盖状态

## 结论

- Status: `hub-canonical`
- Classification: `retired-origin hash-only-provenance plus canonical targets`
- Checked at: `2026-06-25`

## 决策

pcr02-project-knowledge 的旧正文副本已按终态剪枝；Hub 仅保留 source control、hash/provenance、owner decision 和已落地的 canonical 项目正文。旧项目 knowledge 路径不再作为知识正文入口。

## 风险

project-specific 内容不能直接提升团队标准。

## 证据

- `registry/sources.json`
- `artifacts/manifests/knowledge-hub-source-coverage-closeout-20260624.jsonl`
- `sources/pcr02-project-knowledge/inventory.jsonl`

## 2026-07-18 dev 副本收口

- Source：`xcrz_sigmastar_demo_dev/knowledge`。
- Inventory：191 个非 `.git` 文件；178 个非缓存文件由在线核验的 `embedded/knowledge@cadbf4d6777319c8d43b15f842cbea002cd94cef` 保留，13 个 `.pyc` 明确排除。
- Deletion：`absorbed / exact-path deletion verified 2026-07-18`；嵌套 `.git` 只进入回滚备份和前缀 provenance，隔离恢复演练已确认元数据存在。
- Evidence：`artifacts/manifests/xcrz-demo-dev-three-dir-absorption-20260718.jsonl`、`projects/pcr02-ssc305/validation/2026-07-18-embedded-knowledge-absorption-validation.md`。

项目副本不再作为知识正文入口；远端 commit 引用不自动启用旧工具、skill、CI 或 owner 配置。
