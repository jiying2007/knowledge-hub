# Knowledge Hub owner handoff 与 manifest profile advisory 加固 2026-06-23

## 结论

本轮把两个会影响终态维护成本的非 owner gap 收口：

- owner gate 增加可发现的一包化只读 handoff 入口：`--handoff-packet --json`。
- manifest profile 中缺少 `boundaries` 字段的恢复提示从硬失败式 `missing-boundary` 改为 `advisory-missing-boundary`。

这些变化只降低人工签收和恢复误读成本，不生成 owner decision、不关闭 owner gate、不修改 PCR02 源项目、不写 memory、不启用自动化写操作。

## 终态差距地图

| gap_id | gap_type | 当前影响 | 本轮动作 | 状态 |
|---|---|---|---|---|
| owner-handoff-one-shot-discoverability | manual-maintenance / owner-review | owner 需要在 inbox、summary、evidence-readiness、forms-jsonl、validate、landing-plan、landing-audit 多个命令间切换 | 在 `knowledge-owner-gates.sh` 输出 `owner_handoff_packets[]`，并在 `knowledge-status.sh` 暴露 `handoff_packet_json_command` | applied |
| owner-handoff-json-contract | tooling / regression | `--handoff-packet` 不带 `--json` 时可能退出 0 但只输出普通文本板 | 要求 `--handoff-packet` 必须搭配 `--json`，并用回归固定 | applied |
| manifest-profile-boundary-advisory | manifest / Chinese-readability | `missing-boundary` 容易被中文维护者误读为硬失败 | 改为 `advisory-missing-boundary`，文档说明 `advisory-*` 只是人工补强方向 | applied |

## 改动范围

- `tools/knowledge-owner-gates.sh`
  - 新增只读 `--handoff-packet --json`。
  - packet 包含 owner inbox、evidence readiness、forms JSONL lines、owner checklists、命令序列和 guardrails。
  - 不带 `--json` 时返回参数错误，避免消费方误读普通文本输出。
- `tools/knowledge-status.sh`
  - 在 `owner_dispatch[]` 增加 `handoff_packet_json_command`。
- `tools/knowledge-index-plan.sh`
  - 将缺少 boundaries 的 profile health 改为 `advisory-missing-boundary`。
- `tools/knowledge-regression.sh`
  - 新增 `owner-handoff-packet-json` 和 `manifest-profile-boundary-advisory` 回归。
  - 当前回归当次捕获覆盖扩展到 119 项。
- `README.md`、`tools/README.md`、`indexes/README.md`
  - 补中文可发现性和 advisory 语义说明。

## 边界

- 不生成 `owner_decision`。
- 不代填 `reviewed_by`、`reviewed_at`、`source_sha256` 或 `source_size`。
- 不关闭 owner gate。
- 不复制 owner-gated 正文。
- 不修改 PCR02 源项目。
- 不提升 PCR02 project-specific 内容到 `domains/embedded/standards/`。
- 不写 `~/.codex/memories`。
- 自动化仍保持 read-only / report-only。

## 验证证据

| Command | Exit/Status | Result Summary |
|---|---:|---|
| `rtk bash -n tools/knowledge-owner-gates.sh` | 0 | shell 语法通过 |
| `rtk bash -n tools/knowledge-status.sh` | 0 | shell 语法通过 |
| `rtk bash -n tools/knowledge-index-plan.sh` | 0 | shell 语法通过 |
| `rtk bash -n tools/knowledge-regression.sh` | 0 | shell 语法通过 |
| `rtk bash tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --owner project-owner --handoff-packet` | 2 | 预期参数错误；`--handoff-packet` 必须带 `--json` |
| `rtk bash tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --owner project-owner --handoff-packet --json` | 0 | 输出 1 个 project-owner packet，覆盖 2 条 open gate；不生成 decision |
| `rtk bash tools/knowledge-check.sh --dry-run --json --diagnostics --as-of 2026-06-23` | 0 | 通过；0 errors、0 warnings |
| `rtk bash tools/knowledge-regression.sh --json --as-of 2026-06-23` | 0 | 通过；当次捕获 119 个回归场景全部 pass |
| `rtk git diff --check` | 0 | 通过；无 whitespace error |
| `rtk bash tools/knowledge-final-gate.sh --json --as-of 2026-06-23` | needs-owner-review | 终态门禁只剩 `owner-gates-open`：7 个 open gate，owner-ready 覆盖 7/7，active exposure 0 |

## 剩余状态

非 owner 自动治理面继续向终态收敛；剩余 PCR02 docs owner gate 仍需要真实 owner decision。当前 packet 只是降低 owner 接手成本，不能替代签收。
