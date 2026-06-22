# Knowledge Hub source check snapshot evidence and readability hardening 2026-06-22

## 结论

本轮继续压实 Knowledge Hub 终态恢复证据和中文长期资产可读性，处理 2 个非 owner 切片：

- `knowledge-status.sh --json` 新增 `sources.source_check_execution_snapshot`，只读汇总既有 PCR02 Level 2 source check 手动快照。
- `knowledge-final-gate.sh --json` 新增 `source_check_execution_snapshot_20260621`，并在 Level 2 source audit 和 `evidence_index` 中暴露快照证据。
- `knowledge-regression.sh` 扩展 status/final gate 断言，固定快照是并列证据，且 `source_check_health.executed` 仍为 `false`。
- `indexes/by-decision.md`、`indexes/by-source.md` 和 `indexes/by-status.md` 中文化当前恢复入口的高优先级英文残留。

## 变更范围

| 文件 | 变更 |
|---|---|
| `tools/knowledge-status.sh` | 输出 PCR02 Level 2 source check 快照只读摘要；不执行 source check。 |
| `tools/knowledge-final-gate.sh` | 输出 `source_check_execution_snapshot_20260621`，并加入 Level 2 audit 和 evidence index。 |
| `tools/knowledge-regression.sh` | 断言 status/final gate 快照摘要通过，同时保持 `source_check_health` 静态契约。 |
| `indexes/by-decision.md` | 中文化 owner review、owner-ready 和终态决策恢复说明。 |
| `indexes/by-source.md` | 中文化 source 治理恢复和 source-specific 审查制品说明。 |
| `indexes/by-status.md` | 中文化 2026-06-21 之后的高优先级 status 恢复行，并登记本轮制品。 |

## 快照语义

`source_check_execution_snapshot_20260621` 只说明 `artifacts/manifests/pcr02-level2-source-check-execution-snapshot-20260621.jsonl` 中 7 条 report-only 手动检查在 2026-06-21 均为 `exit_code=0`。

它不代表：

- source 正文内容正确。
- source 语义可迁移。
- owner 已签收。
- owner gate 可关闭。
- active promotion 可成立。
- `source_check_health` 改为 runtime 执行。

## 边界

- 不实时执行 registry source check。
- 不生成 owner decision。
- 不关闭 PCR02 owner gate。
- 不修改 PCR02 源项目文件。
- 不复制 owner-gated source 正文。
- 不把 PCR02 project-specific 内容提升到 `domains/embedded/standards/`。
- 不启用自动化写操作。
- 不写 `~/.codex/memories`。

## Evidence Index

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
|---|---:|---|---|---|---|
| `rtk bash -n tools/knowledge-status.sh` | 0 | 通过；status 新增快照摘要逻辑语法可解析。 | `tools/knowledge-status.sh` | Tool | `knowledge-hub-source-check-snapshot-evidence-readability-20260622` |
| `rtk bash -n tools/knowledge-final-gate.sh` | 0 | 通过；final gate 新增快照摘要逻辑语法可解析。 | `tools/knowledge-final-gate.sh` | Tool | `knowledge-hub-source-check-snapshot-evidence-readability-20260622` |
| `rtk bash -n tools/knowledge-regression.sh` | 0 | 通过；回归新增 status/final gate 快照摘要断言。 | `tools/knowledge-regression.sh` | Tool | `knowledge-hub-source-check-snapshot-evidence-readability-20260622` |
| `rtk bash tools/knowledge-status.sh --json --as-of 2026-06-22` | 0 | 预期通过；`sources.source_check_execution_snapshot.status=pass`，`runtime_execution=false`。 | `tools/knowledge-status.sh` | Status | `knowledge-hub-source-check-snapshot-evidence-readability-20260622` |
| `rtk bash tools/knowledge-final-gate.sh --json --as-of 2026-06-22` | 1 | 预期停在 owner-review；快照摘要 pass，唯一 blocker 仍是 7 个 owner gate。 | `tools/knowledge-final-gate.sh` | Final Gate | `knowledge-hub-source-check-snapshot-evidence-readability-20260622` |
| `rtk rg -n 'documented by\|is tracked by\|are tracked by\|remains ' indexes/by-source.md indexes/by-decision.md` | 1 | 通过；本轮目标 source/decision 索引旧式英文句式已清理。 | `indexes/by-source.md`; `indexes/by-decision.md` | Readability Gate | `knowledge-hub-source-check-snapshot-evidence-readability-20260622` |

## 终态说明

本轮没有改变真实终态：自动治理继续保持 `complete-except-owner-review`，剩余 7 个 PCR02 owner gate 仍需人工 owner decision。Codex 不得代签、不得代填 `reviewed_by`、不得关闭 owner gate。
