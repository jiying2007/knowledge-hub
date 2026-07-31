---
related:
- indexes/obsidian-home.md
maturity: null
security_classification: null
human_reviewed_by: null
human_reviewed_at: null
review_basis: null
id: knowledge-hub-comprehensive-optimization-assessment-20260730
title: Knowledge Hub 全维度评估与持续优化蓝图 2026-07-30
kind: audit
domain: governance
path: governance/product/current/knowledge-hub-comprehensive-optimization-assessment-20260730.md
scope: team-general
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: manual
  from: repository-audit
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
- maintainability
- performance
- long-term-assets
validation_refs:
- governance/product/current/knowledge-hub-comprehensive-optimization-assessment-20260730.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- governance/product/current/knowledge-hub-comprehensive-optimization-assessment-20260730.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-07-30'
updated_at: '2026-07-31'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-07-30'
manual_validation_pending: true
summary_zh: 基于实时仓库、治理门禁、检索性能、运行时占用和维护复杂度证据，评估 Knowledge Hub 的定位、目标、架构、功能、性能、可维护性与长期资产，并给出分阶段优化路线。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
aliases:
- Knowledge Hub 全维度评估与持续优化蓝图 2026-07-30
---

# Knowledge Hub 全维度评估与持续优化蓝图

## 摘要

Knowledge Hub 的存在价值成立，且当前已经具备可用的统一知识控制面：Markdown 正文、registry、生命周期、检索/context、项目路由、owner gate、恢复和产品门禁均有明确入口。当前主要矛盾已经从“能力不足”转为“产品运营与复杂度控制”。

下一阶段不应继续以增加工具、manifest 或全局终态字段为主要进展，而应围绕四个结果优化：

1. 使用者能在可接受延迟内找到正确、当前且可追溯的答案。
2. 当前事实、候选、历史证据和高风险授权不会相互污染。
3. review、运行时缓存、二进制制品和工具复杂度不会无限增长。
4. Hub 在没有 AI 的情况下仍可由开发者直接阅读、维护、验证和恢复。

本评估是 `reviewing` 候选，不是 owner decision，不自动改变 active、项目 evidence contract、发布状态或远端状态。

## 适用范围与非目标

适用范围：

- Knowledge Hub 自身的产品定位、目标、信息架构、工具链、检索性能、运营状态和长期资产。
- 当前仓库与本机忽略目录的只读证据，基准日期为 2026-07-30。
- 本轮已实现的低风险本仓优化及其验证结果。

非目标：

- 不代替源项目 README、源码、构建系统、发布系统和设备实验室。
- 不把 Hub 变成二进制仓库、通用任务管理器、聊天记录仓库或向量数据库。
- 不为 30 个项目生成虚假 artifact、device、release 或 rollback 证据。
- 不代签 owner decision，不自动清零人工复核队列，不自动提升 active。
- 不执行运行时删除；清理命令继续要求显式 `--apply`。

## 一、总体判断

### 1.1 结论

当前阶段可概括为：

```text
控制面可用，检索质量强，治理边界完整；
默认体验仍偏重，运营状态语义和长期成本需要继续收敛。
```

建议把 Knowledge Hub 的北极星从“所有项目和所有证据达到全局 terminal”调整为：

> 在正确权限与证据边界内，让人和 Agent 快速找到可追溯的当前答案，并以可控成本持续维护。

全局 `terminal` 适合作为一次性发布证据或特定批次验收，不适合作为长期知识系统的日常终点。知识系统天然持续变化，日常判断应优先使用 SLO、趋势和分轴状态。

### 1.2 维度评估

