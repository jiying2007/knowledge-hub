---
title: Knowledge Hub root
summary_zh: Knowledge Hub 根控制面入口，定义本库作为统一知识控制面的目录、registry、source、owner gate、索引和验证链路。该 active 条目只描述 Hub 自身架构入口，不替代任何项目 owner
  decision、source project write、remote publish 或 memory write 授权。
tags:
- knowledge-hub
- governance
id: knowledge-hub-root
kind: architecture
domain: root
path: README.md
scope: team-general
visibility: team-internal
status: active
owner: leiwenjun
review_after: '2026-09-16'
review_status: active-control-plane-accepted
promotion: none
aliases:
- Knowledge Hub root
related:
- indexes/obsidian-home.md
---

# Knowledge Hub

Knowledge Hub 是本机长期知识主库：负责统一登记、检索和治理跨领域知识、项目知识、工程归档、专利材料、Codex 历史、AI 自动化和个人笔记。

终态模型：

```text
Knowledge Hub = Obsidian-friendly Markdown Vault + 最小 registry 账本 + 高风险授权门禁
```

## 日常入口

普通维护优先使用 5 条短命令：

```bash
rtk bash ~/knowledge-hub/tools/knowledge-health-summary.sh --summary-json
rtk bash ~/knowledge-hub/tools/knowledge-new.sh --kind <kind> --domain <domain> --owner <owner> --id <id> --path <path> --summary-json
rtk bash ~/knowledge-hub/tools/knowledge-search.sh "<关键词>" --summary-json
rtk bash ~/knowledge-hub/tools/knowledge-review-after.sh --window-days 30 --summary-json
rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --summary-json --diagnostics
```

这 5 条分别覆盖健康概览、新增草稿、检索、复核排期和一致性门禁。短概览只用于首屏判断；正式收口仍以 `knowledge-final-gate.sh` 为 terminal gate。
命令面的机器权威是 `registry/command-surface.json`：当前 48 个稳定 wrapper 被归入体验、查询、治理、正文与制品、证据与运营五个平面，并按 daily、maintenance、governance、engineering、internal 分级。daily 固定为上述 5 条；新增 wrapper 必须同时更新 catalog，且总数不得越过 `registry/engineering-budgets.json` 的基线。公共 JSON 状态统一映射为 `pass / needs-review / needs-fix / blocked`；完整取证使用 `--json`，首屏与 Agent 默认使用有界 `--summary-json`。
`knowledge-health-summary.sh` 会聚合 changed-only 正文覆盖检查、reviewing triage、分轴健康状态和 report-only 运行时维护摘要；review queue 直接消费 `knowledge-index-plan` 的 canonical projection，不再维护第二套 blocker 推断。Health full contract 为 v3、summary projection 为 v2，顶层唯一综合结论是 `status`；排障时继续读取 `health_axes.control_plane`、`evidence_freshness`、`content_governance` 和 `runtime_hygiene`，不要把快照过期、内容待 owner 与控制面故障混为一类。运行时摘要只报告可回收字节和权限修复候选，不自动删除。changed-only 扫描区分新增、修改、重命名和删除，删除中的旧正文只计数并给出有界样本，不会被误报为 orphan。默认按 `full -> quick` 顺序选择 24 小时内、日期和工作树签名均匹配的 Product v5 快照；旧 schema 快照直接判为 stale，不能降级消费。可用 `--gate-suite auto|quick|full` 固定读取层级；`--refresh-gate` 在 `auto` 下刷新 quick，在显式层级下刷新所选 suite。新增长期正文应优先使用 `knowledge-new.sh` / `knowledge-capture.sh` 的事务入口，使正文、registry、lifecycle 和派生索引在同一变更中收敛；随后运行 `rtk bash ~/knowledge-hub/tools/knowledge-orphan-files.sh --json`，终态审计运行 `rtk bash ~/knowledge-hub/tools/knowledge-orphan-files.sh --all --strict --json`。完整扫描要求正文由 `registry/items.jsonl` 精确登记，或由 `registry/body-coverage.json` 的 `unregistered-only` 冻结路径清单覆盖。已精确登记的新增正文不改变集合 hash；未登记正文继续 fail closed。集合覆盖不创建 active 条目。

跨项目会话、排障、发布、归档或决策类问题先做 Hub 上下文预检：

```bash
rtk bash ~/knowledge-hub/tools/knowledge-context.sh --cwd "$PWD" --query "<任务或问题>" --task-type general --context-budget small --limit 3 --summary-json
```

