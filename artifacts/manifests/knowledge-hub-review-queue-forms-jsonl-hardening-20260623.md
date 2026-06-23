# Knowledge Hub review queue JSONL 表单骨架加固 2026-06-23

## 结论

本轮继续压实 AI / external source 人工复核队列的终态维护路径，新增只读 JSONL 表单骨架输出，并修复 review queue 分页命令恢复路径中的非 owner 回归。

- `knowledge-index-plan.sh --section review-queue --queue-forms-jsonl` 现在可按现有 queue 过滤和分页参数输出 JSONL-only 人工填写前骨架。
- `review_batch_packet` 现在显式暴露当前批次 JSON 命令、JSONL 表单命令和下一页命令，避免新会话从普通文本中反推命令。
- `knowledge-status.sh` 与 `knowledge-final-gate.sh` 现在暴露推荐批次领取命令和推荐表单骨架命令。
- 回归断言覆盖分页 JSON、JSONL-only 输出、`--json` 互斥错误、空白人工字段和 final gate 恢复命令。

该能力只降低人工复核成本，不生成 review 结论，不回填 `human_reviewed_by` / `human_reviewed_at` / `review_basis`，不写 registry，不提升 active，不关闭 owner gate。

## 终态差距地图

| gap_id | gap_type | 当前影响 | 本轮动作 | 状态 |
|---|---|---|---|---|
| review-queue-forms-jsonl | manual-maintenance / owner-review-prep | 人工处理 review queue 时缺少可直接分发的 JSONL 填写骨架 | 新增 `--queue-forms-jsonl`，复用 queue 过滤与分页，仅输出空白人工字段和只读上下文 | applied |
| review-queue-recovery-command-drift | regression / cross-session-recovery | 分页恢复命令重构后存在 `command_parts` 残留引用，可能让 final gate 回退到非 owner `needs-fix` | 将 summary `next_command` 收口到 `next_page_command` helper，并增加回归覆盖 | applied |
| final-gate-review-queue-command-discoverability | final-gate / readability | final gate 只能暴露 generic index-plan 入口，人工领取批次和表单命令不够直接 | 在 status/final gate 透传 `recommended_batch_json` 与 `recommended_forms_jsonl` | applied |

## 改动范围

- `tools/knowledge-index-plan.sh`
  - 新增 `--queue-forms-jsonl`。
  - 与 `--json` 互斥，并强制只允许 `--section review-queue`。
  - JSONL 表单不输出顶层 `owner`，只在 `read_only_context.registry_owner` 中保留维护 owner 参考，避免被误读为人工签收字段。
  - 表单中的 `human_reviewed_by`、`human_reviewed_at`、`review_basis` 固定为空字符串。
  - `review_batch_packet` 增加 `recommended_batch_json`、`recommended_forms_jsonl` 和 `forms_jsonl_command`。
- `tools/knowledge-status.sh`
  - 从当前队列首条待复核项动态生成推荐批次领取命令和推荐表单骨架命令。
- `tools/knowledge-final-gate.sh`
  - 在 `review_queue_recovery.commands` 中透传推荐命令。
- `tools/knowledge-regression.sh`
  - 扩展 `review-queue-json-contract` 与 `final-gate-owner-review-blocker` 断言。
- `README.md`、`tools/README.md`
  - 补充 JSONL 表单骨架的用途、互斥关系和禁止事项。

## 边界

- 不生成 owner decision。
- 不关闭 owner gate。
- 不自动回填 `human_reviewed_by`、`human_reviewed_at` 或 `review_basis`。
- 不把 JSONL 表单骨架当作已复核结果。
- 不写 registry。
- 不提升 active。
- 不修改 PCR02 源项目。
- 不复制 owner-gated 正文。
- 不提升 PCR02 project-specific 内容到 `domains/embedded/standards/`。
- 不启用自动化写操作。
- 不写 `~/.codex/memories`。

## 验证证据

| Command | Exit/Status | Result Summary |
|---|---:|---|
| `rtk bash tools/knowledge-index-plan.sh --section review-queue --queue-type ai-human-review --queue-owner leiwenjun --queue-limit 3 --json` | 0 | 分页 JSON 输出成功，`summary.next_command`、`review_batch_packet.recommended_batch_json` 和 `recommended_forms_jsonl` 可恢复 |
| `rtk bash tools/knowledge-index-plan.sh --section review-queue --queue-type ai-human-review --queue-owner leiwenjun --queue-limit 3 --queue-forms-jsonl` | 0 | 输出 3 行 JSONL 表单骨架，人工字段为空，边界字段保持 read-only/report-only |
| `rtk bash tools/knowledge-index-plan.sh --section review-queue --queue-forms-jsonl --json` | 2 | 正确拒绝 JSON object 与 JSONL-only 模式混用 |
| `rtk bash tools/knowledge-status.sh --json --review-queue-limit 3` | 0 | `review_queues.commands` 暴露推荐批次和表单骨架命令 |
| `rtk bash -n tools/knowledge-index-plan.sh` | 0 | shell 语法通过 |
| `rtk bash -n tools/knowledge-status.sh` | 0 | shell 语法通过 |
| `rtk bash -n tools/knowledge-final-gate.sh` | 0 | shell 语法通过 |
| `rtk bash -n tools/knowledge-regression.sh` | 0 | shell 语法通过 |
| `rtk git diff --check` | 0 | 通过；无 whitespace error |
| `rtk bash tools/knowledge-check.sh --dry-run --json --diagnostics --as-of 2026-06-23` | 0 | 通过；0 errors、0 warnings |
| `rtk bash tools/knowledge-regression.sh --json --as-of 2026-06-23` | 0 | 通过；119 项回归全部 pass |
| `rtk bash tools/knowledge-final-gate.sh --json --as-of 2026-06-23` | needs-owner-review | 自动治理面 `complete=true`；唯一 blocker 是 7 个 `owner-gates-open`；普通 review queue 176 条，active/promotion blocker 为 0 |

## 剩余状态

本轮消除了 review queue 分页恢复路径的非 owner 工具回归，并补齐人工填写前 JSONL 骨架。普通 AI-human-review 队列仍需真实人工复核；PCR02 docs 的 7 个 owner gate 仍需要真实 owner decision，当前工具不代签、不关闭 gate。
