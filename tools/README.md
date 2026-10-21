# Knowledge Hub Tools

Provider `archive --help` 的 `source_contract` 列出归档输入要求。工程文档经常带有
`id/status/owner/path` 等 frontmatter；这些字段由 Provider 分配，不能直接作为候选输入。
应另建脱敏结论 Markdown，仅保留 `title/summary_zh/tags/primary_language/source_language/translation_status/terminology_status`
这些描述字段，保留工程原记录，通过 `--subject`、`--kind` 明确主体和类型。

`SOURCE_REJECTED` 的 `diagnostics` 返回固定类别，不回显命中的正文、路径、字段名或值：
`unsupported-source-metadata` 或 `invalid-source-metadata` 表示输入头不符合契约；
`sanitization-required` 要求确认脱敏后传入 `--sanitized`；`empty-source-body` 和
`source-title-required` 要求补充正文或标题；`sensitive-content`、`machine-specific-content`、
`raw-session-content` 要求先脱敏、提炼。预检 `PLANNED` 仍不代表归档成功；
只有 `ARCHIVED/ALREADY_ARCHIVED` 且 `persisted=true` 才能声明候选已归档。

所有工具默认保守：优先只读、dry-run、report-only；允许在 Hub 本仓内完成可回滚维护。commit/push/merge/release/tag、删除、发布、提升 active、关闭 owner gate、写 memory 和源项目写入分别需要明确授权。

## 外部来源逐文件快照（私有证据候选）

`knowledge-inventory.sh` 保留原有的 Hub source control 盘点；额外增加**显式源目录/单文件只读快照**模式，不增加公共命令或新的 canonical 状态源。须在能访问真实来源的机器上运行，不能通过 GitHub 上的 Hub 目录反推外部迁移完成。

```bash
rtk bash ~/knowledge-hub/tools/knowledge-inventory.sh \
  --snapshot-source-id embedded-knowledge \
  --snapshot-source-path /absolute/path/to/original/source \
  --snapshot-claimed-revision <40位小写Git提交SHA> \
  --json
```

未获得可信版本标识时**省略** `--snapshot-claimed-revision`，不可填 `main`、`latest` 或臆造哈希；即使填写 40 位 SHA，也只是**未认证的版本声明**。源 ID 必须存在于 `registry/sources.json` 或 `registry/retired-sources.jsonl`，扫描根必须由调用者显式传入。仅排除目录中的 `.git` 版本控制元数据，其余常规文件均计数并流式 SHA-256；符号链接、特殊文件、读取错误、目录变化或预算溢出均 fail closed。上限为 20,000 文件、20,000 目录、单文件 256 MiB、总读取 2 GiB，不适合原始大 SDK/运行时制品直接整仓扫描，应先确定适用的证据范围而**不得静默跳过**。

快照以内容寻址写到本机忽略提交的 `.tmp/source-snapshots/<source-id>/<digest>.json`，文件权限为 0600；只输出不含绝对源路径的简短 JSON 摘要。**文件相对路径仍可能包含敏感名称**，完整快照不得直接放进公开 PR、Actions 日志、源仓或知识正文。该入口不会复制正文、修改外部源、写 registry、提升条目或关闭任何 owner/Content/Product gate。

输出固定为 `status=candidate`，并显式保留 `claimed_revision_verified=false`、`origin_binding_verified=false`、`atomic_snapshot_verified=false`、`target_disposition_verified=false`、`full_external_migration_proven=false`。源侧候选获取后，仍需可信修订/原子快照绑定、每文件与现有 `sources/<id>/inventory.jsonl` 及唯一目标处置的核对、授权语义复核，才能判断单个来源是否真正迁移完毕。

**私有逐文件对账（只读）：**源侧快照已经产生后，复用同一工具入口与既有 source inventory 做严格的相对路径、SHA-256 和字节数匹配。示例：

```bash
rtk bash ~/knowledge-hub/tools/knowledge-inventory.sh \
  --reconcile-snapshot .tmp/source-snapshots/embedded-knowledge/<digest>.json \
  --json
```

此命令只接受 Hub 私有快照目录内的内容寻址 JSON；拒绝外部文件、符号链接、篡改、非 0600 文件和非 owner-only 的私有子目录。比较时根据已登记 source `origin_path` 的**字符串范围**匹配 inventory 中逐文件记录，不猜测文件归属或用根目录/批次级记录补齐缺口。只输出候选精确匹配、缺行、缺 hash、冲突、歧义和超出快照范围的数量；不向终端暴露源侧文件名或原始内容。

即使全部字节级候选匹配，也固定 `full_external_migration_proven=false`；因为源 revision 尚未经可信渠道认证，普通目录扫描没有原子快照保证，且未验证目标文件处置/版本、授权内容审核和真实 owner 决策。对账结果是同一源控制面上的**观察投影**，不是新的可变状态或 Product/Repository 终态。

## 运营与检索闭环

并发快照、活动回执身份、受控 Provider 执行、检查缓存、独立评估与复核消费详见[运营契约](optimization-operations.md)。

日常仍使用 5 条稳定入口。需要深入时选择以下选项：

| 目标 | 已有入口与选项 | 结果边界 |
| --- | --- | --- |
| 近期采用健康 | `knowledge-metrics.sh --summary-json` 的 recent_health | 7/30/90 天按当前 contract/generation 统计；累计 adoption 单列，local-only 不成为生产证据 |
| owner 批次复核 | `knowledge-review-after.sh --batch-size 10 --json` | current-validity、candidate-decision、historical-integrity 分流；正文/镜像、重复候选和证据目录自动准备，人签语义决定 |
| 新鲜健康概览 | `knowledge-health-summary.sh --refresh-gate --gate-suite quick --summary-json` | 更新本机 quick 快照；full 留在正式工程批次，不补造外部观测 |
| 自然问句 | `knowledge-search.sh "如何在 Obsidian 查看知识的反向链接和关系图？" --query-mode natural --summary-json --no-telemetry` | 显式选择的问句规范化；否定约束保留，默认 exact 不变 |
| 评估集对比 | `knowledge-retrieval-benchmark.sh --holdout --cases tests/fixtures/retrieval_unseen.json` | 明确区分 dev/regression 与冻结工程验证；绑定数据集、源码和 evaluator，不是 production-derived 资格 |
| Provider 权限 | `rtk bash ~/codex/scripts/knowledge-provider.sh status` | 分操作能力与 policy/config 状态；实际调用继续校验 |
| 事务异常 | `knowledge-recovery-audit.sh --summary-json` | 用完整 writes 和 before/after hash 判断，不能仅看 applied_paths；冲突保留后续用户写入 |
| 运行时维护 | `knowledge-runtime-maintenance.sh --summary-json` | 默认计划；明确授权后按 scope apply，保护当前索引、未完成事务和 telemetry |

复核 packet 的优先级由当前事实暴露、治理风险和逾期时间决定；只选择有界批次，不自动延后日期、删候选、代签或提升。包内 preparation_ms 是机器准备耗时，不冒充人工审阅耗时。归档输入的摘要/主题标签经过校验保留；近重复只提示关联，回执绑定事务和内容 hash。可通过已有 traceparent 关联归档，不保存 raw query/body；观测失败不使已验证的持久化结果失败。

`knowledge-review-after.sh --json --include-sources --include-owner-gates --triage-limit 500 --batch-size 10` 会同时准备条目与来源的 `evidence_triage.owner_preparation` 交接包。查看 `remaining` 和 `overflow` 确认实际覆盖；声明 Owner 路由与真实签收分开，机器包不产生审阅决定。投影只保留有界元数据，canonical JSON UTF-8 最多 48KiB。

## CI 职责与成本

| 链路 | 责任 | 运行策略 |
| --- | --- | --- |
| quality | runtime 兼容、pytest、工程/供应链、恢复、MCP | PR 代表版本，master 完整矩阵；完整验证复用已有 engineering evidence |
| signed-quality-attestation | 同 master SHA 的 Quality 制品签名与回读 | 只消费受信 push/master 成功 run；subject、policy、verifier 和 evidence digest 分开验证 |
| security-critical-change-review | 高风险修改的人审绑定 | 不与普通 pytest 合并或跳过；批准绑定精确 head/fingerprint |
| terminal-closure / hosting reconcile | 仓库托管与终态事实 | 不代替产品、owner 或生产采用验收 |
| observation / evidence intake / ratchet | 真实外部观测与有界状态推进 | 缺真实 provenance 保持阻断，不用 fixture 刷绿 |
| recovery-drill | 独立恢复验证 | 保留周期演练和证据，不以同机备份宣称异地恢复 |

优化 CI 先比较同一提交的 job/step 时长、队列等待和重复执行，再调整职责。不能减少安全、exact-head、签名或恢复约束换取速度。关键事务/归档故障分支使用 `coverage --branch` 的定向验证，报告与全仓 statement coverage 分开；不直接让历史分支覆盖率阻断无关修改。

full engineering 的子命令统一使用本仓受限 CI transport。外层完整 pytest 与 full regression 仍执行；递归标记本身不构成成功证据，缺少新鲜父测试证据时返回 delegated-unverified，不给 shared_unit_tests PASS。超时返回结构化失败，不提高时间预算或当作通过。归档只对提交前的 WriteConflict 自动重试至多三次，绑定同一份已检查输入；持久化/回读不确定、脱敏和策略失败均不自动重试。

用户、文档和自动化默认只调用稳定 shell 入口：

```bash
rtk bash ~/knowledge-hub/tools/<tool>.sh ...
```

不要在长期文档中直接引用内部 Python 入口，也不要绕过 `rtk` 裸跑 shell 命令。

所有 `tools/*.sh` 都是稳定薄包装层：只解析自身目录、定位 `ROOT`、注入 `PYTHONPATH` 并转发到 `tools.codex_assets.knowledge_hub`。registry/frontmatter、日期、路径脱敏、schema、索引、授权、诊断和事务语义只在 Python 内核维护一份。

## 工具资产候选归档

`knowledge-capture.sh --tool-asset-candidate` 接收源仓候选检测器生成的脱敏 Markdown，只归档工具治理元数据与验证摘要。它会验证：

- `source_repo` 能唯一路由到 `registry/repositories.json` 中的项目；
- `source_commit`、源码相对路径和 `candidate_sha256` 合法；
- unit test、CLI help、dry-run、非仓库 cwd 四类验证状态齐全；
- endpoint、credential、raw log 三类脱敏声明满足安全门禁；
- 输入中没有 secret-like 内容或私有端点。

默认只生成事务计划：

```bash
rtk bash ~/knowledge-hub/tools/knowledge-capture.sh \
  --tool-asset-candidate /tmp/tool-asset-candidates/<timestamp>/hub-candidate.md \
  --json
```

