# embedded-knowledge 覆盖状态

## 结论

- Status: `hard-migrated-to-hub`
- Classification: `retired-origin copy-docs`
- Checked at: `2026-06-25`

## 决策

embedded-knowledge 已从过渡快照完整归位到 Hub canonical embedded domain；正文权威位于 `domains/embedded/*`，`sources/embedded-knowledge` 只保留控制面，旧路径只保留 `origin_path` / tombstone provenance。

## 风险

历史 team knowledge 不自动成为 active standard；后续提升仍需按 Hub owner/review 规则拆分。

## 证据

- `registry/sources.json`
- `artifacts/manifests/source-hard-migration-20260625.jsonl`
- `sources/embedded-knowledge/inventory.jsonl`
- `domains/embedded/`