预检结果用于确定项目入口、当前事实目录、归档目录、决策目录和候选知识落点。Codex memory、raw session 和项目本地 README 只能辅助定位，不能覆盖 Hub 当前事实。
预检和检索不会修改受 Git 管理的知识资产；context 预检默认不写 telemetry，需要运营样本时显式加 `--telemetry`。检索 telemetry 仍是可重建的本地 cache，存储不可用时业务结果继续返回并标记 `degraded`。运行时保留由 `tools/knowledge-runtime-maintenance.sh` 管理：默认只规划；显式 `--apply` 也不删除 telemetry 或未完成事务。
Agent 默认使用 `--summary-json --context-budget small --limit 3`，只装配 route、候选索引、风险和原文入口；路由歧义、需要完整排序解释或高风险结论时，去掉 `--summary-json` 并使用 `--json` 回退完整证据。`--context-budget small|normal|deep` 和 `--limit` 会共同约束候选与全文搜索结果。任何输出都不代表条目已提升 active 或 owner 已签收。
在 `~/knowledge-hub` 内自举维护时，`repo_route` 表示当前 cwd 属于 Knowledge Hub 仓库，`route` 表示 query 目标；如果 query 明确命中 PCR02、agent-dev-kit 等项目别名，预检仍应路由到目标项目。检查 Hub 自身治理上下文可用：

```bash
rtk bash ~/knowledge-hub/tools/knowledge-context.sh --cwd ~/knowledge-hub --query "增强 Knowledge Hub 自举体验" --task-type general --context-budget small --limit 3 --summary-json
```

## Agent 运行时派生契约

Agent 需要先导航、再查询、再读原文；对后果性动作还应做确定性预检。以下入口都是 registry/Markdown 的只读派生视图，不创建第二套知识正文：

```bash
rtk bash ~/knowledge-hub/tools/knowledge-map.sh --summary-json
rtk bash ~/knowledge-hub/tools/knowledge-evidence-pack.sh "<任务或问题>" --scope-ref repository:<repo-id> --json
rtk bash ~/knowledge-hub/tools/knowledge-action-check.sh --task "<任务>" --candidate "<候选动作>" --scope-ref repository:<repo-id> --json
rtk bash ~/knowledge-hub/tools/knowledge-proposal-route.sh --proposal <candidate.json> --json
rtk bash ~/knowledge-hub/tools/knowledge-proposal-shadow-stats.sh --json
rtk bash ~/knowledge-hub/tools/knowledge-compliance-eval.sh --root tests/fixtures/agent_compliance_root --cases tests/fixtures/agent_compliance_cases.jsonl --minimum-cases 50 --require-verdict-coverage --json
rtk bash ~/knowledge-hub/tools/knowledge-evidence-ledger.sh --ledger <rawmem-events.jsonl> --json
rtk bash ~/knowledge-hub/tools/knowledge-artifact-restore-drill.sh --release-root <release-dir> --source-label <stable-ref> --json
```

- `knowledge-map` 使用 item/byte/filter budget、source fingerprint 和游标提供紧凑导航；domain 按完整路径段匹配，personal 元数据默认不进入 map vocabulary，只有显式 `--status personal` 才可查看；map 不是事实证据。
- `knowledge-search` 的 JSON contract 已升为 v3；`search_trace.excluded_by_filters[]` 是必需、有界字段，会返回被错误过滤的已登记 ID，不再把“过滤隐藏”伪装成“不存在”；`timing` 将校验、索引 freshness、候选查询和重排分别计时。外部 JSON consumer 应显式检查 `schema_version=3`。
- `knowledge-evidence-pack` 将 active 事实与 `reviewing/draft` 候选分别放入 CONTEXT/PROVISIONAL；只有显式、active、scope 命中的 `agent_contract` 才能进入 MUST/SHOULD。
- `knowledge-action-check` 无显式适用规则时返回 `NEEDS_REVIEW`，候选 constraint 永不参与判定；task/candidate、scope、exception 均有硬预算，`deny_regex` 只允许无 backreference、lookaround、嵌套 group/量词、过大量词或超大 repeat bound 的受限子集；`ALLOW` 只表示全部适用的确定性 guard 已求值通过，不是通用安全证明。
- `knowledge-proposal-route` 默认 policy disabled 且固定 report-only shadow；proposal、client ID、证据 quote、source 文件和策略枚举均有硬预算，策略字段无效时 fail-closed；它不会写 registry 或提升 active。可选 shadow audit 只接受固定枚举的脱敏元数据，以单调 sequence 和 hash chain 追加到 `0600` ignored cache；文件、单行和行数均有上限，拒绝 symlink、截断尾行和未知 metadata。`knowledge-proposal-shadow-stats` 对实际非人工路由、高风险非人工候选、链损坏和内容字段泄漏 fail，且不会把恶意 route/reason 值原样回显。
- `knowledge-compliance-eval` v2 支持有界 JSONL 和 `--minimum-cases`，只输出 candidate SHA、适用 item 与 high-risk false-allow 汇总；仓库固定 fixture root 提供显式 active constraints，矩阵必须同时覆盖 `ALLOW/BLOCK/NEEDS_REVIEW`，且每条关键案例的 `applicable_ids` 非空。真实 Hub 根没有适用规则时仍 fail-closed 为 `NEEDS_REVIEW`，不能据此推导自动写入已安全。
- `knowledge-evidence-ledger` 只校验 `rawmem.event.v1` 的链和隐私元数据，不输出事件正文，并固定 `eligible_for_text_ingest=false`；默认限制 ledger 64 MiB、100000 events 和单行 1 MiB，可在受控调用中显式收紧或放宽到硬上限。
- `knowledge-artifact-restore-drill` 只读 checksum-bound release source，在临时部署副本中验证复制、故意损坏检测与精确恢复；最多 1000 个文件、manifest 1 MiB、制品集 10 GiB，拒绝 symlink 和路径逃逸。它固定声明远端留存、设备和生产回滚未验证，不能单独提升 evidence-ready。