| 维度 | 当前判断 | 优势 | 主要缺口 |
| --- | --- | --- | --- |
| 存在意义 | 强 | 统一正文、项目事实、历史证据与高风险授权边界 | 需要持续证明减少查找时间和错误决策，而非只证明目录完整 |
| 目标模型 | 中上 | “Markdown Vault + 最小 registry + 高风险门禁”方向正确 | 全局 terminal 与 30/30 evidence-ready 容易让平台成熟度被外部项目永久绑架 |
| 架构 | 强 | SSOT、派生索引、可重建 cache、事务写入、五平面 catalog 和 fail-closed 边界清楚；查询生产者不再依赖运营聚合 | 11 个既有大模块仍为 report-only attention，需要持续防增长 |
| 功能 | 强 | 捕获、检索、context、review、恢复、导出、Obsidian 和门禁完整 | 48 个 wrapper 仍偏多，但已固定 5 条 daily 入口并由 catalog 约束 |
| 性能 | 强 | 302/302 检索质量；warm、并发和真实 wrapper P95 均达标 | 当前实现代际自然 telemetry 尚不足 10+10，长期采用仍需时间窗 |
| 可维护性 | 中上 | 锁定依赖、CI、恢复验证、复杂度预算、双向 command contract 与零依赖环 | Python 约 4.2 万行，多个 1,000–2,600 行历史模块仍需渐进拆分 |
| 长期资产 | 中上 | 中文摘要、owner、review_after、证据和 provenance 规则完整 | reviewing/archived 占比高，artifact 与运行时资产需容量预算和退出机制 |
| 安全与治理 | 强 | 授权、owner gate、秘密边界、raw evidence 和 report-only 自动化完善 | 治理规则多，需防止门禁本身成为主要维护对象 |
| 真实采用 | 中 | 17 天 550 次当前契约调用、10 条绑定反馈 | found rate 为 0.8；当前实现代际性能样本仍不足，adoption 保持 pending |

## 二、当前事实基线

### 2.1 内容与生命周期

评估开始时 registry 共 443 项：

- `active` 16 项，约 3.6%。
- `archived` 288 项，约 65.0%。
- `reviewing` 136 项，约 30.7%。
- `draft` 3 项。

这说明 Hub 的历史保留能力很强，但“当前可直接使用的权威知识”占比很小，候选治理成本较高。该比例本身不是错误；后续应关注 reviewing 年龄、消费价值和退出率，而不是单纯追求 active 数量。

评估时人工复核队列为 32 项，均为 AI 生成候选；其中 active 或 promotion 暴露为 0。正确处理方式是人工审阅、退回、归档或保留 reviewing，不能用自动填 reviewer 的方式清零。

### 2.2 代码与工具复杂度

2026-07-31 完成性复审盘点：

- Git 跟踪文件约 1,388 个，其中 `artifacts/` 约 641 个。
- Python 内核 105 个模块、约 42,249 行。
- 全量 pytest 299 项。
- `knowledge-*.sh` 公共 wrapper 48 个；相对 baseline 增长 0。
- 新模块/函数复杂度回归 0；11 个既有大模块只作 attention，不阻断历史基线。
- 最大模块包括 `check_cli.py`、`regression/lifecycle.py`、`regression/governance.py`、`owner_gates_cli.py`、`search.py` 和 `status_cli.py`，单文件约 1,900–2,685 行。

结论：系统已经超过“少量脚本”规模，应按产品内核管理。继续新增平行 CLI 或复制状态推断会显著增加回归成本。

### 2.3 检索与采用

基线真实 metrics：

- 当前契约调用 530 次，观察 16 天。
- search 144 次、context 386 次。
- search zero-hit 8 次，约 5.6%。
- 绑定真实 interaction 的 feedback 10 条，found 8、not-found 2，found rate 0.8。
- 历史 warm search P95 926.74 ms，高于 500 ms 目标。
- context P95 450.87 ms，低于 1,000 ms 目标。

已知答案 benchmark 在 302 个 search/route 用例上保持：

- hit rate 1.0。
- MRR 1.0。
- NDCG@10 1.0。
- Top-3 authority recall 1.0。
- route accuracy 1.0。

这些数字是评估开始时的历史基线。当前实现不删除或重写这些样本，而是用显式 `implementation_generation` 将它们保留在 usage/provenance，并从当前实现 SLA 中隔离；长期采用仍需自然积累。