人工确认计划后才可显式执行 `--apply`。应用会原子创建 `projects/<project>/validation/tool-asset-candidate-*.md`，并同步 registry、核心索引、Obsidian 派生视图和 lifecycle ledger；新条目始终为 `reviewing`，不会生成 owner decision 或自动提升。该模式复用既有 capture wrapper，不增加公共命令面；无人值守自动化不得使用 `--apply`。

项目会话可在收尾时自动扫描本次 Git 变更，并直接串联 Hub dry-run：

```bash
rtk bash ~/knowledge-hub/tools/knowledge-capture.sh \
  --scan-tool-assets \
  --repo-root "$PWD" \
  --hub-candidate-out "$PWD/tmp/tool-asset-candidates/<session-id>/hub-candidate.md" \
  --source-repo <registry-repo-id> \
  --session-path <本会话修改的工具相对路径> \
  --hub-dry-run \
  --json
```

存在可唯一匹配的 `origin` 时可省略 `--source-repo`。`--hub-dry-run` 要求至少一个显式 `--session-path`，多个文件重复传入，防止把会话开始前的用户 dirty 变更错误归因到当前会话。不串联 Hub 时可省略该参数做 all-dirty report-only 扫描。扫描范围固定为本次变更中的 `codex_assets/`、`tools/`、`scripts/` 文本工具；扫描器不执行工具代码，只识别 CLI/help、dry-run、测试引用、内联文档和显式传入的验证结果。实际完成验证后可传入：

```bash
--unit-tests pass \
--cli-help pass \
--candidate-dry-run pass \
--non-repo-cwd pass
```

没有证据时保持默认 `not-run`。候选输出只允许位于项目 `tmp/`、`.tmp/` 或系统 `/tmp`；secret、私有端点、非 UTF-8、symlink、超大文件、raw/runtime 路径会被拒绝。当前实现每次选择最高分的单文件候选生成 `hub-candidate.md`，其他发现保留在命令 JSON 摘要中。

### 跨会话与跨项目自动发现

推荐在项目会话开始时记录基线：

```bash
rtk bash ~/knowledge-hub/tools/knowledge-capture.sh \
  --tool-asset-session-start \
  --repo-root "$PWD" \
  --session-state-out "$PWD/.tmp/tool-asset-sessions/<session-id>/baseline.json" \
  --json
```

会话结束时关闭并聚合：

```bash
rtk bash ~/knowledge-hub/tools/knowledge-capture.sh \
  --tool-asset-session-close \
  --repo-root "$PWD" \
  --session-state "$PWD/.tmp/tool-asset-sessions/<session-id>/baseline.json" \
  --hub-candidate-out "$PWD/tmp/tool-asset-candidates/<session-id>/hub-candidate.md" \
  --used-tool-path codex_assets/tools/<本次调用但未修改的工具> \
  --hub-dry-run \
  --json
```

baseline 只保存 HEAD、路径、size 和 SHA256。结束时自动分类为 `created-in-session`、`modified-in-session`、`deleted-in-session` 或 `used-unchanged-in-session`。Observation 默认进入忽略提交的 `~/knowledge-hub/.cache/knowledge-hub/tool-assets/observations.jsonl`，保存 repo/project、session hash、工具 hash、确定性 capability signature、验证枚举和时间，不保存原始会话或参数值。

同项目至少两个不同会话出现同一 capability，生成 `keep-project-tool` 候选；至少三个不同会话且覆盖两个项目时，生成 `recommend-global-codex` 候选。未达到阈值时本地 observation 正常落账，但 `hub_plan.status=not-ready`。可用 `--observation-ledger /tmp/<file>.jsonl` 覆盖本机 ledger 位置进行隔离测试。

## 低复杂度入口速查

日常维护 5 条短命令：

```bash
rtk bash ~/knowledge-hub/tools/knowledge-health-summary.sh --summary-json
rtk bash ~/knowledge-hub/tools/knowledge-new.sh --kind <kind> --domain <domain> --owner <owner> --id <id> --path <path> --summary-json
rtk bash ~/knowledge-hub/tools/knowledge-search.sh "<关键词>" --summary-json
rtk bash ~/knowledge-hub/tools/knowledge-review-after.sh --window-days 30 --summary-json
rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --summary-json --diagnostics
```

`registry/command-surface.json` 是稳定 wrapper 的机器可读目录，数量以其中的 `wrapper_baseline` 和 `commands` 为准，按五平面与 daily/maintenance/governance/engineering/internal 分级；daily 固定为这 5 条，复杂度门禁禁止 wrapper 无计划增长。公共 JSON CLI 使用统一 `status_contract`，状态稳定为 `pass / needs-review / needs-fix / blocked`；`--json` 用于完整取证，`--summary-json` 用于有界首屏。

忽略提交的运行时资产使用独立保留策略维护。默认命令只输出精确候选，不删除任何内容；只有显式 `--apply` 才清理旧 schema 搜索索引、超过保留期且状态为 `applied/rolled-back` 的事务目录，或把运行时目录/文件权限收紧到 `0700/0600`。当前索引、未来版本索引、telemetry、未完成/无 journal 事务始终保留，symlink 或特殊文件会阻断整批计划：

```bash
rtk bash ~/knowledge-hub/tools/knowledge-runtime-maintenance.sh --scope all --summary-json
rtk bash ~/knowledge-hub/tools/knowledge-runtime-maintenance.sh --scope obsolete-search-index --apply --json
rtk bash ~/knowledge-hub/tools/knowledge-runtime-maintenance.sh --scope runtime-permissions --apply --json
```

短命令只做首屏维护和日常巡检；全面产品成熟度验收只有一个入口：`knowledge-final-gate.sh --final-profile product`。

工程与供应链门禁使用 `knowledge-engineering-check.sh`：

| 模式 | 命令 | 语义 |
|---|---|---|
| contract | `knowledge-engineering-check.sh --mode contract --json` | 只读验证能力型系统 Python 选择、Python 3.8–3.14 CI 覆盖、直接 pin、hash locks、CI least privilege、Action SHA、精确 CI transport allowlist 和 Dependabot |
| full | `knowledge-engineering-check.sh --mode full --json` | 在 hash-locked Python 3.10–3.14 工程环境执行全包 Ruff correctness、直接 mypy 清单、Bandit 中高风险扫描、pytest 与 full regression/subprocess 合并后的 whole-package statement coverage（总计 ≥75%）、build、Hub check、retrieval、pip-audit 和 SBOM；成功快照绑定 candidate signature |

full regression 属于 Level 2 长门禁，默认不对非零退出、确定性错误或未知失败自动重试；仅明确 transient 的 EAGAIN/EINTR 异常或调用者显式分类的退出码可在既定预算内重试。每次 attempt 的退出码、错误分类和有界 stdout/stderr 都写入工程快照，成功恢复则显式标记 `recovered_after_retry=true`，预算耗尽仍阻断。full 模式写入的 coverage、build、SBOM 和工程快照都位于 `.tmp/` 或 `.cache/`，不是长期知识或 release artifact。product full gate 要求 24 小时内且 signature 匹配的工程快照；紧接 full engineering 运行时可加 `--reuse-engineering-evidence`，只复用同一签名快照中的 coverage/pytest 与 full regression 通过证据。quick gate 自动复用同一签名的新鲜 coverage/pytest 证据以满足日常反馈时延，但不会取得 full regression 或 `terminal=true` 资格；快照陈旧、签名变化或证据项不完整时一律自动重跑真实测试。

## Agent 运行时只读入口

| 能力 | 稳定命令 | 权威与失败边界 |
|---|---|---|
| 有界导航 | `knowledge-map.sh --summary-json` | registry 派生；默认 20 items / 8192 bytes，cursor 绑定完整 source fingerprint 与 filters；domain 按路径段匹配，personal vocabulary 默认不暴露；map 不可作为引用证据 |
| 分层证据 | `knowledge-evidence-pack.sh "<query>" --scope-ref <scope> --json` | active 与 provisional 分道；terminal/personal 不服务；只有显式 active contract 进入 MUST/SHOULD |
| 动作预检 | `knowledge-action-check.sh --task <task> --candidate <action> --scope-ref <scope> --json` | `ALLOW/BLOCK/NEEDS_REVIEW`；无规则不 ALLOW，候选规则无 authority；task/candidate 各最多 8192 字符，scope/exception 各最多 32 项；不安全 regex fail-closed，输出不回显 candidate 正文 |
| 合规评测 | `knowledge-compliance-eval.sh --root tests/fixtures/agent_compliance_root --cases tests/fixtures/agent_compliance_cases.jsonl --minimum-cases 50 --require-verdict-coverage --json` | v2 批量复放显式 active fixture contract；必须覆盖 ALLOW/BLOCK/NEEDS_REVIEW 三态，文件 ≤1 MiB、单行 ≤16 KiB、最多 1000 条；只输出 candidate SHA、item id、verdict coverage 和 high-risk false-allow 汇总，不输出动作正文，也不把 reviewing 候选提升为 active |
| Shadow 路由 | `knowledge-proposal-route.sh --proposal <candidate.json> --json`、`knowledge-proposal-shadow-stats.sh --json` | `registry/agent-review-policy.json` 默认禁用；proposal ≤128 KiB、quote ≤4096 字符、证据源 ≤8 MiB，策略和身份越界时 fail-closed；actual route 固定 human-review；可选 `0600` audit 只写固定枚举的脱敏 metadata，以 sequence + hash chain 追加，限制 64 MiB/16 KiB 单行/100000 行并拒绝 symlink 或截断尾行；stats 不回显未知 route/reason |
| 原始证据检查 | `knowledge-evidence-ledger.sh --ledger <events.jsonl> --json` | 严格只读、metadata-only、chain fail-closed；默认 64 MiB/100000 events/单行 1 MiB 输入预算；永远 reference-only，不复制 raw body |
| 制品恢复演练 | `knowledge-artifact-restore-drill.sh --release-root <dir> --source-label <stable-ref> --json` | source 只读；按 `SHA256SUMS.txt` 校验、临时复制、故意破坏、恢复和 source 不变复核；manifest ≤1 MiB、≤1000 文件、总量 ≤10 GiB，拒绝 symlink/路径逃逸；不证明远端、设备或生产回滚 |

这些入口独立实现并参考 `memdsl@2d87af7` / `rawmem@9842be6` 的公开契约；不引入上游运行时依赖、不启动 MCP/daemon、不安装 hook、不修改外部仓库。长期采用边界见 `governance/product/decisions/agent-runtime-contract-absorption-candidate.md`。

## 产品成熟度入口

