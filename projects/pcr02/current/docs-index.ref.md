# PCR02 Project Docs Hub Index

## Reference

- Source id: `pcr02-project-docs`
- Hub source path: `sources/pcr02-project-docs`
- Hub source control: `sources/pcr02-project-docs/README.md`
- 旧正文剪枝账本：`artifacts/manifests/pcr02-retired-body-prune-20260625.jsonl`
- Origin provenance: `registry/sources.json` origin_path for `pcr02-project-docs`; `registry/source-tombstones.jsonl`
- Source path: `README.md`
- Source size: `3010`
- Source SHA256: `bb1b3ce7a1187d9c0c90ca53ae9a0aa9f0ca31ff5d1b2247369b0284a0243a60`
- Source owner: `team-core`
- Source status: `retired-origin-provenance`
- Knowledge Hub status: `reviewing`
- Review after: `2026-09-17`

## Boundary

This file is a Hub index entry. It no longer treats the PCR02 project docs README in the source project as the active authority. The old migrated body copy has been pruned; the source control directory, body prune ledger and canonical `projects/pcr02/` targets are the Knowledge Hub entry points. Retired origin details are retained only in source registry provenance and tombstones for hash comparison.

Use this entry to find the Hub-controlled PCR02 project docs source and to connect migrated Knowledge Hub records back to their original project-local docs index when provenance is needed.

## Current Handling

- Keep source control, provenance ledger and project current/archive targets as the Knowledge Hub authority.
- Keep migrated PCR02 content under `projects/pcr02/`.
- Do not create new Knowledge Hub references that read from the retired source project docs path by default.
- Do not promote project-specific docs index rules into `domains/embedded/`.
- Do not treat historical plans or reports listed by the source README as current execution tasks without fresh verification.

## Review Boundary

- `team-core` is retained as the Hub maintenance owner for this project docs index reference.
- Do not reopen the retired source project README as an active authority. Future link expansion must start from Hub source control, tombstone/hash provenance and canonical `projects/pcr02/` targets.
