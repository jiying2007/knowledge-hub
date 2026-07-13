# Knowledge Hub P1/P2/P3 optimization closeout 2026-07-11

## Scope

本记录收口用户要求的三项成熟态后优化：

- P1：处理 3 条 PCR02 decision candidate 的 owner-review-and-validation，并补 2 条 evidence-needed 的证据。
- P2：优化 full regression 慢项，目标是把 release gate 稳定压到 3 分钟内。
- P3：整理运营状态页表达，把当前基线和历史基线分开。

本记录只修改 Knowledge Hub 控制面、只读工具和治理文档；不生成 owner decision、不关闭 owner gate、不提升 active、不写 memory、不修改源项目、不发布远端状态。

## P1 closeout

P1 的正确闭环不是把 PCR02 候选直接提升 active，而是把证据状态表达清楚：

| Item | Before triage | After triage | Closeout |
|---|---|---|---|
| `pcr02-camera-raw-preview-virtual-stream-architecture-20260711` | `owner-review-and-validation` | `owner-ready-validation-pending` | 已有实现证据、构建/协议/diff 验证和候选边界；等待 owner/release 决策，不提升 active。 |
| `pcr02-st77912-dual-screen-spi-clock-fps-decision-20260711` | `owner-review-and-validation` | `owner-ready-validation-pending` | 已有源码、原理图、设备输出和带宽计算证据；高温老化、示波器、动画统计仍是 active 前置条件。 |
| `pcr02-st77912-fb-mi-fb-boundary-decision-20260711` | `owner-review-and-validation` | `owner-ready-validation-pending` | 已有 `/proc/fb`、`fb_st77912`、fbtft、MI_FB 路径证据；固件变更后仍需目标设备复核。 |
| `pcr02-evt2-hardware-pdf-reference-index-20260711` | `evidence-needed` | `evidence-backed-validation-pending` | 已登记 PDF SHA256、页数、文本抽取和页级索引证据；不替代 PCB/BOM/板级测量。 |
| `pcr02-evt2-mcu-soc-contract-index-20260711` | `evidence-needed` | `evidence-backed-validation-pending` | 已登记 GD32/MM32/SoC 文档与源码索引证据；不替代构建、HIL、串口、示波器或 release 验证。 |

`tools/knowledge-reviewing-triage.sh` 现在根据 `human_reviewed_by`、`human_review_decision`、`evidence_refs`、`validation_refs` 和 `evidence_strength` 区分：

- `owner-ready-validation-pending`：候选已有人审记录和证据，下一步是 owner/实机/发布验证，不是补基础证据。
- `evidence-backed-validation-pending`：source-audit 已补足可检索证据，但仍不能冒充板级或发布验收。

## P2 closeout

Regression 优化采用低风险路径：

- `copy_repo()` 不再把 `.tmp`、`.codex` 和 `artifacts/vault` 复制进每个 `/tmp` fixture。
- `review-after-as-of-deterministic` 的 final-gate 子验证改用 `KNOWLEDGE_FINAL_GATE_SKIP_REGRESSION=1`，仍验证 final gate as-of 传递和 `knowledge_check` 状态，但不重复嵌套回归。
- `knowledge-regression.sh --suite full` 默认使用最多 4 个 worker 并行执行；每个 worker 使用线程局部结果记录和临时目录清理，`regression-manifest-coverage` 保持串行尾项，避免统计当前结果时被并行抢跑。

这些改动不放宽门禁语义；release 级 `knowledge-final-gate.sh --final-profile mature --full-regression` 仍会运行 full regression、diff check、strict status 和 source check runtime。

实际验证结果：

- full regression trend：`duration_seconds=50`，`regression_status=pass`，`failed_ids=[]`，`result_count=140`。
- mature release gate：`duration_seconds=55`，`final_status=ok`，`blockers=[]`，`gap_map=[]`，低于 3 分钟目标。

## P3 closeout

`governance/status/knowledge-hub-operational-maturity.md` 已调整为：

- 先给当前 2026-07-11 live baseline。
- 再给 2026-07-01 和 2026-07-11 中间态历史基线。
- 明确 19 条 reviewing 是运营队列，不是 mature blocker。
- 明确 5 条 P1 已进入 owner-ready / evidence-backed validation pending，而不是未处理缺口。

## Evidence Index

| Command | Expected result | Layer |
|---|---|---|
| `rtk bash -n tools/knowledge-reviewing-triage.sh` | shell syntax pass | Tool |
| `rtk bash -n tools/knowledge-regression.sh` | shell syntax pass | Tool |
| `rtk bash tools/knowledge-reviewing-triage.sh --json --as-of 2026-07-11` | 3 owner-ready-validation-pending, 2 evidence-backed-validation-pending, 0 owner-review-and-validation/evidence-needed | Tool |
| `rtk bash tools/knowledge-regression-trend.sh --run --suite full --as-of 2026-07-11 --json` | 退出码 0；full regression pass；`failed_ids=[]`；墙钟 50 秒 | Gate |
| `rtk bash tools/knowledge-final-gate.sh --json --final-profile mature --full-regression --as-of 2026-07-11` | 退出码 0；`final_status=ok`；墙钟 55 秒；低于 3 分钟目标 | Gate |
| `rtk git diff --check` | whitespace/conflict marker check pass | Git |

## Residual risk

- P1 中的 PCR02 decision candidate 仍不是 active decision；需要真实 owner/实机/发布证据后才能提升。
- PDF/source-derived 索引仍不是板级验收报告。
- P2 当前已低于 3 分钟目标；若未来回归场景继续增加，应继续记录 `jobs`、`slowest_results`、`failed_ids` 和 release gate 墙钟。
