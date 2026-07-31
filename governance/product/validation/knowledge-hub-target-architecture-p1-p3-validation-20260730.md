---
related:
- indexes/obsidian-home.md
target_version: Knowledge Hub 目标架构 P1-P3 repository capability complete 2026-07-31
test_environment: Linux 本机隔离 Python 3.14 + /tmp restore/regression fixtures
human_reviewed_by: null
human_reviewed_at: null
review_basis: null
id: knowledge-hub-target-architecture-p1-p3-validation-20260730
title: Knowledge Hub 目标架构 P1-P3 落地验证 2026-07-30
kind: validation
domain: governance
path: governance/product/validation/knowledge-hub-target-architecture-p1-p3-validation-20260730.md
scope: team-general
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: manual
  from: target-architecture-implementation-verification
  source_sha256: 21383d3c228cbf679e64e8ec1ed7ec35de74b1486fd8cf8889b7599425569f30
review_after: '2026-10-28'
review_status: automated-validation-pass-manual-review-pending
content_review_status: pending
evidence_validation_status: verified
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- validation
- knowledge-new
- manual-validation-pending
validation_refs:
- governance/product/validation/knowledge-hub-target-architecture-p1-p3-validation-20260730.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: automated-validation-pass-manual-review-pending
evidence_refs:
- governance/product/validation/knowledge-hub-target-architecture-p1-p3-validation-20260730.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-07-30'
updated_at: '2026-07-31'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-07-30'
manual_validation_pending: true
summary_zh: 验证五平面目标架构、P1-P3 公共契约、生命周期与制品运营、成熟度分轴、复杂度预算、恢复证据链及季度演练已在本仓实现并通过自动化门禁；远端、异地、项目和人工证据继续 fail-closed。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
aliases:
- Knowledge Hub 目标架构 P1-P3 落地验证 2026-07-30
---

# Knowledge Hub 目标架构 P1-P3 落地验证

## 验证目标

证明以下能力已经进入本仓可执行实现，并由机器契约与回归覆盖：

1. 五平面、五层级命令 catalog 和固定 5 条 daily 入口。
2. 有界 summary、统一状态/退出码、reviewing 生命周期和脱敏检索改进队列。
3. 平台、内容、项目证据、交付、采用度独立成熟度轴。
4. 新代码复杂度预算、既有大模块防增长及纯逻辑边界拆分。
5. artifact 容量/增长预算、严格不可变引用和无自动上传/删除边界。
6. restore v4 同 run 受信证据、candidate/HEAD 离线演练和季度 GitHub-hosted workflow。
7. Status v2、Product v5/v4、Health v3/v2、Restore v4 单版本硬切换；旧状态别名、旧 schema 和重复顶层投影被拒绝。

本报告不证明真实 owner 已审阅 AI 候选、30 个项目已 evidence-ready、当前候选已经 commit/push、远端 workflow 已实际成功、生产回滚已验证或长期采用期已满足。

## 验证对象

- 工作树：`~/knowledge-hub` 当前 P1-P3 候选。
- 目标架构：`governance/product/current/knowledge-hub-target-architecture-p1-p3-implementation-20260730.md`。
- 评估蓝图：`governance/product/current/knowledge-hub-comprehensive-optimization-assessment-20260730.md`。
- 契约：`registry/command-surface.json`、`registry/engineering-budgets.json`、`registry/artifact-policy.json`、`schemas/catalog.json`。
- CI：`.github/workflows/quality.yml`、`.github/workflows/recovery-drill.yml`。

## 环境

- 本机 Linux，受控 `tools/ci/python-runtime.sh` 选择 Python 3.14。
- 依赖来自 `requirements-runtime.lock` / `requirements-dev.lock`，full engineering 使用 hash-locked 环境。
- restore 与 regression 在 `/tmp` 隔离副本执行，不修改源工作树。
- 未使用网络、设备实验室、远端写权限或外部对象存储凭证。

