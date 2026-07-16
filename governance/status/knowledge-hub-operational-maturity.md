# Knowledge Hub 产品成熟度历史快照 2026-07-13

> 归档身份：registry item `knowledge-hub-operational-maturity-20260701` 的状态为 `archived`。本页只保存 2026-07-13 当日结论与命令证据，不是当前状态入口；当前状态以 [`governance/product/validation/project-readiness.md`](../product/validation/project-readiness.md) 和实时 product gate 输出为准。

## 结论

Knowledge Hub 已按“统一知识控制面”完成平台产品化：canonical Markdown、registry、schema catalog、Python 内核、事务化生命周期、可解释检索/context、30 个规范项目结构与路由、Obsidian 只读工作台、团队导出、恢复演练和统一产品门禁均有稳定入口。`pcr02` 仅作为 group 元数据，不重复占用项目槽位。

当前不能声明“长期使用终态已经实证”，也不能声明 30 个规范项目的内容和发布证据全部成熟。项目结构槽位刻意保持 `reviewing`；本机 source mapping 已达到 30/30，但它只证明仓库可定位。真实 decision owner、当前 source commit、人工/实机、制品、release 和 rollback 证据仍为 0/30，尚未逐项目闭环。正确结论应是：

- 平台产品化：由当前 product gate 技术检查决定。
- 平台发布：还必须有 clean committed HEAD、已跟踪依赖清单、full regression 和该 HEAD 的 `git archive` 恢复证据。
- 内容成熟度：存在 owner/source/device/release 缺口时保持 `needs-owner-review` 或 `partial`。
- 长期采用成熟度：连续 30 天或至少 50 次脱敏本地调用前不得声明已实证。

本页不替代 owner decision，不提升 active，不写 memory，不修改源项目，也不代表 ST77912 高温老化、SCLK/EMI、HIL、发布或远端状态已签收。

## 唯一终态接口

当前运行态只保留一个终态 profile 和一个命令入口：

```bash
rtk bash ~/knowledge-hub/tools/knowledge-final-gate.sh --json --final-profile product --as-of 2026-07-13
rtk bash ~/knowledge-hub/tools/knowledge-final-gate.sh --json --final-profile product --regression-suite full --as-of 2026-07-13
rtk bash ~/knowledge-hub/tools/knowledge-final-gate.sh --require-terminal --final-profile product --as-of 2026-07-13
```

可执行接口以以上命令为准。archive/ledger 中的命令只解释当时证据，不作为 README、runbook、模板、生成器或自动化入口。

## 成熟度模型

| 维度 | 判据 | 当前边界 |
|---|---|---|
| `platform_status` | check、strict status、source runtime、unit/full regression、diff、事务恢复、schema、link/Obsidian、export、restore | 技术检查必须全部通过，任一失败为 `needs-fix` |
| `content_readiness` | 30×4 槽位、30×9 route、有效 canonical 内容及 evidence readiness | 结构完整不等于事实成熟；group 元数据不重复计数；缺真实证据保持 pending |
| `retrieval_quality` | known-answer Top-3、MRR、零命中、current 生命周期过滤、解释字段和 fallback | archived/superseded/audit/provenance 不得进入 `context.current` |
| `operational_readiness` | health snapshot、team export、fresh restore、transaction recovery、脱敏 metrics | 本地恢复和导出通过不等于远端发布 |
| `delivery_readiness` | clean committed HEAD、tracked dependency manifests、full regression、HEAD `git archive` restore | dirty candidate 只能声明技术候选通过，不能声明平台发布完成 |
| `overall_status` | 技术、内容、owner evidence、full regression、采用观察共同决定 | 只允许 `needs-fix`、`needs-owner-review`、`partial`、`mature` |

候选文档、目录存在、Properties 完整或治理门禁通过都不能冒充 owner、source、设备和 release 证据。

## 架构终态

