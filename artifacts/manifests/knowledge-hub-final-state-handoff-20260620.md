# Knowledge Hub final state handoff 2026-06-20

## Superseded Recovery Note

本接力包保留为历史证据。2026-06-23 起，当前恢复口径以 `artifacts/manifests/knowledge-hub-final-state-handoff-supersede-20260623.md` 为准：最新自动治理状态仍是 `needs-owner-review` / `complete-except-owner-review`，剩余语义 blocker 仍只有 7 个 PCR02 owner gates，且 final proof 可发现性已扩展到 `indexes/by-decision.md`。

## Latest Goal

按 `docs/goals/knowledge-hub-final-state.md` 定义，继续把 Knowledge Hub 压实为长期可维护、跨会话可恢复、人工可独立维护、AI 可辅助治理、自动化受控的统一知识控制面。

当前自动治理终态为 `complete-except-owner-review`：除真实人工 owner decision 外，source coverage、source registry、registry/index、manifest、状态看板、final gate、回归、人工维护入口和 owner 签收辅助路径已具备可验证控制面。

## Invalidated Goals

- 不把“终态推进”解释为复制全部源正文。
- 不把 `knowledge-status.sh --strict` 当作 terminal final gate；terminal gate 是 `rtk bash tools/knowledge-final-gate.sh --json`。
- 不把 handoff 摘要当完成证据；完成声明必须回读原始 manifest、registry、index 和命令输出。
- 不把 open owner gate 当工具失败；它是人工语义 blocker。

## Stable Context

- 仓库：`/home/leiwenjun/knowledge-hub`
- 接力包输入基线：`5f4ec31 docs(governance): 暴露终态门禁入口`
- 接力包初始落盘提交：`9542510 docs(governance): 生成终态接力包`
- 恢复时必须先用 `rtk git log --oneline -5` 确认最新 HEAD，不要把输入基线当作当前提交。
- 所有 shell 命令必须通过 `rtk`。
- 手工写文件必须使用 `apply_patch`。
- 不直接写 `~/.codex/memories`。
- 不修改 PCR02 源项目 docs、tools、knowledge、product-test、scratch 或根目录源文件。
- 不把 PCR02 project-specific 内容提升到 `domains/embedded/standards/`。
- 自动化默认 read-only / report-only，不自动删除、发布、提交、提升 active、关闭 owner gate 或写 memory。
- source 正文只维护一份；Knowledge Hub 通过迁移副本、ref、artifact-ref、registry、manifest 和 index 管理控制面。

## Dynamic Context

最近终态推进提交：

- `5f4ec31 docs(governance): 暴露终态门禁入口`
- `faf570b docs(governance): 增加owner表单分发入口`
- `39d0849 docs(governance): 压实source终态字段`
- `26feab5 docs(governance): 汇总终态分层审计`
- `150f8d1 docs(governance): 结构化终态差距地图`

当前 final gate 摘要：

- `final_status=needs-owner-review`
- `automatic_governance.status=complete-except-owner-review`
- `level1_pcr02_docs=complete-except-owner-review`
- `level2_pcr02_candidate_sources=complete`
- `level3_registered_sources=complete`
- `gap_map=[owner-gates-open]`

当前 remaining semantic blocker：

- 7 个 PCR02 docs owner decision worksheet 仍未人工签收。
- `owner-ready package coverage=7/7`，无 owner-ready missing / invalid / duplicate。
- owner-gated 内容未 active，未复制 owner-gated 正文。

## Evidence

| Evidence | Path / Command | Summary |
|---|---|---|
| Final-state goal | `docs/goals/knowledge-hub-final-state.md` | 终态目标、非目标、Level 1/2/3、owner-gated 两阶段流程和 handoff 可恢复要求。 |
| Final gate | `rtk bash tools/knowledge-final-gate.sh --json` | 当前预期 exit `1`，只剩 `owner-gates-open`。 |
| Status dashboard | `rtk bash tools/knowledge-status.sh --strict --json` | 输出 `final_gate_command`、owner summary、by-owner forms-jsonl、validate-forms 和 landing-plan 命令。 |
| Knowledge check | `rtk bash tools/knowledge-check.sh --dry-run --json --diagnostics` | 当前应为 pass，0 errors / 0 warnings。 |
| Regression | `rtk bash tools/knowledge-regression.sh --json` | 当前 33 个回归场景应全部 pass。 |
| Owner forms | `rtk bash tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --forms-jsonl` | 输出 7 条 owner 人工填写 skeleton，不写文件。 |
| Owner by-owner forms | `rtk bash tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --owner project-owner --forms-jsonl` | 输出 `project-owner` 负责的 owner skeleton，不写文件。 |
| Source registry final-state fields | `artifacts/manifests/knowledge-hub-source-registry-final-state-fields-20260620.md` | source registry 维护 owner、review_after、migration strategy、final disposition 已门禁化。 |
| Final audit summary | `artifacts/manifests/knowledge-hub-final-state-audit-summary-20260620.md` | final gate Level 1/2/3 摘要字段和证据锚点。 |
| Owner-ready packages | `artifacts/manifests/pcr02-*-owner-ready-package-20260620.md` | 7 个单项 owner-ready 包，均保持 `owner-ready-no-decision`。 |

