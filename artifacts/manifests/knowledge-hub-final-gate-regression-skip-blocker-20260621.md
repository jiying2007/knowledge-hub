# Knowledge Hub final gate regression skip blocker 2026-06-21

## 结论

本轮修复终态门禁的潜在绕过口：`KNOWLEDGE_FINAL_GATE_SKIP_REGRESSION=1` 只能作为回归自测辅助信号，不能被 `knowledge-final-gate.sh` 当作终态通过证据。

修复后，final gate 如果检测到 `checks.knowledge_regression.skipped_for_self_test=true`，会输出 `knowledge-regression-skipped` blocker，`final_status=needs-fix`，`automatic_governance.core_checks_pass=false`。默认路径仍会真实执行 `knowledge-regression.sh`。

## 范围

- `tools/knowledge-final-gate.sh`
  - 将 regression self-test skip 标记为 blocker。
  - `core_checks_pass` 明确要求 regression 未被 skip。
- `tools/knowledge-regression.sh`
  - 增加 `final-gate-skip-regression-blocker` 负向场景。
  - owner-review 正向场景改为使用 `KNOWLEDGE_FINAL_GATE_INNER_REGRESSION=1`，证明默认路径仍执行 regression。
- `artifacts/manifests/knowledge-hub-governance-regression-helper-20260619.md`
  - 同步回归场景清单和计数。

## 控制规则

| 规则 | 状态 |
|---|---|
| 不把跳过 regression 的结果当终态证据 | enforced |
| 不关闭 owner gate | enforced |
| 不生成 owner decision | enforced |
| 不修改源项目 | enforced |
| 不启用自动化写操作 | enforced |

## Evidence Index

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
|---|---:|---|---|---|---|
| subagent `final gate / regression / index review` | 0 | 指出 `KNOWLEDGE_FINAL_GATE_SKIP_REGRESSION=1` 会让 final gate 把 regression skip 当 pass，建议阻断 | subagent `019ee99a-067e-72d2-8cba-eba9faae3a98` | Subagent evidence | `knowledge-hub-final-gate-regression-skip-blocker-20260621` |
| `rtk bash -lc 'KNOWLEDGE_FINAL_GATE_SKIP_REGRESSION=1 rtk bash tools/knowledge-final-gate.sh --json --as-of 2026-06-21'` | pending | 应返回 `needs-fix`，并出现 `knowledge-regression-skipped` blocker | `tools/knowledge-final-gate.sh` | Negative regression | `knowledge-hub-final-gate-regression-skip-blocker-20260621` |
| `rtk bash tools/knowledge-regression.sh --json --as-of 2026-06-21` | pending | 应覆盖 skip blocker、默认 regression 路径和 owner-review terminal gate | `tools/knowledge-regression.sh` | Regression | `knowledge-hub-final-gate-regression-skip-blocker-20260621` |

## 下一步

- 运行 full regression 与 final gate 后，将 Evidence Index 中 pending 命令替换为最终验证结果不作为必要前置；本 manifest 的可审查证据以提交前命令输出为准。
- owner gates 仍需人工 owner decision；本修复只加强 terminal gate，不改变 owner 语义门禁。
