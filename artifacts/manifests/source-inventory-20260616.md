# Source Inventory Baseline - 2026-06-16

## Scope

- Root: `~/knowledge-hub`
- Command: `rtk bash tools/knowledge-inventory.sh --markdown --max-files 20000`
- Mode: read-only inventory.
- Result: all 6 registered sources exist and no source scan was truncated.

## Summary

| source | files | dirs | size | text-like | binary-like | git state | migration stance |
|---|---:|---:|---:|---:|---:|---|---|
| `embedded-knowledge` | 174 | 54 | 390.2 KiB | 106 | 0 | git `main`, dirty=7 | Keep as legacy team SSOT until owner review. Do not write through Knowledge Hub. |
| `engineering-archive` | 35 | 12 | 201.0 KiB | 35 | 0 | no git | First copy-first migration candidate. |
| `patent-disclosure` | 192 | 14 | 22.9 MiB | 10 | 28 | git `HEAD`, dirty=28 | Keep isolated under patent workflow; do not mix with engineering knowledge. |
| `codex-archive` | 165 | 12 | 1015.6 KiB | 165 | 0 | no git | Reference via Codex archive tools; do not duplicate wholesale. |
| `codex-memories` | 10 | 5 | 23.7 KiB | 10 | 0 | git, dirty=0 | Auxiliary recall only; promotion requires review. |
| `pcr02-project-docs` | 32 | 7 | 214.0 KiB | 31 | 0 | no git | Current project docs; externalize before any project-doc pruning. |

## Risk Notes

- `embedded-knowledge` has uncommitted source changes. Treat it as live source material, not migration input, until the owner decides whether to stabilize or snapshot it.
- `patent-disclosure` has uncommitted source changes and many binary documents/images. It must stay under `domains/patents/` boundaries and should not be blended into team engineering standards.
- `pcr02-project-docs` contains current project operating material. Migration should preserve project specificity under `domains/projects/pcr02/` and must not promote it to `domains/embedded/standards/` without review.
- `codex-memories` is not an authority source. It can seed candidates but cannot become an active fact without registry evidence.

## Priority Plan

1. `pcr02-project-docs`: generate a file-level classification table and map each file to `current`, `archive`, `decisions`, `validation`, or `personal`.
2. `engineering-archive`: create copy-first candidates under `domains/projects/pcr02/archive/` after file-level review.
3. `embedded-knowledge`: keep as external source and only register cross-project standards after owner review.
4. `codex-archive`: add indexes or references only; avoid duplicate historical notes.
5. `patent-disclosure`: create patent-only registry records for Markdown disclosure files first; binaries remain artifact references with hash and size.
6. `codex-memories`: inspect only through `adk-memory-curator`; no direct memory write or automatic promotion.

## Non-Actions

- No source files were copied, moved, deleted, renamed, or edited.
- No project repository `docs` directory was pruned.
- No memory file was written.
- No binary artifact was imported into Knowledge Hub.
