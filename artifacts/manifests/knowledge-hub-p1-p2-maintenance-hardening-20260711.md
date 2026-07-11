# Knowledge Hub P1/P2 Maintenance Hardening 2026-07-11

## Scope

本记录收口 Knowledge Hub 终态成熟后的 P1/P2 维护增强：summary backfill 专项回归、archived 摘要抽样质量审计、reviewing 周期 triage、短 health dashboard、full regression 性能趋势记录、维护文档瘦身入口和 review_after 运营节奏制度化。

本批次只写 Hub 本仓治理材料和只读工具，不生成 owner decision，不关闭 owner gate，不提升 active，不写 memory，不修改源项目，不发布远端状态。

## P1/P2 Result

| 项 | 结果 | 边界 |
|---|---|---|
| summary backfill regression | 新增 `summary-backfill-archived-only-contract`，覆盖 dry-run no-write、apply archived-only、active/reviewing untouched、manifest/index sync | fixture 只改 `/tmp` 临时副本 |
| archived summary audit | 抽样 20 条高价值 archived 摘要，覆盖 governance、PCR02 decision/current、patents、embedded、artifact-ref、Codex provenance | 只确认摘要不误导 active/owner/release 语义，不代表 owner 内容复核 |
| reviewing triage | 15 条 reviewing 已列入周度 triage 队列，当前比例约 4.90%，低于 mature 阈值 10% | 不自动 archive，不自动 active promotion |
| health dashboard | 新增 `knowledge-health-summary.sh`，输出总数、summary gap、review queue、stale review、mature blocker 和 final gate 摘要 | 只读；terminal gate 仍以 `knowledge-final-gate.sh` 为准 |
| full regression trend | 当前 live 目标升级为 136 个回归场景，后续记录 `selected_test_count`、`result_count` 和 `slowest_results` | 不保存大段 raw JSON |
| maintenance docs | README 和 tools README 增加 5 条短命令入口 | 不删除长文档，只降低首屏进入成本 |
| review_after cadence | 运营成熟态页固定 daily/weekly/release gate 节奏和 near-due 分类动作 | stale/near-due 是人工运营提醒，不是默认 blocker |

## Archived Summary Sample Audit

| # | Item | Domain/kind | Audit result |
|---:|---|---|---|
| 1 | `knowledge-hub-index-drift-remediation-20260619` | governance/audit | 摘要说明 registry/index 覆盖漂移治理，带 report-only/owner gate 边界，无 active 误导 |
| 2 | `knowledge-hub-registry-enum-gate-20260619` | governance/audit | 摘要聚焦枚举门禁和拼写漂移风险，无 owner decision 误导 |
| 3 | `knowledge-hub-manual-entry-guide-20260619` | governance/audit | 摘要明确只读人工向导，不暗示自动落盘 |
| 4 | `knowledge-hub-status-dashboard-20260619` | governance/audit | 摘要说明状态总览和 owner/stale/active exposure 可观测性，不替代 final gate |
| 5 | `knowledge-hub-final-gate-20260620` | governance/audit | 摘要记录终态聚合入口，保留不生成 owner decision 边界 |
| 6 | `knowledge-hub-governance-regression-helper-20260619` | governance/audit | 摘要说明 regression fixture 在 `/tmp` 运行，不写真实仓库 |
| 7 | `knowledge-hub-source-coverage-closeout-20260619` | governance/audit | 摘要说明 source 覆盖终态边界，不把外部来源误当 active fact |
| 8 | `knowledge-hub-owner-decision-landing-plan-20260619` | governance/audit | 摘要强调只读人工落地计划，不代表 owner 已签收 |
| 9 | `pcr02-diag-command-architecture-final` | projects/pcr02/decision | 摘要保留历史 decision provenance 边界，不声明当前 active 决策 |
| 10 | `pcr02-project-detailed-design` | projects/pcr02/decision | 摘要来自正文片段，带 archived decision provenance 边界 |
| 11 | `pcr02-diag-v4-hybrid-refcount-discovery-spec` | projects/pcr02/decision | 摘要描述历史设计方向，不声明当前发布状态 |
| 12 | `pcr02-build-and-deploy-guide` | projects/pcr02/project-current | 摘要说明历史 retired-source provenance，不代表当前项目事实 |
| 13 | `pcr02-prog-tool-usage-guide` | projects/pcr02/project-current | 摘要说明 prog_tool 用途，同时带 archived retired-source 边界 |
| 14 | `pcr02-diag-usage-guide` | projects/pcr02/project-current | 摘要面向测试人员场景，无 active/release 误导 |
| 15 | `pcr02-third-party-libraries-reference` | projects/pcr02/project-current | 摘要保留项目本地边界，不提升团队标准 |
| 16 | `patent-disclosure-canonical-archive-corpus` | patents/patent | 摘要明确只作专利材料检索，不代表法律复核或正式提交 |
| 17 | `patent-disclosure-artifact-ref-manifest-20260619` | patents/audit | 摘要说明附件身份和 vault 边界，不声明公开授权 |
| 18 | `embedded-knowledge-owner-review-gate-20260619` | embedded/audit | 摘要保留 embedded 历史治理边界，不提升 active 标准 |
| 19 | `pcr02-prog-tool-ci-smoke-session-ref-20260618` | projects/pcr02/artifact-ref | 摘要只登记 artifact identity，不代表测试复核或发布许可 |
| 20 | `codex-archive-reference-boundary-20260619` | codex/audit | 摘要说明 Codex archive provenance，不写 memory、不改变运行态 |

