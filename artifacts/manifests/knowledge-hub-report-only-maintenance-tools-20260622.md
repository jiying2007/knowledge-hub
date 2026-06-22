# Knowledge Hub report-only maintenance tools 2026-06-22

## 结论

本轮新增两个只读维护入口，降低人工复核和 source availability 检查的重复成本。

- `tools/knowledge-review-after.sh`
  - 用途：按 `as_of + window_days` 输出 `review_after` 过期和即将到期报告。
  - 本轮基线：`as_of=2026-06-22`，30 天窗口覆盖 32 个 near-due item、0 个 stale item、0 个 near-due source，owner gate open 仍为 7。
  - 边界：near-due 不是 blocking gate，不自动修改 `review_after`，不关闭 owner gate，不生成 owner decision。
- `tools/knowledge-source-check.sh`
  - 用途：显式人工调用时，对 PCR02 Level 2 allowlist 做 report-only source availability check。
  - 本轮基线：7 个 PCR02 Level 2 source 只读路径存在性检查全部通过。
  - 边界：只证明路径或文件在执行时存在，不证明内容正确、语义可迁移、owner 已签收或 active promotion 可成立。

两个工具都不写 registry/index/manifest，不修改源项目，不读取 PCR02 source 正文，不写 `~/.codex/memories`，不启用自动化写操作。

## 工具边界

### knowledge-review-after.sh

- 默认窗口：30 天。
- 日期来源优先级：`--as-of`、`KNOWLEDGE_TODAY`、系统日期。
- 默认输出 item 明细；source 和 owner gate 明细需显式参数。
- 输出统计包含 stale item、near-due item、stale source、near-due source 和 owner gate open count。
- `status=report-only` 不表示 owner gate 已关闭。

### knowledge-source-check.sh

- 支持范围：`--scope pcr02-level2`。
- 允许 source：
  - `pcr02-project-tools`
  - `pcr02-project-knowledge`
  - `pcr02-product-test`
  - `pcr02-project-scratch`
  - `pcr02-project-root-artifacts`
  - `pcr02-module-agent-rules`
  - `pcr02-project-agent-config`
- 允许命令形态：
  - `rtk bash -lc 'test -d <absolute-source-path>'`
  - `rtk bash -lc 'test -f <absolute-source-file>'`
- 拒绝命令形态：
  - 非 allowlist source。
  - 非 `rtk bash -lc`。
  - 非单一 `test -d` / `test -f`。
  - 包含 shell 控制符、变量展开、glob、相对路径、`~` 或 `..`。
  - check target 不在 source registry path 内。

## Evidence Index

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
|---|---:|---|---|---|---|
| `rtk bash -n tools/knowledge-source-check.sh` | 0 | 通过；source-check helper 语法检查通过。 | `tools/knowledge-source-check.sh` | Tool | `knowledge-hub-report-only-maintenance-tools-20260622` |
| `rtk bash -n tools/knowledge-review-after.sh` | 0 | 通过；review-after helper 语法检查通过。 | `tools/knowledge-review-after.sh` | Tool | `knowledge-hub-report-only-maintenance-tools-20260622` |
| `rtk bash tools/knowledge-source-check.sh --scope pcr02-level2 --json --as-of 2026-06-22` | 0 | 通过；7 个 PCR02 Level 2 source availability row 全部 pass，`source_check_health_executed=false`。 | `tools/knowledge-source-check.sh` | Tool | `knowledge-source-check-report-only-helper` |
| `rtk bash tools/knowledge-review-after.sh --json --as-of 2026-06-22 --window-days 30` | 0 | 通过；near_due_items=32，stale_items=0，near_due_sources=0，owner_gate_open_count=7。 | `tools/knowledge-review-after.sh` | Tool | `knowledge-review-after-report-only-helper` |
| `rtk bash tools/knowledge-check.sh --dry-run --json --diagnostics --as-of 2026-06-22` | 0 | 通过；`status=pass`，errors=0，warnings=0。 | `tools/knowledge-check.sh` | Gate | `knowledge-check` |
| `rtk bash tools/knowledge-regression.sh --json --as-of 2026-06-22` | 0 | 通过；`status=pass`，`result_count=90`。 | `tools/knowledge-regression.sh` | Gate | `knowledge-regression` |
| `rtk bash tools/knowledge-final-gate.sh --json --as-of 2026-06-22` | 1 | 预期停在 owner-review；`automatic_governance.status=complete-except-owner-review`，唯一 blocker 为 7 个 `owner-gates-open`。 | `tools/knowledge-final-gate.sh` | Gate | `knowledge-final-gate` |

## 边界

- 不修改 PCR02 源项目文件。
- 不读取 PCR02 source 正文。
- 不写 `~/.codex/memories`。
- 不启用自动化写操作。
- 不生成 owner decision。
- 不关闭 owner gate。
- 不把 path-exists 当作内容正确或语义可迁移。
- 不改变 `knowledge-check` 的 `source_check_health.mode=static-registry-only` 和 `executed=false` 契约。
