---
related:
- indexes/obsidian-home.md
maturity: null
security_classification: null
human_reviewed_by: null
human_reviewed_at: null
review_basis: null
id: knowledge-hub-target-architecture-p1-p3-implementation-20260730
title: Knowledge Hub 目标架构与 P1-P3 全量落地计划 2026-07-30
kind: architecture
domain: governance
path: governance/product/current/knowledge-hub-target-architecture-p1-p3-implementation-20260730.md
scope: team-general
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: manual
  from: manual-entry:knowledge-new.sh
  source_sha256: 68775bd5dc006985341ca28b46ed04a033e262dacbdea74efdb8973dea650896
review_after: '2026-10-30'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- knowledge-hub
- architecture
- implementation
- recovery
validation_refs:
- governance/product/current/knowledge-hub-target-architecture-p1-p3-implementation-20260730.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- governance/product/current/knowledge-hub-target-architecture-p1-p3-implementation-20260730.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-07-30'
updated_at: '2026-07-31'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-07-30'
manual_validation_pending: true
summary_zh: 将五平面目标架构、P1 公共体验与运营指标、P2 状态解耦与制品治理、P3 独立环境恢复证据转为可执行契约、实现、测试和长期资产。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
aliases:
- Knowledge Hub 目标架构与 P1-P3 全量落地计划 2026-07-30
---

# Knowledge Hub 目标架构与 P1-P3 全量落地计划

## 一、目标与边界

### 目标

把综合评估中的五平面目标架构和 P1、P2、P3 路线图转为本仓可执行实现：

1. 体验平面：固定 5 条日常命令，其他入口明确分层。
2. 查询平面：统一有界摘要、状态和隐私保护的失败反馈闭环。
3. 治理平面：把平台健康、内容治理、项目证据和交付终态分开表达。
4. 正文与制品平面：建立 artifact 容量预算、不可变外部引用和恢复契约。
5. 证据与运营平面：建立 reviewing 生命周期指标、复杂度预算和独立环境恢复演练。
6. 硬切换：删除运行时兼容字段、旧状态别名和重复权威投影；新 consumer 只能使用当前 schema，旧 consumer 直接失败。

### 非目标

- 不代替 owner 完成内容审查、项目证据签收或 active promotion。
- 不伪造远端发布、外部对象存储、设备、生产回滚或长期采用证据。
- 不静默删除 runtime、artifact、archive 或用户既有 dirty 变更。
- 不新增常驻 daemon，不引入网络依赖，不放宽授权和 secret 边界。

### 成功标准

- 公共命令面有机器可验证的五平面、五层级 catalog；5 条 daily 入口固定，wrapper 数量不增长。
- 大输出入口具备统一 `--summary-json`；公共状态只允许 `pass / needs-review / needs-fix / blocked`，未知或旧别名直接失败。
- reviewing 年龄、吞吐、首次人工决定 lead time 和冷候选建议可被 report-only 查询。
- final gate 明确输出 platform、content、project evidence、delivery 和 adoption 五个相互独立的成熟度轴。
- 大模块至少完成纯逻辑边界拆分，公共 JSON contract 与回归行为不漂移。
- artifact budget、不可变 external ref、hash/size/owner/restore 字段可自动校验。
- zero-hit/not-found 形成脱敏、去重、有界、report-only 的改进队列。
- committed HEAD 可在独立临时环境完成固定 revision、hash-bound、无网络恢复演练；真实 remote/offsite 只能由受信执行环境证明。
- 定向测试、全量 pytest、Ruff、mypy、schema、检索、恢复、full regression 和最终门禁均有可复跑证据；若受既有基线阻断则显式列出。

## 二、阶段与依赖

```text
T1 公共 contract 与 command catalog
  -> T2 生命周期/反馈/复杂度运营指标
  -> T3 产品成熟度分轴与模块拆分
  -> T4 artifact budget 与 immutable ref
  -> T5 offsite restore contract 与独立环境演练
  -> T6 全量集成验证与长期资产更新
```