```bash
rtk bash ~/knowledge-hub/tools/knowledge-final-gate.sh --final-profile product --as-of 2026-07-13
rtk bash ~/knowledge-hub/tools/knowledge-final-gate.sh --summary-json --final-profile product --as-of 2026-07-13
rtk bash ~/knowledge-hub/tools/knowledge-final-gate.sh --json --final-profile product --as-of 2026-07-13
rtk bash ~/knowledge-hub/tools/knowledge-final-gate.sh --summary-json --final-profile product --regression-suite full --reuse-engineering-evidence --as-of 2026-07-13
rtk bash ~/knowledge-hub/tools/knowledge-final-gate.sh --require-terminal --final-profile product --as-of 2026-07-13
```

`knowledge-final-gate.sh --final-profile product` 聚合一致性、共享单元测试、事务恢复、链接、检索基准、30 个规范项目结构、task route、Obsidian Properties/MOC/Bases、团队导出计划和恢复演练。Product v5 只保留一个顶层 `status` 与一个 `terminal`，并刻意分离：

- `maturity_axes.platform`：平台技术能力是否通过。
- `maturity_axes.delivery` 与 `delivery_readiness`：分别报告本地 clean committed HEAD、远端发布和异地恢复证据。
- `maturity_axes.status`：四值 canonical 综合状态。
- `terminal`：只有本地交付、远端发布、异地恢复、真实采用，以及规范项目的 owner/source/人工或实机/发布证据全部闭环时才为真。

默认模式只要技术门禁通过即退出 0；`--require-terminal` 会在真实证据未闭环时退出 2。新项目首次生成的 4 个槽位默认使用 `decision_owner=unassigned`；当前 30 个项目已由 `knowledge-hub-terminal-owner-attestation-20260716` 统一绑定 `decision_owner=leiwenjun`，3 项 PCR02 专项边界又由 `knowledge-hub-pcr02-specialized-owner-attestation-20260716` 精确绑定。两组候选都仍保持 `reviewing`、`manual_validation_pending=true` 和 `promotion=none`，工具不得据此自动提升 active 或把 evidence contract 判为 ready。

配套稳定入口：

| 能力 | 命令 | 关键边界 |
|---|---|---|
| 30 项目结构 | `knowledge-project-readiness.sh --check --json` | 每项目只检查/生成 1 份 validation evidence contract 与统一 dashboard；不生成 profile/runbook/decision 模板投影，不生成真实项目事实；group 元数据不重复计数 |
| 本机源码发现 | `knowledge-workspace-discover.sh --plan --json` | 默认只读扫描 `~` 与存在时的 `/vsdata/<user>`，仅按 registered remote key 精确匹配；`--apply` 只写未跟踪的 `local/workspaces.json` |
| 检索质量 | `knowledge-retrieval-benchmark.sh --summary-json` | 28 条语义 case + 274 条动态 route；v3 同时校验权威/排序/污染率、index preparation、warm、4-worker 并发和 10 倍 corpus |
| 链接与 Bases | `knowledge-link-audit.sh --summary-json` | 有界首屏；`--json` 提供完整历史 warning 取证。检查标准 Markdown links、readiness inbound 和只读 `.base` schema；不读取本机 `.obsidian/` 配置作为权威 |
| Obsidian 视图 | `knowledge-obsidian-view-build.sh --check --json` | 检查 managed Properties、总/项目/主题 MOC 和只读 Bases；真实 GUI 验收单列为 `obsidian_runtime_status`，不由文件层结果冒充 |
| 团队导出 | `knowledge-export.sh --plan --json` | 仅 `active + team-internal` canonical Markdown；执行共享 secret scan、链接闭包、hash manifest 和原子发布 |
| 恢复演练 | `knowledge-restore-drill.sh --source-mode candidate\|head --as-of 2026-07-19 --summary-json` | v4 schema 绑定 repository、commit/workflow SHA、run id/attempt、ref 与证据 hash；candidate 验证当前候选，head 只验证 `git archive HEAD`；本地环境和不同 run 的快照不能证明 remote/offsite |

Obsidian 只是在同一份 canonical Markdown 之上的可选本地 workbench。提交的 `indexes/obsidian/*.base` 是只读视图；正文、状态、owner、review_after、授权和 promotion 仍由 Hub registry 与 gate 决定。

| 层级 | 使用场景 | 稳定入口 | 边界 |
|---|---|---|---|
| 日常路径 | 人工新增、检索、索引计划和全仓检查 | `knowledge-new.sh`、`knowledge-search.sh`、`knowledge-index-plan.sh`、`knowledge-check.sh --dry-run --json --diagnostics` | new/capture 默认 dry-run；受控 `--apply` 只创建 draft/reviewing/personal，不伪造 source/owner/evidence |
| 健康首屏 | 总数、summary 缺口、review queue、stale review、changed-only 正文覆盖、reviewing triage、分轴状态、运行时维护建议和最近 product gate 摘要 | `knowledge-health-summary.sh --json` | 只读；`health_axes` 分开控制面、证据 freshness、内容治理和运行时卫生；默认按 full、quick 顺序选择日期、工作树签名和 24 小时 freshness 均匹配的 snapshot；`--gate-suite` 可固定层级，`--refresh-gate` 显式刷新 |
| 上下文预检 | 核定执行主体、独立检索范围、候选知识和归档资格 | `knowledge-provider.sh context --cwd "$PWD" --execution-project <id> --query "如何分析 core" --task-type debug --context-budget small --limit 3 --summary-json` | 默认只读，无 telemetry；显式 receipt-key 启用摘要缓存 |
| 人工复核 | 查看、校验和机械落地 AI 生成内容及外部资料待复核队列 | `knowledge-status.sh --json --review-queue-limit 10`、`knowledge-index-plan.sh --section review-queue --json`、`knowledge-index-plan.sh --section review-queue --queue-forms-jsonl`、`knowledge-index-plan.sh --section review-queue --validate-queue-forms <jsonl> --json`、`knowledge-review-queue-apply.sh --forms <jsonl> --dry-run\|--apply --json` | registry item 表单为 schema v2，并绑定当前整文件 SHA256；正文漂移会拒绝校验/apply，已接受记录漂移后重新入队。apply 只机械落地真实人工填写的 human review 字段，不生成 review 结论、不代签 owner gate、不提升 active、不写 memory、不修改源项目 |
| 生命周期复核 | 生成绑定 item/status/SHA/target 的真人确认包，并在明确真人决定后机械生成本地表单 | `knowledge-review-attest.sh packet`、`knowledge-review-attest.sh generate --apply` | 内容复核与执行授权分离；只写 `*.local.jsonl`，不创建 authorization、不改 registry、不执行 promotion/retire；active 禁止 delegated mode |
| owner gate | 导出、校验和审计人工 owner decision JSONL | `knowledge-owner-gates.sh --owner-inbox`、`--forms-jsonl`、`--validate-forms`、`--landing-plan`、`--landing-audit` | 不生成 owner decision，不代签 `reviewed_by`，不关闭 gate |
| 终态检查 | 区分平台技术通过、内容准备度、检索质量、运营恢复与真实 owner/evidence 成熟度 | `knowledge-final-gate.sh --summary-json --final-profile product` 默认 quick；完整取证用 `--json`，终态证明使用 `--regression-suite full`，声明成熟加 `--require-terminal` | 候选文档、目录存在或治理门禁通过不得冒充内容成熟 |
| 路径漂移 | 扫描旧归档路径在 Hub、Codex、memory、历史 session、runtime rules 和 Codex live/vendor/source skill 资产中的残留，并按 policy/provenance/runtime/memory-superseded/historical 分类 | `knowledge-path-audit.sh --scope hub --json`、`knowledge-path-audit.sh --scope runtime-rules --strict --json`、`knowledge-path-audit.sh --scope all --json` | 只读 report-only；不改写 memory、不改历史 session、不修改 `~/codex`、`/vsdata` 或源项目 |
| 高级写入计划 | artifact-ref、capture、summary backfill、promote、retire 和人工 review apply 等需要 reviewed manifest 的流程 | 对应工具默认 dry-run；`--apply` 只允许人工在证据齐备后触发 | 自动化不得删除、发布、提升 active、关闭 owner gate、写 memory 或改源项目 |

- `knowledge-check.sh`: 只读一致性门禁。
  - 用途：检查 registry JSON/JSONL、owner/project/topic/source 登记、核心索引、source policy、正文 frontmatter 镜像、冻结正文覆盖、artifact vault、template 必填字段、secret-pattern、owner-gated active 阻断、AI provenance 和中文 diagnostics。
  - 主要输出：JSON 中包含 `source_coverage_selection`、`source_coverage_health`、`source_check_health`、`frontmatter_status_health`、`body_coverage_health`、`artifact_vault_health` 和 `--diagnostics` 中文错误分组。
  - 不会做什么：`source_check_health` 不执行 registry check 命令；真实 source availability 由 `knowledge-source-check.sh --scope all` 独立执行。本工具不修复文件、不关闭 owner gate、不写 memory。