### 2.4 存储与运行时

实时本机占用：

- 工作区总量约 468 MiB。
- `.git` 约 27 MiB，pack 约 16.27 MiB。
- tracked `artifacts/` 约 21 MiB。
- `.cache` 约 66 MiB。
- `.tmp` 约 335 MiB，其中事务约 166 MiB、工程验证环境约 166 MiB。

默认 30 天终结事务保留会保护 168 个事务目录，日常维护计划只暴露约 31 MiB 旧索引。只读模拟显示：

- 14 天保留、至少保留最新 20 个时，可规划约 82 MiB 候选。
- 7 天保留、至少保留最新 20 个时，可规划约 129 MiB 候选。

本轮采用 14 天作为默认规划值；删除仍需显式 `--apply`，未完成事务和 telemetry 继续受保护。

## 三、目标与产品模型优化

### 3.1 建议保留的核心定位

继续坚持：

```text
Knowledge Hub =
Obsidian-friendly Markdown Vault
+ 最小 registry 账本
+ 高风险授权与证据门禁
```

“最小”的含义应进一步量化：

- 普通 L0/L1 内容不要求进入完整治理链。
- 只有当前事实、决策、长期 runbook、跨项目标准和高风险动作进入强 registry/manifest。
- 派生 index、cache、dashboard 不拥有第二份正文。
- 新增一个公共入口必须替代或折叠旧入口，不能只增不减。

### 3.2 北极星指标

建议用以下指标代替“文件数量”或单一 `terminal`：

| 结果 | 建议指标 | 初始目标 |
| --- | --- | --- |
| 找得到 | known-answer Top-3 recall、zero-hit rate | recall 100%；真实 zero-hit < 5% |
| 找得对 | found rate、错误 authority 暴露 | found rate ≥ 0.85；错误 active 暴露为 0 |
| 找得快 | warm search、context、并发 P95 | ≤ 500 ms、≤ 1,000 ms、≤ 1,000 ms |
| 可追溯 | 当前知识 owner/source/review_after 覆盖 | active/current 100% |
| 可维护 | reviewing 年龄与退出率 | P1 7 天内处置；普通候选 30 天内有决定 |
| 可恢复 | candidate/HEAD/offsite restore | 每次发布验证 candidate/HEAD；按季度做 offsite |
| 成本可控 | runtime、tracked artifact、公共命令面 | 有预算、趋势、owner 和回收入口 |

### 3.3 平台成熟度与项目证据解耦

建议把成熟度拆成三个长期独立轴：

1. `platform_health`：工具、schema、检索、事务、恢复、CI 是否可靠。
2. `content_health`：当前知识 freshness、review debt、source/owner 覆盖。
3. `project_evidence_health`：每个项目独立报告 artifact/device/release/rollback。

不建议再要求 30 个项目全部 evidence-ready 才能证明 Hub 平台成熟。全局可以报告分布和关键项目阻断，但项目外部证据不应把平台本身永久标为未成熟。

## 四、目标架构优化

建议把现有能力明确收敛为五个平面：

```text
体验平面
  5 条日常命令 + Obsidian/Markdown
        |
查询平面
  search / context / map / evidence-pack
        |
治理平面
  registry / lifecycle / owner gate / authorization
        |
正文与制品平面
  Markdown SSOT / artifact-ref / bounded vault
        |
证据与运营平面
  check / metrics / restore / final gate / runtime maintenance
```

优化原则：

- 平面之间只通过稳定数据契约通信，不复制推断逻辑。
- `health`、`status`、`final gate` 分别承担首屏、诊断、终态证据，不重复生成不同版本的 blocker。
- shell wrapper 只负责 ROOT、`PYTHONPATH`、受支持 runtime 和转发。
- 大模块按“读取模型、策略判断、投影输出、CLI transport”拆分，优先拆无共享状态的纯函数。
- `artifacts/manifests/` 保持证据包，而不是新的文档默认入口。

## 五、功能与体验优化

### 5.1 公共命令分级