完整采用/拒绝边界见 `governance/product/decisions/agent-runtime-contract-absorption-candidate.md`。该决策仍为 `reviewing`，不改变本文现有 active 终态定义，也不替代 owner、source、设备、发布、回滚或采用证据。

路径类问题优先看：

```bash
rtk bash ~/knowledge-hub/tools/knowledge-path-audit.sh --scope hub --json
rtk bash ~/knowledge-hub/tools/knowledge-path-audit.sh --scope runtime-rules --strict --json
```

人读规则见 `governance/path-routing.md`。新增归档、会话总结和排障记录只写 Hub canonical 路径；旧 `~/embedded/engineering_archive`、`~/codex/docs/archive` 和源项目旧 `docs/` / `knowledge/` / `tools/` 只作历史 provenance。

状态和收口再使用：

```bash
rtk bash ~/knowledge-hub/tools/knowledge-health-summary.sh --json
rtk bash ~/knowledge-hub/tools/knowledge-status.sh --json
rtk bash ~/knowledge-hub/tools/knowledge-index-plan.sh --section all --json
rtk bash ~/knowledge-hub/tools/knowledge-engineering-check.sh --mode contract --json
rtk bash ~/knowledge-hub/tools/knowledge-final-gate.sh --summary-json
```

`knowledge-final-gate.sh` 只有一个终态 profile：`product`。`--summary-json` 提供有界首屏，`--json` 保留完整取证；`--regression-suite quick` 适合日常收口，`--regression-suite full` 用于高风险工具改动和终态证明。

工程质量另有两个层级：`knowledge-engineering-check.sh --mode contract` 只读核对 Python 支持矩阵、精确依赖、hash lock、CI 权限、Action SHA、受控 CI transport 和 Dependabot；`--mode full` 必须在 Python 3.10–3.14 且已按 `requirements-dev.lock` 安装的隔离环境中运行，会执行全包 Ruff correctness、逐步扩大的直接 mypy 清单、Bandit 中高风险扫描、pytest 与 full regression/subprocess 合并后的 whole-package statement coverage、无隔离 build、Hub check、retrieval、依赖漏洞审计和 CycloneDX SBOM。覆盖率统计覆盖 `tools.codex_assets.knowledge_hub` 全包并要求不低于 75%，不再以少量模块的高比例冒充整体覆盖；subprocess CLI 证据通过 coverage parallel data 合并。Level 2 的 full regression 对单次非零退出最多重试 1 次，并在快照中保留每次有界输出与 `recovered_after_retry`；其余子门禁不自动重试，第二次失败仍会阻断。full 成功后写入私有 ignored 快照 `.cache/knowledge-hub/engineering-quality.json`；快照绑定当前 candidate signature、有效期 24 小时，任何非忽略文件变化都会令其失效。随后执行 product full gate 时可加 `--reuse-engineering-evidence`，只复用同一签名且仍新鲜的 coverage/pytest 与 full regression 结果；quick gate 自动复用同条件下的 coverage/pytest 证据，但仍不取得 full regression 或 terminal 资格。快照不匹配时一律执行真实测试，不降低门禁。

