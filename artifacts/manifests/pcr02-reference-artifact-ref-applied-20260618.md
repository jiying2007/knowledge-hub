# PCR02 Reference and Artifact-Ref Applied - 2026-06-18

## Scope

- Source id: `pcr02-project-docs`
- Source root: `~/work/sigmastar/pcr02_ssc305/SourceCode/sdk/verify/xcrz_sigmastar_demo/docs`
- Baseline: `artifacts/manifests/pcr02-review-required-resolution-20260617.md`
- Machine-readable manifest: `artifacts/manifests/pcr02-reference-artifact-ref-applied-20260618.jsonl`
- Mode: reference registration only. No source files were copied, moved, deleted, renamed, edited, pruned, or promoted.

## Applied Items

| source path | target path | mode | status |
|---|---|---|---|
| `README.md` | `domains/projects/pcr02/current/docs-index.ref.md` | `reference-first-register` | `registered-pending-owner-confirmation` |
| `runbooks/examples/prog-tool-ci-smoke.session` | `domains/projects/pcr02/validation/prog-tool-ci-smoke.session.ref.md` | `artifact-ref-register` | `registered-pending-owner-confirmation` |

## Boundary Decisions

- `README.md` remains the source project docs index authority; Knowledge Hub only records a reference entry.
- `prog-tool-ci-smoke.session` remains an external artifact; Knowledge Hub records `uri`, `size`, and `sha256` and does not import the script body.
- Both entries remain `reviewing` until the owner confirms URI stability and review ownership.
- No remaining review-required item was unblocked by this batch.

## Verification

- `rtk sha256sum` and `rtk wc -c` matched the previous review-required resolution manifest for both sources.
- `tools/knowledge-check.sh --dry-run --json` is the required repository-level validation after applying this batch.
