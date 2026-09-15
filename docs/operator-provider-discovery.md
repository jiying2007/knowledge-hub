# Operator Provider Discovery

Operator Provider Discovery 是 P2.1 Discovery Queue 的受控 provider/caller 执行层。它只执行 Discovery Executor 已生成的 GitHub read-only query，不改变 canonical readiness，也不自动绑定 evidence。

## 使用

P2.2 不增加新的公共 `tools/knowledge-*.sh` wrapper，避免扩张 canonical command surface。显式调用内部 module CLI：

```bash
tools/ci/python-runtime.sh -m tools.codex_assets.knowledge_hub.operator_provider_cli --root . --json
```

限制到单个项目或 evidence field：

```bash
tools/ci/python-runtime.sh -m tools.codex_assets.knowledge_hub.operator_provider_cli --root . --project agent-dev-kit --field release_ref --json
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

Operator UI 仍保持本地 loopback GET-only，也不会因为打开页面而发起 provider 网络请求。P2.1 负责生成可审计 query plan；P2.2 内部 module CLI 显式执行 GitHub provider query；候选经后续治理验证后，才可能通过独立的 governed PR 写入 canonical evidence。