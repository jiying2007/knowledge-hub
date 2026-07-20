---
title: 知识库 CI 接入指南
doc_type: runbook
knowledge_type: process
maturity: verified
status: archived
searchable: false
owner: team-core
created: 2026-05-17
last_updated: 2026-05-17
tags: [ci, governance, automation]
related: [server-hook-setup-guide.md, team-onboarding-guide.md]
validation_refs: [../../.gitlab-ci.yml, ../../.gitea/workflows/knowledge-check.yml]
---

# 知识库 CI 接入指南

## 1. 目标

为支持不同 Git 平台，本仓同时提供 GitLab CI 与 Gitea Actions 配置模板。实际启用哪个由团队 Git 服务决定。

## 2. GitLab CI

入口文件：

```text
.gitlab-ci.yml
```

要求 runner 环境具备：

1. `rtk`
2. `python3`
3. `bash`
4. Git checkout 权限

## 3. Gitea Actions

入口文件：

```text
.gitea/workflows/knowledge-check.yml
```

要求 self-hosted runner 具备同样的 `rtk/python3/bash` 环境。

## 4. 推荐策略

1. 有 CI 平台时，CI 作为合并前可见反馈。
2. 有 Git 管理权限时，服务端 `pre-receive` 作为最终拒绝门禁。
3. 本地 `.githooks/pre-commit` 作为个人提前发现问题的入口。
