# Knowledge Hub owner form context 2026-06-19

## 结论

`tools/knowledge-owner-gates.sh --forms` 已补充 owner decision form 的只读上下文，避免人工只复制 form JSONL 时丢失 owner 中文问题、当前状态、默认状态、允许状态、必填字段和硬门禁信息。

## 问题地图

| ID | 问题 | 风险 | 处理 |
|---|---|---|---|
| OFC-001 | `rows` 和 `owner_checklists` 已包含 `owner_question_zh`、`default_state`、`allowed_next_status`、`hard_gate_summary`、`hard_gate`，但 `decision_forms` 只有填写骨架。 | owner 人工复核如果只复制 form JSONL，可能看不到为什么不能提升 active、不能写团队标准或根规则。 | 在 form 中加入上述只读上下文字段，并补充 `status`、`worksheet_status`、`required_owner_fields`，在 `notes_zh` 明确它们不是 owner 审批。 |
| OFC-002 | 该行为没有独立回归。 | 后续简化 form 时可能再次丢失 owner gate 上下文。 | 新增 `owner-form-context` 回归场景，并把 regression helper manifest 更新到 15 个场景。 |

## 决策

- form 上下文字段是只读提示，不是 owner 决策输入。
- `--forms` 仍然只打印 JSON，不写文件、不关闭 gate、不提升 active。
- 保留 `owner_checklists` 作为更完整的人读清单；form 只补齐复制使用时必须携带的最小上下文。

## Evidence Index

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
|---|---:|---|---|---|---|
| `rtk bash tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --worksheet-id pcr02-owner-decision-worksheet-001 --forms --json` | 0 | 通过；单条 owner decision form 携带 owner 中文问题、当前状态、默认状态、允许状态、必填字段和硬门禁只读上下文 | `tools/knowledge-owner-gates.sh` | Tool | `knowledge-hub-owner-form-context-20260619` |
| `rtk bash tools/knowledge-regression.sh --json` | 0 | 通过；15 个回归场景全部 pass，包含 `owner-form-context` | `tools/knowledge-regression.sh` | Tool | `knowledge-hub-owner-form-context-20260619` |
| `rtk bash tools/knowledge-check.sh --dry-run --json --diagnostics` | 0 | 通过；0 errors、0 warnings，确认新增 manifest、registry 和 index 登记无漂移 | `tools/knowledge-check.sh` | Tool | `knowledge-hub-owner-form-context-20260619` |

## 边界

- 不修改 PCR02 源项目 docs。
- 不关闭任何 PCR02 owner gate。
- 不生成 owner decision。
- 不启用自动化，不写 memory。
- 不把 PCR02 project-specific 内容提升到 `domains/embedded/standards`。
