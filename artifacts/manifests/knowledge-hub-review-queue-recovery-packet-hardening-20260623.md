# Knowledge Hub review queue recovery packet 加固 2026-06-23

## 结论

本轮继续压实 Knowledge Hub 终态的人工维护面，重点降低 AI 生成 / 外部资料复核队列的长期处理成本：

- `knowledge-index-plan.sh --section review-queue` 的分页结果现在带有 row-level `next_commands[]`、证据引用、AI provenance 和 `review_batch_packet`。
- `knowledge-final-gate.sh --json` 现在直接暴露 `review_queue_recovery`，让终态 JSON 可以一屏恢复普通 review queue 状态。
- manifest profile summary 增加 `profile_health_next_actions_zh`，明确 `advisory-missing-boundary` 不是硬失败，也不要求回填历史正文。

这些变化只提供只读恢复入口和人工下一步，不生成 `human_reviewed_by`，不回填 `review_basis`，不提升 active，不生成 owner decision，不关闭 owner gate。

## 终态差距地图

| gap_id | gap_type | 当前影响 | 本轮动作 | 状态 |
|---|---|---|---|---|
| review-queue-row-diagnostics | manual-maintenance / Chinese-readability | 人工分页处理 174+ 条 AI-human-review 队列时，需要手工拼 explain 命令和证据入口 | 在 review queue row 中加入 `evidence_refs`、AI provenance、`next_commands[]` 和 `must_not` | applied |
| review-queue-batch-packet | manual-maintenance / tooling | 分页结果缺少一批条目的统一领取包，难以作为离线人工处理材料 | 增加 `review_batch_packet`，包含过滤条件、row ids、必填人工字段、下一页命令和禁止事项 | applied |
| final-gate-review-queue-recovery | final-gate / cross-session-linking | final gate JSON 原来只能从 next action 文本间接恢复 review queue | 增加 `review_queue_recovery` 和 evidence row；普通队列不阻断 owner-review 终态 | applied |
| manifest-profile-next-action | manifest / Chinese-readability | `advisory-missing-boundary` 已是软提示，但没有结构化下一步 | 增加 `profile_health_next_actions_zh`，说明不回填历史正文，只对后续新增治理 manifest 补 boundaries | applied |

## 改动范围

- `tools/knowledge-index-plan.sh`
  - review queue row 增加证据、AI provenance、`next_commands[]`、`must_not`。
  - 增加 `review_batch_packet`，用于按当前过滤和分页领取一批待复核项。
  - manifest summary 增加 `profile_health_next_actions_zh`。
- `tools/knowledge-final-gate.sh`
  - 增加只读 `review_queue_recovery`。
  - 在 Evidence Index 增加 `review-queue-recovery`。
  - 文本模式 Gap Map 增加 `codex_auto_can_complete`、`requires_owner_decision`、`write_scope` 和 validation 命令。
- `tools/knowledge-regression.sh`
  - 扩展既有 review queue、manifest advisory 和 final gate owner-review 回归断言。
- `README.md`、`tools/README.md`
  - 补 AI-human-review 分页复核路径和 final gate review queue 恢复字段说明。

## 边界

- 不生成 owner decision。
- 不关闭 owner gate。
- 不写 `human_reviewed_by`、`human_reviewed_at` 或 `review_basis`。
- 不提升 active。
- 不修改 PCR02 源项目。
- 不复制 owner-gated 正文。
- 不提升 PCR02 project-specific 内容到 `domains/embedded/standards/`。
- 不写 `~/.codex/memories`。
- 自动化仍保持 read-only / report-only。

## 验证证据

| Command | Exit/Status | Result Summary |
|---|---:|---|
| `rtk bash -n tools/knowledge-index-plan.sh` | 0 | shell 语法通过 |
| `rtk bash -n tools/knowledge-final-gate.sh` | 0 | shell 语法通过 |
| `rtk bash -n tools/knowledge-regression.sh` | 0 | shell 语法通过 |
| `rtk git diff --check` | 0 | 通过；无 whitespace error |
| `rtk bash tools/knowledge-index-plan.sh --section review-queue --json --queue-type ai-human-review --queue-owner leiwenjun --queue-limit 2` | 0 | 输出 `review_batch_packet`；匹配 175 条，展示 2 条，每条有 explain `next_commands[]` |
| `rtk bash tools/knowledge-index-plan.sh --section manifest --json` | 0 | 输出 `profile_health_next_actions_zh`，`advisory-missing-boundary` 明确不回填历史正文 |
| `rtk bash tools/knowledge-check.sh --dry-run --json --diagnostics --as-of 2026-06-23` | 0 | 通过；0 errors、0 warnings |
| `rtk bash tools/knowledge-regression.sh --json --as-of 2026-06-23` | 0 | 通过；当次捕获 119 个回归场景全部 pass |
| `rtk bash tools/knowledge-final-gate.sh --json --as-of 2026-06-23` | needs-owner-review | 新增 `review_queue_recovery`；175 条普通 review queue 待复核项不改变唯一 owner blocker，active/promotion blocker 为 0 |

## 剩余状态

Codex 自动治理面继续保持 `complete-except-owner-review` 目标；普通 AI-human-review 队列仍需人工逐批复核。剩余 PCR02 docs owner gate 仍需要真实 owner decision，当前工具只降低接手和恢复成本。
