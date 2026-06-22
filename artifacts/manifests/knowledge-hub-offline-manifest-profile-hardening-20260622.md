# Knowledge Hub 离线维护与 manifest profile 门禁加固 2026-06-22

## 摘要

本轮把子代理发现的低风险治理缺口落到可验证入口：

- `knowledge-new.sh --source` 的 registry source 草稿不再把 `review_after` 默认设为当天，改为当前日期后三个月，避免新 source 一登记就进入过期复核噪音。
- README 和 tools README 明确终态检查离线 fallback：工具不可用时不得声明 terminal `ok` / `pass`，必须记录 `manual_validation_pending: true`、owner、日期、cwd、阻塞原因和后续命令。
- `knowledge-check.sh` 的治理 manifest JSONL profile gate 扫描 2026-06-21 及之后的 `knowledge-hub-*.jsonl`，避免新日期 manifest 漏过中文摘要、证据和边界字段。
- `knowledge-regression.sh` 增加 README 5 条人工维护最短路径和离线 fallback 回归，并把 manifest profile gate 覆盖扩展到 2026-06-22 样例。

## 范围

| 项目 | 状态 | 说明 |
|---|---|---|
| Source 新增默认复核周期 | applied | registry source `review_after` 默认使用三个月复核周期，coverage row `checked_at` 保持当天。 |
| 终态检查离线 fallback | applied | README / tools README 要求离线时只能记录待验证，不得伪造通过结果。 |
| Manifest profile gate 日期范围 | applied | 2026-06-21 及之后的 `knowledge-hub-*.jsonl` 都进入轻量 profile 检查。 |
| Regression coverage | applied | 回归场景从 93 个扩展到 94 个，新增 README 离线最短路径保护。 |

## 边界

- 不修改 PCR02 源项目文档、工具、源码或配置。
- 不生成 owner decision，不关闭 owner gate。
- 不把 PCR02 project-specific 内容提升到 `domains/embedded/standards/`。
- 不启用自动化写操作，不写 `~/.codex/memories`。
- 本轮只强化 Knowledge Hub 控制面、文档入口和只读/临时 fixture 回归。

## Evidence Index

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
|---|---:|---|---|---|---|
| `rtk bash -n tools/knowledge-new.sh` | 0 | 通过；source 新增向导 shell 语法有效 | `tools/knowledge-new.sh` | Tool | `knowledge-hub-offline-manifest-profile-hardening-20260622` |
| `rtk bash -n tools/knowledge-check.sh` | 0 | 通过；knowledge-check shell 语法有效 | `tools/knowledge-check.sh` | Tool | `knowledge-hub-offline-manifest-profile-hardening-20260622` |
| `rtk bash -n tools/knowledge-regression.sh` | 0 | 通过；knowledge-regression shell 语法有效 | `tools/knowledge-regression.sh` | Tool | `knowledge-hub-offline-manifest-profile-hardening-20260622` |
| `KNOWLEDGE_TODAY=2026-06-22 rtk bash tools/knowledge-new.sh --source --source-id example-source --source-path /tmp/example --role project-current-docs-source --authority legacy-project-current-docs --write-policy read-only-unless-explicitly-approved --no-check-reason "classify-first pending coverage"` | 0 | 通过；source 草稿 `review_after=2026-09-22`，coverage row `checked_at=2026-06-22`，命令未写文件 | `tools/knowledge-new.sh` | Tool | `knowledge-hub-offline-manifest-profile-hardening-20260622` |
| `rtk bash tools/knowledge-regression.sh --json --as-of 2026-06-22` | 0 | 通过；94 个回归场景全部 pass，`regression-manifest-coverage` 覆盖 94/94 | `tools/knowledge-regression.sh` | Tool | `knowledge-hub-offline-manifest-profile-hardening-20260622` |
| `rtk bash tools/knowledge-check.sh --dry-run --json --diagnostics --as-of 2026-06-22` | 0 | 通过；errors=0、warnings=0，manifest profile gate 只检查主 summary 行并接受 guardrails/boundaries | `tools/knowledge-check.sh` | Tool | `knowledge-hub-offline-manifest-profile-hardening-20260622` |
| `rtk git diff --check` | 0 | 通过；当前 diff 无空白错误 | git diff | Tool | `knowledge-hub-offline-manifest-profile-hardening-20260622` |
| `rtk bash tools/knowledge-final-gate.sh --json --as-of 2026-06-22` | 1 | 符合预期；`final_status=needs-owner-review`，自动治理 `complete-except-owner-review`，唯一 blocker 是 7 个 PCR02 owner gates | `tools/knowledge-final-gate.sh` | Tool | `knowledge-hub-offline-manifest-profile-hardening-20260622` |

## 后续

- 继续保持 owner gate 为人工签收边界；本轮没有关闭任何 PCR02 owner gate。
- 可在后续窄路线中继续处理 owner 表单逐字段诊断、landing audit 实际对账或 index-plan markdown 摘要，但这些不是本轮阻塞项。