- `knowledge-check.sh`、`knowledge-status.sh` 和 `knowledge-final-gate.sh` 支持 `--as-of YYYY-MM-DD`；未传时可用环境变量 `KNOWLEDGE_TODAY=YYYY-MM-DD` 固定日期，再未设置时才使用系统日期。`--as-of` 用于复现 `review_after` 过期判断和终态证据，不生成 owner decision，不改变 registry。
- `knowledge-health-summary.sh`: 只读健康首屏入口。Health full contract 为 v3、summary projection 为 v2，顶层唯一综合状态为 `status`。它汇总 registry、canonical review queue、stale review_after、正文覆盖、reviewing triage、owner gate、运行时维护建议和最近 Product v5 snapshot；`health_axes` 分开控制面故障、证据快照 freshness、内容治理状态与运行时卫生。review queue 直接消费 `knowledge-index-plan` 单一派生视图，changed-only 扫描不会把 Git 删除项误报为 orphan，长列表只返回计数和有界样本。运行时建议只报告旧索引、过期终结事务和权限候选；默认事务保留 14 天且至少保留最新 20 个，任何删除仍要求维护命令显式 `--apply`。`--gate-suite auto` 默认优先读取新鲜 full、再回退 quick，`--gate-suite quick|full` 可固定层级；旧 schema snapshot 直接判 stale。默认不重新执行重门禁；`--refresh-gate` 在 auto 下刷新 quick，在显式层级下刷新所选 suite。它不生成 owner decision、不提升 active、不关闭 owner gate、不写 memory、不修改源项目。
- `knowledge-orphan-files.sh`: 只读正文覆盖检查入口。默认 `changed-only`；`--all --strict` 扫描全部长期 Markdown，并要求每个路径由 `registry/items.jsonl` 精确登记或由 `registry/body-coverage.json` 的 `unregistered-only` 冻结集合覆盖。精确登记优先且从集合 inventory 排除，因此通过 `knowledge-new.sh` / `knowledge-capture.sh` 事务新增的正文不会再触发集合 count/hash 漂移；未登记正文或未登记历史 corpus 的新增、删除、改名仍会 fail closed。集合不创建 active/owner decision/promotion。
- `knowledge-reviewing-triage.sh`: 只读 reviewing 周期 triage 入口。按 bucket、recommended_action、review_after 输出 reviewing 队列，帮助每周判断 keep-reviewing、evidence-needed、evidence-backed-validation-pending、owner-review-and-validation、owner-ready-validation-pending 或 archive-ready-check；不自动 archive、不提升 active、不代签 owner。
- registry item 和 registered source 的 stale `review_after` 只是 warning/status surface，不是阻断错误；日期格式非法和 `updated_at < created_at` 仍是错误。
- `knowledge-review-after.sh`: 只读复核排期报告入口。它按 `--as-of` 和 `--window-days` 输出 stale / near-due registry item、source 统计和 owner gate open 计数；near-due 只是人工提醒，不作为 blocking gate，不自动修改 `review_after`，不关闭 owner gate。
- `knowledge-source-check.sh`: 只读 source availability 报告入口。默认 `--scope all` 从 current 与 retired source registry 动态选择全部条目，并把唯一允许的 `rtk test -d/-f ...` 契约解析为进程内 `stat`，不启动 shell；路径必须留在 Hub 根目录，symlink、绝对路径、越界、控制字符或复合命令 fail-closed。`knowledge-check` 仍只做 `static-registry-only` 契约检查，status/final gate 另行消费本入口的真实 runtime 执行结果。
- `knowledge-source-control.sh`: source 主控目录生成和检查入口。它读取 `registry/sources.json` current source、`registry/retired-sources.jsonl` provenance ledger 与 latest source coverage closeout，为每个 current/retired source 生成或检查 `sources/<source_id>/README.md`、`inventory.jsonl`、`coverage.md`、`source-policy.md`；默认只输出计划，`--apply` 只写 Hub 本仓控制文件，不读取或复制 source 正文。
- `knowledge-provider.sh context`: Provider v4 上下文入口。默认 `--summary-json --context-budget small --limit 3`，摘要不超过 4096 bytes；已知主体用 `--execution-project <id>` 或 `--workspace <uri>`，跨项目检索用 `--retrieval-project <id>`。query 别名不改变执行主体。高风险结论回读原文，缓存只在显式 `--receipt-key` 下启用，失败标记 `cache.status=unavailable`。该入口不提供 telemetry 参数。
- `knowledge-workspace-discover.sh`: 本机 Git workspace 只读发现入口。默认扫描 `~` 与存在时的 `/vsdata/<user>`，也可重复传 `--scan-root`；只把 `.git/config` 中规范化后的 remote key 与 `registry/repositories.json` 精确匹配，输出未匹配 remote、重复副本、README、构建/测试/版本入口和 HEAD 指纹。默认 `--plan` 不写文件；`--apply` 只事务化刷新 `.gitignore` 已排除的 `local/workspaces.json`，绝对路径、alternate path 和动态 HEAD 不得复制到 tracked registry、Markdown、team export 或 owner evidence。发现源码只关闭“可定位”缺口，不等于 owner、构建、实机或发布验证完成。
- `knowledge-path-audit.sh`: 全局路径漂移只读审计入口。它扫描 retired 路径在 Hub、Codex、memory、历史 session、runtime rules 和 Codex live/vendor/source skill 资产中的命中，并分类为 `canonical-policy`、`provenance`、`detector-config`、`runtime-route-candidate`、`memory-superseded` 或 `historical-session`。`detector-config` 是扫描器自身规则常量，不计入 runtime residue。默认 `--scope hub`，运行时规则门禁用 `--scope runtime-rules --strict --json`，skill/agent 专项用 `--scope skills --json`，需要跨仓报告时用 `--scope all --max-matches <N> --json`；它只报告，不改写 memory、历史 session、`~/codex`、`/vsdata` 或源项目。
- `knowledge-pcr02-owner-targets.sh`: PCR02 owner-approved target materialization 入口。默认只读检查 4 个 Hub 内目标正文是否存在，并从 owner decision landing manifest 读取 source identity，不读取 retired origin 正文；`--apply` 才要求退役源文件仍可用并按已授权 worksheet 重新生成目标正文。不修改源项目、不写 memory、不提升 embedded standards。
- `knowledge-search.sh`: 只读检索入口。默认 JSON contract 为 v3；v3 把有界 `search_trace` 和阶段化 `timing` 固化为必需字段，外部 JSON consumer 必须按 `schema_version=3` 验证。默认语料只包含 `registry/items.jsonl` 中路径唯一、正文存在且未声明 `searchable=false` 的受治理文本；未登记正文、personal-local、artifact/index/registry/template/tool 等控制面文件不会回退混入结果，控制面正文只有显式 `searchable=true` 才可进入。它对中英文 query term 做带覆盖率的加权召回，支持中文 2/3-gram、短词、短语、别名和同义词，综合 canonical path、status、title/id/tags/summary/path/body 排序；JSON 的 `score`、`query_coverage`、`match_kind`、`why_selected` 解释排序。`search_trace` 记录 query terms、applied filters、candidate pool、有界 `excluded_by_filters[]` 和 retry query；只返回已登记条目的稳定元数据，不回显被过滤正文。它也支持 registry-backed 过滤：`--owner`、`--status`、`--kind`、`--domain`、`--source-id`；domain 使用完整路径段边界，`projects/p1` 不匹配 `projects/p10`。query 最多 4096 字符、结果最多 100 条、每类过滤最多 32 个值且单值最多 256 字符。`--source` 仍表示物理扫描源，`--source-id` 表示 registry item 的 `source.source_id`。本地倒排索引、token provenance 和 telemetry 都是可重建、非权威的 cache；任一写入因只读环境失败时安全回退扫描、重算 token 或标记 telemetry degraded，不改变命中语义和原有退出码。

  搜索索引使用 SQLite 原子事务增量刷新：普通受治理正文的小批增删改只更新受影响的 FTS 行；`registry/items.jsonl`、source registry 变化、索引 schema 升级、冷启动或一次变化超过 128 个文件时执行完整 rebuild。v8 的 freshness 签名只覆盖可检索 registry 正文及 registry/source 依赖，不再扫描无权威关系的全仓文件；每个已哈希文件保存 `size`、`mtime_ns`、OS 管理的 `ctime_ns`、`device`、`inode` 与 SHA-256。只有文件身份元组完全未变且 cache digest 合法时才复用 content hash，否则使用 nofollow 有界读取重新哈希并复核读后身份；cache 损坏、读中变化、重复 registry path、缺失/符号链接正文均 fail-closed。增量失败时由 rollback journal 回滚，不会用 stale index 换取低延迟。
  完整 rebuild 不重复倒排原始 `body`，正文仍完整保存在 `documents` 表并由等价的 index token 集合覆盖；同时使用确定性去重、frontmatter 单行 title 快路径和 source path 边界比较。`search-token-cache-v2.sqlite3` 以精确 token 输入 SHA-256 复用 token provenance，并为 `cache_key + token_text` 绑定完整性 digest；单项最多 4 MiB、待写与落盘 token 总量最多 128 MiB、最多 10000 项，文件权限为 `0600`。cache 行损坏、越界或不可写时只降级为确定性重算，不参与 freshness 或事实判定。所有查询统一使用最多 4096 个 FTS candidate，避免过滤前预排序截断合法结果；最终结果再按 canonical path 去重并校验 retrieval-result-v3 schema。
  查询生产者只依赖轻量 `retrieval_telemetry`，运营聚合 `metrics` 反向消费它，查询平面不再导入 artifact/lifecycle 平面。retrieval-result-v3 热路径校验仅接受当前 schema 已使用的受支持关键词；出现未知关键词立即 fail-closed，完整 Draft 2020-12 一致性由 schema 与 full engineering 门禁复核。公共 wrapper 的解释器缓存只减少 warm CLI 的第二次 Python 启动，不跳过首次版本/依赖验证，也不会进入 tracked 资产或恢复权威链。
- `knowledge-retrieval-benchmark.sh`: retrieval-result v3 先执行一次 index preparation，再测量 28 个语义 search cases、274 个动态 route、4-worker 并发和 10 倍 corpus；默认 warm P95 ≤ 500 ms、index preparation ≤ 5000 ms、并发 P95 ≤ 1000 ms。Hit Rate、MRR、nDCG@10、authority Recall@3 以及 unregistered/control/duplicate/compatibility/internal-endpoint 五类污染同时受硬门禁约束。known-answer case 的 `forbidden_ids` / `forbidden_paths` 证明旧 readiness 投影、冻结 archive 或控制面 provenance 不会重新泄漏到默认检索；JSON 保留准备状态、查询耗时和 scale/concurrency 结果，既不混淆 cold/warm，也不隐藏 schema-upgrade 成本。
- `knowledge-metrics.sh` / `knowledge-feedback.sh`: metrics v5 仍以 `knowledge-retrieval-interaction-v1` 聚合真实 usage/feedback，同时用 `knowledge-retrieval-performance-v2 + implementation_generation` 把 `warm_interactive`、`index_preparation` 和 report-only `end_to_end_observed` 分开统计；cold rebuild 不再污染 warm SLA，端到端等待仍完整披露。它还报告 reviewing 年龄、30 天 lifecycle flow、首次决定 lead time、90 天冷候选，以及 artifact 容量/增长。zero-hit 与显式 not-found 只按 query SHA 和绑定 interaction 汇总成有界改进队列，不保存 raw query、不自动改路由或正文。冷候选和 artifact 超预算也只报告，不自动删除。旧 performance contract 或旧实现代际的交互继续保留并计入 usage/provenance，但分别列入 `excluded_stale_contract_sample_count`、`excluded_stale_generation_sample_count`，不被静默按当前实现口径重解释。warm search/context 各不足 10 个当前代际样本时为 `pending`，不是无样本 `pass`；准备样本一旦出现必须满足 5000 ms 上限。feedback 必须绑定已发生的当前检索，同一 interaction 只能反馈一次。

  活动报告已硬切到独立的 `knowledge-activity.sh` v2，不再由 metrics CLI 承载。它只接受 `work-activity-item` v2 与 `activity-session-receipt` v2，并将事项状态与验证状态分离；个人归属必须由 `subject_id` 显式声明，Git author、Hub、memory 和目录名均不能推断身份。个人报告只读取 subject-bound v2 事项，项目/跨项目报告才读取 Hub registry 与登记 Git。默认输出到 `.tmp/activity/`，不自动归档、提交、推送、提升 active、写 memory 或外发。

  ```bash
  rtk bash ~/knowledge-hub/tools/knowledge-activity.sh report --period daily --scope personal --summary-json
  rtk bash ~/knowledge-hub/tools/knowledge-activity.sh report --period weekly --scope project --project-id codex --summary-json
  rtk bash ~/knowledge-hub/tools/knowledge-activity.sh coverage --period weekly --scope personal
  rtk bash ~/knowledge-hub/tools/knowledge-activity.sh record --title "完成某项工作" --project-id <project_id> --apply
  rtk bash ~/knowledge-hub/tools/knowledge-activity.sh capture --input /tmp/work-item-v2.json
  rtk bash ~/knowledge-hub/tools/knowledge-activity.sh capture --input /tmp/work-item-v2.json --apply
  rtk bash ~/knowledge-hub/tools/knowledge-activity.sh capture --input /tmp/activity-session-receipt-<session-id>.json --apply --json
  ```

  本地 SSOT 是忽略提交的 `local/activity-report.json` v2，模板见 `templates/activity-report-config-v2.json`。未显式传 `--scope` 时读取 `default_scope`；两者都缺失则返回 `needs-input`，不猜测个人或项目范围。日常优先在会话收尾时由 `session-wrap` 写入回执；未在 Codex 会话内完成的工作可用 `record --title "…" --project-id <id> --apply` 一行记录，无需手写 JSON。`record` 默认写入 `done + reported`，即“已完成待验证”；只有显式传 `--verification verified --evidence-ref <ref>` 才可记为已验证完成。`capture --input` 保留给已有 v2 JSON 的批量或集成场景。旧输入不会自动转换，也不会进入运行时事实包；报告会仅按文件数提示旧目录回执，且不会读取其内容。

  `capture` 会按 `kind` 自动识别单条 `work-activity-item` 或 `activity-session-receipt`。会话回执只有在本地 v2 配置启用、`receipt_persistence=true`、存在显式 `subject_id` 且回执主体一致时，才会原子写入 `.tmp/activity/receipts/YYYY-MM-DD/`；返回结果必须同时满足 `status=pass`、`applied=true` 且 `target` 位于该目录，才能声明已持久化。系统 `/tmp` 中的输入文件只是待校验载体，不是 Hub 持久化结果，也不应称为长期知识归档。

  `tools/systemd/knowledge-activity-daily.*` 与 `knowledge-activity-weekly.*` 是本地 user timer 源文件：日报每天 20:30，周报每周五 20:45，时区为 `Asia/Hong_Kong`。timer 仅获准写 `.tmp/activity/`，无网络能力；安装、启用和任何外部发送均需用户明确授权。
