# Knowledge Hub owner inbox、linking 与人工维护入口加固 2026-06-23

## 结论

本轮把 owner gate 人工签收入口、跨会话 linking 恢复入口和人工维护最短路径做成更稳定的低复杂度控制面。

- `knowledge-status.sh` 在 `owner_gates.owner_dispatch[]` 中新增 `owner_inbox_json_command`，并把 `suggested_owner_packet.recommended_sequence[]` 的第一步改为 `1-open-owner-inbox`。
- `knowledge-owner-gates.sh --owner-inbox` 的人读输出新增字段分组、只读候选和表单/校验命令，减少 owner 必须跳回 JSON 查字段的成本。
- 根 `README.md`、`indexes/README.md` 和 `indexes/by-project.md` 补齐 `knowledge-index-plan.sh --section linking --json`、PCR02 `validation/` 和 manifests 恢复锚点。
- `knowledge-check.sh` 新增 manual-entry anchor 检查，防止 README、tools README 和 indexes README 的人工最短路径、linking 入口、owner-inbox 入口和离线维护入口退化。

## 证据

| 命令 | 结果 | 摘要 |
|---|---|---|
| `rtk bash -n tools/knowledge-status.sh` | pass | status 脚本语法通过。 |
| `rtk bash -n tools/knowledge-owner-gates.sh` | pass | owner gate 脚本语法通过。 |
| `rtk bash -n tools/knowledge-check.sh` | pass | knowledge-check 脚本语法通过。 |
| `rtk bash -n tools/knowledge-regression.sh` | pass | regression 脚本语法通过。 |
| `rtk bash tools/knowledge-check.sh --dry-run --json --diagnostics --as-of 2026-06-23` | pass | 新增 manual-entry anchor 检查后，知识库一致性通过，errors=0。 |
| `rtk bash tools/knowledge-status.sh --json --as-of 2026-06-23` | pass | `project-owner` 分派包含 `owner_inbox_json_command`，recommended sequence 为 7 步且第一步是 owner-inbox。 |
| `rtk bash tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --owner project-owner --owner-inbox` | pass | 人读 owner-inbox 显示字段分组、只读候选和 validate template。 |
| `rtk bash tools/knowledge-regression.sh --json --as-of 2026-06-23` | pass | 103 个 regression 场景全部通过。 |
| `rtk bash tools/knowledge-search.sh knowledge-hub-owner-inbox-linking-maintenance-hardening-20260623 --json --limit 5` | pass | 可从 registry、migration 和核心索引恢复本轮条目。 |
| `rtk bash tools/knowledge-final-gate.sh --json --as-of 2026-06-23` | owner-review | final gate 仍只剩 `owner-gates-open`；proof expected=22，selection_dynamic=2，overlap=0。 |

## 边界

- 不生成 owner decision。
- 不填写 `reviewed_by`、`reviewed_at` 或 owner 签收字段。
- 不关闭 owner gate。
- 不修改 PCR02 源项目 docs 或其他源项目文件。
- 不复制 owner-gated source 正文。
- 不把 PCR02 project-specific 内容提升到 `domains/embedded/standards/`。
- 不启用非 report-only 自动化。
- 不写 `~/.codex/memories`。

## 剩余状态

终态 gate 的唯一预期剩余 blocker 仍应是 7 个 `pcr02-project-docs` owner gate。`owner-inbox` 只是只读人工首屏入口；真实 owner 仍需自行填写 owner decision JSONL，并通过 validate / landing-plan / landing-audit 后才能进入人工落地流程。
