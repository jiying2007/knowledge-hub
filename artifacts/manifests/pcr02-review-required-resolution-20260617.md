# PCR02 Review-Required Resolution Plan - 2026-06-17

## Scope

- Source id: `pcr02-project-docs`
- Source root: `~/work/sigmastar/pcr02_ssc305/SourceCode/sdk/verify/xcrz_sigmastar_demo/docs`
- Classification baseline: `artifacts/manifests/pcr02-project-docs-classification-20260616.md`
- Machine-readable blocked manifest: `artifacts/manifests/pcr02-review-required-resolution-20260617.jsonl`
- Mode: review plan only. No source files were copied, moved, deleted, renamed, edited, or promoted.

## Parallel Review Summary

Subagents were used with `scope_write=NONE`; the main thread performed all file writes.

| slice | files | result | migration decision |
|---|---:|---|---|
| reference/rules/standards | 3 | reviewed | `README.md` may enter a later reference-first batch; `AGENTS.md` and diag metadata standard remain blocked until owner review and metadata completion. |
| runbook/personal/artifact | 3 | reviewed | ASAN requires split review, memory curation remains personal/local, `.session` must be artifact-ref only. |
| active/debug/session | 3 | reviewed | DVR plan, motor debug record and DVR session archive remain blocked pending owner status and metadata review. |

## Disposition

| source path | disposition | next action | owner/review requirement |
|---|---|---|---|
| `README.md` | `reference-first-candidate` | Create reference-only entry in a later batch; do not copy as active content authority. | Confirm `team-core` remains owner and source authority. |
| `AGENTS.md` | `metadata-required` | Add metadata plan only; no migration until owner confirms current validity. | Confirm PCR02 docs owner, status and review cycle. |
| `standards/diag-command-metadata-standard.md` | `metadata-required/project-standard-risk` | Keep project-local; no global promotion. | PCR02 diag owner or `team-core` must confirm source of truth, version and gate commands. |
| `runbooks/asan-debug-guide.md` | `split-required` | Split PCR02-specific build/run details from reusable ASAN guidance before any migration. | Owner decides whether team-level ASAN content should be created separately. |
| `runbooks/memory-auto-curation-guide.md` | `personal-local` | Keep out of team active index; do not write memory. | Teamization requires report-only automation manifest and explicit no-memory-write gate. |
| `runbooks/examples/prog-tool-ci-smoke.session` | `artifact-ref-candidate` | Register as artifact reference with `uri`, `size`, and `sha256`; do not import script as prose. | PCR02 registry owner confirms URI format and usage scope. |
| `plans/2026-06-15-dvr-record-proto-sensor-decoupling-plan.md` | `state-conflict` | Decide whether it is still current contract/design baseline or completed/superseded plan. | Project owner must resolve active-vs-completed status. |
| `reports/2026-05-29-motor-mcu-debug-record.md` | `validation-candidate-metadata-required` | Separate verified facts, field feedback, inference, recommendation and open items. | Motor MCU/SoC owner confirms evidence and firmware/test context. |
| `reports/2026-06-16-dvr-record-replay-session-archive.md` | `archive-only-session-handoff` | Archive-only after metadata; memory candidates and handoff text must not enter active index. | Owner confirms what engineering evidence is reusable. |

## Policy Decisions

- Do not migrate any of the 9 files as ordinary `copy-first` text in the next batch.
- `README.md` is a source authority/reference candidate, not a replacement active docs authority.
- `.session` content must go through `artifact-ref` with size and SHA256.
- Memory-related material remains personal/local until a separate governance manifest exists.
- Session archive and memory candidates are not team active facts and must not write `~/.codex/memories`.

## Next Batch Candidates

Allowed after review:

- `README.md` as reference-first.
- `runbooks/examples/prog-tool-ci-smoke.session` as artifact-ref.

Blocked until owner review:

- `AGENTS.md`
- `standards/diag-command-metadata-standard.md`
- `runbooks/asan-debug-guide.md`
- `runbooks/memory-auto-curation-guide.md`
- `plans/2026-06-15-dvr-record-proto-sensor-decoupling-plan.md`
- `reports/2026-05-29-motor-mcu-debug-record.md`
- `reports/2026-06-16-dvr-record-replay-session-archive.md`

## Non-Actions

- No source project docs were copied, moved, deleted, renamed, edited, or pruned.
- No project-specific material was promoted to `domains/embedded/standards/`.
- No personal/local automation content was added to team active indexes.
- No session script content was imported as text knowledge.
- No memory file was written.
