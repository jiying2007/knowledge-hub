---
title: Knowledge Hub current readiness model
summary_zh: Knowledge Hub 当前状态的人读入口，只解释状态模型、权威来源和当前外部边界，不固化动态项目计数与历史性能快照。
tags:
- knowledge-hub
- readiness
- current
id: knowledge-hub-current-readiness-model
kind: architecture
domain: governance
path: governance/product/current/readiness-model.md
scope: team-general
visibility: team-internal
status: active
owner: leiwenjun
review_after: '2026-12-18'
review_status: active-control-plane-accepted
promotion: none
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
  ├─ private hosting
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

当前 repository 已观测为 private；canonical private-boundary 仍必须通过 governed ratchet 绑定 durable hosted evidence。

default branch protection 仍是独立 hosting requirement；如果当前 GitHub plan 不支持 private repository protection，应升级 hosting capability，而不是降低 terminal contract。

## 详细证据

需要审计历史与项目级缺口时再进入：

- `governance/product/validation/project-readiness.md`
- `indexes/project-readiness.md`
- Signed quality attestation artifacts / attestations

本页不得手工维护项目数量、ready 数量、调用量或性能数字。