- Markdown：标题、摘要、标签、关系和正文内容权威；managed 文档使用一致 Properties。
- Registry：身份、path、status、owner、review_after、promotion、authorization 和 lifecycle 权威。
- Python package：`tools.codex_assets.knowledge_hub` 是共享内核，shell 入口仅定位根目录、注入 `PYTHONPATH` 和转发参数。
- Schema：`schemas/catalog.json` 只发布当前 contract；breaking 字段或语义变化必须使用新 contract id 并提供回归证据。
- Index/cache：核心 Markdown 索引可重建；SQLite FTS 与 metrics 位于忽略目录，缺失或过期时安全回退。
- Local workspace：`local/workspaces.json` 只保存本机映射且不提交；tracked registry 只保存 `workspace://` 和 remote key。
- Store：多文件 apply 使用单写锁、expected hash、journal、临时文件、fsync、`os.replace` 和 recovery audit。
- Obsidian：直接消费同一份 Markdown；`.obsidian/` 私有，Properties/MOC/Bases 只提供发现和阅读，不改变权威状态。
- Export/restore：团队导出按 visibility/status/evidence policy 选择并生成 hash manifest；恢复演练不依赖 cache 或本机 workspace mapping。

## 功能终态

| 能力 | 稳定入口 | 关键边界 |
|---|---|---|
| 捕获 | `knowledge-capture.sh`、`knowledge-new.sh` | `--apply` 只创建 draft/reviewing/personal，不创建 active |
| 生命周期 | `knowledge-review-attest.sh`、`knowledge-promote.sh`、`knowledge-retire.sh` | execution authorization 与 content review attestation 独立校验；明确真人决定后可机械生成本地 form，active 禁止 delegated mode，工具不生成 owner 决策 |
| 恢复审计 | `knowledge-recovery-audit.sh` | 只读检查未完成 transaction 和恢复动作 |
| 检索/context | `knowledge-search.sh`、`knowledge-context.sh` | FTS5 + 中文 2/3-gram + weighted recall + fallback + `why_selected` |
| 项目矩阵 | `knowledge-project-readiness.sh` | 30×4 reviewing 槽位；30/30 本机 source mapped，0/30 evidence-ready；group 元数据不重复计数 |
| PCR02 证据路径 | `knowledge-pcr02-owner-readiness.sh` | 三条 candidate 已绑定 hash-bound owner 决定，继续保持 reviewing、实机/release/evidence pending |
| Obsidian | `knowledge-obsidian-view-build.sh`、`knowledge-link-audit.sh` | 文件层 Properties/MOC/Base/链接自动检查；真实 GUI 验收单独报告，当前为 `not-validated` |
| 质量 | `knowledge-retrieval-benchmark.sh`、`knowledge-regression.sh` | full regression 仅跟踪 slowest 10，不泛化重构 |
| 交付恢复 | `knowledge-export.sh`、`knowledge-restore-drill.sh` | 不发布远端、不导出 personal/pending owner decision/secret |
| 运营 | `knowledge-health-summary.sh`、`knowledge-metrics.sh`、`knowledge-feedback.sh` | snapshot 快路径；metrics v2 只统计当前 interaction contract，feedback 绑定真实检索，只保存查询 hash 和 found/not-found，不保存原始查询 |

## 项目内容边界

30 个 registered project 均有 profile、runbook、decision candidate 和 validation readiness。`pcr02` 只保留为 group 元数据，不生成重复 readiness 槽位。结构覆盖只能证明入口可达：

- source 可定位时，只读发现 remote、README、构建/测试入口和版本线索；本轮不执行源仓构建、测试或发布。
- source 不可定位时，只写 registry 已知事实和 `manual_validation_pending`，不得推断当前源码。
- decision candidate 初始默认 `decision_owner=unassigned`；PCR02 三项已由 2026-07-16 hash-bound attestation 绑定 owner，但没有独立 active authorization 和真实证据时仍不得 promotion。
- 设备、板级、实验室和 release 结论必须记录 source commit、制品 hash、设备/环境、命令、返回码、结果及回滚。

PCR02 三条 owner-attested candidate 的详细路径见 [PCR02 owner-ready validation paths](../../artifacts/manifests/pcr02-owner-ready-validation-paths-20260713.md)。Owner 边界已接受；ST77912 仍必须补齐高温老化、SCLK/CS/DC/MOSI 信号、EMI 风险、端到端双屏显示、发布制品和降档回滚证据。

