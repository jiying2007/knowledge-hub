# Contributing

Changes must preserve the Knowledge Hub authority model and pass the repository
Engineering, Compliance, Restore, and Product Final Gate chain.

For runtime/platform changes:

1. Keep canonical Markdown + registry authoritative.
2. Put new runtime entrypoints under `tools/runtime/` unless a public wrapper is
   explicitly justified and added to the governed command-surface catalog.
3. Add deterministic positive and fail-closed negative tests.
4. Keep new Python modules within engineering budgets.
5. Do not silently weaken ACL, lifecycle, evidence, owner, or high-risk gates.
6. Retrieval/ranking changes require fresh evaluation evidence against a baseline.
7. Connector, memory, graph, and observability state must stay rebuildable/private
   unless a separate governed promotion flow writes canonical state.
