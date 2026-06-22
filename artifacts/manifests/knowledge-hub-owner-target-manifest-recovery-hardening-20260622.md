# Knowledge Hub owner target and manifest recovery hardening 2026-06-22

## 结论

本轮继续推进终态治理，但不越过 owner 语义门禁。

- `knowledge-owner-gates.sh --validate-forms` 新增保守的 `owner_decision` / `target_decision` 成对兼容检查。
  - `reference-only` 只能搭配 `reference-only`。
  - `no-migration` 只能搭配 `no-migration`。
  - `rejected` 只能搭配 `no-migration`。
  - `archive-only` 只能搭配 `archive-only`。
  - 落地类 `owner_decision` 不能搭配 `reference-only` 或 `no-migration` target。
- `knowledge-index-plan.sh --section manifest` 文本模式同步显示 `profile_health`、`summary_source` 和 `evidence_source`，和 JSON 恢复视图保持一致。
- README、tools README 和 indexes README 增补中文说明，明确这些恢复字段是 report-only 质量提示，不是历史正文回填要求，也不是新的硬门禁。

本轮没有把 owner-ready Markdown 表反向生成完整矩阵，也没有新增结构化 `decision_target_pairs` 权威字段。原因是现有 worksheet 的 `target_candidates` 偏落地目标，部分 owner-ready package 的表格偏语义目标，二者层级尚未完全统一。当前只拦截字段分别合法但组合明显矛盾的表单。

## Owner 表单门禁

新增诊断 code：

- `owner-decision-target-mismatch`

该诊断只在 owner 人工填写的 JSONL 中两个字段都存在时触发。它不自动修复表单，不替 owner 选择目标，不关闭 gate，不进入 landing plan。

当前覆盖的负向回归：

- `owner-form-decision-target-pair-reference-only-project-path`
- `owner-form-decision-target-pair-no-migration-project-path`
- `owner-form-decision-target-pair-project-rule-reference-only`

这些场景证明：即使 `owner_decision` 和 `target_decision` 分别属于候选集合，只要组合语义明显冲突，`--validate-forms` 仍必须失败。

## Manifest 恢复视图

`knowledge-index-plan.sh --section manifest` 文本模式现在会输出：

- `profile_health` 分布。
- 每条 latest manifest 的 `profile_health`。
- 每条 latest manifest 的 `summary_source`。
- 每条 latest manifest 的 `evidence_source`。

这些字段只帮助中文开发人员恢复最新治理制品的摘要、证据和边界质量。`legacy-missing-profile`、`reference-only`、`missing-boundary` 等值是人工补强方向或历史例外提示，不要求批量回填历史正文。

## Evidence Index

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
|---|---:|---|---|---|---|
| `rtk bash -n tools/knowledge-owner-gates.sh` | 0 | 通过；owner gate helper 语法检查通过。 | `tools/knowledge-owner-gates.sh` | Tool | `knowledge-hub-owner-target-manifest-recovery-hardening-20260622` |
| `rtk bash -n tools/knowledge-index-plan.sh` | 0 | 通过；index planner 语法检查通过。 | `tools/knowledge-index-plan.sh` | Tool | `knowledge-hub-owner-target-manifest-recovery-hardening-20260622` |
| `rtk bash -n tools/knowledge-regression.sh` | 0 | 通过；regression helper 语法检查通过。 | `tools/knowledge-regression.sh` | Tool | `knowledge-hub-owner-target-manifest-recovery-hardening-20260622` |
| `rtk bash tools/knowledge-regression.sh --json --as-of 2026-06-22` | 0 | 通过；`status=pass`，新增 owner decision/target 成对兼容负向场景后回归总数为 98。 | `tools/knowledge-regression.sh` | Gate | `knowledge-regression` |
| `rtk bash tools/knowledge-index-plan.sh --section manifest` | 0 | 通过；文本恢复视图包含 `profile_health`、`summary_source` 和 `evidence_source`。 | `tools/knowledge-index-plan.sh` | Tool | `manifest-recovery-view` |
| `rtk bash tools/knowledge-check.sh --dry-run --json --diagnostics --as-of 2026-06-22` | 0 | 通过；`status=pass`，errors=0。 | `tools/knowledge-check.sh` | Gate | `knowledge-check` |
| `rtk bash tools/knowledge-final-gate.sh --json --as-of 2026-06-22` | 1 | 预期停在 owner-review；`automatic_governance.status=complete-except-owner-review`，唯一 blocker 仍是 7 个 `owner-gates-open`。 | `tools/knowledge-final-gate.sh` | Gate | `knowledge-final-gate` |

## 边界

- 不生成 owner decision。
- 不关闭 owner gate。
- 不把 owner-ready Markdown 表当作 owner decision。
- 不把 PCR02 project-specific 内容提升到 `domains/embedded/standards/`。
- 不修改 PCR02 源项目。
- 不复制 owner-gated source 正文。
- 不启用自动化写操作。
- 不写 `~/.codex/memories`。
