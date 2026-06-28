# PCR02 Docs Governance Closeout - 2026-06-18

## 摘要

本 closeout 是 PCR02 项目 docs 纳入 Knowledge Hub 长期治理的阶段性总收口。它汇总 32 个源文件的治理归宿、registry/index 可追溯性和剩余 owner gate。

本文件不是 owner 决策完成证明，不把 owner-gated 条目声明为 active，也不创建新的项目正文。当前完成的是“治理面闭环”：每个源文件都有分类、迁移、引用、artifact-ref 或 owner-gated 归宿。

## Scope

- Source id: `pcr02-project-docs`
- Source root: `~/work/sigmastar/pcr02_ssc305/SourceCode/sdk/verify/xcrz_sigmastar_demo/docs`
- Files classified: `32`
- Closeout mode: registry/index/governance audit
- Write policy: main-agent-only; subagents read-only

## 覆盖结论

| 类别 | 数量 | 当前归宿 | 证据 |
| --- | ---: | --- | --- |
| copy-first 已执行 | 23 | 已落到 Hub 内 PCR02 canonical/archive 目标，registry 状态为 `reviewing` 或 `archived`，非 active。 | `artifacts/manifests/knowledge-hub-source-control-unification-20260624.jsonl`、`sources/pcr02-project-docs/inventory.jsonl` |
| README reference-first | 1 | `domains/projects/pcr02/current/docs-index.ref.md`，source README 仍是正文权威。 | `pcr02-reference-artifact-ref-applied-20260618.jsonl` |
| prog-tool session artifact-ref | 1 | `domains/projects/pcr02/validation/prog-tool-ci-smoke.session.ref.md`，不复制脚本正文。 | `pcr02-reference-artifact-ref-applied-20260618.jsonl` |
| owner-gated closeout | 7 | 已全部形成 owner-gated / archive-only / report-only / split-boundary 治理包。 | ASAN、memory、DVR/motor、remaining owner gates manifest |
| 合计 | 32 | 覆盖完整，无未归属源文件。 | 子代理 coverage audit |

## 7 个 owner-gated 条目

| Source path | 当前治理归宿 | 不能误读为 |
| --- | --- | --- |
| `AGENTS.md` | `reference-only-pending-owner-gate` | active/global Codex rule |
| `standards/diag-command-metadata-standard.md` | `reference-only-pending-owner-gate` | team standard 或已通过 gate 的 current standard |
| `runbooks/asan-debug-guide.md` | `split-required` / `blocked-pending-owner-review` | team-level ASAN standard |
| `runbooks/memory-auto-curation-guide.md` | `blocked-personal-local` / disabled report-only governance | enabled automation 或 memory writer |
| `plans/2026-06-15-dvr-record-proto-sensor-decoupling-plan.md` | `blocked-pending-owner-status-decision` | 当前源码已完成 |
| `reports/2026-05-29-motor-mcu-debug-record.md` | 默认 `archive-only`，补证后才可 validation candidate | 已验证 root cause 或生产策略 |
| `reports/2026-06-16-dvr-record-replay-session-archive.md` | `archive-only`，排除 memory candidates 和 handoff notes | active project facts |

## Registry 与 Index 结论

### 已登记主链路

以下关键治理产物均已登记到 `registry/items.jsonl`，并存在对应文件：

- `pcr02-review-required-resolution-20260617`
- `pcr02-reference-artifact-ref-applied-20260618`
- `pcr02-owner-review-package-20260618`
- `pcr02-owner-review-follow-up-20260618`
- `pcr02-owner-decision-worksheets-20260618`
- `pcr02-asan-split-targets-20260618`
- `memory-auto-curation-report-only-governance-20260618`
- `pcr02-dvr-motor-closeout-targets-20260618`
- `pcr02-remaining-owner-gates-20260618`
- `pcr02-docs-governance-closeout-20260618`
- `pcr02-project-docs-owner-decision-landing-20260623`
- `knowledge-hub-source-control-unification-20260624`

`registry/items.jsonl` 已覆盖从早期 classification/copy-first 过程，到 reference/artifact-ref、owner package、follow-up、worksheets、owner decision landing、source-control unification 和后续 split/closeout/gate 的治理演进链路；成熟态不再保留 20260616 过程 manifest 文件作为当前树文件。

### 本轮索引修补

本轮补齐：

- `indexes/by-project.md`：增加 PCR02 docs governance closeout。
- `indexes/by-source.md`：增加 registry/index control-plane closeout。
- `indexes/by-status.md`：把 closeout id 纳入 `reviewing`。
- `indexes/by-topic.md`：增加 PCR02 docs governance closeout 和 registry/index closeout topic。
- `indexes/by-owner.md`：补齐 owner 为 `leiwenjun` 的早期 PCR02 audit 条目。
- `indexes/by-review-date.md`：补齐 2026-07-16、2026-07-17、2026-07-18 和 2026-09-17 的 PCR02 audit/review 条目。

本轮未展开 23 个 `migrated-pcr02-docs-copyfirst-*` 到 `by-owner`，因为这些条目的 owner 是 `team-core`，且当前 `by-owner` 只有 `leiwenjun` 分组。它们已通过 `registry/items.jsonl`、`by-status` 和 copy-first manifest 可追溯。

## Non-actions

- No source project file was edited.
- No source document body was copied in this closeout.
- No new `domains/projects/pcr02/**` body was created.
- No owner-gated item was marked resolved or active.
- No PCR02 project-specific material was promoted to `domains/embedded/standards/`.
- No automation was enabled.
- No memory was written.
- No source worktree was cleaned, reverted or rewritten.

## Open owner gates

这些 open items 是后续 owner 决策任务，不是本 closeout 的覆盖缺口：

- PCR02 `AGENTS.md`：owner、当前有效性、project-only scope、适用 branch/SDK/project phase、review cycle、target decision。
- `diag-command-metadata-standard.md`：diag owner sign-off、project-only source-of-truth、适用版本、provider/metadata match evidence、五个 gate 实际结果或 owner exception。
- ASAN split：owner decision、适用版本、target binary、实际 build artifact、team candidate status、external overlap decision。
- Memory automation：owner decision、report artifact path、secret scan、rollback、no-memory-write gate 和 runtime evidence。
- DVR plan：唯一状态、最终 branch/commit/tag、proto/build/refcount/grep 证据、`task/iot`、replay data channel、`LIST_FETCH`、`RecordSetEvent` contract decision。
- Motor MCU debug record：Motor MCU/SoC owner review、固件/参数/串口或协议日志、复测、标定前后数据、故障码字段、整机验证记录。
- DVR session archive：archive metadata approval、validation/decision extract approval、memory candidate exclusion confirmation。

## Verification plan

```bash
rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run
rtk bash ~/knowledge-hub/tools/knowledge-search.sh "PCR02 docs governance closeout"
rtk bash ~/knowledge-hub/tools/knowledge-search.sh "PCR02 32 docs owner-gated"
rtk bash ~/knowledge-hub/tools/knowledge-search.sh "PCR02 registry index closeout"
rtk bash ~/knowledge-hub/tools/knowledge-search.sh "owner-gated not active"
rtk jq -c . artifacts/manifests/pcr02-docs-governance-closeout-20260618.jsonl
```

## Review

- owner：`leiwenjun`
- review_after：`2026-09-17`
- validation_refs：`tools/knowledge-check.sh --dry-run`