```bash
rtk bash ~/knowledge-hub/tools/knowledge-final-gate.sh --final-profile product --as-of 2026-07-13
rtk bash ~/knowledge-hub/tools/knowledge-final-gate.sh --summary-json --final-profile product --as-of 2026-07-13
rtk bash ~/knowledge-hub/tools/knowledge-final-gate.sh --json --final-profile product --as-of 2026-07-13
rtk bash ~/knowledge-hub/tools/knowledge-final-gate.sh --json --final-profile product --regression-suite full --as-of 2026-07-13
rtk bash ~/knowledge-hub/tools/knowledge-final-gate.sh --summary-json --final-profile product --regression-suite full --reuse-engineering-evidence --as-of 2026-07-13
rtk bash ~/knowledge-hub/tools/knowledge-final-gate.sh --require-terminal --final-profile product --as-of 2026-07-13
```

产品门禁 full contract 为 v5、summary projection 为 v4。顶层只保留 `status` 与 `terminal`；五个成熟度轴从 `maturity_axes.platform/content/project_evidence/delivery/adoption` 读取，详细证据从 `platform_status`、`content_readiness`、`retrieval_quality`、`operational_readiness` 和 `delivery_readiness` 读取。项目外部证据不足不会改写平台技术健康。工程 contract 始终是 hard check；full profile 还要求新鲜且 signature 匹配的工程质量快照。本地 clean committed HEAD、两份 hash lock、受控 CI contract、full engineering、full regression 与匹配 HEAD 的 `git archive` 恢复只能使 `maturity_axes.delivery.local_delivery_complete=true`；远端发布和独立环境恢复分别由 `maturity_axes.delivery.remote_published` 与 `offsite_restore_verified` 表达，必须由受信执行证据单独判真。`terminal` 仍要求五个成熟度轴及当前登记项目的真实 owner、source、人工/实机和发布证据闭环。新增项目后 readiness 分母从 registry 动态扩展，结构覆盖不等于 evidence-ready。默认命令在平台通过但仍待 owner 复核时退出 0；需要终态声明时使用 `--require-terminal`，未闭环返回 2。

JSON consumer 必须按当前单版本契约校验：Product full v5、Product summary v4、Health full v3、Health summary v2、Restore v4、Status contract v2。旧字段、旧状态别名和旧 schema 不提供 shim、双写或降级解析；旧 consumer 必须同步升级。Restore v4 不接受仅凭 `GITHUB_ACTIONS/GITHUB_SHA` 的弱证明，必须绑定 registry 中的 repository、commit SHA、workflow SHA、run id/attempt、ref 和同一次 GitHub-hosted 执行。未知版本和缺字段必须 fail closed，不得解释成 remote/offsite 已验证。

本机首次建立工程环境可使用以下受控流程；如果本机没有 `python3.14`，可换成支持范围内的 3.10–3.13：

```bash
rtk python3.14 -m venv .tmp/engineering/venv
rtk .tmp/engineering/venv/bin/python -m pip install --require-hashes -r requirements-dev.lock
rtk env PATH="$PWD/.tmp/engineering/venv/bin:$PATH" bash tools/knowledge-engineering-check.sh --mode full --json
```

`pyproject.toml`、runtime/dev 直接 pin、两份 universal SHA-256 lock 和构建后端必须一致；full build 使用 `--no-isolation`，防止构建时绕过 lock 临时下载另一套后端。GitHub Actions 覆盖 Python 3.10–3.14，权限固定为 `contents: read`，禁止 `pull_request_target`、checkout credential persistence 和可变 Action ref；本地 contract 通过不等于远端 workflow 已实际运行。

公共 Python wrapper 首次仍完整验证解释器版本和 runtime 依赖；验证成功后，只为 `tools.codex_assets.knowledge_hub.*` 公共模块写入 `.cache/knowledge-hub/python-runtime-selection-v1` 私有缓存。缓存只有在解释器仍属于允许候选、归当前用户所有，且新于解释器、selector 和 `requirements-runtime.lock` 时才复用；任一条件漂移即重新验证。缓存不是事实权威，删除后只会回到首次验证路径。检索热路径使用 fail-closed 的 JSON Schema 关键词子集校验器，未知关键词直接失败；完整 Draft 2020-12 校验仍由 schema catalog、pytest 和 full engineering 执行。

