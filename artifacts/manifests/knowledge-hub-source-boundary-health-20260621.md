# Knowledge Hub source check and boundary health 2026-06-21

## 结论

本轮把终态 gate 中仍偏隐性的两个健康面显式化：

- `source_check_health`：静态审计 `registry/sources.json` 中每个 source 是否具备 `check` 或 `no_check_reason`，并阻断缺失、二者同时存在、以及非 `rtk` 开头的检查命令。
- `boundary_health`：只读取 Knowledge Hub 内部的 PCR02 Level 2 boundary manifest、registry item 和 by-source/by-project 索引，确认 7 个 candidate source 的边界证据链完整。

这两个健康面都不执行 source registry 中的 check 命令，不读取 PCR02 源项目正文，不生成 owner decision，不关闭 owner gate，不启用自动化，也不写 memory。

## 改动范围

- `tools/knowledge-check.sh`：新增顶层 `source_check_health` 和 `boundary_health`，并将 boundary 错误归入 diagnostics。
- `tools/knowledge-status.sh`：在 `sources` 看板中透传 source coverage、source check 和 boundary health。
- `tools/knowledge-final-gate.sh`：在 Level 2 / Level 3 final-state audit 中纳入 boundary/source check health，并保持 owner gate 作为唯一真实终态阻塞。
- `tools/knowledge-regression.sh`：新增 source check contract 和 boundary internal evidence 的正负向回归。
- `README.md`、`tools/README.md`、`artifacts/manifests/knowledge-hub-governance-regression-helper-20260619.md`：同步长期维护说明和 regression helper 覆盖项。

## 健康面边界

`source_check_health` 的边界：

- 只检查 registry source 的静态字段。
- 只确认命令契约是否以 `rtk` 开头。
- 不执行任何 source check 命令。
- path 缺失保留为 report-only warning，不替代 owner review。

`boundary_health` 的边界：

- 只验证 7 个已登记 PCR02 Level 2 boundary manifest 的 Markdown/JSONL、registry item 和 index 引用。
- 只消费 Knowledge Hub 内部证据，不读取 PCR02 源项目目录。
- 不修改 owner worksheet，不把 owner-gated 内容提升为 active。
- 不写 `~/.codex/memories`。

## 当前只读结果

- registered source：13
- source check：9
- no_check_reason：4
- missing check/no_check_reason：0
- non-rtk check：0
- PCR02 Level 2 boundary manifest：7/7
- boundary JSONL rows：78
- boundary hard failures：0

## Evidence Index

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
|---|---:|---|---|---|---|
| `rtk bash -n tools/knowledge-check.sh` | 0 | 语法检查通过，source/boundary health 路径可解析 | `tools/knowledge-check.sh` | Tool | `knowledge-hub-source-boundary-health-20260621` |
| `rtk bash -n tools/knowledge-status.sh` | 0 | 语法检查通过，status source health 透传路径可解析 | `tools/knowledge-status.sh` | Tool | `knowledge-hub-source-boundary-health-20260621` |
| `rtk bash -n tools/knowledge-final-gate.sh` | 0 | 语法检查通过，final-state audit source/boundary 字段可解析 | `tools/knowledge-final-gate.sh` | Tool | `knowledge-hub-source-boundary-health-20260621` |
| `rtk bash -n tools/knowledge-regression.sh` | 0 | 语法检查通过，新增正负向回归场景可解析 | `tools/knowledge-regression.sh` | Tool | `knowledge-hub-source-boundary-health-20260621` |
| `rtk bash tools/knowledge-check.sh --dry-run --json --diagnostics` | 0 | `source_check_health` 与 `boundary_health` 均为 pass | `tools/knowledge-check.sh` | Gate | `knowledge-hub-source-boundary-health-20260621` |
| `rtk bash tools/knowledge-regression.sh --json` | 0 | regression 覆盖 72 个场景，新增 source check 和 boundary 场景通过 | `tools/knowledge-regression.sh` | Regression | `knowledge-hub-source-boundary-health-20260621` |
| `rtk git diff --check` | 0 | 未发现 whitespace 或 conflict marker 漂移 | git diff check | Git | `knowledge-hub-source-boundary-health-20260621` |
| `rtk bash tools/knowledge-final-gate.sh --json` | 1 | 终态 gate 预期停在 `needs-owner-review`；工具、registry、source/boundary health 和 regression 均通过 | `tools/knowledge-final-gate.sh` | Final Gate | `knowledge-hub-source-boundary-health-20260621` |

## 后续

1. 若新增 source，必须提供 `check` 或 `no_check_reason`；有 `check` 时必须使用 `rtk` 开头。
2. 若新增 PCR02 Level 2 boundary source，必须同步 Markdown/JSONL manifest、registry item、by-source 和 by-project 索引。
3. 真正终态仍取决于 7 个 PCR02 owner gate 的人工决策，不由本健康面自动关闭。
