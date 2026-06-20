# Knowledge Hub final state audit summary 2026-06-20

## 结论

本轮在 `knowledge-final-gate.sh` 中新增 `final_state_audit`，把终态 Level 1 / Level 2 / Level 3 摘要直接放进 final gate JSON：

- Level 1 `level1_pcr02_docs`：PCR02 docs 控制面状态。当前为 `complete-except-owner-review`，表示 docs 控制面已闭合，但 7 个 owner-gated docs 仍需人工 owner decision。
- Level 2 `level2_pcr02_candidate_sources`：PCR02 docs 外 7 个关键 candidate source 的登记和 coverage 状态。当前为 `complete`。
- Level 3 `level3_registered_sources`：`registry/sources.json` 中全部 registered source 的最新 coverage 状态。当前为 `complete`。
- 每层摘要都带 `evidence_refs`，用于回溯到 source coverage、owner worksheet、owner intake、registry 或 check 命令；不携带 owner decision 正文。

该摘要只读、只做审计，不生成 owner decision，不关闭 owner gate，不把 `complete-except-owner-review` 写成 active 或 pass。

## 问题地图

| ID | Finding | Severity | Evidence | Action |
|---|---|---:|---|---|
| GAP-FINAL-STATE-AUDIT-SUMMARY | final gate 能证明门禁状态，但不能直接输出带证据引用的 Level 1/2/3 摘要 | P1 | `docs/goals/knowledge-hub-final-state.md` | 增加 `final_state_audit` 和 `evidence_refs` |
| GAP-FINAL-STATE-AUDIT-REGRESSION | Level 1/2/3 摘要字段缺少回归保护 | P1 | `tools/knowledge-regression.sh` | 强化 `final-gate-owner-review-blocker` |
| GAP-FINAL-STATE-AUDIT-DOCS | 工具契约变化后 README/tools README 缺少新字段说明 | P2 | `README.md`、`tools/README.md` | 补充 `final_state_audit` 说明 |

## 变更范围

| 文件 | 类型 | 说明 |
|---|---|---|
| `tools/knowledge-final-gate.sh` | 工具契约 | 新增 `final_state_audit` JSON 字段和 Markdown 摘要 |
| `tools/knowledge-regression.sh` | 回归 | 断言 Level 1/2/3 当前摘要状态、source 数量和 owner gate 边界 |
| `README.md` | 文档 | 终态检查路径补充 `final_state_audit` |
| `tools/README.md` | 文档 | final gate 工具契约补充 `final_state_audit` |

## Evidence Index

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
|---|---:|---|---|---|---|
| `KNOWLEDGE_FINAL_GATE_SKIP_REGRESSION=1 rtk bash tools/knowledge-final-gate.sh --json` | 1 | 通过自检模式；`final_state_audit.level1_pcr02_docs.status=complete-except-owner-review`，Level 2/3 均为 `complete` | `tools/knowledge-final-gate.sh` | Tool | `knowledge-hub-final-state-audit-summary-20260620` |
| `rtk bash tools/knowledge-regression.sh --json` | 0 | 通过；33 个回归场景全部 pass，覆盖 Level 1/2/3 摘要断言 | `tools/knowledge-regression.sh` | Tool | `knowledge-hub-final-state-audit-summary-20260620` |
| `rtk bash tools/knowledge-check.sh --dry-run --json --diagnostics` | 0 | 通过；0 errors、0 warnings | `tools/knowledge-check.sh` | Gate | `knowledge-hub-final-state-audit-summary-20260620` |
| `rtk bash tools/knowledge-final-gate.sh --json` | 1 | 预期阻塞；`final_status=needs-owner-review`，`automatic_governance.status=complete-except-owner-review`，`final_state_audit` 显示 Level 1 only owner-review pending、Level 2/3 complete | `tools/knowledge-final-gate.sh` | Gate | `knowledge-hub-final-state-audit-summary-20260620` |

## 边界

- `final_state_audit` 是审计摘要，不是 owner decision。
- Level 1 的 `complete-except-owner-review` 不关闭 owner gate，不允许复制 owner-gated 正文，不允许 active。
- 不修改 PCR02 源项目文件，不写 memory，不启用自动化写操作。
