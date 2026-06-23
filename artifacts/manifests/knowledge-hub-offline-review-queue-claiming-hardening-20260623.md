# Knowledge Hub offline and review queue claiming hardening 2026-06-23

## 结论

本轮把离线人工维护包的 `required_followup` 统一为完整 `rtk` 命令，并把 AI / external source 人工复核队列从“可恢复”推进到“可分批领取”。

该变更只增强只读治理入口、文档可读性和回归保护；不生成 owner decision，不关闭 owner gate，不提升 active，不修改 PCR02 源项目，不启用自动化，不写 memory。

## 本轮收口

- `docs/goals/knowledge-hub-final-state.md` 的离线 fallback 从弱自然语言改为完整 `rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics; rtk bash ~/knowledge-hub/tools/knowledge-index-plan.sh --section all`。
- `README.md` 增加“人工复核”低复杂度入口，并收敛 item/source 字段细节，避免根 README 复制出第二套字段权威。
- `tools/README.md` 增加 review queue 工具入口，说明 `--review-queue-limit`、`--section review-queue` 和只读边界。
- `tools/knowledge-index-plan.sh` 的 `--section review-queue` 增加 `--queue-type`、`--queue-owner`、`--queue-review-after`、`--queue-priority`、`--queue-limit`、`--queue-offset`，用于按 owner / 日期 / 类型 / priority 分批领取。
- `tools/knowledge-regression.sh` 增加 `manual-entry-offline-package-consistency`，并扩展 `review-queue-json-contract` 覆盖过滤、分页和 no-memory-write 边界。
- `artifacts/manifests/knowledge-hub-review-queue-topic-readability-20260623.md` 将固定计数改为动态说明，避免把历史 170 条误当 live 状态。
- `artifacts/manifests/knowledge-hub-governance-regression-helper-20260619.md` 更新回归覆盖到 115 项。

## 动态状态说明

- 本轮开始时 `knowledge-status.sh --json --as-of 2026-06-23` 显示 review queue 为 171 条，全部为 `ai-human-review`，`active_or_promotion_blocker_count=0`。
- 本 manifest 登记后，AI 生成的治理条目会自然进入下一轮复核队列，因此 live 计数可能变为 172；后续以 `knowledge-status.sh` 和 `knowledge-index-plan.sh --section review-queue --json` 为准。
- PCR02 docs owner gate 仍为 7 个 open，owner-ready coverage 仍为 `7/7`，active exposure 仍为 0。

## Evidence

| Evidence | Path / Command | Summary |
|---|---|---|
| 终态目标 | `docs/goals/knowledge-hub-final-state.md` | 离线人工维护 follow-up 使用完整 `rtk` 命令。 |
| 根入口 | `README.md` | 增加人工复核入口，保留 5 条最短路径，字段权威指向 templates/schema/tools。 |
| 工具入口 | `tools/README.md` | 明确 review queue status/index-plan 入口和只读边界。 |
| 队列工具 | `tools/knowledge-index-plan.sh --section review-queue --queue-owner leiwenjun --queue-limit 3 --json` | 输出过滤、分页、matched/shown 和 next command。 |
| 回归门禁 | `tools/knowledge-regression.sh` | 覆盖离线维护包一致性和 review queue 分页过滤契约。 |

## Validation

本轮最终验证以当前命令输出为准：

- `rtk bash -n tools/knowledge-index-plan.sh`
- `rtk bash -n tools/knowledge-regression.sh`
- `rtk bash tools/knowledge-index-plan.sh --section review-queue --queue-owner leiwenjun --queue-limit 3 --json`
- `rtk bash tools/knowledge-check.sh --dry-run --json --diagnostics --as-of 2026-06-23`
- `rtk bash tools/knowledge-regression.sh --json --as-of 2026-06-23`
- `rtk git diff --check`
- `rtk bash tools/knowledge-final-gate.sh --json --as-of 2026-06-23`

## Must Not

- 不生成 owner decision。
- 不关闭 owner gate。
- 不修改源项目。
- 不复制 owner-gated 正文。
- 不提升 active。
- 不启用自动化。
- 不写 `~/.codex/memories`。

