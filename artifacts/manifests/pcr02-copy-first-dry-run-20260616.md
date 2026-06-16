# PCR02 Copy-First Migration Dry-Run - 2026-06-16

## Scope

- Source id: `pcr02-project-docs`
- Source root: `/home/leiwenjun/work/sigmastar/pcr02_ssc305/SourceCode/sdk/verify/xcrz_sigmastar_demo/docs`
- Classification baseline: `artifacts/manifests/pcr02-project-docs-classification-20260616.md`
- Machine-readable manifest: `artifacts/manifests/pcr02-copy-first-dry-run-20260616.jsonl`
- Mode: dry-run only. No source or target files were copied, moved, deleted, renamed, edited, or promoted.

## Parallel Review Summary

Subagents were used with `scope_write=NONE`; the main thread performed all file writes.

| slice | result | accepted | excluded | notes |
|---|---:|---:|---:|---|
| active current/decisions | pass | 13 | 0 | Keep all targets under `domains/projects/pcr02`; do not promote project-specific standards globally. |
| archive/validation | pass-with-cautions | 10 | 0 | `reports/2026-05-17-session-archive-report.md` is archive-only/session-summary. |
| review-required/reference/artifact/personal | pass | 0 | 9 | Excluded from first copy-first batch. |

## First Safe Batch

- Total accepted dry-run entries: 23.
- Current/decision entries: 13.
- Archive/validation entries: 10.
- Excluded entries: 9.
- Target overwrite risk: none; all accepted target paths were treated as dry-run candidates and must be checked again before any real copy.

## Required Fields Per Entry

Each JSONL entry includes:

- `id`
- `source_id`
- `source_root`
- `source_path`
- `target_path`
- `bucket`
- `mode`
- `source_sha256`
- `size`
- `owner`
- `review_status`
- `risk`
- `rollback_policy`
- `source_status`

## Excluded From First Batch

| source path | reason |
|---|---|
| `README.md` | `reference-first`; avoid creating a second active docs authority. |
| `AGENTS.md` | Missing frontmatter; project docs rules need owner review. |
| `standards/diag-command-metadata-standard.md` | Missing frontmatter and project-specific standard risk. |
| `runbooks/asan-debug-guide.md` | Potential overlap with team ASAN/GDB/core dump knowledge. |
| `runbooks/memory-auto-curation-guide.md` | Personal/local memory automation; do not enter team active index. |
| `runbooks/examples/prog-tool-ci-smoke.session` | Session script; register as artifact reference, not text knowledge. |
| `plans/2026-06-15-dvr-record-proto-sensor-decoupling-plan.md` | Active plan under `plans/`; confirm current execution state first. |
| `reports/2026-05-29-motor-mcu-debug-record.md` | Debug record lacks metadata and includes open questions. |
| `reports/2026-06-16-dvr-record-replay-session-archive.md` | Session archive with memory candidates; not active knowledge. |

## Gates Before Real Copy

1. Re-run source hash generation and compare against this manifest.
2. Confirm every target path still does not exist, or explicitly review overwrite behavior.
3. Copy only into `domains/projects/pcr02/**`.
4. Do not update team active indexes for archive-only/session-summary entries.
5. Do not write `~/.codex/memories`.
6. After copy, register migrated items with owner, review date, source hash and rollback record.

## Rollback

The only allowed rollback for first copy execution is `remove-copied-target-only`: remove newly copied Knowledge Hub target files and registry entries created by that run. Source docs must not be modified by rollback.
