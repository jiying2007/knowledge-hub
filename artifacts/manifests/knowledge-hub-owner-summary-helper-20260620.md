# Knowledge Hub owner summary helper 2026-06-20

## 结论

`tools/knowledge-owner-gates.sh` 新增 `--summary` 只读视图，用于一次性查看当前筛选范围内的 owner gate 总览。它面向人工分派和收口，不生成 owner decision，不写文件，不关闭门禁，不提升 active。

## 问题地图

| ID | 问题 | 风险 | 处理 |
|---|---|---|---|
| OSH-001 | `--next-open` 适合逐条处理，但 owner 要排期 7 条 gate 时缺少一屏总览。 | 人工需要在长 JSON / 文本中查 owner、必填字段、source identity 和聚焦命令，容易漏项。 | 增加 `--summary` 输出 owner 分布、source identity 计数、每条 gate 的必填字段数量和聚焦命令。 |
| OSH-002 | 总览如果和 forms/checklist 混在一起，容易被误认为已经生成 owner 决策。 | owner gate 可能被误读为已关闭。 | `--summary` 默认只输出 `owner_summary`，不输出 `decision_forms` 或 `owner_checklists`。 |
| OSH-003 | 新入口如果没有回归，后续维护时可能被删除或语义漂移。 | 人工收口入口再次退化。 | 增加 `owner-summary-all-open` 回归场景，并同步 regression helper manifest 到 18 个场景。 |

## 行为

- `--summary --json` 输出 `owner_summary`。
- `owner_summary.status` 在仍有 open gate 时为 `needs-owner-review`。
- `owner_summary.source_identity_counts` 汇总当前源身份状态。
- 每条摘要包含 `focus_command`，可继续进入该 worksheet 的 `--checklist --forms` 视图。
- 该命令不填充 `source_sha256` / `source_size`，不输出 owner decision skeleton，除非显式再加 `--forms`。

## Evidence Index

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
|---|---:|---|---|---|---|
| `rtk bash tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --summary --json` | 0 | 通过；输出 7 条 open gate 摘要，`source_identity_counts.match=7`，`active_exposure_count=0`，不含 `decision_forms` 和 `owner_checklists` | `tools/knowledge-owner-gates.sh` | Tool | `knowledge-hub-owner-summary-helper-20260620` |
| `rtk bash tools/knowledge-regression.sh --json` | 0 | 通过；20 个回归场景全部 pass，包含 `owner-summary-all-open` | `tools/knowledge-regression.sh` | Tool | `knowledge-hub-owner-summary-helper-20260620` |
| `rtk bash tools/knowledge-check.sh --dry-run --json --diagnostics` | 0 | 通过；0 errors、0 warnings，确认新增 manifest、registry 和 index 登记无漂移 | `tools/knowledge-check.sh` | Tool | `knowledge-hub-owner-summary-helper-20260620` |

## 边界

- 不修改 PCR02 源项目 docs。
- 不关闭 owner gate，不生成 owner decision。
- 不把 PCR02 project-specific 内容提升到 `domains/embedded/standards/`。
- 不启用自动化，不写 `~/.codex/memories`。
- 不替代 owner review、`knowledge-check` 或 `knowledge-status --strict`。
