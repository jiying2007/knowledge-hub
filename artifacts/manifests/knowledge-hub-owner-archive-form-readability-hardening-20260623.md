# Knowledge Hub owner archive 表单与维护文案加固 2026-06-23

## 结论

本轮继续推进 Knowledge Hub 终态治理中的非 owner 自动治理面，处理 4 个互不冲突的维护切片。

- `knowledge-final-gate.sh` 的运行时维护入口摘要不再使用易漂移的“第七节”口径，改为指向 `docs/goals` 中列出的 8 类长期维护入口。
- `knowledge-owner-gates.sh --validate-forms` 允许 `archive-only` owner decision 搭配明确的 `/archive/` 目标路径，解决 worksheet 007 只有 archive 路径候选却无法合法填写的问题。
- `archive-only` 仍会拒绝 `validation/`、`decisions/`、`current/` 等非 archive 目标，避免把 session archive 或历史记录误落到非 archive 位置。
- `knowledge-owner-gates.sh` 顶层新增 `status_scope=tool-health`、`owner_review_status` 和 `owner_gate_status`，降低外部消费方把工具健康 `status=ok` 误读成 owner gate 已完成的风险。
- `.gitignore` 新增 `artifacts/manifests/*.local.jsonl`，并在 README / tools README 中说明 owner 表单草稿不登记 registry/index，不作为 landing artifact。
- `knowledge-regression.sh` 新增 3 个运行契约：final gate 维护入口文案不依赖章节号、archive-only 可使用 archive 路径、archive-only 拒绝非 archive 目标；现有 README 最短路径回归同步覆盖 `.local.jsonl` 防误提交规则。

## 差距地图

| gap_id | gap_type | 影响 | 处理状态 |
|---|---|---|---|
| final-gate-maintenance-entry-section-drift | Chinese-readability | final gate 运行时摘要引用“第七节”会让维护者跟随章节编号漂移。 | applied |
| owner-archive-only-target-compatibility | owner-review-recovery | worksheet 007 真实 owner 选择唯一 `archive-only` 时，原校验要求字面 target，导致无合法 archive path 填写路径。 | applied |
| owner-local-jsonl-draft-boundary | manual-maintenance | 推荐把临时 owner JSONL 放在 governed 目录，但未忽略会增加误提交和误登记风险。 | applied |
| owner-gates-status-scope-ambiguity | tooling | `knowledge-owner-gates.sh` 顶层 `status=ok` 只表示工具健康，容易被外部消费方误读为 owner gate 完成。 | applied |

## 证据

| 命令 | 结果 | 摘要 |
|---|---|---|
| `rtk bash -n tools/knowledge-owner-gates.sh` | pass | owner gate 工具语法通过。 |
| `rtk bash -n tools/knowledge-regression.sh` | pass | regression 工具语法通过。 |
| `rtk bash -n tools/knowledge-final-gate.sh` | pass | final gate 工具语法通过。 |
| `rtk bash tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --summary --json` | owner-review expected | 顶层 `status=ok`、`status_scope=tool-health`、`owner_review_status=needs-owner-review`、`owner_gate_status=owner-gates-open`。 |
| `rtk bash tools/knowledge-regression.sh --json --as-of 2026-06-23` | pass | 当次运行历史捕获：111 个回归场景全部通过；新增 final gate 文案和 archive-only 表单兼容回归；当前 live 回归数量以 `tools/knowledge-regression.sh --json` 输出为准。 |
| `rtk bash tools/knowledge-check.sh --dry-run --json --diagnostics --as-of 2026-06-23` | pass | 全仓一致性通过，errors=0，warnings=0。 |
| `rtk git diff --check` | pass | 当前补丁无 whitespace / conflict marker 问题。 |
| `rtk bash tools/knowledge-final-gate.sh --json --as-of 2026-06-23` | owner-review expected | `final_status=needs-owner-review`，非 owner 自动治理保持 `complete-except-owner-review`，唯一 gap 仍为 `owner-gates-open`。 |

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

本轮只降低真实 owner 后续签收的工具阻塞和误读风险，不改变 owner gate 语义状态。7 个 `pcr02-project-docs` owner gate 仍需真实 owner 人工决策；Codex 只能提供只读分派、校验和 no-write landing plan，不能代签或关闭 gate。