| 阶段 | scope_write | 完成条件 | 定向验证 |
| --- | --- | --- | --- |
| P1-A | command catalog、CLI output contract、metrics/status | daily=5、wrapper 不增长、summary 有界、状态映射唯一 | shell wrapper、CLI help、metrics/status tests |
| P1-B | lifecycle metrics、complexity budget | 年龄/吞吐/lead time/cold candidate 与复杂度趋势可查 | lifecycle、metrics、engineering tests |
| P2-A | product gate schema/projection、status projection | 平台与项目 evidence 独立；旧字段、旧版本和别名被拒绝 | product gate、schema、regression |
| P2-B | check/status/owner/search 纯逻辑模块 | 依赖单向、公共行为不变、重复策略减少 | unit、mypy、full regression |
| P2-C | artifact budget/ref contract、feedback queue | report-only、hash-bound、无自动删除/外部写入 | artifact、metrics/security tests |
| P3 | restore schema/runner/evidence | fixed revision、独立目录、无网络、来源不变；外部声明 fail-closed；旧 restore schema 被拒绝 | restore tests、candidate/head drill |
| 收口 | docs、registry、validation | 全量证据索引、风险和回退完整 | final-ready、knowledge gates |

## 三、2026-07-31 Breaking Cutover 契约

### 硬切范围

1. `status-contract-v2` 只接受四个 canonical status；删除 alias normalization、`canonical_status` 和 `legacy_status` 输出。
2. Product full contract 升为 `final-gate-product-v5`，summary 升为 v4。
3. Product 顶层只保留一个 `status` 和一个 `terminal`；技术、内容、项目 evidence、交付和采用状态只从 `maturity_axes` 与对应 detail section 读取。
4. 删除 Product 顶层 `gate_status`、`final_status`、`maturity_status`、`overall_status`、`platform_productization_complete`、`local_delivery_complete`、`remote_published`、`offsite_restore_verified`、`adoption_ready`。
5. 删除 Product 的 `retrieval`、`operations`、`summary` 重复投影；分别只保留 `retrieval_quality`、`operational_readiness` 和独立 summary CLI projection。
6. Health full contract 升为 v3、summary 升为 v2；删除 `health_status`，唯一顶层状态为 `status`，旧 Product snapshot 直接判 stale。
7. Restore contract 升为 `restore-drill-v4`；失败状态从 `fail` 硬切为 `needs-fix`，v3 不再进入 catalog。
8. README、工具说明、schema catalog、测试和内部 consumer 同步切换；不提供 alias、shim、双写、旧版本解析或降级路径。

### 明确保留

- 历史知识正文中的“兼容性”术语和既有 evidence provenance。
- 检索基准的 compatibility-pollution 检测，它用于证明旧入口没有泄漏。
- 正常的无状态 fallback，例如索引不可写时回退只读扫描；这不是旧 API 兼容层。
- 复杂度预算中的 historical/legacy debt 标签；它只描述技术债务，不提供运行时兼容行为。

### Breaking 验收

- 当前公共 schema catalog 只暴露 v5/v4/v2，不包含 Product v4、Restore v3、status v1。
- 新输出中不存在上述 forbidden fields；向 v5 schema 注入任一旧字段必须校验失败。
- `status_contract("ok")`、`status_contract("fail")`、`status_contract("needs-owner-review")` 和未知状态必须抛错。
- Product、Health、Restore 的文本、full JSON、summary JSON、快照 consumer 与 regression 全部切换到新字段。
- 仓库文档不得再指导 consumer 读取旧字段或声明迁移兼容期。

## 四、测试策略

- Test Level：Level 2。
- 原因：变更公共 JSON contract、状态语义、恢复证据和共享逻辑。
- 红灯要求：先建立旧状态别名仍被接受、Product/Health 仍输出 forbidden fields、Restore v3 仍被 catalog 接受的失败用例。
- 绿灯要求：定向测试后执行全量 pytest、Ruff、mypy、schema、retrieval benchmark、restore drill、full regression。
- 不可自动验证：真实远端 push、外部对象存储留存、生产回滚和人工 owner 签收；这些维度必须保持 pending，不得由本地模拟刷绿。

## 五、运行状态与防卡死

