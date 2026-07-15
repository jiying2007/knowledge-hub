# PCR02 IMSSV05C13 Memory Candidates

- Captured at: 2026-06-01
- Source scope: current session wrap, `~/Iford_IMSSV05C13` commits, PCR02 validation archive
- Mode: report-only
- Sanitization: credential material omitted, no full chat transcript, no bulk logs
- Do not auto-promote: these candidates require human confirmation before writing to `~/.codex/memories` or project `AGENTS.md`.

## Source Counts

| Source | Count / Status |
| --- | --- |
| Target SDK ordered commits | 13 commits from import through SNI fix |
| Nested app/library repo commits | 1 local commit |
| Host validation records | compile pass, OTA pass, gzip pass, SNI direct tool pass |
| Remaining acceptance blockers | real PCR02 EVT2 boot, real PCR02 EVT2 OTA |

## High Signal Findings

- PCR02 migration onto IMSSV05C13 is no longer only a plan; it has a committed ordered patch stack in the target SDK.
- `current.configs.in` from the old product was explicitly excluded by user instruction and should stay excluded unless the user reverses that decision.
- IMSSV05C13 `image.mk` expects `snigenerator -q`; the imported tool lacked that option and was fixed in `35645c874`.
- Host validation is strong enough for compile/package confidence, but not enough for product acceptance because real board boot and OTA are mandatory.
- The dirty worktree is dominated by build-generated artifacts; do not clean or revert without explicit approval.

## Candidate Table

| Scope | Candidate | Evidence | Risk | Confidence | Write route |
| --- | --- | --- | --- | --- | --- |
| Project fact | PCR02 first-round acceptance on IMSSV05C13 requires real PCR02 EVT2 boot and real OTA upgrade test; host compile/OTA alone is insufficient. | User instruction; session wrap remaining blockers. | Low | High | Project `AGENTS.md` or PCR02 archive decision note after user confirmation. |
| Project fact | For PCR02 migration input, ignore `pcr02_ssc305_compile/SourceCode/project/configs/current.configs.in` because the user declared it not an effective change. | User instruction; session wrap constraints. | Low | High | Project `AGENTS.md` after confirmation. |
| Project fact | Target SDK migration repository is `~/Iford_IMSSV05C13`; current product source is `~/pcr02_ssc305_compile`; older maintained baseline comparison is `~/Iford_IMD00V5.1.1_20250529`. | Session wrap repository table. | Medium, path may be local-machine specific | High | Archive-only or machine-local memory after confirmation. |
| Migration lesson | In IMSSV05C13 PCR02 image packaging, verify `snigenerator -q` support because a missing option can print an error while the higher-level build still exits successfully. | Commit `35645c874`; direct SNI tool validation. | Low | High | Archive plus project migration checklist. |
| Build hygiene | PCR02 IMSSV05C13 compile/OTA dirties many generated tracked and untracked SDK build artifacts; do not assume `git status` dirt means source changes. | `git status --short` after compile/OTA. | Medium | High | Archive-only, or project cleanup SOP after confirmation. |
| Product behavior | PCR02 rootfs still includes `/usr/sbin/adbd`, and this was observed to be inherited from the old product rather than newly introduced by IMSSV05C13. | Session review comparison. | Medium, policy-sensitive | Medium | Archive-only unless product policy confirms ADB handling. |
| OTA safety | First migration OTA with `ubia` rewrites the whole UBI container; run from SD/external storage and set `OTA_UMOUNT_OTA=1` on target. | Prior OTA migration validation note and session wrap warning. | Medium | High | PCR02 validation checklist or project `AGENTS.md` after confirmation. |

## Archive-Only Items

- Full commit list and exact host validation hashes should remain in the session wrap and validation archive, not long-term memory.
- The current dirty file list is useful as local state but too volatile for memory.
- Exact generated OTA artifact hashes are evidence for this run only; keep them in validation archives.

## Drop / Review Items

- Do not store full serial logs, private NAS paths, credentials, or complete build logs in long-term memory.
- Do not promote the local absolute paths as global rules unless this machine remains the canonical PCR02 migration workspace.
- Do not promote "rootfs ADB is acceptable" as a rule; only store that it was inherited and needs explicit policy if changed.

## Human Confirmation Needed

Suggested memory/project-rule promotions, if the user approves:

1. PCR02 IMSSV05C13 first-round acceptance requires real EVT2 board boot plus real OTA, not only host packaging.
2. Exclude old product `SourceCode/project/configs/current.configs.in` from PCR02 effective migration input.
3. For PCR02 IMSSV05C13 packaging, always verify SNI generation because `snigenerator -q` mismatch was found and fixed in commit `35645c874`.

## Gate Result

- Memory curator mode: report-only
- Candidate quality: pass
- Direct memory write: not performed
