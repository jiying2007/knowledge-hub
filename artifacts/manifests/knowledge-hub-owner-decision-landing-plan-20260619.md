# Knowledge Hub Owner Decision Landing Plan 2026-06-19

## 目标

在 owner 决策表校验通过后，生成只读人工落地计划，明确需要修改的控制面文件、人工动作、验证命令和禁止事项，避免 owner 决策从“表已填好”到“治理面落地”之间再次依赖会话记忆或手工拼规则。

## 问题地图

| ID | 问题 | 风险 | 处理 |
| --- | --- | --- | --- |
| OLP-001 | `--validate-forms` 能校验 owner 回填表，但没有给出后续人工落地文件清单。 | owner 决策可能通过校验后仍漏改 registry、migration 或索引。 | 新增 `--landing-plan`。 |
| OLP-002 | 落地计划若自动写文件，会越过 owner review 和人工复核。 | 自动关闭 gate 或提升 active 会造成知识污染。 | landing plan 只读输出，不写文件、不关闭 gate、不提升 active。 |
| OLP-003 | 校验失败时仍输出落地步骤会误导维护者。 | 无效 owner form 可能被继续人工落地。 | 只有 `form_validation.status=pass` 时计划为 `planned`；失败时为 `blocked`。 |

## 决策

- 新增参数：`rtk bash tools/knowledge-owner-gates.sh --validate-forms <jsonl> --landing-plan`。
- `--landing-plan` 必须与 `--validate-forms` 一起使用。
- JSON 输出增加 `landing_plan`，包含：
  - `required_manual_files`
  - `verification_commands`
  - 每个 form 的 `manual_actions_zh`
  - `must_not`
- 计划只读，不执行 apply。
- `required_manual_files` 必须包含 `indexes/by-project.md`，与 PCR02 owner resolution playbook 的控制面落地规则一致。

## 非目标

- 不自动修改 registry、index、migration 或正文。
- 不生成 owner decision。
- 不判断 owner 决策语义正确性。
- 不关闭 owner gate。
- 不迁移 owner-gated 正文。
- 不修改源项目 docs。
- 不启用自动化。
- 不写 `~/.codex/memories`。

## Evidence Index

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
| --- | --- | --- | --- | --- | --- |
| `/tmp valid owner form + landing plan fixture` | 0 | 有效 owner form 校验通过，`landing_plan.status=planned`，生成 1 个人工落地 step。 | `/tmp/kh-owner-form-valid3.jsonl` | Positive fixture | owner-decision-landing-plan |
| `/tmp invalid owner form + landing plan fixture` | 1 expected | 无效 owner form 校验失败，`landing_plan.status=blocked`，不提供可用落地计划。 | `/tmp/kh-owner-form-invalid3.jsonl` | Negative fixture | owner-decision-landing-plan |
| `rtk bash tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --landing-plan --json` | 1 expected | 缺少 `--validate-forms` 时返回 1，原因是 `--landing-plan requires --validate-forms <jsonl>`。 | `tools/knowledge-owner-gates.sh` | Negative fixture | owner-decision-landing-plan |
| `rtk bash tools/knowledge-regression.sh --json` | 0 | 通过；landing plan 回归确认 `required_manual_files` 包含 `indexes/by-project.md`。 | `tools/knowledge-regression.sh` | Knowledge Hub | owner-decision-landing-plan |
| `rtk bash tools/knowledge-check.sh --dry-run --json --diagnostics` | 0 | 新增 landing plan 后全仓门禁应通过。 | `tools/knowledge-check.sh` | Knowledge Hub | owner-decision-landing-plan |
| `rtk bash tools/knowledge-search.sh owner-decision-landing-plan-applied --json` | 0 | 本制品应可检索，命中 registry、status index 和本 manifest。 | `registry/items.jsonl`、`indexes/by-status.md`、本 manifest | Knowledge Hub | owner-decision-landing-plan |

## Review

- owner：`leiwenjun`
- review_after：`2026-09-19`
- review_status：`owner-decision-landing-plan-applied`
- 下一次复核内容：若 owner decision landing 流程变更，更新 `required_manual_files`、`verification_commands` 和对应回归场景。
