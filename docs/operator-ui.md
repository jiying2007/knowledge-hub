# Knowledge Hub Operator UI

Operator UI 是 Knowledge Hub 的本地只读人工控制面。它的目标是减少“找命令、翻 JSON、手工拼接下一步”的工作，而不是建立第二套事实源或绕开治理门禁。

## 启动

```bash
tools/knowledge-status.sh --ui
```

默认只监听 `127.0.0.1:8765`。需要换端口时：

```bash
tools/knowledge-status.sh --ui --port 8876
```

只读取 operator projection、不启动 HTTP server：

```bash
tools/knowledge-status.sh --ui --json
```

## 页面内容

单屏页面直接投影现有 canonical 状态：

- control-plane status；
- 项目 structural/source/owner/evidence 覆盖；
- Governed Binding Lifecycle：可选地观测 P2.4–P2.11 已保存 JSON；
- Discovery Queue：本地自动发现候选，远端生成精确 provider query；
- Machine Queue：先由机器检索候选或等待前置依赖的 action；
- Human / External Queue：必须由 owner、真实设备、生产环境或外部管理员处理的例外；
- evidence contract 的 missing/invalid fields；
- external closure open gaps；
- terminal closure（本机存在 fresh snapshot 时）；
- `knowledge-status` 给出的下一步动作。

JSON API 为 `GET /api/state`，健康检查为 `GET /healthz`。

## Governed Binding Lifecycle

P2.4–P2.11 的 CLI 输出由调用方决定是否保存，目前**没有 canonical lifecycle result 目录**。因此 Operator UI 不扫描 `.tmp`、不猜文件名，也不会把某个 transaction journal 自动解释成 owner decision。

需要观测 lifecycle 时，由 operator 在启动时显式传入已保存 JSON：

```bash
tools/knowledge-status.sh --ui \
  --binding-proposal /path/to/proposal.json \
  --binding-patch-plan /path/to/patch-plan.json \
  --binding-review-bundle /path/to/review-bundle.json \
  --binding-authorization-result /path/to/authorization-result.json \
  --binding-apply-result /path/to/apply-result.json \
  --binding-rollback-result /path/to/rollback-result.json
```

也可以只传其中一个或若干阶段。完全不传时：

- `binding_lifecycle.status=not-observed`；
- 不会产生 lifecycle action；
- `not-observed` **不表示失败，也不表示生命周期尚未完成**，只表示当前 Operator 进程没有拿到显式观测输入。

观测阶段与 P2.x 对应如下：

- `proposal`：P2.4 governed evidence binding proposal；
- `patch_plan`：P2.5 deterministic patch plan；
- `review_bundle`：P2.6 governed review bundle；
- `authorization`：P2.7 authorization validation result；
- `apply`：P2.8 governed apply result；
- `apply_receipt`：由 UI 调用现有 P2.9 verifier 现场重算，不从独立文件读取；
- `rollback`：P2.10 rollback validation/execution result；
- `rollback_receipt`：由 UI 调用现有 P2.11 verifier 现场重算，不从独立文件读取。

### 信任边界

保存的 proposal / patch plan / review bundle / authorization result 只标记为 `observed-output-not-revalidated`。UI 会检查 projection/schema/read-only/automatic-execution 等基本边界，并在同时提供相邻阶段时核 fingerprint、selection、registry before/after SHA 等链身份，但不会把“文件存在”升级为授权证明。

对 `apply.status=applied`：

- UI 调用 `build_governed_apply_receipt()`；
- 重新核 transaction journal、before backup、authorization-bound transaction id 与当前 registry SHA；
- receipt 状态直接进入 lifecycle projection。

对 `rollback.status=rolled-back`：

- UI 调用 `build_governed_rollback_receipt()`；
- 重新核 apply→rollback lifecycle、独立 rollback journal/backup、恢复 SHA 与 scope；
- 完成 rollback 后不会生成自动 reapply action。

若同时提供的 JSON 来自不同操作，selection/fingerprint/SHA 链不一致时，projection 固定进入 `observation-error`，下一责任分类为 `governance-review`。UI 不尝试“自动挑一个看起来最新的文件”来修复链。

### 生命周期责任进入现有 Action Queue

Lifecycle 不建立第二套 queue。`next_execution_class` 只允许复用现有七类责任模型：

