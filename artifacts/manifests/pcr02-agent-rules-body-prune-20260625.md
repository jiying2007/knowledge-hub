# PCR02 AGENTS 正文剪枝账本

本账本记录 2026-06-25 对 PCR02 旧迁移正文层中历史 `AGENTS.md` 正文副本的终态剪枝。

## 结论

- 源项目仍需要的本地 Codex 运行规则，由对应源码独立仓 Git 管理。
- Knowledge Hub 不再把历史 `AGENTS.md` 正文副本作为规则来源、知识正文入口或新增归档入口。
- Hub 仅保留 `pcr02-agent-rules-body-prune-20260625.jsonl` 中的路径、source_id、sha256、剪枝状态和理由，作为 hard migration 的 hash/provenance 证据。

## 剪枝范围

- `pcr02-module-agent-rules` 历史 `AGENTS.md` 正文副本
- `pcr02-project-docs` 历史 `AGENTS.md` 正文副本
- `pcr02-project-knowledge` 历史 `AGENTS.md` 正文副本
- `pcr02-project-tools` 历史 `AGENTS.md` 正文副本
- `pcr02-project-root-artifacts` 历史 `AGENTS.md` 正文副本
- `pcr02-product-test` 历史 `AGENTS.md` 正文副本

## 保留范围

- 非 `AGENTS.md` 的 PCR02 历史文档、runbook、计划、报告和工程归档仍按 `projects/pcr02/archive/` 边界保留。
- `artifacts/manifests/source-coverage-closeout-*.jsonl` 保留原始迁移事实；本账本只声明后续正文剪枝状态。

## 验证

- `rtk bash tools/knowledge-source-control.sh --dry-run --json --as-of 2026-06-25`
- `rtk bash tools/knowledge-check.sh --dry-run --json --diagnostics --as-of 2026-06-25`
- `rtk bash tools/knowledge-final-gate.sh --as-of 2026-06-25 --json --final-profile max-body`
