# pcr02-project-agent-config 覆盖状态

## 结论

- Status: `hard-migrated-control-only`
- Classification: `retired-origin agent-config`
- Checked at: `2026-06-24`

## 决策

pcr02-project-agent-config 作为配置/自动化边界已在 Hub 控制面退役外部 source path；旧配置路径不再作为知识源。

## 风险

配置可能含外部依赖或敏感信息；启用自动化前需授权和审计。

## 证据

- `registry/sources.json`
- `artifacts/manifests/knowledge-hub-source-coverage-closeout-20260624.jsonl`
- `sources/pcr02-project-agent-config/inventory.jsonl`
