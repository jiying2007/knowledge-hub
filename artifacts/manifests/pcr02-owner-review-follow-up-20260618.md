# PCR02 Owner Review Follow-Up - 2026-06-18

## Scope

- Source id: `pcr02-project-docs`
- Source root: `/home/leiwenjun/work/sigmastar/pcr02_ssc305/SourceCode/sdk/verify/xcrz_sigmastar_demo/docs`
- Baseline package: `artifacts/manifests/pcr02-owner-review-package-20260618.md`
- Machine-readable follow-up: `artifacts/manifests/pcr02-owner-review-follow-up-20260618.jsonl`
- Mode: owner-review follow-up only. No source files were copied, moved, deleted, edited, pruned, promoted, or rewritten.

This package narrows the remaining owner-review decisions. It does not unblock migration by itself.

## Follow-Up Summary

| route | owner-review rows | result |
|---|---:|---|
| ASAN split boundary | 1 | `runbooks/asan-debug-guide.md` can become a PCR02-local runbook after owner approval; any team-level ASAN runbook is candidate-only and requires a separate rewrite and review. |
| memory automation governance | 1 | `runbooks/memory-auto-curation-guide.md` remains personal/local unless owner approves a disabled/report-only governance path with a hard no-memory-write gate. |
| DVR and motor closeout | 3 | DVR plan, motor MCU debug record and DVR session archive need status/fact-boundary decisions before any validation, decision or archive extract. |
| existing blockers retained | 2 | `AGENTS.md` and `standards/diag-command-metadata-standard.md` remain unchanged from the owner-review package and still require owner/scope/gate evidence. |

## Row-Level Decisions

### `pcr02-owner-review-001` - `AGENTS.md`

No new evidence was added in this follow-up. The row remains blocked pending owner, status, scope and review-cycle confirmation.

Allowed outcomes remain:

- PCR02 project-local rule after owner approval.
- Reference-only item.
- No migration.

### `pcr02-owner-review-002` - `standards/diag-command-metadata-standard.md`

No new evidence was added in this follow-up. The row remains blocked pending project-only scope, source-of-truth, applicable version and gate command evidence.

Allowed outcomes remain:

- PCR02 project decision/current standard after owner approval and gate evidence.
- No global team standard unless a separate split review rewrites the content without PCR02-only commands, paths or lifecycle assumptions.

### `pcr02-owner-review-003` - `runbooks/asan-debug-guide.md`

Recommended status: `split-required`.

Project-local content that should stay under PCR02 scope:

- `DEBUG=256` / `DEBUG=1` mapping to `build/build.mk` and `build/compile.mk`.
- PCR02 build commands such as `make -j8 DEBUG=256`, `make install`, and module-specific object builds.
- `TARGET_REL_FOLDER := debug` and project build-output assumptions.
- `/customer/bin/prog_pcr02`, `release/bin/prog_pcr02`, `/customer/lib`, `libs/3rdparty/libasan`, and `libasan.so.6` deployment details.
- Firmware capacity, strip behavior and dynamic linker assumptions tied to this project.

Team-level candidate boundary, if owner wants a separate reusable runbook:

- General ASAN compile flag expectations.
- Using `readelf` to check `libasan` dependency with path placeholders.
- First-error-first triage, BuildID matching, stack extraction, minimal call chain and minimal fix/repro loop.
- Embedded-friendly `ASAN_OPTIONS` tradeoffs such as stop-on-first-error, no leak focus, log-to-file and symbolization.
- Warnings about mixed release/debug packages and serial log truncation.

Must not:

- Do not promote to `domains/embedded/standards`.
- Do not copy the whole PCR02 source runbook to a team-level path.
- Do not treat PCR02 build commands, binary names, deploy paths or `libasan` layout as cross-project defaults.

### `pcr02-owner-review-004` - `runbooks/memory-auto-curation-guide.md`

Recommended status: keep `blocked-personal-local` until owner chooses one outcome.

Allowed owner decisions:

- `personal-local`: no team active index, no automation enablement, no formal memory write.
- `teamized-report-only`: only after owner approves a report-only governance manifest.
- `rejected` or `no-migration`.

Report-only governance requirements for any teamized path:

- `mode=report-only`
- `enabled=false`
- `writes_memory=false`
- `writes_team_active_index=false`
- allowed writes limited to owner-approved report artifacts
- denied writes include `~/.codex/memories/**`, `domains/embedded/**`, team active indexes and source project docs
- manual approval before enabling, promoting candidates, writing memory, adding team indexes or modifying source docs
- hard `no-memory-write` / `no_memory_write_gate`; failure must block, not warn
- secret scan and rollback procedure before any later enablement

Must not:

- Do not write `~/.codex/memories`.
- Do not add personal/local workflow material to a team active index.
- Do not enable automatic send, commit, publish, delete, promote or memory-write actions.

### `pcr02-owner-review-005` - `plans/2026-06-15-dvr-record-proto-sensor-decoupling-plan.md`

Recommended status resolution: `completed` or `superseded` should be considered first, because the later DVR session archive records implementation and validation evidence. Keep `active` only if the project owner confirms this plan is still the current execution baseline.

