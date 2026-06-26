# Knowledge Hub Manual Entry Copyable Skeleton 2026-06-19

## 目标

降低人工新增知识条目的重复查表成本。`knowledge-new.sh` 在保持只读的前提下，输出可复制的 `registry/items.jsonl` 草稿、核心索引登记提示、`registry/items.jsonl` 草稿和验证命令，帮助人工维护者按当前 schema 和门禁一次性补齐关键字段。

## 问题地图

| ID | 问题 | 风险 | 处理 |
| --- | --- | --- | --- |
| MCS-001 | 人工新增 item 时需要在 schema、模板、索引和 migration 之间反复切换。 | 容易漏 `promotion`、`tags`、`validation_refs`、核心索引或 migration。 | `knowledge-new.sh` 输出可复制草稿和验证命令。 |
| MCS-002 | 项目域 item 的 `scope` 容易误填为团队通用。 | project-specific 内容可能被错误提升或分类。 | 当 `--domain projects/<project>` 时，草稿默认 `scope=project-specific`。 |
| MCS-003 | `by-status` 容易新增重复 bucket。 | 核心索引漂移或重复引用。 | 输出明确提示把 id 追加到现有 `- reviewing:` 行。 |
| MCS-004 | 项目域 item 容易只补 registry 和核心 status 索引，漏掉 `indexes/by-project.md`。 | 项目导航入口缺失，人工查找 PCR02 等项目知识时需要回到 registry 搜索。 | `knowledge-new.sh` 仅对项目域输出项目索引提示，回归覆盖 PCR02 项目条目示例和 governance 非项目示例。 |

## 决策

- `knowledge-new.sh` 继续只读，不创建、不修改、不提交任何文件。
- `registry/items.jsonl` 草稿包含当前必填字段、`promotion=none`、`tags`、`validation_refs` 和日期占位符。
- 项目域默认生成 `scope=project-specific`；其他域默认 `scope=team-general`。
- 核心索引草稿提示 `by-owner`、`by-review-date` 和 `by-status` 的人工登记位置；仅项目域条目额外提示 `by-project` 导航入口。
- 验证命令包含默认全仓检查、`--explain <id>`、`--diagnostics` 和搜索。

## 非目标

- 不自动创建正文、registry 行、索引或 migration。
- 不引入索引生成器。
- 不执行 `validation_refs`。
- 不改变 `knowledge-check` 门禁。
- 不修改源项目 docs。
- 不启用自动化。
- 不写入 `~/.codex/memories`。

## 验证计划

- `rtk bash -n tools/knowledge-new.sh`
- `rtk bash tools/knowledge-new.sh --help`
- `rtk bash tools/knowledge-new.sh --kind decision --domain governance --id sample-manual-entry --path governance/sample-manual-entry.md`
- `rtk bash tools/knowledge-new.sh --kind runbook --domain projects/pcr02 --project pcr02 --id pcr02-sample --path domains/projects/pcr02/current/runbooks/pcr02-sample.md`
- `rtk bash tools/knowledge-regression.sh --json`
- `/tmp` 验证：从 governance 示例输出中抽取 registry JSON 草稿，替换日期和标题占位符后应可被 `jq` 解析，并包含 `scope=team-general`。
- `/tmp` 验证：从 PCR02 示例输出中抽取 registry JSON 草稿，替换日期和标题占位符后应可被 `jq` 解析，并包含 `scope=project-specific`。
- `rtk bash tools/knowledge-check.sh --dry-run --json`
- `rtk bash tools/knowledge-check.sh --dry-run --json --diagnostics`
- `rtk bash tools/knowledge-search.sh manual-entry-copyable-skeleton-applied --json`
- `rtk git diff --check`

## 结果

- `rtk bash -n tools/knowledge-new.sh`：通过。
- `rtk bash tools/knowledge-new.sh --help`：通过，命令仍声明只读，不创建、不修改、不提交。
- `rtk bash tools/knowledge-new.sh --kind decision --domain governance --id sample-manual-entry --path governance/sample-manual-entry.md`：通过，输出 registry item 草稿、核心索引提示、source policy 草稿和验证命令；registry 草稿默认 `scope=team-general`。
- `rtk bash tools/knowledge-new.sh --kind runbook --domain projects/pcr02 --project pcr02 --id pcr02-sample --path domains/projects/pcr02/current/runbooks/pcr02-sample.md`：通过，registry 草稿默认 `scope=project-specific`。
- `rtk bash tools/knowledge-regression.sh --json`：通过，manual project entry 回归确认项目域新增向导输出 `indexes/by-project.md`，非项目域新增向导不输出项目索引草稿。
- `/tmp` 验证：从 governance 示例输出中抽取 registry JSON 草稿后，`jq -e '.scope == "team-general" and .id == "sample-manual-entry"'` 通过。
- `/tmp` 验证：从 PCR02 示例输出中抽取 registry JSON 草稿后，`jq -e '.scope == "project-specific" and .domain == "projects/pcr02"'` 通过。
- `rtk jq -c . artifacts/manifests/knowledge-hub-manual-entry-copyable-skeleton-20260619.jsonl`：通过。
- `rtk jq -c . registry/items.jsonl`：通过。
- `rtk jq -c . registry/items.jsonl`：通过。
- `rtk bash tools/knowledge-check.sh --dry-run --json`：通过，`status=pass`。
- `rtk bash tools/knowledge-check.sh --dry-run --json --diagnostics`：通过，`status=pass`。
- `rtk bash tools/knowledge-search.sh manual-entry-copyable-skeleton-applied --json`：通过，返回 3 条可发现结果。
- `rtk git diff --check`：通过。
