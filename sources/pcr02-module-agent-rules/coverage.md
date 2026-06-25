# pcr02-module-agent-rules 覆盖状态

## 结论

- Status: `hard-migrated-to-hub`
- Classification: `retired-origin agent-rules plus project-local-runtime-control plus hash-only-provenance`
- Checked at: `2026-06-25`

## 决策

pcr02-module-agent-rules 的历史 AGENTS 材料已完成硬迁移证据登记；历史 `AGENTS.md` 正文副本已从 Hub 旧迁移正文层剪枝，只保留 hash/provenance。Hub 不把项目本地 AGENTS 提升为全局规则或团队标准。当前源码仓及独立子仓的 `AGENTS.md` 作为项目本地 Codex 运行控制文件保留在源项目 Git 中。

## 风险

模块本地约束未经 owner review 不得提升为全局规则；源项目本地 `AGENTS.md` 不等于 Hub active rule。

## 证据

- `registry/sources.json`
- `artifacts/manifests/knowledge-hub-source-coverage-closeout-20260624.jsonl`
- `artifacts/manifests/pcr02-agent-rules-body-prune-20260625.jsonl`
- `sources/pcr02-module-agent-rules/inventory.jsonl`