```yaml
goal_statement: 五平面目标架构与 P1-P3 本仓能力完全落地，运行时兼容层硬切删除，并对外部证据边界保持 fail-closed
completion_claim: repository-capability-complete
claimant: Codex
verifier: adk-verification-before-completion
retry_budget_per_gate: 2
staleness_threshold: 任一共享 contract 在下游实现前发生漂移即重新审查计划
heartbeat: 每完成一个阶段更新计划、测试证据和风险
stop_condition: pass | replan | split | blocked | abort
open_items: []
external_evidence_not_auto_closable:
  - human review
  - project source/device/release/rollback
  - clean commit and remote publish
  - same-run GitHub-hosted offsite restore
  - long-term adoption window
```

## 六、风险台账

| 风险 | 防护 |
| --- | --- |
| 现有 dirty 变更与本轮 registry/index 交叠 | 不回退、不重建覆盖；使用事务入口和局部 patch |
| 状态 schema breaking change | 接受显式不兼容；单次切换所有内部 consumer，schema 对旧字段 fail-closed，不提供双写 |
| dirty 工作树中的旧快照被误用 | 新 consumer 强制检查 schema version、candidate signature 与 freshness；旧快照直接 stale |
| 复杂度治理变成历史代码一次性红灯 | 历史基线 report-only；只对新增恶化 fail |
| artifact 预算误删正文或制品 | 只报告与校验，不自动删除或迁移 |
| 本地环境冒充 offsite | 只有受信 provider、匹配 revision、remote event 和独立 runner 同时满足才为真 |
| full regression 被既有内容阻断污染 | 记录原始 blocker；修复必须保持用户内容且单独验证 |
| UTC 与本地日期跨午夜导致动态门禁漂移 | regression 默认日期与公共 CLI 统一使用 host-local calendar；关键取证继续显式传 `--as-of` |

## 七、验证与证据

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
| --- | ---: | --- | --- | --- | --- |
| `rtk bash ~/knowledge-hub/tools/knowledge-new.sh ... --kind plan` | 2 | `plan` 不是允许的 item kind；改用 `architecture`，没有产生半截事务。 | CLI output | Knowledge Hub | 本文 |
| `rtk bash ~/knowledge-hub/tools/knowledge-new.sh ... --kind architecture --apply --json` | 0 | 计划以 reviewing architecture 事务落盘，未提升 active。 | `.tmp/transactions/kh-20260730T150010Z-6f874123/journal.json` | Knowledge Hub | 本文 |
| `rtk bash ~/knowledge-hub/tools/ci/python-runtime.sh -m pytest -q` | 0 | 全量 299 项 pytest 通过；breaking contract、代际隔离、热路径 schema 一致性、复杂度、full regression 与 restore 重试证据均有测试覆盖。 | stdout | Tool | 当前候选 |
| `rtk bash ~/knowledge-hub/tools/knowledge-engineering-check.sh --mode full --summary-json` | 0 | 修复 UTC/本地日期跨午夜漂移后，13 个工程、供应链、覆盖率和 SBOM 子门禁全绿。 | `.cache/knowledge-hub/engineering-quality.json` | Tool | 当前候选 |
| `rtk bash ~/knowledge-hub/tools/knowledge-retrieval-benchmark.sh --summary-json` | 0 | 302/302；warm P95 139.82 ms，并发 P95 670.27 ms。 | stdout | Knowledge Hub | 当前候选 |
| `rtk bash ~/knowledge-hub/tools/knowledge-restore-drill.sh --source-mode candidate --as-of 2026-07-31 --summary-json` | 0 | 冻结 candidate 全量文件完成 signature-bound 恢复，v4 schema 通过，未联网。 | `.cache/knowledge-hub/restore-drill-candidate.json` | Tool | 当前候选 |
| `rtk bash ~/knowledge-hub/tools/knowledge-restore-drill.sh --source-mode head --as-of 2026-07-31 --summary-json` | 0 | 当前 committed HEAD 1388 文件恢复通过；remote/offsite 正确保留 false。 | `.cache/knowledge-hub/restore-drill-head.json` | Tool | HEAD |
| `rtk bash ~/knowledge-hub/tools/knowledge-regression.sh --suite full --summary-json --as-of 2026-07-30` | 0 | 修复 fixture Git index 与文档 cwd-stable 兼容问题后，133/133 场景通过。 | stdout | Tool | 当前候选 |
| `rtk bash ~/knowledge-hub/tools/knowledge-final-gate.sh --summary-json --final-profile product --regression-suite full --reuse-engineering-evidence --as-of 2026-07-30` | 0 | technical hard checks 全绿；platform=pass，真实外部/人工轴保持 pending。 | `.cache/knowledge-hub/final-gate-product-full.json` | Knowledge Hub | 当前候选 |