- `knowledge-status.sh`: 只读控制面 dashboard。
  - 用途：汇总 `knowledge-check`、registry/source policy、owner gate、人工复核队列、项目证据缺口、product source inventory、迁移残留和 `strict_blockers`。
  - 主要输出：`final_profile` 固定为 `product`；`owner_dispatch[]`、`next_open_queue[]` 和 recovery commands 只提供真人 owner 交接路径；普通 owner/evidence backlog 归类为 `needs-owner-review`，active/promotion 缺授权、不安全 source inventory、当前迁移残留、schema 或技术错误归类为 `needs-fix`。已归档且带 archive-only/tombstone/no-active-promotion 边界的历史材料只计入 sealed provenance，不进入 current。
  - `registry/retired-process-ledger.jsonl` 只作迁移过程封存清单，不参与 `review_queues`、owner gate、active promotion 或默认 source 恢复；需要审计 dry-run、applied、classification、source-inventory 历史时显式查看该文件。
  - 不会做什么：不生成或应用 owner decision；`--strict` 只作为 blocker dashboard；terminal gate 仍以 `knowledge-final-gate.sh --json` 为准。`strict_blockers[].commands` 可直接执行，`strict_blockers[].command_templates` 需要替换 `<owner-decisions.jsonl>`。
- `knowledge-final-gate.sh`: 唯一产品终态门禁。完整 JSON contract 为 v5，摘要 projection 为 v4；`maturity_axes` 独立报告 platform、content、project evidence、delivery、adoption。顶层只保留 `status` 与 `terminal`，旧总览字段和重复投影已删除。
  - quick gate 在 full engineering 快照新鲜、candidate signature 一致且 `coverage`、`coverage_report` 均通过时自动复用 pytest 证据；full gate 只有显式指定 `--reuse-engineering-evidence` 且 `full_regression` 同样通过时才复用完整工程证据。任一条件不满足就执行真实检查。输出 `engineering_evidence_reuse` 明示请求、`unit_test_policy`、freshness 和实际复用状态。
  - 用途：固定 `--final-profile product`，聚合 check、strict status、registry 全量 source runtime、共享单元测试、可选 full regression、diff、事务恢复、schema、检索 benchmark、动态项目结构与 route matrix、Obsidian Properties/MOC/Bases、team export 和 restore drill；hard check 全部来自本次运行或与当前候选签名绑定的新鲜快照。
  - 主要输出：顶层 `status`、`terminal`，以及 `maturity_axes`、`platform_status`、`content_readiness`、`retrieval_quality`、`operational_readiness`、`delivery_readiness`、typed `blockers` 和 `gap_map`。交付、远端、异地恢复和采用度布尔值位于对应轴或 detail section；owner/source/设备/release 缺口不会伪装成技术 pass，也不会被候选目录或 governance check 自动关闭。
  - 退出码：技术门禁失败为 1；默认模式在平台通过但 evidence pending 时为 0；`--require-terminal` 在未达到真实终态时为 2。工具不代签 owner、不提升 active、不写 memory、不修改源项目或远端。
- `knowledge-review-queue-apply.sh`: 人工复核队列表单应用入口。
  - 用途：读取 `knowledge-index-plan.sh --section review-queue --queue-forms-jsonl` 导出的 schema v2 JSONL；registry item 骨架携带当前整文件 `content_sha256`。真实人工填入 `human_reviewed_by`、`human_reviewed_at`、`review_basis` 和 `review_decision` 后，先 `--dry-run` 校验，再用 `--apply` 机械更新 `registry/items.jsonl`，并保存 `human_review_content_sha256`。正文 hash 不一致时 fail closed；后续漂移会重新入队。`archive-only/reject` 只记录普通复核结论，不改变 lifecycle status；真正退役仍需独立 attestation、授权与 `knowledge-retire.sh`。
  - 主要输出：`--json` 下包含 `status`、`read_only`、`applied`、`planned_update_count`、逐行 diagnostics 和 planned updates；`accept-as-review-record` 会写入 `review_status=human-reviewed-accepted`，`archive-only` / `reject` 只写普通复核结论且保持当前 lifecycle status，`needs-edits` / `defer` 会保留为后续复核 blocker。
  - 不会做什么：不生成人工结论、不代签 owner decision、不关闭 owner gate、不提升 active、不写 memory、不修改源项目；表单若包含 `owner`、`owner_decision`、`target_decision`、`reviewed_by` 或 `reviewed_at` 等 owner gate 字段会被拒绝。
