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
- Discovery Queue：本地自动发现候选，远端生成精确 provider query；
- Machine Queue：先由机器检索候选或等待前置依赖的 action；
- Human / External Queue：必须由 owner、真实设备、生产环境或外部管理员处理的例外；
- evidence contract 的 missing/invalid fields；
- external closure open gaps；
- terminal closure（本机存在 fresh snapshot 时）；
- `knowledge-status` 给出的下一步动作。

JSON API 为 `GET /api/state`，健康检查为 `GET /healthz`。

## Action Queue 语义

Action Queue 不等于自动执行器。当前 `automatic_execution_enabled=false`，所有 action 都是只读分类：

- `machine-discovery`：机器应先检索已有 source、validation、artifact 或 release 候选；没有真实候选时保持 open；
- `machine-after-prerequisite`：前置 release/artifact 身份就绪后可由机器执行 restore/rollback drill；
- `dependency-gate`：等待其它真实项目/成员 evidence ready，不通过补字段绕过；
- `human-authorization`：必须由授权 owner/admin 明确决策；
- `real-world-evidence`：必须来自真实设备、生产评估、生命周期或真实 adoption；
- `external-environment`：必须在真实外部 provider、ACL、repository administration 等环境执行；
- `governance-review`：已有 evidence 无效或出现未知 contract 语义，需要先审计而不是覆盖。

`release_ref` 的默认策略是**先机器发现现有 release**；如果不存在，则升级为 `human-authorization`，UI 不会自动创建或发布版本。

## Discovery Executor

Discovery Executor 只处理 `machine-discovery` action，并保持只读：

- `source_refs`：从 `registry/project-routes.json`、`registry/repositories.json` 与 `registry/sources.json` 生成 canonical repository/source 候选；
- `validation_refs`：从 `registry/items.jsonl` 中项目 `validation_path` 下的已登记条目生成候选；
- `artifact_refs` / `release_ref`：只根据项目已登记 repository remote 生成精确 provider query；
- GitHub provider query 会区分 workflow、release/tag、release asset / Actions artifact；内部 Git 则生成对应只读查询意图；
- Hub core 本身不执行这些远端 query，transport 仍属于 provider adapter / caller。

所有本地 discovery candidate 都固定为：

- `candidate_only=true`；
- `eligible_for_binding=false`。

整个 discovery projection 还固定声明：

- `network_performed=false`；
- `canonical_write_performed=false`；
- `automatic_binding_enabled=false`。

因此“发现候选”不等于“证据有效”，也不会改变 readiness。远端 provider 找不到现有 release 时，后续应升级到显式发布授权，而不是由 UI 自动创建 release。

## 安全与治理边界

- 只绑定 loopback `127.0.0.1`；
- UI 只实现 GET；POST 返回 HTTP 405；
- 不引入数据库、浏览器端持久化或第二份 readiness 计算；
- project readiness 直接复用 product gate 的 canonical evaluator；
- external closure 直接复用 terminal closure evaluator；
- Action Queue 与 Discovery Queue 都只分类/发现，不执行 canonical 或外部写操作；
- owner approval、release、promote、retire、registry mutation 等写操作不由 UI 执行。

后续开放自动处理时，只允许从经过 provider 验证的 `machine-discovery` / 已满足前置的 `machine-after-prerequisite` 开始，并仍遵循 `Plan → Diff → Governed PR → CI → Merge`。owner/release/external administration 等高风险动作继续保留显式授权。