保留普通使用者首屏的 5 条命令：

1. `knowledge-health-summary`
2. `knowledge-new`
3. `knowledge-search`
4. `knowledge-review-after`
5. `knowledge-check`

其余命令分为：

- 维护层：runtime maintenance、metrics、restore、index plan、source check。
- 治理层：owner gate、promotion、review apply、authorization/evidence。
- 工程层：regression、engineering check、compliance eval、artifact restore drill。
- 内部层：只由其他入口或 CI 调用，不作为普通用户 API。

每新增公共命令必须回答：

- 不能由现有命令增加 subcommand 或 projection 解决吗？
- 是否有独立 owner、输入输出 schema 和退出码？
- 是否会增加 README 日常路径的认知成本？
- 可否同时退役一个旧入口？

### 5.2 CLI 一致性

后续统一要求：

- 数据量可能较大的 JSON CLI 同时提供 `--summary-json`。
- `--json` 为完整取证，`--summary-json` 为有界首屏。
- read-only、tracked writes、external writes、authorization requirement 使用统一字段。
- `pass`、`needs-review`、`needs-fix`、`blocked` 与退出码建立单一映射。
- 错误输出保留 `action_zh` 和最小重跑命令，不返回整份无界队列。

P1 已用 `registry/command-surface.json` 收敛 summary 支持声明，并由 command-surface 门禁双向比较 catalog 与实际实现；声明为支持但实现缺失、或声明为不支持但实现存在，都会失败。5 条 daily 入口全部提供有界 summary。

## 六、性能优化

### 6.1 已定位根因

修复前一次 warm search 的核心内部耗时约 158 ms，但 CLI 端到端为 0.9–1.55 秒。仅执行 Python runtime selector 的空命令就需要约 0.69–0.77 秒。

根因链：

```text
CLI 延迟高
-> 每个 wrapper 先运行 runtime selector
-> selector 启动 Python 并完整 import PyYAML/jsonschema
-> 随后再次启动 Python 执行真实 CLI
-> 固定双启动成本在并发查询下被放大
```

第一阶段将 selector 改为 `importlib.util.find_spec` 轻量依赖发现。完成性复审进一步证明每次调用仍有双 Python 启动：selector 空调用中位数 235.30 ms，直接解释器空调用中位数 92.39 ms；wrapper search 中位数 577.84 ms，而同一解释器直接执行 module 为 400.81 ms。

最终修复由三部分组成：

1. 首次完整验证后缓存“允许的绝对解释器 + 版本”，仅对公共 Hub module 复用；解释器、selector 或 runtime lock 漂移即失效。
2. 将查询生产者依赖的 telemetry contract/append 原语拆到轻量 `retrieval_telemetry.py`，由 metrics 反向消费，移除 query -> operations 聚合依赖。
3. retrieval-result-v3 热路径使用 fail-closed schema 关键词子集校验器；未知关键词直接失败，完整 Draft 2020-12 仍由 schema/full engineering 门禁执行。

### 6.2 修复后证据

- search import time 从约 173–184 ms 降至 89.76 ms。
- 20 次真实 `rtk bash ~/knowledge-hub/tools/knowledge-search.sh ... --no-telemetry`：P50 391.40 ms、P95 408.02 ms、最大 420.60 ms，达到端到端 500 ms 目标。
- benchmark warm search P95 142.62 ms。
- 4 worker / 8 query 并发 P95 426.56 ms。
- 302 个质量与路由用例全部通过，五类污染为 0。

一次完整 benchmark 在系统争用下出现 7.15 秒并发离群值；随后 1/2/4 worker 隔离实验分别约 573/534/533 ms，并再次完整通过。离群结果不删除，后续应保留趋势观测并在复发时记录 CPU、I/O 和 `rtk` 调度证据。

### 6.3 后续性能方向

当前性能优化项已落地：

