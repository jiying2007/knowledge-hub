# pcr02-project-scratch 覆盖状态

## 结论

- Status: `hub-canonical`
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

## 2026-07-18 dev 副本收口

- Source：`xcrz_sigmastar_demo_dev/scratch`。
- Inventory：8 个 Markdown，全部保留逐文件 SHA-256。
- Disposition：2 份 core/WAV 会话、2 份 Diag V4 resume/wrap 仅提炼可复用结论；4 份未填写 context preflight 和完整工作区转储不复制 raw 正文。
- Deletion：`absorbed / exact-path deletion verified 2026-07-18`；未写 `~/.codex/memories`。
- Evidence：`artifacts/manifests/xcrz-demo-dev-three-dir-absorption-20260718.jsonl`、`projects/xcrz-sigmastar-demo/validation/2026-07-18-dev-copy-three-dir-absorption-validation.md`。
