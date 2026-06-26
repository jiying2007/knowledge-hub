# Knowledge Hub Manual Entry Freshness Gate 2026-06-19

## 目标

让人工新增入口持续跟随当前 registry、template 和 core index 门禁，避免维护者按 `knowledge-new.sh` 或 `templates/README.md` 操作后仍因漏写 `promotion`、`tags`、`validation_refs` 或重复索引引用而失败。

## 问题地图

| ID | 问题 | 风险 | 处理 |
| --- | --- | --- | --- |
| MEFG-001 | `knowledge-new.sh` 没有提示最近固化的 `promotion`、`tags` 和 `validation_refs` 要求。 | 人工新增条目容易漏字段，导致 registry 门禁失败。 | 更新 `knowledge-new.sh` 的最小人工步骤，并由 `knowledge-check` 检查关键门禁词。 |
| MEFG-002 | `templates/README.md` 没有同步核心索引路径和 duplicate item reference 约束。 | 人工维护索引时可能重复登记或漏登记。 | 更新模板 README，并由 `knowledge-check` 检查当前门禁词。 |
| MEFG-003 | 人工向导本身此前没有 freshness gate。 | 后续新增门禁后，人工入口可能再次变旧。 | 在 `knowledge-check` 中加入 `manual-entry` freshness check。 |

## 决策

- `knowledge-check` 默认检查 `tools/knowledge-new.sh` 和 `templates/README.md` 是否包含当前人工新增所需的关键门禁词。
- 当前关键门禁词包括 `promotion`、`tags`、`validation_refs`、核心索引路径、`registry/items.jsonl` 和 `duplicate`。
- 本门禁只检查人工入口是否覆盖关键维护点，不生成文件、不修改 registry 内容、不启用自动化。

## 非目标

- 不自动创建正文、registry 行或索引。
- 不引入索引生成器。
- 不改变已有 item owner、status、review_after 或 promotion。
- 不修改源项目 docs。
- 不启用自动化。
- 不写入 `~/.codex/memories`。

## 验证计划

- `rtk bash -n tools/knowledge-check.sh`
- `rtk bash tools/knowledge-new.sh --help`
- `rtk bash tools/knowledge-new.sh --kind decision --domain governance --id sample-manual-entry --path governance/sample-manual-entry.md`
- `rtk jq -c . registry/items.jsonl`
- `rtk jq -c . artifacts/manifests/knowledge-hub-manual-entry-freshness-gate-20260619.jsonl`
- `rtk jq -c . registry/items.jsonl`
- `rtk bash tools/knowledge-check.sh --dry-run --json`
- `/tmp` 负向验证：复制仓库后从 `tools/knowledge-new.sh` 删除 `promotion`，`knowledge-check` 应报 manual-entry missing current gate term。
- `/tmp` 负向验证：复制仓库后从 `templates/README.md` 删除 `duplicate`，`knowledge-check` 应报 manual-entry missing current gate term。
- `rtk bash tools/knowledge-search.sh manual-entry-freshness-gate-applied --json`

## 结果

- `rtk bash -n tools/knowledge-check.sh`：通过。
- `rtk bash tools/knowledge-new.sh --help`：通过，确认命令仍为只读人工清单。
- `rtk bash tools/knowledge-new.sh --kind decision --domain governance --id sample-manual-entry --path governance/sample-manual-entry.md`：通过，输出包含 `promotion`、`tags`、`validation_refs`、核心索引和 `duplicate item reference` 提示。
- `rtk jq -c . registry/items.jsonl`：通过。
- `rtk jq -c . artifacts/manifests/knowledge-hub-manual-entry-freshness-gate-20260619.jsonl`：通过。
- `rtk jq -c . registry/items.jsonl`：通过。
- `rtk bash tools/knowledge-check.sh --dry-run --json`：通过，`status=pass`。
- `rtk bash tools/knowledge-check.sh --sources-only --dry-run --json`：通过，`status=pass`。
- `/tmp/kh-mefg-neg-prom.qIDTZG` 负向验证：从 `tools/knowledge-new.sh` 移除 `promotion` 后，`knowledge-check` 报 `manual-entry:tools/knowledge-new.sh missing current gate term: promotion`。
- `/tmp/kh-mefg-neg-dup.3pbOTf` 负向验证：从 `templates/README.md` 移除 `duplicate` 后，`knowledge-check` 报 `manual-entry:templates/README.md missing current gate term: duplicate`。
- `rtk bash tools/knowledge-search.sh manual-entry-freshness-gate-applied --json`：通过，返回 3 条可发现结果。
- `rtk git diff --check`：通过。
