# Knowledge Hub Owner Decision Forms 2026-06-19

## 目标

为 owner-gated 条目生成只读、可复制的 owner decision JSONL 填报骨架，降低人工闭环 7 个 PCR02 owner gates 的成本，同时不替 owner 做任何决策。form 骨架现在同时携带 owner 问题、当前状态、默认状态、允许状态、必填字段、硬门禁和当前源文件身份只读上下文，避免离线复制后丢失复核背景。

## 问题地图

| ID | 问题 | 风险 | 处理 |
| --- | --- | --- | --- |
| ODF-001 | owner decision worksheet 的必填字段较多，人工需要从多个 manifest 中拼字段。 | owner 填报成本高，容易漏字段或漏证据。 | `knowledge-owner-gates.sh --forms` 输出每个 open row 的完整 JSONL 骨架。 |
| ODF-002 | 工具生成骨架可能被误解为 owner 决策。 | 未 review 的骨架可能被当作已闭环事实。 | 骨架含 `notes_zh`，并明确不写文件、不关闭门禁、不提升 active。 |
| ODF-003 | 文本看板默认只展示部分 required fields，适合扫描但不适合直接填报。 | owner 可能遗漏后续必填字段。 | `--forms` 使用 JSON 数据中的完整 `required_owner_fields` 生成字段。 |
| ODF-004 | form 早期只包含填写字段和 must-not，未携带 owner intake 中的中文问题、默认状态和硬门禁。 | owner 或 AI 只复制单条 JSONL 时，可能脱离 gate 背景理解决策。 | form 中加入 `status`、`worksheet_status`、`owner_question_zh`、`default_state`、`allowed_next_status`、`required_owner_fields`、`hard_gate_summary` 和 `hard_gate` 只读字段。 |
| ODF-005 | form 要求 owner 填写 `source_sha256` 和 `source_size`，但过去没有当前源文件身份提示。 | owner 人工另跑 hash/size 命令时可能复制错，或误用过期 preflight。 | form 中加入 `observed_source_identity` 只读字段；`source_sha256` / `source_size` 仍保持空值，等待 owner 复核后填写。 |

## 决策

- 新增参数：`rtk bash tools/knowledge-owner-gates.sh --forms`。
- 可组合：`--source-id pcr02-project-docs --forms`。
- JSON 模式中增加 `decision_forms`，便于 AI 或人工工具读取。
- `decision_forms` 携带只读 owner context，但这些字段不能替代 owner 决策或证据。
- `observed_source_identity` 是当前源文件身份提示，不自动填充 owner 必填字段。
- 默认看板语义不变；当前 PCR02 owner gate 看板返回 7 open、0 active exposure。

## 非目标

- 不生成 owner 决策结果。
- 不写 worksheet、registry、index 或 memory。
- 不关闭 owner gate。
- 不迁移 owner-gated 正文。
- 不修改源项目 docs。
- 不启用自动化。

## Evidence Index

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
| --- | --- | --- | --- | --- | --- |
| `rtk bash tools/knowledge-owner-gates.sh --source-id pcr02-project-docs` | 0 | 默认 owner gate 看板语义保持不变，仍显示 7 open、0 active exposure。 | `tools/knowledge-owner-gates.sh` | Knowledge Hub | owner-decision-forms |
| `rtk bash tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --forms` | 0 | 输出 7 个 copyable JSONL owner decision skeleton。 | `tools/knowledge-owner-gates.sh` | Owner review | owner-decision-forms |
| `rtk bash tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --forms --json` | 0 | JSON 输出包含 `decision_forms`，数量为 7，且 `row_count=7`、`open_count=7`。 | `tools/knowledge-owner-gates.sh` | Owner review | owner-decision-forms |
| `rtk bash tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --worksheet-id pcr02-owner-decision-worksheet-001 --forms --json` | 0 | 单条 form 携带 owner 中文问题、当前状态、默认状态、允许状态、必填字段和硬门禁只读上下文。 | `tools/knowledge-owner-gates.sh` | Owner review | owner-decision-forms |
| `rtk bash tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --next-open --forms --json` | 0 | 单条 form 携带 `observed_source_identity.identity_status=match`，但 `source_sha256` / `source_size` 仍为空，等待 owner 填写。 | `tools/knowledge-owner-gates.sh` | Owner review | owner-decision-forms |
| `rtk bash tools/knowledge-owner-gates.sh --help` | 0 | help 展示 `--forms` 参数。 | `tools/knowledge-owner-gates.sh` | Tool smoke | owner-decision-forms |
| `rtk bash tools/knowledge-check.sh --dry-run --json --diagnostics` | 0 | 新增 owner decision forms 后全仓门禁应通过。 | `tools/knowledge-check.sh` | Knowledge Hub | owner-decision-forms |
| `rtk bash tools/knowledge-search.sh owner-decision-forms-applied --json` | 0 | 本制品应可检索，命中 registry、status index 和本 manifest。 | `registry/items.jsonl`、`indexes/by-status.md`、本 manifest | Knowledge Hub | owner-decision-forms |

## Review

- owner：`leiwenjun`
- review_after：`2026-09-19`
- review_status：`owner-decision-forms-applied`
- 下一次复核内容：若 owner worksheet 字段或状态判定变化，同步 `decision_forms` 骨架字段。
