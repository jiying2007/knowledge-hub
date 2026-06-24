# PCR02 Memory Auto-Curation Owner Ready Package - 2026-06-20

## 结论

本包把 `pcr02-owner-decision-worksheet-004` 单独收口成 owner 可签收材料。它只服务 PCR02 docs `runbooks/memory-auto-curation-guide.md` 这一条 owner gate：

- 不复制源 runbook 正文。
- 不修改源项目 docs。
- 不生成 owner decision。
- 不关闭 owner gate。
- 不启用任何自动化。
- 不写 `~/.codex/memories`。
- 不写 curation inbox。
- 不写 team active index。
- 不把 personal/local workflow 提升为团队 active workflow。
- 不提升到 `domains/embedded/standards/`。

当前状态仍为 `owner-fill-required`，最终门禁仍预期是 `needs-owner-review`，直到 owner 明确填写并验证通过。

## Source Identity

| 字段 | 值 |
| --- | --- |
| source_id | `pcr02-project-docs` |
| source_path | `runbooks/memory-auto-curation-guide.md` |
| worksheet_id | `pcr02-owner-decision-worksheet-004` |
| owner | `personal-owner-and-team-review-if-teamized` |
| observed_sha256 | `36e8529bff008fb42c90779f11724e020141e19d64a6533d6af99f70dfeedc91` |
| observed_size | `2060` |
| identity_status | `match` |

`observed_sha256` 和 `observed_size` 只是只读提示，不能自动替代 owner 在签收 JSONL 中显式填写的 `source_sha256` 和 `source_size`。

## Owner 只需回答的问题

请 owner 对以下问题给出唯一结论：

> 是否仅允许 personal-local，还是批准一个 teamized-report-only 的禁用治理版本；若团队化，能否明确 enabled=false、writes_memory=false、writes_team_active_index=false？

允许的 `owner_decision` 只有：

| owner_decision | 含义 | 允许 target_decision |
| --- | --- | --- |
| `personal-local` | 仅作为个人/本地参考；不进入团队 active index，不启用自动化。 | `personal-local-reference` |
| `teamized-report-only` | 只允许团队化为禁用的 report-only governance 候选。 | `report-only-governance-candidate` |
| `rejected` | owner 拒绝迁移、抽取或团队化。 | `no-migration` |
| `no-migration` | 不迁移正文，只保留控制面记录和 gate。 | `no-migration` |

## 必填字段

owner decision JSONL 必须填写：

- `owner_decision`
- `target_decision`
- `reviewed_by`
- `reviewed_at`
- `review_after`
- `source_status`
- `source_sha256`
- `source_size`
- `governance_mode`
- `automation_enabled`
- `writes_memory`
- `writes_team_active_index`
- `no_memory_write_gate`
- `manual_approval_owner`
- `manual_approval_cadence`
- `evidence_refs`
- `open_items`
- `status_reason`

## Report-only Governance Boundary

若 owner 选择 `teamized-report-only`，只能进入禁用的 report-only governance 候选，必须同时满足：

- `governance_mode=report-only`
- `automation_enabled=false`
- `writes_memory=false`
- `writes_team_active_index=false`
- `no_memory_write_gate=hard-block`
- `manual_approval_owner` 明确。
- `manual_approval_cadence` 明确。
- 只允许生成 owner 可审查报告类产物。
- `allowed_report_artifact_path` 在证据引用或 open items 中明确。
- secret scan、rollback procedure、runtime no-write evidence 作为证据引用。

允许输出仅限：

- report artifact
- candidate list
- owner worksheet
- run summary
- archive-only note

这些产物不得自动进入正式 memory、AGENTS、skill、workflow、team active index 或团队标准。

## Hard Gate

以下任一条件出现时，不能越过 owner gate：

- 写 `~/.codex/memories/**`。
- 写 `~/.codex/memories/.codex/curation-inbox/**`。
- 写 team active index。
- 自动 send、commit、publish、delete、promote 或 memory-write。
- `teamized-report-only` 被当作自动化启用批准。
- `automation_enabled` 不是 `false`。
- `writes_memory` 不是 `false`。
- `writes_team_active_index` 不是 `false`。
- `no_memory_write_gate` 不是 hard block。
- 未说明人工审批 owner 和复核周期。
- 未补 secret scan、rollback 或 runtime no-write evidence。
- 修改源项目 docs。
- 提升到 `domains/embedded/standards/`。

