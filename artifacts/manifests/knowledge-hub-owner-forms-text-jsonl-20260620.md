# Knowledge Hub owner forms 文本 JSONL 输出（2026-06-20）

## 结论

`tools/knowledge-owner-gates.sh --forms` 的非 JSON 输出现在会直接打印可复制的 owner decision JSONL skeleton。

这解决了一个人工维护瓶颈：此前文本模式只有标题和说明，真正的表单正文只存在于 `--json` 输出的 `decision_forms` 字段中。维护者需要在较大的 JSON 结构里提取表单，容易漏字段、复制错层级或把上下文误当作已签收事实。

## 变更

- `--forms` 文本模式在 `## Owner Decision JSONL Skeletons` 下逐行打印紧凑 JSON。
- 每个 open worksheet 对应 1 行 JSONL skeleton。
- JSONL skeleton 仍然只是人工填写草稿：
  - 不自动填 `owner_decision`。
  - 不自动填 `source_sha256/source_size`。
  - 不关闭 owner gate。
  - 不写 registry、migration 或 index。
  - 不提升 active。

## 边界

- 不生成 owner decision。
- 不关闭 owner gate。
- 不修改源项目 docs。
- 不迁移 owner-gated source 正文。
- 不把 PCR02 project-specific 内容提升到 `domains/embedded/standards/`。
- 不启用自动化。
- 不写 `~/.codex/memories`。

## Evidence Index

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
| --- | ---: | --- | --- | --- | --- |
| `rtk bash tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --worksheet-id pcr02-owner-decision-worksheet-001 --forms` | 0 | 文本模式输出 1 条可复制 JSONL skeleton，包含 `worksheet_id`、`source_path`、`owner_decision` 和 `observed_source_identity`。 | `tools/knowledge-owner-gates.sh` | Tool | owner-forms-text-jsonl |
| `rtk bash tools/knowledge-regression.sh --json` | 0 | 通过；新增回归 `owner-forms-text-jsonl-output` 通过，回归总数为 24 个。 | `tools/knowledge-regression.sh` | Tool | owner-forms-text-jsonl |
| `rtk bash tools/knowledge-check.sh --dry-run --json --diagnostics` | 0 | 通过；0 errors、0 warnings，本 manifest、registry、migration 和索引登记一致。 | `tools/knowledge-check.sh` | Knowledge Hub | owner-forms-text-jsonl |
| `rtk bash tools/knowledge-final-gate.sh --json` | expected 1 | 终态门禁仍返回 `needs-owner-review`，因为 7 条 owner gate 尚未由 owner 人工签收；`knowledge-check` 与 `knowledge-regression` 均通过。 | `tools/knowledge-final-gate.sh` | Knowledge Hub | owner-forms-text-jsonl |

## Review

- owner：`leiwenjun`
- review_after：`2026-09-20`
- review_status：`owner-forms-text-jsonl-applied`
- 下一次复核内容：若 owner form 字段、上下文或 `--forms` 输出契约变化，需同步更新 README、tools README、回归场景和本 manifest。
