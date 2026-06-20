# Knowledge Hub final gate gap map 2026-06-20

## 结论

本轮把 `knowledge-final-gate.sh` 的终态判定从“可由人推导”压实为“可由 JSON 直接消费”：

- 新增 `automatic_governance` 顶层字段，用于区分 `complete`、`complete-except-owner-review` 和 `needs-fix`。
- 新增 `gap_map` 顶层字段，把 blocker 映射为可审计 gap 条目，包含 `gap_id`、`gap_type`、`source_id`、`evidence`、影响、是否可由 Codex 自动完成、是否需要 owner decision、修复动作、写入范围、验证命令和状态。
- Markdown 输出增加 `automatic_governance` 摘要和 `Gap Map` 段落。
- 回归场景 `final-gate-owner-review-blocker` 增加 automatic governance 与 owner gap map 断言。

当前自动治理状态为 `complete-except-owner-review`：`knowledge-check` 与 `knowledge-regression` 通过，`knowledge-status --strict` 只剩 `owner-gates-open`，7 个 owner gate 仍需人工 owner decision。该状态不代表 owner gate 已关闭，也不允许 Codex 代签。

## 问题地图

| ID | Finding | Severity | Evidence | Action |
|---|---|---:|---|---|
| GAP-FINAL-GATE-AUTO-STATUS | final gate 原先需要调用方自行组合 `checks` 和 `blockers` 才能判断自动治理是否只剩 owner review | P1 | `tools/knowledge-final-gate.sh --json` | 增加 `automatic_governance` |
| GAP-FINAL-GATE-GAP-MAP | goal 要求维护终态差距地图，但 final gate 没有结构化 gap map 输出 | P1 | `docs/goals/knowledge-hub-final-state.md` | 增加 `gap_map` |
| GAP-REGRESSION-FINAL-STATE | automatic governance / gap map 字段缺少回归保护 | P1 | `tools/knowledge-regression.sh` | 强化 `final-gate-owner-review-blocker` 断言 |
| GAP-DOC-DISCOVERY | 工具契约变化后 README/tools README 缺少新字段说明 | P2 | `README.md`、`tools/README.md` | 补充 `automatic_governance.status` 和 `gap_map` 说明 |

## 变更范围

| 文件 | 类型 | 说明 |
|---|---|---|
| `tools/knowledge-final-gate.sh` | 工具契约 | 新增 `automatic_governance` 和 `gap_map` JSON 字段；Markdown 输出增加 Gap Map |
| `tools/knowledge-regression.sh` | 回归 | 强化 final gate owner blocker 场景，断言 automatic governance 和 gap map |
| `README.md` | 文档 | 终态检查路径说明 `complete-except-owner-review` |
| `tools/README.md` | 文档 | 工具说明和示例说明 final gate 新字段 |

## Evidence Index

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
|---|---:|---|---|---|---|
| `KNOWLEDGE_FINAL_GATE_SKIP_REGRESSION=1 rtk bash tools/knowledge-final-gate.sh --json` | 1 | 通过自检模式；`final_status=needs-owner-review`，`automatic_governance.status=complete-except-owner-review`，`gap_map` 仅含 `owner-gates-open` | `tools/knowledge-final-gate.sh` | Tool | `knowledge-hub-final-gate-gap-map-20260620` |
| `rtk bash tools/knowledge-regression.sh --json` | 0 | 通过；33 个回归场景全部 pass，覆盖 automatic governance 和 owner gap map 断言 | `tools/knowledge-regression.sh` | Tool | `knowledge-hub-final-gate-gap-map-20260620` |
| `rtk bash tools/knowledge-check.sh --dry-run --json --diagnostics` | 0 | 通过；0 errors、0 warnings | `tools/knowledge-check.sh` | Gate | `knowledge-hub-final-gate-gap-map-20260620` |
| `rtk bash tools/knowledge-final-gate.sh --json` | 1 | 预期阻塞；`final_status=needs-owner-review`，`automatic_governance.status=complete-except-owner-review`，唯一 gap/blocker 为 7 个 open owner gate | `tools/knowledge-final-gate.sh` | Gate | `knowledge-hub-final-gate-gap-map-20260620` |

## 边界

- 不修改 PCR02 源项目 docs、tools、knowledge、app_product_test、scratch 或源码树。
- 不生成 owner decision，不关闭 owner gate，不把 owner-gated 内容设为 active。
- 不启用自动化写操作，不写 `~/.codex/memories`。
- 不把 PCR02 project-specific 内容提升到 `domains/embedded/standards/`。
- `automatic_governance.complete=true` 只表示 Codex 自动治理门禁闭环；人工 owner decision 仍是 open blocker。
