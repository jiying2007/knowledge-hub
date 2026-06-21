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
- item `source.migration_manifest`, when present, must be a relative existing Knowledge Hub local path.
- item `source.source_sha256`, when present, must be a lowercase 64-character SHA256 hex string.
- active item `source.source_id` + `source.source_path` must not match an unresolved owner-gated row in owner decision worksheet manifests.
- active item must not use `owner_gate_verified=false`.
- active item must not use blocking owner-gate `review_status` values such as `pending-owner-review`, `needs-owner-resolution`, `owner-intake-ready`, `source-identity-match` or `embedded-knowledge-owner-review-required`.
- `artifact-ref` item `sha256` must be a lowercase 64-character SHA256 hex string, and `size` must be a positive integer.

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
codex-session
codex-workflow
personal-note
artifact-ref
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
embedded
patents
codex
personal
```

Domain/path invariants:

- `root` domain path must be `README.md` or `AGENTS.md`.
- `governance` domain path must live under `governance/`, `registry/`, `indexes/`, `tools/`, `templates/`, `docs/goals/` or `artifacts/manifests/`.
- `projects/<project>` domain path must live under `domains/projects/<project>/` or `artifacts/manifests/`.
- `embedded` domain path must live under `domains/embedded/` or `artifacts/manifests/`.
- `patents` domain path must live under `domains/patents/` or `artifacts/manifests/`.
- `codex` domain path must live under `domains/codex/` or `artifacts/manifests/`.
- `personal` domain path must live under `domains/personal/` or `artifacts/manifests/`.
- `project-specific` scope must use `projects/<project>` domain.
- `codex-memory-curation-governance` scope must use `codex` domain.

## sources.json

登记 Knowledge Hub 挂接的外部或旧知识源。

Required source fields:

- `id`
- `path`
- `role`
- `authority`
- `status`
- `write_policy`
- `migration_strategy`
- `owner`
- `review_after`
- `final_disposition`

Recommended source fields:

- `source_language`
- `expected_normalization`
- `translation_required`
- `retrieved_at`
- `review_status`
- `check`
- `no_check_reason`

Allowed source `role`:

```text
team-knowledge-source
project-archive-source
patent-source
codex-governance-source
auxiliary-memory-source
project-current-docs-source
project-current-tools-source
project-current-knowledge-source
project-product-test-source
project-scratch-source
project-root-artifact-source
project-agent-rules-source
project-agent-config-source
```

Allowed source `authority`:

```text
legacy-team-ssot
legacy-project-history
patent-materials
codex-workflow-history
auxiliary-recall-only
legacy-project-current-docs
legacy-project-current-tools
legacy-project-current-knowledge
legacy-project-product-test
legacy-project-scratch
legacy-project-root-artifacts
legacy-project-agent-rules
legacy-project-agent-config
```

Allowed source `status`:

```text
registered
deprecated
retired
```

Allowed source `write_policy`:

```text
do-not-write-through-knowledge-hub
copy-first-migration-only
do-not-mix-with-engineering-knowledge
use-codex-archive-tools
read-only-unless-explicitly-approved
externalize-to-knowledge-hub-before-prune
```

Allowed source `final_disposition`:

```text
fully-migrated
copy-first-migrated
reference-first-registered
artifact-ref-registered
archive-only-registered
owner-gated-pending-decision
no-migration-with-reason
auxiliary-recall-only
external-tool-owned
mixed-terminal-coverage
```

Source/index invariants:

- source `id` must be unique.
- `indexes/by-source.md` main source table must include every source `id`.
- `indexes/by-source.md` main source table must not include unregistered source ids.
- source `owner` is the maintenance owner for registry/source governance; it is not an owner decision or owner sign-off.
- source `owner` must be registered in `registry/owners.json`.
- source `review_after` must use ISO date format: `YYYY-MM-DD`.
- source `migration_strategy` must explain how the source enters Knowledge Hub control-plane governance without implying copied正文 or active promotion.
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
- `status`

## topics.json

登记主题导航入口及允许的 item kind。每个 topic 必须有唯一 `id`、存在的相对本地 `domain` 路径和非空 `allowed_kinds` 列表；`allowed_kinds` 只能使用 `items.jsonl` 的 allowed `kind`。

Required topic fields:

- `id`
- `domain`
- `allowed_kinds`

## migrations.jsonl

登记 Knowledge Hub 治理、迁移、引用、归档和门禁变更的可追溯记录。

Required migration fields:

- `from`
- `to`
- `mode`
- `status`
- `checked_at`
- `notes`
- `notes_zh` for rows checked on or after 2026-06-21

Migration invariants:

- `checked_at` must use ISO date format: `YYYY-MM-DD`.
- Rows checked on or after 2026-06-21 must include `notes_zh` so migration history remains readable for Chinese maintainers.
- `to` must reference an existing Knowledge Hub local path, such as `artifacts/`, `domains/`, `registry/`, `indexes/`, `governance/`, `tools/` or `templates/`.
- `to` must be relative, not absolute.
- Multiple `to` references may be separated by semicolons.
- The bootstrap placeholder may use empty `from` and `to` only when `mode=none` and `status=bootstrap-empty`.

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
