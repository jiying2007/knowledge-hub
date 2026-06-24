# Knowledge Hub final-state handoff supersede 2026-06-23

## 结论

本文件是 `artifacts/manifests/knowledge-hub-final-state-handoff-20260620.md` 的恢复口径 supersede 记录，不是新的 owner decision，也不是完成声明。

当前可自动治理部分已经保持 `complete-except-owner-review`，但 PCR02 docs 的 7 个 owner gates 仍未由真实 owner 签收，因此终态仍应报告为 `needs-owner-review`。

## 本轮收口

- 将 final gate 的 `proof_artifacts` 可发现性索引从 `by-owner/by-status/by-review-date/by-topic` 扩展到 `indexes/by-decision.md`。
- 在 `indexes/by-decision.md` 增加 2026-06-23 当前治理 proof 的中文决策恢复锚点。
- 在回归中新增 `final-proof-decision-index-recovery-contract`，防止后续 proof 只登记到主题索引、但缺少决策恢复视图。
- 给 2026-06-20 旧 handoff 增加 supersede 提示，避免新会话继续把旧的 33 项回归、旧 HEAD 或旧恢复命令当作当前口径。

## Stable Context

- 仓库：`~/knowledge-hub`
- 本轮输入基线：`8f48ac2 docs(governance): 加固owner归档表单路径`
- 所有 shell 命令必须通过 `rtk`。
- 手工写文件必须使用 `apply_patch`。
- 不直接写 `~/.codex/memories`。
- 不修改 PCR02 源项目 docs、tools、knowledge、product-test、scratch 或根目录源文件。
- 不把 PCR02 project-specific 内容提升到 `domains/embedded/standards/`。
- 自动化默认 read-only / report-only，不自动删除、发布、提交、提升 active、关闭 owner gate 或写 memory。
- source 正文只维护一份；Knowledge Hub 通过迁移副本、ref、artifact-ref、registry、manifest 和 index 管理控制面。

## Dynamic Context

- 当前自动治理状态：`complete-except-owner-review`。
- 当前终态状态：`needs-owner-review`。
- 当前唯一严格语义 blocker：`owner-gates-open`。
- PCR02 docs owner gate：7 个仍 open。
- owner-ready package coverage：`7/7`。
- active exposure：`0`。
- report-only source check snapshot：继续只作为快照证据，不代表 source 内容有效、owner 签收或 active 提升。

## Evidence

| Evidence | Path / Command | Summary |
|---|---|---|
| 旧 handoff | `artifacts/manifests/knowledge-hub-final-state-handoff-20260620.md` | 保留历史接力上下文，并已增加 supersede 提示。 |
| 当前状态命令 | `rtk bash tools/knowledge-status.sh --json --as-of 2026-06-23` | 预期输出 `needs-owner-review`，仅剩 owner gates。 |
| owner gate 摘要 | `rtk bash tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --summary --json` | 预期 7 open，owner-ready coverage 7/7，active exposure 0。 |
| final proof 门禁 | `tools/knowledge-final-gate.sh` | `FINAL_PROOF_INDEX_PATHS` 已包含 `indexes/by-decision.md`。 |
| 决策恢复索引 | `indexes/by-decision.md` | 2026-06-23 当前治理 proof 已有中文锚点，并明确不生成 owner decision、不关闭 owner gate、不写 memory。 |
| 回归门禁 | `tools/knowledge-regression.sh` | 新增 `final-proof-decision-index-recovery-contract`。 |

## Excluded Context

- 不把旧 handoff 中的旧 HEAD、旧回归数量或旧恢复命令当作当前事实。
- 不把 owner-ready package、owner inbox、landing plan 或表单骨架当作 owner decision。
- 不把 `.session`、handoff 或 memory candidates 提升为 active facts。
- 不把 PCR02 project-specific 内容提升到 `domains/embedded/standards/`。
- 不写 `~/.codex/memories`。

## Resume Prompt

```text
继续 ~/knowledge-hub 的终态治理。当前应先验证最新 HEAD 和工作区状态，不要把 2026-06-20 handoff 当作当前口径。恢复时读取：
- docs/goals/knowledge-hub-final-state.md
- artifacts/manifests/knowledge-hub-final-state-handoff-supersede-20260623.md
- registry/items.jsonl
- indexes/by-decision.md

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
- 不写 memory。
