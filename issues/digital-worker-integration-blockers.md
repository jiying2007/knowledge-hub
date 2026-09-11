---
id: issue-digital-worker-integration-blockers
title: digital-worker integration blockers
kind: issue
domain: governance
scope: team-general
visibility: team-internal
status: reviewing
owner: leiwenjun
promotion: none
review_status: needs-owner-and-ci
summary_zh: digital-worker 作为 Knowledge Hub 消费方的接口候选已存在，但正式项目路由登记与当前 CI transport/public-wrapper 红灯尚未闭环；在此之前不得声明 Knowledge Hub integration ready。
tags:
- digital-worker
- integration
- knowledge-hub
- blocked
---

# digital-worker integration blockers

## 已完成候选接口

- `registry/integrations/digital-worker.json`
- `registry/compatibility-embedded-v0.json`（空 records；无真实证据不登记 qualified）

## 阻断 1：正式 Project Route 未登记

`knowledge-context` 当前依赖 `registry/projects.json`、`registry/repositories.json`、`registry/project-routes.json`。必须使用 Knowledge Hub 既有受治理事务/登记路径把 `digital-worker` 同时加入三者，并保留 alias/root/repository/route 一致性；不得只建目录或单改一个 registry 冒充已可路由。

完成证据：

- `knowledge-context.sh --cwd <digital-worker> --query ...` 明确解析到 digital-worker project/repository route；
- path/orphan/check/final gate 均通过；
- 未产生第二份 source truth。

## 阻断 2：当前 Quality Matrix CI transport/public-wrapper gate 红

在 `master@8541d5f0a40263536179ea44764bca2baa063731` 的 Quality Matrix run `34615620047` 中，多 Python 版本一致在 `tools/ci/rtk` repository wrapper transport/public-entrypoint allowlist 失败，job 已进入 runner，不是本条目把失败改写为 PASS 的场景。

在 CI transport 恢复并得到 fresh green 前：

- `registry/integrations/digital-worker.json` 保持 candidate；
- digital-worker Gate K/Adapter 对 Provider unavailable/unresolved route 必须 BLOCKED/NEEDS_REVIEW；
- 不提升 Knowledge Hub 为 digital-worker 默认 Production Provider。

## Done when

1. CI transport/public wrapper gate fresh green；
2. digital-worker 三 registry governed route 完整登记；
3. context/evidence-pack/action-check/proposal-route 真实 smoke 有证据；
4. 至少一个 digital-worker real Pilot 使用 Hub context，并至少一个 Knowledge Harvest candidate 进入 proposal route + owner review；
5. owner 决定是否把 candidate integration 提升为 active/default 或继续 not-frozen。