Fact boundary:

- Verified facts: the plan exists, declares scope/out-of-scope, records target semantics, and lists validation commands.
- Inference: the 2026-06-16 session archive suggests the plan may have been implemented and should therefore be completed or superseded.
- Open items: `task/iot` integration, replay data channel, `LIST_FETCH` pagination/limit, and build artifact submission boundaries.

Owner evidence required:

- Project owner sign-off.
- Final branch, commit or tag references.
- Proto-generation, build, refcount and grep evidence.
- `task/iot` dependency status.
- Decision on whether `RecordSetEvent` semantics become a project contract.

### `pcr02-owner-review-006` - `reports/2026-05-29-motor-mcu-debug-record.md`

Recommended status resolution: `archive-only` or `validation/report-candidate`. If migrated into validation, unresolved status must remain explicit.

Fact boundary:

- Verified facts: record date, test firmware label, listed issue groups and listed open items.
- Field feedback: low-speed stop, same-current torque mismatch, version-read serial no-output, insufficient calibration success criteria.
- Inference: likely false protection, likely calibration issue, and SoC-level comprehensive decision direction.
- Recommendations: exception-report fields, stop-decision strategy, validation plan and follow-up actions.
- Open items: `1.3A for 3s` versus `10s` parameter conflict, phase-loss filtering, Hall replacement conditions, abnormal motor retest, version-read root cause, calibration reasonableness and SoC strategy implementation.

Owner evidence required:

- Motor MCU or SoC owner review.
- Firmware version and parameter table.
- Serial waveform, protocol logs or hardware-start evidence.
- Field retest records and calibration before/after data.
- Fault-code/protocol field definitions.
- Whole-device validation records.

Must not:

- Do not promote inference or suggested strategy as verified validation.
- Do not treat stage firmware behavior as production policy.
- Do not delete or hide open issues.

### `pcr02-owner-review-007` - `reports/2026-06-16-dvr-record-replay-session-archive.md`

Recommended status resolution: `archive-only`.

Required archive metadata:

- `status=archive-only`
- `source_status_at_capture=active handoff`
- `contains_memory_candidates=true`
- `not_active_source=true`
- `excluded_sections=["Memory Candidates","handoff/worktree cleanup notes"]`
- `extracts_require_owner_review=true`
- owner, reviewer, date, source hash, review date and evidence refs

Allowed extracts after owner review:

- Validation extract: only command results, branch/commit refs and reproducible evidence.
- Decision extract: only confirmed DVR lifecycle and interface semantics.

Must not:

- Do not treat session handoff, dirty worktree notes or memory candidates as active facts.
- Do not write memory candidates to `~/.codex/memories`.
- Do not clean, revert or rewrite source worktrees mentioned by the archive.

## Shared Owner Evidence Checklist

Every follow-up row needs:

- `owner_decision`
- `reviewed_by`
- `reviewed_at`
- `review_after`
- `source_sha256`
- `source_size`
- `source_status`
- `target_decision`
- `evidence_refs`
- `open_items`
- `status_reason`

## Verification Plan

Knowledge Hub checks after any follow-up migration:

```bash
rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run
rtk bash ~/knowledge-hub/tools/knowledge-search.sh "ASAN"
rtk bash ~/knowledge-hub/tools/knowledge-search.sh "memory-auto-curation"
rtk bash ~/knowledge-hub/tools/knowledge-search.sh "PCR02 DVR RecordSetEvent task iot sensor"
rtk bash ~/knowledge-hub/tools/knowledge-search.sh "PCR02 motor MCU 0.2.0-20260527"
rtk bash ~/knowledge-hub/tools/knowledge-search.sh "PCR02 DVR session archive memory candidates"
```

Source-project evidence checks for owners to attach as references:

```bash
rtk rg -n "DEBUG_ASAN|fsanitize=address|TARGET_REL_FOLDER|fno-omit-frame-pointer|fsanitize-recover|funwind-tables" /home/leiwenjun/work/sigmastar/pcr02_ssc305/SourceCode/sdk/verify/xcrz_sigmastar_demo/build
rtk rg -n "DVR_RECORD|DVR_REPLAY|DvrRecordPayload|DvrReplayPayload" /home/leiwenjun/work/sigmastar/pcr02_ssc305/SourceCode/sdk/verify/xcrz_sigmastar_demo
rtk rg -n "VSAPIDVR_RecordSetEvent|astRecordTiming|_DVR_RecordCheckNextTiming" /home/leiwenjun/work/sigmastar/pcr02_ssc305/SourceCode/sdk/verify/xcrz_sigmastar_demo
rtk rg -n "0.2.0-20260527|1.3A|10s|缺相|堵转|Hall|校准" /home/leiwenjun/work/sigmastar/pcr02_ssc305/SourceCode/sdk/verify/xcrz_sigmastar_demo/docs
```

## Non-Actions

- No source project file was edited.
- No remaining review-required content was copied into `domains/`.
- No PCR02 project-specific material was promoted to `domains/embedded/standards/`.
- No personal/local automation was enabled.
- No session handoff or memory candidate was written to `~/.codex/memories`.
- No review blocker is marked resolved by this package.