1. wrapper 端到端 P95 已低于 500 ms，继续以 benchmark 与真实当前代际 telemetry 双轨观测。
2. `implementation_generation` 已落地：历史样本继续计入 usage/provenance，当前 SLA 只使用当前 performance contract 与实现代际；旧代际样本显式计入 `excluded_stale_generation_sample_count`。
3. schema validation 和进程启动占比已定向降低，不引入常驻服务。
4. 当前单进程模型满足 warm/并发 SLO，不启动 query daemon 评估；未来只有连续趋势失败且单进程优化耗尽时才重新决策。

## 七、可维护性优化

### 7.1 模块拆分顺序

优先处理同时满足“文件大、改动频繁、状态多”的模块：

1. `check_cli.py`：拆 schema、path、authorization、source 和 diagnostics projection。
2. `status_cli.py`：拆 live checks、review queue、owner gate 和 summary projection。
3. `owner_gates_cli.py`：拆 intake、form validation、landing plan 和 audit。
4. `search.py`：拆 corpus signature、index store、candidate retrieval、ranking 和 public contract。
5. regression 大模块：按产品域拆 fixture，runner 只负责编排与汇总。

拆分验收不是“文件变小”，而是：

- 公共 JSON contract 不漂移。
- 纯函数可单测。
- 子模块依赖方向单向。
- full regression 与 retrieval benchmark 不退化。
- 每次拆分至少删除一处重复策略或重复解析。

### 7.2 复杂度预算

建议建立 report-only 预算：

- 新模块默认不超过 800 行。
- 新函数默认不超过 80 行；超过需说明原因。
- 公共 wrapper 数量不增长，新增必须伴随退役或合并计划。
- 新 schema contract 必须有 producer、consumer、fixture 和升级策略。
- README 日常入口不超过 7 条。

预算先报告趋势，不立即作为历史代码硬失败，避免一次性机械拆分。

## 八、长期资产优化

### 8.1 生命周期债务

建议新增四个运营指标：

- reviewing 项按年龄分桶：`0–7 / 8–30 / 31–90 / >90` 天。
- 每月 reviewing 的新增、转 active、归档、拒绝和继续保留数量。
- 从 capture 到首次人工决定的 lead time。
- 90 天内没有被 search/context 命中的候选，仅生成“复核或归档建议”，不自动删除。

对 reviewing 条目只允许四种明确动作：

1. 补证据后继续 reviewing。
2. 人工接受并按规则提升。
3. 归档为历史证据。
4. 拒绝或 supersede，并保留原因。

### 8.2 Artifact 与 Git 增长

`artifacts/` 已占 tracked 文件约 46%，虽然当前 Git pack 仍约 16 MiB，但二进制增长具有不可逆历史成本。建议：

- `artifacts/manifests/` 只保留文本证据。
- `artifacts/vault/` 设置单文件、单集合和年度增长预算。
- 超过预算的二进制转为外部不可变 URI + SHA256 + size + restore drill。
- 每月报告 tracked binary 数量、总字节、最大对象和新增趋势。
- 不因 Obsidian 可见性要求复制附件正文。

### 8.3 归档价值

archive 不是越多越好。归档条目至少应满足一个条件：

- 能解释当前事实的 provenance。
- 能避免重复排障。
- 能支持版本回滚、事故复盘或专利证据。
- 能提炼为跨项目 runbook 的候选。

不满足上述条件的一次性日志、原始会话和机器输出继续只保留外部引用或短期 cache。

## 九、分阶段路线图

