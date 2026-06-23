# Knowledge Hub review queue and topic readability hardening 2026-06-23

## 结论

本轮把 AI / external source 人工复核队列从分散 registry 字段中派生出来，并把 `indexes/by-topic.md` 的首屏恢复视图拆成“优先恢复主题速查 / 领域入口 / 历史治理台账”三段。

该变更只提供只读、report-only 的治理视图和回归保护，不生成 owner decision，不关闭 owner gate，不提升 active，不写 memory。

## 本轮收口

- `tools/knowledge-status.sh` 新增 `review_queues` 顶层 JSON 字段，按 registry 派生 AI 生成内容和外部资料的待人工复核队列。
- `tools/knowledge-index-plan.sh` 新增 `--section review-queue`，输出可恢复的 review queue 索引计划。
- `indexes/by-topic.md` 首屏仅保留恢复主题、领域入口和最短命令；历史治理制品集中到“历史治理台账”。
- `indexes/README.md` 增加 by-topic 首屏维护规则，避免历史 manifest 再次挤占恢复入口。
- `tools/knowledge-regression.sh` 新增 `by-topic-first-screen-readability-contract` 和 `review-queue-json-contract` 两个回归场景，回归覆盖扩展到 114 项。
- `artifacts/manifests/knowledge-hub-governance-regression-helper-20260619.md` 更新回归场景说明，保留中文可读维护证据。

## Stable Context

- 仓库：`/home/leiwenjun/knowledge-hub`
- 输入基线：`4e16206 docs(knowledge): 生成 PCR02 复核包`
- 所有 shell 命令必须通过 `rtk`。
- 手工写文件必须使用 `apply_patch`。
- 不直接写 `~/.codex/memories`。
- 不修改 PCR02 源项目 docs、tools、knowledge、product-test、scratch 或根目录源文件。
- 不把 PCR02 project-specific 内容提升到 `domains/embedded/standards/`。
- 自动化默认 read-only / report-only，不自动删除、发布、提交、提升 active、关闭 owner gate 或写 memory。
- 文档、索引、manifest 和 worksheet 默认使用简体中文，并优先保证可读性。

## Dynamic Context

- `review_queues.summary.total_pending_count` 在本 manifest 登记前为 170；登记该 AI 生成 manifest 后，当前 status 派生视图为 171。该计数是 registry 实时派生值，不应作为固定历史事实手工维护。
- `review_queues.summary.active_or_promotion_blocker_count` 当前为 0，因此复核队列不阻塞 final gate。
- PCR02 docs owner gate 仍为 7 个 open。
- owner-ready package coverage 仍为 `7/7`。
- active exposure 仍为 0。
- 当前自动治理状态仍为 `complete-except-owner-review`，终态仍应报告 `needs-owner-review`。

## Evidence

| Evidence | Path / Command | Summary |
|---|---|---|
| 状态视图 | `tools/knowledge-status.sh` | 新增 read-only / report-only `review_queues`，从 registry 派生待人工复核队列。 |
| 索引计划 | `tools/knowledge-index-plan.sh --section review-queue --json` | 输出 review queue rows、类型分组、owner 分组和禁止动作。 |
| 主题索引 | `indexes/by-topic.md` | 首屏恢复入口与历史治理台账已拆分。 |
| 索引维护说明 | `indexes/README.md` | by-topic 首屏可读性规则已记录。 |
| 回归门禁 | `tools/knowledge-regression.sh` | 新增 by-topic 首屏可读性和 review queue JSON 契约。 |
| 回归说明 | `artifacts/manifests/knowledge-hub-governance-regression-helper-20260619.md` | 回归覆盖说明更新到 114 项。 |

## Validation

- `rtk bash -n tools/knowledge-status.sh`
- `rtk bash -n tools/knowledge-index-plan.sh`
- `rtk bash -n tools/knowledge-regression.sh`
- `rtk bash tools/knowledge-status.sh --json --as-of 2026-06-23`
- `rtk bash tools/knowledge-index-plan.sh --section review-queue --json`
- `rtk bash tools/knowledge-index-plan.sh --section linking --json`
- `rtk bash tools/knowledge-check.sh --dry-run --json --diagnostics --as-of 2026-06-23`
- `rtk bash tools/knowledge-regression.sh --json --as-of 2026-06-23`
- `rtk git diff --check`
- `rtk bash tools/knowledge-final-gate.sh --json --as-of 2026-06-23`

## Excluded Context

- 不把 AI 复核队列中的 `reviewing` 条目视为 human reviewed。
- 不把 `review_queues` 视为 owner decision、owner gate 关闭依据或 active 提升依据。
- 不把外部资料、AI 生成内容、handoff 或 memory candidates 自动提升为 active facts。
- 不写 `~/.codex/memories`。
- 不修改源项目文件。

## Resume Prompt

```text
继续 /home/leiwenjun/knowledge-hub 的终态治理。当前新增了 review queue 只读恢复视图和 by-topic 首屏可读性契约。恢复时优先读取：
- artifacts/manifests/knowledge-hub-review-queue-topic-readability-20260623.md
- tools/knowledge-status.sh
- tools/knowledge-index-plan.sh
- indexes/by-topic.md
- tools/knowledge-regression.sh

严格遵守：
- 所有 shell 命令用 rtk
- 手工修改用 apply_patch
- 不写 ~/.codex/memories
- 不修改 PCR02 源项目
- 不把 PCR02 project-specific 内容提升到 domains/embedded/standards
- 自动化默认 report-only/read-only

下一步只推进不需要 owner 代签的治理缺口。终态验证至少运行：
- rtk bash tools/knowledge-check.sh --dry-run --json --diagnostics --as-of 2026-06-23
- rtk bash tools/knowledge-regression.sh --json --as-of 2026-06-23
- rtk git diff --check
- rtk bash tools/knowledge-final-gate.sh --json --as-of 2026-06-23
```

## Must Not

- 不生成 owner decision。
- 不关闭 owner gate。
- 不修改源项目。
- 不复制 owner-gated 正文。
- 不启用自动化。
- 不提升 active。
- 不写 memory。
