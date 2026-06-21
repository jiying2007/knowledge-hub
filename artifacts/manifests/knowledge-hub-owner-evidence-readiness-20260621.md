# Knowledge Hub owner evidence readiness 2026-06-21

## 结论

本轮为 owner gate 工具增加只读证据准备度视图和预填候选字段，目标是降低 PCR02 7 个 open owner gate 的人工签收整理成本。

该能力不生成 `owner_decision`，不填写 `reviewed_by`，不关闭 owner gate，不修改 PCR02 源项目 docs，不把 PCR02 project-specific 内容提升到 `domains/embedded/standards/`，不启用自动化，也不写 `~/.codex/memories`。

## 变更

| 路径 | 变更 |
|---|---|
| `tools/knowledge-owner-gates.sh` | 新增 `--evidence-readiness`，输出字段 readiness、source identity 候选、owner-ready evidence ref 候选、safe/project command candidates。 |
| `tools/knowledge-owner-gates.sh` | owner decision form 增加 `read_only_prefill_candidates`，但正式 owner 字段仍保持人工填写。 |
| `tools/knowledge-status.sh` | 在 `owner_gates.owner_dispatch[]`、next open 和 strict blocker commands 中暴露 evidence-readiness 恢复命令。 |
| `tools/knowledge-regression.sh` | 增加 `owner-prefill-candidates-manual-fields` 和 `owner-evidence-readiness` 回归，并扩展 status owner 命令断言。 |
| `README.md`、`tools/README.md` | 补充 owner evidence readiness 的人工使用路径和边界说明。 |
| `artifacts/manifests/knowledge-hub-governance-regression-helper-20260619.md` | 回归 helper coverage 从 68 个场景更新到 70 个场景。 |

## Owner 字段边界

`read_only_prefill_candidates` 只给候选值：

- `source_sha256_candidate` 和 `source_size_candidate` 来自 `observed_source_identity`。
- `review_after_candidate` 来自 worksheet。
- `evidence_ref_candidates` 来自 owner-ready package 的只读 evidence refs。
- `field_readiness` 说明每个 required field 是机械可查、枚举选择、证据候选还是 owner 必填。

正式字段仍由 owner 人工填写：

- `owner_decision`
- `target_decision`
- `reviewed_by`
- `reviewed_at`
- `source_sha256`
- `source_size`
- `evidence_refs`
- `status_reason`

## Evidence Index

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
|---|---:|---|---|---|---|
| `rtk bash -n tools/knowledge-owner-gates.sh` | 0 | 通过；shell/Python wrapper 语法有效 | `tools/knowledge-owner-gates.sh` | Tool | `knowledge-hub-owner-evidence-readiness-20260621` |
| `rtk bash -n tools/knowledge-status.sh` | 0 | 通过；status wrapper 语法有效 | `tools/knowledge-status.sh` | Tool | `knowledge-hub-owner-evidence-readiness-20260621` |
| `rtk bash -n tools/knowledge-regression.sh` | 0 | 通过；regression wrapper 语法有效 | `tools/knowledge-regression.sh` | Tool | `knowledge-hub-owner-evidence-readiness-20260621` |
| `rtk bash tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --worksheet-id pcr02-owner-decision-worksheet-001 --evidence-readiness --json` | 0 | 通过；`evidence_readiness.status=ready-for-owner-review`，但 row 仍为 open，正式 owner 字段未填写 | `tools/knowledge-owner-gates.sh` | Owner Gate | `knowledge-hub-owner-evidence-readiness-20260621` |
| `rtk bash tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --worksheet-id pcr02-owner-decision-worksheet-001 --forms --json` | 0 | 通过；form 包含 `read_only_prefill_candidates`，`owner_decision/source_sha256/source_size` 仍为空 | `tools/knowledge-owner-gates.sh` | Owner Gate | `knowledge-hub-owner-evidence-readiness-20260621` |
| `rtk bash tools/knowledge-status.sh --json` | 0 | 通过；`owner_gates.owner_dispatch[]`、`next_open` 和 strict blocker commands 暴露 evidence-readiness 命令，整体状态仍为 `needs-owner-review` | `tools/knowledge-status.sh` | Status | `knowledge-hub-owner-evidence-readiness-20260621` |
| `rtk bash tools/knowledge-regression.sh --json` | 0 | 通过；70 个回归场景全部 pass，包含 owner prefill candidates 和 owner evidence readiness | `tools/knowledge-regression.sh` | Regression | `knowledge-hub-owner-evidence-readiness-20260621` |

## 后续

下一轮可继续选择非 owner blocker 增强项，例如 `source_check_health` 或 manifest unpaired 分类；也可以在 owner 真正返回 JSONL 后走 `--validate-forms` 与 `--landing-plan`，但仍必须人工落地 registry、migration 和索引。

## 边界

- 不生成 owner decision。
- 不关闭 PCR02 owner gate。
- 不修改源项目 docs。
- 不复制 source 正文。
- 不提升 PCR02 project-specific 内容到 `domains/embedded/standards/`。
- 不启用写自动化。
- 不写 `~/.codex/memories`。
