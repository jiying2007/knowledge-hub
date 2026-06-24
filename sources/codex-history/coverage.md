# codex-history 覆盖状态

## 结论

- Status: `runtime-input-control`
- Classification: `runtime-input index-summary-only`
- Checked at: `2026-06-24`

## 决策

codex-history 只作为运行态输入 provenance；Hub source path 为 sources/codex-history，不把 raw history 行复制为正文。

## 风险

raw history 行不能直接提升为 active fact。

## 证据

- `registry/sources.json`
- `artifacts/manifests/knowledge-hub-source-coverage-closeout-20260624.jsonl`
- `sources/codex-history/inventory.jsonl`
