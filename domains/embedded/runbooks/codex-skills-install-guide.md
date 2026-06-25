---
title: Codex Skills 安装指南
doc_type: runbook
knowledge_type: process
maturity: verified
status: active
owner: team-core
created: 2026-05-16
last_updated: 2026-05-16
tags: [codex, skills, install]
related: [team-onboarding-guide.md, ../standards/knowledge-contribution-guide.md]
validation_refs: []
---

# Codex Skills 安装指南

## 1. 目标

将知识库内团队 skill 安装到个人 Codex skills 目录，便于在不同项目中复用。

## 2. 预检

```bash
export EMBEDDED_KNOWLEDGE_HOME="$HOME/embedded/knowledge"
test -d "$EMBEDDED_KNOWLEDGE_HOME"
```

## 3. 干跑

```bash
rtk bash "$EMBEDDED_KNOWLEDGE_HOME/scripts/install-codex-skills.sh" --dry-run
```

## 4. 安装

```bash
rtk bash "$EMBEDDED_KNOWLEDGE_HOME/scripts/install-codex-skills.sh"
```

如需覆盖已有软链接：

```bash
rtk bash "$EMBEDDED_KNOWLEDGE_HOME/scripts/install-codex-skills.sh" --force
```

## 5. 安装范围

1. `docs/.codex/skills/*`
2. `tools/.codex/skills/*`
