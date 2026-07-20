---
id: knowledge-hub-product-maturity-implementation-20260713
title: Knowledge Hub 产品成熟度全面实现审计 2026-07-13
kind: audit
domain: governance
path: artifacts/manifests/knowledge-hub-product-maturity-implementation-20260713.md
scope: team-general
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: generated
  from: current-session Knowledge Hub product maturity implementation
  source_sha256: 4431af7ccf7ef0c5e5d27cda521b718582b2259d2b2587bde4b842489b249cc9
review_after: '2026-10-13'
review_status: human-reviewed-accepted
content_review_status: accepted
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- knowledge-hub
- product-maturity
- architecture
- retrieval
- obsidian
- restore
- report-only
- no-active-promotion
validation_refs:
- artifacts/manifests/knowledge-hub-product-maturity-implementation-20260713.md
- artifacts/manifests/knowledge-hub-product-maturity-implementation-20260713.jsonl
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics --as-of 2026-07-13
- rtk bash ~/knowledge-hub/tools/knowledge-final-gate.sh --final-profile product --regression-suite full --as-of 2026-07-13
  --json
evidence_strength: reviewing-validation-pending
evidence_refs:
- artifacts/manifests/knowledge-hub-product-maturity-implementation-20260713.md
- artifacts/manifests/knowledge-hub-product-maturity-implementation-20260713.jsonl
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics --as-of 2026-07-13
- rtk bash ~/knowledge-hub/tools/knowledge-final-gate.sh --final-profile product --regression-suite full --as-of 2026-07-13
  --json
created_at: '2026-07-13'
updated_at: '2026-07-19'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-07-13'
manual_validation_pending: true
summary_zh: 记录 Knowledge Hub 产品化全面实现：Python 单内核、事务生命周期、31 项目结构与路由、可解释检索、Obsidian 只读视图、受控导出、恢复演练和唯一 product 门禁；平台通过但真实项目证据
  0/31，保持 needs-owner-review。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
---

# Knowledge Hub 产品成熟度全面实现审计 2026-07-13

## 结论

本轮已把 Knowledge Hub 从“治理脚本集合”推进为可验证的本地知识产品平台：目标与权威边界、共享内核、事务化生命周期、项目结构、检索质量、上下文路由、Obsidian 呈现、团队导出、恢复演练和产品门禁均有稳定实现与测试。

当前平台技术门禁通过，但不能声明全面终态成熟。31 个项目均达到 4/4 结构覆盖，本机 source mapping 已达到 31/31，但真实 owner、人工/实机和发布 evidence-ready 仍为 0/31；因此当前产品结论是 `gate_status=pass`、`overall_status=needs-owner-review`、`terminal=false`。这只能声明“平台产品化完成”，不能在观察期前声明“长期使用终态已被实证”。

本候选由 Codex 生成，保持 `reviewing`、`manual_validation_pending=true`、`promotion=none`。它不是 owner decision，不提升 active，不关闭 owner gate，不写 memory，不修改源项目，也不授权 push、merge、tag 或发布远端状态。本轮只允许在全部门禁通过后形成一个 Hub 本地提交。

## 目标与架构

终态架构固定为：

```text
canonical Markdown
  + registry/schema/lifecycle ledger
  + transactional write boundary
  + rebuildable indexes and local caches
  + stable search/context/product APIs
  + optional Obsidian workbench
  + explicit authorization and evidence gates
```

- Markdown 是唯一正文；registry 是状态、owner、review_after、source、promotion 和 authorization 权威。
- `indexes/`、SQLite FTS、Obsidian Bases、export 都是可重建派生层，不能反向改变权威状态。
- `knowledge-workspace-discover.sh` 按 registered remote key 精确匹配本机 Git 仓库；`local/workspaces.json` 只保存本机路径、HEAD 和重复副本诊断，不把机器状态写入团队 registry 或 Markdown。
- 高风险动作继续要求授权、证据、回滚和验证；结构完整不等于内容事实成熟。

