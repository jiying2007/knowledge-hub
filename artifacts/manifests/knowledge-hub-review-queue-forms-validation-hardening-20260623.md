# Knowledge Hub review queue 表单校验加固 2026-06-23

## 结论

本轮继续降低 AI / external source 普通人工复核队列的维护成本：在 JSONL 表单骨架之后，新增 report-only 的填回表单校验入口。

- `knowledge-index-plan.sh --section review-queue --validate-queue-forms <review-queue-forms.jsonl> --json` 现在可校验人工填写后的 review queue JSONL。
- 校验内容包括表单身份、必填人工字段、`human_reviewed_at` 日期、`review_decision` 枚举、queue id 覆盖、重复 queue id、未知 queue id、owner gate 字段混入和 guardrail 字段。
- `knowledge-status.sh` 与 `knowledge-final-gate.sh` 现在暴露 `recommended_validate_queue_forms`，用于跨会话恢复人工批次校验入口。
- 回归覆盖正向填写、重复 `queue_id`、未知 `queue_id`、非法 `review_decision`、缺失人工必填字段、混入 owner gate 字段、身份字段篡改、guardrail 字段篡改，以及命令级组合拒绝。

该能力只做结构校验和边界校验，不写 registry，不自动回填 `human_reviewed_by` / `human_reviewed_at` / `review_basis`，不生成 review 结论，不生成 owner decision，不关闭 owner gate，不提升 active。

## 终态差距地图

| gap_id | gap_type | 当前影响 | 本轮动作 | 状态 |
|---|---|---|---|---|
| review-queue-filled-form-validation | manual-maintenance / report-only-validation | 人工导出 JSONL 表单后缺少只读校验，容易把 owner decision 字段或非法 decision 混入普通 review queue | 新增 `--validate-queue-forms <jsonl> --json`，输出 `form_validation` 结构化报告 | applied |
| review-queue-validation-discoverability | final-gate / cross-session-recovery | final gate 和 status 只能暴露领取/导出命令，缺少人工填回后的下一步 | 在 status/final gate 透传 `recommended_validate_queue_forms` 模板 | applied |
| review-queue-first-screen-recovery | Chinese-readability / index | by-topic 首屏缺少普通 review queue 恢复入口 | 增加 `review queue` 主题速查，指向 `knowledge-status` 和 `knowledge-index-plan` | applied |

## 改动范围

- `tools/knowledge-index-plan.sh`
  - 新增 `--validate-queue-forms <jsonl>`。
  - 校验入口要求 `--section review-queue --json`，且不能与 `--queue-forms-jsonl` 组合。
  - 输出 `form_validation`，包含 `status`、`diagnostics`、`warnings`、`coverage_status`、`required_submission_fields` 和 guardrail 字段。
  - 校验通过只证明 JSONL 结构、字段和边界有效，不代表 registry 已更新。
- `tools/knowledge-status.sh`
  - `review_queues.commands` 增加 `recommended_validate_queue_forms`。
- `tools/knowledge-final-gate.sh`
  - `review_queue_recovery.commands` 透传 `recommended_validate_queue_forms`。
- `tools/knowledge-regression.sh`
  - 扩展 `review-queue-json-contract` 与 `final-gate-owner-review-blocker`。
- `README.md`、`tools/README.md`
  - 区分普通 review queue 表单校验和 owner decision 表单校验。
- `indexes/by-topic.md`
  - 首屏增加 `review queue` 恢复入口。

## 边界

- 不生成 owner decision。
- 不关闭 owner gate。
- 不自动回填 `human_reviewed_by`、`human_reviewed_at` 或 `review_basis`。
- 不写 registry。
- 不生成普通 review 结论。
- 不提升 active。
- 不把普通 AI-human-review 队列变成 final gate blocker。
- 不修改 PCR02 源项目。
- 不复制 owner-gated 正文。
- 不提升 PCR02 project-specific 内容到 `domains/embedded/standards/`。
- 不启用自动化写操作。
- 不写 `~/.codex/memories`。

## 验证证据

| Command | Exit/Status | Result Summary |
|---|---:|---|
| `rtk bash -n tools/knowledge-index-plan.sh` | 0 | shell 语法通过 |
| `rtk bash -n tools/knowledge-status.sh` | 0 | shell 语法通过 |
| `rtk bash -n tools/knowledge-final-gate.sh` | 0 | shell 语法通过 |
| `rtk bash -n tools/knowledge-regression.sh` | 0 | shell 语法通过 |
| `rtk bash tools/knowledge-index-plan.sh --section review-queue --queue-type ai-human-review --queue-owner leiwenjun --queue-limit 1 --json --validate-queue-forms /tmp/kh-review-queue-valid.jsonl` | 0 | `form_validation.status=pass`，`accepted_count=1`，无 registry write，无 landing support |
| `rtk git diff --check` | 0 | 无 whitespace/error |
| `rtk bash tools/knowledge-check.sh --dry-run --json --diagnostics --as-of 2026-06-23` | 0 / pass | 0 error，0 warning |
| `rtk bash tools/knowledge-regression.sh --json --as-of 2026-06-23` | 0 / pass | 119 项回归全部 pass；review queue 正向、命令级拒绝和负向表单校验均覆盖 |
| `rtk bash tools/knowledge-final-gate.sh --json --as-of 2026-06-23` | 1 / needs-owner-review | 自动治理 complete；仅剩 `owner-gates-open` owner-review blocker；普通 review queue 不作为 active/promotion blocker |

## 剩余状态

普通 review queue 仍是人工分批复核事项，不阻断 final gate。PCR02 docs 的 7 个 owner gate 仍需要真实 owner decision；当前工具只提供领取、导出和只读校验，不代签、不关闭 gate。
