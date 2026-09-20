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
- automation PR 使用仓库 `GITHUB_TOKEN` 创建时，不假设 PR/push 会递归触发 CI；创建/复用 PR 后必须显式确认 exact-head Quality 已 active/success，否则由受信 execution workflow 主动 `workflow_dispatch` Quality。
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

- `source_refs`、`validation_refs`、`artifact_refs`：仅当 GitHub provider identity 已验证、候选唯一、mutation 为 append-only、现有 canonical prefix 完整保留，且变更不会改变 owner/status/readiness/evidence-ready 时，可进入 `autonomous-low-risk-ratchet`。validation 必须与同 item source revision 同 SHA；artifact 当前只允许 immutable `github-release-asset`，并要求 release tag 重新解析出的 exact commit SHA 与 source revision 一致。会过期的 Actions artifact 不进入长期 machine ratchet。
- `release_ref`：继续属于 `human-authorization`，机器只发现和准备 packet，不自动绑定。
- machine evidence candidate 先在非 canonical `.cache` 中 materialize，并绑定 registry before/after digest、proposal fingerprints 与 trusted provider run identity。
- canonical 落地只能通过 same-repository `automation/evidence-bind-*` PR；不得直接写 `master`。
- auto-merge 仅在真实 `master protected=true`、exact-head Quality SUCCESS、当前 master 未漂移、两文件 allowlist、append-only 语义 verifier、trusted origin run/attempt 和 origin artifact digest 全部重验通过后执行。
- auto-merge verifier 只执行当前 master 的可信代码，不 checkout 或执行 PR 代码；原始 provider artifact 只短期保留，长期只保留 bounded durable evidence identity/digest。

### Real external evidence ratchet

真实外部证据采用“真实观测人工/环境边界，验证后的 canonical ratchet 自动化”：

- observation/source artifact 必须来自真实 provider、真实生产评估、真实 memory lifecycle 或真实 adoption；不得由 AI 合成、mock、fixture、local-only 结果替代。
- observation source run 还必须属于当前仓库、运行在 `master`，event 仅允许 `workflow_dispatch` / `schedule`，并记录 exact workflow path/head SHA；PR 分支、临时分支或无法识别 workflow path 的 artifact 不得进入真实证据链。
- 仅满足 same-repo/master 仍不够：source workflow 必须显式注册在 `registry/ai-operations-policy.json#external_evidence.observation_source_workflow_allowlist` 对应 gap 下。当前列表为空表示尚未接入真实 observation producer，而不是让任意 master workflow 自报 `synthetic=false` 即获得生产证据资格。
- `external-pilot-evidence-producer` 只把显式选择的真实 observation 投影成 strict evidence；它不修改 canonical state。
- 真实环境输入合同由 schema catalog 唯一声明：`connector-provider-observation-v1`、`production-retrieval-observation-v1`、`production-memory-observation-v1`、`production-adoption-observation-v1`；producer 输入先过 JSON Schema，再过 Python 跨字段严格 validator。外部系统无需读取实现代码猜测 payload。
- strict producer 成功后，`external-evidence-intake` 可对 connector/retrieval/memory/adoption 四类 gap 自动从唯一 bounded artifact 推导 gap/run/artifact identity；manual master-only fallback 只保留给特殊非 producer 来源。
- manual fallback 只改变 source run/artifact 的选择方式，不降低 trust level：source 仍必须 same-repository、`master`、trusted event，并且 workflow path 必须已注册在该 gap 的 observation allowlist；未注册 workflow 不得借 manual intake 绕过 producer 根信任。
- external evidence trust chain 明确保留两层 provenance：`root_observation_provenance` 指向最初真实 observation source run/attempt/SHA/workflow/artifact；`source_provenance` 指向 intake 直接消费的 source（通常是 producer run）。自动 producer 路径必须用 `producer-receipt.json` 将两层绑定，manual fallback 则两者相同。
- root observation 必须 same-repository、`master`、trusted event，且 root head SHA 必须等于 strict evidence `source_revision`；connector 的 `adapter_commit` 也必须等于该 source revision。
- 跨 workflow trust artifact 全部采用 catalog contract：`external-evidence-source-provenance-v1`、`external-pilot-evidence-producer-receipt-v1`、`external-evidence-receipt-v1`、`external-evidence-intake-receipt-v1`、`external-evidence-intake-host-binding-v1`、`external-evidence-ratchet-proposal-v2`、`external-evidence-ratchet-verification-v1`；生成端与高权限 merge verifier 双重验证。
- strict validator 只有在 synthetic/mock/local-only 全部明确为 false，且 gap-specific contract 全部通过时，才产生 `closure_ready=true`。
- 所有 observation `observed_at` 必须是 UTC RFC3339；retrieval/memory/adoption 的 `window_end` 不得早于 `window_start`。validator receipt 的 `generated_at` 直接锚定 observation `observed_at`，同一输入重放不依赖 runner wall-clock。
- closure-ready intake 会自动进入 deterministic `external-evidence-ratchet` candidate；此时 canonical gap closure 属于 `autonomous-low-risk-ratchet`，不再要求人工重复确认同一机器事实。
- canonical 变更只能通过 same-repository `automation/external-gap-*` PR，且只修改 `registry/knowledge-platform-p5-p10.json` 与追加一条 durable evidence record。
- automation PR 显式触发 exact-head Quality；master protection 后续恢复时，由 `hosting-posture-reconcile` 统一对受限 `automation/evidence-bind-*` / `automation/external-gap-*` PR 重新触发 fresh Quality，不把旧 success 当作新保护状态下的 merge 证据，也不为每类 ratchet 保留独立 daily poll。
- `external-ratchet-automerge` 只 checkout current master 的可信 verifier，并用 origin closure/intake/binding receipts 重放 `build_external_gap_ratchet_candidate()`；PR registry 必须与 trusted replay byte-for-byte 一致。
- 只有 live repository 仍 private、`master protected=true`、same-repo/direct-child、two-file allowlist、origin run/attempt、durable digest 与 exact-head Quality 全部通过，才执行 expected-head squash merge。
- #20 仅在 canonical `connector-provider-pilot=closed` 后自动关闭；#21 仅在 retrieval/memory/adoption 三个 canonical gap 全部 closed 后自动关闭。#74/#96 的 owner/project evidence 边界不会被该机器链关闭。


### Owner/project qualification packet

Owner/project qualification 采用“机器聚合、真实 owner 决策”的边界：

- daily maintenance 从 canonical Product readiness 生成 deterministic `owner-qualification-packet`，只汇总 owner declaration、owner boundary 和 real-evidence pending 项，不生成 owner decision，也不写 canonical state。
- #74 只在 fresh current-master packet 中 `owner_declaration_pending=0` 且 `owner_boundary_pending=0` 时自动关闭；任一条件回归会自动 reopen。
- #96 只在 fresh current-master packet 的完整 owner/project qualification 为 PASS 时自动关闭；资格回归会自动 reopen。
- pending packet 按 fingerprint 去重写入 tracker，避免 daily sweep 重复刷屏。
- maintenance workflow 只有 schedule 或 `master` manual dispatch 可以进入 issue-write job，并在执行前验证 source revision 仍是 live current master；旧分支/stale run 不得改变 tracker 状态。
- 自动关闭 tracker 只表示 canonical 条件已满足，不代表 AI 代替 owner 签名，也不会制造 device/release/production evidence。

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
