---
title: 嵌入式知识域首次使用指南
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

# 嵌入式知识域首次使用指南

## 1. 目标

统一团队成员使用 Knowledge Hub 的嵌入式团队级知识域，避免每个项目重复维护通用文档和工具。

## 2. 标准路径

终态入口：

```text
~/knowledge-hub/domains/embedded
```

常用入口：

- 团队规范：`domains/embedded/standards/`
- 排障 runbook：`domains/embedded/runbooks/`
- 平台和架构知识：`domains/embedded/platform/`、`domains/embedded/architecture/`
- 技能和工具说明：`domains/embedded/skills/`、`domains/embedded/tools/`

## 3. 验证

```bash
rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
rtk bash ~/knowledge-hub/tools/knowledge-search.sh "embedded" --json --limit 10
```

如需个人开发增强建议：

```text
domains/embedded/standards/personal-development-enhancements.md
domains/embedded/runbooks/dev-tooling-setup-guide.md
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
