# Knowledge Hub README Maintenance Path Sync 2026-06-19

## 目标

让根 README 的常用命令和人工新增最短路径跟随当前维护工具链，避免新加入的 `knowledge-doctor.sh`、`--explain` 和 `--diagnostics` 只存在于 `tools/README.md`，而入口文档仍引导维护者走旧流程。

## 问题地图

| ID | 问题 | 风险 | 处理 |
| --- | --- | --- | --- |
| RMS-001 | 根 README 的常用命令未包含 `knowledge-doctor.sh`。 | 人工维护者可能不知道一条命令即可串联 diagnostics、explain 和 search。 | 在常用命令中加入 `rtk bash ~/knowledge-hub/tools/knowledge-doctor.sh --id <id>`。 |
| RMS-002 | 人工新增最短路径仍直接从 `knowledge-check` 跳到 `knowledge-search`。 | 失败时缺少 diagnostics/explain 定位步骤，维护成本上升。 | 将第 4 步改为先运行 doctor，再用 `knowledge-check` 做提交前全仓门禁。 |
| RMS-003 | 入口文档和工具文档可能再次漂移。 | 新维护者从根 README 进入时获得过期流程。 | 登记 manifest、registry、migration 和核心索引，纳入 `knowledge-check` 可发现治理。 |

## 决策

- 根 README 的常用命令加入 doctor helper。
- 人工新增最短路径优先使用 doctor 输出 diagnostics、explain 和 search。
- `knowledge-check --dry-run --json` 保留为提交前全仓门禁。
- 本次只同步入口文档，不改工具行为。

## 非目标

- 不修改源项目 docs。
- 不启用自动化。
- 不生成索引。
- 不改变 `knowledge-check`、`knowledge-new` 或 `knowledge-doctor` 的行为。
- 不写入 `~/.codex/memories`。

## 验证计划

- `rtk rg -n "knowledge-doctor|人工新增最短路径|knowledge-check.sh --dry-run --json" README.md`
- `rtk bash tools/knowledge-doctor.sh --id knowledge-hub-root`
- `rtk bash tools/knowledge-check.sh --dry-run --json`
- `rtk bash tools/knowledge-check.sh --dry-run --json --diagnostics`
- `rtk bash tools/knowledge-search.sh readme-maintenance-path-sync-applied --json`
- `rtk jq -c . artifacts/manifests/knowledge-hub-readme-maintenance-path-sync-20260619.jsonl`
- `rtk jq -c . registry/items.jsonl`
- `rtk jq -c . registry/items.jsonl`
- `rtk git diff --check`

## 结果

- `rtk rg -n "knowledge-doctor|人工新增最短路径|knowledge-check.sh --dry-run --json" README.md`：通过，根 README 已暴露 doctor 命令、人工新增路径和提交前全仓门禁。
- `rtk bash tools/knowledge-doctor.sh --id knowledge-hub-root`：通过，diagnostics、explain 和 search 均可用。
- `rtk bash tools/knowledge-check.sh --dry-run --json`：通过，`status=pass`。
- `rtk bash tools/knowledge-check.sh --dry-run --json --diagnostics`：通过，`status=pass`。
- `rtk bash tools/knowledge-search.sh readme-maintenance-path-sync-applied --json`：通过，可检索到 registry、status index 和 manifest 证据。
- `rtk jq -c . artifacts/manifests/knowledge-hub-readme-maintenance-path-sync-20260619.jsonl`：通过，JSONL 格式有效。
- `rtk jq -c . registry/items.jsonl`：通过，registry 条目格式有效。
- `rtk jq -c . registry/items.jsonl`：通过，migration 记录格式有效。
- `rtk git diff --check`：通过，无空白错误。
