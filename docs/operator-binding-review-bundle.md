# Operator Governed Binding Review Bundle

P2.6 在 P2.5 governed patch plan 之后增加一个**只读、可审阅、不可 apply** 的 review bundle。目标不是自动绑定 evidence，而是把“机器候选 → proposal → exact patch plan”中与人工审批相关的事实固化成一个确定性对象，避免审批人只能看到 SHA256 而看不到字段级变化。

## 使用

P2.6 不新增公共 `tools/knowledge-*.sh` wrapper，继续使用内部 module CLI：

```bash
tools/ci/python-runtime.sh -m tools.codex_assets.knowledge_hub.operator_provider_cli \
  --root . \
  --project agent-dev-kit \
  --field release_ref \
  --review-binding sha256:<proposal-fingerprint> \
  --json
```

`--review-binding` 可以对不同 canonical field 重复，但不能与 `--plan-binding` 同时使用。它会在一次显式调用中执行 P2.2 provider discovery → P2.3 qualification → P2.4 proposal → P2.5 exact patch plan → P2.6 review bundle。

## 重新验证而不是信任上游标签

P2.6 只接受 `status=needs-governed-pr` 的 P2.5 projection，并重新验证 P2.5 的安全边界：

- `read_only=true`、`canonical_write_performed=false`；
- `automatic_binding_enabled=false`、`automatic_execution_enabled=false`；
- `apply_enabled=false`、`selection_is_authorization=false`；
- status / owner / readiness mutation 均为 false；
- `registry/items.jsonl` 的 before/after SHA256 形状有效；
- transaction plan 仍是 read-only，且只计划一个 canonical registry write；
- selected proposal fingerprints 为唯一、排序后的 canonical 集合。

随后 P2.6 会使用同一份 P2.4 proposal 和 selected fingerprints **重新执行 P2.5**。只有重新计算得到的整个 patch-plan fingerprint 与输入完全一致时才继续。因此以下情况都会 fail-closed：

- `registry/items.jsonl` 在 plan 后发生变化；
- proposal 被删除、替换或 fingerprint 漂移；
- patch plan 的 before/after SHA、target、transaction plan 或 safety flags 被改写；
- 原本可 plan 的 evidence contract 不再是 pending 或 canonical field 已变化。

## Review bundle 内容

成功状态固定为 `needs-governed-authorization`。bundle 包含：

- selected proposal fingerprints；
- exact `patch_plan_fingerprint`；
- `registry_before_sha256` / `registry_after_sha256`；
- 每个 selected proposal 的 project、item id/path、field、mutation intent；
- `current_value`、`proposed_reference`、`proposed_value`；
- provider / source target；
- candidate snapshot fingerprint；
- deterministic `review_bundle_fingerprint`；
- 仅供人工审阅的 PR title/summary 建议。

Review rows 受 50 条 proposal 与 128 KiB 序列化体积预算约束，超限直接 blocked，不静默截断。

## 授权边界

P2.6 明确保持：

- `authorization_state=not-provided`；
- `requires_governed_authorization=true`；
- `selection_is_authorization=false`；
- `apply_enabled=false`；
- `canonical_write_performed=false`；
- `automatic_binding_enabled=false`；
- `automatic_execution_enabled=false`；
- `requires_governed_pr=true`。

因此 review bundle fingerprint 只是把“审阅的是哪一份 proposal + 哪一份 exact patch plan”绑定起来，**不是 owner 签名、不是授权凭据、不是 merge approval，也不是 terminal closure evidence**。

真正 canonical evidence write 仍必须进入独立阶段：接收明确治理授权，重新检查 bundle/plan/canonical precondition，在受控 feature branch/PR 中产生真实 registry diff，并再次执行现有 evidence/readiness/terminal gates。P2.6 自身不会调用 `RepositoryTransaction.apply()`，也不会创建或合并 PR。
