# Knowledge Hub terminal gate resilience 2026-06-20

## 结论

本批推进把终态门禁的非 owner 缺口继续收窄：

- 释放宿主可重建缓存后，恢复 `/tmp` 与根分区可用空间，`knowledge-regression` 可正常复制临时 fixture。
- `tools/knowledge-final-gate.sh` 将 regression 临时空间耗尽归类为 `environment` gap，避免误判为知识内容回归失败。
- `tools/knowledge-check.sh` 对 `registry/decisions.jsonl` 与 `indexes/by-decision.md` 增加 registry decision 强一致性门禁。
- `tools/knowledge-regression.sh` 从 39 个场景扩展到 43 个场景，新增 topic/decision 规划健康和 decision registry 负向门禁。

当前终态仍不是完全完成：7 个 PCR02 owner decision worksheets 仍保持 open，只能由 owner 人工签收。Codex 未生成 owner decision，未关闭 owner gate，未修改 PCR02 源项目 docs，未启用自动化，未写 memory。

## 本批变更

| Area | Change | Boundary |
|---|---|---|
| Final gate | 识别 `No space left on device`、`cannot create temp file`、`insufficient temp space` 等 regression 环境失败 | 只读分类，不自动清理环境 |
| Gap map | 环境型 blocker 输出 `gap_type=environment`，`codex_auto_can_complete=false` | 不把环境修复写成知识内容完成 |
| Decision index | 只对 `registry/decisions.jsonl` 的 `decision_id` 要求在 `indexes/by-decision.md` 中恰好出现一次 | 不把 owner worksheets 或 migration decisions 升级为强门禁 |
| Topic health | `knowledge-index-plan --section topic --json` 与 `registry/topics.json` 对齐 | 空 topic 允许存在，不作为硬失败 |
| Regression | 新增 4 个回归场景，helper manifest 自检更新为 43 个场景 | 仍只复制临时 fixture，不写真实仓库 |

## Evidence Index

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
|---|---:|---|---|---|---|
| `rtk df -h / /tmp ~/knowledge-hub` | 0 | 清理可重建缓存后，根分区恢复约 11G 可用空间 | Host environment | Environment | `knowledge-hub-terminal-gate-resilience-20260620` |
| `rtk bash tools/knowledge-check.sh --dry-run --json --diagnostics` | 0 | 通过；0 errors、0 warnings，含 registry decision / by-decision 强门禁 | `tools/knowledge-check.sh` | Tool | `knowledge-hub-terminal-gate-resilience-20260620` |
| `rtk bash tools/knowledge-regression.sh --json` | 0 | 通过；43 个回归场景全部 pass，新增 topic/decision 索引规划健康和 decision registry 负向门禁 | `tools/knowledge-regression.sh` | Tool | `knowledge-hub-terminal-gate-resilience-20260620` |
| `rtk bash tools/knowledge-final-gate.sh --json` | 1 | 预期返回 `needs-owner-review`；自动治理为 `complete-except-owner-review`，仅剩 7 个 owner gates open | `tools/knowledge-final-gate.sh` | Final Gate | `knowledge-hub-terminal-gate-resilience-20260620` |

## 决策

- 环境空间不足是执行环境问题，不是知识内容回归；final gate 必须单独暴露。
- `by-decision` 的强门禁只锁 registry decisions，避免把 owner decision worksheet、migration decision 和历史索引说明误判为必须同步的正式决策 registry。
- topic registry 目前用于规划和健康视图；空 topic 是允许状态，不应阻断终态。

## 边界

- 不修改 PCR02 源项目 docs。
- 不关闭任何 PCR02 owner gate。
- 不生成 owner decision。
- 不把 PCR02 project-specific 内容提升到 `domains/embedded/standards/`。
- 不启用自动化，不写 `~/.codex/memories`。
