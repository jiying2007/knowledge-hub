# 自动化策略（AI-first Operations Policy）

## 目标

Knowledge Hub 默认按 **AI-first / machine-verifiable-first** 运行：能由机器确定性证明、可重放、可回滚且不涉及语义授权的工作，不要求人工逐项操作。人工只保留无法由机器替代的责任边界。

机器权威策略：`registry/ai-operations-policy.json`。

## 默认执行模型

```text
read/discover/reconcile
        ↓ autonomous
deterministic candidate/proposal
        ↓ autonomous
governed branch / PR
        ↓ autonomous creation allowed
exact-head CI
        ↓
merge
        ├─ protected branch + exact-head checks 已建立：仅受限 machine ratchet 可自动 merge
        └─ protection 未建立：自动 merge fail-closed

owner / semantic / release / device / production / ACL / repository administration
        ↓
human or real-world boundary
```

## 无需人工逐项确认

以下工作默认允许机器自动执行：

- 只读扫描、检索、健康检查、freshness、drift detection。
- source / validation / artifact / release 的只读候选发现。
- schema、contract、tracker、hosting posture 的确定性一致性检查。
- 基于精确 source revision 和 immutable provider identity 的候选生成。
- 不覆盖已有语义、不改变 owner decision 的低风险 ratchet candidate。
- 创建 governed branch / PR；不得直接写 `master`。
- CI、恢复演练、SBOM、attestation、证据摘要和 bounded ledger 生成。

## 仍必须保留人工或真实环境

以下边界不得因为“AI-first”而自动伪造：

- owner decision、content review 的真实语义结论。
- `reviewing -> active` 等改变知识权威等级的 promotion。
- 正式发布批准、生产回滚授权、不可逆删除。
- 真实设备/HIL/高温/EMI/生产验证。
- production-derived retrieval expectation 与真实用户 feedback。
- provider ACL transition、Workspace/Shared Drive 等真实外部权限变化。
- GitHub plan、branch protection、organization/team permission 等外部 administration。

AI 可以准备 packet、发现候选、校验证据和生成最小 PR，但不得代签上述决定。

## 自动 canonical 变更边界

机器可验证的 canonical 变更允许自动形成 PR，但必须同时满足：

1. exact source revision；
2. deterministic diff；
3. 只修改声明的 machine-verifiable field；
4. 不生成 owner decision；
5. 不提升 active；
6. 不伪造 real-world evidence；
7. 不直接写 `master`；
8. exact-head CI 可重放。

在默认分支仍未 protected 时，自动 merge 保持关闭。启用 protected branch 后，只有 `autonomous-low-risk-ratchet` 类 PR 在 exact-head Quality 成功、same-repository、当前 master 未漂移、文件与语义 allowlist 全部通过时才允许自动 squash merge；该高权限 workflow 不 checkout 或执行 PR 代码。

### Provider evidence machine ratchet

Provider evidence 进一步按字段拆分责任边界：

- `source_refs`、`validation_refs`、`artifact_refs`：仅当 GitHub provider identity 已验证、候选唯一、mutation 为 append-only、现有 canonical prefix 完整保留，且变更不会改变 owner/status/readiness/evidence-ready 时，可进入 `autonomous-low-risk-ratchet`。
- `release_ref`：继续属于 `human-authorization`，机器只发现和准备 packet，不自动绑定。
- machine evidence candidate 先在非 canonical `.cache` 中 materialize，并绑定 registry before/after digest、proposal fingerprints 与 trusted provider run identity。
- canonical 落地只能通过 same-repository `automation/evidence-bind-*` PR；不得直接写 `master`。
- auto-merge 仅在真实 `master protected=true`、exact-head Quality SUCCESS、当前 master 未漂移、两文件 allowlist、append-only 语义 verifier、trusted origin run/attempt 和 origin artifact digest 全部重验通过后执行。
- auto-merge verifier 只执行当前 master 的可信代码，不 checkout 或执行 PR 代码；原始 provider artifact 只短期保留，长期只保留 bounded durable evidence identity/digest。

## Operator UI 边界

Operator UI 继续保持 projection / diagnosis / routing 面：

- loopback；
- GET-only；
- 不持有高权限 write token；
- 不直接执行 apply / rollback / release / protection administration。

自动化执行属于独立 governed execution plane，不把浏览器 UI 变成第二套高权限控制面。

## 禁止事项

- direct-to-master canonical write。
- 从 routing owner 推断 final owner approval。
- 用 synthetic evidence 关闭真实设备、生产、adoption 或 ACL gap。
- 因为希望得到 terminal=true 而降低安全门禁。
- 自动覆盖已有单值 evidence 或 owner decision。
- 把机器 PR 的创建行为解释为 owner 签收。
