# Knowledge Hub Summary Gap Governance 2026-07-11

## Scope

本记录收口 2026-07-11 Knowledge Hub registry `summary_zh` 缺口治理策略。目标是提升长期可维护性，同时避免未经原文复核的批量 AI 摘要污染历史条目。

## Result

- P0 草稿已登记为 `reviewing` decision candidate，并补齐 `summary_zh`、review 边界和核心索引。
- P1 active 条目已补齐 `summary_zh`：处理后 active 缺口为 0。
- 11 条优先 archived 历史包已补齐 `summary_zh`、archive-only 边界、`promotion_decision` 和 `no-active-promotion` 标记。
- 14 个既有 reviewing 条目中，Codex archive 审计条目已有 delete/freshness/no-memory/no-active 边界；PCR02 debug/runbook reviewing 条目已补 `reviewing-followup`、`no-active-promotion` 和更明确的 `promotion_decision`。
- 剩余 `summary_zh` 缺口为 125，全部为 `archived` 条目；其中多数是历史 audit 或 retired-source provenance，不作为 mature gate blocker。

## Policy

- `active`、`reviewing`、owner-gated、外部资料吸收、AI 生成/摘要、近期触达或准备提升的条目必须有 `summary_zh`。
- `archived` 长尾条目如果已具备 `status=archived`、`promotion=none`、历史 provenance、owner/review 边界或 no-active-promotion 语义，可以作为非阻断维护债保留。
- 不对 125 条 archived 长尾做盲目批量 AI 摘要；后续按检索痛点、触达批次或提升需求分批读取正文后补。
- 补摘要不能改变历史事实、不能生成 owner decision、不能提升 active、不能关闭 owner gate、不能写 memory、不能修改源项目。
- 每次分批补摘要后必须运行 `rtk bash tools/knowledge-check.sh --dry-run --json --diagnostics`，并按需运行 mature/final gate。

## Next Batches

- 若后续继续治理 summary 长尾，优先处理 `kind=project-current` 但 `status=archived` 的 PCR02 retired-source provenance 条目。
- 第二优先级为 owner-review / source-control / final-gate 相关 audit 包。
- 第三优先级为 artifact-ref、project-archive、patent 等低频历史条目。

## Boundary

本记录是 report-only governance audit。它证明本次 summary 缺口已按优先级建立处置策略，不证明 125 条 archived 长尾内容已被逐篇复核，也不把 summary 缺口自动视为 mature blocker。
