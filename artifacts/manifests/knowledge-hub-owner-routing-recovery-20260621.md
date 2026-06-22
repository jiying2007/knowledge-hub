# Knowledge Hub Owner Routing Recovery 2026-06-21

## 摘要

本 manifest 固化 owner decision 角色路由的只读治理改动。目标是让 PCR02 仍未签收的 owner gate 能从抽象角色恢复到人工分派路径，而不是让 Codex 代签 owner decision。

## 范围

- 新增 `registry/owner-routing.json`，登记 6 个 PCR02 owner decision role 的路由、升级说明和禁止事项。
- `knowledge-owner-gates.sh` 的 row、forms、checklist 和 summary dispatch 输出 `owner_route`。
- `knowledge-status.sh` 的 `owner_gates.owner_dispatch[]` 和 `next_open` 透传 `owner_route`，final gate 通过 `owner_recovery` 继承该字段。
- `knowledge-check.sh` 校验 owner-routing 字段、source/owner 引用和 worksheet role 覆盖。
- README、tools README、schema 和 indexes 说明 maintenance owner 与 decision owner role 的区别。

## 结论

当前自动治理可继续停在 `complete-except-owner-review`。本轮只降低人工分派歧义：

- `routing_owner` 是分派/升级责任人，不是最终签收人。
- `decision_owner_role` 来自 owner worksheet，不自动进入 `registry/owners.json`。
- `owner_route.no_owner_decision_generated=true` 明确路由不会关闭 gate。

## 边界

- 不生成 owner decision。
- 不关闭任何 owner gate。
- 不修改 PCR02 源项目 docs。
- 不把 PCR02 project-specific 内容提升到 `domains/embedded/standards/`。
- 不启用自动化。
- 不写 `~/.codex/memories`。

## Evidence Index

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
|---|---:|---|---|---|---|
| `rtk bash -n tools/knowledge-owner-gates.sh` | 0 | 通过；owner gate shell/python wrapper 语法检查通过。 | `tools/knowledge-owner-gates.sh` | Tool | `knowledge-hub-owner-routing-recovery-20260621` |
| `rtk bash -n tools/knowledge-status.sh` | 0 | 通过；status wrapper 语法检查通过。 | `tools/knowledge-status.sh` | Tool | `knowledge-hub-owner-routing-recovery-20260621` |
| `rtk bash -n tools/knowledge-check.sh` | 0 | 通过；check wrapper 语法检查通过。 | `tools/knowledge-check.sh` | Tool | `knowledge-hub-owner-routing-recovery-20260621` |
| `rtk bash tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --summary --json` | 0 | 通过；`project-owner` route 为 `pcr02-registry-owner`，`no_owner_decision_generated=true`。 | `tools/knowledge-owner-gates.sh` | Owner Gate | `knowledge-hub-owner-routing-recovery-20260621` |
| `rtk bash tools/knowledge-status.sh --json` | 0 | 通过；`owner_gates.owner_dispatch[].owner_route` 和 `next_open.owner_route` 已透传。 | `tools/knowledge-status.sh` | Status | `knowledge-hub-owner-routing-recovery-20260621` |
| `rtk bash tools/knowledge-check.sh --dry-run --json --diagnostics` | 0 | 通过；`status=pass`，0 errors，0 warnings，owner-routing 自检通过。 | `tools/knowledge-check.sh` | Gate | `knowledge-hub-owner-routing-recovery-20260621` |
| `rtk bash tools/knowledge-regression.sh --json` | 0 | 通过；`result_count=64`，无失败，owner route 回归断言通过。 | `tools/knowledge-regression.sh` | Regression | `knowledge-hub-owner-routing-recovery-20260621` |
| `rtk git diff --check` | 0 | 通过；当前 diff 无空白或补丁格式问题。 | `git diff --check` | Git | `knowledge-hub-owner-routing-recovery-20260621` |
| `rtk bash tools/knowledge-final-gate.sh --json` | 1 | 预期负结果；`final_status=needs-owner-review`，`automatic_governance=complete-except-owner-review`，唯一 blocker/gap 为 `owner-gates-open`，owner open count 仍为 7。 | `tools/knowledge-final-gate.sh` | Final Gate | `knowledge-hub-owner-routing-recovery-20260621` |

## 下一步

人工 owner 填写 JSONL 前，先运行：

```bash
rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --summary
rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --owner project-owner --forms-jsonl
```

如果 `owner_route.routing_status=needs-human-assignment`，必须先由 `routing_owner` 找到真实签收人，再由真实 owner 填写 `reviewed_by`。
