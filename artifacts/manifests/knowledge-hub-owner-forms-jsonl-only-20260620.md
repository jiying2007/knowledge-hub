# Knowledge Hub owner forms 纯 JSONL 输出（2026-06-20）

## 结论

`tools/knowledge-owner-gates.sh` 新增 `--forms-jsonl`，用于只输出 owner decision JSONL skeleton，每个 open worksheet 一行。

这个入口面向人工保存、脚本校验和后续 owner 回填前的低噪音复制场景。它和 `--forms` 的定位不同：`--forms` 保留人读说明、上下文和验证提示；`--forms-jsonl` 的 stdout 只允许出现 JSONL skeleton。

## 变更

- 新增参数：`--forms-jsonl`。
- `--forms-jsonl` 可与 `--source-id`、`--worksheet-id`、`--next-open`、`--status` 组合。
- `--forms-jsonl` 与 `--json`、`--summary`、`--forms`、`--checklist`、`--validate-forms`、`--landing-plan` 显式互斥。
- 输出复用 `make_decision_form`，避免 form 字段与既有 `--forms` / `--forms --json` 漂移。
- 新增 3 个回归场景：
  - `owner-forms-jsonl-single-output`
  - `owner-forms-jsonl-all-open-output`
  - `owner-forms-jsonl-conflict-json-mode`

## 边界

- 不生成 owner decision。
- 不关闭 owner gate。
- 不自动填 `owner_decision`、`source_sha256` 或 `source_size`。
- 不修改源项目 docs。
- 不写 registry、migration 或 index。
- 不迁移 owner-gated source 正文。
- 不把 PCR02 project-specific 内容提升到 `domains/embedded/standards/`。
- 不启用自动化。
- 不写 `~/.codex/memories`。

## Evidence Index

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
| --- | ---: | --- | --- | --- | --- |
| `rtk bash tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --worksheet-id pcr02-owner-decision-worksheet-001 --forms-jsonl` | 0 | 输出 1 行纯 JSONL skeleton；stdout 不含 Markdown 标题、说明或验证段落，owner 决策字段仍为空。 | `tools/knowledge-owner-gates.sh` | Tool | owner-forms-jsonl-only |
| `rtk bash tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --forms-jsonl` | 0 | 输出 7 行纯 JSONL skeleton，每条 open owner worksheet 一行。 | `tools/knowledge-owner-gates.sh` | Tool | owner-forms-jsonl-only |
| `rtk bash tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --forms-jsonl --json` | expected 2 | 互斥保护生效；拒绝把纯 JSONL 与包裹 JSON object 混用。 | `tools/knowledge-owner-gates.sh` | Tool | owner-forms-jsonl-only |
| `rtk bash tools/knowledge-regression.sh --json` | 0 | 通过；回归场景数更新为 27 个，包含纯 JSONL 单条、全量和冲突保护。 | `tools/knowledge-regression.sh` | Tool | owner-forms-jsonl-only |
| `rtk bash tools/knowledge-check.sh --dry-run --json --diagnostics` | 0 | 通过；0 errors、0 warnings，本 manifest、registry、migration 和索引登记一致。 | `tools/knowledge-check.sh` | Knowledge Hub | owner-forms-jsonl-only |
| `rtk bash tools/knowledge-final-gate.sh --json` | expected 1 | 终态门禁仍返回 `needs-owner-review`，因为 7 条 owner gate 尚未由 owner 人工签收；`knowledge-check` 与 `knowledge-regression` 均通过。 | `tools/knowledge-final-gate.sh` | Knowledge Hub | owner-forms-jsonl-only |

## Review

- owner：`leiwenjun`
- review_after：`2026-09-20`
- review_status：`owner-forms-jsonl-only-applied`
- 下一次复核内容：若 owner form 字段、互斥参数或 stdout 契约变化，需同步更新 README、tools README、回归场景和本 manifest。
