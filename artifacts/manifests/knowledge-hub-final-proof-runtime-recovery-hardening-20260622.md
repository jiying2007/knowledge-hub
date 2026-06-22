# Knowledge Hub 终态 proof 与运行时恢复门禁加固 2026-06-22

## 摘要

本轮根据 3 个只读 subagent 审查结果，把终态恢复面继续压实：

- `knowledge-final-gate.sh` 的终态 proof 主制品契约从 5 项扩展到 10 项，覆盖 final gate、owner recovery、proof summary、source-check snapshot/runtime 和 report-only maintenance tools 的主证明面。
- `knowledge-regression.sh` 增加 `final-gate-source-check-runtime-failed-blocker` 负向回归，证明 source-check runtime 失败会触发 `source-check-runtime-failed` blocker，不能被 owner gate 掩盖。
- `knowledge-index-plan.sh --section manifest --json` 增加 `profile_health`、`summary_source`、`evidence_source`、`derived_summary_zh` 和 `derived_evidence_count`，用于中文恢复阅读，不回填旧 manifest 正文。
- `knowledge-owner-gates.sh --validate-forms` 保留原 `errors[]` 字符串，同时新增逐字段 `diagnostics[]`，方便 owner UI 或人工工具定位字段、实际值、期望值和中文动作。

## 边界

- 不修改 PCR02 源项目文档、工具、源码或配置。
- 不生成 owner decision，不关闭 owner gate。
- 不把 PCR02 project-specific 内容提升到 `domains/embedded/standards/`。
- 不启用自动化写操作，不写 `~/.codex/memories`。
- 本轮所有负向 fixture 只写 `/tmp` 临时副本，不写真实仓库外部 source。

## Evidence Index

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
|---|---:|---|---|---|---|
| `rtk bash -n tools/knowledge-final-gate.sh` | 0 | 通过；final gate shell 包装层语法有效 | `tools/knowledge-final-gate.sh` | Tool | `knowledge-hub-final-proof-runtime-recovery-hardening-20260622` |
| `rtk bash -n tools/knowledge-index-plan.sh` | 0 | 通过；index-plan shell 包装层语法有效 | `tools/knowledge-index-plan.sh` | Tool | `knowledge-hub-final-proof-runtime-recovery-hardening-20260622` |
| `rtk bash -n tools/knowledge-owner-gates.sh` | 0 | 通过；owner-gates shell 包装层语法有效 | `tools/knowledge-owner-gates.sh` | Tool | `knowledge-hub-final-proof-runtime-recovery-hardening-20260622` |
| `rtk bash -n tools/knowledge-regression.sh` | 0 | 通过；knowledge-regression shell 包装层语法有效 | `tools/knowledge-regression.sh` | Tool | `knowledge-hub-final-proof-runtime-recovery-hardening-20260622` |
| `rtk bash tools/knowledge-check.sh --dry-run --json --diagnostics --as-of 2026-06-22` | 0 | 通过；errors=0、warnings=0，source 和 manifest profile 门禁保持健康 | `tools/knowledge-check.sh` | Tool | `knowledge-hub-final-proof-runtime-recovery-hardening-20260622` |
| `rtk git diff --check` | 0 | 通过；当前 diff 无空白错误 | git diff | Tool | `knowledge-hub-final-proof-runtime-recovery-hardening-20260622` |
| `rtk bash tools/knowledge-regression.sh --json --as-of 2026-06-22` | 0 | 通过；95 个回归场景全部 pass，新增 source-check runtime 失败 blocker 覆盖 | `tools/knowledge-regression.sh` | Tool | `knowledge-hub-final-proof-runtime-recovery-hardening-20260622` |
| `rtk bash tools/knowledge-final-gate.sh --json --as-of 2026-06-22` | 1 | 符合预期；`final_status=needs-owner-review`，自动治理 complete-except-owner-review，剩余 blocker 仅 7 个 PCR02 owner gates | `tools/knowledge-final-gate.sh` | Tool | `knowledge-hub-final-proof-runtime-recovery-hardening-20260622` |

## 后续

- owner gate 仍需真实 owner 人工签收；Codex 只能继续提供只读分派、表单校验和 landing plan。
- 若后续 owner 表单契约需要收紧，可在人工 owner 决策样例出现后再增加 `owner_decision -> target_decision` 成对兼容矩阵。
