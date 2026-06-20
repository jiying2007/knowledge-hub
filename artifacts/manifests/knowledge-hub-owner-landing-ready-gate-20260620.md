# Knowledge Hub owner landing ready gate（2026-06-20）

## 结论

本轮加固 `tools/knowledge-owner-gates.sh --landing-plan` 的只读人工落地计划门禁：

- owner decision form 可以继续独立校验。
- 只有 form validation 通过，且对应 worksheet 已有强校验通过的 `owner-ready` package 时，`landing_plan.status` 才能进入 `planned`。
- 若 `owner-ready` package 缺失、无效或重复，即使 owner form 字段校验通过，`landing_plan.status` 也必须保持 `blocked`。
- 被阻断时不输出人工落地 `steps`，避免没有签收准备包的 owner decision 被继续手工落地。

## 背景

`knowledge-hub-owner-ready-coverage-status-20260620` 已把 7 条 PCR02 owner gate 的 `owner-ready` package 覆盖状态显示出来。但仅显示覆盖状态还不够，后续人工落地路径也必须强制依赖该覆盖结果，否则可能出现：

- owner form 字段完整，但缺少对应签收准备包。
- owner-ready package registry item 被误删、路径漂移或 JSONL 内容失配。
- landing plan 仍给出 registry、migration、index 手工步骤，造成维护者误以为可以继续落地。

## 变更

- `make_landing_plan` 在 form validation 通过后逐条检查 `owner_ready_state(row)`。
- `owner_ready_state.status` 只有为 `covered` 时才允许生成该 form 的人工落地 step。
- `missing`、`invalid`、`duplicate` 都会写入 `landing_plan.owner_ready_gate.errors`。
- `landing_plan.owner_ready_gate.status` 为 `blocked` 时，`landing_plan.steps` 为空。
- 文本输出补充 `owner_ready_gate` 和 `owner_ready_gate_errors`，便于非 JSON 查看。
- 回归测试新增三条 owner-ready 负向路径，覆盖 `missing`、`invalid`、`duplicate` 均会阻断 landing plan。

## 非目标

- 不生成 owner decision。
- 不关闭 owner gate。
- 不自动修改 registry、migration 或 index。
- 不迁移 owner-gated source 正文。
- 不修改源项目 docs。
- 不把 PCR02 project-specific 内容提升到 `domains/embedded/standards/`。
- 不启用自动化。
- 不写 `~/.codex/memories`。

## Evidence Index

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
| --- | --- | --- | --- | --- | --- |
| `rtk bash tools/knowledge-regression.sh --json` | 0 | 23 个回归场景通过；新增负向场景确认 form validation 通过但 owner-ready package 缺失、无效或重复时 `landing_plan.status=blocked`，不输出 steps。 | `tools/knowledge-regression.sh` | Knowledge Hub | owner-landing-ready-gate |
| `rtk git diff --check` | 0 | 当前补丁无 whitespace error。 | working tree diff | Git | owner-landing-ready-gate |
| `rtk bash tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --worksheet-id pcr02-owner-decision-worksheet-001 --forms --json` | 0 | focused owner form 仍可只读生成，且显示对应 owner-ready 覆盖状态。 | `tools/knowledge-owner-gates.sh` | Knowledge Hub | owner-landing-ready-gate |
| `rtk bash tools/knowledge-check.sh --dry-run --json --diagnostics` | 0 | 通过；0 errors、0 warnings，本 manifest、registry、migration 和索引登记一致。 | `tools/knowledge-check.sh` | Knowledge Hub | owner-landing-ready-gate |
| `rtk bash tools/knowledge-status.sh --strict --json` | 1 expected | 返回 `needs-owner-review`；`knowledge_check` 通过，唯一 strict blocker 是 7 条 owner gate 尚未签收。 | `tools/knowledge-status.sh` | Knowledge Hub | owner-landing-ready-gate |
| `rtk bash tools/knowledge-final-gate.sh --json` | 1 expected | 返回 `needs-owner-review`；`knowledge-check` 与 `knowledge-regression` 通过，唯一 blocker 为 `owner-gates-open count=7`。 | `tools/knowledge-final-gate.sh` | Knowledge Hub | owner-landing-ready-gate |

## 边界说明

本制品是 Knowledge Hub 控制面治理加固，不是 PCR02 正文迁移，也不是 owner decision。`by-project` 不需要更新，因为没有新增 `domains/projects/pcr02/` 下的当前事实、决策、验证报告或归档正文。

## Review

- owner：`leiwenjun`
- review_after：`2026-09-20`
- review_status：`owner-landing-ready-gate-applied`
- 下一次复核内容：若 owner decision landing plan 的 required files、manual actions 或 owner-ready package 强校验口径变化，需同步更新本 manifest、回归场景和 registry validation refs。
