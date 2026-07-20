---
related:
- README.md
- governance/external-source-absorption.md
- governance/evidence-rules.md
- governance/product/validation/project-readiness.md
human_reviewed_by: leiwenjun-via-codex-delegation
human_reviewed_at: '2026-07-16'
review_basis: 用户于 2026-07-16 当前会话明确回复“授权，按建议继续推进”。Codex 作为透明受托复核执行人，已完整读取候选正文，核对 memdsl@2d87af7 与 rawmem@9842be6 的固定来源、许可证和采用边界，并复核
  Knowledge Hub 138 项 pytest、140/140 full regression、350/350 正文覆盖、1396 路径 candidate restore 与 product gate 技术通过证据。结论仅接受为普通内容
  review record，保持 reviewing、promotion=none、manual_validation_pending 和 shadow/采用证据缺口；不生成 owner lifecycle decision、不关闭 owner
  gate、不提升 active、不写 memory、不修改源项目。authorization_id=auth-20260716-agent-runtime-absorption-review-push。
human_review_decision: accept-as-review-record
decision_status: delegated-review-accepted-remain-reviewing
decision_date: null
aliases:
- Knowledge Hub Agent 运行时契约吸收决策候选
id: knowledge-hub-agent-runtime-contract-absorption-20260716
title: Knowledge Hub Agent 运行时契约吸收决策候选
kind: decision
domain: governance
path: governance/product/decisions/agent-runtime-contract-absorption-candidate.md
scope: team-general
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: external-reference-synthesis
  from: memdsl@2d87af7 and rawmem@9842be6 public source audit
  source_sha256: 7ce01cdbf3966fc66fbc75c3898372a31cc330dbd363f561e64b2c16eadeb1ed
review_after: '2026-10-16'
review_status: human-reviewed-accepted
content_review_status: accepted
evidence_validation_status: pending
promotion: none
promotion_decision: adapt accepted; remain reviewing for shadow and adoption evidence; no active promotion
tags:
- knowledge-hub
- agent-runtime
- memdsl
- rawmem
- external-source
- ai-generated
- delegated-review-accepted
- no-active-promotion
validation_refs:
- rtk python3 -m pytest -q
- rtk bash ~/knowledge-hub/tools/knowledge-regression.sh --suite full --json --as-of 2026-07-16
- rtk bash ~/knowledge-hub/tools/knowledge-final-gate.sh --json --final-profile product --regression-suite full --as-of 2026-07-16
evidence_strength: external-reference-plus-direct-source-audit
evidence_refs:
- https://github.com/Liyuan1992/memdsl/tree/2d87af7838474a2b1546afd645caf5522bdc39a8
- https://github.com/Liyuan1992/rawmem/tree/9842be6c90955100035b71d1af181ce8dde42cf9
- governance/external-source-absorption.md
- governance/evidence-rules.md
created_at: '2026-07-16'
updated_at: '2026-07-19'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-07-16'
manual_validation_pending: true
decision_owner: leiwenjun
summary_zh: 吸收 memdsl 的有界导航、可解释检索、EvidencePack、合规预检与 shadow review，以及 rawmem 的只追加证据链、metadata projection 和隐私边界；保持 Markdown/registry
  唯一权威，不引入第二套记忆 SSOT。
primary_language: zh-CN
source_language: en
translation_status: summarized-zh
terminology_status: pending-review
agent_contract:
  schema_version: 1
  role: guidance
  force: strong
  subject: KnowledgeHub.AgentRuntimeContract
  scope_refs:
  - repository:knowledge-hub
  capabilities:
  - searchable
  - requires_evidence
---

# Knowledge Hub Agent 运行时契约吸收决策候选

## 背景

Knowledge Hub 已具备 Git 管理的 Markdown 正文、registry、生命周期、证据、人工复核和高风险授权门禁，但 Agent 仍需要自行把 `kind`、`status`、证据状态和治理文本解释成运行时行为。已知条目被错误过滤时，当前检索只返回原因计数，不返回被隐藏条目的稳定 ID；`reviewing` 候选虽然携带状态，也可能与 active 当前事实出现在同一 `context.current` 通道。

本候选评估两个公开项目：

- `memdsl`：把长期记忆组织成可 lint、可导航、可分层服务并可做确定性合规预检的 Source/Compiled View 契约。
- `rawmem`：把原始事件保存在本地只追加证据层，以 hash chain、稳定 cursor、只读验证和 metadata projection 支持后续派生。

## 适用范围

- 适用于 Knowledge Hub 本仓的只读导航、检索解释、Agent 上下文装配、动作预检、候选路由和外部原始证据引用。
- 不改变源项目事实权威、owner decision、active promotion、memory write 或远端发布权限。
- 不把 `.mem`、raw event JSONL、MCP 服务或外部项目运行目录变成 Hub 正文权威。

