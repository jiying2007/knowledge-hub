# Registry Schema

## items.jsonl

每行一个知识条目。

Required fields:

- `id`
- `title`
- `kind`
- `domain`
- `path`
- `scope`
- `visibility`
- `status`
- `owner`
- `source`
- `review_after`
- `validation_refs`
- `review_status`
- `created_at`
- `updated_at`
- `promotion`
- `tags`

Recommended readability fields:

- `summary_zh`
- `source_language`
- `primary_language`
- `translation_status`
- `terminology_status`
- `glossary_refs`

Recommended evidence fields:

- `evidence_strength`
- `evidence_refs`
- `review_status`
- `owner_gate_verified`

Recommended AI provenance fields:

- `generated_by_ai`
- `ai_role`
- `ai_model_or_tool`
- `ai_generated_at`
- `human_reviewed_by`
- `human_reviewed_at`
- `review_basis`
- `human_review_decision`

AI human review decision values:

```text
accept-as-review-record
needs-edits
archive-only
reject
defer
```

`human_review_decision` 记录真实人工复核结论，不等同于 owner decision、active promotion 或 source 项目授权。`needs-edits` 和 `defer` 表示复核未闭环，在 `knowledge-status.sh --strict --final-profile max-body` 中仍是 blocker。

Recommended external-source fields:

- `retrieved_at`
- `read_status`
- `source_license`
- `promotion_decision`

Date invariants:

- `created_at`, `updated_at` and `review_after` must use ISO date format: `YYYY-MM-DD`.
- `updated_at` must be the same date as or later than `created_at`.
- stale `review_after` is a warning, not an error; it should guide human review without blocking unrelated maintenance.

Source reference invariants:

- item `source` must be an object.
- item `source.source_id`, when present, must be registered in `registry/sources.json`.
- item `source.source_manifest`, when present, must be a relative existing Knowledge Hub local path.
- item `source.source_sha256`, when present, must be a lowercase 64-character SHA256 hex string.
- active item `source.source_id` + `source.source_path` must not match an unresolved owner-gated row in owner decision worksheet manifests.
- active item must not use `owner_gate_verified=false`.
- active item must not use blocking owner-gate `review_status` values such as `pending-owner-review`, `needs-owner-resolution`, `owner-intake-ready`, `source-identity-match` or `embedded-knowledge-owner-review-required`.
- `artifact-ref` item `sha256` must be a lowercase 64-character SHA256 hex string, and `size` must be a positive integer.

Source control directory invariants:

- 每个 `registry/sources.json` 中的 registered source 必须有 `sources/<source_id>/README.md`、`inventory.jsonl`、`coverage.md`、`source-policy.md`。
- `inventory.jsonl` 每行至少包含：`id`、`source_id`、`source_path`、`object_type`、`hub_disposition`、`target_path`、`status`、`reason_zh`、`risk_zh`、`checked_at`。
- `object_type` 允许值：`markdown`、`session`、`history`、`tool`、`source-code`、`config`、`artifact`、`binary`、`log`、`archive`、`manifest`、`automation-run`、`unknown`。
- `hub_disposition` 允许值：`copy-body`、`summary-only`、`artifact-ref`、`reference-only`、`archive-only`、`hash-only-provenance`、`exclude`。
- `status` 允许值：`pending`、`covered`、`blocked`、`excluded`。
- `target_path` 必须是 repo-relative local path、source-local reference 或空值；不得使用绝对路径、`./` 或 `../`。
- `session`、`history`、`source-code`、`binary`、`log` 不能使用 `copy-body`，只能使用摘要、引用、artifact-ref、archive-only、hash-only-provenance 或 exclude。
- 正文最大迁移 profile 下，`copy-body` 只允许用于 `object_type=markdown` 且 `target_path` 指向 Hub 正文目录 `projects/`、`domains/` 或 `notes/` 下的现存路径；其他正文迁移动作必须改为 summary-only、artifact-ref、reference-only、archive-only 或 exclude。
- 正文最大迁移 profile 下，`status=pending` 的 inventory row 是 blocker；`covered`、`blocked`、`excluded` 才能表达已分类终态，其中 `blocked` 必须写清 `reason_zh` 和 `risk_zh`。
- owner decision landing 产生本地 target 时，`knowledge-check` 按硬切换后的 canonical path 校验目标存在；`domains/projects/<project>/...` 与 `domains/personal/...` 不再自动映射，当前 owner decision 不得继续使用旧入口。

Validation reference invariants:

- `active` and `reviewing` items must have non-empty `validation_refs`.
- `validation_refs`, when present, must be a list of non-empty strings.
- validation refs that are plain local Knowledge Hub paths must be normalized repository-relative paths and must exist.
- absolute paths, `./` paths, `../` paths, and unsupported path-like refs are rejected unless they are part of a command-shaped ref.
- command-shaped refs are recorded but not executed by `knowledge-check`.

