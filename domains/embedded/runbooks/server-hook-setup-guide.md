---
title: 知识库服务端 Hook 部署指南
doc_type: runbook
knowledge_type: process
maturity: verified
status: archived
searchable: false
owner: team-core
created: 2026-05-17
last_updated: 2026-05-17
tags: [git, hook, governance]
related: [team-onboarding-guide.md, ../standards/knowledge-contribution-guide.md]
validation_refs: [../../scripts/pre-receive-knowledge.sh]
---

# 知识库服务端 Hook 部署指南

## 1. 目标

本地 pre-commit 依赖每个成员主动启用，不能作为唯一合入门禁。服务端 `pre-receive` hook 用于在远程仓库拒绝未通过 `scripts/check-all.sh` 的推送。

## 2. 前置条件

1. Git 服务器可以访问 `rtk`。
2. `knowledge.git` 为 bare repository。
3. 管理员有权限写入远程仓库的 `hooks/` 目录。

## 3. 部署步骤

在 Git 服务器上执行：

```bash
cd /path/to/embedded/knowledge.git
cp /path/to/checkout/scripts/pre-receive-knowledge.sh hooks/pre-receive
chmod +x hooks/pre-receive
```

若服务器只有 bare 仓库，可从本仓导出脚本：

```bash
git --git-dir=/path/to/embedded/knowledge.git show main:scripts/pre-receive-knowledge.sh > hooks/pre-receive
chmod +x hooks/pre-receive
```

## 4. 验证方式

1. 推送一个只改文档且通过门禁的分支，确认允许进入远程。
2. 临时制造一个 schema 错误文档，推送测试分支，确认远程拒绝。
3. 删除测试分支并恢复工作区。

## 5. 运维注意

- Hook 运行的是被推送 commit 的树，不依赖推送者本机状态。
- 如果服务器没有 `rtk`，先不要启用强拒绝；应先修复服务器环境。
- Hook 日志应保留在 Git 服务日志或系统 journal，便于排查误拒绝。