## 验证命令

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
| --- | --- | --- | --- | --- | --- |
| `rtk bash ~/knowledge-hub/tools/ci/python-runtime.sh -m pytest -q` | 0 | 全量 299 项 pytest 通过；包含旧状态别名/Product 禁用字段/旧 catalog ID 拒绝、metrics 代际隔离、热路径 schema 一致性和 Restore v4 验证。 | stdout | Tool | 当前候选 |
| `rtk bash ~/knowledge-hub/tools/ci/python-runtime.sh -m ruff check tools/codex_assets/knowledge_hub tests` | 0 | Ruff 全绿。 | stdout | Tool | 当前候选 |
| `rtk bash ~/knowledge-hub/tools/ci/python-runtime.sh -m mypy` | 0 | 配置内 19 个 source files 类型检查通过。 | stdout | Tool | 当前候选 |
| `rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --summary-json --diagnostics --as-of 2026-07-31` | 0 | canonical `status=pass`，status contract v2，error/warning 均为 0。 | stdout | Knowledge Hub | 当前候选 |
| `rtk bash ~/knowledge-hub/tools/ci/python-runtime.sh -c '...validate_schema_catalog...'` | 0 | 32 个 current contract 和 769 个实例全部通过；catalog 只暴露 Product v5、Restore v4、Status v2、Metrics v5。 | stdout | Schema | 当前候选 |
| `rtk bash ~/knowledge-hub/tools/knowledge-engineering-check.sh --mode contract --summary-json` | 0 | 命令面、复杂度和 artifact contract 全部通过。 | stdout | Tool | 当前候选 |
| `rtk bash ~/knowledge-hub/tools/knowledge-engineering-check.sh --mode full --summary-json` | 0 | Ruff、mypy、Bandit、coverage、build、299 项 pytest、Hub check、retrieval、133/133 full regression、dependency audit、SBOM 共 13 项全绿；coverage 77%。 | `.cache/knowledge-hub/engineering-quality.json` | Tool | 当前候选 |
| `rtk bash ~/knowledge-hub/tools/knowledge-retrieval-benchmark.sh --summary-json` | 0 | 302/302；Hit/MRR/nDCG/authority/route 均 1.0；warm P95 142.62 ms，并发 P95 426.56 ms，五类污染为 0。 | stdout | Knowledge Hub | 当前候选 |
| 20 次真实 `rtk bash ~/knowledge-hub/tools/knowledge-search.sh ... --no-telemetry` | 0 | wrapper 端到端 P50 391.40 ms、P95 408.02 ms、最大 420.60 ms，低于 500 ms 目标。 | stdout | Knowledge Hub | 当前候选 |
| `rtk bash ~/knowledge-hub/tools/knowledge-link-audit.sh --summary-json --strict` | 0 | 738 个 Markdown、911 个标准链接 blocking broken 为 0，managed frontmatter 覆盖率 100%。 | stdout | Knowledge Hub | 当前候选 |
| `rtk bash ~/knowledge-hub/tools/knowledge-orphan-files.sh --all --strict --limit 20` | 0 | 342 个正文全部受精确 registry 或冻结集合覆盖。 | stdout | Knowledge Hub | 当前候选 |
| `rtk bash ~/knowledge-hub/tools/knowledge-restore-drill.sh --source-mode candidate --as-of 2026-07-31 --summary-json` | 0 | 冻结 candidate 全量文件完成 signature-bound 离线恢复，内部检查零失败，restore-drill-v4 schema 通过，未使用网络。 | `.cache/knowledge-hub/restore-drill-candidate.json` | Tool | 当前候选 |
| `rtk bash ~/knowledge-hub/tools/knowledge-restore-drill.sh --source-mode head --as-of 2026-07-31 --summary-json` | 0 | 固定 revision 的 committed HEAD 1388 个文件离线恢复；本地 remote/offsite 保持 false。 | `.cache/knowledge-hub/restore-drill-head.json` | Tool | HEAD |
| `rtk bash ~/knowledge-hub/tools/knowledge-regression.sh --suite full --summary-json --as-of 2026-07-31` | 0 | 130 个测试函数产生 133/133 结果，全部通过。 | stdout | Tool | 当前候选 |
| `rtk bash ~/knowledge-hub/tools/knowledge-final-gate.sh --summary-json --final-profile product --regression-suite full --reuse-engineering-evidence --as-of 2026-07-31` | 0 | Product full v5 schema 与全部 technical hard checks 通过；platform=pass，外部与人工轴按真实证据保持 `needs-review`，terminal=false。 | `.cache/knowledge-hub/final-gate-product-full.json` | Knowledge Hub | 当前候选 |

补充说明：

- date：2026-07-31
- cwd：`~/knowledge-hub`
- scope：Knowledge Hub 本仓实现、隔离恢复、fixture 回归与本地工程供应链门禁。

### 外部与人工证据边界

```yaml
manual_validation_pending: true
manual_validation_reason: AI 生成验证候选仍需真实人工复核；remote/offsite workflow、项目 evidence 和长期采用不能由本地自动化代签
required_followup: 在合适的 clean committed HEAD 上由 GitHub-hosted recovery workflow 生成同 run v4 证据，并由 owner 审阅本报告
owner: leiwenjun
review_after: 2026-10-28
```

## 结果矩阵