Manual offline minimum fields:

- 人工在 AI、Codex、网络或工具不可用时也可以先写正文和 registry/index，但必须保留 `validation_refs` 与 `review_status`。
- 证据暂时不足时，`status` 使用 `reviewing`，`review_status` 使用 `manual-entry-pending-review`，`validation_refs` 至少填写人工可复核路径、现场记录或 no-check reason。
- 无法立即运行工具时，在正文或相邻维护记录中保留 `manual_validation_pending: true`、原因、后续检查命令、owner 和 review_after。

Discoverability and promotion invariants:

- `tags` must be a non-empty list of non-empty strings.
- `promotion` must be present.
- currently allowed item `promotion` value is `none`; future promotion states must be added to schema and `knowledge-check` before use.
- `promotion_decision` is a human-readable decision note for promotion boundary or non-promotion rationale; it does not replace `promotion`, owner decision, active review or team-level promotion gates.

Allowed `kind`:

```text
standard
runbook
architecture
decision
project-current
project-archive
validation
audit
patent
debug-record
external-source-note
owner-decision-worksheet
patent-disclosure
codex-session
codex-workflow
personal-note
artifact-ref
authorization
automation-run
```

Allowed `status`:

```text
draft
active
reviewing
archived
superseded
rejected
personal
```

Allowed `scope`:

```text
team-general
project-specific
codex-memory-curation-governance
```

Allowed `visibility`:

```text
team-internal
personal-local
```

Allowed `promotion`:

```text
none
```

Allowed `domain` roots:

```text
root
governance
projects
notes
embedded
patents
codex
```

Domain/path invariants:

- `root` domain path must be `README.md` or `AGENTS.md`.
- `governance` domain path must live under `governance/`, `registry/`, `indexes/`, `tools/`, `templates/`, `docs/goals/` or `artifacts/manifests/`.
- `projects/<project>` domain path must live under `projects/<project>/` or `artifacts/manifests/`.
- `notes` domain path must live under `notes/` or `artifacts/manifests/`.
- `embedded` domain path must live under `domains/embedded/` or `artifacts/manifests/`.
- `patents` domain path must live under `domains/patents/` or `artifacts/manifests/`.
- `codex` domain path must live under `domains/codex/` or `artifacts/manifests/`.
- `personal` domain is deprecated. New personal-local content must use `domain=notes` and `path=notes/personal/**`.
- `project-specific` scope must use `projects/<project>` domain.
- `codex-memory-curation-governance` scope must use `codex` domain.

## sources.json

登记 Knowledge Hub 的 source 控制面。终态下 `path` 必须指向 Hub 内 `sources/<source_id>`；旧外部路径只能写入 `origin_path` 作为 provenance，不得作为 active source、check command 或新增归档入口。

Required source fields:

- `id`
- `path`
- `role`
- `authority`
- `status`
- `write_policy`
- `source_strategy`
- `owner`
- `review_after`
- `final_disposition`

Recommended source fields:

- `origin_path`
- `canonical_target`
- `artifact_target`
- `canonical_manifest`
- `decommission_manifest`
- `source_language`
- `expected_normalization`
- `translation_required`
- `retrieved_at`
- `review_status`
- `check`
- `no_check_reason`

Allowed source `role`:

```text
hub-canonical-source
hub-runtime-input
hub-native-source
```

Allowed source `authority`:

```text
knowledge-hub-canonical
runtime-input-provenance
knowledge-hub-ledger
```

Allowed source `status`:

```text
registered
deprecated
retired
```

Allowed source `write_policy`:

```text
knowledge-hub-only
runtime-read-only-input
hub-native-registry
```

Allowed source `final_disposition`:

```text
hub-canonical
runtime-input-reference-only
hub-native-source
```

Source path invariants:

- `path` must be a Hub-relative `sources/<source_id>` path and must exist.
- `origin_path`, when present, is historical provenance only; it must not be used as a default scan path, search source, check command, active index entry, or new archive destination.
- `check` must validate the Hub control directory or Hub-native ledger; it must not call retired external tools or depend on `~/embedded`, `~/codex/docs/archive`, `~/work`, `~/.codex`, or `/vsdata`.
- Former external sources use `status=retired`, `role=hub-canonical-source`, `authority=knowledge-hub-canonical`, `write_policy=knowledge-hub-only`, and `final_disposition=hub-canonical`.
- Runtime inputs such as Codex history, raw sessions, session index, and memories use `role=hub-runtime-input` and `final_disposition=runtime-input-reference-only`; they are not deleted and are not copied as knowledge正文.

