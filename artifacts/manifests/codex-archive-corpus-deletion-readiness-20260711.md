# Codex archive corpus deletion readiness 2026-07-11

## 摘要

本记录在 final bodies 删除执行后检查 `domains/codex/archive/codex-archive` corpus 状态。

结论：旧 Codex archive 已无非 `index.md` / `README.md` 正文，但 corpus-level 目录删除仍需要单独授权和单独删除账本。本次不删除 corpus、topic 目录或 topic index。

结构化台账：`artifacts/manifests/codex-archive-corpus-deletion-readiness-20260711.jsonl`。

## Readiness

| Gate | Status | Evidence |
| --- | --- | --- |
| live body files | `clear-after-final-bodies-deletion` | `rtk rg --files domains/codex/archive/codex-archive` |
| topic indexes retained | `yes` | `research-notes/index.md`、`debug-notes/index.md`、`daily-summary/index.md`、`release-governance/index.md` 等均保留 |
| tombstone coverage | `yes` | `artifacts/manifests/codex-archive-removal-execution-20260711-final-bodies.jsonl` |
| corpus deletion authorization | `missing` | 本次用户目标要求给 readiness report，但不要自动删除整个 corpus |
| corpus deletion action | `not-applied` | 无目录级删除 |

## Remaining policy

- 后续如需删除整个 `domains/codex/archive/codex-archive` corpus，必须另建授权账本，精确列出待删除目录、保留/迁移的 index/tombstone 入口、rollback 方式和验证命令。
- 不得把本记录当作 corpus deletion authorization。
- 不得删除 `domains/codex/archive/codex-archive.ref.md` 或 Hub registry/index 中的历史 provenance。

## Validation Plan

```bash
rtk rg --files domains/codex/archive/codex-archive
rtk bash tools/knowledge-search.sh "Codex archive corpus deletion readiness"
rtk bash tools/knowledge-check.sh --dry-run
rtk git diff --check
```
