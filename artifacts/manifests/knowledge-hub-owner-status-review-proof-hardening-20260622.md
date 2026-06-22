# Knowledge Hub owner 状态、复核与终态证明加固 2026-06-22

## 结论

本轮根据子代理只读审查结果，继续推进非 owner 决策类终态加固，重点解决 3 个治理缝隙：

- `knowledge-status.sh` 的 `owner_gates.next_open_queue[]` 现在从 owner-ready registry items 保守推导 `owner_ready_package_status=covered`，避免把已存在的 owner-ready package 误报为 missing。
- `knowledge-review-after.sh` 不再只读取固定 `pcr02-owner-decision-worksheets-20260618.jsonl`，改为扫描 `artifacts/manifests/*owner-decision-worksheets-*.jsonl`，并在 open owner gate 行中输出 `worksheet_file`。
- `knowledge-final-gate.sh` 的 `proof_artifacts_20260622` 从固定 10 个主制品改为“种子清单 + registry 动态选择”，当前覆盖 2026-06-22 已登记的 governance proof 制品，并把最新 `knowledge-hub-review-after-topic-owner-hardening-20260622` 纳入终态证明。

同时补了一组轻量中文可读性改动：`governance/automation-policy.md`、`governance/migration-policy.md`、`governance/promotion-policy.md` 和 `governance/source-boundaries.md` 的一级/二级标题改为中文优先、英文括注，保留技术术语可检索性。

## 边界

- 不生成 owner decision，不代填 `reviewed_by`，不关闭 PCR02 7 个 open owner gate。
- 不修改 PCR02 源项目 docs、tools、knowledge、product-test、scratch 或其他 source 文件。
- 不复制 owner-gated source 正文。
- 不把 PCR02 project-specific 内容提升到 `domains/embedded/standards/`。
- 不启用自动化，不写 `~/.codex/memories`。
- `knowledge-review-after.sh` 仍是 report-only 人工提醒，不自动修改 `review_after`。

## 变更明细

| 区域 | 文件 | 变更 |
|---|---|---|
| owner 状态队列 | `tools/knowledge-status.sh` | 从 `registry_items` 推导 owner-ready package 覆盖，`next_open_queue[]` 输出 `covered` 和 package count |
| 复核提醒 | `tools/knowledge-review-after.sh` | owner worksheet 文件从 glob 加载，并在 owner gate 行输出 `worksheet_file` |
| 终态 proof | `tools/knowledge-final-gate.sh` | 新增动态 selector，按 governance、audit、2026-06-22、tag、path 和 review_status 选择 proof 制品 |
| 回归 | `tools/knowledge-regression.sh` | 锁定 owner queue、review-after worksheet_file 和动态 proof 可发现性契约 |
| 中文可读性 | `governance/*.md` | 将核心 governance 标题中文化，保留英文括注 |

## Evidence Index

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
|---|---:|---|---|---|---|
| `rtk bash -n tools/knowledge-status.sh` | 0 | shell 语法通过 | `tools/knowledge-status.sh` | Tool | `knowledge-hub-owner-status-review-proof-hardening-20260622` |
| `rtk bash -n tools/knowledge-review-after.sh` | 0 | shell 语法通过 | `tools/knowledge-review-after.sh` | Tool | `knowledge-hub-owner-status-review-proof-hardening-20260622` |
| `rtk bash -n tools/knowledge-final-gate.sh` | 0 | shell 语法通过 | `tools/knowledge-final-gate.sh` | Tool | `knowledge-hub-owner-status-review-proof-hardening-20260622` |
| `rtk bash -n tools/knowledge-regression.sh` | 0 | shell 语法通过 | `tools/knowledge-regression.sh` | Tool | `knowledge-hub-owner-status-review-proof-hardening-20260622` |
| `rtk bash tools/knowledge-status.sh --json --as-of 2026-06-22` | 0 | `next_open_queue` 为 7 条；前两条 owner-ready 状态为 `covered`，package count 为 1 | `tools/knowledge-status.sh` | Tool | `knowledge-hub-owner-status-review-proof-hardening-20260622` |
| `rtk bash tools/knowledge-review-after.sh --json --as-of 2026-06-22 --window-days 30 --include-owner-gates` | 0 | report-only；39 条明细，其中 7 条 open owner gate 均带 `worksheet_file` | `tools/knowledge-review-after.sh` | Tool | `knowledge-hub-owner-status-review-proof-hardening-20260622` |
| `KNOWLEDGE_FINAL_GATE_INNER_REGRESSION=1 rtk bash tools/knowledge-final-gate.sh --json --as-of 2026-06-22` | 1 | 预期停在 `needs-owner-review`；`proof_artifacts_20260622` 通过，动态 proof selector 覆盖最新 governance proof | `tools/knowledge-final-gate.sh` | Tool | `knowledge-hub-owner-status-review-proof-hardening-20260622` |

## 后续人工动作

- owner 仍需从 `tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --next-open --checklist --forms` 逐条签收。
- 新增 worksheet 文件时，`knowledge-review-after.sh --include-owner-gates` 会自动纳入提醒；但不会代签或关闭 owner gate。
- 新增 2026-06-22 governance proof manifest 后，需要确保 registry、migration 和核心索引同步，否则 final gate 的动态 proof 摘要会失败。
