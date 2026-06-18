# PCR02 Owner Decision Worksheets - 2026-06-18

## Scope

- Source id: `pcr02-project-docs`
- Source root: `/home/leiwenjun/work/sigmastar/pcr02_ssc305/SourceCode/sdk/verify/xcrz_sigmastar_demo/docs`
- Baseline package: `artifacts/manifests/pcr02-owner-review-package-20260618.md`
- Follow-up package: `artifacts/manifests/pcr02-owner-review-follow-up-20260618.md`
- Machine-readable worksheets: `artifacts/manifests/pcr02-owner-decision-worksheets-20260618.jsonl`
- Mode: owner decision worksheet only. No source files were copied, moved, deleted, edited, pruned, promoted, or rewritten.

These worksheets give owners fillable decision fields. They do not unblock migration by themselves.

## Required Owner Fields

Every worksheet row must be completed before any migration or extract:

- `owner_decision`
- `target_decision`
- `reviewed_by`
- `reviewed_at`
- `review_after`
- `source_status`
- `source_sha256`
- `source_size`
- `evidence_refs`
- `status_reason`

## `pcr02-owner-review-001` - `AGENTS.md`

Decision options:

- `project-local-rule`: accept only as a PCR02 project-local docs governance rule.
- `reference-only`: keep as source reference or audit context, not active rule.
- `no-migration`: owner confirms stale, superseded or not suitable.

Required evidence:

- PCR02 docs owner or `team-core` sign-off.
- Source identity: SHA256 `95ed7fa20ee52972d79038fb7ec9c5e9b8594fb35b29df50eefdcbf102130566`, size `2414`.
- Current validity statement.
- Project-only scope statement.
- Applicable branch, SDK version or project phase.
- Review cycle with `reviewed_by`, `reviewed_at`, `review_after`.
- Target decision reason.

Pass gates:

- Owner, status, scope, review date and applicable version are explicit.
- Target remains under PCR02 project boundary.
- Any migrated target does not overwrite Knowledge Hub root `AGENTS.md`.
- `knowledge-check` and targeted search pass after a later migration.

Fail gates:

- Current validity is not confirmed.
- Scope may be interpreted as global Codex rules or team standard.
- Source hash, size or review cycle is missing.
- Target attempts to write `domains/embedded/standards` or root `AGENTS.md`.

Must not:

- Do not overwrite Knowledge Hub root `AGENTS.md`.
- Do not promote to `domains/embedded/standards`.
- Do not treat project-local rules as global Codex rules.

Suggested verification:

```bash
rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run
rtk bash ~/knowledge-hub/tools/knowledge-search.sh "PCR02 AGENTS"
rtk bash ~/knowledge-hub/tools/knowledge-search.sh "project docs agent rules"
```

## `pcr02-owner-review-002` - `standards/diag-command-metadata-standard.md`

Decision options:

- `pcr02-project-decision-after-owner-gate`: accept as PCR02 project decision after owner and gate evidence.
- `pcr02-project-current-after-owner-gate`: accept as PCR02 current project standard after gate evidence or documented owner exception.
- `reference-only`: keep as reference when evidence is insufficient.
- `no-migration`: owner confirms stale, mismatched or replaced.

Required evidence:

- PCR02 diag owner or `team-core` sign-off.
- Source identity: SHA256 `89e897bee7e3f8372a0d4c4655748fbe3476780129b157718387c1cbbb80e95d`, size `5316`.
- Project-only source-of-truth statement.
- Applicable branch, firmware or SDK version.
- Provider lifecycle, command metadata and catalog/help runtime match evidence.
- Diag metadata, command quality, naming, interface coverage and layer-dependency gate evidence, or a documented owner exception.

Pass gates:

- Diag owner sign-off exists.
- Project-only source-of-truth is explicit.
- Applicable version is explicit.
- Implementation still matches the documented command metadata.
- Target stays under PCR02 project decision/current path.

Fail gates:

- Gate evidence is missing and no owner exception exists.
- Provider lifecycle or metadata behavior is unverified.
- PCR02 command names, paths or lifecycle assumptions are generalized.
- Whole file is promoted as team standard.

