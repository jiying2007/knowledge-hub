# Knowledge Hub 运营成熟态状态 2026-07-01

## 结论

Knowledge Hub 已达到治理控制面和成熟态门禁可交付状态：registry、索引、source control、owner gate、review queue、final gate、search/context/status/check 工具链都有可验证入口，且 `mature` profile 能阻断迁移态残留和高比例 `reviewing` 滞留。

长期运营成熟态尚未等同于“无人值守完成态”。当前还需要按 review_after 节奏处理 2026-07-16 到 2026-07-18 的近期待复核批次，并持续补齐跨项目证据、owner 复核和脏工作区收口。本页是运营状态入口，不替代 final gate，不生成 owner decision，不关闭 owner gate，不提升 active，不写 memory，不修改源项目。

## 当前基线

| 指标 | 当前值 | 说明 |
|---|---:|---|
| registry item | 246 | 以 2026-07-01 运营状态登记后的门禁输出为基线 |
| Markdown 文档 | 588 | 知识正文、索引、治理材料和 manifest |
| JSONL 台账 | 221 | registry、manifest、授权和运行记录 |
| 工具入口 | 22 | search/status/check/context/final gate 等稳定 shell 入口 |
| registered source | 18 | 已有 Hub 内 source 主控目录 |
| 30 天 near-due item | 27 | review_after 运营队列，非 blocker |
| reviewing item | 24 | `mature` profile 阈值内，但需持续消化 |
| review queue pending | 0 | 普通 AI/external review queue 已清零 |
| owner gate open | 0 | PCR02 owner gate 当前无打开项 |

## 终态成熟条件

- 目标成熟：Hub 是统一知识控制面，能回答“事实在哪、依据是什么、谁负责、何时复核、如何回滚”。
- 功能成熟：分类、registry、source、owner、review_after、search、context、status、check、final gate 形成闭环。
- 性能成熟：日常命令轻量，release 级 `--full-regression` 可作为重门禁；慢查询通过 `slowest_results` 定位。
- 可维护性成熟：正文只维护一份，索引可重建，历史治理制品只进台账，自动化默认 report-only。
- 可交付成熟：任何交付声明必须能映射到命令证据、registry item、索引入口和回滚边界。

## 运营节奏

### Daily

```bash
rtk bash ~/knowledge-hub/tools/knowledge-status.sh --json
rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
rtk bash ~/knowledge-hub/tools/knowledge-review-after.sh --as-of 2026-07-01 --window-days 30 --json
```

### Weekly

```bash
rtk bash ~/knowledge-hub/tools/knowledge-review-after.sh --as-of 2026-07-01 --window-days 30 --json
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
rtk bash ~/knowledge-hub/tools/knowledge-final-gate.sh --json --final-profile mature --full-regression --as-of 2026-07-01
rtk bash ~/codex/scripts/final-ready.sh
```

## 2026-07 运营重点

1. 处理 2026-07-16 到 2026-07-18 的 PCR02 near-due 批次，优先 current / decision / runbook。
2. 优先消化 13 个 `team-core` current/reviewing 条目，避免 `reviewing` 比例长期接近 `mature` 阈值。
3. 确认 10 个 PCR02 archive-only 条目仍只作为历史证据，不提升 active fact。
4. 4 个历史 owner-review artifact 只作为人工复核提示，不自动补 `source_id`，不反推出 owner approval。
5. ASAN 非 PCR02 实操证据仍是 follow-up，不伪造跨项目验证结论。
6. 正式交付前按主题分组处理工作区改动，避免把无关历史改动混进本次成熟态产物。

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
- 若 full final gate 超过 3 分钟，先记录 `slowest_results`、命令环境和当次变更范围，再决定是否优化工具或拆分回归。
- 搜索性能优先看首屏相关性和 fallback 行为，不以全文扫描替代 registry/query 契约。

## 证据索引

| 命令 | 结果摘要 |
|---|---|
| `rtk bash ~/knowledge-hub/tools/knowledge-status.sh --strict --json --as-of 2026-07-01 --final-profile mature` | 退出码 0；`status=ok`；`strict_blockers=[]`；mature profile 通过 |
| `rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics --as-of 2026-07-01` | 退出码 0；errors=0；warnings=0 |
| `rtk bash ~/knowledge-hub/tools/knowledge-final-gate.sh --json --final-profile mature --full-regression --as-of 2026-07-01` | 退出码 0；final_status=ok；full regression 通过；blockers=[]；gap_map=[] |
| `rtk bash ~/knowledge-hub/tools/knowledge-review-after.sh --as-of 2026-07-01 --window-days 30 --json` | 退出码 0；near_due_items=27；stale_items=0；owner_gate_open_count=0 |

## 剩余风险

- review_after 批次仍需要人工或 owner 复核后才能延后、归档或变更状态。
- ASAN 团队级 runbook 已 active，但非 PCR02 项目实操证据仍是增强项。
- 完整交付仍需本地 Git 快照收口；本页只描述 Hub 成熟态运营，不代表远端发布、owner approval 或 push 授权。
- 本页不改变任何源项目、远端仓库、owner decision 或 memory 状态。

## 下一步

1. 按 `artifacts/manifests/knowledge-hub-review-after-operation-plan-20260701.md` 分批领取 2026-07 near-due 队列。
2. 每批处理后运行 `knowledge-check.sh --dry-run --json --diagnostics` 和 `knowledge-status.sh --strict --final-profile mature`。
3. release 前运行 mature full final gate，并将实际输出追加到对应 manifest 或交付说明。
