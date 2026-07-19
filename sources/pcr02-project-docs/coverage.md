# pcr02-project-docs 覆盖状态

## 结论

- Status: `hub-canonical`
- Classification: `retired-origin hash-only-provenance plus owner-approved canonical targets`
- Checked at: `2026-06-25`

## 决策

pcr02-project-docs 的旧正文副本已按终态剪枝；Hub 仅保留 source control、hash/provenance、owner decision 和已落地的 projects/pcr02 canonical 项目正文。旧项目 docs 路径只保留 origin_path，不再作为新增归档或知识入口。

## 风险

owner-gated 历史内容仍不能绕过 owner/review 直接提升 active。

## 证据

- `registry/sources.json`
- `artifacts/manifests/knowledge-hub-source-coverage-closeout-20260624.jsonl`
- `sources/pcr02-project-docs/inventory.jsonl`

## 2026-07-18 dev 副本收口

- Source：`xcrz_sigmastar_demo_dev/docs`。
- Inventory：44 个文件；27 个由既有 Hub hash/provenance 覆盖，17 个未覆盖文件已在项目验证条目中保留完整文本。
- Deletion：`absorbed / exact-path deletion verified 2026-07-18`；授权 `auth-20260718-xcrz-demo-dev-docs-knowledge-scratch-absorb-delete` 已使用，恢复演练 243/243 hash 匹配。
- Evidence：`artifacts/manifests/xcrz-demo-dev-three-dir-absorption-20260718.jsonl`、`projects/xcrz-sigmastar-demo/validation/2026-07-18-dev-copy-three-dir-absorption-validation.md`。

旧 origin 和 dev 副本都不再作为新增知识入口；附录中保留的源 frontmatter 不创建 active 状态或 owner decision。
