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

## Safety invariants

- `active` and `reviewing` items must have `owner` and `review_after`.
- `superseded` items must have `superseded_by`.
- `artifact-ref` items must have `uri`, `size`, and `sha256`.
- `project-specific` items must not live under `domains/embedded/standards`.
- `personal-local` items must not be referenced by active team indexes.
- Human-readable title, summary, conclusion, risk and review notes should be Chinese by default.
- AI generated or AI transformed content must not become `active` without human review evidence.
- External-source derived items must record source metadata, read status and promotion decision before promotion.
