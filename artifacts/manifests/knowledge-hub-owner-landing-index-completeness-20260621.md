# Knowledge Hub owner landing index completeness 2026-06-21

## 结论

本轮补齐 owner decision 人工落地链路中的索引提示：`landing-plan` 与 `landing-audit` 现在显式列出 `indexes/by-source.md` 和 `indexes/by-decision.md`，并在回归中断言这些人工落点不会从输出中丢失。

该改动只改变只读提示和回归契约，不生成 owner decision，不关闭 owner gate，不自动修改 worksheet / registry / migration / index。

## 范围

- `tools/knowledge-owner-gates.sh`
  - `required_manual_files` 增加 `indexes/by-source.md` 和 `indexes/by-decision.md`。
  - landing plan 的中文人工动作同步列出 by-source / by-decision。
  - landing audit 的 `expected_manual_deltas.indexes` 增加 by-source / by-decision。
- `tools/knowledge-regression.sh`
  - owner landing plan / audit 回归断言这些索引提示存在。

## 控制规则

| 规则 | 状态 |
|---|---|
| 不生成 owner decision | enforced |
| 不关闭 owner gate | enforced |
| 不自动写 registry/index/source-policy/worksheet | enforced |
| 只读 landing plan / landing audit 仍需人工落地 | enforced |

## Evidence Index

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
|---|---:|---|---|---|---|
| subagent `owner-gated signoff review` | 0 | 指出 landing plan/audit 缺少 by-source/by-decision 人工索引提示，建议补工具输出和回归 | owner chain review | Subagent evidence | `knowledge-hub-owner-landing-index-completeness-20260621` |
| `rtk rg -n "required_manual_files|expected_manual_deltas|by-source|by-decision|landing-audit|landing_plan" tools/knowledge-owner-gates.sh` | 0 | 定位 owner landing 输出字段 | `tools/knowledge-owner-gates.sh` | Tooling | `knowledge-hub-owner-landing-index-completeness-20260621` |
| `rtk rg -n "landing-audit|by-source|by-decision|required_manual_files|expected_manual_deltas" tools/knowledge-regression.sh` | 0 | 定位既有 owner landing 回归 | `tools/knowledge-regression.sh` | Regression | `knowledge-hub-owner-landing-index-completeness-20260621` |

## 下一步

后续只有真实 owner 提供有效 decision JSONL 后，才能按 validate-forms、landing-plan 和 landing-audit 进行人工落地。Codex 不代签、不自动 apply。
