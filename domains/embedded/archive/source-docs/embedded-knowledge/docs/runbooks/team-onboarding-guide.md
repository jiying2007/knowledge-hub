---
title: 团队知识库首次使用指南
doc_type: runbook
knowledge_type: process
maturity: verified
status: active
owner: team-core
created: 2026-05-16
last_updated: 2026-05-16
tags: [onboarding, knowledge, git]
related: [codex-skills-install-guide.md, ../standards/knowledge-contribution-guide.md]
validation_refs: []
---

# 团队知识库首次使用指南

## 1. 目标

统一团队成员本机知识库路径，避免每个项目重复维护通用文档和工具。

## 2. 标准路径

每个用户本机统一使用：

```text
~/embedded/knowledge
```

初始化：

```bash
mkdir -p ~/embedded
git clone ssh://git@192.168.1.4:10022/embedded/knowledge.git ~/embedded/knowledge
export EMBEDDED_KNOWLEDGE_HOME="$HOME/embedded/knowledge"
```

建议把环境变量写入个人 shell 配置：

```bash
export EMBEDDED_KNOWLEDGE_HOME="$HOME/embedded/knowledge"
```

## 3. 验证

```bash
cd "$EMBEDDED_KNOWLEDGE_HOME"
rtk bash scripts/check-all.sh
```

如需启用本地提交前检查：

```bash
git config core.hooksPath .githooks
```

如需加载项目 profile：

```bash
source profiles/template.env
```

如需个人开发增强建议：

```text
docs/standards/personal-development-enhancements.md
docs/runbooks/dev-tooling-setup-guide.md
```

## 4. 使用方式

1. 项目内只保留强绑定文档。
2. 通用规范、排障手册、公共工具、Codex skill 统一引用 `$EMBEDDED_KNOWLEDGE_HOME`。
3. 不把 `knowledge/` 目录提交到业务项目仓。

## 5. 推荐本机增强

```bash
rtk bash scripts/check-shell-style.sh
rtk bash scripts/check-secrets.sh
rtk bash scripts/check-tools.sh
```

`shellcheck` 与 `shfmt` 缺失时默认只提示跳过，不阻塞入门。

安装推荐工具：

```bash
rtk bash scripts/bootstrap-dev-tools.sh --install
```
