# Knowledge Hub 运营成熟态状态 2026-07-01

## 结论

Knowledge Hub 已达到长期运营成熟完整交付态：registry、索引、source control、owner gate、review queue、review_after 周期刷新、final gate、search/context/status/check 工具链都有可验证入口，且 `mature` profile 能阻断迁移态残留和高比例 `reviewing` 滞留。

截至 2026-07-13 当前 live baseline，P1/P2/P3 优化、运营审计和 PCR02 owner-ready 验证路径已落为 Hub 控制面资产：3 条 PCR02 decision candidate 不再被粗粒度标成 `owner-review-and-validation`，而是进入 `owner-ready-validation-pending`；2 条 PCR02 EVT2 source-audit 不再被标成 `evidence-needed`，而是进入 `evidence-backed-validation-pending`；18 条 2026-08-09..2026-08-11 Codex archive near-due item 已按 archive-only/provenance 边界复核并刷新到 2026-11-09..2026-11-11；full regression 去掉无用 fixture 复制、减少嵌套回归并支持 full suite 最多 4 worker 并行；本页把当前基线和历史基线拆开。

当前状态仍是运营成熟，不是 owner 代签。本页不替代 final gate，不生成 owner decision，不关闭 owner gate，不提升 active，不写 memory，不修改源项目，不代表板级老化、EMI、HIL、发布或远端状态已签收。

## 当前基线

| 指标 | 当前值 | 说明 |
|---|---:|---|
| registry item | 316 | 2026-07-13 operational audit 和 PCR02 owner-ready validation paths 登记后的 live 总数 |
| active item | 16 | `summary_zh` 缺口为 0 |
| archived item | 280 | 125 条 archived 长尾摘要已全量回填，P1/P2/P3 closeout、ST77912 implementation evidence 和 2026-07-13 operational audit 已登记 |
| reviewing item | 20 | 比例约 6.33%，低于 mature profile 10% 阈值；只进入周度 triage |
| review queue pending | 0 | 普通 AI/external review queue 已清零 |
| stale review_after | 0 | item/source stale 均为 0 |
| 30-day near-due item | 0 | 18 条 Codex archive near-due item 已刷新到 2026-11-09..2026-11-11 |
| mature blocker | 0 | mature audit `status=pass` |
| changed orphan file | 0 | 当前变更文件均已通过 registry/index 覆盖 |
| reviewing triage | 3 owner-ready + 3 evidence-backed + 14 keep-reviewing | P1 五条已从粗粒度待办转为可执行 validation pending；新增 PCR02 validation paths 作为 evidence-backed validation pending |
| owner gate open | 0 | PCR02 owner gate 当前无打开项 |
| full regression baseline | 140 个回归结果场景 | 2026-07-13 mature full gate `final_status=ok`，full regression `failed_ids=[]`；后续性能只盯 slowest 10，不泛化重构 |

## 历史基线

| 日期/阶段 | registry | active | archived | reviewing | 说明 |
|---|---:|---:|---:|---:|---|
| 2026-07-01 运营尾巴收口 | 246 | 未单列 | 未单列 | 0 | 27 个 2026-07 near-due item 刷新到 2026-10-16..2026-10-18；Hub 内部 review 尾巴闭环，但不代表外部 owner/content/source 签收 |
| 2026-07-11 mature closeout 增量 | 306 | 16 | 275 | 15 | summary 缺口、普通 review queue、stale review_after 和 mature blocker 均清零 |
| 2026-07-11 长期运营工具增强 | 311 | 16 | 276 | 19 | 新增 orphan、reviewing triage、regression trend，并把 changed-only orphan 与 reviewing triage 接入 health summary |
| 2026-07-11 长期运营计划固化 | 312 | 16 | 277 | 19 | 固定 daily/weekly/monthly/release 节奏、reviewing 处置规则、full regression 趋势摘要和远端发布授权边界 |
| 2026-07-11 P1/P2/P3 优化闭环 | 314 | 16 | 279 | 19 | P1 五条改为 owner-ready/evidence-backed validation pending，P2 将 mature release gate 压到 55 秒，P3 拆清当前/历史基线 |
| 2026-07-13 运营审计与验证路径 | 316 | 16 | 280 | 20 | 18 条 Codex archive near-due 刷新到 2026-11；新增 PCR02 owner-ready validation paths；mature full gate 通过 |

