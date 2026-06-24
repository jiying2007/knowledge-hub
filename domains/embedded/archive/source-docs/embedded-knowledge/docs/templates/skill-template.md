---
title: SKILL 模板
doc_type: standard
knowledge_type: process
maturity: draft
status: active
owner: team-core
created: 2026-05-17
last_updated: 2026-05-17
tags: [template, skill]
related: [../standards/agent-skill-engineering-baseline.md]
validation_refs: []
---

# SKILL 模板

新增技能优先使用：

```bash
rtk bash scripts/new-skill.sh --name <skill-name> --description "<description>" --scope tools
```

`SKILL.md` 主体应保持以下结构：

```markdown
---
name: <skill-name>
description: <description>
version: 1.0.0
last_updated: YYYY-MM-DD
---

# <Skill Title>

## 1. 触发条件

- <触发条件>

## 2. 处理范围

- <范围>

## 3. 强制检查

1. <检查项>

## 4. 最小验证

- 构建：`rtk bash scripts/check-all.sh`
- 边界扫描：`rtk python3 docs/governance/check_docs_links.py --changed-only`
- 规范检查：`rtk python3 docs/governance/check_agent_skill_consistency.py`

## 5. 输出要求

- <输出要求>
```

技能目录还必须包含：

- `README.md`
- `LICENSE`
- `agents/openai.yaml`