- proposal 等待显式选择/审计时使用 `governance-review`；
- patch plan 已观测、下一步可构建确定性 review bundle 时使用 `machine-after-prerequisite`；
- review bundle 等待真实 owner decision 时使用 `human-authorization`；
- authorization 已 ready、等待显式 apply CLI 三重确认时仍使用 `human-authorization`；
- receipt drift、contract mismatch 或 observation error 使用 `governance-review`；
- `verified-current-post-apply-state` 与 `verified-current-post-rollback-state` 本身不会强制制造 rollback/reapply action。

Lifecycle action 与其它 Operator action 一样固定 `automatic_execution_enabled=false`。页面没有 apply、rollback、authorize 或 reapply 按钮。

## Action Queue 语义

Action Queue 不等于浏览器自动执行器。UI 中 `automatic_execution_enabled=false` 始终表示“页面本身不执行动作”。AI-first 后，machine 类 action 可由独立受控 execution workflow 自动处理；每条 action 通过 `automation_eligible` / `execution_plane` 区分是否可交给外部 AI 自动化：

- `machine-discovery`：机器应先检索已有 source、validation、artifact 或 release 候选；没有真实候选时保持 open；
- `machine-after-prerequisite`：前置身份/计划就绪后可执行受限机器步骤；
- `dependency-gate`：等待其它真实项目/成员 evidence ready，不通过补字段绕过；
- `human-authorization`：必须由授权 owner/admin 明确决策；
- `real-world-evidence`：必须来自真实设备、生产评估、生命周期或真实 adoption；
- `external-environment`：必须在真实外部 provider、ACL、repository administration 等环境执行；
- `governance-review`：已有 evidence 无效或出现未知 contract 语义，需要先审计而不是覆盖。

`release_ref` 的默认策略是**先机器发现现有 release**；如果不存在，则升级为 `human-authorization`，UI 不会自动创建或发布版本。

## Default branch protection

Terminal closure 现在要求默认分支 `master` 在真实 GitHub 托管环境中处于 protected 状态。该事实不由仓库内配置自报，而是复用 Signed workflow 已有的 `.cache/knowledge-hub/remote-branch-inventory.json` fresh remote snapshot：同一次 GitHub `/branches` 读取既记录 branch inventory，也记录默认分支的 `protected` 布尔值。

这条 gate 与 branch GC 独立：

- branch GC 只判断 retirement / implementation branch residue；
- default branch protection 只判断 `master` 是否存在、是否观测到 protection 字段、以及 `protected=true`；
- 两者共用同一 repository/source revision 身份绑定，避免把其它仓库或旧 run 的快照当作当前事实；
- `protected=false` 会使 terminal check `default_branch_protection` 进入 `needs-review`；
- protection 字段缺失、默认分支缺失、repository/revision 不匹配会 fail-closed 为 `blocked`。

Operator UI 不会尝试开启 branch protection。未保护默认分支只会进入现有 Human / External Queue：

- `execution_class=external-environment`；
- `owner=repository-admin`；
- `automatic_execution_enabled=false`。

因此开启保护仍必须由具备 repository administration 权限的人或外部受控流程完成；本仓代码只负责采集、验证和阻塞 terminal overclaim。

## Discovery Executor

Discovery Executor 只处理 `machine-discovery` action，并保持只读：

当 `registry/project-routes.json`、`registry/repositories.json`、`registry/sources.json` 的行形状、身份、route refs 或 remote key 不符合预期，或机器 action 列表损坏时，Discovery 必须返回 `status=unavailable`、空候选并保留脱敏错误类别；不可因丢弃损坏行而将不存在的候选误报为真实零。Operator UI 的 `Candidates found` / `Provider needed` 也显示 `unavailable`，不将无观测当作无工作。该失败不执行网络查询、不写入 Registry、不授权绑定或发布。

- `source_refs`：从 `registry/project-routes.json`、`registry/repositories.json` 与 `registry/sources.json` 生成 canonical repository/source 候选；
- `validation_refs`：从 `registry/items.jsonl` 中项目 `validation_path` 下的已登记条目生成候选；
- `artifact_refs` / `release_ref`：只根据项目已登记 repository remote 生成精确 provider query；
- GitHub provider query 会区分 workflow、release/tag、release asset / Actions artifact；内部 Git 则生成对应只读查询意图；
- Hub core 本身不执行这些远端 query，transport 仍属于 provider adapter / caller。

