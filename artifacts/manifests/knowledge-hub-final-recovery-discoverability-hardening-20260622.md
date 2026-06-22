# Knowledge Hub final recovery discoverability hardening 2026-06-22

## 结论

本轮继续压实 Knowledge Hub 终态恢复和 proof 可发现性，处理 4 个自动治理切片：

- `knowledge-final-gate.sh` 的 `owner_recovery` 直接透传 `next_open_queue[]`、数量和排序规则，让新线程只读 terminal gate JSON 也能恢复下一批 owner worksheet 领取顺序。
- `knowledge-regression.sh` 新增 `final-proof-artifact-discoverability`，检查 5 个 2026-06-22 终态 proof/gate/recovery 主制品在 registry、migration 和核心索引中可发现，且 `.md/.jsonl` 配对存在。
- `tools/README.md` 中 `knowledge-doctor.sh`、`knowledge-index-plan.sh`、`knowledge-regression.sh` 的人读说明改为中文，保留命令、参数、JSON 字段和环境变量原文。
- `knowledge-hub-owner-routing-recovery-20260621.md` 的旧 Evidence Index 表头升级为当前固定列，补齐 Evidence Path、Layer 和 Related Artifact。

## 变更范围

| 文件 | 变更 |
|---|---|
| `tools/knowledge-final-gate.sh` | `owner_recovery` 透传 `next_open_queue[]`、`next_open_queue_count` 和 `next_open_queue_selection_order`。 |
| `tools/knowledge-regression.sh` | 扩展 `final-gate-owner-review-blocker` 队列断言；新增 `final-proof-artifact-discoverability`。 |
| `README.md`、`tools/README.md` | 补充 terminal gate 的 `owner_recovery.next_open_queue[]` 恢复语义；中文化工具说明。 |
| `artifacts/manifests/knowledge-hub-owner-routing-recovery-20260621.md` | Evidence Index 表格升级为当前固定列。 |
| `artifacts/manifests/knowledge-hub-governance-regression-helper-20260619.md` | 增加 `final-proof-artifact-discoverability` 覆盖行，并把回归总数更新为 87。 |

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
| `rtk bash -n tools/knowledge-final-gate.sh` | 0 | 通过；final gate 脚本语法检查通过。 | `tools/knowledge-final-gate.sh` | Tool | `knowledge-hub-final-recovery-discoverability-hardening-20260622` |
| `rtk bash -n tools/knowledge-regression.sh` | 0 | 通过；回归入口语法检查通过。 | `tools/knowledge-regression.sh` | Tool | `knowledge-hub-final-recovery-discoverability-hardening-20260622` |
| `rtk bash tools/knowledge-final-gate.sh --json --as-of 2026-06-22` | 1 | 符合预期；`final_status=needs-owner-review`，automatic governance 为 `complete-except-owner-review`，唯一 blocker 为 `owner-gates-open`，`owner_recovery.next_open_queue_count=7`。 | `/tmp/kh-final-discoverability-20260622.json` | Final Gate | `knowledge-hub-final-recovery-discoverability-hardening-20260622` |
| `rtk rg -n 'read-only maintenance helper\|read-only core index planner\|read-only regression fixture runner\|without writing files\|hard failure' tools/README.md` | 1 | 通过；无命中，相关工具说明已中文化。 | `tools/README.md` | Readability Gate | `knowledge-hub-final-recovery-discoverability-hardening-20260622` |
| `rtk rg -n '^\| Command \| Exit \| Result \| Notes \|' artifacts/manifests/knowledge-hub-owner-routing-recovery-20260621.md` | 1 | 通过；旧 Evidence Index 表头已移除。 | `artifacts/manifests/knowledge-hub-owner-routing-recovery-20260621.md` | Evidence Gate | `knowledge-hub-final-recovery-discoverability-hardening-20260622` |
| `rtk bash tools/knowledge-check.sh --dry-run --json --diagnostics --as-of 2026-06-22` | 0 | 通过；0 errors、0 warnings，source coverage latest 仍选择 `knowledge-hub-source-coverage-closeout-20260620.jsonl`，boundary health 为 pass。 | `tools/knowledge-check.sh` | Gate | `knowledge-hub-final-recovery-discoverability-hardening-20260622` |
| `rtk bash tools/knowledge-regression.sh --json --as-of 2026-06-22` | 0 | 通过；87 个回归场景全部 pass，新增 `final-proof-artifact-discoverability` 通过。 | `/tmp/kh-regression-discoverability-pass.json` | Regression | `knowledge-hub-final-recovery-discoverability-hardening-20260622` |
| `rtk git diff --check` | 0 | 通过；未发现 whitespace 或 conflict marker 问题。 | `git diff --check` | Git | `knowledge-hub-final-recovery-discoverability-hardening-20260622` |

## 终态说明

本轮只压实 owner 恢复队列和 proof artifact 可发现性，不改变 owner gate 语义。`final_status=needs-owner-review` 仍是正确终态，前提是 automatic governance 已闭环且唯一 blocker 为 `owner-gates-open`。