## 功能落地

| 方面 | 当前实现 | 验收结果 |
|---|---|---|
| 共享内核 | `tools/codex_assets/knowledge_hub/` 统一 common/model/store/indexing/lifecycle/search/context/workspace discovery/export/restore/Obsidian | 72 个 pytest 全通过；37 个 shell 入口从任意 cwd 锚定仓库根目录 |
| Schema | 14 个机器可读 schema 与 catalog，覆盖 item、frontmatter、authorization、lifecycle、local workspace、项目 evidence、export、restore、metrics、Obsidian 和 PCR02 evidence | schema 本身和 625 个真实实例均通过 Draft 2020-12 校验 |
| 生命周期 | `knowledge-capture/promote/retire.sh`；事务 plan/apply/rollback；promotion 授权与 review form 门禁 | capture 仅允许 draft/reviewing/personal；AI provenance 可显式登记 |
| 项目结构 | 31 个项目各有 profile/runbook/decision/validation reviewing 槽位 | 31/31 项目、124/124 槽位、生成器幂等零改动；tracked 内容不依赖 local mapping |
| Source discovery | 默认只读扫描 `~` 与 `/vsdata/<user>`，按 exact remote key 选择确定性 canonical path | 34/34 registered remotes、31/31 项目可定位、0 unmatched、16 duplicate remotes 显式保留 alternate 诊断 |
| 路由 | exact project 优先，group alias 次之，Hub control-plane query-aware；歧义和未知项目显式回退全局 | 31 项目 × 9 task type = 279/279，另加 4 条别名/歧义语义，总计 283/283 |
| 检索 | 可重建 SQLite FTS、中文 2/3-gram、短语/别名/同义词、覆盖率加权、fallback 和 `why_selected` | 20/20 top-3，hit rate 100%，MRR 1.0，warm p95 小于 0.5 秒，0 known-answer zero hit |
| 链接 | Markdown link、anchor、attachment、related、readiness inbound、MOC 和 Base schema 审计 | 722 Markdown、1400 links、0 blocking broken；153 条均为 archive/unregistered patent attachment 历史 warning；artifact vault 181 行完整通过 |
| Obsidian | canonical Markdown 上的可选本地 workbench；总/项目/主题 MOC 与 3 个只读 `.base` | managed Properties 147/147、mirror drift=0、MOC orphan=0；文件层通过，真实 GUI 运行态保持 `not-validated` |
| 团队导出 | 只选择 active + team-internal canonical Markdown，执行共享 secret scan、link closure、hash manifest 和 atomic publish | manifest v2；不含 reviewing/personal/pending owner decision，失败不会暴露半成品目标目录 |
| 恢复演练 | `candidate` 验证 tracked + 当前工作树，`head` 只验证 `git archive HEAD`；均在 `/tmp` 逐文件 hash 后运行门禁 | 无 cache/workspace mapping；候选通过不再冒充 committed release，HEAD 演练是发布必要条件 |
| 产品门禁 | 唯一入口 `knowledge-final-gate.sh --final-profile product` 聚合技术、内容、检索、运营和真实证据 | `gate_status=pass`；`overall_status=needs-owner-review`；`terminal=false` |
| 交付真实性 | `delivery_readiness` 分开本地交付、远端发布和异地恢复 | tracked dependencies、full regression 和 HEAD restore 只决定 `local_delivery_complete`；远端 push 与独立环境恢复各自判定 |

## Obsidian 关系

Obsidian 不是第二套 Knowledge Hub，也不是治理权威。它直接打开同一份 canonical Markdown，提供 links、backlinks、Graph、Properties 和只读 Bases 视图；Hub 吸收的是更好的链接可达性、frontmatter 可读性、MOC 和查询视图，不吸收 community plugin、私有配置或 Sync 凭证成为关键依赖。

