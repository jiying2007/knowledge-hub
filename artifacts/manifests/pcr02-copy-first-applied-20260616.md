# PCR02 Copy-First Migration Applied - 2026-06-16

## Scope

- Source manifest: `artifacts/manifests/pcr02-copy-first-dry-run-20260616.jsonl`
- Apply command: `rtk bash tools/knowledge-copy-first.sh --manifest artifacts/manifests/pcr02-copy-first-dry-run-20260616.jsonl --apply --json`
- Result: `applied`
- Planned entries: 23
- Copied entries: 23

## Boundaries

- Source project docs were not modified.
- No project docs were deleted, moved, renamed, or pruned.
- All target files were copied under `domains/projects/pcr02/**`.
- No content was copied to `domains/embedded/standards/`.
- No memory file was written.

## Verification

- Target count: 23
- Target hash check: pass
- `tools/knowledge-check.sh --dry-run --json`: pass
- Registry entries were added as `reviewing` or `archived`; no migrated item was marked `active`.

## Rollback

Rollback policy remains `remove-copied-target-only`: remove the 23 copied Knowledge Hub target files and the registry/migration records created by this run. Do not modify source project docs.
