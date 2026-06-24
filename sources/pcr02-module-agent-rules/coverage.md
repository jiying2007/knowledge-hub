# pcr02-module-agent-rules 覆盖状态

## 结论

- Status: `hard-migrated-to-hub`
- Classification: `retired-origin agent-rules`
- Checked at: `2026-06-24`

## 决策

pcr02-module-agent-rules 已硬迁移到 Hub PCR02 source-docs archive；模块 AGENTS 旧路径不再作为 Hub 规则来源。

## 风险

模块本地约束未经 owner review 不得提升为全局规则。

## 证据

- `registry/sources.json`
- `artifacts/manifests/knowledge-hub-source-coverage-closeout-20260624.jsonl`
- `sources/pcr02-module-agent-rules/inventory.jsonl`
