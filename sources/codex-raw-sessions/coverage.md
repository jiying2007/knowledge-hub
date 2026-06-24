# codex-raw-sessions 覆盖状态

## 结论

- Status: `runtime-input-control`
- Classification: `runtime-input reference-summary-only`
- Checked at: `2026-06-24`

## 决策

codex-raw-sessions 只作为运行态输入 provenance；Hub source path 为 sources/codex-raw-sessions，不复制 raw session 全文。

## 风险

raw session 可能含上下文噪音或敏感信息，不进入正文层。

## 证据

- `registry/sources.json`
- `artifacts/manifests/knowledge-hub-source-coverage-closeout-20260624.jsonl`
- `sources/codex-raw-sessions/inventory.jsonl`
