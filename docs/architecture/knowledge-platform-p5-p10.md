# Knowledge Platform P5-P10

## Purpose

P5-P10 evolves Knowledge Hub from a governed local knowledge control plane into a
production-oriented Knowledge Platform without moving authority away from canonical
Markdown + registry.

The platform follows one invariant:

```text
Canonical knowledge       = Markdown + registry
Derived intelligence      = rebuildable, private, non-authoritative
Task/work-item execution   = external execution plane
High-risk mutation        = explicit owner/human approval
```

## P5 — Security and protocol conformance

P5 adds principal-aware authorization, source ACL propagation, trust classification,
prompt-injection/tool-poisoning boundaries, a native stateless MCP 2026-07-28
profile, and an A2A 1.0 provider card. The legacy MCP adapter remains available as a
compatibility surface but is no longer described as the native 2026-07-28 profile.

External source content is always data-only unless separately promoted through the
governed canonical path. Repository privacy, branch protection, and official
protocol-conformance evidence remain external closure requirements and may not be
faked by repository metadata.

## P6 — Retrieval Intelligence v4

Retrieval v4 applies principal/source ACLs before ranking, then builds a rebuildable
hierarchical Document -> Heading -> Chunk representation. It supports lexical,
pluggable dense, authority, and freshness lanes, query routing, reciprocal-rank
fusion, and an optional reranker.

The default dense fallback remains deterministic feature hashing for offline and
zero-dependency operation. A real embedding provider is opt-in and must pass fresh
Eval v2 regression before becoming a default. A reranker is never trusted to add
candidates; it may only reorder already-authorized candidates.

## P6 — Eval v2

Eval v2 uses versioned JSONL cases carrying query class, language, criticality,
expected/forbidden results, principal context, and scope. Candidate retrieval changes
are compared with an approved baseline and fail on critical-case regressions,
pass-rate drops, or configured latency regression.

The target is 200 production-derived cases, with 500 as a stretch target. Synthetic
cases must not be used merely to inflate coverage numbers.

## P7 — Memory and temporal context

The Memory Runtime is a private hash-chained event store keyed by principal, agent,
and scope. It supports TTL, forget, supersede, active-memory projection, and durable
consolidation candidates. Durable candidates never write canonical knowledge; they
still require provenance, deduplication, evidence, and owner/human promotion.

The derived Temporal Context Graph uses explicit governed relations and validity
windows. It stores item/episode provenance and remains non-authoritative. Invalid
`valid_from` / `valid_to` metadata is fail-closed in P6/P7 paths, and CI audits all
tracked registry items for temporal validity.

## P8 — Source integration

The connector SPI provides bounded incremental checkpoints, ACL propagation,
tombstones, quarantine, content hashing, and provider-neutral normalization.
Provider payload adapters exist for GitHub, Feishu, TAPD, CI, and Google Drive.

Credential handling and network transport remain outside the core. Real provider
adoption requires a production pilot proving ACL changes, tombstones, freshness,
retry/idempotency, and checkpoint semantics. Connector output remains reference,
summary, artifact-reference, or proposal input — never an automatic active item.

## P9 — Platform operations

P9 introduces W3C trace-context correlation across work items, runs, handoffs,
retrieval, evidence, and execution receipts. Raw query/task/prompt/content values are
not persisted; sensitive attributes are hashed before entering the private local span
ledger.

Retrieval lane health detects silent lane loss. Local SLO summaries track latency and
error rate. Network telemetry export remains disabled by default and requires explicit
deployment configuration.

## P10 — Engineering and supply chain

P10 introduces a 15% quarterly legacy-module debt target, a policy branch-coverage
target, focused mutation contracts for fail-closed security logic, and in-toto
Statement/v1-style quality attestations binding subject digest, source commit,
Engineering, Compliance, Restore, Product Final Gate, evidence artifact, and optional
SBOM digest.

The current global statement-coverage gate remains 75% until targeted branch coverage
is proven stable in CI; P10 must not lower existing terminal gates to make the new
platform pass.

## External closure boundary

The following cannot be closed by an ordinary repository commit and remain explicit
external dependencies:

1. make the repository private, or split public engine code from private canonical
   knowledge before any non-public engineering knowledge is hosted;
2. configure a server-side default-branch ruleset with PR and quality requirements,
   conversation resolution, and force-push protection;
3. produce official MCP conformance evidence and A2A TCK evidence if a task server is
   ever implemented in the execution plane;
4. run real Feishu/TAPD/CI/Google Drive provider pilots with production ACL and
   tombstone evidence;
5. configure a production signing identity if quality attestations become signed
   release artifacts.
