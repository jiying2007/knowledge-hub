# Knowledge Hub owner queue and command hardening 2026-06-22

## 结论

本轮继续压实 Knowledge Hub 终态恢复路径，处理 3 个自动治理切片：

- `knowledge-status --json` 增加 `owner_gates.next_open_queue[]`，按 `review_after, worksheet_id` 输出当前 7 条 open owner gate 的只读领取队列。
- `knowledge-regression.sh` 在 `status-next-owner-gate` 中锁定队列顺序、owner-ready 覆盖、前两条 worksheet 和“可执行命令不得包含 `<owner-decisions.jsonl>`”边界。
- 新增 `stable-governance-command-examples` 回归，扫描 README、tools README、templates、governance 和 indexes，防止治理文档退回 repo-relative 或短验证命令。

## 变更范围

| 文件 | 变更 |
|---|---|
| `tools/knowledge-status.sh` | 新增 `owner_gates.next_open_queue[]`、`next_open_queue_count` 和文本模式队列输出。 |
| `tools/knowledge-regression.sh` | 扩展 `status-next-owner-gate`，新增 `stable-governance-command-examples`，并把新 ID 纳入 manifest 覆盖自检。 |
| `README.md`、`tools/README.md` | 补充 `next_open_queue[]` 的恢复语义和命令边界。 |
| `indexes/by-status.md`、`templates/README.md`、`tools/README.md` | 收敛中文说明和稳定 `rtk bash ~/knowledge-hub/...` 命令示例。 |
| `artifacts/manifests/knowledge-hub-governance-regression-helper-20260619.md` | 增加 `stable-governance-command-examples` 覆盖行，并把回归总数更新为 86。 |

## 边界

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
| `rtk bash -n tools/knowledge-status.sh` | 0 | 通过；status dashboard 脚本语法检查通过。 | `tools/knowledge-status.sh` | Tool | `knowledge-hub-owner-queue-command-hardening-20260622` |
| `rtk bash -n tools/knowledge-regression.sh` | 0 | 通过；回归入口语法检查通过。 | `tools/knowledge-regression.sh` | Tool | `knowledge-hub-owner-queue-command-hardening-20260622` |
| `rtk bash tools/knowledge-status.sh --json --as-of 2026-06-22` | 0 | 通过；`owner_gates.next_open_queue_count=7`，前两条为 worksheet 001/002，可执行命令中不包含 `owner-decisions.jsonl`。 | `/tmp/kh-status-after-queue.json` | Status | `knowledge-hub-owner-queue-command-hardening-20260622` |
| `rtk rg -n 'rtk bash tools/\|`knowledge-check --dry-run\|validation_refs":\["tools/knowledge-check.sh --dry-run' README.md tools/README.md templates/README.md governance indexes` | 1 | 通过；无命中，治理文档和模板未保留相对工具命令或短验证命令示例。 | `README.md`、`tools/README.md`、`templates/README.md`、`governance/`、`indexes/` | Readability Gate | `knowledge-hub-owner-queue-command-hardening-20260622` |
| `rtk bash tools/knowledge-check.sh --dry-run --json --diagnostics --as-of 2026-06-22` | 0 | 通过；0 errors、0 warnings，source coverage latest 仍选择 `knowledge-hub-source-coverage-closeout-20260620.jsonl`，boundary health 为 pass。 | `tools/knowledge-check.sh` | Gate | `knowledge-hub-owner-queue-command-hardening-20260622` |
| `rtk bash tools/knowledge-regression.sh --json --as-of 2026-06-22` | 0 | 通过；86 个回归场景全部 pass，新增 `stable-governance-command-examples` 通过，`regression-manifest-coverage` 确认 manifest 表格 86 行。 | `tools/knowledge-regression.sh` | Regression | `knowledge-hub-owner-queue-command-hardening-20260622` |
| `rtk git diff --check` | 0 | 通过；未发现 whitespace 或 conflict marker 问题。 | `git diff --check` | Git | `knowledge-hub-owner-queue-command-hardening-20260622` |
| `rtk bash tools/knowledge-final-gate.sh --json --as-of 2026-06-22` | 1 | 符合预期；`final_status=needs-owner-review`，automatic governance 为 `complete-except-owner-review`，唯一 blocker 为 7 个 `owner-gates-open`。 | `/tmp/kh-final-owner-queue-20260622.json` | Final Gate | `knowledge-hub-owner-queue-command-hardening-20260622` |

## 终态说明

`next_open_queue[]` 只减少 owner gate 恢复和并行领取成本，不改变 owner gate 状态。validate、landing-plan 和 landing-audit 仍要求真实 owner 人工回填 `<owner-decisions.jsonl>` 后再执行；工具、AI 或自动化不能代签、代填 `reviewed_by` 或关闭 gate。
