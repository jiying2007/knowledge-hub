# pcr02-project-docs 覆盖状态

## 结论

- Status: `hard-migrated-to-hub`
- Classification: `retired-origin copy-docs-and-artifacts`
- Checked at: `2026-06-24`

## 决策

pcr02-project-docs 的旧正文副本已按终态剪枝；Hub 仅保留 source control、hash/provenance、owner decision 和已落地的 `projects/pcr02/` canonical 项目正文。旧项目 docs 路径只保留 origin_path，不再作为新增归档或知识入口。

## 风险

owner-gated 历史内容仍不能绕过 owner/review 直接提升 active。

## 证据

- `registry/sources.json`
- `artifacts/manifests/knowledge-hub-source-coverage-closeout-20260624.jsonl`
- `sources/pcr02-project-docs/inventory.jsonl`
