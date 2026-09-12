# Knowledge Hub Terminal Closure

Knowledge Hub uses two deliberately different gates.

- `quality` proves engineering qualification, compatibility, deterministic compliance, recovery, and product readiness assessment. A green run is not a terminal product claim.
- `terminal-closure` is an explicit fail-closed workflow. It requires the product snapshot to report `status=pass` and `terminal=true`, all required external closure gaps to be closed, bounded historical compatibility debt not to grow, and branch GC to be closed.

## Terminal claim rule

A terminal claim is valid only when `tools.codex_assets.knowledge_hub.terminal_closure_cli` returns exit code 0 for the exact remote revision under review. Exit code 2 means readable evidence exists but one or more terminal axes remain open.

Synthetic fixtures, local-only checks, or a green `quality` workflow cannot close repository administration, real provider pilot, official protocol conformance, production signing identity, owner evidence, or adoption requirements.

## Historical debt

The current legacy module and artifact-reference counts are frozen upper bounds, not a declaration that the debt is desirable. New growth is forbidden. Quarterly debt reduction continues independently until the compatibility surface can be retired or the remaining historical references are explicitly accepted as immutable exceptions.

## Branch lifecycle

Completed implementation branches must be deleted after their exact-head evidence is retained, unless an owner and expiry are recorded. Active architecture branches may not remain indefinitely after their contract has been absorbed by `master`.