所有本地 discovery candidate 都固定为：

- `candidate_only=true`；
- `eligible_for_binding=false`。

整个 UI discovery projection 还固定声明：

- `network_performed=false`；
- `canonical_write_performed=false`；
- `automatic_binding_enabled=false`。

独立 `.github/workflows/ai-provider-discovery.yml` 可在受信 `master` 上执行 P2.2→P2.5，并把唯一候选进一步分成 machine route 与 human route。`source_refs` / `validation_refs` / `artifact_refs` 只有在 provider verified、append-only、不会改变 owner/status/readiness/evidence-ready 时才可形成 governed `automation/evidence-bind-*` PR；`release_ref` 继续进入 `human-authorization`。UI 本身仍不执行这些写动作，页面继续保持 GET-only。

因此“发现候选”不等于“证据有效”，也不会改变 readiness。远端 provider 找不到现有 release 时，后续应升级到显式发布授权，而不是由 UI 自动创建 release。

## 安全与治理边界

- 只绑定 loopback `127.0.0.1`，并校验精确端口的 loopback `Host`/`Origin`；
- 最多同时接收 8 个连接，闲置 HTTP 连接超时 15 秒；
- 使用进程内 3 秒 single-flight 状态快照，HTML/JSON 共用同一计算结果；快照过期必须重新评估，失败时不回退到旧结果；
- `/healthz` 和未知路径不运行昂贵的 status/readiness/terminal evaluator，页面标记状态生成时间；
- 内部异常不通过 HTTP 返回本地文件路径或运行细节，CLI/CI 仍承担完整诊断；
- UI 只实现 GET；POST 返回 HTTP 405；
- lifecycle 文件只能由启动参数显式提供，浏览器不能上传或选择文件；
- 不扫描 `.tmp` transaction 目录来推断业务授权；
- 不引入数据库、浏览器端持久化或第二份 readiness 计算；
- project readiness 直接复用 product gate 的 canonical evaluator；
- external closure 与 default-branch protection 直接复用 terminal closure evaluator；
- Action Queue、Discovery Queue 与 Lifecycle projection 都不会执行 canonical 或外部写操作；
- owner approval、release、promote、retire、apply、rollback、reapply、branch-protection administration、registry mutation 等写操作不由 UI 执行。

AI-first 自动处理已从 provider 验证的 `machine-discovery` / 已满足前置的受限机器步骤开始，并仍遵循 `Plan → Diff → Governed PR → CI → Merge`。owner/release/external administration/apply/rollback 等高风险动作继续保留显式授权与确认；master 未 protected 前自动 merge 保持关闭。

## 不可用状态与自治责任可见性

Operator UI 的计数是只读投影，**不是独立验收**。如果 external evaluator 返回
`unavailable` / `blocked` / `needs-fix` 等非可信状态，页面显示
`unavailable` 而不显示虚假的 0 个外部缺口；Status 不可用且没有下一步动作时，
也不会提示“没有下一步动作”。修复 evaluator 或输入后再查看新快照。

Action Queue 的 `Automation eligible` 列直接显示已有 action 合同中的
`automation_eligible`：只有严格布尔 `true` 才标为 `yes`；缺失或其它值一律
`no`。这仅代表符合交给**独立受控执行工作流**的条件，不意味着 UI 执行了动作、
候选通过验收、或产生 owner/设备/生产/发布授权。浏览器仍严格只读。


## 状态一致性防误判

Operator UI 的 External open 数字只在 `status`、`open_count` 与实际
`open_gaps` 列表互相一致时显示；`pass` 必须对应零项，
`needs-review` 必须确有开放列表。异常计数、布尔计数、缺失列表或
`needs-review + 0` 一律显示 `unavailable`，而不是误报“没有缺口”。

终态卡片只有在同一个 canonical evaluator 投影同时给出
`status=pass`、严格布尔 `terminal=true`、`blockers=[]` 时
才显示 `true`。文本 `"true"/"false"`、状态与布尔相冲突、
blockers 非列表或遗漏，均不可作为通过依据。JSON API 使用相同的严格
布尔投影。这只修复 **显示和状态投影** 的防误判边界，
不重新判定 Product/Repository Terminal，也不更改 Owner、外部证据或审批权限。
