# Knowledge Hub final state goal 2026-06-20

## 结论

`docs/goals/knowledge-hub-final-state.md` 是 Knowledge Hub 终态治理的长期目标规格。它定义了 PCR02 docs、PCR02 关键资料源、registered sources、owner-gated 两阶段流程、人工离线维护、跨会话恢复、跨项目关联、subagents 使用和每轮验证提交要求。

本登记只把目标规格纳入 Knowledge Hub 治理面，便于新会话恢复和长期审计；它不表示终态已经完成。

## 终态差距地图

| gap_id | gap_type | source_id | evidence | 当前影响 | 自动完成 | owner decision | 本轮动作 | 状态 |
|---|---|---|---|---|---|---|---|---|
| FSG-001 | cross-session-linking | none | `docs/goals/knowledge-hub-final-state.md` 未登记 | 新会话只能依赖未跟踪目标文档，终态规格不可被 `knowledge-check --explain` 解释 | yes | no | 登记目标规格为 governance item，允许 `docs/goals/` 作为 governance control-plane path | applied |
| FSG-002 | regression | none | `tools/knowledge-regression.sh` 原本没有 governance goal path 覆盖 | 后续 schema 变更可能再次拒绝目标规格路径 | yes | no | 新增 `governance-goal-path-allowed` 回归 | applied |
| FSG-003 | owner-review | pcr02-project-docs | `tools/knowledge-final-gate.sh --json` 返回 `needs-owner-review`，blocker 为 `owner-gates-open count=7` | PCR02 owner-gated docs 不能自动迁移或 active | no | yes | 保持 owner gate open，仅继续降低人工签收成本 | pending-human-owner |
| FSG-004 | source-coverage | pcr02 candidate sources | 目标文档列出 tools、knowledge、app_product_test、scratch、root artifacts、module AGENTS、agent config | Level 2 仍需逐 source coverage | partly | maybe | 后续切片继续 classify-first/source coverage，不改源项目 | pending |

## 边界

- 不修改源项目 docs、tools、knowledge、app_product_test、scratch 或源码树。
- 不生成 owner decision，不关闭 owner gate。
- 不写 `~/.codex/memories`。
- 不启用非 report-only 自动化。
- 不提升 PCR02 project-specific 内容到 `domains/embedded/standards/`。

## Evidence Index

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
|---|---:|---|---|---|---|
| `rtk bash tools/knowledge-check.sh --dry-run --json --explain knowledge-hub-final-state-goal-20260620` | 0 | 目标规格 registry item 可解释，路径 `docs/goals/knowledge-hub-final-state.md` 存在 | `tools/knowledge-check.sh` | Knowledge Hub | `knowledge-hub-final-state-goal-20260620` |
| `rtk bash tools/knowledge-regression.sh --json` | 0 | 29 个回归场景通过，包含 `governance-goal-path-allowed` | `tools/knowledge-regression.sh` | Regression | `knowledge-hub-final-state-goal-20260620` |
| `rtk bash tools/knowledge-final-gate.sh --json` | expected 1 | 仍返回 `needs-owner-review`，唯一 blocker 是 7 条 owner gate 未签收 | `tools/knowledge-final-gate.sh` | Final Gate | `knowledge-hub-final-state-goal-20260620` |

## 维护

- owner：`leiwenjun`
- review_after：`2026-09-20`
- review_status：`final-state-goal-registered`
- 下一步：继续按目标文档的 gap map 批量处理 PCR02 candidate sources 和 owner 签收降阻切片。