长期采用的调用量继续统计当前 interaction contract 的真实交互；metrics v5 使用 `knowledge-retrieval-performance-v2` 与显式 `implementation_generation` 分别报告 `warm_interactive`、`index_preparation` 和 report-only 的 `end_to_end_observed`，不再把 cold rebuild 混入 warm SLA，也不隐藏真实端到端等待。旧 performance contract 或旧实现代际的真实样本继续保留为 usage/provenance，并分别计入 `excluded_stale_contract_sample_count`、`excluded_stale_generation_sample_count`，但不被静默按当前实现口径重解释。warm 性能至少需要 10 个 search 与 10 个 context 当前代际样本；准备阶段观测到时还必须满足 5000 ms 上限。显式反馈必须绑定一次真实检索 interaction，重复反馈或结果集中不存在的 `selected_id` 不计入成熟度。不得通过清 cache、复制反馈或构造未发生的 interaction 刷绿。

高风险脚本或回归改动后，可用 `rtk bash ~/knowledge-hub/tools/knowledge-regression-trend.sh --run --suite full --json` 只保留 full regression slowest 10 与失败 ID，不做无证据的泛化重构。

产品级辅助入口：

```bash
rtk bash ~/knowledge-hub/tools/knowledge-project-readiness.sh --check --json
rtk bash ~/knowledge-hub/tools/knowledge-retrieval-benchmark.sh --json
rtk bash ~/knowledge-hub/tools/knowledge-obsidian-view-build.sh --check --json
rtk bash ~/knowledge-hub/tools/knowledge-link-audit.sh --summary-json
rtk bash ~/knowledge-hub/tools/knowledge-export.sh --plan --json
rtk bash ~/knowledge-hub/tools/knowledge-restore-drill.sh --source-mode candidate --as-of 2026-07-13 --json
rtk bash ~/knowledge-hub/tools/knowledge-restore-drill.sh --source-mode head --as-of 2026-07-13 --json
rtk bash ~/knowledge-hub/tools/knowledge-engineering-check.sh --mode full --json
```

检索基准使用 retrieval-result v3：先单列一次 index preparation，再测量 28 个语义案例、274 个动态 route、4-worker 并发和 10 倍 corpus。除 warm search P95 ≤ 500 ms、index preparation ≤ 5000 ms、并发 P95 ≤ 1000 ms 外，还硬校验 Hit Rate、MRR、nDCG@10、authority Recall@3，以及未注册/控制文件/重复/兼容残留/内部端点污染均为 0；不能通过预热、放宽 corpus 或删除慢样本刷绿。

其中 export 默认只计划或写入本机忽略目录，只选择 `active + team-internal` canonical Markdown，并执行 secret scan、链接闭包、hash manifest 和原子发布；restore drill v4 在 `/tmp` 分别验证当前候选或纯 `git archive HEAD`，并通过 `tools/ci/python-runtime.sh` 绑定调用方已验证的绝对解释器路径，不复制虚拟环境、不联网安装依赖、不修改当前仓库。恢复副本内的检索性能基准最多执行 2 次，每次 attempt 的退出码与有界输出都进入快照，连续失败仍阻断且不降低 SLA；其他恢复子检查不自动重试。candidate 通过不等于 committed release，二者都不执行远端发布；remote/offsite 只有在恢复快照与消费方处于同一个受信 run 且证据 hash 完整时才为真。`.github/workflows/recovery-drill.yml` 每季度及人工触发执行一次 GitHub-hosted HEAD 恢复、full engineering 和同 run product gate，并将证据保留 90 天；workflow 文件存在不等于远端演练已实际成功。

运营指标由 `knowledge-metrics.sh --summary-json` 统一提供：除检索 SLO 和采用度外，还包括 reviewing 年龄分桶、30 天流入/active/归档/拒绝/supersede、首次决定 lead time、90 天冷候选建议、脱敏 zero-hit/not-found 改进队列，以及 artifact 文件数、字节数和相对基线增长。冷候选、反馈和 artifact 超预算都只生成 report-only 建议，不自动删除、改路由、写正文或上传外部存储。

制品预算权威是 `registry/artifact-policy.json`：manifest 只允许文本，vault 有文件数/总量/单文件/年度增长预算。新引用使用 `knowledge-hub.immutable-artifact-ref.v1`，必须包含不可变 URI、SHA256、size、owner、content-addressed identity 和 restore contract。`knowledge-artifact-ref-plan.sh --external-base-uri` 只引用已发布对象，不执行上传；含凭证、query、fragment、控制字符或不支持 scheme 的 URI 会被拒绝。