Must not:

- Do not promote whole file to team standard.
- Do not place under `domains/embedded/standards`.
- Do not treat PCR02 paths and command names as cross-project defaults.
- Do not claim active standard without gate evidence.

Suggested verification:

```bash
rtk python3 tools/diag/checks/check_diag_metadata.py
rtk python3 tools/diag/checks/check_diag_command_quality.py
rtk python3 tools/diag/checks/check_diag_naming.py
rtk python3 tools/diag/checks/check_diag_interface_coverage.py
rtk python3 tools/diag/checks/check_diag_layer_deps.py
rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run
rtk bash ~/knowledge-hub/tools/knowledge-search.sh "PCR02 diag command metadata"
```

## `pcr02-owner-review-003` - `runbooks/asan-debug-guide.md`

Decision options:

- `split-approved`: owner accepts split boundary; PCR02-specific content stays project-local and team-level content remains candidate-only.
- `active-project-local`: migrate only as PCR02 project-local runbook.
- `reference-only`: keep as source reference.
- `rejected`: no migration.
- `team-candidate-only`: create only a candidate for a separately rewritten team ASAN runbook.

Required evidence:

- Owner review record.
- Source identity: SHA256 `d65cf6796eac2c306b6bd0fa101450a1307d5c49ba7b7640e6a329d4263d8e88`, size `4736`.
- PCR02 source status and applicable branch/SDK version.
- Evidence that `DEBUG=256` / `DEBUG=1`, `prog_pcr02`, `/customer/bin`, `/customer/lib`, `release/bin` and `libs/3rdparty/libasan` are still applicable, if migrating project-local content.
- Team-level status: `candidate-only-after-separate-team-review` or `no-team-candidate`.

Pass gates:

- `split-approved` includes both `project_local_keep` and `team_level_candidate_only`.
- PCR02 build commands, binary names, deploy paths and `libasan` layout stay under `domains/projects/pcr02`.
- Team-level ASAN content is rewritten, generic and review-required.

Fail gates:

- Whole source runbook is copied to a team active path.
- PCR02 `DEBUG=256`, `prog_pcr02`, `/customer/*` or `libs/3rdparty/libasan` is made cross-project default.
- Owner, source status or applicable version is missing.

Must not:

- Do not promote to `domains/embedded/standards`.
- Do not copy the whole PCR02 runbook to team-level.
- Do not modify source project runbook for migration convenience.
- Do not declare active before owner confirmation.

Suggested verification:

```bash
rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run
rtk bash ~/knowledge-hub/tools/knowledge-search.sh "ASAN"
rtk bash ~/knowledge-hub/tools/knowledge-search.sh "PCR02 ASAN"
rtk bash ~/knowledge-hub/tools/knowledge-search.sh "libasan"
rtk rg -n "DEBUG_ASAN|fsanitize=address|TARGET_REL_FOLDER|fno-omit-frame-pointer|fsanitize-recover|funwind-tables" /home/leiwenjun/work/sigmastar/pcr02_ssc305/SourceCode/sdk/verify/xcrz_sigmastar_demo/build
```

## `pcr02-owner-review-004` - `runbooks/memory-auto-curation-guide.md`

Decision options:

- `personal-local`: keep as personal/local workflow only.
- `teamized-report-only`: owner approves disabled/report-only governance path.
- `rejected`: reject migration.
- `no-migration`: no migration; source remains evidence only.

Required evidence:

- Personal owner decision.
- Team owner approval if `teamized-report-only`.
- Source identity: SHA256 `36e8529bff008fb42c90779f11724e020141e19d64a6533d6af99f70dfeedc91`, size `2060`.
- Explicit `mode=report-only`, `enabled=false`, `writes_memory=false`, `writes_team_active_index=false`.
- Denied targets include `~/.codex/memories/**`, `domains/embedded/**`, team active index and source project docs.
- Manual approval before enabling, promoting candidate, writing memory, adding team index or modifying source docs.
- Secret scan and rollback procedure before any future enablement.

Pass gates:

