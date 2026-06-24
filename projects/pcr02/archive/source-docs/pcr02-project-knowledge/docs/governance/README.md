---
title: Docs 治理入口
doc_type: index
knowledge_type: process
maturity: draft
status: active
owner: team-core
created: 2026-05-12
last_updated: 2026-05-12
tags: [docs, governance, gate]
related: [../README.md]
validation_refs: []
---

# Docs 治理入口

## 强制 Frontmatter 字段

每篇文档必须包含以下字段：

- `title`
- `doc_type`
- `knowledge_type`
- `maturity`
- `status`
- `owner`
- `created`
- `last_updated`

建议统一补充以下字段用于追溯：

- `tags`
- `related`
- `validation_refs`

## 枚举约束

- `doc_type`: `standard|architecture|runbook|spec|plan|report|archive|index`
- `knowledge_type`: `model|decision|guideline|pitfall|process`
- `maturity`: `draft|verified|proven|historical`
- `status`: `active|archived|deprecated`

## 目录语义（与总规范一致）

- `docs/architecture/`：平台级架构、能力矩阵。
- `docs/archive/`：归档索引与 manifest。
- `docs/runbooks/`：可执行操作手册与排障流程。
- `docs/standards/`：长期稳定规范。
- `docs/templates/`：模板来源，新增文档必须优先复用模板。
- `docs/governance/`：治理规则、校验脚本、门禁入口。

禁止目录见 `docs/standards/repository-structure-guide.md`。

## 本地门禁（仅变更）

```bash
rtk python3 docs/governance/check_docs_naming.py --changed-only
rtk python3 docs/governance/check_docs_schema.py --changed-only
rtk python3 docs/governance/check_docs_links.py --changed-only
rtk python3 docs/governance/check_archive_manifest.py
rtk python3 docs/governance/check_agent_skill_consistency.py
rtk bash scripts/check-repository-shape.sh
rtk bash scripts/check-secrets.sh
rtk bash scripts/check-shell-style.sh
rtk bash scripts/check-tools.sh
```

## 全量门禁（CI/合并前）

```bash
rtk bash scripts/check-all.sh
```

## pre-commit 入口

- Hook 文件：`.githooks/pre-commit`
- 触发策略：当暂存区存在 `docs/` 或 `**/AGENTS.md` 或 `**/SKILL.md` 变更时执行。
- 本地启用：`git config core.hooksPath .githooks`

## CI 与服务端 Hook

- CI 模板：`.gitlab-ci.yml`、`.gitea/workflows/knowledge-check.yml`
- 服务端 hook：`scripts/pre-receive-knowledge.sh`
- 部署说明：`docs/runbooks/ci-setup-guide.md`、`docs/runbooks/server-hook-setup-guide.md`

## 文档生成入口

```bash
rtk bash scripts/new-doc.sh --type runbook --title "标题" --out docs/runbooks/example-runbook.md
```

```bash
rtk bash scripts/new-skill.sh --name example-triage --description "示例分诊技能" --scope tools
```
