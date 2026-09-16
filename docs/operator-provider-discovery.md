# Operator Provider Discovery

Operator Provider Discovery 是 P2.1 Discovery Queue 的受控 provider/caller 执行层。它只执行 Discovery Executor 已生成的 GitHub read-only query，不改变 canonical readiness，也不自动绑定 evidence。

## 使用

P2.2/P2.3/P2.4/P2.5 不增加新的公共 `tools/knowledge-*.sh` wrapper，避免扩张 canonical command surface。显式调用内部 module CLI：

```bash
tools/ci/python-runtime.sh -m tools.codex_assets.knowledge_hub.operator_provider_cli --root . --json
```

限制到单个项目或 evidence field：

```bash
tools/ci/python-runtime.sh -m tools.codex_assets.knowledge_hub.operator_provider_cli --root . --project agent-dev-kit --field release_ref --json
```

在同一次显式 provider discovery 后生成 P2.3 governed-review qualification projection：

```bash
tools/ci/python-runtime.sh -m tools.codex_assets.knowledge_hub.operator_provider_cli --root . --project agent-dev-kit --field release_ref --qualify --json
```

在 P2.3 qualification 之后生成 P2.4 proposal-only governed binding projection：

```bash
tools/ci/python-runtime.sh -m tools.codex_assets.knowledge_hub.operator_provider_cli --root . --project agent-dev-kit --field release_ref --propose --json
```

`--propose` 会在同一次显式调用中执行 P2.2 → P2.3 → P2.4，但只输出 proposal；它不会修改 `registry/items.jsonl`、项目 readiness Markdown、owner、evidence contract status 或其它 canonical state。

P2.5 在已经看到并明确选择某条 proposal fingerprint 后，生成 exact patch plan：

```bash
tools/ci/python-runtime.sh -m tools.codex_assets.knowledge_hub.operator_provider_cli \
  --root . \
  --project agent-dev-kit \
  --field release_ref \
  --plan-binding sha256:<proposal-fingerprint> \
  --json
```

`--plan-binding` 可以重复，但同一 canonical target field 一次只允许选择一个 proposal；不同 field 可以放在同一个 patch plan 中。选择 fingerprint 只是“指定要审阅哪条机器提案”，**不是 owner 授权，也不会触发 apply**。

支持的 field 为 `source_refs`、`validation_refs`、`artifact_refs`、`release_ref`。

公开仓库可以匿名读取。需要更高 GitHub API quota 或访问已授权私有仓库时，可通过 `GITHUB_TOKEN` 或 `GH_TOKEN` 提供调用凭据；token 不写入输出或 canonical registry。

## GitHub read-only allowlist

Provider runner 只接受 P2.1 生成的 `provider=github`、`executed=false`、`read_only=true` query，并只允许：

- `inspect-repository-source`：读取仓库默认分支并解析 exact commit SHA；
- `list-workflow-runs`：读取已完成且 `conclusion=success` 的 Actions run；
- `list-release-assets-and-actions-artifacts`：读取 release asset 与未过期 Actions artifact；
- `list-releases-and-tags`：读取 release/tag identity，并单独标记是否满足 immutable release policy。

网络层固定为 GitHub HTTPS API `api.github.com`，路径必须位于 `/repos/`，repository target 必须是精确 `owner/repository` key。单响应限制 2 MiB，单次 projection 最多执行 20 个 provider query，每个 query 最多输出 20 个候选。

## P2.3 governed-review qualification

P2.3 不执行新的网络请求，只消费 P2.2 provider execution projection，并把每个候选确定性分类为 `reviewable` 或 `rejected`。这里的 `review_eligible=true` 只表示候选达到进入治理审阅队列的最低机器检查门槛，**不表示** evidence contract 已满足，也不表示可以写入 canonical registry。

资格化检查至少包含：

- upstream projection 仍是 read-only、未写 canonical、未开启 automatic binding；
- 候选必须是 `provider_verified=true`、`candidate_only=true`、`eligible_for_binding=false`；
- `source_refs` 必须是 exact GitHub source revision，并携带 repository、commit SHA、`exact_identity=true`；
- `validation_refs` 必须是 successful workflow run，并携带 run id 与 exact head SHA；
- `artifact_refs` 必须是未过期 Actions artifact 或非 draft/non-prerelease Release asset，并携带 digest 与 provider identity；
- `release_ref` 只接受满足 immutable release policy 的 GitHub Release；普通 tag 不会通过 review floor。

拒绝结果输出稳定的 `reason_codes`，例如 `artifact-digest-missing`、`validation-head-sha-missing`、`immutable-release-policy-not-met`。projection 最多资格化 400 个候选，超出时 `truncated=true`，不会静默无限扩张。

无论 `review_eligible` 为何，P2.3 顶层与每个 row 都继续声明 `eligible_for_binding=false`、`automatic_binding_enabled=false`、`automatic_execution_enabled=false`、`canonical_write_performed=false`。

## P2.4 proposal-only governed binding

P2.4 只消费完整、未截断、无 upstream error 的 P2.3 qualification projection。它把 `reviewable` 候选映射成**可供 governed PR 审阅的确定性变更提案**，但本层仍不执行任何 canonical mutation。

Canonical target 不重新定义：P2.4 只允许定位到现有项目 validation slot 的单一 evidence contract，目标由以下条件共同确定：

- `registry/project-routes.json` 中项目必须只有一个 canonical route；
- route 的 `validation_path` 固定映射到 `<validation_path>/project-readiness.md`；
- `registry/items.jsonl` 中必须存在且只存在一个同 `project_id`、`readiness_slot=validation`、exact path 的 item；
- 目标字段必须已由该 contract 的现有 evidence profile 声明为 required field。

