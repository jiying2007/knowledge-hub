# pcr02-project-scratch 覆盖状态

## 结论

- Status: `hard-migrated-to-hub`
- Classification: `retired-origin hash-only-provenance`
- Checked at: `2026-06-25`

## 决策

pcr02-project-scratch 的旧 session/context/resume 正文副本已按终态剪枝；Hub 仅保留 hash/provenance，不进入 active facts 或 memory。

## 风险

scratch/handoff/memory candidates 不能直接提升 active 或写 memory。

## 证据

- `registry/sources.json`
- `artifacts/manifests/knowledge-hub-source-coverage-closeout-20260624.jsonl`
- `sources/pcr02-project-scratch/inventory.jsonl`