| case | 期望 | 实际 | 状态 | 证据 |
| --- | --- | --- | --- | --- |
| 五平面命令面 | daily=5，wrapper 不增长，catalog 完整 | 48 个 wrapper，daily=5，增长 0 | 通过 | engineering contract |
| 公共状态与摘要 | 统一四态；daily 均有 summary | status contract v2；旧别名抛错，daily summary contract 全绿 | 通过 | pytest + command catalog |
| Product 单版本契约 | 顶层唯一 `status/terminal`，旧字段与重复投影拒绝 | full v5、summary v4；12 个旧顶层字段缺席，注入旧字段 schema fail | 通过 | schema + Product snapshot |
| Health 单版本契约 | 顶层唯一 `status`，旧 Product snapshot stale | full v3、summary v2；旧字段缺席 | 通过 | pytest + CLI smoke |
| 生命周期运营 | 年龄/flow/lead time/cold candidate 可查且只报告 | metrics v5 输出 144 reviewing、年龄桶、30 天 flow、lead time、13 个冷候选 | 通过 | metrics summary |
| 成熟度解耦 | platform 不被 project evidence 改写 | platform=pass；project evidence=0/30 pending | 通过 | product full gate |
| 复杂度预算 | 新增回归为 0；历史仅 attention | regression_count=0，legacy_attention_count=11 | 通过 | engineering contract |
| Artifact 治理 | 容量/增长/引用契约通过，无自动删除 | violation=0、binary manifest=0、strict v1 validator 通过 | 通过 | engineering contract + pytest |
| 检索反馈闭环 | 只存 hash/interaction，不自动写正文 | 8 个脱敏改进候选，automatic_content_write=false | 通过 | metrics summary |
| Candidate restore | 独立临时目录、无网络、hash-bound | 1447 文件、零失败、v4 schema pass | 通过 | candidate snapshot |
| HEAD restore | 固定 revision、无网络、hash-bound | 1388 文件、零失败、v4 schema pass；旧 v3 不再进入 catalog | 通过 | head snapshot |
| Offsite restore | 同 run GitHub-hosted 证据才允许 true | workflow 和 contract 已落地；本地三项均 false | 能力通过；外部证据待运行 | recovery workflow |

## 证据

- 工程快照：`.cache/knowledge-hub/engineering-quality.json`。
- 恢复快照：`.cache/knowledge-hub/restore-drill-candidate.json`、`.cache/knowledge-hub/restore-drill-head.json`。
- 产品快照：`.cache/knowledge-hub/final-gate-product-full.json`。
- 计划事务：`.tmp/transactions/kh-20260730T150010Z-6f874123/journal.json`。
- 验证条目事务：`.tmp/transactions/kh-20260730T153412Z-3c55fcc5/journal.json`。

负向证据分四层保留：

1. Breaking 红测首次运行产生 6 个预期失败，分别证明 Status 仍为 v1、Product/Health summary 仍为旧版、maturity 仍接受旧状态、catalog 仍暴露旧 ID、Restore 仍为 v3。实现硬切换后定向 47/47 通过。
2. full regression 首轮为 129/133，4 个失败均来自回归 consumer 仍断言旧根状态或 Product `today` 字段；定向修复后 4/4 通过，第二次完整回归 133/133。原失败摘要作为本节证据保留。
3. 完成性审计发现 `knowledge-recovery-audit` 实际支持 `--summary-json`、catalog 却声明 false；原 evaluator 只检查 true→missing，遗漏反向漂移。修复为双向比较，并新增 false→implemented 负向测试。
4. 真实性能基线先为 wrapper P95 650.69 ms，解释器缓存后仍为 511.13 ms；继续拆出 query telemetry、移除 query→metrics 聚合依赖并引入 fail-closed 热路径 schema 子集后，20 次 P95 降为 408.02 ms。首轮全量 pytest 297/298 的复杂度预算红灯、首轮 full engineering 12/13 的 `/tmp` coverage 路径红灯均保留；修复没有放宽 80 行函数预算或 75% coverage 阈值。

## 结论

P1、P2、P3 的本仓能力与目标架构已完全落地：breaking contract、单元测试、schema、Hub 门禁、真实 wrapper 性能、检索质量、复杂度、制品治理、candidate/HEAD 恢复、full regression、full engineering 和 Product full gate 均已通过冻结候选上的最终验证。

产品整体保持 canonical `needs-review`，不是实现失败：人工复核、30 个项目真实 evidence、当前候选的 clean committed delivery、远端发布、同 run offsite restore 和长期采用证据尚未闭环，工具必须保持 `terminal=false`。

## 剩余风险

- 当前工作树包含用户既有项目知识变更，未自动 commit；因此 candidate restore 证明当前完整工作树能力，HEAD restore 证明恢复机制能从当前 committed revision 工作。两者不会互相冒充发布状态。
- `.github/workflows/recovery-drill.yml` 已通过静态契约，但未经 push/dispatch 无法产生真实 GitHub run evidence。
- 真实项目 source/device/release/rollback 和人工 review 不在 Codex 可自动代签范围。
- 历史自然 telemetry 的旧契约 157 个样本、旧实现代际 389 个样本均保留在 usage/provenance；当前代际仅 1 个 warm search、2 个 warm context 样本，性能状态诚实保持 pending，长期采用仍需自然观测。

## 后续动作

1. owner 审阅本 validation candidate，不得由 Codex 代填人工复核字段。
2. 在合适的 clean commit 上运行季度 recovery workflow，保存同 run v4 证据；这需要用户决定远端发布时机。
3. 按现有 review queue 和项目 evidence contract 持续补真实证据，不以自动清零替代治理。
