# codex-history 覆盖状态

## 结论

- Status: `hub-main-indexed-source`
- Classification: `history jsonl discovery source`
- Checked at: `2026-06-24`

## 决策

Codex history 进入 Hub 主库 source registry；只做索引、摘要、候选和证据定位。

## 风险

raw history 行不能直接提升为 active fact。

## 证据

- `registry/sources.json`
- `artifacts/manifests/knowledge-hub-source-coverage-closeout-20260624.jsonl`
- `sources/codex-history/inventory.jsonl`