## 外部来源登记

| source_id | 标题与作者 | published_at | retrieved_at | URL / commit | source_language / source_license | read_status | review_status / evidence_strength | promotion_decision |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `github-liyuan1992-memdsl-2d87af7` | `memdsl`，Liyuan1992 | 2026-07-16（固定 commit author date） | 2026-07-16 | `https://github.com/Liyuan1992/memdsl` / `2d87af7838474a2b1546afd645caf5522bdc39a8` | en / Code MIT；`docs/SPEC.md` CC-BY-4.0 | README、公开 API、核心实现与测试定向审计 | `human-directed-delegated-review-accepted` / `direct-source-audit` | `adapt` |
| `github-liyuan1992-rawmem-9842be6` | `rawmem`，Liyuan1992 | 2026-07-12（固定 commit author date） | 2026-07-16 | `https://github.com/Liyuan1992/rawmem` / `9842be6c90955100035b71d1af181ce8dde42cf9` | en / MIT | README、架构、ledger protocol、privacy、核心实现与测试定向审计 | `human-directed-delegated-review-accepted` / `direct-source-audit` | `adapt` |

本仓采用独立实现，仅吸收公开契约思想；没有复制外部正文或大段实现代码。后续若复制实质性代码，必须保留相应 MIT notice；引用 `memdsl` 规范文本时必须保留 CC-BY-4.0 attribution。

## 决策问题

如何吸收两个项目已经验证的 Agent 导航和证据治理机制，同时保持 Knowledge Hub 的唯一权威、中文长期资产、现有授权门禁和 raw evidence 禁入正文边界？

## 选项

| 选项 | 影响范围 | 成本 | 风险 |
| --- | --- | --- | --- |
| A：整体引入 `.mem` 与 rawmem runtime | 新增第二套语法、运行目录和依赖 | 高 | SSOT 分裂、权限和版本漂移，不采用 |
| B：把上游契约改写为 Hub 派生视图与只读工具 | 增加 schema、CLI、测试和候选决策 | 中 | 需维持兼容与 fail-closed 语义，建议 |
| C：只保留文章笔记 | 无运行时变化 | 低 | 已知检索失败和候选混层继续存在，不采用 |

## 吸收边界

### 直接采用的设计原则

- Source 是权威，索引、map、catalog、EvidencePack 和 ledger projection 都是可重建派生物。
- 空结果必须区分不存在、被过滤、受限、索引降级和预算截断。
- 非 active 命中进入 `PROVISIONAL`，不得进入 MUST、SHOULD、CONTEXT 或合规判定。
- 约束无法确定性求值时返回 `NEEDS_REVIEW`，不得猜测。
- 原始证据的链完整性、内容可信度和长期知识有效性是三个不同维度。

### 按 Hub 边界改写的机制

- 用现有 Markdown + `registry/items.jsonl` 表达可选 `agent_contract`，不新增 `.mem` 权威层。
- 用 Hub 原生 `knowledge-map`、`knowledge-evidence-pack`、`knowledge-action-check` 和 `knowledge-evidence-ledger` 提供只读运行时表面。
- 自动化只实现 report-only shadow 路由；低风险候选最多建议进入 `reviewing`，不自动 active。
- rawmem 兼容检查只输出 metadata、hash、计数和 reference-only 候选，不复制 `raw_text`、`payload`、`cwd` 或事件正文。

### 明确拒绝

- 不迁移现有正文为 `.mem`。
- 不把外部仓库加入运行时必需依赖。
- 不默认启动 daemon、浏览器扩展、clipboard、shell history 或 Git hook 捕获。
- 不启用 MCP 外部写入，不允许 tool arguments 自报可信身份。
- 不把 hash chain 解释为事件真实性、owner approval 或 active fact。

## 目标运行时契约

```text
Markdown + registry (SSOT)
  -> bounded map/catalog
  -> explainable search trace
  -> MUST / SHOULD / CONTEXT / PROVISIONAL / CONFLICT / MISSING
  -> action check: ALLOW / BLOCK / NEEDS_REVIEW

external raw evidence ledger
  -> read-only chain/privacy inspection
  -> metadata-only artifact reference candidate
  -> reviewing candidate -> existing human review/promotion gates
```

## 完成标准

