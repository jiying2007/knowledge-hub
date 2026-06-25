---
name: docs-knowledge-governance
description: 保障 docs 子仓库的目标范围一致性、元数据完整性与治理门禁可执行。
version: 1.0.0
last_updated: 2026-05-18
---

# Docs Knowledge Governance Skill

## 1. 触发条件

- 修改 `docs/architecture`、`docs/runbooks`、`docs/standards`、`docs/archive`、`docs/templates`。
- 修改 `docs/governance`、`docs/templates`、`docs/AGENTS.md` 或本 `SKILL.md`。

## 2. 处理范围

- 仅处理文档资产治理、结构规范、元数据规范、门禁脚本与模板治理。
- 不修改业务代码行为作为本技能的直接目标。

## 3. 强制检查

1. 文档目标、范围、边界必须与当前代码与构建事实一致。
2. 文档新增或迁移必须满足命名规则与 Frontmatter Schema。
3. 文档链接、`related`、`validation_refs` 必须可解析，禁止悬挂引用。
4. 代码风格遵循 `$EMBEDDED_KNOWLEDGE_HOME/docs/standards/c-coding-standards.md`。
5. 结构与验证流程遵循 `docs/standards/agent-skill-engineering-baseline.md`。

## 4. 最小验证

- 构建：`rtk bash scripts/check-all.sh`
- 边界扫描：`rtk python3 docs/governance/check_docs_links.py --changed-only`
- 规范检查：`rtk python3 docs/governance/check_docs_schema.py --changed-only` 与 `rtk python3 docs/governance/check_agent_skill_consistency.py`

## 5. 输出要求

- 输出文档目标/范围/边界是否变化及原因。
- 输出新增或删除文档清单与落点目录。
- 输出门禁执行结果与未覆盖风险（若有）。