提交的 `indexes/obsidian/project-readiness.base`、`reviewing.base`、`active-knowledge.base` 只做查询呈现。任何在 Obsidian 中看到的目录名、属性或 Graph 关系，都不能被解释为 active promotion、owner approval 或验证通过。文件层自动检查与真实 GUI 验收分开；后者只有在忽略提交的 `local/obsidian-runtime-acceptance.json` 记录版本、验收人、日期、四项 GUI 检查和截图引用后才为 `pass`。

## 性能与回归

full regression 本轮为 137 个 test function、140 个结果场景、4 worker、140/140 pass。后续性能优化只跟踪本次 slowest 10，不做无证据泛化重构：

| 排名 | result id | 秒 |
|---:|---|---:|
| 1 | `final-gate-owner-review-blocker` | 28.269 |
| 2 | `review-after-as-of-deterministic` | 23.694 |
| 3 | `source-coverage-date-filename-selection` | 20.834 |
| 4 | `final-gap-readability-positive-contracts` | 16.941 |
| 5 | `final-gate-source-check-runtime-failed-blocker` | 16.014 |
| 6 | `final-gate-strict-status-nonowner-blocker` | 15.598 |
| 7 | `final-gate-product-review-queue-owner-review-blocker` | 15.290 |
| 8 | `final-gate-default-regression-path` | 15.225 |
| 9 | `final-proof-artifact-as-of-date-selector` | 15.051 |
| 10 | `final-gate-empty-child-json-blocker` | 15.003 |

日常性能与 release regression 分开衡量：固定 retrieval benchmark 关注命中率、MRR 和 warm p50/p95；full suite 只用于 release/high-risk proof。原来递归执行整套 140 项的 `final-gate-default-regression-path` 已改为隔离的 140-result 调用契约夹具，单项由约 84 秒降至约 14 秒；顶层 full regression 和最终真实 product gate 仍执行完整套件。

本地 telemetry 已升级为只统计 `sample_kind=interactive` 的 v2 脱敏样本；275 条无法区分人工与自动测试的旧样本保留但排除，不删除历史数据。当前本机记录为 6 次 interactive-labeled 调用、1 个观察日、0 feedback，远未达到 30 天或 50 次调用且至少 10 条反馈的 adoption 门槛，不可评估且未实证；固定 benchmark 的 warm search p95 小于 0.5 秒，18 个 warm context 样本 p95 小于 1 秒，两者均满足当前性能目标。

## 真实证据缺口

31 个项目结构都已存在，本机 source mapping 也已达到 31/31，但项目 evidence-ready 仍为 0。全部项目的真实 decision owner 与 validation 签收均未闭环。生成器明确写入 `decision_owner=unassigned`、`manual_validation_pending=true`，不会自动提升 active；源码可定位只关闭 discovery 缺口，不能冒充构建、设备或发布验证。

PCR02 三条 owner-ready candidate 继续保持候选边界，重点补齐：

1. 真实 decision owner 与目标硬件、固件、分支、制品身份。
2. ST77912 高温老化时长、温度区间、故障判据和原始证据引用。
3. SCLK 波形、时序裕量、EMI 条件与结论。
4. framebuffer 到 panel 的端到端显示链路验证，覆盖双屏、刷新率和异常恢复。
5. 发布、回滚、复测路径及 owner 签收。

2026-08-09 到 2026-08-11 的 18 个 Codex archive near-due 条目已按 archive-only/provenance 边界分别刷新到 2026-11-09 至 2026-11-11；该处理不改变其 archived 状态，也不自动提升 active。

153 条专利 archive attachment 相对路径继续保留为 historical warning，不进入 managed Markdown 或 team export。对应 artifact vault 总账为 181 行：178 个 required-present 文件全部通过 size/hash 校验，3 个明确为 external-reference-only；因此该 warning 表示历史正文的相对路径未重写，不表示受管 artifact 丢失。