## authorizations.jsonl

登记 AI / Codex 或自动化执行高风险动作前的授权账本。没有匹配授权记录时，AI / Codex 仍可执行 Git 可回滚的 Hub 本仓 L1/L2 维护和本地 commit；高风险动作只能输出 plan、diff、manifest、review package 或 report-only 报告。

Required authorization fields:

- `authorization_id`
- `authorized_by`
- `authorized_at`
- `scope`
- `allowed_actions`
- `expires_at`
- `evidence_refs`
- `rollback_path`
- `validation_commands`
- `status`

Allowed authorization `allowed_actions` values:

```text
owner-decision-landing
active-promotion
memory-write
source-project-write
automation-apply-with-review
external-publish
delete-or-prune
remote-git-write
```

Allowed authorization `status` values:

```text
active
expired
revoked
used
superseded
```

Authorization invariants:

- `authorized_at` and `expires_at` must use ISO date format: `YYYY-MM-DD`.
- `allowed_actions` must be a non-empty list.
- `scope` must be narrow enough to identify project/source/path/action boundary.
- `evidence_refs` must reference an existing local path, command-shaped evidence, or current-session explicit user instruction.
- `rollback_path` and `validation_commands` must be non-empty for write actions.
- AI / Codex may be executor, but must not pretend to be a human reviewer unless the authorization explicitly says it is acting on behalf of that owner.

## automation-runs.jsonl

登记跨项目、跨会话 AI 自动化运行。它是 Hub 主库串联 project、session、source、authorization 和输出证据的最小账本。

Required automation run fields:

- `run_id`
- `automation_id`
- `project_id`
- `trigger`
- `mode`
- `status`
- `started_at`
- `input_refs`
- `output_refs`
- `validation_refs`

Recommended automation run fields:

- `session_id`
- `workstream_id`
- `source_ids`
- `authorization_id`
- `rollback_ref`
- `notes_zh`

Allowed automation `mode` values:

```text
read-only
report-only
plan-only
local-commit
apply-with-review
forbidden
```

Automation run invariants:

- `apply-with-review` requires an `authorization_id` registered in `registry/authorizations.jsonl`.
- `remote-git-write` 类动作必须使用 authorization `allowed_actions=["remote-git-write"]` 或更窄授权，不能用本地 commit 代替。
- `read-only`、`report-only`、`plan-only` 和 `local-commit` 不得写 memory、源项目、team active index、owner gate closure 或远端 Git 状态。
- 每次自动化运行必须能从 `input_refs` 找到来源，从 `output_refs` 找到产物，从 `validation_refs` 找到验证或待验证原因。

Source/index invariants:

- source `id` must be unique.
- `indexes/by-source.md` main source table must include every source `id`.
- `indexes/by-source.md` main source table must not include unregistered source ids.
- source `owner` is the maintenance owner for registry/source governance; it is not an owner decision or owner sign-off.
- source `owner` must be registered in `registry/owners.json`.
- source `review_after` must use ISO date format: `YYYY-MM-DD`.
- stale source `review_after` is a warning/status surface, not a blocking error; `knowledge-check --json` should expose the source id in `source_check_health.stale_review_after_ids`, and `knowledge-status --json` should expose `sources.stale_review_after_count` and `sources.stale_review_after_sample`.
- source `source_strategy` must explain how the source enters Knowledge Hub control-plane governance without implying copied正文 or active promotion.
- source `final_disposition` must use the allowed enum and describe control-plane disposition, not owner approval.
- source `check`, when present, records a read-only validation command or inventory command.
- if source `check` is empty, source registry must record `no_check_reason`; the latest source coverage manifest should also record or reference the reason.
- source coverage rows should include `source_id`, `status`, `classification`, `decision`, `risk`, `owner` and `checked_at`.
- source coverage rows should include `source_identity` or `evidence_refs` when a directory source cannot be represented by one stable file hash.
- tools that select the latest source coverage manifest should expose `source_coverage_selection` with `pattern`, `strategy`, `candidate_count`, `candidates`, `selected` and `reason_zh`.
- `knowledge-check --json` should expose `source_coverage_health` with registered、row、unique、missing、stale、duplicate、missing-field and invalid-date summaries so pass results are still auditable.
- core item indexes `indexes/by-owner.md`, `indexes/by-review-date.md` and canonical status buckets in `indexes/by-status.md` must not duplicate registry item ids.

## owners.json

登记 registry item 可使用的 owner id。每个 `registry/items.jsonl` 条目的 `owner` 必须能在这里找到，避免责任人拼写漂移或临时 owner 长期残留。

Required owner fields:

- `id`

Recommended owner fields:

