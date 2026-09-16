# Operator Governed Binding Authorization Validation

P2.7 在 P2.6 review bundle 之后增加**外部 owner 授权的只读验证层**。它不会生成授权、不会代替人工 owner、不会写 canonical evidence，也不会因为授权验证通过就自动 apply。

## 设计边界

现有 owner-gate 已明确：真实 owner 必须人工提供 decision、`reviewed_by`、`reviewed_at` 等字段；routing owner 不能代替 `reviewed_by`；工具只允许 validate / plan，不能代签。现有 evidence contract 的显式授权形状也已经使用 `owner_ref`、`authorization_id`、`reason`。

P2.7 复用这些语义。每个 selected proposal 必须有且只有一条外部 authorization record，从而在一个 review bundle 跨项目或跨 owner 时仍保持责任边界独立。

## 调用

授权 JSON 必须由外部人工流程提供；Operator 不生成模板中的“批准值”。内部 CLI 只负责读取和验证：

```bash
tools/ci/python-runtime.sh -m tools.codex_assets.knowledge_hub.operator_provider_cli \
  --root . \
  --project agent-dev-kit \
  --field release_ref \
  --review-binding sha256:<proposal-fingerprint> \
  --validate-binding-authorization ./owner-binding-authorization.json \
  --json
```

`--validate-binding-authorization` 必须与 `--review-binding` 一起使用。CLI 会重新执行 P2.2 → P2.3 → P2.4 → P2.5 → P2.6，再用外部 JSON 验证 P2.7；因此授权文件不能绕开前置 discovery / qualification / proposal / exact patch plan / review bundle 链。

## 外部 authorization JSON

最小结构：

```json
{
  "schema_version": 1,
  "review_bundle_fingerprint": "sha256:<exact-p2.6-fingerprint>",
  "patch_plan_fingerprint": "sha256:<exact-p2.5-fingerprint>",
  "authorizations": [
    {
      "proposal_fingerprint": "sha256:<selected-proposal-fingerprint>",
      "authorization_id": "<externally-assigned-id>",
      "owner_ref": {"kind": "owner", "ref": "<canonical-owner-ref>"},
      "owner_decision": "approve-binding",
      "reviewed_by": "<real-human-owner>",
      "reviewed_at": "YYYY-MM-DD",
      "reason": "<owner rationale>"
    }
  ]
}
```

`owner_decision` 的 P2.7 专用枚举只有：

- `approve-binding`：该 owner 明确批准这一个 proposal 进入后续 governed apply 阶段；
- `reject-binding`：该 owner 明确拒绝这一个 proposal。

这两个值只表达 Operator evidence binding 的审批，不替代其它 owner-gate worksheet 的业务决策枚举。

## Fail-closed 验证

P2.7 会重新验证：

- P2.6 仍为 `needs-governed-authorization`，并保持 read-only / no-apply / no-auto-binding 边界；
- `review_bundle_fingerprint` 可由 P2.6 内容重新计算得到；
- authorization 文件中的 review bundle / patch plan fingerprint 与本次 P2.6 输出精确一致；
- 当前 `registry/items.jsonl` SHA256 仍等于 review bundle 的 `registry_before_sha256`；
- review bundle 中每个 project + item id + item path 仍唯一定位到 validation item；
- 当前 evidence contract 的 `owner_ref` 仍有效；
- 每个 selected proposal 恰好有一条 authorization，不能缺失、重复或夹带额外 proposal；
- authorization 的 `owner_ref` 与当前 canonical evidence contract 精确匹配；
- `authorization_id` 非空且不能在同一批 proposal 中复用；
- `reviewed_by` 非空、`reviewed_at` 为合法 `YYYY-MM-DD` 日期、`reason` 非空。

P2.7 **不会声称验证了真实人的外部身份**。输出固定保留 `reviewer_identity_provider_verified=false`；它只验证显式字段和 canonical owner boundary，没有身份提供商、企业目录或电子签名证明时不能提升为“身份已认证”。

## 输出状态

所有 proposal 都被 `approve-binding` 后，状态为 `ready-for-governed-apply`。只要存在一个有效 `reject-binding`，状态为 `rejected-by-governance`。

无论哪种状态，P2.7 始终保持：

- `read_only=true`；
- `canonical_write_performed=false`；
- `apply_enabled=false`；
- `authorization_input_generated=false`；
- `automatic_binding_enabled=false`；
- `automatic_execution_enabled=false`；
- status / owner / readiness mutation 均为 false。

验证成功会生成 deterministic `authorization_fingerprint`，绑定 exact P2.6 review bundle、P2.5 patch plan、registry before/after SHA256 与逐 proposal authorization rows。该 fingerprint 用于后续 P2.8 重新验证整条链，**不是数字签名，也不证明 `reviewed_by` 的真实身份**。

## 后续 governed apply

P2.7 本身不会调用 `RepositoryTransaction.apply()`，也不会创建或合并 evidence PR。后续 P2.8 若实现 governed apply，必须重新计算 P2.4/P2.5/P2.6、重新验证 P2.7 `authorization_fingerprint` 和 registry optimistic precondition，再只在受控 feature branch / PR 中产生 canonical registry diff；任何漂移都必须 fail-closed。
