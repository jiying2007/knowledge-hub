---
id: codex-token-efficiency-roadmap-coverage-20260710
title: Codex token efficiency roadmap 覆盖审计 2026-07-10
kind: audit
domain: codex
scope: team-general
visibility: team-internal
status: archived
owner: leiwenjun
review_after: '2026-08-24'
review_status: human-directed-delegated-retired
promotion: none
tags:
- codex-archive
- token-efficiency
- context-governance
- usage-tail
- usage-report
- archive-search
- caveman
- coverage-audit
- deleted-tombstoned
- no-memory-write
- no-active-promotion
generated_by_ai: true
ai_role: classified
ai_model_or_tool: Codex
ai_generated_at: '2026-07-10'
manual_validation_pending: false
summary_zh: 从旧 Codex archive 的错误 topic 文件中抽取 token/context efficiency 路线图覆盖审计：live Codex 资产已覆盖回答压缩、大输出裁剪、分层读取、HOT/CRITICAL/CTX_PRESSURE
  收口、archive-search 和 usage 观测；usage 归因仍为启发式，结构化代码导航 PoC 与长期 usage 时序未覆盖。旧正文已在独立授权批次中删除并 tombstone，不提升 active。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
promotion_decision: explicit human lifecycle decision delegated to Codex; direct content review not asserted; token=KH-ATTEST-db9b6021b6ab26585890;
  source=current-session exact hash-bound lifecycle attestation and reviewer binding on 2026-07-15
---

# Codex token efficiency roadmap coverage audit 2026-07-10

## 摘要

本记录从旧 Codex archive 抽取 `20260511-112520-codex-token-optimization-roadmap.md` 的长期价值，定位为 coverage audit，不是当前 active roadmap。

旧文件位于 `diag-architecture/`，但正文主题是 Codex token/context 使用效率治理，不属于 PCR02 diagnostic architecture。它不能跟随 PCR02 diag covered/removal 结论删除，也不能直接提升为当前 Codex 规则；后续已在独立授权批次中按 coverage audit tombstone 删除旧正文。

当前事实来源以 live Codex 资产为准；旧 archive 仅保留 provenance。

结构化台账：`artifacts/manifests/codex-token-efficiency-roadmap-coverage-20260710.jsonl`。

## Source Identity

| 字段 | 值 |
| --- | --- |
| source_path | `domains/codex/archive/codex-archive/diag-architecture/20260511-112520-codex-token-optimization-roadmap.md` |
| source_sha256 | `1caa3efc5d0c78b1aae5f769e93222800b919a3ba009512cee6c64ded37e6a83` |
| source_date | 2026-05-11 |
| size_bytes | 7451 |
| line_count | 105 |
| source_topic | `diag-architecture` |
| corrected_topic | `codex/token-efficiency` |
| preflight_row | `artifacts/manifests/codex-archive-extract-first-preflight-20260710.jsonl#CAEF-20260710-008` |

## Sanitization Verdict

结论：可抽取长期结论，但必须 reclassify。旧正文已在 `auth-20260710-codex-archive-delete-carp-004-006` 授权批次中删除，tombstone 保留 source identity、topic mismatch 和 rollback。

- 未发现典型 password、cookie、private key、API key、authorization header 或 bearer credential 形态。
- 未发现 raw log、core dump、session JSONL、完整 traceback、二进制或 release artifact 正文。
- 路径风险低，正文主要使用泛化路径 `~/codex`。
- topic 风险高：旧文件路径与正文主题不匹配，不能被 PCR02 diag canonical 覆盖。

## 覆盖矩阵

| 旧 roadmap 方向 | 当前覆盖状态 | 当前权威入口 |
| --- | --- | --- |
| 回答压缩、减少重复解释和低价值铺陈 | covered | `codex-live:AGENTS.md`、`codex-live:docs/codex-asset-management.md`、`live-skill:caveman` |
| 大日志、大 diff、大 JSON 先裁剪再读 | covered | `codex-live:docs/codex-asset-management.md`、`live-skill:adk-token-context-governance` |
| 分层摘要、原文回退和高风险原文门禁 | covered | `codex-live:docs/context-layout.md`、`live-skill:adk-token-context-governance` |
| HOT、CRITICAL、CTX_PRESSURE 后触发收口动作 | covered | `codex-live:AGENTS.md`、`codex-live:tools/codex_assets/session_coach_rules.py`、`codex-live:tools/codex_assets/usage_dashboard.py` |
| `archive-search` 稳定化、索引和 metadata 过滤 | covered | `codex-live:README.md`、`codex-live:docs/codex-asset-management.md` |
| `usage-report` / `usage-tail` 观测入口 | covered | `codex-live:README.md`、`codex-live:docs/codex-asset-management.md`、`live-skill:codex-usage-telemetry` |
| usage 归因 | partial | live 资产已有 `likely_operation_causes` 类启发式归因，但不是精确审计系统。 |
| memory、archive、agent memory 边界 | covered | `codex-live:docs/context-layout.md`、`codex-live:docs/codex-asset-management.md`、Hub no-memory-write policy |
| `code-review-graph` / `token-savior` 类结构化代码导航 PoC | not-covered | 未发现 live Codex 中已有 PoC、评估结论或正式实现。 |
| usage 快照沉淀为长期时序文件 | not-covered | 当前文档说明第一版不写长期时序文件；后续可另建 metrics JSONL 方案。 |

