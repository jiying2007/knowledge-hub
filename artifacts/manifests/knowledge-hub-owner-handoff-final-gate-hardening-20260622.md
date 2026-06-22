# Knowledge Hub Owner Handoff and Final Gate Hardening 2026-06-22

## 摘要

本次收口面向终态目标中的 owner 人工瓶颈和 final gate 证明强度，压实四类可由 Codex 自动完成的治理切片：

- `owner_dispatch[]` 增加只读 `suggested_owner_packet`，把 summary、evidence-readiness、forms-jsonl、validate、landing-plan 和 landing-audit 排成 owner handoff 顺序，并给出建议本地临时 JSONL 路径。
- owner landing plan / landing audit 的 `required_manual_files` 改为从实际 worksheet row 动态收集，不再把 worksheet 文件固定写死为 PCR02 当前文件。
- final gate 的 Level 3 registered sources audit 直接暴露 `source_coverage_selection`，并新增非 owner strict blocker 负向回归，证明非 owner blocker 不会被包装成 `needs-owner-review`；内层 final-gate 回归使用递归保护，避免 regression 自测反复调用自身。
- 中文长期资产字段收敛：owner worksheet 模板明确 `owner_required` / `owner_candidate` 为工具路由字段，migration 示例使用 `notes_zh`，命名边界优先 `summary_zh` / `title_zh`。

## 改动范围

| 文件 | 改动 |
|---|---|
| `tools/knowledge-owner-gates.sh` | `owner_dispatch[]` 增加 `suggested_owner_packet`；landing plan/audit 动态输出 worksheet required files。 |
| `tools/knowledge-status.sh` | `owner_gates.owner_dispatch[]` 同步增加 status 侧 `suggested_owner_packet`，便于跨会话恢复 owner 领取顺序。 |
| `tools/knowledge-final-gate.sh` | `final_state_audit.level3_registered_sources` 增加 `source_coverage_selection` 和 `check_source_coverage_selection`。 |
| `tools/knowledge-regression.sh` | 增加 `final-gate-strict-status-nonowner-blocker`；扩展 owner handoff、dynamic worksheet required files 和 final gate source coverage selection 断言。 |
| `README.md`、`tools/README.md` | 说明 owner handoff packet 和 README/templates/indexes/tools 的 canonical 分工。 |
| `templates/owner-decision-worksheet.md` | 增加 `owner_required` / `owner_candidate`，说明 `decision_owner` 只是人读别名或兼容字段。 |
| `governance/migration-policy.md`、`governance/naming-boundaries.md` | 示例和字段说明收敛到 `notes_zh`、`summary_zh` / `title_zh`。 |
| `artifacts/manifests/knowledge-hub-governance-regression-helper-20260619.md` | 回归场景计数更新为 80，并登记新增 final gate 负向场景。 |

## 边界

- 不生成 owner decision。
- 不关闭任何 owner gate。
- 不修改 PCR02 源项目文件。
- 不复制 owner-gated source 正文。
- 不提升 PCR02 project-specific 内容到 `domains/embedded/standards/`。
- 不启用自动化写操作。
- 不写 `~/.codex/memories`。

## 验证计划

```bash
rtk bash -n tools/knowledge-owner-gates.sh
rtk bash -n tools/knowledge-status.sh
rtk bash -n tools/knowledge-final-gate.sh
rtk bash -n tools/knowledge-regression.sh
rtk bash tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --owner project-owner --summary --json
rtk bash tools/knowledge-status.sh --json --as-of 2026-06-22
rtk bash tools/knowledge-check.sh --dry-run --json --diagnostics --as-of 2026-06-22
rtk bash tools/knowledge-regression.sh --as-of 2026-06-22
rtk git diff --check
rtk bash tools/knowledge-final-gate.sh --json --as-of 2026-06-22
```

## 当前阻塞

本轮只降低 owner 人工签收的领取和落地摩擦，并提高 final gate 的证明强度。终态仍应停在 `needs-owner-review`，且唯一 blocker 应继续是 `owner-gates-open`；7 个 PCR02 owner gate 不能由 Codex 代签。
