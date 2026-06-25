# codex-archive-registry 覆盖状态

## 结论

- Status: `hard-migrated-to-hub`
- Classification: `retired-origin copy-docs-and-artifacts`
- Checked at: `2026-06-24`

## 决策

codex-archive-registry 已硬迁移到 Hub Codex archive registry 终态目录；旧 archive registry 不再作为 active source path。

## 风险

旧 registry open session 不自动成为当前项目事实。

## 证据

- `registry/sources.json`
- `artifacts/manifests/knowledge-hub-source-coverage-closeout-20260624.jsonl`
- `sources/codex-archive-registry/inventory.jsonl`
