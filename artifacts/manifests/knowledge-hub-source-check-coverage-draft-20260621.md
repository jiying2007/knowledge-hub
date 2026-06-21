# Knowledge Hub source check coverage draft 2026-06-21

## 结论

本轮修正 `tools/knowledge-new.sh --source --check ...` 的 source coverage 草稿字段：当人工为 source 提供稳定只读 `check` 命令时，`registry/sources.json` 草稿和 source coverage JSONL row 草稿都记录 `check`，不再同时输出 JSON 形式的 `no_check_reason`。

这降低了人工复制草稿时的字段漂移风险，尤其适用于“已有可执行检查命令”的 source 登记路径。

## 范围

- `tools/knowledge-new.sh`
  - source 输入摘要在存在 `--check` 时显示 `no_check_reason: <not-required: check provided>`。
  - registry source object 草稿继续使用 `check` / `no_check_reason` 条件字段。
  - source coverage JSONL row 草稿同步使用同一组条件字段。
- `tools/knowledge-regression.sh`
  - `source-manual-entry-guide-check-command` 回归扩展为同时检查 registry object 和 coverage row 的 `check` 字段。
  - 回归断言带 `--check` 的输出不包含 JSON 形式的 `no_check_reason`。
- `artifacts/manifests/`、`registry/`、`indexes/`
  - 登记本次治理证据，便于后续人工复核。

## 不改变的边界

- 不登记新 source，不修改 `registry/sources.json`。
- 不修改 PCR02 源项目文件。
- 不复制 source 正文，不提升 active fact。
- 不生成 owner decision，不关闭 owner gate。
- 不启用自动化写操作，不写 memory。

## 维护规则

- source 有稳定只读检查命令时，优先写 `check`。
- source 暂无可执行检查命令时，才写 `no_check_reason`，并说明为什么只能先做人工 coverage。
- coverage row 只表达治理状态，不等于 owner decision 或 active fact。

## Evidence Index

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
|---|---:|---|---|---|---|
| `rtk bash -n tools/knowledge-new.sh` | 0 | 通过；source 向导脚本语法有效。 | `tools/knowledge-new.sh` | Tool | `knowledge-hub-source-check-coverage-draft-20260621` |
| `rtk bash -n tools/knowledge-regression.sh` | 0 | 通过；回归脚本语法有效。 | `tools/knowledge-regression.sh` | Tool | `knowledge-hub-source-check-coverage-draft-20260621` |
| `rtk bash tools/knowledge-new.sh --source --source-id example-source-check --source-path /tmp/example-check --role project-current-docs-source --authority legacy-project-current-docs --write-policy read-only-unless-explicitly-approved --check "rtk bash tools/knowledge-check.sh --dry-run"` | 0 | 通过；registry object 和 source coverage JSONL row 草稿均输出 `check`，JSON 草稿不输出 `no_check_reason`。 | `tools/knowledge-new.sh` | Tool | `knowledge-hub-source-check-coverage-draft-20260621` |
| `rtk bash tools/knowledge-check.sh --dry-run --json --diagnostics` | 0 | 通过；0 errors、0 warnings，确认 registry、migration 和核心索引同步正确。 | `tools/knowledge-check.sh` | Tool | `knowledge-hub-source-check-coverage-draft-20260621` |
| `rtk bash tools/knowledge-regression.sh --json` | 0 | 通过；50 个回归场景全部 pass，`source-manual-entry-guide-check-command` 覆盖 registry 与 coverage row 的 `check` 一致性。 | `tools/knowledge-regression.sh` | Tool | `knowledge-hub-source-check-coverage-draft-20260621` |
| `rtk bash tools/knowledge-final-gate.sh --json` | 1 | 预期结果；`knowledge_check=pass`、`knowledge_regression=pass`、`git_diff_check=pass`，final status 仍为 `needs-owner-review`，唯一 blocker 为 7 个人工 owner gate。 | `tools/knowledge-final-gate.sh` | Tool | `knowledge-hub-source-check-coverage-draft-20260621` |

## 最终状态

本轮自动治理切片已完成验证。Knowledge Hub 终态仍未整体 complete，因为 PCR02 `pcr02-project-docs` 仍有 7 个 owner decision worksheet 未签收；这是人工语义门禁，不能由 Codex 代签或关闭。