- `knowledge-summary-backfill.sh`: archived `summary_zh` 回填入口。默认 dry-run，只从 Hub 内已存在正文、ref 文件或目录身份生成候选摘要；`--apply` 才机械更新 `registry/items.jsonl`、生成 report-only closeout manifest 并同步核心索引。它只补 archived 可读性字段，不改变 `status` / `promotion`，不生成 owner decision、不提升 active、不关闭 owner gate、不写 memory、不修改源项目。
- `knowledge-doctor.sh`: 只读维护辅助入口；运行 `knowledge-check --diagnostics`，可选输出 `--explain <item-id>`、搜索结果和 `--owner-gates <source-id>` 看板，不写文件。
- `knowledge-index-plan.sh`: 只读核心索引规划入口；输出由 registry 派生的 `by-owner`、`by-review-date`、`by-status`、`by-project`、`by-source`、`by-topic`、`by-decision`、`manifest`、`linking` 和 `review-queue` 恢复视图，不写文件。`--section <name> --json` 只返回所选 section，不再把全部索引附带进单项响应；`--summary-json` 只返回计数与健康投影。review queue 默认每页 50 条，显式 `--queue-limit 0` 才关闭分页；`pagination.next_command` 用于继续读取。`source_coverage_selection` 只在 all/source/manifest 响应中提供，用于追溯 latest closeout manifest；重复 `source_id` 会显式报错并保留第一行恢复视图。`--queue-forms-jsonl` 与 `--validate-queue-forms <jsonl> --json` 继续复用相同过滤和分页边界，前者输出 JSONL-only，后者只做 report-only 结构、正文 SHA256、人工字段、决定枚举和 guardrail 校验，不生成结论、不写 registry、不提升 active、不关闭 owner gate。manifest 的 `profile_health`、`summary_source`、`evidence_source` 只说明恢复质量；历史 unpaired 为 report-only。`--section linking` 只证明当前 registry/index/search 恢复链路，不读取源项目正文、不关闭 owner gate。
- `knowledge-owner-gates.sh`: 只读 owner gate 看板。它输出 unresolved worksheet、必填 owner 字段、active exposure、owner route 和 source identity；`source_identity_read_policy` 和 `observed_source_identity.source_body_read_for_hash=true` 表示为计算 hash 会只读读取 source 文件字节，但不复制正文、不写源项目、不生成 owner decision、不关闭 gate。`--summary` 会给出 owner 分布、`owner_dispatch[]` 和 `suggested_owner_packet`，后者把 summary、evidence-readiness、forms-jsonl、validate、landing-plan、landing-audit 排成 owner handoff 顺序。`--handoff-packet --json` 会一次性聚合 owner inbox、证据准备度、forms JSONL 骨架、checklist 和命令序列，适合交给 owner 离线填写；该入口必须带 `--json`，仍只读、不写 `.local.jsonl`、不生成 owner decision、不关闭 gate。`--forms-jsonl` 只打印骨架，`--validate-forms <jsonl>` 只校验人工回填，`--landing-plan` 和 `--landing-audit` 只输出 no-write 人工落地计划与审计。稳定消费面为 `form_validation.diagnostics[]`，逐字段提供 `code/field/actual/expected/action_zh`；`form_validation.errors[]` 仅是同一诊断的人类可读摘要，不作为新消费方契约。`owner_decision` 与 `target_decision` 会做保守成对一致性校验，并硬拒绝 `domains/projects` / `domains/personal` 旧入口，避免 `reference-only` / `no-migration` 和项目落地路径混用。两者都不生成 owner decision、不代签、不关闭 gate。`read_only_prefill_candidates` 只给候选值；正式 owner 字段仍需真实 owner 填写。`owner_route` 只来自 `registry/owner-routing.json`，不生成 owner decision，也不能替代 `reviewed_by`。
- 顶层 `status` 表示工具健康，不等于 owner gate 完成度；消费方应读取 `owner_review_status` / `owner_gate_status` 或 terminal `knowledge-final-gate.sh`。临时 owner 表单建议使用 `artifacts/manifests/*.local.jsonl`，该类文件已被 `.gitignore` 排除，不能登记为长期 manifest；非 `.local.jsonl` 的 owner decision JSONL 只有在真实 owner 签收并登记为 reviewed landing artifact 后才能长期保留，否则 `knowledge-check --diagnostics` 会给出 owner decision 草稿泄漏 warning。
- `knowledge-owner-gates.sh --owner-inbox`: 单屏 owner 待办入口。它按 worksheet 汇总 owner 中文问题、路由、字段分组、只读候选、owner-ready package、verification commands、forms-jsonl 和 validate/landing 模板，适合从 `owner_recovery.next_open_queue[]` 或 `owner_gates.owner_dispatch[].owner_inbox_json_command` 之后给真实 owner 使用；它不生成 owner decision，不写本地 JSONL，不关闭 gate。
- `knowledge-regression.sh`: 只读回归 fixture 入口；把仓库复制到 `/tmp`，只修改临时副本，用于验证 status bucket mismatch、partial owner resolution 等关键负向门禁。默认 `--suite full` 保持完整覆盖并使用最多 4 个 worker 并行执行，`KNOWLEDGE_REGRESSION_JOBS=<N>` 可覆盖 worker 数；`--suite quick` 只跑日常门禁 smoke 集且默认串行。默认每个场景后清理临时 fixture，内部异常会记录结构化失败细节；`--json` 模式输出 JSON，支持 `--as-of YYYY-MM-DD` / `KNOWLEDGE_TODAY` 固定日期敏感命令，并使用 `KNOWLEDGE_REGRESSION_MIN_TMP_FREE_BYTES` 做低空间预检。JSON 中的 `jobs`、`slowest_results[]` 和每条 result 的 `duration_sec` 用于定位 full suite 性能瓶颈，不参与 pass/fail 判定。
- `knowledge-regression-trend.sh`: 只读回归趋势摘要入口。用 `--from-json <file>` 从既有 regression JSON 生成 compact trend，或用 `--run --suite full --as-of YYYY-MM-DD` 重新运行并压缩输出；只保留 selected/result 数量、failed ids 和 top slowest，不保存大段 full JSON，不写 registry/index/manifest。
- `knowledge-inventory.sh`: 只读 source inventory；列出已登记 source 的 owner、路径、状态、复核日期和维护字段。
- `knowledge-artifact-ref-plan.sh`: 为非文本 source 文件生成 `knowledge-hub.immutable-artifact-ref.v1` manifest，记录 immutable URI、size、SHA256、owner、content-addressed identity 和 restore contract；不复制二进制、不上传外部对象。`--external-base-uri` 只允许无凭证、无 query/fragment 的 `https/s3/artifact` URI。
- `knowledge-new.sh`: 人工新增向导与候选创建入口。无完整 item 参数或 `--source` 时保持只读 guide；item 模式默认输出精确 transaction plan，`--apply` 事务化创建 Markdown、registry、lifecycle event 和索引，状态只允许 `draft/reviewing/personal`。未知 owner/source、缺 AI provenance 或路径越界会阻断，不会自动 active。
- `knowledge-capture.sh`: 事务化候选捕获入口；默认 dry-run，只创建 `draft` / `reviewing` / `personal`，不写 active。Codex 或其他 AI 生成的长期候选必须显式传 `--generated-by-ai --ai-role <role> --ai-model-or-tool <tool>`，使 registry 和正文 frontmatter 同步记录 provenance；稳定来源可成对传 `--source-type <type> --source-from <description>`，避免把临时文件路径当长期来源。capture 默认补中文可读性字段，但该标记不等于人工复核。
- `knowledge-review-attest.sh`: `packet` 只读输出精确 item、原状态、目标状态、正文 SHA256、确认码和真人回复模板；`generate` 在收到绑定这些字段的明确真人回复后，将决定机械写成忽略提交的 `artifacts/manifests/*.local.jsonl`。生成器不要求也不创建 execution authorization，不改 registry；`human-reviewed` 记录真人 reviewer，`human-directed-delegation` 强制使用 `<human>-via-codex-delegation`，且不能用于 active。
- `knowledge-promote.sh`: 默认 dry-run；`--apply` 必须同时提供独立有效的 `--authorization-id`、已确认的 `--forms`、当前正文 `--expected-sha256` 和预期原状态。表单可由真人手填，也可在明确真人决定后由 `knowledge-review-attest.sh` 机械生成；工具不生成 owner decision，active 只接受直接 `human-reviewed` attestation。
- `knowledge-retire.sh`: 默认 dry-run；受控 apply 使用同一 authorization/attestation/hash/expected-state 契约，支持 archived/superseded/rejected。执行授权只允许写操作，attestation 只证明真人决定；两者任一缺失都 blocked，事务失败会定向回滚，不删除正文。
- `knowledge-recovery-audit.sh`: 只读检查 transaction journal、applied paths、backup 和可恢复性；损坏 journal 必须计入 `attention_count` 并 fail closed。JSON 默认每页 50 条，`--limit 0` 才返回全部，`--summary-json` 不返回 rows；不会自动覆盖当前 worktree。

高风险写入、跨 source 写入、`apply-with-review`、promote 和 retire 必须走显式 reviewed manifest、dry-run、owner、rollback 和验证证据；Hub 本仓 L1/L2 维护和 `local-commit` 按 `AGENTS.md` / `README.md` 边界执行，必须门禁全绿且可回滚。无人值守自动化不得执行未授权高风险写入。成熟态不再提供 copy-first 迁移入口；外部资料吸收统一走 source 登记、artifact-ref、人工 review queue 和 promote/retire。

## `knowledge-check.sh` 参数语义

`knowledge-check.sh` 是全仓一致性门禁。终态不再兼容 `--project` 或 `--domain` 检查过滤；需要定位项目或领域时，先用 `knowledge-search.sh` / `knowledge-index-plan.sh` 收窄，再运行全仓 `knowledge-check.sh --dry-run --json --diagnostics`。

`--explain <item-id>` 是只读人工诊断入口，用于解释单个 registry item 的基础字段、正文路径是否存在、核心索引引用计数、`by-status` bucket 和维护提示。它不修复文件、不生成索引、不执行 `validation_refs`，适合在 `knowledge-check` 报缺失或重复引用后定位人工修改点。

`--diagnostics` 是只读错误分组入口，用于把原始 errors 按 registry、source、source-policy、template、manual-entry、item、index、secret 和 explain 等类别生成中文摘要与人工修复提示。它不隐藏原始错误、不改变退出码、不自动修复，适合在全仓门禁失败后快速判断先改哪个文件。

示例：

下面的 `pcr02-project-docs` 是 owner-gated source-id 示例；维护其他 source 时替换为对应 `source_id`。

按场景复制：

```bash
# 新增一条知识
rtk bash ~/knowledge-hub/tools/knowledge-new.sh --kind runbook --domain projects/xcrz-sigmastar-demo --owner <owner> --id <id> --path projects/xcrz-sigmastar-demo/current/runbooks/<file>.md --manual-source-reason field-debug --manual-validation-pending --manual-validation-reason "offline note awaiting rtk validation"
rtk bash ~/knowledge-hub/tools/knowledge-new.sh --kind runbook --domain projects/xcrz-sigmastar-demo --owner <owner> --id <id> --path projects/xcrz-sigmastar-demo/current/runbooks/<file>.md --item-source-id pcr02-project-docs --item-source-path runbooks/<file>.md
rtk bash ~/knowledge-hub/tools/knowledge-new.sh --kind debug-record --domain projects/xcrz-sigmastar-demo --owner <owner> --id <id> --path projects/xcrz-sigmastar-demo/archive/debug/<file>.md
rtk bash ~/knowledge-hub/tools/knowledge-new.sh --kind external-source-note --domain codex --owner <owner> --id <id> --path artifacts/manifests/<file>.md
rtk bash ~/knowledge-hub/tools/knowledge-new.sh --kind owner-decision-worksheet --domain projects/xcrz-sigmastar-demo --owner <owner> --id <id> --path artifacts/worksheets/<file>.md
rtk bash ~/knowledge-hub/tools/knowledge-new.sh --kind patent-disclosure --domain patents --owner <owner> --id <id> --path domains/patents/disclosures/<file>.md
rtk bash ~/knowledge-hub/tools/knowledge-index-plan.sh --section all
rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
rtk bash ~/knowledge-hub/tools/knowledge-search.sh "<id-or-keyword>" --json

# 新增一个 source
rtk bash ~/knowledge-hub/tools/knowledge-inventory.sh --markdown
rtk bash ~/knowledge-hub/tools/knowledge-new.sh --source --source-id <source-id> --source-path sources/<source-id> --role <role> --authority <authority> --write-policy <policy> --check "rtk test -d sources/<source-id>"
rtk bash ~/knowledge-hub/tools/knowledge-new.sh --source --source-id <source-id> --source-path sources/<source-id> --role <role> --authority <authority> --write-policy <policy> --no-check-reason "classify-first pending source coverage"
rtk bash ~/knowledge-hub/tools/knowledge-index-plan.sh --section source
rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
rtk bash ~/knowledge-hub/tools/knowledge-search.sh "<source-id>" --source knowledge-hub --json

# 归档一条历史记录
rtk bash ~/knowledge-hub/tools/knowledge-new.sh --kind project-archive --domain projects/<project> --owner <owner> --id <id> --path projects/<project>/archive/<file>.md
rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
rtk bash ~/knowledge-hub/tools/knowledge-search.sh "<archive-id-or-keyword>" --domain projects/<project> --kind project-archive --json

# 复核过期项
rtk bash ~/knowledge-hub/tools/knowledge-status.sh --json
rtk bash ~/knowledge-hub/tools/knowledge-index-plan.sh --section review-date
rtk bash ~/knowledge-hub/tools/knowledge-review-after.sh --as-of 2026-06-22 --window-days 30 --json
rtk bash ~/knowledge-hub/tools/knowledge-source-check.sh --scope all --as-of 2026-06-22 --json
rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics

# owner 签收一个 gate
rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --next-open --checklist --forms
rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --owner project-owner --summary
rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --owner project-owner --owner-inbox --json
rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --owner project-owner --forms-jsonl
rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --owner project-owner --evidence-readiness --json
rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --owner project-owner --validate-forms '<owner-decisions.jsonl>' --json
rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --owner project-owner --validate-forms '<owner-decisions.jsonl>' --landing-plan --json
rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --owner project-owner --validate-forms '<owner-decisions.jsonl>' --landing-audit --json
rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --forms-jsonl
rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --validate-forms '<owner-decisions.jsonl>' --json
rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --validate-forms '<owner-decisions.jsonl>' --landing-plan --json

# 跑一次终态检查
rtk git diff --check
rtk bash ~/knowledge-hub/tools/knowledge-final-gate.sh --json
rtk bash ~/knowledge-hub/tools/knowledge-final-gate.sh --json --final-profile product --regression-suite full
```

