---
title: 知识库仓库结构规范
doc_type: standard
knowledge_type: guideline
maturity: verified
status: active
owner: team-core
created: 2026-05-17
last_updated: 2026-05-17
tags: [repository, structure, governance]
related: [knowledge-contribution-guide.md, ../governance/README.md, agent-skill-engineering-baseline.md]
validation_refs: [../../scripts/check-repository-shape.sh]
---

# 知识库仓库结构规范

## 1. 目标

保持团队知识库边界清晰、目录稳定、内容可复用，避免业务项目生命周期文档和一次性材料回流到团队仓库。

## 2. 顶层目录

允许的顶层入口：

| 路径 | 职责 |
| --- | --- |
| `docs/` | 技术知识、规范、runbook、模板、治理脚本 |
| `tools/` | 跨项目复用调试、诊断、归档工具 |
| `scripts/` | 仓库门禁、安装、发布、脚手架入口 |
| `profiles/` | 项目环境变量 profile 示例 |
| `.githooks/` | 本地 Git hook |
| `.gitea/`、`.github/`、`.gitlab/` | Git 平台集成模板 |

顶层新增目录必须先更新本规范与 `scripts/check-repository-shape.sh`。

## 3. docs 子目录

允许的长期目录：

| 路径 | 职责 |
| --- | --- |
| `docs/architecture/` | 平台级架构、能力矩阵 |
| `docs/archive/` | 归档索引、manifest、历史资料引用 |
| `docs/governance/` | 文档治理脚本、测试、迁移记录 |
| `docs/runbooks/` | 可执行操作手册、排障流程 |
| `docs/standards/` | 长期稳定规范 |
| `docs/templates/` | 文档、AGENT、SKILL 模板 |
| `docs/.codex/skills/` | 文档治理相关 Codex skill |

## 4. 禁止目录

以下目录不允许出现在知识库中：

- `docs/project/`
- `docs/specs/`
- `docs/plans/`
- `docs/reports/`
- `docs/superpowers/`

原因：这些目录承载项目生命周期、阶段设计和执行记录，应留在业务项目仓库或归档系统，不应进入团队通用知识库。

## 5. 迁移记录

当前迁移事实源只有：

```text
docs/governance/knowledge-repo-migration-map.csv
```

旧项目内部迁移表不得回流到本仓。

## 6. 验证

```bash
rtk bash scripts/check-repository-shape.sh
rtk bash scripts/check-all.sh
```
