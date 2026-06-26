# Knowledge Hub Item Explain Diagnostic 2026-06-19

## 目标

为人工维护者提供一个低复杂度、只读的 item 级诊断入口。维护者在新增或修复知识条目时，可以用 `knowledge-check --explain <item-id>` 快速看到 registry 摘要、正文路径状态、核心索引登记状态和下一步人工维护提示，减少在多个 registry/index 文件之间手工排查的成本。

## 问题地图

| ID | 问题 | 风险 | 处理 |
| --- | --- | --- | --- |
| IED-001 | `knowledge-check` 默认输出全仓错误，缺少单个 item 的维护定位信息。 | 人工新增或修复条目时需要反复翻 registry 和核心索引，维护成本上升。 | 增加 `--explain <item-id>` 只读诊断输出。 |
| IED-002 | 核心索引缺失、重复或状态 bucket 错误的定位点分散。 | 人工修复容易改错文件或漏改。 | explain 输出 `by-owner`、`by-review-date`、`by-status` 引用计数和维护提示。 |
| IED-003 | 自动修复或索引生成器可能引入额外复杂度。 | 长期维护变成依赖工具链，人工添加内容反而更难。 | 本轮只做诊断，不写文件、不生成索引、不执行 `validation_refs`。 |

## 决策

- `knowledge-check.sh` 新增 `--explain <item-id>` 参数。
- explain 结果在 `--json` 模式下进入 `result.explain`；非 JSON 模式输出简短文本段。
- explain 覆盖 registry 基础字段、正文路径存在性、`tags` 与 `validation_refs` 数量、核心索引引用计数和 `by-status` bucket。
- 未找到 item 时返回失败，并输出 `explain:<item-id> item not found`。
- `--sources-only` 与 `--explain` 同时使用时不执行 item 解释，仅给 warning，保持 sources-only 的轻量边界。

## 非目标

- 不自动修改 registry、index、manifest 或正文。
- 不引入索引生成器。
- 不执行 `validation_refs`。
- 不改变默认 `knowledge-check` 全仓门禁行为。
- 不修改源项目 docs。
- 不启用自动化。
- 不写入 `~/.codex/memories`。

## 验证计划

- `rtk bash -n tools/knowledge-check.sh`
- `rtk bash tools/knowledge-check.sh --dry-run --json`
- `rtk bash tools/knowledge-check.sh --sources-only --dry-run --json`
- `rtk bash tools/knowledge-check.sh --dry-run --json --explain knowledge-hub-manual-entry-freshness-gate-20260619`
- `rtk bash tools/knowledge-check.sh --dry-run --explain knowledge-hub-manual-entry-freshness-gate-20260619`
- `/tmp` 负向验证：复制仓库后从 `indexes/by-owner.md` 删除目标 id，`--explain` 应显示该索引 `missing` 并给出维护提示。
- 负向验证：解释不存在的 item，应返回 `explain:<item-id> item not found`。
- `rtk jq -c . artifacts/manifests/knowledge-hub-item-explain-diagnostic-20260619.jsonl`
- `rtk jq -c . registry/items.jsonl`
- `rtk jq -c . registry/items.jsonl`
- `rtk bash tools/knowledge-search.sh item-explain-diagnostic-applied --json`
- `rtk git diff --check`

## 结果

- `rtk bash -n tools/knowledge-check.sh`：通过。
- `rtk bash tools/knowledge-check.sh --dry-run --json`：通过，`status=pass`。
- `rtk bash tools/knowledge-check.sh --sources-only --dry-run --json`：通过，`status=pass`。
- `rtk bash tools/knowledge-check.sh --dry-run --json --explain knowledge-hub-manual-entry-freshness-gate-20260619`：通过，输出 registry 摘要、`path_exists=true`、三个核心索引均 `status=ok`，`by-status` bucket 为 `reviewing`。
- `rtk bash tools/knowledge-check.sh --dry-run --explain knowledge-hub-manual-entry-freshness-gate-20260619`：通过，非 JSON 输出可读诊断段。
- `/tmp/kh-ied-neg-owner.csYZhp` 负向验证：删除 `indexes/by-owner.md` 中目标 id 后，`knowledge-check` 报 `index:indexes/by-owner.md missing item knowledge-hub-manual-entry-freshness-gate-20260619 (owner=leiwenjun)`，`explain.indexes["indexes/by-owner.md"].status=missing`，并给出补登记提示。
- 负向验证：`rtk bash tools/knowledge-check.sh --dry-run --json --explain does-not-exist-for-diagnostic` 返回失败，并报 `explain:does-not-exist-for-diagnostic item not found`。
- `rtk bash tools/knowledge-check.sh --sources-only --dry-run --json --explain knowledge-hub-root`：通过，输出 warning 说明 `--sources-only` 下忽略 `--explain`。
- `rtk jq -c . artifacts/manifests/knowledge-hub-item-explain-diagnostic-20260619.jsonl`：通过。
- `rtk jq -c . registry/items.jsonl`：通过。
- `rtk jq -c . registry/items.jsonl`：通过。
- `rtk bash tools/knowledge-search.sh item-explain-diagnostic-applied --json`：通过，返回 3 条可发现结果。
- `rtk git diff --check`：通过。
