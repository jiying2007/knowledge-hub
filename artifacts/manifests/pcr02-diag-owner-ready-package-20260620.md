# PCR02 Diag Metadata Owner Ready Package - 2026-06-20

## 结论

本包把 `pcr02-owner-decision-worksheet-002` 单独收口成 owner 可签收材料。它只服务 PCR02 docs `standards/diag-command-metadata-standard.md` 这一条 owner gate：

- 不复制源文档正文。
- 不修改源项目 docs。
- 不生成 owner decision。
- 不关闭 owner gate。
- 不创建 PCR02 current / decision 正文。
- 不提升为团队标准，不写入 `domains/embedded/standards/`。
- 不把源文档里的 gate command 文本当成已通过证据。
- 不启用自动化，不写 `~/.codex/memories`。

当前状态仍为 `owner-fill-required`，最终门禁仍预期是 `needs-owner-review`，直到 owner 明确填写并验证通过。

## Source Identity

| 字段 | 值 |
| --- | --- |
| source_id | `pcr02-project-docs` |
| source_path | `standards/diag-command-metadata-standard.md` |
| worksheet_id | `pcr02-owner-decision-worksheet-002` |
| owner | `pcr02-diag-owner-or-team-core` |
| observed_sha256 | `89e897bee7e3f8372a0d4c4655748fbe3476780129b157718387c1cbbb80e95d` |
| observed_size | `5316` |
| identity_status | `match` |

`observed_sha256` 和 `observed_size` 只是只读提示，不能自动替代 owner 在签收 JSONL 中显式填写的 `source_sha256` 和 `source_size`。

## Owner 只需回答的问题

请 owner 对以下问题给出唯一结论：

> 是否确认它仍是 PCR02 的 project-only source of truth，且 provider lifecycle、metadata、catalog/help 运行态与文档一致；若不一致，是转 reference-only 还是给 documented owner exception？

允许的 `owner_decision` 只有：

| owner_decision | 含义 | 允许 target_decision |
| --- | --- | --- |
| `pcr02-project-decision-after-owner-gate` | 作为 PCR02 项目 decision 候选，仍需 owner 证据和落地验证。 | `projects/pcr02/decisions/diag-command-metadata-standard.md` |
| `pcr02-project-current-after-owner-gate` | 作为 PCR02 项目 current 候选，必须有 gate evidence 或 documented owner exception。 | `projects/pcr02/current/diag-command-metadata-standard.md` |
| `reference-only` | 只保留引用和 source identity，不复制正文。 | `reference-only` |
| `no-migration` | owner 确认不迁移、不抽取。 | `no-migration` |

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
- `project_only_source_of_truth`
- `applicable_branch_firmware_version`
- `implementation_match`
- `gate_evidence`
- `evidence_refs`
- `status_reason`

## Gate Evidence 要求

若 owner 选择 `pcr02-project-decision-after-owner-gate` 或 `pcr02-project-current-after-owner-gate`，必须至少提供以下二选一：

- 五类 diag gate 的实际运行结果引用。
- documented owner exception，并说明为什么允许在缺少部分 gate 输出时继续。

建议 gate 类别：

- diag metadata check。
- diag command quality check。
- diag naming check。
- diag interface coverage check。
- diag layer deps check。

仅把源文档中的命令文本复制到 `gate_evidence` 不算通过证据。

## Hard Gate

以下任一条件不满足时，不能越过 owner gate：

- `project_only_source_of_truth` 未明确。
- `applicable_branch_firmware_version` 未明确。
- `implementation_match` 未说明 provider lifecycle、metadata、catalog/help 运行态是否与文档一致。
- `gate_evidence` 为空，且没有 documented owner exception。
- 目标指向 `domains/embedded/standards/`。
- 把 PCR02 命令名、项目路径或 provider lifecycle 假设泛化为跨项目默认。
- 把 `reference-only` 或 `no-migration` 结果继续落成 active/current。