结论：20 条样本均保留 archived/provenance 边界；未发现把历史证据误写成 active fact、owner decision、release signoff、memory write 或 source project write 的摘要措辞。剩余 105 条未抽样 archived 摘要仍按 registry/check/final gate 覆盖；后续只在人工发现误读风险时做定向修订。

## Reviewing Triage Cadence

当前 15 条 reviewing 不作为 mature blocker；按周度 triage 处理：

| Queue | Item ids | Default action |
|---|---|---|
| Codex archive deletion / tombstone provenance | `codex-archive-extract-first-preflight-20260710`, `codex-archive-migration-preflight-20260709`, `codex-archive-phased-migration-removal-20260709`, `codex-archive-removal-preflight-20260710`, `codex-knowledge-hub-final-hardcut-tombstone-audit-20260710` | 保持 reviewing，等后续删除/coverage 批次确认是否 archive |
| Codex runtime / memory governance | `codex-adk-hardcut-source-to-live-audit-20260710`, `codex-archive-memory-curation-file-level-audit-20260710`, `codex-openai-local-runtime-boundary-20260524`, `codex-token-efficiency-roadmap-coverage-20260710` | 需要 freshness 或 memory candidate 边界复核后再决定 archive |
| PCR02 camera decision candidate | `pcr02-camera-raw-preview-virtual-stream-architecture-20260711` | 保持 decision candidate；不得提升 active 或 release signoff，除非 owner/release 证据进入决策流程 |
| PCR02 high-load debug records | `pcr02-prog-pcr02-high-load-debug-runbook-20260702`, `pcr02-prog-pcr02-high-load-monitoring-20260702`, `pcr02-prog-pcr02-high-load-third-capture-20260702`, `pcr02-prog-pcr02-runtime-hot-thread-followup-20260710`, `pcr02-prog-pcr02-source-hot-thread-capture-20260702` | 保持 debug evidence reviewing；等源码/驱动计数或 owner 判断后 archive 或拆 active runbook |

周度动作：

1. 运行 `rtk bash ~/knowledge-hub/tools/knowledge-health-summary.sh --json --as-of 2026-07-11 --skip-final-gate`。
2. 运行 `rtk bash ~/knowledge-hub/tools/knowledge-review-after.sh --as-of 2026-07-11 --window-days 30 --json`。
3. 对 near-due/reviewing 分为 `owner-needed`、`content-evidence-needed`、`archive-ready`、`keep-reviewing`。
4. 只有真实 owner/evidence 到位时才改 status 或 promotion；Codex 不代签 owner decision。

## Regression Performance Trend

性能趋势只保留摘要，不保存 full regression 大段 JSON。

| Metric | Current target | Record rule |
|---|---:|---|
| full regression scenes | 136 | helper manifest 覆盖表必须同步 |
| full selected test functions | 133 | 以 live `selected_test_count` 为准 |
| slowest results | top 10 | 写入收口说明或相邻 manifest |
| threshold | 3 分钟 | 超过后记录命令环境、慢测和变更范围，再决定优化 |

## Validation Plan

- `rtk bash -n tools/knowledge-health-summary.sh`
- `rtk bash -n tools/knowledge-summary-backfill.sh`
- `rtk bash -n tools/knowledge-regression.sh`
- `rtk bash ~/knowledge-hub/tools/knowledge-health-summary.sh --json --as-of 2026-07-11 --skip-final-gate`
- `rtk bash ~/knowledge-hub/tools/knowledge-regression.sh --json --suite full --as-of 2026-07-11`
- `rtk bash ~/knowledge-hub/tools/knowledge-final-gate.sh --json --final-profile mature --as-of 2026-07-11`
