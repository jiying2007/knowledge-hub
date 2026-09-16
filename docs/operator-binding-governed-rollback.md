# Operator governed binding rollback (P2.10)

P2.10 is the separate rollback boundary for a previously successful P2.8 governed evidence binding transaction.

It does **not** reuse the original P2.7 apply approval as rollback approval. A rollback needs a new external decision bound to the exact P2.9 receipt and exact post-apply registry state.

## Required chain

Before rollback can be considered ready, the implementation recomputes and verifies:

`P2.8 applied result -> P2.9 receipt -> before backup/current registry diff -> exact rollback scope -> external rollback authorization`

The P2.9 receipt must still report `verified-current-post-apply-state` and `rollback_ready=true`. If `registry/items.jsonl` has changed since the governed apply, rollback is blocked rather than overwriting later work.

## Exact rollback scope

P2.10 derives the scope from the actual P2.8 transaction backup and the current post-apply registry. It requires:

- identical registry item identity/order before and after the original apply;
- no non-`evidence_contract` item changes;
- no `status`, `profile`, or `owner_ref` drift;
- changed evidence fields limited to `source_refs`, `validation_refs`, `artifact_refs`, and `release_ref`;
- a valid unchanged `owner_ref` for every affected item.

Each affected item becomes one rollback authorization responsibility. Multi-item or multi-owner applies therefore require one independent rollback decision per affected item.

## External rollback authorization

The external JSON object is created outside the Operator. It binds:

- `receipt_fingerprint`;
- original apply `transaction_id`;
- original apply `authorization_fingerprint`;
- exact post-apply registry SHA256;
- exact restore registry SHA256;
- one authorization row per affected item.

Each row contains the exact `item_id`, `project_id`, `item_path`, `owner_ref`, a unique `authorization_id`, `owner_decision`, `reviewed_by`, `reviewed_at`, and `reason`.

Allowed decisions are:

- `approve-rollback`;
- `reject-rollback`.

Any missing item decision, extra item, owner mismatch, reused authorization ID, malformed review date, or rejection blocks execution.

`reviewer_identity_provider_verified=false` remains explicit. P2.10 validates structural ownership against the exact before/after registry scope; it does not claim an external identity provider authenticated `reviewed_by`.

## Validation is the default

The rollback CLI is intentionally validation-only unless `--execute` is supplied:

```bash
tools/ci/python-runtime.sh -m tools.codex_assets.knowledge_hub.operator_binding_rollback_cli \
  --root . \
  --apply-result <p2.8-applied-result.json> \
  --rollback-authorization <external-rollback-authorization.json> \
  --json
```

Validation performs no canonical write.

## Explicit execution boundary

Execution additionally requires four independent operator confirmations:

```bash
tools/ci/python-runtime.sh -m tools.codex_assets.knowledge_hub.operator_binding_rollback_cli \
  --root . \
  --apply-result <p2.8-applied-result.json> \
  --rollback-authorization <external-rollback-authorization.json> \
  --execute \
  --confirm-receipt-fingerprint sha256:<receipt> \
  --confirm-rollback-authorization-fingerprint sha256:<rollback-authorization> \
  --confirm-registry-current-sha256 <64-hex-post-apply-sha256> \
  --acknowledge-reviewer-identity-unverified \
  --json
```

These confirmations are an anti-accident boundary. They are not owner identity authentication.

## Transaction behavior

A successful rollback changes exactly one tracked path:

- `registry/items.jsonl`

The restore bytes are the exact P2.8 `before/registry/items.jsonl` backup verified by P2.9. P2.10 creates a **new** `RepositoryTransaction`; it never edits the original apply journal.

The rollback transaction therefore gets the existing safeguards:

- global single-writer lock;
- optimistic current-SHA precondition checked again after the lock is acquired;
- staged/fsynced restore bytes;
- backup of the post-apply state;
- independent rollback journal;
- automatic recovery to the post-apply state if the rollback transaction itself fails mid-apply.

After execution, P2.10 requires the actual registry SHA to equal the exact P2.8 pre-apply SHA. Otherwise the operation is an error, not a successful rollback.

## What rollback does not mean

A filesystem evidence rollback does not itself revoke or rewrite historical governance decisions. The original P2.8 apply journal and P2.9 receipt remain audit evidence.

P2.10 does not mutate canonical owner/status/readiness fields and does not enable automatic execution. The product terminal-closure verdict and repository branch protection remain separate governance concerns.

Tests exercise the write path only in temporary repositories. No synthetic rollback authorization is justification for changing the real repository registry.