## 终态成熟条件

- 目标成熟：Hub 是统一知识控制面，能回答“事实在哪、依据是什么、谁负责、何时复核、如何回滚”。
- 功能成熟：分类、registry、source、owner、review_after、search、context、status、check、final gate 形成闭环。
- 性能成熟：日常命令轻量，release 级 `--full-regression` 可作为重门禁；慢查询通过 `slowest_results` 定位。
- 可维护性成熟：正文只维护一份，索引可重建，历史治理制品只进台账，自动化默认 report-only。
- 可交付成熟：任何交付声明必须能映射到命令证据、registry item、索引入口和回滚边界。

## 运营节奏

### Daily

```bash
rtk bash ~/knowledge-hub/tools/knowledge-health-summary.sh --json --as-of 2026-07-13
rtk bash ~/knowledge-hub/tools/knowledge-status.sh --json --as-of 2026-07-13
rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
rtk bash ~/knowledge-hub/tools/knowledge-review-after.sh --as-of 2026-07-13 --window-days 30 --json
rtk bash ~/knowledge-hub/tools/knowledge-orphan-files.sh --json
```

### Weekly

```bash
rtk bash ~/knowledge-hub/tools/knowledge-health-summary.sh --json --as-of 2026-07-13 --skip-final-gate
rtk bash ~/knowledge-hub/tools/knowledge-review-after.sh --as-of 2026-07-13 --window-days 30 --json
rtk bash ~/knowledge-hub/tools/knowledge-reviewing-triage.sh --json --as-of 2026-07-13
rtk bash ~/knowledge-hub/tools/knowledge-index-plan.sh --section linking --json
rtk bash ~/knowledge-hub/tools/knowledge-search.sh "Knowledge Hub mature" --json --limit 8
rtk bash ~/knowledge-hub/tools/knowledge-search.sh "成熟态" --json --limit 8
rtk bash ~/knowledge-hub/tools/knowledge-search.sh "review_after" --json --limit 8
rtk bash ~/knowledge-hub/tools/knowledge-search.sh "PCR02 归档路径" --json --limit 8
```

### Release Gate

```bash
rtk git status --short
rtk git diff --check
rtk bash ~/knowledge-hub/tools/knowledge-orphan-files.sh --json --strict
rtk bash ~/knowledge-hub/tools/knowledge-final-gate.sh --json --final-profile mature --full-regression --as-of 2026-07-13
rtk bash ~/knowledge-hub/tools/knowledge-regression-trend.sh --run --suite full --as-of 2026-07-13 --json
rtk bash ~/codex/scripts/final-ready.sh
```

## 2026-07 运营重点

1. 2026-07-01 已刷新 PCR02 近期待复核批次：23 个 `team-core` 条目延后至 2026-10-16，1 个 2026-07-17 条目延后至 2026-10-17，3 个 2026-07-18 条目延后至 2026-10-18。
2. 2026-10 窗口前仍可安排真实 owner/content review；本次闭环只关闭 Hub 内部 review 尾巴，不替代 owner 内容复核。
3. 10 个 PCR02 archive-only 条目仍只作为历史证据，不提升 active fact。
4. 4 个历史 owner-review artifact 只作为人工复核提示，不自动补 `source_id`，不反推出 owner approval。
5. ASAN 非 PCR02 实操证据保持为外部增强输入，不伪造跨项目验证结论，不再作为成熟态或完整交付剩余运营阻塞。
6. 正式交付前保持 Git 快照、远端推送和门禁输出可追溯。

## 搜索验收查询

| 查询 | 期望命中 |
|---|---|
| `Knowledge Hub mature` | 本状态页、README mature profile、final gate 相关制品 |
| `成熟态` | 本状态页、成熟态目标和 mature profile 说明 |
| `review_after` | 运营计划、review_after 工具、近期待复核说明 |
| `PCR02 归档路径` | PCR02 archive-only 目标、归档路径和 source control 证据 |
| `ASAN` | 团队级 runbook、PCR02 project-local runbook、active promotion 和 follow-up |
| `owner gate` | PCR02 owner decision landing、owner gates 工具和 owner gate 状态 |
| `source coverage` | 18 个 source 主控目录和 source control unification 证据 |

