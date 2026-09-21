# Security Policy

## Supported security boundary

Knowledge Hub treats canonical Markdown and registry state as governed knowledge, but
repository hosting controls are outside the runtime trust boundary. `team-internal`
and `personal-local` are application metadata and do not make a public Git repository
private.

## Reporting

Do not open a public issue containing credentials, private source content, device
secrets, customer data, access tokens, or undisclosed vulnerabilities. Use the
repository owner's private security-reporting channel when available.

## Design rules

- External connector content is data-only and cannot grant instruction authority.
- Principal/source ACLs are applied before P6 ranking.
- Derived indexes, memory, graphs, traces, and connector caches are non-authoritative.
- High-risk write/promotion/merge/release capabilities remain fail-closed.
- Local ledgers and telemetry use private directories/files and reject symlinks.
- Raw queries/prompts/tasks are not persisted by P9 observability.
- Repository privacy is mandatory for any instance containing non-public engineering knowledge.
- Repository closure baseline requires a protected default branch; the stronger production-hardened
  profile additionally expects PR/status-check/conversation/force-push/deletion controls when the
  selected GitHub plan supports them. Never weaken the baseline merely to obtain terminal=true.