外部 Codex 仓的 cwd 隔离问题已在独立提交 `de1876a4a9b3196226504469141030dbd0a2ae0e` 修复：`final-ready.sh` 和 `session-coach.sh` 会在模块执行前锚定 Codex 仓根目录，并覆盖同名 Python package collision 回归。该独立变更不属于 Hub 本仓提交，也不改变 Knowledge Hub product gate 的权威边界。

## 验证证据

- [机器 companion](knowledge-hub-product-maturity-implementation-20260713.jsonl) 固定本候选的结构化结果、边界和最终复跑要求。
- `rtk python3 -m pytest -q`：72 passed。
- `rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics --as-of 2026-07-13`：pass，errors=0，warnings=0。
- `rtk bash ~/knowledge-hub/tools/knowledge-regression.sh --json --suite full --as-of 2026-07-13`：140/140 pass，jobs=4。
- `rtk bash ~/knowledge-hub/tools/knowledge-workspace-discover.sh --apply --json`：34/34 registered remotes，0 unmatched，16 duplicate remote diagnostics，重复执行 changed=0；只写 ignored local mapping。
- `rtk bash ~/knowledge-hub/tools/knowledge-project-readiness.sh --check --json --as-of 2026-07-13`：31 projects、31 routes、124 slots、changed=0；31/31 source mapped、0/31 evidence-ready。
- `rtk bash ~/knowledge-hub/tools/knowledge-retrieval-benchmark.sh --json`：20/20 top-3，283/283 route，hit rate 100%，MRR 1.0，warm p95 小于 0.5 秒。
- `rtk bash ~/knowledge-hub/tools/knowledge-link-audit.sh --json --strict`：722 Markdown、1400 links、0 blocking、147/147 managed Properties、3 Bases。
- `rtk bash ~/knowledge-hub/tools/knowledge-obsidian-view-build.sh --check --json`：3 MOC、3 Bases、drift=0、changed=0；文件层 pass，GUI runtime=`not-validated`。
- `rtk bash ~/knowledge-hub/tools/knowledge-export.sh --plan --json`：ready；实际本地 export 的 secret 与 link closure 均为 pass，使用 manifest v2 和 atomic publish。
- `rtk bash ~/knowledge-hub/tools/knowledge-restore-drill.sh --source-mode candidate --as-of 2026-07-13 --json`：候选快照通过，无 cache/local workspace mapping；提交后必须再以 `--source-mode head` 复核。
- `rtk bash ~/knowledge-hub/tools/knowledge-final-gate.sh --final-profile product --full-regression --as-of 2026-07-13 --json`：平台 pass；overall=needs-owner-review；structural=31/31；evidence=0/31；retrieval=100%。

## 下一步

1. 真实 owner 按项目补 decision 与 validation evidence，不把 31/31 本机 source mapping 当作签收，也不批量自动关闭 124 个 reviewing 槽位。
2. PCR02 优先完成 ST77912 高温、SCLK/EMI、端到端显示、发布与回滚验证。
3. release 或“全面终态成熟”声明必须运行 `knowledge-final-gate.sh --final-profile product --require-terminal`；退出 2 时保持 owner-review 状态。
4. 当前 dirty worktree 按用户授权只在全部门禁通过后形成一个本地 commit；随后以 HEAD restore 和 full product gate 复核。该提交不代表远端发布。

## 回滚与边界

- 本仓修改通过 Git diff 和事务 ledger 可审计；未创建本地 commit 前以当前 working tree 为唯一候选快照。
- local cache、search DB、export 和 restore snapshot 均在 ignored 目录或 `/tmp`，可重建，不是长期正文。
- 不以降低 reviewing 阈值、删除 owner gap 或伪造 workspace 路径来换取 terminal pass。
- must-not：owner decision、active promotion、memory write、source project write、remote publish、push、merge、tag、release；允许动作仅为门禁全绿后的 Hub 本地 commit。