提案只允许两种 mutation intent：

- `source_refs`、`validation_refs`、`artifact_refs`：`append-reference`，只追加 `{kind, ref}`；
- `release_ref`：`set-if-empty`，只有当前值为 `null` 时才提出设置。

如果引用已经存在，结果为 `already-present`；如果单值字段已有不同引用、现有字段形状无效、canonical route/item 不唯一、field 不属于该 evidence profile，或该 field 已有显式授权的 `not_applicable`，结果都会 fail-closed 为 `blocked-conflict` / `unmappable`，不会生成覆盖动作。

每条 ready proposal 都包含 canonical target locator、当前值、建议值、mutation intent、完整 verified candidate snapshot 与 deterministic `sha256:` proposal fingerprint。canonical 建议值保持现有 `{kind, ref}` contract 形状；provider 的 digest、head SHA、immutable 等验证细节保留在 candidate snapshot，并被 proposal fingerprint 绑定。fingerprint 只用于审阅时识别同一提案，不是 evidence 签名，也不是授权。

P2.4 顶层和每条 row 始终保持：

- `read_only=true`、`network_performed=false`；
- `proposal_only=true`；
- `canonical_write_performed=false`；
- `automatic_binding_enabled=false`、`automatic_execution_enabled=false`；
- `eligible_for_binding=false`；
- `status_mutation_planned=false`、`owner_mutation_planned=false`、`readiness_mutation_planned=false`；
- `requires_governed_review=true`。

因此 `proposal_status=ready-for-governed-review` 只表示“机器已经形成可审阅的最小变更提案”，不表示该变更已获 owner 授权、不表示 evidence contract 可以声明 `ready`，也不表示 readiness/terminal closure 可以关闭。

## P2.5 governed patch plan

P2.5 只消费 P2.4 proposal projection 和**显式选中的 proposal fingerprint**。它不会直接写 registry，而是把选中提案重新绑定到当前 canonical `registry/items.jsonl`，验证没有 stale/drift 后，使用现有 `RepositoryTransaction.plan()` 生成 exact write plan。

P2.5 会重新验证：

- P2.4 顶层仍是 read-only / proposal-only / no automatic binding；
- proposal fingerprint 与 candidate snapshot fingerprint 都能重算一致；
- snapshot 仍是 `provider_verified=true`、`candidate_only=true`、`eligible_for_binding=false`，且 provider/kind/ref 与 proposal 一致；
- target 的 project、validation slot、item id/path、contract field、evidence profile 一致；
- canonical item 当前 field 仍与 proposal 的 `current_value` 完全一致；
- evidence contract 的 declared status 必须仍为 `pending`；P2.5 不允许在 plan 阶段把 readiness 自动提升为 ready；
- 同一 item + field 一次只能选择一个 proposal，避免多个 proposal 基于同一个旧 `current_value` 时破坏 optimistic precondition。

成功结果为 `status=needs-governed-pr`，并输出：

- `registry_before_sha256` / `registry_after_sha256`；
- 每个受影响 canonical item 的 before/after row fingerprint；
- `changed_fields` 与对应 selected proposal fingerprints；
- `RepositoryTransaction.plan()` 的 `expected_sha256`、before/after SHA256、changed count。

P2.5 始终声明：

- `read_only=true`；
- `canonical_write_performed=false`；
- `apply_enabled=false`；
- `selection_is_authorization=false`；
- `automatic_binding_enabled=false`、`automatic_execution_enabled=false`；
- `status_mutation_planned=false`、`owner_mutation_planned=false`、`readiness_mutation_planned=false`；
- `requires_governed_pr=true`。

因此 P2.5 的输出只是**可重复核对的 governed PR patch plan**。后续真正 canonical write 必须是单独阶段，要求重新核 optimistic SHA256、明确治理授权、生成真实 diff，并再次执行完整 evidence/readiness/terminal gates；P2.5 自身不会调用 `RepositoryTransaction.apply()`。

## Fail-closed 边界

Provider result 始终声明：

- `read_only=true`；
- `canonical_write_performed=false`；
- `automatic_binding_enabled=false`；
- 所有候选 `candidate_only=true`；
- 所有候选 `eligible_for_binding=false`。

因此 `provider_verified=true` 只表示候选确实来自本次只读 GitHub API 响应，不表示 evidence contract 已满足，更不表示 readiness 已关闭。

`release_ref` 只有 `immutable=true`、非 draft、非 prerelease 的 GitHub Release 才标记 `meets_immutable_release_policy=true`。普通 tag、可变 release、prerelease 都不会被升级成可接受 release evidence；没有合格 release 时仍应升级到显式 `human-authorization`，而不是自动创建 Release。

非 GitHub provider 当前保持 `unsupported-provider / executed=false`。内部 Git、Gitee 或其它 provider 后续如需执行，必须各自提供独立的只读 adapter，不允许把任意 URL 或通用网络 transport 下沉到 Hub core。

## 与 Operator UI 的关系

Operator UI 仍保持本地 loopback GET-only，也不会因为打开页面而发起 provider 网络请求。P2.1 负责生成可审计 query plan；P2.2 内部 module CLI 显式执行 GitHub provider query；P2.3 只把结果资格化为 governed-review candidates；P2.4 只生成 proposal-only governed binding projection；P2.5 只为显式选择的 proposal 生成 governed patch plan。任何 canonical evidence 写入仍必须经过后续独立 governed PR 与现有 evidence contract/readiness/terminal gates。