## Copyable Owner Decision Skeleton

以下 JSON 只能由 owner 填写空字段后作为单行 JSONL 使用。不要把它当作已签收结果。

```json
{"worksheet_id":"pcr02-owner-decision-worksheet-002","source_id":"pcr02-project-docs","source_path":"standards/diag-command-metadata-standard.md","worksheet":"artifacts/manifests/pcr02-owner-decision-worksheets-20260618.jsonl","owner":"pcr02-diag-owner-or-team-core","status":"open","worksheet_status":"owner-fill-required","owner_question_zh":"是否确认它仍是 PCR02 的 project-only source of truth，且 provider lifecycle、metadata、catalog/help 运行态与文档一致；若不一致，是转 reference-only 还是给 documented owner exception？","default_state":"reference-only-pending-owner-gate","allowed_owner_decisions":["pcr02-project-decision-after-owner-gate","pcr02-project-current-after-owner-gate","reference-only","no-migration"],"must_not":["do not promote whole file to team standard","do not place under domains/embedded/standards","do not treat PCR02 paths and command names as cross-project defaults","do not claim active standard without gate evidence"],"owner_decision":"","target_decision":"","reviewed_by":"","reviewed_at":"","review_after":"2026-09-17","source_status":"","source_sha256":"","source_size":"","project_only_source_of_truth":"","applicable_branch_firmware_version":"","implementation_match":"","gate_evidence":"","evidence_refs":[],"status_reason":""}
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

3. 只按 landing plan 手工更新 Knowledge Hub，不修改源项目 docs。

4. 手工落地后至少运行：

```bash
rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
rtk bash ~/knowledge-hub/tools/knowledge-regression.sh --json
rtk bash ~/knowledge-hub/tools/knowledge-final-gate.sh --json
```

## Evidence Index

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
| --- | ---: | --- | --- | --- | --- |
| `rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --worksheet-id pcr02-owner-decision-worksheet-002 --checklist --forms` | 0 | 单条 checklist 和 form 可生成；source identity 为 match；owner fields 保持空白。 | `tools/knowledge-owner-gates.sh` | Owner gate | `pcr02-diag-owner-ready-package-20260620` |
| `rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --worksheet-id pcr02-owner-decision-worksheet-002 --forms --json` | 0 | JSON form 聚焦 worksheet-002；`owner_decision` 为空，allowed decisions 与 worksheet 一致。 | `tools/knowledge-owner-gates.sh` | Owner gate | `pcr02-diag-owner-ready-package-20260620` |
| `rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics` | 0 | 全仓一致性通过，0 errors、0 warnings。 | `tools/knowledge-check.sh` | Knowledge Hub | `pcr02-diag-owner-ready-package-20260620` |
| `rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --explain pcr02-diag-owner-ready-package-20260620` | 0 | registry 条目存在，核心索引引用均为 ok。 | `tools/knowledge-check.sh` | Knowledge Hub | `pcr02-diag-owner-ready-package-20260620` |
| `rtk bash ~/knowledge-hub/tools/knowledge-regression.sh --json` | 0 | 20 个 governance regression 场景通过，`kept_temp=false`。 | `tools/knowledge-regression.sh` | Regression | `pcr02-diag-owner-ready-package-20260620` |
| `rtk bash ~/knowledge-hub/tools/knowledge-final-gate.sh --json` | 1 expected | 预期仍为 `needs-owner-review`；`knowledge_check` 和 `knowledge_regression` 通过，唯一 blocker 是 7 个 owner gates open。 | `tools/knowledge-final-gate.sh` | Final gate | `pcr02-diag-owner-ready-package-20260620` |

## 非目标

- 不把源文档迁移到 `projects/pcr02/decisions/`。
- 不把源文档迁移到 `projects/pcr02/current/`。
- 不把源文档提升为团队标准。
- 不变更 worksheet 状态。
- 不修改 `registry/items.jsonl` 中既有 PCR02 owner gate 的状态。
