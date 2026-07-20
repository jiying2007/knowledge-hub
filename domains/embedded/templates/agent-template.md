---
title: AGENTS 模板
doc_type: standard
knowledge_type: process
maturity: draft
status: archived
searchable: false
owner: team-core
created: 2026-05-17
last_updated: 2026-05-17
tags: [template, agent]
related: [../standards/agent-skill-engineering-baseline.md]
validation_refs: []
---

# AGENTS 模板

复制到目标目录的 `AGENTS.md` 后，保留 7 个章节顺序。

```markdown
# <Scope> AGENTS

## 1. 基本信息

- 仓库/子仓库：
- 角色定位：
- 层级定位：

## 2. 职责范围

- <职责 1>
- <职责 2>

## 3. 依赖边界

- 允许依赖：
- 禁止依赖：

## 4. 禁止事项

- <禁止项 1>
- <禁止项 2>

## 5. 规范要求

- 工程基线：遵循 `docs/standards/agent-skill-engineering-baseline.md`。
- 代码规范：遵循 `docs/standards/c-coding-standards.md`。

## 6. 最小验证

- 构建：`rtk bash scripts/check-all.sh`
- 边界扫描：`rtk python3 docs/governance/check_docs_links.py --changed-only`
- 规范检查：`rtk python3 docs/governance/check_agent_skill_consistency.py`

## 7. 推荐技能

- `<path-to-skill>/SKILL.md`
```
