# Operator Provider Discovery

Operator Provider Discovery 是 P2.1 Discovery Queue 的受控 provider/caller 执行层。它只执行 Discovery Executor 已生成的 GitHub read-only query，不改变 canonical readiness，也不自动绑定 evidence。

## 使用

P2.2/P2.3 不增加新的公共 `tools/knowledge-*.sh` wrapper，避免扩张 canonical command surface。显式调用内部 module CLI：

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

无论 `review_eligible` 为何，P2.3 顶层与每个 row 都继续声明 `eligible_for_binding=false`、`automatic_binding_enabled=false`、`automatic_execution_enabled=false`、`canonical_write_performed=false`。后续如要真正绑定 evidence，必须经过独立 governed review/PR 与既有 evidence contract 验证，不能由本层直接升级。

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

Operator UI 仍保持本地 loopback GET-only，也不会因为打开页面而发起 provider 网络请求。P2.1 负责生成可审计 query plan；P2.2 内部 module CLI 显式执行 GitHub provider query；P2.3 只把结果资格化为 governed-review candidates。任何候选仍必须经过后续独立治理验证，才可能通过 governed PR 写入 canonical evidence。