当前产品状态与证据缺口以 `governance/product/validation/project-readiness.md` 和实时 `knowledge-final-gate.sh` 输出为准。`governance/status/knowledge-hub-operational-maturity.md` 仅保留 2026-07-13 历史快照；2026-07 运营批次和交付记录分别见 `artifacts/manifests/knowledge-hub-review-after-operation-plan-20260701.md` 与 `artifacts/manifests/knowledge-hub-complete-delivery-closure-20260701.md`，均不替代当前 owner、设备、发布或回滚证据。
本轮覆盖功能、性能、安全、扩展性、维护性、运行时支持和供应链的验证候选见 `governance/product/validation/knowledge-hub-terminal-closure-validation-20260718.md`；该候选保持 `reviewing / manual-validation-pending`，不会把本地自动化结果冒充 GUI、实机、发布、生产回滚、人工复核或长期采用证据。

## 目录边界

| 目录 | 用途 | 维护强度 |
|---|---|---|
| `inbox/` | 未分类输入、临时草稿、待处理材料 | L0，可短期停留 |
| `notes/` | 普通长期笔记、个人笔记、学习和研究记录 | L1，registry 可选 |
| `projects/<project>/` | 项目当前事实、决策、验证和历史归档 | L2，registry 必填 |
| `domains/` | 跨项目领域知识、专利、Codex 治理材料 | L2，registry 按复用风险决定 |
| `sources/` | source 人读边界、inventory、coverage 和 source policy | L2，和 current/retired source registry 对齐 |
| `registry/` | 机器账本：items、sources、projects、owners、`registry/authorizations.jsonl`、`registry/automation-runs.jsonl` | L2/L3 |
| `indexes/` | 可重建导航，不是事实权威 | 可由工具检查 |
| `artifacts/manifests/` | 高风险 source 处置、owner gate、自动化和终态证据包 | L3 |
| `artifacts/vault/` | 经批准的不可变附件副本；必须有 manifest、size、SHA256 和边界说明 | L3，禁止无清单落盘 |
| `templates/` | 人工维护模板 | 低频维护 |
| `governance/` | 中文治理规则和边界 | 低频维护 |
| `tools/` | 检查、检索、诊断和门禁工具 | 变更后跑 regression/final gate |

新增内容不得写入旧项目/个人入口：

```text
domains/projects/**
domains/personal/**
```

旧路径只允许出现在 Git 历史、历史 manifest 或明确标记的 provenance 字段中，不作为当前查询、恢复或新增入口。

## Source 处置口径

“终态落地”采用治理全覆盖，不等于复制所有正文。

- 每个来源、项目、历史会话和自动化链路必须登记、分类、索引和定责。
- `registry/sources.json` 只保留当前 source 主表；已关闭来源进入 `registry/retired-sources.jsonl`，仅作 provenance ledger。
- `registry/retired-process-ledger.jsonl` 只保留迁移过程账本、dry-run、applied、classification 和 source inventory 的封存线索；它不是当前知识入口，不参与默认新增、提升或 owner gate。
- 每个 current 或 retired source 必须有 Hub 内 `sources/<source_id>/README.md`、`inventory.jsonl`、`coverage.md`、`source-policy.md`。
- 安全、可读、长期有价值的 Markdown/text 可以落到 canonical 正文。
- raw log、binary、SDK、release artifact、源码包、raw session、history jsonl 默认只登记引用、摘要、hash 或 artifact-ref；只有经 owner 确认、体量受控且纳入 vault manifest 完整性门禁的不可变附件才允许进入 `artifacts/vault/`。
- current/retired source registry 中的 `path` 必须指向 Hub 内 `sources/<source_id>`；当前知识入口只使用 Hub 内路径，retired source 不作为默认新增入口。
- Codex archive 当前 canonical 目录是 `domains/codex/archive/codex-archive/`；新归档和新索引只写 Knowledge Hub 终态目录。
- PCR02 工程归档当前 canonical 目录是 `projects/pcr02-ssc305/archive/engineering-archive/pcr02/`；PCR02 新归档、会话总结和排障材料只写 Knowledge Hub 终态目录。
- `~/.codex/history.jsonl`、`~/.codex/sessions/**`、`~/.codex/memories/**` 只作为运行态输入或辅助召回 provenance，不复制 raw 正文，不直接等于 active fact。
- 全局路径回答和跨仓协同以 `governance/path-routing.md` 为准；发现旧路径召回时先运行 `knowledge-path-audit.sh`，再按 Hub / Codex runtime / memories / historical session 分类处理。

