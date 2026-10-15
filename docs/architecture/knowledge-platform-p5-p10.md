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
profile, and an A2A 1.0 provider card. The shipped native stateless MCP
2026-07-28 stdio implementation does not accept the retired initialize/session
compatibility path. Historical module labels such as `runtime_v3` and P4 consumer
contracts are not separate authoritative knowledge databases. The stable
`search.py` module is still a caller-facing compatibility facade; it cannot be
deleted without discovering and qualifying real consumers.

External source content is data-only until separately promoted under the
governed canonical path. The repository intentionally runs as a public personal
GitHub repository; it does NOT require switching to private for repository
terminal closure. Public hosting never authorizes exposing secrets, private
workspaces, unlicensed third-party bodies, or raw session content. Protected
`master`, actual Quality/Security checks and hosted conformance evidence remain
required and are verified from GitHub, not assumed from local configuration.

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

## One canonical state and content migration proof

There is only one current writable knowledge authority: canonical Markdown plus
its governed registry. `projects/`, `domains/`, and `notes/` contain the
current or historical bodies; `sources/` and source ledgers record provenance
and dispositions; `indexes/`, search caches, graph, and runtime memory are
rebuildable/non-authoritative. Work-item execution and device, CI, release,
provider ACL, and source-code facts stay authoritative in their own systems.

Do not confuse a single canonical knowledge authority with one boolean that
erases independent evidence. The existing `terminal_closure_cli` computes the
**GitHub repository** verdict; the existing `knowledge-final-gate.sh`
computes **product, content, project evidence, delivery and adoption** maturity.
A human-facing dashboard may summarize these axes, but must derive them from
these two gates, never persist a competing mutable verdict.

The source-control contract covers registered source identities and approved
dispositions; **it does not promise a byte-for-byte copy of external sources**.
Raw Codex history/session/memory, code, logs, credentials and restricted files
are intentionally reference-only or excluded. Even `status=covered` on a
source-root inventory row cannot establish per-file hash completeness. The
existing `knowledge-orphan-files.sh --all --strict` proves Hub body coverage
by exact registry identity or frozen, unregistered-only collection. Its optional
`--convergence --json` report hashes every tracked Hub body, produces
non-destructive exact-duplicate hints, and highlights source-file provenance
that cannot be independently verified from GitHub. It is a **read-only evidence
projection**, not a new Product terminal, content promotion, or external scan.

All of the following are independent acceptance conditions before claiming
full knowledge migration: every reachable source revision has an authorized
snapshot and a complete file-level disposition; retained bodies have a unique
canonical path or documented historical/archive-only role; source hashes and
links are reproducible; pending content and project owner decisions are
resolved or explicitly excluded; no active duplicate authority remains.
Absence of external source access must be reported as *unverified*.

## Actual external qualification boundary

1. Public repository hosting is allowed by the current policy; check public
   information classification and licenses, never silently copy private or
   secret-like data to GitHub.
2. Protected `master`, quality and security gates, hosted offsite restore,
   branch hygiene, and OIDC/Sigstore-signed exact-source evidence must be
   observed for each repository release SHA. Current green evidence does not
   cover later commits.
3. Official native MCP conformance remains required for the shipped MCP
   profile. A2A TCK applies only if the external execution plane later
   implements a task server.
4. Real connector/provider ACL changes, tombstones, retry/checkpoint behavior,
   production retrieval evaluation, memory lifecycle and adoption metrics
   require independent provider or production observations.
5. Product/project owners must explicitly attest semantic boundaries and real
   device, build, validation, release and rollback evidence. Neither CI
   fixtures nor this architecture document can sign on their behalf.
6. Signed CI artifacts currently use hosted OIDC/Sigstore identity. A separate
   production **release** signing requirement, if adopted, is another
   qualification scope and is not implied by a CI attestation.
