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

Allowed `kind`:

```text
standard
runbook
architecture
decision
project-current
project-archive
validation
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

## Safety invariants

- `active` and `reviewing` items must have `owner` and `review_after`.
- `superseded` items must have `superseded_by`.
- `artifact-ref` items must have `uri`, `size`, and `sha256`.
- `project-specific` items must not live under `domains/embedded/standards`.
- `personal-local` items must not be referenced by active team indexes.
