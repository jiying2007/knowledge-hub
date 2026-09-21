---
title: Knowledge Hub current readiness model
summary_zh: 作为 Knowledge Hub 当前状态的人读首屏，只解释 repository closure、product/operational qualification、AI-first 维护边界和机器权威入口，不固化动态项目计数与历史快照。
tags:
- knowledge-hub
- readiness
- current
- ai-first
- human-facing
id: knowledge-hub-current-readiness-model-v1
kind: architecture
domain: governance
path: governance/product/current/readiness-model.md
scope: team-general
visibility: team-internal
status: reviewing
owner: leiwenjun
review_after: '2026-10-18'
review_status: manual-entry-pending-review
promotion: none
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: ChatGPT GPT-5.6 Sol
ai_generated_at: '2026-09-18'
aliases:
- Knowledge Hub current readiness
related:
- governance/product/validation/project-readiness.md
- registry/terminal-closure.json
---

# Knowledge Hub 当前 Readiness 模型

本页是**人读首屏**，不复制动态计数，不作为第二套机器状态源。

## 机器权威

- GitHub repository closure：`terminal_closure_cli`
- Product / operational maturity：`knowledge-final-gate.sh`
- Project evidence：`knowledge-project-readiness.sh`
- Review queue：`knowledge-index-plan.sh --section review-queue`
- Hosting fact：fresh `.cache/knowledge-hub/hosting-posture.json`

历史数字、性能快照、旧 blocker packet 保留在 validation/archive 中，只作 provenance。

## 当前分层

```text
repository closure
  ├─ canonical repository identity + observed visibility
  ├─ protected default branch
  ├─ engineering / restore / attestation
  └─ branch GC

product / operational qualification
  ├─ project real evidence
  ├─ provider ACL pilot
  ├─ production retrieval
  ├─ memory lifecycle
  └─ real adoption
```

两条验收线独立报告，不互相伪装。

## AI-first

普通维护默认由 AI 自动完成：

- health / search / drift / freshness；
- candidate discovery；
- deterministic reconciliation；
- review packet；
- governed PR preparation。

只把 owner 语义决定、正式发布/回滚、真实设备/生产/ACL 和 repository administration 升级给人。

## 当前外部硬边界

当前采用个人账号 + public repository 的托管策略。repository visibility 继续被 fresh hosting evidence 记录，但不再作为 GitHub terminal closure 的隐私硬门槛。

default branch protection 仍是独立 hosting requirement；terminal contract 关注 canonical repository identity、fresh hosted posture、protected `master`、工程质量、恢复、签名与 branch GC，而不是强制 private。

## 详细证据

需要审计历史与项目级缺口时再进入：

- `governance/product/validation/project-readiness.md`
- `indexes/project-readiness.md`
- Signed quality attestation artifacts / attestations

本页不得手工维护项目数量、ready 数量、调用量或性能数字。
