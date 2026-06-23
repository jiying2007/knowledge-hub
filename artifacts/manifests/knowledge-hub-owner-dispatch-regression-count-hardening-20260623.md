# Knowledge Hub owner 分派与回归计数口径加固 2026-06-23

## 结论

本轮继续推进 Knowledge Hub 终态治理中的非 owner 自动治理面，处理两个不会关闭 owner gate 的结构性问题。

- `knowledge-owner-gates.sh` 和 `knowledge-status.sh` 的 `owner_dispatch[]` 改为按 `source_id + owner` 分派，而不是只按 owner 合并。
- `owner_dispatch[]` 新增 `dispatch_scope_id`、`source_ids` 和 `mixed_source_owner=false`，便于人工识别同一 owner 在不同 source 下的独立签收范围。
- `tools/knowledge-regression.sh` 新增 `owner-dispatch-source-scope-isolation`，在临时副本中制造同一 owner 跨 source 场景，锁定 owner-gates 和 status 两个入口都必须保留对应 `--source-id`。
- 2026-06-23 既有治理 manifest 中固定的回归数量已标注为“当次运行历史捕获”，避免长期维护者把旧证据数量误读为当前 live 回归数量。
- `tools/knowledge-regression.sh` 新增 `manifest-regression-count-capture-qualifier`，后续新增日期化治理 manifest 若写固定回归数量，必须说明历史捕获或 live 输出口径。
- `artifacts/manifests/knowledge-hub-governance-regression-helper-20260619.md` 已同步两个新增回归 ID，当前 live 目标为 117 项。

## 子代理审查输入

| 子代理 | 关注点 | 结论 |
|---|---|---|
| Peirce | owner 分派与 source scope | 发现同一 owner 跨 source 时，按 owner 合并会让分派命令丢失或混用 source scope；建议改为 `(source_id, owner)` 分组并补回归。 |
| Ampere | 终态 gate 与非 owner 阻塞 | 未发现新的非 owner blocker；终态仍只剩 7 个 owner gate。 |
| Linnaeus | manifest/readability 漂移 | 发现多个 2026-06-23 manifest 把历史回归数量写成固定事实；建议加口径说明和回归保护。 |

## 验证证据

| 命令 | 结果 | 摘要 |
|---|---|---|
| `rtk bash -n tools/knowledge-owner-gates.sh` | pass | owner gate 工具语法通过。 |
| `rtk bash -n tools/knowledge-status.sh` | pass | status dashboard 语法通过。 |
| `rtk bash -n tools/knowledge-regression.sh` | pass | regression 工具语法通过。 |
| `rtk bash tools/knowledge-owner-gates.sh --summary --json` | owner-review expected | 顶层 `status=ok` 仍只代表 tool-health，7 个 owner gate 保持 open。 |
| `rtk bash tools/knowledge-status.sh --json --as-of 2026-06-23` | owner-review expected | status 侧 owner dispatch 按 `source_id + owner` 输出只读分派范围。 |
| `rtk bash tools/knowledge-check.sh --dry-run --json --diagnostics --as-of 2026-06-23` | pass | 全仓一致性检查通过，errors=0，warnings=0。 |
| `rtk bash tools/knowledge-regression.sh --json --as-of 2026-06-23` | pass | 117 项回归全部通过，新增两项回归覆盖本轮改动。 |
| `rtk bash tools/knowledge-final-gate.sh --json --as-of 2026-06-23` | owner-review expected | `final_status=needs-owner-review`，自动治理为 `complete-except-owner-review`，唯一 gap 为 `owner-gates-open`。 |

## 边界

- 不生成 owner decision。
- 不填写 `reviewed_by`、`reviewed_at` 或 owner 签收字段。
- 不关闭 owner gate。
- 不修改 PCR02 源项目 docs、tools、knowledge、app_product_test、scratch 或 source tree。
- 不复制 owner-gated source 正文。
- 不把 PCR02 project-specific 内容提升到 `domains/embedded/standards/`。
- 不启用非 report-only 自动化。
- 不写 `~/.codex/memories`。

## 剩余状态

本轮只压实只读分派和历史证据口径，不改变真实 owner gate 状态。7 个 `pcr02-project-docs` owner gate 仍需真实 owner 人工决策；Codex 只能提供只读分派、校验、landing plan 和审计证据，不能代签或关闭 gate。
