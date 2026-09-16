# Operator governed binding apply (P2.8)

P2.8 is the explicit write boundary after P2.2–P2.7 discovery, qualification, proposal, patch planning, review, and external owner authorization.

It is intentionally **not** part of the read-only `operator_provider_cli` surface. The write-capable command is a separate internal module so discovery/review cannot accidentally become apply by adding one option.

## Required chain

A governed apply invocation must provide all of the following:

1. the exact proposal fingerprints selected for the transaction;
2. an external P2.7 authorization JSON object created outside the Operator;
3. the exact deterministic P2.7 `authorization_fingerprint` reviewed by the invoking operator;
4. the exact current `registry/items.jsonl` SHA256 reviewed by the invoking operator;
5. an explicit acknowledgement that P2.7 reviewer identity is **not** authenticated by an external identity provider.

Immediately before any write, P2.8 recomputes from the current workspace:

`provider candidate -> P2.3 qualification -> P2.4 proposal -> P2.5 patch plan -> P2.6 review bundle -> P2.7 authorization validation`

The apply executor then materializes the registry bytes using the same P2.5 mutation functions. It does not implement a second evidence-mutation algorithm.

## Explicit invocation

```bash
tools/ci/python-runtime.sh -m tools.codex_assets.knowledge_hub.operator_binding_apply_cli \
  --root . \
  --project <project-id> \
  --proposal-fingerprint sha256:<proposal> \
  --authorization <external-owner-authorization.json> \
  --confirm-authorization-fingerprint sha256:<authorization> \
  --confirm-registry-before-sha256 <64-hex-registry-sha256> \
  --acknowledge-reviewer-identity-unverified \
  --json
```

Repeat `--proposal-fingerprint` only for distinct proposal targets included in the same externally authorized review bundle.

There is deliberately no default apply, no automatic selection, and no generated authorization file. Omitting the reviewer-identity acknowledgement leaves the executor fail-closed.

## Write scope

A successful P2.8 transaction may change exactly one tracked path:

- `registry/items.jsonl`

Within that file, mutation semantics remain those already validated by P2.5:

- `source_refs`, `validation_refs`, `artifact_refs`: append one exact reference;
- `release_ref`: set only when currently empty;
- evidence contract declared status must remain `pending`;
- the mutation must not auto-promote readiness;
- `owner_ref` is not changed;
- registry item owner/status/readiness fields are not changed.

P2.8 does not edit project source documents, indexes, owner worksheets, release records, or user memory.

## Transaction safety

P2.8 uses the existing `RepositoryTransaction` implementation:

- the transaction is planned against the confirmed current registry SHA;
- the single-writer lock is acquired before mutation;
- optimistic SHA preconditions are checked again after lock acquisition;
- new bytes are staged and fsynced;
- the previous file is backed up;
- a write-ahead journal records progress;
- apply failure triggers rollback through the existing transaction layer.

After apply, P2.8 requires the actual registry SHA to equal the exact P2.7/P2.6/P2.5 expected after SHA. A mismatch is an error, not a successful partial result.

## Authorization and identity boundary

P2.8 does not improve the trust level of P2.7 owner identity evidence.

`reviewer_identity_provider_verified=false` remains explicit. The P2.7 file proves that the supplied authorization fields are structurally coherent with the exact canonical `owner_ref`; it does not prove identity through an external identity provider.

The fingerprint/SHA confirmations and `--acknowledge-reviewer-identity-unverified` are an **operator anti-accident boundary**, not identity authentication. They force the invoking operator to name the exact reviewed authorization, exact pre-write registry state, and consciously acknowledge the remaining identity limitation. They must not be described as cryptographic owner identity verification.

## Automatic execution remains disabled

Even though P2.8 contains a write-capable executor:

- `automatic_binding_enabled=false`;
- `automatic_execution_enabled=false`;
- no scheduler or UI automatically invokes the apply CLI;
- test authorizations are never valid justification to mutate the repository's real registry.

Repository-level branch protection and product terminal closure remain separate governance concerns. P2.8 must not be used to claim either one is complete.
