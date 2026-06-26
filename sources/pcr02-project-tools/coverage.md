# pcr02-project-tools 覆盖状态

## 结论

- Status: `hub-canonical`
- Classification: `retired-origin hash-only-provenance`
- Checked at: `2026-06-25`

## 决策

pcr02-project-tools 的旧可读文档副本已按终态剪枝；Hub 仅保留 source control、hash/provenance 和必要的命令契约/验证记录，工具代码不作为 Hub 正文源。

## 风险

脚本和工具逻辑仍属于源项目代码边界，不由 Hub 自动改写。

## 证据

- `registry/sources.json`
- `artifacts/manifests/knowledge-hub-source-coverage-closeout-20260624.jsonl`
- `sources/pcr02-project-tools/inventory.jsonl`
