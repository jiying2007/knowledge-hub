# codex-memories 覆盖状态

## 结论

- Status: `runtime-input-control`
- Classification: `runtime-input no-copy no-memory-write`
- Checked at: `2026-06-24`

## 决策

codex-memories 不是迁移正文源；Hub 只保留 sources/codex-memories 控制面和 runtime provenance，禁止自动写 memory。

## 风险

memory candidate 不得静默进入长期记忆或 active facts。

## 证据

- `registry/sources.json`
- `artifacts/manifests/knowledge-hub-source-coverage-closeout-20260624.jsonl`
- `sources/codex-memories/inventory.jsonl`
