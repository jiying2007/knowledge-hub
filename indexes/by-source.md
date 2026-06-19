# Knowledge Sources

| Source | Role | Path |
| --- | --- | --- |
| embedded-knowledge | team-knowledge-source | `/home/leiwenjun/embedded/knowledge` |
| engineering-archive | project-archive-source | `/home/leiwenjun/embedded/engineering_archive` |
| patent-disclosure | patent-source | `/home/leiwenjun/embedded/patent_disclosure` |
| codex-archive | codex-governance-source | `/home/leiwenjun/codex/docs/archive` |
| codex-memories | auxiliary-memory-source | `/home/leiwenjun/.codex/memories` |
| pcr02-project-docs | project-current-docs-source | `/home/leiwenjun/work/sigmastar/pcr02_ssc305/SourceCode/sdk/verify/xcrz_sigmastar_demo/docs` |

## Source-Specific Review Artifacts

- `pcr02-project-docs/runbooks/asan-debug-guide.md`: ASAN split targets are tracked by `artifacts/manifests/pcr02-asan-split-targets-20260618.md`.
- `pcr02-project-docs/runbooks/memory-auto-curation-guide.md`: report-only governance is tracked by `artifacts/manifests/memory-auto-curation-report-only-governance-20260618.md`.
- `pcr02-project-docs/plans/2026-06-15-dvr-record-proto-sensor-decoupling-plan.md`: owner-gated DVR plan closeout is tracked by `artifacts/manifests/pcr02-dvr-motor-closeout-targets-20260618.md`.
- `pcr02-project-docs/reports/2026-05-29-motor-mcu-debug-record.md`: motor MCU fact split and archive-only boundary are tracked by `artifacts/manifests/pcr02-dvr-motor-closeout-targets-20260618.md`.
- `pcr02-project-docs/reports/2026-06-16-dvr-record-replay-session-archive.md`: DVR session archive-only metadata and memory-candidate exclusion are tracked by `artifacts/manifests/pcr02-dvr-motor-closeout-targets-20260618.md`.
- `pcr02-project-docs/AGENTS.md`: PCR02 project-local docs rule owner gate is tracked by `artifacts/manifests/pcr02-remaining-owner-gates-20260618.md`.
- `pcr02-project-docs/standards/diag-command-metadata-standard.md`: PCR02 diag metadata owner/gate evidence boundary is tracked by `artifacts/manifests/pcr02-remaining-owner-gates-20260618.md`.
- `pcr02-project-docs`: 32/32 docs governance coverage and registry/index closeout are tracked by `artifacts/manifests/pcr02-docs-governance-closeout-20260618.md`.
- `pcr02-project-docs owner gates`: executable owner decision board is tracked by `artifacts/manifests/pcr02-owner-action-board-20260618.md`.
- `pcr02-project-docs owner intake`: Chinese owner sign-off fields and hard-gate questions are tracked by `artifacts/manifests/pcr02-owner-intake-package-20260618.md`.
- `pcr02-project-docs owner-gated source identity`: current source SHA256/size preflight is tracked by `artifacts/manifests/pcr02-owner-source-identity-preflight-20260618.md`.
- `pcr02-project-docs owner resolution`: owner decision landing rules are tracked by `artifacts/manifests/pcr02-owner-resolution-playbook-20260618.md`.
- `pcr02-project-docs owner resolution schema`: owner decision fields, value sets and invalid combinations are tracked by `artifacts/manifests/pcr02-owner-resolution-schema-20260618.md`.
- `pcr02-project-docs governance closeout`: recoverable handoff is tracked by `artifacts/manifests/pcr02-governance-handoff-20260618.md`.
- `registry/items.jsonl`、`registry/migrations.jsonl`、`indexes/by-*.md`: PCR02 control-plane closeout audit is tracked by `artifacts/manifests/pcr02-docs-governance-closeout-20260618.md`.
- `codex-memories`: remains auxiliary recall only; memory auto-curation governance must not write `~/.codex/memories/**`.
- `engineering-archive`: 38 PCR02 historical engineering archive files were copy-first migrated to `domains/projects/pcr02/archive/engineering-archive` and verified by `artifacts/manifests/engineering-archive-copy-first-applied-20260619.md`.
