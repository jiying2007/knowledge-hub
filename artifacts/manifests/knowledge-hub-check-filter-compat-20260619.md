# Knowledge Hub Check Filter Compatibility 2026-06-19

## 目标

消除 `knowledge-check.sh` 的 CLI 语义漂移。脚本历史上接受 `--project` 和 `--domain` 参数，但没有实际按项目或 domain 缩小检查范围；这容易让人工或 AI 误以为只验证了某个子集。

## 问题地图

| ID | 问题 | 风险 | 处理 |
| --- | --- | --- | --- |
| CFC-001 | `--project` 参数已声明但未使用。 | 调用者可能误以为检查只覆盖某个项目。 | 保持兼容接受参数，但输出 warning，说明仍执行全仓检查。 |
| CFC-002 | `--domain` 参数已声明但未使用。 | 调用者可能误以为检查只覆盖某个 domain。 | 保持兼容接受参数，但输出 warning，说明仍执行全仓检查。 |
| CFC-003 | 直接删除参数会破坏潜在脚本兼容。 | 旧命令可能失败。 | 不删除参数，不实现半套过滤；先明确语义。 |

## 决策

- `knowledge-check.sh` 当前仍是全仓一致性门禁。
- `--project` 和 `--domain` 暂定为保留参数，不改变检查范围。
- 传入这两个参数时，结果保持可机器读取，并在 `warnings` 中记录兼容提示。
- 后续若真正需要局部检查，应另行设计过滤语义，并证明不会绕过 registry、index、template 和 safety gates。

## 非目标

- 不实现局部过滤。
- 不改变默认 `knowledge-check` 覆盖范围。
- 不修改源项目 docs。
- 不启用自动化。
- 不写入 `~/.codex/memories`。

## 验证计划

- `rtk bash -n tools/knowledge-check.sh`
- `rtk jq -c . artifacts/manifests/knowledge-hub-check-filter-compat-20260619.jsonl`
- `rtk jq -c . registry/items.jsonl`
- `rtk jq -c . registry/migrations.jsonl`
- `rtk bash tools/knowledge-check.sh --dry-run --json`
- `rtk bash tools/knowledge-check.sh --project pcr02 --domain projects/pcr02 --dry-run --json`
- `rtk bash tools/knowledge-search.sh "check-filter-compat-applied" --json`

## 结果

已落地并验证通过。

- 默认 `rtk bash tools/knowledge-check.sh --dry-run --json` 仍执行全仓检查，结果为 `pass`。
- 带 `--project pcr02 --domain projects/pcr02` 时仍执行全仓检查，结果为 `pass`，并在 `warnings` 中提示这两个参数不会缩小检查范围。
- `check-filter-compat-applied` 可通过 `knowledge-search` 回查到 registry、status index 和本 manifest。