## 权威边界

- 项目事实：`projects/<project>/current/`
- 项目决策：`projects/<project>/decisions/`
- 项目验证：`projects/<project>/validation/`
- 项目历史：`projects/<project>/archive/`

目录位置和生命周期是两个维度。`current/`、`decisions/` 可保留 owner 已选定的 canonical 落点，但条目是否 active、reviewing 或 archived 始终以 registry 为准；路径名称不得被解释为隐式 active promotion。
- 普通和个人笔记：`notes/`
- 跨项目嵌入式知识：`domains/embedded/`
- 专利材料：`domains/patents/`
- Codex 会话、工作流和记忆治理：`domains/codex/`
- Source 边界说明和迁移控制面：`sources/`

`registry/items.jsonl` 是长期资产权威账本；`indexes/` 是可重建导航；`artifacts/manifests/` 是高风险证据包。

## AI 自动化权限

在 Git 管理下，AI / Codex 默认可执行 L1/L2 Hub 内维护：

- 修改本仓内 Markdown、registry、index、manifest、template 和 tools。
- 移动、重命名、归并本仓内知识文件。
- 生成 source coverage、source policy、review queue、automation run record。
- 运行 `knowledge-check`、`knowledge-regression`、`knowledge-final-gate`。
- 门禁全绿后创建本地 commit。

本地 commit 只代表可审计快照，不代表发布、owner approval 或 active promotion。自动 push、merge、release、tag、删除外部资料、修改源项目、写 memory、关闭 owner gate、提升 active 或改变远端 Git 状态仍必须走授权账本。

AI / 外部资料人工复核的默认路径是先导出 JSONL 骨架，再由真实人工填写 `human_reviewed_by`、`human_reviewed_at`、`review_basis` 和 `review_decision`：

```bash
rtk bash ~/knowledge-hub/tools/knowledge-index-plan.sh --section review-queue --queue-forms-jsonl > artifacts/manifests/review-queue.local.jsonl
rtk bash ~/knowledge-hub/tools/knowledge-review-queue-apply.sh --forms artifacts/manifests/review-queue.local.jsonl --dry-run --json
rtk bash ~/knowledge-hub/tools/knowledge-review-queue-apply.sh --forms artifacts/manifests/review-queue.local.jsonl --apply --json
```

`knowledge-review-queue-apply.sh` 只机械落地已校验人工复核字段。registry item 表单使用 schema v2，并绑定导出时的整文件 `content_sha256`；正文漂移会拒绝校验和 apply，成功落地后保存 `human_review_content_sha256`，后续漂移会重新入队。表单中出现 owner gate、active promotion、memory write、source project write 等字段会被拒绝。`needs-edits` 和 `defer` 会继续阻断人工复核闭环，直到人工补正或改判；`archive-only/reject` 也不会直接改变 lifecycle status，退役必须走独立内容 attestation、执行授权和 `knowledge-retire.sh`。

## 高风险授权

AI / Codex 可以执行以下高风险动作，但必须先有授权账本记录：

- 代签或落地 owner decision。
- 提升条目为 `active`。
- 写入 `~/.codex/memories` 或其他长期记忆层。
- 修改 PCR02 或其他源项目文件。
- 执行非 `report-only` 自动化，例如 `apply-with-review`。
- push、merge、release、tag 或其他远端 Git 状态变更。

授权记录写入 `registry/authorizations.jsonl`，必须包含：

- `authorization_id`
- `authorized_by`
- `authorized_at`
- `scope`
- `allowed_actions`
- `expires_at`
- `evidence_refs`
- `rollback_path`
- `validation_commands`

跨项目、跨会话自动化运行写入 `registry/automation-runs.jsonl`。没有授权记录时，AI / Codex 只能在 Hub 内执行 L1/L2 维护、本地 commit，或输出 plan、diff、manifest、review package、report-only 报告。

### 生命周期复核与执行授权

`promote` / `retire` 使用两个相互独立的门禁：

- execution authorization：只允许执行限定写操作，来自 `registry/authorizations.jsonl`。
- content review attestation：只确认真人对精确 item、原状态、目标状态和正文 SHA256 作出的决定，不授权写操作。

先生成只读确认包；真人明确回复包内绑定信息后，Codex 可机械生成本地表单，无需人工编辑 JSON：