| 优先级 | 优化项 | 预期价值 | 风险 | 验收 |
| --- | --- | --- | --- | --- |
| P0 | runtime selector 首次验证与安全缓存 | 降低所有 CLI 固定延迟 | cache 失效边界错误 | wrapper 测试、锁/解释器失效、search P95、并发 probe |
| P0 | health 分轴状态 | 区分控制面故障、快照过期、内容待 owner 和运行时卫生 | consumer 未按 schema version 校验 | Health v3 顶层只保留 `status`，并提供 `health_axes` |
| P0 | 14 天终结事务规划 | 控制忽略目录增长 | 过早删除回滚材料 | 至少保留最新 20 个；未完成事务保护；显式 `--apply` |
| P1 | 公共命令分级与 summary 统一 | 降低日常认知与输出成本 | CLI contract 迁移 | 5 条日常入口稳定；大输出都有 summary |
| P1 | reviewing 年龄/吞吐 dashboard | 把候选积压变成可运营指标 | 被误用为自动清理 | report-only；人工决定仍必需 |
| P1 | 模块复杂度报告 | 防止继续形成 2,000 行单体 | 历史代码一次性噪声 | 先趋势后门禁；新代码受预算 |
| P2 | 平台与项目 evidence 成熟度解耦 | 避免平台状态被 30 个项目外部证据永久绑架 | 终态语义 breaking change | Product v5、单版本 consumer 回归、旧字段拒绝测试 |
| P2 | artifact 增长预算与外部不可变存储 | 降低 Git 长期成本 | 外部存储可用性 | hash、size、owner、restore drill |
| P2 | 零命中与失败反馈闭环 | 提升真实使用价值 | 隐私泄漏 | 继续只存 query hash 和绑定 interaction |
| P3 | offsite restore 与季度演练 | 证明灾难恢复能力 | 外部环境与凭证 | 独立环境、固定 commit、完整证据 |

## 十、本轮已实施变更

1. `tools/ci/python-runtime.sh`
   - 用轻量模块发现替代完整依赖 import。
   - 增加私有、可失效的已验证解释器缓存，消除 warm wrapper 的第二次 Python 启动。
   - 保持版本范围、绝对 injected interpreter 和缺失依赖 fail-closed。
2. `knowledge-health-summary`
   - 增加 `health_axes`。
   - 增加 report-only `runtime_maintenance` 摘要。
   - 运行时候选不自动改变综合状态，也不自动执行清理。
3. `knowledge-runtime-maintenance`
   - 默认终结事务保留从 30 天调整为 14 天。
   - 继续至少保留最新 20 个终结事务。
   - 继续保护未完成事务和 telemetry。
4. 文档与测试
   - 更新根 README 和工具说明。
   - 增加 runtime selector、14 天默认保留和 health 分轴测试。
5. P1 公共体验与运营
   - 建立 `registry/command-surface.json`，把 48 个 wrapper 收敛到五平面、五层级，固定 5 条 daily 入口。
   - 为 daily、大输出和工程/恢复入口补有界 `--summary-json`，并用统一四态 status contract 解释退出码。
   - metrics v5 增加 reviewing 年龄、30 天 flow、首次决定 lead time、90 天冷候选、脱敏检索改进队列和实现代际隔离。
6. P2 架构、复杂度与制品
   - product gate 完整契约升级为 v5，摘要升级为 v4；顶层只保留 `status` 与 `terminal`，平台、内容、项目证据、交付、采用度独立计算。
   - 建立新增模块/函数、既有大模块增长和 wrapper 增长预算；当前新增回归为 0。
   - 去重 check/status 的 source closeout 选择，拆出 product summary、owner form rule、search ranking、retrieval telemetry 和轻量 schema validator 边界；105 个模块、195 条内部 import edge 无环。
   - 建立 artifact 文件数/字节/单文件/年度增长预算，以及 strict immutable artifact ref v1；不自动上传或删除。
7. P3 恢复与持续演练
   - restore contract 升级为 v4，失败统一为 canonical `needs-fix`，并绑定 repository、commit/workflow SHA、run id/attempt、ref、runner 与证据 hash。
   - product consumer 只接受同一受信执行 run 的 offsite 证据，本地或跨 run 快照 fail-closed。
   - 新增季度/人工触发的 GitHub-hosted recovery workflow，证据保留 90 天。
   - candidate 与当前 committed HEAD 的本地离线恢复均通过；真实 remote/offsite 仍需远端 run，未被本地模拟刷绿。

## 十一、验证与证据

