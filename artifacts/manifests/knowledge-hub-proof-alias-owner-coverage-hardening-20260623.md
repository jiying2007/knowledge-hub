# Knowledge Hub proof alias、owner coverage 与最短路径口径加固 2026-06-23

## 结论

本轮继续压实 Knowledge Hub 终态治理中的非 owner 自动治理面，处理 3 个可由 Codex 完成、且不会关闭 owner gate 的切片。

- `knowledge-final-gate.sh` 新增稳定 JSON 字段 `proof_artifacts`，旧字段 `proof_artifacts_20260622` 仅作为兼容别名保留，两者内容保持一致。
- `knowledge-owner-gates.sh --validate-forms` 新增覆盖范围摘要，合法分批签收仍可通过，但会提示当前过滤范围内未提交的 open worksheet。
- `landing-plan` 和 `landing-audit` 透传 `landing_scope` 与 `remaining_open_after_this_batch`，避免人工把本批计划误读成该 owner/source 全部闭环。
- `docs/goals/knowledge-hub-final-state.md` 统一“5 条核心最短路径 + 搜索/复核辅助入口”口径，消除 5 条/6 项描述漂移。
- README、tools README 和 regression helper manifest 已同步新的字段说明与回归场景。

## 差距地图

| gap_id | gap_type | 影响 | 处理状态 |
|---|---|---|---|
| proof-artifacts-date-key-drift | cross-session-linking | 新会话可能继续绑定 `proof_artifacts_20260622`，误以为 proof 摘要只代表固定日期。 | applied |
| owner-validate-subset-coverage | owner-review | 批量 owner 表单可以合法只覆盖子集，但缺少 remaining open 提示会增加漏验风险。 | applied |
| manual-shortest-path-count-drift | Chinese-readability | 终态 goal 中 5 条核心路径和 6 项辅助入口口径混用，影响中文维护者恢复。 | applied |

## 证据

| 命令 | 结果 | 摘要 |
|---|---|---|
| `rtk bash -n tools/knowledge-owner-gates.sh` | pass | owner gate 工具语法通过。 |
| `rtk bash -n tools/knowledge-final-gate.sh` | pass | final gate 工具语法通过。 |
| `rtk bash -n tools/knowledge-regression.sh` | pass | regression 工具语法通过。 |
| `rtk git diff --check` | pass | 当前补丁无 whitespace / conflict marker 问题。 |
| `KNOWLEDGE_FINAL_GATE_INNER_REGRESSION=1 rtk bash tools/knowledge-final-gate.sh --json --as-of 2026-06-23` | owner-review expected | `proof_artifacts` 与 `proof_artifacts_20260622` 同时存在且内容一致，终态仍只剩 `owner-gates-open`。 |
| `rtk bash tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --validate-forms /tmp/kh-owner-partial-form-20260623.jsonl --landing-plan --landing-audit --json` | pass | 单条合法 owner form 在全 source 范围校验时 `coverage_status=partial`，剩余 6 条 open worksheet 进入 validation、landing plan 和 audit 提示。 |
| `rtk bash tools/knowledge-regression.sh --json --as-of 2026-06-23` | pass | 107 个回归场景全部通过；`final-proof-artifacts-stable-alias`、`owner-validate-forms-partial-coverage-warning` 和 `regression-manifest-coverage` 均通过。 |
| `rtk bash tools/knowledge-check.sh --dry-run --json --diagnostics --as-of 2026-06-23` | pass | 全仓一致性通过，errors=0，warnings=0。 |
| `rtk bash tools/knowledge-final-gate.sh --json --as-of 2026-06-23` | owner-review expected | `final_status=needs-owner-review`，`automatic_governance.status=complete-except-owner-review`，唯一 gap 为 `owner-gates-open`，proof artifacts expected_count=24。 |

## 边界

- 不生成 owner decision。
- 不填写 `reviewed_by`、`reviewed_at` 或 owner 签收字段。
- 不关闭 owner gate。
- 不修改 PCR02 源项目 docs、tools、knowledge、app_product_test、scratch 或 source tree。
- 不复制 owner-gated source 正文。
- 不把 PCR02 project-specific 内容提升到 `domains/embedded/standards/`。
- 不启用非 report-only 自动化。
- 不写 `~/.codex/memories`。

## 剩余状态

本轮不改变真实终态：非 owner 自动治理继续以 final gate 证明为准；7 个 `pcr02-project-docs` owner gate 仍需要真实 owner decision。Codex 只能降低签收和恢复成本，不能代签或关闭 gate。