- `teamized-report-only` has `mode=report-only` and `enabled=false`.
- `writes_memory=false` and `writes_team_active_index=false`.
- `no-memory-write` gate is hard block, not warning.
- Allowed writes are owner-approved report artifacts only.

Fail gates:

- Writes to `~/.codex/memories/**`.
- Personal/local workflow enters team active index.
- Automatic send, commit, publish, delete, promote or memory-write is enabled.
- Report-only is treated as enablement approval.

Must not:

- Do not write `~/.codex/memories`.
- Do not add personal/local workflow material to team active index.
- Do not enable automatic actions.
- Do not modify source project docs.

Suggested verification:

```bash
rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run
rtk bash ~/knowledge-hub/tools/knowledge-search.sh "memory-auto-curation"
rtk bash ~/knowledge-hub/tools/knowledge-search.sh "no-memory-write"
rtk bash ~/knowledge-hub/tools/knowledge-search.sh "teamized-report-only"
```

## `pcr02-owner-review-005` - `plans/2026-06-15-dvr-record-proto-sensor-decoupling-plan.md`

Decision options:

- `completed`
- `superseded`
- `active-if-owner-confirms-current-baseline`
- `archive-only`

Recommended default: `completed` or `superseded`.

Required evidence:

- Project owner sign-off.
- Source identity: SHA256 `9134247182e7578eec8c2bb4d702ffaed6c75359039d549b679f058bf8532cb3`, size `4786`.
- Final branch, commit or tag refs.
- Proto generation, build, API DVR refcount and targeted grep evidence.
- `task/iot` dependency status.
- Replay data channel status.
- `LIST_FETCH` pagination or limit decision.
- `RecordSetEvent` contract extract decision.

Pass gates:

- Owner confirms exactly one status.
- Planned validation commands are backed by actual result refs.
- Final branch, commit or tag refs are attached.
- `task/iot` ownership and remaining boundary are explicit.
- `RecordSetEvent` semantics are either approved as PCR02 project contract or left unextracted.
- Open items remain visible.

Fail gates:

- Owner remains `local-codex`.
- Status remains active without owner current-baseline confirmation.
- Planned commands are treated as passed evidence.
- `task/iot` integration gap is hidden.
- DVR project design is promoted to team embedded standard.

Must not:

- Do not use `local-codex` as long-term owner.
- Do not treat planned validation commands as passed evidence.
- Do not promote DVR project design to `domains/embedded/standards`.
- Do not import session archive handoff notes as active facts.

Suggested verification:

```bash
rtk bash -lc "modules/proto/build_proto.sh"
rtk bash -lc "./make.sh"
rtk bash -lc "python3 build/check_api_dvr_refcount.py"
rtk rg -n "astRecordTiming|_DVR_RecordCheckNextTiming" modules/api/src/api_dvr/api_dvr_record.c
rtk rg -n "VSAPIDVR_RecordStart|VSAPIDVR_RecordStop|VSAPIDVR_Replay" modules/sensor modules/proto
rtk rg -n "DVR_RECORD|DVR_REPLAY|DvrRecordPayload|DvrReplayPayload" /home/leiwenjun/work/sigmastar/pcr02_ssc305/SourceCode/sdk/verify/xcrz_sigmastar_demo
```

## `pcr02-owner-review-006` - `reports/2026-05-29-motor-mcu-debug-record.md`

Decision options:

- `archive-only`
- `validation-report-candidate`

Recommended default: `archive-only`.

Required evidence:

- Motor MCU or SoC owner review.
- Source identity: SHA256 `2ebdb26b56f3bd7a3561fd4f6a0aaf05389044e34530a10743d4032434fde734`, size `13646`.
- Firmware version refs and protection parameter table.
- Serial waveform, protocol logs or hardware-start evidence.
- Field retest records.
- Calibration before/after data.
- Fault-code or protocol field definitions.
- Whole-device validation records.
- Explicit acknowledgement of unresolved items.

Fact split that must remain visible:

- Verified facts: record date, test firmware label `0.2.0-20260527.hex`, listed issue groups, listed open items.
- Field feedback: low-speed stop, same-current torque mismatch, version-read serial no-output, insufficient calibration success criteria.
- Inference: false-protection tendency, calibration-issue tendency, SoC comprehensive-decision direction.
- Recommendations: exception report fields, stop-decision strategy, validation plan, follow-up actions.
- Open items: `1.3A for 3s` versus `10s` conflict, phase-loss filtering, Hall replacement conditions, abnormal motor retest, version-read root cause, calibration reasonableness, SoC strategy implementation.

Pass gates:

- Archive-only keeps unresolved items explicit.
- Facts, feedback, inference, recommendations and open items are separated.
- Firmware version and parameter refs exist before validation promotion.
- Calibration and torque claims have before/after data.
- SoC strategy remains recommendation unless implementation and validation evidence is attached.

Fail gates:

- Inference is promoted as verified fact.
- Stage firmware behavior is treated as production policy.
- Likely calibration issue is recorded as root cause without retest data.
- Parameter conflict is hidden.
- Open issues are deleted, closed or omitted.

Must not:

- Do not promote inference or suggested strategy as verified fact.
- Do not treat `0.2.0-20260527.hex` behavior as production policy.
- Do not delete or hide open issues.
- Do not promote motor MCU local strategy to team standard.

Suggested verification:

```bash
rtk rg -n "0.2.0-20260527|1.3A|10s|缺相|堵转|Hall|校准" /home/leiwenjun/work/sigmastar/pcr02_ssc305/SourceCode/sdk/verify/xcrz_sigmastar_demo/docs
```

## `pcr02-owner-review-007` - `reports/2026-06-16-dvr-record-replay-session-archive.md`

Decision options:

- `archive-only`

Recommended default: `archive-only`.

Required evidence:

- Owner archive metadata approval.
- Source identity: SHA256 `266a1c2706da87b39d9e4b204ccece61b0ec9c7a95183c64324e95f606c1dadc`, size `6697`.
- `source_status_at_capture=active handoff`
- `contains_memory_candidates=true`
- `not_active_source=true`
- `extracts_require_owner_review=true`
- Commit, branch and dirty-state evidence.
- Proto generation, build, refcount, grep and final-ready refs.
- `task/iot`, replay data channel and `LIST_FETCH` pagination risk status.
- Memory candidate exclusion confirmation.

Pass gates:

- Target status is archive-only.
- `Memory Candidates` are excluded from active extraction.
- Validation extract includes only command results, branch/commit refs and reproducible evidence.
- Decision extract includes only owner-confirmed DVR lifecycle and interface semantics.

Fail gates:

- Whole session archive is copied into current.
- Session handoff is treated as active fact.
- Memory candidates are written to `~/.codex/memories`.
- Dirty worktree notes are promoted into project facts.
- Decisions are extracted without owner review.
- Source worktrees are cleaned, reverted or rewritten because the archive mentioned them.

Must not:

- Do not treat session handoff as active facts.
- Do not write memory candidates to `~/.codex/memories`.
- Do not copy whole file to current.
- Do not clean, revert or rewrite source worktrees mentioned by the archive.

Suggested verification:

```bash
rtk bash -lc "modules/proto/build_proto.sh"
rtk bash -lc "./make.sh --jobs 8"
rtk bash -lc "python3 build/check_api_dvr_refcount.py"
rtk rg -n "astRecordTiming|_DVR_RecordCheckNextTiming|g_stEventParam|_DVR_RecordGetEvent" modules/api/src/api_dvr/api_dvr_record.c
rtk rg -n "VSAPIDVR_RecordStart|VSAPIDVR_RecordStop|VSAPIDVR_Replay" modules/sensor modules/proto
rtk bash ~/knowledge-hub/tools/knowledge-search.sh "PCR02 DVR session archive memory candidates"
rtk bash ~/knowledge-hub/tools/knowledge-search.sh "memory candidates archive-only not_active_source"
```

## Non-Actions

- No source project file was edited.
- No review-required content was copied into `domains/`.
- No blocked row was marked resolved.
- No PCR02 project-specific material was promoted to `domains/embedded/standards/`.
- No personal/local automation was enabled.
- No memory candidate was written to `~/.codex/memories`.
