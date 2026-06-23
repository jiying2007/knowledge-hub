# Knowledge Hub owner/source/subagent 边界加固 2026-06-23

## 摘要

本轮把 owner gate 恢复入口、source identity 读取边界和 subagent 使用规则进一步显性化：

- `knowledge-owner-gates.sh` 在 `observed_source_identity` 与顶层 `source_identity_read_policy` 中说明：为计算 hash 会只读读取 source 文件字节，但不复制正文、不写源项目、不生成 owner decision、不关闭 gate。
- `knowledge-status.sh` 在 owner dashboard 和 `suggested_owner_packet` 中透传同一读取边界，并为 7 步 owner handoff 补齐 `notes_zh`。
- `knowledge-final-gate.sh` 的 `highest_priority_rules_audit` 新增 `subagent-single-writer-readonly`，把“子代理默认只读审查，主线程唯一写入和最终整合”提升为可见过程审计。
- `knowledge-check.sh --diagnostics` 新增非 `.local.jsonl` owner decision 草稿泄漏 warning：未登记的长期命名 owner decision JSONL 不能被误当作 reviewed landing artifact。
- `knowledge-index-plan.sh` 在 manifest 恢复视图中过滤 `.local.jsonl` owner 草稿，并在 decision 恢复视图显示真实 `owner_decision` 状态，避免把本地草稿或已签收 worksheet 误读为固定文案。
- `README.md`、`tools/README.md` 和 regression helper manifest 同步中文入口和回归覆盖。

## 边界

- 未生成 owner decision。
- 未关闭 owner gate。
- 未修改 PCR02 源项目文件。
- 未复制 owner-gated source 正文到 Knowledge Hub。
- 未把 PCR02 project-specific 内容提升到 `domains/embedded/standards/`。
- 未启用自动化写入。
- 未写 `~/.codex/memories`。
- 当前仓库中已有 PCR02 owner decision landing 草稿/登记痕迹不由本制品背书；其是否为真实 owner 授权 landing artifact 仍以 owner/维护者复核为准。

## 变更面

- `tools/knowledge-owner-gates.sh`
- `tools/knowledge-status.sh`
- `tools/knowledge-final-gate.sh`
- `tools/knowledge-check.sh`
- `tools/knowledge-index-plan.sh`
- `tools/knowledge-regression.sh`
- `README.md`
- `tools/README.md`
- `artifacts/manifests/knowledge-hub-governance-regression-helper-20260619.md`

## 回归场景

- `owner-source-identity-context`
- `status-next-owner-gate`
- `final-gate-owner-review-blocker`
- `readme-offline-shortest-paths`
- `owner-decision-draft-leak-warning`
- `index-plan-extended-sections`
- `regression-manifest-coverage`

## 验证计划

```bash
rtk bash -n tools/knowledge-owner-gates.sh
rtk bash -n tools/knowledge-status.sh
rtk bash -n tools/knowledge-final-gate.sh
rtk bash -n tools/knowledge-check.sh
rtk bash -n tools/knowledge-index-plan.sh
rtk bash -n tools/knowledge-regression.sh
rtk git diff --check
rtk bash tools/knowledge-index-plan.sh --section decision --json
rtk bash tools/knowledge-index-plan.sh --section manifest --json
rtk bash tools/knowledge-check.sh --dry-run --json --diagnostics --as-of 2026-06-23
rtk bash tools/knowledge-regression.sh --json --as-of 2026-06-23
rtk bash tools/knowledge-final-gate.sh --json --as-of 2026-06-23
```

## 后续

- 如果 owner 确认 PCR02 owner decision landing 为真实签收产物，应继续用 owner-gates 的 validate/landing-audit 路径补齐 final gate 证据。
- 如果该 landing 只是草稿，应改为 `.local.jsonl` 或移出长期 manifest 命名空间，避免污染 manifest 恢复视图。