## Copyable Owner Decision Skeleton

以下 JSON 只能由 owner 填写空字段后作为单行 JSONL 使用。不要把它当作已签收结果。

```json
{"worksheet_id":"pcr02-owner-decision-worksheet-004","source_id":"pcr02-project-docs","source_path":"runbooks/memory-auto-curation-guide.md","worksheet":"artifacts/manifests/pcr02-owner-decision-worksheets-20260618.jsonl","owner":"personal-owner-and-team-review-if-teamized","status":"open","worksheet_status":"owner-fill-required","owner_question_zh":"是否仅允许 personal-local，还是批准一个 teamized-report-only 的禁用治理版本；若团队化，能否明确 enabled=false、writes_memory=false、writes_team_active_index=false？","default_state":"blocked-personal-local","allowed_owner_decisions":["personal-local","teamized-report-only","rejected","no-migration"],"must_not":["do not write ~/.codex/memories","do not add personal/local workflow material to team active index","do not enable automatic actions","do not modify source project docs"],"owner_decision":"","target_decision":"","reviewed_by":"","reviewed_at":"","review_after":"2026-09-17","source_status":"","source_sha256":"","source_size":"","governance_mode":"","automation_enabled":null,"writes_memory":null,"writes_team_active_index":null,"no_memory_write_gate":null,"manual_approval_owner":"","manual_approval_cadence":"","evidence_refs":[],"open_items":[],"status_reason":""}
```

## 验证和落地顺序

1. Owner 填写 JSONL 后，先只读校验：

```bash
rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --validate-forms '<owner-decisions.jsonl>' --json
```

2. 校验通过后，生成只读落地计划：

```bash
rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --validate-forms '<owner-decisions.jsonl>' --landing-plan --json
```

3. 只按 landing plan 手工更新 Knowledge Hub，不修改源项目 docs，不启用自动化，不写 memory。

4. 手工落地后至少运行：

```bash
rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
rtk bash ~/knowledge-hub/tools/knowledge-regression.sh --json
rtk bash ~/knowledge-hub/tools/knowledge-final-gate.sh --json
```

## Evidence Index

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
| --- | ---: | --- | --- | --- | --- |
| `rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --worksheet-id pcr02-owner-decision-worksheet-004 --checklist --forms` | 0 | 单条 checklist 和 form 可生成；source identity 为 match；owner fields 保持空白。 | `tools/knowledge-owner-gates.sh` | Owner gate | `pcr02-memory-auto-curation-owner-ready-package-20260620` |
| `rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --worksheet-id pcr02-owner-decision-worksheet-004 --forms --json` | 0 | JSON form 聚焦 worksheet-004；`owner_decision` 为空，allowed decisions 与 worksheet 一致。 | `tools/knowledge-owner-gates.sh` | Owner gate | `pcr02-memory-auto-curation-owner-ready-package-20260620` |
| `rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics` | 0 | 全仓一致性通过，0 errors、0 warnings。 | `tools/knowledge-check.sh` | Knowledge Hub | `pcr02-memory-auto-curation-owner-ready-package-20260620` |
| `rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --explain pcr02-memory-auto-curation-owner-ready-package-20260620` | 0 | registry 条目存在，核心索引引用均为 ok。 | `tools/knowledge-check.sh` | Knowledge Hub | `pcr02-memory-auto-curation-owner-ready-package-20260620` |
| `rtk bash ~/knowledge-hub/tools/knowledge-regression.sh --json` | 0 | 20 个 governance regression 场景通过，`kept_temp=false`。 | `tools/knowledge-regression.sh` | Regression | `pcr02-memory-auto-curation-owner-ready-package-20260620` |
| `rtk bash ~/knowledge-hub/tools/knowledge-final-gate.sh --json` | 1 expected | 预期仍为 `needs-owner-review`；`knowledge_check` 和 `knowledge_regression` 通过，唯一 blocker 是 7 个 owner gates open。 | `tools/knowledge-final-gate.sh` | Final gate | `pcr02-memory-auto-curation-owner-ready-package-20260620` |

## 非目标

- 不把源 runbook 迁移到 `projects/pcr02/personal/`。
- 不把源 runbook 提升为团队 workflow。
- 不启用 `memory-auto-curation-report-only` 自动化。
- 不写任何 memory 或 curation inbox。
- 不变更 worksheet 状态。
- 不修改 `registry/items.jsonl` 中既有 memory auto-curation governance 条目的状态。
