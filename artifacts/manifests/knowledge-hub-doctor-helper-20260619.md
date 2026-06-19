# Knowledge Hub Doctor Helper 2026-06-19

## 目标

给人工维护者和 AI 维护流程提供一个低复杂度、只读的诊断入口。`knowledge-doctor.sh` 串联全仓 diagnostics、可选 item explain 和可选 search，减少维护者记忆多条命令的成本，同时保留失败退出码，避免把诊断误当作通过。

## 问题地图

| ID | 问题 | 风险 | 处理 |
| --- | --- | --- | --- |
| KDH-001 | 失败定位需要手动运行多条命令。 | 人工维护成本高，容易只跑一个窄检查就误判完成。 | 新增只读 `knowledge-doctor.sh` 串联推荐诊断顺序。 |
| KDH-002 | 诊断脚本如果吞掉失败退出码，会掩盖真实门禁失败。 | 自动化或人工可能误判为通过。 | doctor 保留首个失败状态作为最终退出码。 |
| KDH-003 | 诊断入口不应升级为自动修复器。 | 自动写入可能造成漂移或覆盖人工判断。 | doctor 只读运行现有工具，不创建、不修改、不提交、不提升。 |

## 决策

- 新增 `tools/knowledge-doctor.sh`。
- 默认运行 `knowledge-check.sh --dry-run --json --diagnostics`。
- 传入 `--id <item-id>` 时追加 `knowledge-check.sh --dry-run --json --explain <item-id>` 和 `knowledge-search.sh <item-id> --json`。
- 每个步骤都打印标题和状态码。
- 最终退出码为首个失败步骤的状态码；全部通过时返回 0。

## 非目标

- 不自动修复 registry、index、migration、template 或正文。
- 不生成索引。
- 不执行 `validation_refs`。
- 不改变 `knowledge-check` 默认行为。
- 不修改源项目 docs。
- 不启用自动化。
- 不写入 `~/.codex/memories`。

## 验证计划

- `rtk bash -n tools/knowledge-doctor.sh`
- `rtk bash tools/knowledge-doctor.sh --help`
- `rtk bash tools/knowledge-doctor.sh`
- `rtk bash tools/knowledge-doctor.sh --id knowledge-hub-root`
- 负向验证：`rtk bash tools/knowledge-doctor.sh --id does-not-exist-for-doctor` 应返回失败，并保留 explain 的 item not found 证据。
- `rtk bash tools/knowledge-check.sh --dry-run --json`
- `rtk bash tools/knowledge-check.sh --dry-run --json --diagnostics`
- `rtk bash tools/knowledge-search.sh doctor-helper-applied --json`
- `rtk jq -c . artifacts/manifests/knowledge-hub-doctor-helper-20260619.jsonl`
- `rtk jq -c . registry/items.jsonl`
- `rtk jq -c . registry/migrations.jsonl`
- `rtk git diff --check`

## 结果

- `rtk bash -n tools/knowledge-doctor.sh`：通过。
- `rtk bash tools/knowledge-doctor.sh --help`：通过，声明只读，不创建、不修改、不提交、不提升。
- `rtk bash tools/knowledge-doctor.sh`：通过，运行全仓 diagnostics 并返回 0。
- `rtk bash tools/knowledge-doctor.sh --id knowledge-hub-root`：通过，依次输出全仓 diagnostics、`knowledge-hub-root` explain 和 search，最终返回 0。
- 负向验证：`rtk bash tools/knowledge-doctor.sh --id does-not-exist-for-doctor` 返回 1；全仓 diagnostics 通过，但 explain 报 `explain:does-not-exist-for-doctor item not found`，最终提示诊断未通过。
- `rtk jq -c . artifacts/manifests/knowledge-hub-doctor-helper-20260619.jsonl`：通过。
- `rtk jq -c . registry/items.jsonl`：通过。
- `rtk jq -c . registry/migrations.jsonl`：通过。
- `rtk bash tools/knowledge-check.sh --dry-run --json`：通过，`status=pass`。
- `rtk bash tools/knowledge-check.sh --dry-run --json --diagnostics`：通过，`status=pass`。
- `rtk bash tools/knowledge-search.sh doctor-helper-applied --json`：通过，返回 3 条可发现结果。
- `rtk git diff --check`：通过。