## 可保留结论

- 输出侧节流仍有效：长线程、上下文压力、HOT/CRITICAL 状态下，应减少重复背景、长过渡语和无证据铺陈。
- 读取侧节流仍有效：大文件、大日志和大 diff 先用索引、摘要和关键窗口定位，必要时再回退原文。
- 高风险任务不能只依赖压缩摘要：安全、权限、迁移、发布、生产故障、协议字段和签名校验等场景必须保留原文入口。
- usage telemetry 的长期目标是从“看到总量和速率”推进到“解释为什么消耗 token”，但当前只可声明启发式归因。
- archive/search 回用是减少重复解释背景的核心路径；不应因为旧 roadmap 提到候选工具就引入重型系统。
- memory 写入必须走候选审查；archive、memory、agent memory 不允许自动双写。

## 降级或丢弃项

- 2026-05-11 的“当前资产基线”只代表当时状态，不代表 2026-07-10 当前事实。
- `code-review-graph`、`token-savior` 只能保留为待评估候选，不能声明已采纳。
- “暂不引入重型 MCP / vector DB”是当时路线判断，不是永久禁令。
- Phase 1 到 Phase 4 和 P0/P1/P2 只作为历史路线图，不直接转成当前实施计划。
- 旧称 `knowledge-archive`、`memory-curator` 只能作为兼容线索；当前路由应以 adk-first 名称和 live registry 为准。

## 删除门禁

`delete_ready=true`，旧正文已由 `auth-20260710-codex-archive-delete-carp-004-006` 授权删除并登记为 `artifacts/manifests/codex-archive-removal-execution-20260710-token-patent-004-006.jsonl#CARE-20260710-010`。

删除后的保留边界：

- 保留 source path、source sha256、size、line count、topic mismatch 和本 coverage audit 引用。
- 保留 rollback 说明，恢复锚点为 `db07bd4839016d76f37218cd2b72857ed8575d48`。
- 明确该旧文件不能被 `projects/pcr02/decisions/diag-v4-hybrid-refcount-discovery-spec.md` 覆盖。
- 本 coverage audit 仍不是 active roadmap；`structured-code-navigation-poc` 和 `long-term-usage-timeseries` 仍为未覆盖候选。
- 验证 registry、core indexes 和迁移账本仍一致。

## Evidence Commands

```bash
rtk sha256sum domains/codex/archive/codex-archive/diag-architecture/20260511-112520-codex-token-optimization-roadmap.md
rtk wc -l domains/codex/archive/codex-archive/diag-architecture/20260511-112520-codex-token-optimization-roadmap.md
rtk wc -c domains/codex/archive/codex-archive/diag-architecture/20260511-112520-codex-token-optimization-roadmap.md
rtk file domains/codex/archive/codex-archive/diag-architecture/20260511-112520-codex-token-optimization-roadmap.md
rtk rg -n "长期省 Token|usage-tail|usage-report|archive-search|caveman|token-savior|code-review-graph" domains/codex/archive/codex-archive/diag-architecture/20260511-112520-codex-token-optimization-roadmap.md
rtk rg -n "usage-tail|usage-report|archive-search|caveman|CTX_PRESSURE|HOT|CRITICAL|上下文|裁剪|压缩|归因" ~/codex/AGENTS.md ~/codex/README.md ~/codex/docs/codex-asset-management.md ~/codex/docs/context-layout.md
```

## 验证计划

```bash
rtk jq -c . artifacts/manifests/codex-token-efficiency-roadmap-coverage-20260710.jsonl artifacts/manifests/codex-archive-extract-first-preflight-20260710.jsonl artifacts/manifests/codex-archive-removal-preflight-20260710.jsonl artifacts/manifests/codex-archive-phased-migration-removal-20260709.jsonl
rtk rg -n "(?i)(password|token|cookie|private[_ -]?key|secret)\\s*[:=]" artifacts/manifests/codex-token-efficiency-roadmap-coverage-20260710.md artifacts/manifests/codex-token-efficiency-roadmap-coverage-20260710.jsonl
rtk test ! -e domains/codex/archive/codex-archive/diag-architecture/20260511-112520-codex-token-optimization-roadmap.md
rtk bash ~/knowledge-hub/tools/knowledge-search.sh "Codex token efficiency roadmap"
rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run
```
