# knowledge-hub-automation-runs 覆盖状态

## 结论

- Status: `hub-native-control`
- Classification: `hub-native ledger`
- Checked at: `2026-06-24`

## 决策

knowledge-hub-automation-runs 是 Hub 原生账本；source path 收敛为 sources/knowledge-hub-automation-runs，正文权威仍是 registry/automation-runs.jsonl。

## 风险

apply-with-review 必须引用授权账本；自动化默认 report-only。

## 证据

- `registry/sources.json`
- `artifacts/manifests/knowledge-hub-source-coverage-closeout-20260624.jsonl`
- `sources/knowledge-hub-automation-runs/inventory.jsonl`
