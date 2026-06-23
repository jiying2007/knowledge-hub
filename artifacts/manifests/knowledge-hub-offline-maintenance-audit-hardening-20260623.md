# Knowledge Hub 离线维护审计加固 2026-06-23

## 结论

本轮继续压实 Knowledge Hub 终态证据：`knowledge-final-gate.sh` 的 `maintenance_entry_audit` 从“8 类长期维护入口”扩展为“8 类长期维护入口 + 1 个离线维护包”，显式证明 `docs/goals/knowledge-hub-final-state.md` 七.2 要求的离线人工维护包可恢复。

新增的 `offline-maintenance-package` 审计条目检查：

- `README.md`：离线人工维护、`manual_validation_pending: true` 和 `required_followup`。
- `tools/README.md`：离线维护说明、`registry/schema.md` 和 `indexes/README.md`。
- `templates/README.md`：中文模板和 Evidence Index。
- `registry/schema.md`：离线最小字段、`manual-entry-pending-review` 和 `manual_validation_pending: true`。
- `indexes/README.md`：最小同步、离线待验证标记和 `knowledge-index-plan.sh --section all`。
- `tools/knowledge-new.sh`：`manual-validation-pending` / `manual-source-reason`。
- `tools/knowledge-check.sh`：`--dry-run` / `--diagnostics`。

同时，根 README 的首屏入口口径向 5 条人工最短路径靠拢，并把 source 示例的推荐 check 命令统一为 `rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics`，避免离线维护者复制到弱校验命令。

## 终态差距地图

| gap_id | gap_type | 当前影响 | 本轮动作 | 状态 |
|---|---|---|---|---|
| offline-maintenance-package-final-gate-evidence | final-gate / manual-maintenance | 离线维护包文件已存在，但 final gate 只证明 8 类长期维护入口，没有显式证明七.2 离线维护包 | 新增 `offline-maintenance-package` 审计条目，并把回归期望从 8/8 更新为 9/9 | applied |
| manual-shortest-path-first-screen-drift | Chinese-readability / manual-maintenance | 根 README 首屏入口命名与 5 条 canonical 最短路径不完全一致 | 首屏表格改为更贴近“新增一条知识 / 新增一个 source / 归档一条历史记录 / owner 签收一个 gate / 跑一次终态检查” | applied |
| source-check-copyable-example-drift | manual-maintenance / README | README、tools README 和 `knowledge-new.sh --help` 的 source check 示例可复制为较弱 `--dry-run` 命令 | 推荐示例统一为 `--dry-run --json --diagnostics`，保留工具对任意 `--check` 的原样草稿能力 | applied |
| review-queue-jsonl-flag-readability | Chinese-readability / manual-maintenance | 根 README 未直接提醒 `--queue-forms-jsonl` 是 JSONL-only，不能与 `--json` 同用 | 在根 README 的 review queue 段落补充约束说明 | applied |

## 边界

- 不生成 owner decision。
- 不关闭 owner gate。
- 不修改 PCR02 源项目。
- 不复制 owner-gated 正文。
- 不提升 PCR02 project-specific 内容到 `domains/embedded/standards/`。
- 不启用自动化写操作。
- 不写 `~/.codex/memories`。
- `maintenance_entry_audit` 只证明入口、文件和边界可恢复，不代表人工维护动作已经完成。

## 改动范围

- `tools/knowledge-final-gate.sh`
  - 新增 `offline-maintenance-package` 审计条目。
  - `maintenance_entry_audit` 摘要改为“8 类长期维护入口和 1 个离线维护包”。
- `tools/knowledge-regression.sh`
  - `final-gate-owner-review-blocker` 期望更新为 `expected_entry_count=9`、`passed_entry_count=9`。
  - 文档偏好断言更新为 diagnostics source check 示例。
- `tools/knowledge-new.sh`
  - source 示例 check 命令使用 `--dry-run --json --diagnostics`。
- `README.md`、`tools/README.md`
  - 对齐首屏人工最短路径、review queue JSONL-only 约束和 source check 推荐命令。
- `artifacts/manifests/knowledge-hub-governance-regression-helper-20260619.md`
  - 同步回归说明中的维护入口口径。

## 验证证据

| Command | Exit/Status | Result Summary |
|---|---:|---|
| `rtk bash -n tools/knowledge-final-gate.sh` | 0 | shell 语法通过 |
| `rtk bash -n tools/knowledge-regression.sh` | 0 | shell 语法通过 |
| `rtk bash -n tools/knowledge-new.sh` | 0 | shell 语法通过 |
| `rtk git diff --check` | 0 | 无 whitespace/error |
| `rtk bash tools/knowledge-check.sh --dry-run --json --diagnostics --as-of 2026-06-23` | 0 / pass | 0 error，0 warning |
| `rtk bash tools/knowledge-final-gate.sh --json --as-of 2026-06-23` | 1 / needs-owner-review | 自动治理 complete；`maintenance_entry_audit=pass 9/9`；唯一 blocker 为 `owner-gates-open`；普通 review queue 不作为 active/promotion blocker |
| `rtk bash tools/knowledge-regression.sh --json --as-of 2026-06-23` | 0 / pass | 119 项全部 pass；`final-gate-owner-review-blocker` 已验证 `maintenance_entry_audit=9/9`，`source-manual-entry-docs-check-preferred` 已验证 diagnostics 示例 |

## 剩余状态

Codex 自动治理终态仍应停在 `needs-owner-review`，且唯一 blocker 应为 `owner-gates-open`。7 个 PCR02 owner gate 仍需要真实 owner decision；本轮不代签、不关闭 gate。