| Command | Exit Code | Result Summary | Layer |
| --- | ---: | --- | --- |
| `rtk bash ~/knowledge-hub/tools/knowledge-context.sh ... --summary-json` | 0 | 路由到 Knowledge Hub 当前治理入口，风险边界明确。 | Context |
| `rtk bash ~/knowledge-hub/tools/knowledge-engineering-check.sh --mode contract --json` | 0 | Python 3.10–3.14、锁定依赖、CI SHA 与权限 contract 通过。 | Engineering |
| `rtk bash ~/knowledge-hub/tools/knowledge-retrieval-benchmark.sh --summary-json` | 0 | 302/302 质量与路由通过；warm P95 142.62 ms；并发 P95 426.56 ms；五类污染为 0。 | Retrieval |
| `rtk bash ~/knowledge-hub/tools/ci/python-runtime.sh -m pytest -q tests/test_shell_wrappers.py tests/test_runtime_maintenance.py tests/test_health.py` | 0 | 21 个定向测试通过。 | Tests |
| `rtk bash ~/knowledge-hub/tools/ci/python-runtime.sh -m pytest -q` | 0 | 全量 299 项 pytest 通过。 | Tests |
| `rtk bash ~/knowledge-hub/tools/ci/python-runtime.sh -m ruff check tools/codex_assets/knowledge_hub tests` | 0 | Python 静态检查通过。 | Tooling |
| `rtk bash ~/knowledge-hub/tools/ci/python-runtime.sh -m mypy tools/codex_assets/knowledge_hub/health.py tools/codex_assets/knowledge_hub/health_cli.py tools/codex_assets/knowledge_hub/runtime_maintenance.py` | 0 | 本轮修改的 Python 模块类型检查通过。 | Tooling |
| `rtk bash ~/knowledge-hub/tools/ci/python-runtime.sh -m compileall -q tools/codex_assets/knowledge_hub` | 0 | Python 语法编译通过。 | Tooling |
| `rtk bash ~/knowledge-hub/tools/knowledge-link-audit.sh --summary-json --strict` | 0 | 738 个 Markdown、911 个标准链接无 blocking broken；managed frontmatter 覆盖率 100%。 | Content |
| `rtk bash ~/knowledge-hub/tools/knowledge-orphan-files.sh --all --strict --limit 20` | 0 | 342 个正文全部被精确 registry 或 frozen collection 覆盖，missing registry 为 0。 | Content |
| `rtk git diff --check` | 0 | 当前 diff 无空白错误。 | Git |
| `rtk bash ~/codex/scripts/final-ready.sh` | 0 | final-ready 通过；session coach 为 HOT，另提示 `~/codex` 存在不属于本轮范围的既有 skill/governance dirty 变更。 | Handoff |
| `rtk bash ~/knowledge-hub/tools/knowledge-health-summary.sh --json` | 1 | `control_plane=pass`、snapshot stale、content needs-owner-review、runtime attention；退出 1 为综合状态，不表示本轮实现测试失败。 | Operations |
| `rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics` | 1 | 基线存在用户新增 `active-low-1-warm-switch-experiment.md` 的 user-path-boundary 阻断；本轮不覆盖该现有内容。 | Governance |
| `rtk bash ~/knowledge-hub/tools/knowledge-regression.sh --suite full --summary-json --as-of 2026-07-30` | 1 | 110/133 通过；23 项失败均运行在同一非绿工作树上，多项输出直接携带上述 user-path-boundary 错误并发生级联，不能作为独立绿灯。 | Regression |
| `rtk bash ~/knowledge-hub/tools/knowledge-regression.sh --suite full --summary-json --as-of 2026-07-30` | 0 | P1-P3 收口后 133/133 通过；首轮 129/133 的 fixture Git index 与 cwd-stable 文档问题已定向复现、修复并完整复验。 | Regression |
| `rtk bash ~/knowledge-hub/tools/knowledge-engineering-check.sh --mode full --summary-json` | 0 | Ruff、mypy、Bandit、coverage、build、pytest、check、retrieval、full regression、dependency audit、SBOM 共 13 项全绿。 | Engineering |
| `rtk bash ~/knowledge-hub/tools/knowledge-restore-drill.sh --source-mode candidate --as-of 2026-07-31 --summary-json` | 0 | 冻结 candidate 全量文件完成 signature-bound 离线恢复，内部检查和 restore v4 schema 全绿；未使用网络。 | Recovery |
| `rtk bash ~/knowledge-hub/tools/knowledge-restore-drill.sh --source-mode head --as-of 2026-07-31 --summary-json` | 0 | 当前 committed HEAD 1388 文件离线恢复、内部检查和 restore v4 schema 全绿；remote/offsite 均保持 false。 | Recovery |
| `rtk bash ~/knowledge-hub/tools/knowledge-final-gate.sh --summary-json --final-profile product --regression-suite full --reuse-engineering-evidence --as-of 2026-07-30` | 0 | 全部 technical hard checks 通过；platform=pass，content/project/delivery/adoption 真实缺口独立保留。 | Product |

