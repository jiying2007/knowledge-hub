# Knowledge Hub source selection and owner warning 2026-06-21

## 结论

本轮压实两个低风险维护边界：

- latest source coverage 只从 `knowledge-hub-source-coverage-closeout-YYYYMMDD.jsonl` 日期候选中选择，非日期候选进入 `ignored_non_date_candidates`，避免 `latest/current` 等文件名被静默误选。
- `knowledge-new.sh --source` 在人工 source 草稿阶段检查 `--owner` 是否已登记到 `registry/owners.json`。未知 owner 只输出中文 warning，不阻断草稿生成；正式落盘仍由 `knowledge-check` 的 source owner gate 拦截。

当前 PCR02 7 个 owner gate 仍保持 open；本轮没有生成 owner decision、没有关闭 gate、没有修改源项目 docs、没有启用自动化写操作，也没有写 memory。

## 变更范围

| 路径 | 变更 |
| --- | --- |
| `tools/knowledge-check.sh` | 增加 `filename-yyyymmdd-sort-last` selector，暴露 dated/ignored candidates；非日期候选 warning，不参与选择。 |
| `tools/knowledge-status.sh` | 与 `knowledge-check` 使用同一 selection 语义，status JSON 暴露 dated/ignored candidates。 |
| `tools/knowledge-index-plan.sh` | source index planning 使用日期候选选择 latest coverage，并在 warnings 中提示非日期候选。 |
| `tools/knowledge-new.sh` | source 草稿输出 `owner_registry_status`；未知 owner 输出 `owner_warning_zh`。 |
| `tools/knowledge-regression.sh` | 新增非日期 closeout negative fixture 和 source unknown-owner warning 正向契约。 |
| `tools/README.md`、相关历史治理 manifest | 同步 source coverage selection 和 source owner warning 的维护说明。 |

## 回归契约

| ID | 类型 | 预期 |
| --- | --- | --- |
| `source-coverage-date-filename-selection` | negative fixture | 临时副本新增 `knowledge-hub-source-coverage-closeout-latest.jsonl` 后，check/status/index-plan 仍选择 20260620 日期 closeout，并把 latest 候选列入 ignored metadata。 |
| `source-manual-entry-unknown-owner-warning` | positive contract | `knowledge-new.sh --source --owner unknown-source-owner` exit 0，输出草稿和 `owner_registry_status=unknown-owner`，提示先补 `registry/owners.json`。 |

## Evidence Index

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
| --- | ---: | --- | --- | --- | --- |
| `rtk bash -n tools/knowledge-check.sh` | 0 | 通过；source coverage selector 语法有效。 | `tools/knowledge-check.sh` | Tool | `knowledge-hub-source-selection-owner-warning-20260621` |
| `rtk bash -n tools/knowledge-status.sh` | 0 | 通过；status selector 语法有效。 | `tools/knowledge-status.sh` | Tool | `knowledge-hub-source-selection-owner-warning-20260621` |
| `rtk bash -n tools/knowledge-index-plan.sh` | 0 | 通过；index-plan selector 语法有效。 | `tools/knowledge-index-plan.sh` | Tool | `knowledge-hub-source-selection-owner-warning-20260621` |
| `rtk bash -n tools/knowledge-new.sh` | 0 | 通过；source owner warning 语法有效。 | `tools/knowledge-new.sh` | Tool | `knowledge-hub-source-selection-owner-warning-20260621` |
| `rtk bash -n tools/knowledge-regression.sh` | 0 | 通过；新增回归函数语法有效。 | `tools/knowledge-regression.sh` | Tool | `knowledge-hub-source-selection-owner-warning-20260621` |
| `rtk bash tools/knowledge-new.sh --source --source-id example-source-owner-warning --source-path /tmp/example-owner-warning --role project-current-docs-source --authority legacy-project-current-docs --write-policy read-only-unless-explicitly-approved --check "rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run" --owner unknown-source-owner` | 0 | 通过；输出 `owner_registry_status: unknown-owner` 和中文 warning，仍生成人工草稿。 | `tools/knowledge-new.sh` | Tool | `knowledge-hub-source-selection-owner-warning-20260621` |
| `rtk bash tools/knowledge-index-plan.sh --section source --json` | 0 | 通过；latest coverage 选中 `knowledge-hub-source-coverage-closeout-20260620.jsonl`，dated candidate 为 2，ignored candidate 为空。 | `tools/knowledge-index-plan.sh` | Tool | `knowledge-hub-source-selection-owner-warning-20260621` |
| `rtk bash tools/knowledge-check.sh --dry-run --json --diagnostics` | 0 | 通过；0 errors / 0 warnings，source coverage health 仍为 13/13。 | `tools/knowledge-check.sh` | Knowledge Hub | `knowledge-hub-source-selection-owner-warning-20260621` |
| `rtk bash tools/knowledge-regression.sh --json` | 0 | 通过；68 个回归场景全部 pass，包含 `source-coverage-date-filename-selection` 和 `source-manual-entry-unknown-owner-warning`。 | `tools/knowledge-regression.sh` | Regression | `knowledge-hub-source-selection-owner-warning-20260621` |
| `rtk bash tools/knowledge-final-gate.sh --json` | 1 | 预期返回 `needs-owner-review`；`automatic_governance.status=complete-except-owner-review`，核心检查、68 个回归和 `git diff --check` 通过，唯一 blocker 是 7 个 owner gate。 | `tools/knowledge-final-gate.sh` | Terminal Gate | `knowledge-hub-source-selection-owner-warning-20260621` |

## 边界

- 不修改 PCR02 源项目 docs 或其他 source 正文。
- 不复制 source 正文，不新增 active fact。
- 不生成 owner decision，不关闭 owner gate，不把 routing/registry owner 当作 reviewed_by。
- 不提升 PCR02 project-specific 内容到 `domains/embedded/standards/`。
- 不启用自动化写操作，不写 `~/.codex/memories`。
- 对未知 owner 只做草稿阶段 warning；正式落盘仍以 `knowledge-check` 为准。