## 性能策略

- 日常使用 `knowledge-status.sh`、`knowledge-check.sh`、`knowledge-search.sh` 和 `knowledge-context.sh`。
- `knowledge-final-gate.sh --full-regression` 只作为 release 级或高风险脚本改动后的重门禁。
- 每次 high-risk tool/regression 改动后，用 `knowledge-regression-trend.sh` 将 full regression 的 `jobs`、`selected_test_count`、`result_count`、`slowest_results[0:10]` 和失败 ID 压缩进相邻 manifest 或交付说明；不保存大段 raw JSON。
- full regression 当前默认最多 4 worker 并行；如需诊断并行互扰，可临时用 `KNOWLEDGE_REGRESSION_JOBS=1` 回退串行。
- 若 full final gate 超过 3 分钟，先记录 `slowest_results`、命令环境和当次变更范围，再决定是否优化工具或拆分回归。
- 搜索性能优先看首屏相关性和 fallback 行为，不以全文扫描替代 registry/query 契约。

## 证据索引

| 命令 | 结果摘要 |
|---|---|
| `rtk bash ~/knowledge-hub/tools/knowledge-status.sh --strict --json --as-of 2026-07-01 --final-profile mature` | 退出码 0；`status=ok`；`strict_blockers=[]`；mature profile 通过 |
| `rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics --as-of 2026-07-01` | 退出码 0；errors=0；warnings=0 |
| `rtk bash ~/knowledge-hub/tools/knowledge-final-gate.sh --json --final-profile mature --full-regression --as-of 2026-07-01` | 退出码 0；final_status=ok；full regression 通过；blockers=[]；gap_map=[] |
| `rtk bash ~/knowledge-hub/tools/knowledge-review-after.sh --as-of 2026-07-01 --window-days 30 --json` | 退出码 0；near_due_items=0；stale_items=0；owner_gate_open_count=0 |
| `rtk bash ~/knowledge-hub/tools/knowledge-regression-trend.sh --run --suite full --as-of 2026-07-13 --json` | 退出码 0；regression_status=pass；result_count=140；failed_ids=[]；slowest 10 已记录到 `knowledge-hub-operational-audit-20260713` |
| `rtk bash ~/knowledge-hub/tools/knowledge-final-gate.sh --json --final-profile mature --full-regression --as-of 2026-07-13` | 退出码 0；final_status=ok；full regression 通过；blockers=[]；gap_map=[] |
| `rtk bash ~/knowledge-hub/tools/knowledge-review-after.sh --as-of 2026-07-13 --window-days 30 --json` | 退出码 0；刷新前 near_due_items=18；已按 2026-07-13 operational audit 刷新到 2026-11 窗口 |

## 剩余风险

- 已无 2026-07-13 30 天窗口内 near-due 运营阻塞；18 条 Codex archive near-due 已按 archive-only/provenance 边界刷新到 2026-11 窗口。
- ASAN 团队级 runbook 已 active；非 PCR02 项目实操证据仍是未来外部证据输入，已由 `embedded-asan-non-pcr02-evidence-followup-20260629` 和 `knowledge-hub-complete-delivery-closure-20260701` 固定边界，不作为完整交付阻塞。
- 完整交付仍需本地 Git 快照和远端 push 证据；本页只描述 Hub 成熟态运营，不代表 owner approval 或 source project write 授权。
- 本页不改变任何源项目、远端仓库、owner decision 或 memory 状态。

## 下一步

1. 在 2026-10-13 前复核 PCR02 owner-ready validation paths；在 2026-10-16 前按运营节奏安排 PCR02 内容复核；需要 owner 判断时只走 owner gate，不由 Codex 代签。
2. 每周运行 health summary 与 review_after 30 天窗口；发现 near-due 时先分类为 owner/content/source/tooling，再决定刷新排期、补证、归档或走 owner gate。
3. release 前运行 mature full final gate，并将实际输出写入交付说明或对应 manifest。
4. 新增真实 ASAN 非 PCR02 实机验证时，按 `templates/asan-validation-report.md` 生成项目本地验证记录，再回链到本 closeout。