- 错误 kind/status/owner/domain 过滤导致零命中时，返回有界且不含正文的 `excluded_by_filters[]`。
- map/catalog 有 item/byte budget、source fingerprint、游标失效检测和显式截断。
- active 与 reviewing/draft 在 EvidencePack 中分道；候选 constraint 永不参加 action check。
- action check 只执行显式、active、scope 命中的确定性 guard；无规则或不完整规则返回 `NEEDS_REVIEW`。
- proposal route 默认 disabled/shadow，只产生建议与脱敏审计元数据。
- raw evidence 检查严格只读，链失败 fail-closed，默认不输出事件正文，永远标记 `eligible_for_text_ingest=false`。
- 定向单元测试、全量 pytest、full regression、Knowledge Hub final gate 均有新鲜证据。

## 证据

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
| --- | --- | --- | --- | --- | --- |
| `rtk git rev-parse HEAD`（memdsl checkout） | 0 | 固定 `memdsl` 为 `2d87af7`。 | GitHub commit URL | External Reference | `github-liyuan1992-memdsl-2d87af7` |
| `rtk git rev-parse HEAD`（rawmem checkout） | 0 | 固定 `rawmem` 为 `9842be6`。 | GitHub commit URL | External Reference | `github-liyuan1992-rawmem-9842be6` |
| `rtk python3 -m pytest -q`（memdsl checkout） | 2 | 本机 Python 3.8 且未注入 `src`，不满足 memdsl 3.9+ 基线；该结果不证明上游测试失败。 | 当前会话命令证据 | External Reference | negative-path |
| `rtk python3 -m unittest discover -s tests`（rawmem checkout） | 1 | 本机 Python 3.8 不满足 rawmem 3.10+；出现 3.10 语法与 pathlib API 失败，不作为上游缺陷结论。 | 当前会话命令证据 | External Reference | negative-path |
| `rtk python3 scripts/open_source_audit.py`（rawmem checkout） | 0 | rawmem 开源制品审计通过。 | 当前会话命令证据 | External Reference | `rawmem@9842be6` |
| `rtk python3 -m pytest -q`（Knowledge Hub） | 0 | 整库 pytest 全绿；包含新增 map、trace、EvidencePack、action check、proposal routing、raw evidence 与 compliance eval 测试。 | 当前工作树 | Local Validation | implementation |
| `rtk bash ~/knowledge-hub/tools/knowledge-orphan-files.sh --all --strict --json` | 0 | 350/350 个长期 Markdown 由精确 registry 或冻结集合覆盖，coverage contract 通过。 | `registry/body-coverage.json` | Current SSOT | body-coverage |
| `rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics --as-of 2026-07-16` | 0 | 0 error、0 warning。 | 当前工作树 | Local Validation | governance-gate |
| `rtk bash ~/knowledge-hub/tools/knowledge-regression.sh --suite full --json --as-of 2026-07-16` | 0 | full regression 140/140 通过。 | 当前工作树 | Local Validation | regression |

实现验证和普通内容受托复核已完成；`manual_validation_pending` 仍保持为 `true`，表示 shadow 运行、长期采用和 active lifecycle 决定尚未闭环，不表示实现门禁失败。

## 当前决策

采用选项 B：契约级吸收并使用 Hub 原生独立实现。用户已授权透明受托普通内容复核，结论为 `accept-as-review-record`；条目继续保持 `reviewing`，该复核不自动等同 owner lifecycle decision 或 active promotion。

## 生效条件

- 普通内容复核已按 `auth-20260716-agent-runtime-absorption-review-push` 完成；active lifecycle promotion 仍需独立决定。
- 新 schema/CLI 的兼容、权限和负向用例全绿。
- 现有检索、生命周期、授权、export、restore 和终态门禁无回归。
- 如未来接入 MCP、daemon 或自动写入，必须另建 transport、identity、credential、deny-path、日志脱敏和回退审查。

## 回滚条件

- 新派生视图破坏现有 JSON contract、检索 P95 或恢复门禁。
- action check 出现 candidate authority、漏扫 active hard rule 或无规则返回 ALLOW。
- raw evidence 工具输出正文、绝对敏感路径、凭证或把 ledger 当作事实。

回滚时删除新增派生 CLI/schema，并恢复 search/context 的旧输出；不需要迁移或回写正文，因为本方案不改变知识 SSOT。

## 风险与限制

- 外部项目均处 Alpha；本仓不依赖其性能承诺或未发布功能。
- lexical trace 只能解释当前检索路径，不能证明知识不存在。
- regex guard 来自受治理 registry，但仍需限制输入长度和编译错误。
- metadata-only ledger 检查能够证明链一致性，不能证明事件内容真实或已经充分脱敏。
- 本候选不得用于关闭当前 30 个项目的真实 owner、设备、发布、回滚或采用证据缺口。

## Review 周期

- owner：`leiwenjun`
- review_after：`2026-10-16`
- 下一次复核：CLI/schema 稳定性、误阻断/漏阻断、shadow 路由统计、raw evidence 隐私抽查和是否进入 active。
