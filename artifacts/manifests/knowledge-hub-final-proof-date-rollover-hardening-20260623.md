# Knowledge Hub final proof 日期滚动加固 2026-06-23

## 结论

本轮修复了 `2026-06-23` 日期推进后终态 gate 的 regression 漂移，并压缩根 README / tools README 的维护入口说明。

- 根 README 只保留低复杂度最短入口，把 owner gate、doctor、inventory、capture、promote、retire 和 landing-audit 详细示例转到 `tools/README.md`。
- `tools/README.md` 把终态 JSON 字段说明压缩为 4 组字段，降低人工恢复时的扫读成本。
- `tools/knowledge-final-gate.sh` 的 proof artifact 选择器改为保留 `2026-06-22` 基线动态治理 proof，并继续叠加当前 `--as-of` 日期的动态 proof。
- `tools/knowledge-final-gate.sh` 会显式暴露 `baseline_selection_overlap_ids`，并在非基线日期出现 baseline/selection 同 ID 重叠时让 proof fail，避免去重掩盖日期滚动冲突。
- `tools/knowledge-regression.sh` 的 owner-review blocker 断言改为日期参数化，并断言 baseline/selection proof ID 无重叠，避免把 `2026-06-22` source-check 命令硬编码成未来日期的期望。

## 证据

| 命令 | 结果 | 摘要 |
|---|---|---|
| `rtk bash -n tools/knowledge-final-gate.sh` | pass | shell 语法通过。 |
| `rtk bash -n tools/knowledge-regression.sh` | pass | shell 语法通过。 |
| `KNOWLEDGE_FINAL_GATE_INNER_REGRESSION=1 rtk bash tools/knowledge-final-gate.sh --json --as-of 2026-06-23` | owner-review | final gate 保留 20 个 baseline 动态 proof；本轮 manifest 登记后，当前日期新增 proof 为 1，总 expected proof 为 21，baseline/selection overlap 为 0，source-check runtime 命令跟随 `2026-06-23`。 |
| `rtk bash tools/knowledge-regression.sh --json --as-of 2026-06-23` | pass | 当次运行历史捕获：103 个 regression 场景全部通过；当前 live 回归数量以 `tools/knowledge-regression.sh --json` 输出为准。 |
| `rtk git diff --check` | pass | 当前 diff 无空白错误。 |
| `rtk bash tools/knowledge-check.sh --dry-run --json --diagnostics --as-of 2026-06-23` | pass | 知识库一致性检查通过，errors=0，warnings=0。 |
| `rtk bash tools/knowledge-search.sh "PCR02 OTA" --json --limit 5` | pass | 检索能恢复根 README、AGENTS 和 PCR02 OTA 归档链路。 |

## 边界

- 不生成 owner decision。
- 不关闭 owner gate。
- 不修改 PCR02 源项目 docs 或其他源项目文件。
- 不复制 owner-gated source 正文。
- 不把 PCR02 project-specific 内容提升到 `domains/embedded/standards/`。
- 不启用非 report-only 自动化。
- 不写 `~/.codex/memories`。

## 剩余状态

终态 gate 的唯一预期剩余 blocker 仍应是 7 个 `pcr02-project-docs` owner gate。该 blocker 只能由真实 owner 通过 owner decision JSONL 签收，Codex 不得代签或关闭。