- `display_name`
- `default_review_cycle_days`

## owner-routing.json

登记 owner decision worksheet 中抽象签收角色的人工分派路由。它只解决“应该找谁分派/升级”，不生成 owner decision，不替代 `reviewed_by`，不关闭 owner gate。

Required route fields:

- `decision_owner_role`
- `source_id`
- `routing_status`
- `routing_owner`
- `required_real_owner_zh`
- `escalation_zh`
- `notes_zh`

Recommended route fields:

- `candidate_registry_owners`
- `must_not`

Allowed route `routing_status`:

```text
mapped-to-registry-owner
needs-human-assignment
unmapped
retired
```

Owner routing invariants:

- `decision_owner_role` must match an owner role used by owner decision worksheets, such as `owner_required` or `owner_candidate`.
- `source_id` must be registered in `registry/sources.json`.
- `routing_owner` is a registered maintenance owner responsible for分派和升级，不是最终 decision owner。
- `routing_owner` and `candidate_registry_owners[]` must be registered in `registry/owners.json`.
- Every open owner decision worksheet role should have one route. Missing routes are blocking governance drift, not owner approval.
- `owner-routing.json` must keep `notes_zh` and `required_real_owner_zh` readable in Chinese.
- A route must not be used as `reviewed_by` unless the same human owner actually fills and signs the owner decision form.

## projects.json

登记 registry item 可使用的 project id。每个 `registry/items.jsonl` 条目若使用 `domain=projects/<project>`，则 `<project>` 必须能在这里找到，避免项目 id 拼写漂移或临时项目目录长期残留。

Required project fields:

- `id`

Recommended project fields:

- `name`
- `domain`
- `entry`
- `current`
- `archive`
- `status`

Project registry must be Hub-first: `entry`, `current` and `archive` point to local Knowledge Hub paths. Retired external locations are not current project facts; when needed, recover them from Git history instead of adding current registry fields.

## topics.json

登记主题导航入口及允许的 item kind。每个 topic 必须有唯一 `id`、存在的相对本地 `domain` 路径和非空 `allowed_kinds` 列表；`allowed_kinds` 只能使用 `items.jsonl` 的 allowed `kind`。

Required topic fields:

- `id`
- `domain`
- `allowed_kinds`

## artifacts/manifests JSONL lightweight contract

`artifacts/manifests/*.jsonl` 是治理证据、source coverage、artifact-ref、owner worksheet 和回归记录的结构化制品。它不是 `registry/items.jsonl`，不得强行套用完整 item schema。

新增或 2026-06-21 及之后的 `knowledge-hub-*.jsonl` governance manifest 至少保持：

- `id`
- `status`
- 日期证据：`checked_at`、`created_at`、`updated_at`、`review_after` 或文件名中的 `YYYYMMDD`
- 中文可读说明：`summary_zh` 或 `notes_zh`
- 证据字段：`evidence`、`evidence_refs`、`validation_refs`、`verification_commands` 或 `source_refs`
- 边界字段：`boundaries`、`must_not`、`non_goals`、`rollback_policy` 或 `risk`

Manifest profile invariants:

- 2026-06-21 之前的历史 manifest 不反向强制改写。
- copy-first、artifact-ref、owner worksheet、owner form 和 source coverage 清单按各自类型字段保持兼容，不为美化字段而改变语义。
- source coverage row 继续遵守 source coverage 字段要求。
- owner worksheet/form 结构门禁不得生成 owner decision，不得关闭 owner gate。
- 机器清单可以保留英文 key，但 `summary_zh`、`notes_zh`、`decision`、`risk` 或相邻 Markdown 必须给中文维护者足够上下文。

## Safety invariants

- `active` and `reviewing` items must have `owner` and `review_after`.
- item `owner` must be registered in `registry/owners.json`.
- item `domain=projects/<project>` must use a project id registered in `registry/projects.json`.
- topic `domain` must be a relative existing local path, and topic `allowed_kinds` must use item kind enums.
- `superseded` items must have `superseded_by`.
- `artifact-ref` items must have `uri`, `size`, and `sha256`.
- `project-specific` items must not live under `domains/embedded/standards`.
- `personal-local` items must not use `active` status and must not be referenced by active team indexes.
- Human-readable title, summary, conclusion, risk and review notes should be Chinese by default.
- AI generated or AI transformed content must not become `active` without human review evidence.
- AI generated `active` items must provide `human_reviewed_by`, `human_reviewed_at`, and `review_basis`.
- AI generated registry items created on or after 2026-06-21 must provide `ai_role`, `ai_model_or_tool`, and `ai_generated_at`, even when they remain `reviewing`.
- External-source derived items must record source metadata, read status and promotion decision before promotion.
