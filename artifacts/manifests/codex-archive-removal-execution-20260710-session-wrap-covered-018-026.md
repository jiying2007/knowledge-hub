# Codex archive session-wrap covered 删除执行批次 2026-07-10

## Scope

本批只删除 9 个已由 subagents 判定为 covered 或 provenance-only 的旧 `session-wrap` 正文。

授权 ID：`auth-20260710-codex-archive-delete-session-wrap-covered-018-026`

恢复锚点：`db07bd4839016d76f37218cd2b72857ed8575d48`

## 删除清单

| CARE | Old source | SHA256 | 覆盖目标 |
| --- | --- | --- | --- |
| `CARE-20260710-018` | `session-wrap/20260510-000000-diag-v4-hybrid-refcount-session-wrap.md` | `d7ff24f51dc48b4491f79b63d493ba44a39fc1f84d9ef8311d692af0360d352e` | `projects/pcr02/decisions/diag-v4-hybrid-refcount-discovery-spec.md` |
| `CARE-20260710-019` | `session-wrap/20260510-135300-session-wrap.md` | `d14df87fd0063ce1a26bab055cd003747c3149138fddecb9b1595c728152a271` | `domains/codex/archive/codex-archive/daily-summary/20260510-094820-codex-v2-knowledge-archive-summary.md` |
| `CARE-20260710-020` | `session-wrap/20260510-150728-session-wrap.md` | `b0ac3a275e97dc68cb32b24666e552bef2b5391c504bb43f094ce7983560f240` | current context-compress-handoff routing and old bwrap provenance |
| `CARE-20260710-021` | `session-wrap/20260511-104901-session-wrap.md` | `a77391f979bde0b4336c7793b7c2ce71453a3f903af8d5dc636d16a61711076a` | `artifacts/manifests/codex-token-efficiency-roadmap-coverage-20260710.md` |
| `CARE-20260710-022` | `session-wrap/20260511-132348-session-wrap.md` | `34e9e0b1c9304fe1b3d096cf6ffaead7fa114d25169cd6994e7e617ba7feb455` | `artifacts/manifests/codex-token-efficiency-roadmap-coverage-20260710.md` |
| `CARE-20260710-023` | `session-wrap/20260523-082158-wechat-absorption.md` | `19b73358583b2da99bcfa45f7889f5d9dfa663c07aa2b5c70280ffa65c6eee89` | `session-wrap/20260523-135801-wechat-all-cleared-handoff.md` retained as final anchor |
| `CARE-20260710-024` | `session-wrap/20260523-085953-wechat-p0-batches.md` | `9e39a34b0fb429f2c267c5386df0d861b6471d23b974c6f3943abc6646e3b9e5` | `session-wrap/20260523-135801-wechat-all-cleared-handoff.md` retained as final anchor |
| `CARE-20260710-025` | `session-wrap/20260523-101841-wechat-p0-context-handoff.md` | `e0236e7074fc1007892c6371710eae6e0b0824015d0d29e14917e6be3b22fb8b` | `session-wrap/20260523-135801-wechat-all-cleared-handoff.md` retained as final anchor |
| `CARE-20260710-026` | `session-wrap/20260523-112927-context-compress-handoff-wechat-p0-after-006.md` | `becd6fba63ce51c1f59ebb9da966cabcdad780981966ef4d8a6eed1ee08e0b54` | `session-wrap/20260523-135801-wechat-all-cleared-handoff.md` retained as final anchor |

## Boundaries

- 不删除 `session-wrap/20260523-135801-wechat-all-cleared-handoff.md`，它仍是 WeChat 中间批次的最终覆盖锚点，后续必须 extract-first 后才能删除。
- 不删除 promote-candidate 文件：PCR02 crash/core debug、llm_tools 三仓、GD32 固件/GD32 app boot、PCR02 GROS、Knowledge Base 独立仓、PCR02 SSC305 统一构建、HDI warning zero。
- 不写 `~/.codex/memories`。
- 不提升 active，不生成 owner decision，不改源项目，不 commit，不 push。
- 不整 topic 删除 `session-wrap`，不整 corpus 删除 `codex-archive`。

## Rollback

只允许从 `db07bd4839016d76f37218cd2b72857ed8575d48` 精确恢复本批 9 个 source path、本执行 manifest、`session-wrap/index.md`、`registry/authorizations.jsonl`、`registry/items.jsonl`、受影响 `indexes/by-*.md`、`CAEF/CARP/CAMR` 行。

禁止使用 `git reset --hard` 或覆盖其它未提交工作。

## Validation Plan

```bash
rtk jq -c . artifacts/manifests/codex-archive-removal-execution-20260710-session-wrap-covered-018-026.jsonl
rtk bash -lc "test ! -e domains/codex/archive/codex-archive/session-wrap/20260510-000000-diag-v4-hybrid-refcount-session-wrap.md && test ! -e domains/codex/archive/codex-archive/session-wrap/20260510-135300-session-wrap.md && test ! -e domains/codex/archive/codex-archive/session-wrap/20260510-150728-session-wrap.md && test ! -e domains/codex/archive/codex-archive/session-wrap/20260511-104901-session-wrap.md && test ! -e domains/codex/archive/codex-archive/session-wrap/20260511-132348-session-wrap.md && test ! -e domains/codex/archive/codex-archive/session-wrap/20260523-082158-wechat-absorption.md && test ! -e domains/codex/archive/codex-archive/session-wrap/20260523-085953-wechat-p0-batches.md && test ! -e domains/codex/archive/codex-archive/session-wrap/20260523-101841-wechat-p0-context-handoff.md && test ! -e domains/codex/archive/codex-archive/session-wrap/20260523-112927-context-compress-handoff-wechat-p0-after-006.md"
rtk bash tools/knowledge-search.sh "Diag V4 Hybrid RefCount"
rtk bash tools/knowledge-search.sh "Codex V2 context assets"
rtk bash tools/knowledge-search.sh "Usage TUI finalization"
rtk bash tools/knowledge-search.sh "Codex token efficiency roadmap"
rtk bash tools/knowledge-search.sh "WeChat intake fully cleared"
rtk bash tools/knowledge-check.sh --dry-run
rtk git diff --check
```