## Excluded Context

以下内容不得在恢复后自动进入 active facts、active rules 或 owner decision：

- 任何 owner-gated source 正文。
- PCR02 `AGENTS.md`、module `AGENTS.md` 或项目局部规则，除非 owner 决策确认目标范围。
- `diag-command-metadata-standard.md` 作为团队标准。
- `asan-debug-guide.md` 作为 team-level ASAN 标准。
- `memory-auto-curation-guide.md` 作为已启用自动化或 memory writer。
- DVR session archive 的 handoff、dirty-state、memory candidates。
- `~/codex` 中当前 5 个无关 manifest/workflow/schema 脏变更。
- 本 handoff 摘要本身，作为完成证据或 owner 签收证据。

## Open Blockers

唯一终态 blocker：

- `owner-gates-open`：7 个 PCR02 owner decision worksheet 未签收。

这些 blocker 只能通过真实 owner 填写 owner decision JSONL 后解决：

```bash
rtk bash tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --forms-jsonl
rtk bash tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --validate-forms '<owner-decisions.jsonl>' --json
rtk bash tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --validate-forms '<owner-decisions.jsonl>' --landing-plan --json
```

## Next Actions

1. 若继续自动治理，优先寻找 owner gate 之外仍能降低人工维护成本或恢复风险的切片；不得伪造 owner decision。
2. 若用户提供 owner decision JSONL，先运行 `validate-forms`，再生成 no-write landing plan；只有校验通过后才能按 landing plan 人工落地。
3. 若上下文继续增长，优先新开会话并使用本 handoff 恢复；恢复后必须重新运行 `knowledge-status` 或 `knowledge-final-gate`，不要直接信任本摘要的动态状态。

第一条建议命令：

```bash
rtk bash tools/knowledge-final-gate.sh --json
```

## Resume Prompt

```text
继续 /home/leiwenjun/knowledge-hub 的 Knowledge Hub 终态治理。先用 rtk git log --oneline -5 确认当前 HEAD；本接力包的输入基线是 5f4ec31，初始落盘提交是 9542510。自动治理状态为 complete-except-owner-review；final gate 预期返回 exit 1 / needs-owner-review，唯一 gap 是 owner-gates-open。Level 1 PCR02 docs 为 complete-except-owner-review，Level 2 PCR02 candidate sources complete，Level 3 registered sources complete。

请先读取：
- artifacts/manifests/knowledge-hub-final-state-handoff-20260620.md
- docs/goals/knowledge-hub-final-state.md
- tools/README.md

严格遵守：
- 所有 shell 命令用 rtk。
- 手工修改用 apply_patch。
- 不写 ~/.codex/memories。
- 不修改 PCR02 源项目 docs/tools/knowledge/app_product_test/scratch/root source。
- 不把 PCR02 project-specific 内容提升到 domains/embedded/standards。
- 不生成 owner decision，不关闭未签收 owner gate。
- 自动化默认 read-only/report-only。

下一步优先处理 owner gate 之外的可验证终态缺口；如果用户提供 owner decision JSONL，则先 validate-forms，再生成 no-write landing-plan。
```

## Memory Candidates

不直接写 memory。候选：

- Knowledge Hub final gate 的 terminal entrypoint 是 `rtk bash tools/knowledge-final-gate.sh --json`；`knowledge-status.sh` 是状态看板，不替代 final gate。
- PCR02 owner-gated source 只允许通过真实 owner decision JSONL 关闭，Codex 只能生成 skeleton、校验和 no-write landing plan。
- Handoff / session archive / memory candidates 只能作为 archive 或恢复参考，不进入 active facts，不写 memory。

## Archive Candidates

- 本文件可作为 Knowledge Hub 终态治理长线程恢复包；它不替代 raw evidence。

## Gate Result

`pass-for-handoff`

Fallback condition：若后续要声明 `complete`、`active`、`owner-approved`、`team-standard`、`automation-enabled` 或 `memory-written`，必须回读原始 evidence 并重新运行门禁，不能只引用本 handoff。
