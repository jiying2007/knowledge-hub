# Hosting Posture 与 GitHub 闭环分层

## 为什么单独建模

Git SHA 不变化时，repository visibility、default branch、protection/ruleset 等 hosting fact 仍可能变化。因此：

```text
source revision freshness != hosting posture freshness
```

Signed/terminal 证据必须捕获当次 hosted posture，而不能只依赖仓库内声明。

## 两层目标

### repository-closure-baseline

回答“GitHub repository 工程闭环是否成立”：

- canonical repository identity 与 fresh hosted metadata 一致；
- repository visibility（public/private）被记录但不作为 terminal 隐私硬门槛；
- default branch 为 `master`；
- default branch protected；
- source / CI / restore / attestation / branch GC 满足 terminal contract。

### production-hardened

回答“是否达到长期团队生产治理标准”：

- baseline 全部满足；
- PR-based change；
- required status checks；
- conversation resolution；
- force-push protection；
- branch deletion protection；
- organization/team ownership 与 break-glass 流程。

Production hardening 可以比 repository closure 更严格，但不得反向混淆两个结论。

## Freshness 与 reconciliation

Hosted workflow 应保存同一次观测中的：

- repository identity；
- visibility/private；
- default branch；
- default branch protection；
- rulesets capability diagnosis（`available` / `plan-gated` / `integration-forbidden` / `unavailable`），仅用于解释平台能力，不替代 `protected=true`；
- source revision；
- observed_at；
- workflow run identity。

如果 live hosting fact 与 canonical registry / open tracker 不一致，标记为 `fact-drift`，优先生成确定性 ratchet proposal，而不是要求人工先发现漂移。
