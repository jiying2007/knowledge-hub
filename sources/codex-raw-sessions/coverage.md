# codex-raw-sessions 覆盖状态

## 结论

- Status: `hub-main-reference-source`
- Classification: `raw session reference source`
- Checked at: `2026-06-24`

## 决策

Codex raw sessions 进入 Hub 主库 source registry；只做引用、摘要和证据定位。

## 风险

raw session 可能包含上下文噪音或敏感信息，不进入正文层。

## 证据

- `registry/sources.json`
- `artifacts/manifests/knowledge-hub-source-coverage-closeout-20260624.jsonl`
- `sources/codex-raw-sessions/inventory.jsonl`