`owner-decision-worksheet` 只输出人工签核草稿建议，不代表 owner decision 已签收，也不能关闭 owner gate。

新增 source 时，`registry/sources.json` 的 `owner` 必须是 `registry/owners.json` 中已有的 source registry 维护责任人。`knowledge-new.sh --source` 要求 `--check` 或 `--no-check-reason` 二选一。优先使用稳定只读 `--check "rtk test -d sources/<source-id>"`；只有没有稳定检查入口时才使用 `--no-check-reason`，并在 source coverage 或相邻 manifest 写清 no-check reason。使用 `--check` 时，registry source object 和 source coverage JSONL row 草稿都应记录 `check`，不再补 JSON 形式的 `no_check_reason`。`knowledge-new.sh --source` 会输出 `role-aware 推荐终态` 和中文理由，但 copyable JSON 仍默认保守；推荐提示不替代 owner decision、不关闭 owner gate，人工必须按 `registry/schema.md`、coverage manifest 和 owner gate 状态确认后再替换。

个人笔记必须保持 `personal-local` visibility，落在 `notes/personal/`，不得进入团队 active index、团队导出或 owner gate。该边界由 registry、索引派生和产品终态门禁共同校验，不能通过 Obsidian Properties 或手工链接绕过。

Product v5 JSON 先看顶层 `status` 与 `terminal`，再看 `maturity_axes.platform/content/project_evidence/delivery/adoption`。`platform_status.hard_checks` 解释技术门禁，`delivery_readiness` 分开报告本地 committed HEAD、远端发布与异地恢复，`content_readiness.project_readiness` 分开报告 30 个规范项目的结构、source mapping 和真实 evidence-ready；这些字段是当前产品成熟度的唯一判定接口。

- `platform_status`：check、status、source runtime、共享测试、full regression、diff、事务恢复、链接、检索、项目结构、路由、导出、恢复、Obsidian 和 schema。
- `content_readiness`：registry 内容与 30 个规范项目的结构/owner/source/人工或实机/发布证据；候选目录存在只计 structural，不计 evidence-ready。
- `retrieval_quality`、`operational_readiness`：检索 benchmark、恢复、事务、导出和可运维性证据。
- `delivery_readiness`：本地 clean committed HEAD、远端 push 和独立环境 restore 三轴证据；candidate restore、本地提交或普通 CI checkout 不能互相替代。
- `owner_and_real_evidence`、`adoption`：真实 owner/验证缺口与当前 telemetry contract 下 30 天或 50 次调用、search/context 各至少 10 个性能样本及至少 10 条绑定真实 interaction 的显式反馈；历史样本保留但不混入当前 P95。
- `checks`、`blockers` 和 `gap_map`：本次门禁采信的实时命令结果及可执行阻断分类。

`knowledge-status.sh --strict` 是 blocker dashboard，`knowledge-final-gate.sh --final-profile product --json` 是唯一产品门禁；普通 owner/evidence backlog 使用 `needs-review`，技术/契约失败使用 `needs-fix`。

如果离线或工具不可用，不能把终态写成 `ok` / `pass`。在相邻维护记录中写 `manual_validation_pending: true`，并记录 owner、日期、当前 `cwd`、阻塞原因和 `required_followup: rtk git diff --check; rtk bash ~/knowledge-hub/tools/knowledge-final-gate.sh --json`；恢复后先补跑命令再更新证据。

失败恢复决策树以根 README 为准，本文件只补工具字段和边界。当前结论只以本次 Product v5 顶层 `status` 和 `terminal` 为准。

简要顺序：

1. 顶层 `status=needs-fix|blocked`：先看 `platform_status.hard_checks`，再按 `blockers[]` / `gap_map[]` 修复技术、契约或不可安全求值的问题。
2. 顶层 `status=needs-review`：平台可用但 owner、人工/实机/发布 evidence、交付、采用度或 review queue 未闭环；按对应 `maturity_axes`、`owner_and_real_evidence` 和 status 中的 owner/review queue 入口处理。
3. 顶层 `status=pass` 且 `terminal=false` 不应出现；schema、测试和门禁将该组合视为契约错误。
4. 顶层 `status=pass` 且 `terminal=true`：产品终态证据完整；发布声明仍应使用 `--regression-suite full --require-terminal` 复跑并保存验证证据。

`<owner-decisions.jsonl>` 是 owner 人工填写后的临时 JSONL 路径；工具只校验和生成 no-write landing plan，不代签、不关闭 gate。表单中的 `owner_route` 只说明抽象 decision owner role 的分派责任人、真实签收人待确认说明和升级路径；不能把 `routing_owner` 自动填成 `reviewed_by`。`target_decision` 不仅要在 `target_candidates` 内，还要和 `owner_decision` 成对兼容。`validate-forms` 可以合法只校验本批 JSONL 子集；批量处理时必须查看 `form_validation.coverage_status`、`missing_open_worksheet_ids`、`landing_scope` 和 `remaining_open_after_this_batch`，并在落地后复查 owner gate `open_count`。表单中的 `verification_cwd` 和 landing plan step 中的 `worksheet_verification_cwd` 是项目侧命令执行目录；相对命令必须在该目录下运行，而不是在 Knowledge Hub root 下运行。

搜索和恢复入口：

```bash
rtk git rev-parse --short HEAD
rtk git status --branch --short
rtk bash ~/knowledge-hub/tools/knowledge-search.sh "ASAN" --json --limit 10
rtk bash ~/knowledge-hub/tools/knowledge-search.sh "owner decision" --source knowledge-hub --json
rtk bash ~/knowledge-hub/tools/knowledge-search.sh "ASAN" --domain projects/xcrz-sigmastar-demo --kind project-current --status reviewing --json
rtk bash ~/knowledge-hub/tools/knowledge-search.sh "diag" --source-id pcr02-project-docs --json
rtk rg -n "PCR02|pcr02-project-docs|owner decision" ~/knowledge-hub/indexes/by-project.md ~/knowledge-hub/indexes/by-source.md ~/knowledge-hub/indexes/by-topic.md ~/knowledge-hub/indexes/by-decision.md ~/knowledge-hub/indexes/by-status.md
```

先用 git 命令固定 HEAD、分支和工作区状态，再运行 status/final gate 或结构化搜索，避免把旧 handoff、旧 manifest 或外部脏工作区当成当前事实。
结构化过滤只对能关联到 `registry/items.jsonl` 的本仓登记条目生效；使用 `--owner`、`--status`、`--kind`、`--domain` 或 `--source-id` 时，未登记普通文件会被排除，避免把外部原始文件误当治理条目。`knowledge-search.sh` 的当前 JSON 输出包含 `query`、`count`、`results` 字段，并在命中 registry item 时附带 `item_id/title/kind/domain/status/owner/source_id/review_after/tags`。

| 场景 | 最小落盘文件 | 关键验证 |
|---|---|---|
| 新增知识 | 唯一正文、`registry/items.jsonl`、核心索引；已登记 source 才同步 `indexes/by-source.md`，decision 类条目同步 `indexes/by-decision.md`，未知 source 不伪造 source id；人工来源、中文摘要、语言/术语、review/evidence、AI provenance 字段必须清楚；2026-06-21 及之后 `generated_by_ai=true` 的 item 必须带 `ai_role`、`ai_model_or_tool` 和 `ai_generated_at` | `knowledge-index-plan --section all`、`knowledge-check --diagnostics`、定向 `knowledge-search` |
| 新增 source | `registry/sources.json`、`indexes/by-source.md`、source coverage/source identity manifest | `knowledge-index-plan --section source`、`knowledge-check --diagnostics`、`knowledge-search "<source-id>" --source knowledge-hub --json` |
| 新增治理 manifest | `artifacts/manifests/*.md`、`artifacts/manifests/*.jsonl`、必要的 registry/index 登记 | `knowledge-index-plan --section manifest --json`、`knowledge-check --diagnostics`、`knowledge-regression --json` |
| 归档历史 | `projects/<project>/archive/...`、`registry/items.jsonl`、相关索引 | `knowledge-check --diagnostics`、`knowledge-search "<keyword>" --domain projects/<project> --kind project-archive --json` |
| owner 人工签收 | owner 人工填写的临时 JSONL；真正落地文件以 `--landing-plan` 输出为准 | `--validate-forms '<owner-decisions.jsonl>' --json`、`--landing-plan --json` |
| AI / 外部资料人工复核 | 人工填写后的临时 JSONL；长期只落地 human review 字段到 registry item | `knowledge-index-plan.sh --section review-queue --validate-queue-forms '<review-forms.jsonl>' --json`、`knowledge-review-queue-apply.sh --forms '<review-forms.jsonl>' --dry-run --json`、`knowledge-status.sh --strict --json` |
| 终态检查 | 通常不新增文件；需要保存证据时落相邻 manifest | `rtk git diff --check`、`knowledge-final-gate.sh --json --final-profile product`；高风险收口加 `--regression-suite full` |

```bash
rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --explain knowledge-hub-root
rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
rtk bash ~/knowledge-hub/tools/knowledge-status.sh
rtk bash ~/knowledge-hub/tools/knowledge-status.sh --strict
rtk bash ~/knowledge-hub/tools/knowledge-status.sh --strict
rtk bash ~/knowledge-hub/tools/knowledge-final-gate.sh --json
rtk bash ~/knowledge-hub/tools/knowledge-final-gate.sh --json --final-profile product
rtk bash ~/knowledge-hub/tools/knowledge-doctor.sh --id knowledge-hub-root
rtk bash ~/knowledge-hub/tools/knowledge-doctor.sh --id knowledge-hub-root --owner-gates pcr02-project-docs
rtk bash ~/knowledge-hub/tools/knowledge-index-plan.sh --section status
rtk bash ~/knowledge-hub/tools/knowledge-index-plan.sh --section source
rtk bash ~/knowledge-hub/tools/knowledge-index-plan.sh --section decision
rtk bash ~/knowledge-hub/tools/knowledge-index-plan.sh --section linking --json
rtk bash ~/knowledge-hub/tools/knowledge-inventory.sh --markdown
rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id pcr02-project-docs
rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --summary
rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --owner project-owner --summary
rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --owner project-owner --owner-inbox --json
rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --worksheet-id pcr02-owner-decision-worksheet-001 --checklist
rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --worksheet-id pcr02-owner-decision-worksheet-001 --forms
rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --worksheet-id pcr02-owner-decision-worksheet-001 --forms-jsonl
rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --next-open --checklist --forms
rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --forms
rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --forms-jsonl
rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --validate-forms '<owner-decisions.jsonl>'
rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --validate-forms '<owner-decisions.jsonl>' --landing-plan
rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --validate-forms '<owner-decisions.jsonl>' --landing-audit
rtk bash ~/knowledge-hub/tools/knowledge-new.sh --kind runbook --domain projects/xcrz-sigmastar-demo --owner <owner> --id <id> --path projects/xcrz-sigmastar-demo/current/runbooks/<file>.md
rtk bash ~/knowledge-hub/tools/knowledge-regression.sh --json
```

