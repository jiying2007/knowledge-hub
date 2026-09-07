# DOCS 子仓库 AGENTS

## 1. 基本信息

- 子仓库：`docs`
- 角色定位：知识资产治理与技术文档主仓
- 层级定位：规范、架构、手册、模板与归档索引统一收口层

## 2. 职责范围

- 维护 `docs/` 下技术文档的目标、范围、边界与可执行门禁。
- 治理文档分类结构（`architecture/runbooks/standards/archive/templates/governance`）与元数据一致性。
- 维护文档治理脚本与模板，确保命名、Schema、链接、AGENT/SKILL 一致性可机检。
- 将高频排障经验沉淀为 runbook，将长期稳定规则沉淀为 standard，将系统模型沉淀为 architecture。

## 3. 依赖边界

- 允许依赖：`docs/governance/*`、`docs/templates/*`、`docs/standards/*`、`docs/architecture/*`、`docs/runbooks/*`。
- 禁止依赖：业务源码实现细节作为文档真值来源（必须以源码与构建脚本事实校验后写入）。
- 禁止依赖：阶段性临时结论覆盖终版主文档。
- 项目强绑定 spec、plan、report 必须留在项目仓，不进入本知识库生命周期目录。

## 4. 禁止事项

- 禁止把历史版本内容回流到终版主文档。
- 禁止在未验证事实的情况下写“已支持/已完成/已上线”。
- 禁止绕过治理门禁直接合入文档变更。
- 禁止新增 `docs/project`、`docs/specs`、`docs/plans`、`docs/reports`、`docs/superpowers`。
- 禁止把个人路径、现场敏感日志、客户信息、临时命令噪音写入长期文档。

## 5. 规范要求

- 设计规范：目标、范围、边界、回归要求必须可执行且可追溯。
- 工程基线：遵循 `docs/standards/agent-skill-engineering-baseline.md`。
- 代码规范：遵循 `docs/standards/c-coding-standards.md`。
- 制品规范：遵循 `docs/standards/embedded-artifact-provenance-standard.md`。
- 元数据规范：Frontmatter 必填字段完整，`doc_type/knowledge_type/maturity/status` 合法。
- 命名规范：遵循 `docs/governance/check_docs_naming.py` 规则。
- Runbook 必须包含：适用场景、输入材料、操作步骤、失败路径、验证方式、误判风险。
- Standard 必须包含：适用范围、强制规则、例外条件、验证方式。

## 6. 最小验证

- 构建：`rtk bash scripts/check-all.sh`
- 边界扫描：`rtk python3 docs/governance/check_docs_links.py --changed-only`
- 规范检查：`rtk python3 docs/governance/check_docs_schema.py --changed-only` 与 `rtk python3 docs/governance/check_agent_skill_consistency.py`

## 7. 推荐技能

- `.agents/skills/docs-knowledge-governance/SKILL.md`
