# Operator binding rollback lifecycle receipt

P2.11 adds a read-only lifecycle receipt for a completed P2.10 governed evidence-binding rollback.

It does not authorize rollback, execute rollback, authorize reapply, execute reapply, or mutate canonical evidence.

## Position in the chain

The receipt closes the audit chain:

1. P2.8 governed apply writes an explicitly authorized evidence reference change.
2. P2.9 verifies the apply journal, before backup, and rollback readiness.
3. P2.10 separately validates rollback authorization and, when explicitly executed, restores the exact P2.8 before bytes through a new `RepositoryTransaction`.
4. P2.11 verifies the completed rollback and records the lifecycle state without granting any new write permission.

The original apply authorization and the rollback authorization are not reusable for a new apply.

## Inputs

The internal CLI consumes two saved JSON results:

```bash
python -m tools.codex_assets.knowledge_hub.operator_binding_rollback_receipt_cli \
  --apply-result ./governed-apply-result.json \
  --rollback-result ./governed-rollback-result.json \
  --json
```

Both files are evidence inputs only. The CLI does not accept owner authorization and does not expose an execute flag.

## Verification contract

P2.11 fails closed unless the supplied rollback result is an exact successful P2.10 projection. It requires, among other invariants:

- `status=rolled-back`;
- `canonical_write_performed=true` for the historical P2.10 result;
- `automatic_binding_enabled=false`;
- `automatic_execution_enabled=false`;
- rollback authorization was validated and unanimously approved;
- reviewer identity remains `reviewer_identity_provider_verified=false`;
- exactly `registry/items.jsonl` was changed;
- registry post-rollback SHA equals the declared restore SHA;
- P2.10 transaction identity is deterministically derived from the rollback-authorization fingerprint.

P2.11 then verifies the actual rollback transaction journal and its backup on disk.

## Apply-to-rollback chain verification

The original P2.8 apply result is re-verified through P2.9.

After a successful rollback, the historical apply receipt is expected to report `post-apply-state-drift`, because the current registry no longer equals the P2.8 after SHA. P2.11 accepts that historical drift only when all of the following are true:

- the apply receipt itself is still cryptographically/deterministically consistent with its original journal and backup;
- P2.10 `registry_pre_rollback_sha256` equals the P2.8/P2.9 apply-after SHA;
- P2.10 `registry_restore_sha256` equals the P2.8/P2.9 apply-before SHA;
- P2.10's referenced apply receipt fingerprint, apply transaction id, and apply authorization fingerprint all match the recomputed P2.9 receipt.

Arbitrary current-state drift is not treated as rollback success.

## Scope re-derivation

P2.11 does not trust the `rollback_scope` in the P2.10 JSON by itself.

It re-derives the rollback scope from two independently retained byte snapshots:

- the original P2.8 transaction's `before/registry/items.jsonl`, which is the pre-apply state;
- the P2.10 rollback transaction's `before/registry/items.jsonl`, which is the post-apply/pre-rollback state.

The resulting item/owner/field scope must exactly equal the scope reported by P2.10. The same P2.8 inverse-mutation checks are therefore exercised again through the shared P2.10 scope logic.

## Current-state verdict

If the current registry SHA still equals the exact P2.10 restore SHA, the result is:

```text
status=verified-current-post-rollback-state
lifecycle_status=rolled-back-and-verified
```

If the historical lifecycle evidence remains valid but the registry changed after rollback, the result is:

```text
status=post-rollback-state-drift
```

The rollback receipt fingerprint remains bound to the completed historical apply/rollback transaction evidence, not to later current-state drift.

## Reapply boundary

A successful P2.11 receipt always keeps:

```text
reapply_ready=false
requires_new_governed_apply=true
original_apply_authorization_reusable=false
rollback_authorization_reusable=false
reapply_performed=false
automatic_execution_enabled=false
```

Reapplying the previously removed reference requires a new governed apply chain. P2.11 never interprets a historical apply approval, rollback approval, user selection, or lifecycle receipt as new authorization.

## Identity boundary

P2.11 preserves the existing conservative identity statement:

```text
reviewer_identity_provider_verified=false
```

The receipt proves consistency of repository evidence and transaction material. It is not an external IdP, e-signature, or reviewer-identity attestation.

## Mutation boundary

P2.11 is read-only:

- no canonical registry write;
- no owner/status/readiness mutation;
- no rollback execution;
- no reapply execution;
- no network access;
- no automatic binding or execution.

The production repository must not be modified using synthetic lifecycle fixtures. Tests exercise the full apply/rollback lifecycle only in temporary repositories.
