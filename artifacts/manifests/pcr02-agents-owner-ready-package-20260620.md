# PCR02 AGENTS Owner Ready Package - 2026-06-20

## 结论

本包把 `pcr02-owner-decision-worksheet-001` 单独收口成 owner 可签收材料。它只服务 PCR02 docs `AGENTS.md` 这一条 owner gate：

- 不复制源 `AGENTS.md` 正文。
- 不修改源项目 docs。
- 不生成 owner decision。
- 不关闭 owner gate。
- 不覆盖 Knowledge Hub 根 `AGENTS.md`。
- 不提升到 `domains/embedded/standards/`。
- 不启用自动化，不写 `~/.codex/memories`。

当前状态仍为 `owner-fill-required`，最终门禁仍预期是 `needs-owner-review`，直到 owner 明确填写并验证通过。

## Source Identity

| 字段 | 值 |
| --- | --- |
| source_id | `pcr02-project-docs` |
| source_path | `AGENTS.md` |
| worksheet_id | `pcr02-owner-decision-worksheet-001` |
| owner | `team-core-or-pcr02-docs-owner` |
| observed_sha256 | `95ed7fa20ee52972d79038fb7ec9c5e9b8594fb35b29df50eefdcbf102130566` |
| observed_size | `2414` |
| identity_status | `match` |

`observed_sha256` 和 `observed_size` 只是只读提示，不能自动替代 owner 在签收 JSONL 中显式填写的 `source_sha256` 和 `source_size`。

## Owner 只需回答的问题

请 owner 对以下问题给出唯一结论：

> 是否确认该文件只代表 PCR02 项目本地规则，而不是 Knowledge Hub 根规则或团队标准；若保留，目标只允许落在 PCR02 项目边界的哪个位置？

允许的 `owner_decision` 只有：

| owner_decision | 含义 | 允许 target_decision |
| --- | --- | --- |
| `project-local-rule` | 作为 PCR02 项目本地 docs 规则候选。 | `projects/pcr02/current/project-docs-agent-rules.md` |
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
- `current_validity`
- `scope_statement`
- `applicable_project_version`
- `evidence_refs`
- `status_reason`

## Hard Gate

以下任一条件不满足时，不能越过 owner gate：

- `current_validity` 未明确。
- `scope_statement` 未明确为 PCR02 project-only。
- 未说明适用 branch、SDK version 或 project phase。
- 目标指向 Knowledge Hub 根 `AGENTS.md`。
- 目标指向 `domains/embedded/standards/`。
- 把 PCR02 项目本地规则当成全局 Codex 规则或团队标准。

## Copyable Owner Decision Skeleton

以下 JSON 只能由 owner 填写空字段后作为单行 JSONL 使用。不要把它当作已签收结果。

```json
{"worksheet_id":"pcr02-owner-decision-worksheet-001","source_id":"pcr02-project-docs","source_path":"AGENTS.md","worksheet":"artifacts/manifests/pcr02-owner-decision-worksheets-20260618.jsonl","owner":"team-core-or-pcr02-docs-owner","status":"open","worksheet_status":"owner-fill-required","owner_question_zh":"是否确认该文件只代表 PCR02 项目本地规则，而不是 Knowledge Hub 根规则或团队标准；若保留，目标只允许落在 PCR02 项目边界的哪个位置？","default_state":"reference-only-pending-owner-gate","allowed_owner_decisions":["project-local-rule","reference-only","no-migration"],"must_not":["do not overwrite Knowledge Hub root AGENTS.md","do not promote to domains/embedded/standards","do not treat project-local rules as global Codex rules"],"owner_decision":"","target_decision":"","reviewed_by":"","reviewed_at":"","review_after":"2026-09-17","source_status":"","source_sha256":"","source_size":"","current_validity":"","scope_statement":"","applicable_project_version":"","evidence_refs":[],"status_reason":""}
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
| `rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --summary` | 0 | 当前 7 open、0 resolved、0 active exposure；`AGENTS.md` 是下一条 open gate。 | `tools/knowledge-owner-gates.sh` | Owner gate | `pcr02-agents-owner-ready-package-20260620` |
| `rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --worksheet-id pcr02-owner-decision-worksheet-001 --forms --json` | 0 | 单条 form 可生成；source identity 为 match；owner fields 保持空白。 | `tools/knowledge-owner-gates.sh` | Owner gate | `pcr02-agents-owner-ready-package-20260620` |
| `rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics` | 0 | 全仓一致性通过，0 errors、0 warnings。 | `tools/knowledge-check.sh` | Knowledge Hub | `pcr02-agents-owner-ready-package-20260620` |
| `rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --explain pcr02-agents-owner-ready-package-20260620` | 0 | registry 条目存在，核心索引引用均为 ok。 | `tools/knowledge-check.sh` | Knowledge Hub | `pcr02-agents-owner-ready-package-20260620` |
| `rtk bash ~/knowledge-hub/tools/knowledge-regression.sh --json` | 0 | 20 个 governance regression 场景通过，`kept_temp=false`。 | `tools/knowledge-regression.sh` | Regression | `pcr02-agents-owner-ready-package-20260620` |
| `rtk bash ~/knowledge-hub/tools/knowledge-final-gate.sh --json` | 1 expected | 预期仍为 `needs-owner-review`；`knowledge_check` 和 `knowledge_regression` 通过，唯一 blocker 是 7 个 owner gates open。 | `tools/knowledge-final-gate.sh` | Final gate | `pcr02-agents-owner-ready-package-20260620` |

## 非目标

- 不把 `AGENTS.md` 原文迁移到 `projects/pcr02/current/`。
- 不创建 `projects/pcr02/current/project-docs-agent-rules.md`。
- 不把 `AGENTS.md` 规则合并进 Knowledge Hub 根规则。
- 不变更 worksheet 状态。
- 不修改 `registry/items.jsonl` 中既有 PCR02 owner gate 的状态。