## 命令证据

命令证据应记录执行目录、完整 `rtk ...` 命令、日期、退出码、覆盖范围和中文结果摘要。写入计划工具默认先 dry-run；`--apply` 只能由人工在 reviewed manifest、owner、rollback policy、hash 校验和验证命令齐备后触发。

## 离线人工维护

工具不可用时，人工仍可按 `README.md`、`templates/`、`registry/schema.md` 和 `indexes/README.md` 写唯一正文、registry 草稿和索引 TODO。恢复后先运行：

```bash
rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
rtk bash ~/knowledge-hub/tools/knowledge-index-plan.sh --section linking --json
```

离线记录必须保留 `manual_validation_pending: true`、owner、review_after 和 required_followup；AI 恢复后只做校验、补索引和提示风险，不自动改 active、不关闭 owner gate、不写 memory。
# Provider Python 环境

公开工具通过 `tools/ci/python-runtime.sh` 选择具备依赖的解释器。能力探针和正式模块均使用 Python 隔离模式；只加载本仓 `tools` 包，每次使用独立字节码目录，不从工作目录、`PYTHONPATH` 或 user-site 导入代码。

如果系统解释器没有运行依赖，在本仓创建 `.tmp/provider-runtime/venv`，使用该环境的 `python -m pip install --require-hashes -r requirements-runtime.lock` 安装锁定依赖。随后从任意工作目录执行公开 wrapper。虚拟环境是本机依赖，不进入 Git、源码身份清单或发布数据。


## LAN Team MCP v1.3 — 小团队 Git 共享与归档

工程师客户端安装和现场验收细节见 [团队 MCP 客户端指南](team/CLIENTS.md)。

**工作流**：工程师用 Codex 或 Markdown 提交知识 PR，维护者按已有
Git/CI 复核并合入 master；同一 Ubuntu 服务器上的 MCP 服务只读发布
经验证的 Git SHA。Git/Markdown/Registry 是唯一知识权威。

团队 MCP 默认只发布三个工具：knowledge_search / knowledge_get /
knowledge_context。Draft、Personal、Archived、Superseded、Rejected、
控制目录和 archive 路径永不在团队查询中服务；Reviewing 明确标记为
provisional，Git PR 合并不等于 Active 认证。

**工程师日常归档（Ubuntu/Linux）**。先写脱敏、确认为允许公开的
safe-note.md 文件，在本仓工作区执行：

    bash tools/team/knowledge-submit.sh create --project pcr02-ssc305 --kind debug-record --source /tmp/safe-note.md --public-approved --create-pr

更新已有的 Reviewing 条目，必须先读取其完整旧正文 SHA256：

    bash tools/team/knowledge-submit.sh update --item-id <id> --expected-sha256 <64hex> --source /tmp/corrected-note.md --public-approved --create-pr

由 Codex 实际生成的候选应另外传入 --generated-by-ai，并保留证据中的
实测、推断和待验证边界；不得把 AI 产物标记为人工实测。

提交器通过工程师**自己的** git 和 gh 凭证工作，创建隔离 worktree，
复用 canonical capture/Index/Registry/事务内核并限制 PR 文件范围；
Active 与历史文档不能用普通 Update 改写。无远程认证时只允许
prepared-local，不得宣称 PR 已创建。两个 PR 更新同一条时须人工处理
CAS 冲突；禁止直接强推主线或机械合并索引。

**一键用户级安装（推荐）**：主线合并且安全审核通过后，在受信 Ubuntu 服务用户的 knowledge-hub checkout 中执行 `bash tools/team/install-user.sh`。它负责建立私有令牌、独立 Python venv、用户级 systemd 单元、首次 SHA 发布与定时更新；需预先确保 `/srv/knowledge-hub` 对该服务用户可写。SSH 断开后保持用户级服务需管理员确认 lingering。安装器不负责 Caddy/证书、GitHub 安全审批和真实客户端验收。下面保留详细手工安装步骤以供故障排查。

**一次性安装**：需要 Ubuntu 服务器上能运行 Git/Python 的服务用户，
且 /srv/knowledge-hub 可由该用户管理。先在本仓 checkout 操作：

    mkdir -p ~/.config/knowledge-hub ~/.config/systemd/user
    umask 077
    openssl rand -hex 32 > ~/.config/knowledge-hub/team-token
    python3 -m venv ~/.venvs/knowledge-hub
    ~/.venvs/knowledge-hub/bin/pip install --require-hashes -r requirements-runtime.lock
    cp tools/team/systemd/*.service tools/team/systemd/*.timer ~/.config/systemd/user/
    systemctl --user daemon-reload

将两个 service 中的 KH_PYTHON 改成上述 venv 的绝对路径，必要时调整
KH_INSTALL_ROOT 和 token 路径后，手工 bootstrap：

    KH_INSTALL_ROOT=/srv/knowledge-hub KH_PYTHON="$HOME/.venvs/knowledge-hub/bin/python" KH_TEAM_TOKEN_FILE="$HOME/.config/knowledge-hub/team-token" KH_SYSTEMCTL_MODE=user bash tools/team/deploy.sh
    systemctl --user enable --now knowledge-hub-team-mcp.service
    systemctl --user enable --now knowledge-hub-team-deploy.timer

部署从 GitHub master 获取 SHA，要求同一 SHA 的受信 Quality/Signed 成功，
候选独立构建和 Search/Get/Context HTTP smoke；通过后切换 current，
失败恢复上一版（单机允许短暂重启中断）。缓存仅在该 SHA 的 .cache 中
可写，Git 更新失败不影响已发布副本。成员都已有 SSH 时可用
ssh -L 3000:127.0.0.1:3000 user@server；其他情况参考
tools/team/Caddyfile.example，使用内网 HTTPS、共享 Bearer 和可信 CA。
无论使用 SSH 还是 HTTPS，本机 MCP 后端仍必须检验 Bearer。
禁止把 token 写到 Git 或绕过 TLS 校验。

**备份**：KH_BACKUP_DIR 指向独立挂载的 NAS/磁盘时运行
bash tools/team/backup.sh；必须验证 bundle 与临时隔离恢复，不能
把同机镜像视为已完成异地备份。

**必须现场验收的边界**：真实 Codex CLI/VS Code MCP 协议版本；
内网 TLS/Host/Origin/防火墙，主线实际分支规则；两名真实工程师的
Create/Update PR；实际 5–10 并发、磁盘/索引故障与回滚；备份恢复。
GitHub Public 仓库只接收允许互联网公开且适合发送至所用模型的知识。
这些未执行之前，不能宣称 LAN TEAM DEPLOYED/ADOPTED。

**Team MCP 当前事实消费边界**：`authority=verified` 只保留历史
Active + accepted + evidence-verified 身份，并不代表当前正文仍通过复核。
`team_search` 仅返回检索元数据，不能在未读取全部正文时证明当前版本哈希，
因此 `review_required=true`，`review_binding_state` 仅可为
`unbound` 或 `declared-unverified`。只有 `team_get` 对服务端
完整 Markdown bytes 计算 SHA256 并匹配 `human_review_content_sha256`，
且未超过 `review_after`，才返回 `review_required=false`；
`team_context.current` 使用同样的服务端正文证明，否则放入
`provisional` 并保留历史权威信息。AI 授权不生成 human 审核身份，
metadata claim 不等于内容未发生漂移。

## 全库知识复核及 AI 授权边界（2026-10-17）

用户明确授权 AI 辅助 review；这允许机器归类、逐条核对来源与生成修改建议，
不构成人工签收、Active 晋升、设备实测、外部真实性或 GitHub 安全审批授权。
复用原有 review-after / review-semantic / delegated-content-review 权限与状态合同。

按 2026-10-17 主线登记元数据：总计 709，Active 17 / Reviewing 398 /
Archived 288 / Draft 3 / Personal 2 / Rejected 1；Reviewing 中 391 条标记 AI 生成。
已过 review_after 的 Active 15、Reviewing 148、Archived 254、Draft 1。
这只证明元数据复核日期逾期，不证明内容错误或者语义审核已经执行。

在受信 Git checkout 中运行完整、只读、哈希绑定的机器盘点：

    python3 -m tools.codex_assets.knowledge_hub.corpus_review_cli --as-of 2026-10-17 --output .tmp/knowledge-hub/corpus-review-20261017.json

默认仅返回脱敏统计；加 --json 输出每条非私人知识的检查详情。该脚本逐条
核对 Registry 对应正文、frontmatter、证据和验证引用、本地重复候选、逾期、
历史 human/AI 复核证据的哈希及授权状态。报告标注 review-only，绝不写
canonical 正文或 Registry。私人内容只计数、隐藏身份和路径、不输出正文。
完整逐条报告仅存 ignored .tmp/knowledge-hub/ 下，不上传外部共享位置。
质量测试 test_real_repository_full_coverage 会读取仓库中全部登记条目，
确保审查覆盖不是限于首 10 条的抽样，亦不冒充独立语义审核。

2026-10-17 Git Tree 事实复核：709 条 registry 记录中有 2 条历史 archived
条目绑定的是目录（pcr02-engineering-archive-corpus、patent-disclosure-canonical-archive-corpus），
不是 Markdown 正文文件。机器报告将 archive-directory-observed 与 machine_checked
（正文成功读取）、machine_failed（真实缺失/无效）分开计数；目录存在且非空
只证明历史集合的目录身份，contents_verified=false，不声称逐文件哈希、语义、
owner 或专利法律资格已经验证。只有 archived / retired-source-provenance /
archive-corpus-materialized / promotion=none 的精确集合路径才可采用此分类；
缺失、空目录、非法路径或其它状态仍 fail-closed 为 P0。

处置顺序：P0 修复正文丢失、Frontmatter 不匹配、权限/秘密及 AI 复核无效证据；
P1 为逾期 Active 补足实证后由真实 owner 决定适用性；P2 将 Reviewing 分批做
AI 辅助语义复核和 Git 修改建议；P3 为 Archived 保留历史边界，仅作重复
关联建议，不自动删除。Git CI 全绿也不能证明外部实机或 owner 审核。

历史 ai_delegated_content_review 字段存在不等于用户授权证明有效：只有
request_proof、内容 SHA、授权对象均匹配才可按既有合同计入有效复核。
human_reviewed_by 但缺失当下正文哈希只能视为历史声明。用户本次授权
并不允许机器补写人工审核身份、虚构复核时间或自动晋升正式知识。
