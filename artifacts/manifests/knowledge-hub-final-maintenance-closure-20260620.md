# Knowledge Hub final maintenance closure 2026-06-20

## 结论

本批次根据并行 subagent 审查结果，压实 Knowledge Hub 终态维护入口。变更只覆盖 read-only 工具、人工维护文档、回归清单和 registry/index 登记；不生成 owner decision，不关闭 PCR02 owner gate，不修改 PCR02 源项目 docs，不启用自动化，不写 `~/.codex/memories`。

当前预期终态仍是 `needs-owner-review`：非 owner 自动治理门禁应通过，剩余语义 blocker 仍是 7 个 `owner-gates-open`。

## 已落地项

| ID | 范围 | 处理结果 |
|---|---|---|
| final-gate-diff-check-evidence | `tools/knowledge-final-gate.sh`、`tools/knowledge-regression.sh` | `rtk git diff --check` 进入 final gate JSON checks、blocker 判断和回归断言，避免终态检查遗漏 whitespace/conflict-marker drift。 |
| owner-forms-jsonl-target-candidates | `tools/knowledge-owner-gates.sh`、`tools/knowledge-regression.sh` | owner decision JSONL skeleton 增加只读 `target_candidates`，owner 人工签收前能看到候选落点边界。 |
| status-text-owner-summary-commands | `tools/knowledge-status.sh`、`tools/knowledge-regression.sh` | 文本 dashboard 增加 all-open/by-owner owner summary commands，避免人工分派只能从 JSON 恢复命令。 |
| manual-offline-shortest-path-docs | `README.md`、`tools/README.md`、`templates/README.md` | 澄清 source owner 必须登记在 `registry/owners.json`、优先使用稳定只读 `--check`、离线人工默认 `reviewing/manual-entry-pending-review`，以及 `registry/migrations.jsonl` 只在迁移、引用或归档时补齐。 |
| regression-manifest-sync | `artifacts/manifests/knowledge-hub-governance-regression-helper-20260619.md` | 回归 helper manifest 从 33 项同步到 36 项，覆盖新增 status 文本命令、final gate 默认 regression 路径和离线人工文档默认值。 |

## Deferred

| 项 | 原因 | 后续建议 |
|---|---|---|
| owner-ready package 中 cwd-relative `rtk bash tools/...` 命令 | 已有 README 和 tools README 提供稳定 `~/knowledge-hub/tools/...` 入口；批量改历史 owner-ready package 容易造成低价值 churn。 | 下次 owner package 模板刷新时统一替换。 |
| `indexes/by-source.md` 增加 project/target domain 列 | 需要同步 planner/check 预期，表结构变更风险高于本批次收益。 | 独立切片评估索引 schema。 |
| `indexes/by-project.md` 最新 governance anchor 密度 | 当前 by-topic/by-owner/by-status 已覆盖，本批次只追加直接相关入口。 | 后续做项目索引可读性专项。 |

## Evidence Index

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
|---|---:|---|---|---|---|
| `rtk git diff --check` | 0 | 通过；无 whitespace/conflict-marker drift。 | `tools/knowledge-final-gate.sh` | Tool | `knowledge-hub-final-maintenance-closure-20260620` |
| `rtk bash tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --worksheet-id pcr02-owner-decision-worksheet-001 --forms-jsonl` | 0 | 通过；JSONL skeleton 包含 `target_candidates`，owner 决策字段仍为空。 | `tools/knowledge-owner-gates.sh` | Tool | `knowledge-hub-final-maintenance-closure-20260620` |
| `rtk bash tools/knowledge-status.sh` | 0 | 通过；文本 dashboard 输出 owner summary commands、owner forms-jsonl commands 和 final gate command。 | `tools/knowledge-status.sh` | Tool | `knowledge-hub-final-maintenance-closure-20260620` |
| `rtk bash tools/knowledge-check.sh --dry-run --json --diagnostics` | 0 | 通过；0 errors、0 warnings。 | `tools/knowledge-check.sh` | Gate | `knowledge-hub-final-maintenance-closure-20260620` |
| `rtk bash tools/knowledge-regression.sh --json` | 0 | 通过；36 个回归场景全部 pass，包含 target candidates、status 文本命令和 final gate 默认 regression 路径。 | `tools/knowledge-regression.sh` | Regression | `knowledge-hub-final-maintenance-closure-20260620` |
| `rtk bash tools/knowledge-final-gate.sh --json` | 1 | 预期非零；`final_status=needs-owner-review`，`automatic_governance.status=complete-except-owner-review`，核心检查通过，唯一 blocker 为 7 个 owner gates。 | `tools/knowledge-final-gate.sh` | Final Gate | `knowledge-hub-final-maintenance-closure-20260620` |

## 边界

- 不生成 owner decision。
- 不关闭 owner gate。
- 不复制或修改 PCR02 源项目 docs。
- 不把 PCR02 project-specific 内容提升到 `domains/embedded/standards/`。
- 不启用自动化；自动化仍默认 `report-only`。
- 不写 `~/.codex/memories`。