## Obsidian 关系

Knowledge Hub 是知识系统和权威控制面，Obsidian 是可选客户端。有效结合方式是：

- 直接打开 Hub 根目录，不复制第二份正文。
- 使用 Properties、标准 Markdown Related links、Backlinks、Graph、总 MOC、项目 MOC、主题 MOC 和只读 Bases。
- Inbox 模板只创建候选；生命周期仍由 Hub 工具和 registry 决定。
- 不依赖 community plugin，不启用 Publish/Sync 自动写入，不把 Graph 中心度当成熟度。
- `aliases/tags/related` 漂移由 view build 和 link audit 阻断，不能静默同步错误状态。

## 运营与性能

日常快路径：

```bash
rtk bash ~/knowledge-hub/tools/knowledge-health-summary.sh --json
rtk bash ~/knowledge-hub/tools/knowledge-search.sh "<query>" --json
rtk bash ~/knowledge-hub/tools/knowledge-context.sh --cwd "$PWD" --query "<task>" --task-type general --json
rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
```

显式刷新与 release 级验证：

```bash
rtk bash ~/knowledge-hub/tools/knowledge-health-summary.sh --refresh-gate --json --as-of 2026-07-13
rtk bash ~/knowledge-hub/tools/knowledge-regression-trend.sh --run --suite full --json --as-of 2026-07-13
rtk bash ~/knowledge-hub/tools/knowledge-restore-drill.sh --source-mode candidate --json --as-of 2026-07-13
rtk bash ~/knowledge-hub/tools/knowledge-restore-drill.sh --source-mode head --json --as-of 2026-07-13
rtk bash ~/knowledge-hub/tools/knowledge-final-gate.sh --json --final-profile product --regression-suite full --as-of 2026-07-13
```

性能判断只依据脱敏本地 metrics 和 full regression `slowest_results[0:10]`。目标为 warm search p95 ≤ 0.5 秒、context p95 ≤ 1 秒、status/默认 health ≤ 3 秒、quick final ≤ 15 秒；当前 contract 的 search/context 各不足 10 个样本时只能标为 `pending`。历史 contract 样本不删除，但不与当前实现 P95 混算；显式反馈必须绑定真实 interaction，不能靠重复反馈刷绿。未达到时先定位具体 slowest 项，不做跨模块泛化重构。

## 当日待复核与历史边界

- 2026-08-09 至 2026-08-11 的 18 条 Codex archive near-due 项已逐条复核 archive-only/provenance 边界并刷新到 2026-11-09 至 2026-11-11。
- 18 条均保持 archive/provenance 或 reviewing governance ledger 边界，promotion 为 none，没有自动提升 active。
- archive/ledger 中的命令、过程记录和测试输出只作 provenance；默认 search/context/current 不消费这些材料。

## 剩余风险

- 30/30 本机 source mapping 只属于 discovery 证据；30 个规范项目真实 evidence readiness 仍为 0/30。
- PCR02 三条候选已补验证路径，但尚无本轮真实 owner、实机、高温、EMI、release 或 rollback 执行证据。
- Obsidian managed Markdown、MOC、Bases 和链接自动检查已通过，但尚未在真实 GUI 完成 Properties、Backlinks、Bases 与导航验收。
- 历史 patent archive 有缺失图片引用，只作为历史 warning；当前 managed Markdown 链接、Properties 和关系目标必须保持零错误。
- candidate restore 必须匹配当前 working-tree signature；平台发布还必须匹配 clean committed HEAD 的 `git archive` restore。
- 观察期前只能声明“平台产品化完成”，不能声明“长期使用终态已被实证”。

## 证据索引

- [产品成熟度实现审计](../../artifacts/manifests/knowledge-hub-product-maturity-implementation-20260713.md)
- [全面成熟度修复计划](../../artifacts/manifests/knowledge-hub-comprehensive-maturity-remediation-20260713.md)
- [Obsidian 集成边界](../obsidian-integration.md)
- [项目成熟度工作台](../../indexes/project-readiness.md)
- [Knowledge Hub Home](../../indexes/obsidian-home.md)