### 2026-07-31 Breaking Cutover 证据

| Command | Exit Code | Result Summary | Evidence Path | Layer |
| --- | ---: | --- | --- | --- |
| `pytest` 定向 breaking suite（首次） | 1 | 6 个预期红灯锁定旧 Status/Product/Health/Restore contract。 | stdout | Test |
| `pytest` 定向 breaking suite（实现后） | 0 | 47/47 通过；旧 alias、旧 catalog ID 和 Product 禁用字段均被拒绝。 | stdout | Test |
| `rtk bash ~/knowledge-hub/tools/ci/python-runtime.sh -m pytest -q` | 0 | 293/293 通过。 | stdout | Test |
| schema catalog 实例验证 | 0 | 32/32 contract、763 个实例通过；仅保留 Product v5、Restore v4、Status v2。 | stdout | Schema |
| runtime compatibility residue scan | 1（无命中） | 运行时代码、schema、registry 无旧字段读取或旧 contract ID。 | stdout | Contract |
| `rtk bash ~/knowledge-hub/tools/knowledge-regression.sh --suite full --summary-json --as-of 2026-07-31` | 0 | 第二次完整回归 133/133；首轮 129/133 的 4 个旧 consumer 断言已定向修复。 | stdout | Regression |
| `rtk bash ~/knowledge-hub/tools/knowledge-retrieval-benchmark.sh --summary-json` | 0 | 302/302，兼容污染 0，warm P95 174.06 ms，并发 P95 638.62 ms。 | stdout | Retrieval |

### 2026-07-31 完成性复审

| 审计项 | 负向证据 | 修复与最终证据 |
| --- | --- | --- |
| command catalog 双向一致性 | `knowledge-recovery-audit` 实现支持 summary，但 catalog 误报 false | evaluator 改为双向比较；专用负向测试与 48/48 catalog 门禁通过 |
| 真实性能 | 初始 wrapper search P95 650.69 ms；第一阶段后 20 次 P95 511.13 ms | 解释器验证缓存、query/metrics 解耦和热路径 schema 子集后，20 次 P95 408.02 ms；benchmark warm 142.62 ms、并发 426.56 ms |
| telemetry 代际 | 旧慢样本与当前实现共用 performance contract | metrics v5 增加 implementation generation；旧契约 157、旧代际 389 个样本保留并显式排除，当前样本不足时为 pending |
| 依赖方向 | search 直接依赖重型 metrics 聚合 | query 只依赖 retrieval telemetry；metrics 反向聚合；105 模块、195 条内部 import edge 无环 |
| 复杂度与 coverage | 首轮全量 pytest 297/298；首轮 full engineering 12/13 | 拆分超 80 行函数；修复 `/tmp` fixture omit 后全量 299/299、coverage 77%、full engineering 13/13 |
| P3 恢复 | 当前候选不是 clean committed HEAD，不能冒充发布 | 冻结 candidate 全量文件与 committed HEAD 1388 文件均完成 v4 离线恢复；本地 remote/offsite 保持 false |

tracked 文件冻结后，full engineering、candidate/HEAD restore、Product full gate 和 final-ready 已按本计划命令重新执行；最终证据只绑定冻结后的 current candidate，不复用修改前签名。

## 八、恢复点

- 恢复入口：本文。
- 当前阶段：Status/Product/Health/Restore 单版本硬切、全部 consumer 清退、P1-P3 实现和最终签名绑定验证均已完成。
- 下一步：只剩不属于本仓能力实现的持续运营——owner 人工复核、项目真实 evidence、clean commit/remote publish、同 run GitHub-hosted offsite restore 与自然采用窗口；这些不会被 Codex 本地模拟关闭。
- 回退原则：新增字段可移除；默认值可恢复；不修改外部系统；不删除用户数据。

## Review

- owner：leiwenjun
- review_after：2026-10-30
- 下一次复核内容：目标架构、状态语义、artifact 预算、offsite 证明边界和全量验证证据。