补充说明：

- date：2026-07-31
- cwd：`~/knowledge-hub`
- scope：Knowledge Hub 本仓与忽略运行时目录的只读审计、本仓 L1/L2 实现。
- 证据路径：本文、实时 CLI JSON、Git diff 和 `.cache/knowledge-hub/` 私有快照。

## 十二、风险与限制

- 当前工作树在本轮开始前已有多份项目知识、registry 和 index 变更；这些内容视为用户工作，本轮未回退或代签。
- 完整 regression 已在修复基线绝对路径、fixture Git index fallback 和文档 cwd-stable 问题后达到 133/133；首轮失败保留为负向证据。
- 完成性复审首轮全量 pytest 为 297/298，唯一失败是新增 schema 子集函数超过 80 行预算；拆分后 299/299。首轮 full engineering 的 12/13 通过、`coverage_report` 失败源于 `/tmp` fixture 绝对路径未命中既有 omit，改为 restore-root 无关的精确后缀规则后覆盖率 77%（阈值 75%）。
- 本轮没有执行 runtime maintenance `--apply`，约 82 MiB 只是 14 天策略下的规划候选。
- 真实 metrics 的旧代际慢样本完整保留在 usage/provenance，并从当前实现 SLA 显式排除；当前代际样本不足 10 search + 10 context 时保持 `pending`，不得通过复制或构造 telemetry 刷绿。
- 历史一次并发 benchmark 出现 7.15 秒离群值；当前完整复验并发 P95 为 426.56 ms。若趋势中复发，仍应采集 CPU、I/O、进程和 `rtk` 调度证据。
- 32 项人工复核队列及 30 个项目的外部 evidence 缺口不能由 Codex 自行关闭。
- Health、Product、Restore 和共享 Status contract 已执行单版本硬切换；旧字段、旧状态别名和旧 schema 不提供 shim、双写或降级解析，旧 consumer 必须同步升级。
- 未执行远端 push、tag、release 或真实 GitHub-hosted offsite run，也未创建 owner decision；P3 已落地执行契约和季度 workflow，但不会把“workflow 文件存在”冒充“远端演练已通过”。

### 待完成验证

```yaml
manual_validation_pending: true
manual_validation_reason: 自动化技术验证已通过；AI 生成候选、项目 evidence、remote/offsite 和长期采用仍需真实人工或外部证据。
required_followup: owner 审阅 governance/product/validation/knowledge-hub-target-architecture-p1-p3-validation-20260730.md；在合适的 clean commit 上运行 quarterly recovery workflow
owner: leiwenjun
review_after: 2026-10-30
```

## Review

- owner：leiwenjun
- review_after：2026-10-30
- 人工复核重点：
  - 是否接受“持续 SLO 优先于全局 terminal”的目标调整。
  - 是否接受平台成熟度与 30 个项目 evidence readiness 解耦。
  - 是否将 14 天事务保留作为团队默认策略。
  - 是否批准后续公共命令分级、模块复杂度预算和 artifact 增长预算。
