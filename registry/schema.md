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
- `created_at`
- `updated_at`

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
- `governance` domain path must live under `governance/`, `registry/`, `indexes/`, `tools/`, `templates/` or `artifacts/manifests/`.
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

Recommended source fields:

- `source_language`
- `expected_normalization`
- `translation_required`
- `retrieved_at`
- `review_status`

Allowed source `role`:

```text
team-knowledge-source
project-archive-source
patent-source
codex-governance-source
auxiliary-memory-source
project-current-docs-source
```

Allowed source `authority`:

```text
legacy-team-ssot
legacy-project-history
patent-materials
codex-workflow-history
auxiliary-recall-only
legacy-project-current-docs
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

## migrations.jsonl

登记 Knowledge Hub 治理、迁移、引用、归档和门禁变更的可追溯记录。

Required migration fields:

- `from`
- `to`
- `mode`
- `status`
- `checked_at`
- `notes`

Migration invariants:

- `checked_at` must use ISO date format: `YYYY-MM-DD`.
- `to` must reference an existing Knowledge Hub local path, such as `artifacts/`, `domains/`, `registry/`, `indexes/`, `governance/`, `tools/` or `templates/`.
- `to` must be relative, not absolute.
- Multiple `to` references may be separated by semicolons.
- The bootstrap placeholder may use empty `from` and `to` only when `mode=none` and `status=bootstrap-empty`.

## Safety invariants

- `active` and `reviewing` items must have `owner` and `review_after`.
- `superseded` items must have `superseded_by`.
- `artifact-ref` items must have `uri`, `size`, and `sha256`.
- `project-specific` items must not live under `domains/embedded/standards`.
- `personal-local` items must not use `active` status and must not be referenced by active team indexes.
- Human-readable title, summary, conclusion, risk and review notes should be Chinese by default.
- AI generated or AI transformed content must not become `active` without human review evidence.
- AI generated `active` items must provide `human_reviewed_by`, `human_reviewed_at`, and `review_basis`.
- External-source derived items must record source metadata, read status and promotion decision before promotion.