```bash
rtk bash ~/knowledge-hub/tools/knowledge-review-attest.sh packet --id <item-id> --target archived --json
rtk bash ~/knowledge-hub/tools/knowledge-review-attest.sh generate --id <item-id> --target archived --expected-sha256 <sha256> --attestation-mode human-reviewed --attested-by <human> --attestation-source-ref <source-ref> --attestation-text '<exact-human-response>' --confirm-attestation --output artifacts/manifests/<item-id>-archive-review.local.jsonl --apply --json
rtk bash ~/knowledge-hub/tools/knowledge-retire.sh --id <item-id> --target archived --authorization-id <execution-authorization-id> --forms artifacts/manifests/<item-id>-archive-review.local.jsonl --expected-sha256 <sha256> --apply --json
```

确认包和表单生成不创建 authorization，也不执行状态变更。`human-directed-delegation` 只适用于非 active 目标，并强制把 `reviewed_by` 记为 `<human>-via-codex-delegation`；active promotion 必须使用 `human-reviewed`。生命周期工具只接受 `content-review-attestation`，表单禁止嵌入执行授权。

## 离线人工维护

无法立刻联网、上板、跑完整工具或确认 owner 时，可以先登记人工待验证状态，但不能把它当作已验证事实。

最小字段：

```yaml
source:
  type: manual
  from: field-debug / meeting / code-review / lab-test / owner-decision / design-review
status: reviewing
review_status: manual-entry-pending-review
manual_validation_pending: true
required_followup: rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
```

等价 JSON 片段：

```json
{
  "source": {
    "type": "manual",
    "from": "field-debug / meeting / code-review / lab-test / owner-decision / design-review"
  },
  "status": "reviewing",
  "review_status": "manual-entry-pending-review",
  "manual_validation_pending": true,
  "required_followup": "rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics"
}
```

涉及 source、index 或迁移关系时，再运行：

```bash
rtk bash ~/knowledge-hub/tools/knowledge-index-plan.sh --section all
rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
```

新增 source 优先提供稳定只读 `--check`；没有稳定检查时才使用 `--no-check-reason` 写清原因。registry source object 和 source coverage JSONL row 草稿都应记录 `check`，有 `check` 时不再补 JSON 形式的 `no_check_reason`。

## 中文长期资产

长期文本默认使用简体中文。命令、路径、协议字段、API 名称和代码标识可以保留英文，但必须有中文摘要或中文说明。

长期文档优先写清：

- 背景
- 适用范围
- 结论
- 证据
- 风险
- 下一步

不要长期保留只有命令堆、AI 过程流水账、大段无摘要英文、未区分事实/推断/建议/open items 的材料。

## 新会话恢复

新线程或 AI 恢复时先运行：

```bash
rtk git rev-parse --short HEAD
rtk git status --branch --short
rtk bash ~/knowledge-hub/tools/knowledge-status.sh --json
rtk bash ~/knowledge-hub/tools/knowledge-final-gate.sh --json
rtk bash ~/knowledge-hub/tools/knowledge-index-plan.sh --section linking --json
```

恢复顺序：

1. 固定 HEAD、分支和工作区状态。
2. 看 `knowledge-status` 恢复 source、review queue、owner gate 和 automation 状态。
3. 看 `knowledge-final-gate` 判断终态是否通过。
4. 用 `knowledge-search` 和 `indexes/` 找具体正文。
5. 修改后运行 `knowledge-check`，工具/schema/final gate 相关变更再跑 regression/final gate。

## Obsidian

Obsidian 是阅读和手工编辑客户端，不是治理权威。直接把 `~/knowledge-hub` 作为 vault 打开，首屏使用 [`indexes/obsidian-home.md`](indexes/obsidian-home.md)，完整边界见 [`governance/obsidian-integration.md`](governance/obsidian-integration.md)。

推荐主要阅读：

- `README.md`
- `notes/`
- `projects/`
- `domains/`
- `indexes/`
- `templates/`

`.obsidian/` 已整体忽略，主题、布局和插件保持本机私有。建议在 Obsidian 中排除 `.git/`、`.tmp/`、`registry/`、`artifacts/manifests/`、`sources/` 和 `tools/`；新附件先进入 `inbox/attachments/`。普通使用者不需要日常阅读控制面目录，Properties 中的 `status`、`owner`、`review_after` 只能镜像 registry。

<!-- knowledge-hub-project-readiness:start -->
## 成熟度工作台

以下入口是单一 `reviewing` evidence contract 与统一 dashboard；不代表 owner 签收或发布就绪。

- [项目 evidence contract](governance/product/validation/project-readiness.md)
- [统一 readiness dashboard](indexes/project-readiness.md)
<!-- knowledge-hub-project-readiness:end -->
