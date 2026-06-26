# Knowledge Hub Check Diagnostics 2026-06-19

## 目标

让 `knowledge-check` 的失败原因更适合中文开发人员和人工维护者阅读。新增 `--diagnostics` 只读输出，把原始 errors 按 registry、source、migration、template、manual-entry、item、index、secret、explain 等类别汇总为中文摘要、数量、示例和修复提示，降低从全仓门禁失败到定位修复文件的成本。

## 问题地图

| ID | 问题 | 风险 | 处理 |
| --- | --- | --- | --- |
| KCD-001 | `knowledge-check` 失败时只有原始错误行，维护者需要理解所有内部错误格式。 | 人工维护门槛变高，修复顺序不清晰。 | 增加 `--diagnostics` 中文分类摘要。 |
| KCD-002 | 同类错误可能分散在多处，例如 item 字段、validation_refs、核心索引。 | 维护者可能先修低优先级问题，导致反复运行。 | diagnostics 输出 category、count、examples 和 action_zh。 |
| KCD-003 | 自动修复会提高风险和维护复杂度。 | 工具可能覆盖人工判断，产生新漂移。 | 本轮只做只读分类，不改文件、不生成索引、不改变退出码。 |

## 决策

- `knowledge-check.sh` 新增 `--diagnostics` 参数。
- `--diagnostics --json` 在结果中增加 `diagnostics` 对象。
- 非 JSON 输出中追加 `diagnostics:` 可读段。
- diagnostics 不改变 `status`、`errors`、`warnings` 或退出码。
- diagnostics 只取原始错误的前 5 条示例，避免输出过长。

## 非目标

- 不自动修复 registry、index、template、manifest 或正文。
- 不引入索引生成器。
- 不隐藏或改写原始 errors。
- 不执行 `validation_refs`。
- 不修改源项目 docs。
- 不启用自动化。
- 不写入 `~/.codex/memories`。

## 验证计划

- `rtk bash -n tools/knowledge-check.sh`
- `rtk bash tools/knowledge-check.sh --dry-run --json --diagnostics`
- `rtk bash tools/knowledge-check.sh --dry-run --diagnostics`
- `rtk bash tools/knowledge-check.sh --sources-only --dry-run --json --diagnostics`
- `/tmp` 负向验证：复制最小工作树后删除 `indexes/by-owner.md` 中目标 id，`--diagnostics` 应返回 `core-index` 分类和中文 action。
- `/tmp` 负向验证：复制最小工作树后从 `tools/knowledge-new.sh` 删除 `promotion`，`--diagnostics` 应返回 `manual-entry` 分类和中文 action。
- `/tmp` 负向验证：复制最小工作树后从 `registry/items.jsonl` 注入无效 `validation_refs`，`--diagnostics` 应返回 `validation-ref` 分类和中文 action。
- `rtk jq -c . artifacts/manifests/knowledge-hub-check-diagnostics-20260619.jsonl`
- `rtk jq -c . registry/items.jsonl`
- `rtk jq -c . registry/items.jsonl`
- `rtk bash tools/knowledge-check.sh --dry-run --json`
- `rtk bash tools/knowledge-search.sh check-diagnostics-applied --json`
- `rtk git diff --check`

## 结果

- `rtk bash -n tools/knowledge-check.sh`：通过。
- `rtk bash tools/knowledge-check.sh --dry-run --json --diagnostics`：通过，`status=pass`，`diagnostics.summary_zh` 为 0 错误、0 警告。
- `rtk bash tools/knowledge-check.sh --dry-run --diagnostics`：通过，非 JSON 输出包含 `diagnostics:` 可读段。
- `rtk bash tools/knowledge-check.sh --sources-only --dry-run --json --diagnostics`：通过，`status=pass`。
- `/tmp/kh-kcd-index.JopY3T` 负向验证：删除 `indexes/by-owner.md` 中 `knowledge-hub-check-diagnostics-20260619` 后，`diagnostics.categories[0].id=core-index`，并给出同步核心索引的中文 action。
- `/tmp/kh-kcd-manual.Xsywux` 负向验证：从 `tools/knowledge-new.sh` 删除 `promotion` 后，`diagnostics.categories[0].id=manual-entry`，并给出同步人工入口提示的中文 action。
- `/tmp/kh-kcd-validation.kXlc4N` 负向验证：向 `registry/items.jsonl` 注入无效 `validation_refs` 后，`diagnostics.categories[0].id=validation-ref`，并给出检查 `validation_refs` 的中文 action。
- `rtk jq -c . artifacts/manifests/knowledge-hub-check-diagnostics-20260619.jsonl`：通过。
- `rtk jq -c . registry/items.jsonl`：通过。
- `rtk jq -c . registry/items.jsonl`：通过。
- `rtk bash tools/knowledge-check.sh --dry-run --json`：通过，`status=pass`。
- `rtk bash tools/knowledge-search.sh check-diagnostics-applied --json`：通过，返回 3 条可发现结果。
- `rtk git diff --check`：通过。
