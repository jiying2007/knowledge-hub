# Embedded Knowledge Base AGENTS

## 1. 基本信息

- 仓库：`embedded/knowledge`
- 角色定位：嵌入式研发团队知识库
- 内容范围：技术文档、排障手册、平台知识、调试工具、Codex skill
- 层级定位：团队级知识资产与工程工具单一事实源

## 2. 职责范围

- 维护 `docs/` 下长期可复用的知识资产。
- 维护 `tools/` 下跨项目复用的调试、诊断、归档脚本。
- 维护 `scripts/` 下团队入口、门禁、脚手架与发布辅助脚本。
- 保证文档、工具、AGENT、SKILL 与脚本的入口、依赖、验证方式一致。
- 只沉淀跨项目、跨会话、可验证、可维护的技术知识。

## 3. 依赖边界

- 允许引用项目仓路径作为 `validation_refs` 的历史证据。
- 工具默认值可以服务当前团队主平台，但必须支持参数或环境变量覆盖。
- 不把单项目一次性临时脚本提升为公共工具，除非已沉淀为 runbook。
- 允许新增面向 SigmaStar、嵌入式 Linux、AI Vision 的通用技术文档与技能。
- 禁止把未脱敏的客户日志、SDK 包、core、私有路径或凭据写入 Git。

## 4. 禁止事项

- 禁止在 Git 中提交大体积二进制归档、core、日志包、私有 SDK 原始压缩包。
- 禁止把未验证的排障结论写成团队规范。
- 禁止绕过 `scripts/check-all.sh` 门禁合入文档结构、脚本、profile、manifest 或 skill 变更。
- 禁止新增没有 README/runbook 入口、没有失败路径说明、没有最小验证命令的公共脚本。
- 禁止新增不包含 `README.md`、`LICENSE`、`agents/openai.yaml` 的 skill。
- 禁止把个人工作区绝对路径、一次性迁移过程、阶段性组织方式、低复用环境噪音写入长期知识或 memory。

## 5. 规范要求

- 工程基线：遵循 `docs/standards/agent-skill-engineering-baseline.md`。
- 文档规范：遵循 `docs/governance/README.md` 与 `docs/standards/knowledge-contribution-guide.md`。
- Shell 规范：遵循 `docs/standards/shell-script-style-guide.md`。
- 制品规范：遵循 `docs/standards/embedded-artifact-provenance-standard.md`。
- 技术结论：必须能追溯到命令、日志、源码、构建产物或归档 manifest。
- 新增 AGENT/SKILL：必须使用模板或脚手架生成，并通过一致性门禁。
- 技术知识准入：必须同时满足“可复用、可验证、边界清晰、维护责任明确”。不满足时只能归档或丢弃。

## 6. 最小验证

- 构建：`rtk bash scripts/check-all.sh`
- 边界扫描：`rtk python3 docs/governance/check_docs_links.py --changed-only`
- 规范检查：`rtk python3 docs/governance/check_docs_schema.py --changed-only` 与 `rtk python3 docs/governance/check_agent_skill_consistency.py`

## 7. 推荐技能

- `.agents/skills/docs-knowledge-governance/SKILL.md`
- `.agents/skills/offline-gdb-core-debug/SKILL.md`
- `.agents/skills/embedded-performance-triage/SKILL.md`
- `.agents/skills/yolo-ai-vision-triage/SKILL.md`
- `.agents/skills/sigmastar-media-pipeline-triage/SKILL.md`
- `.agents/skills/embedded-build-release-check/SKILL.md`
- `.agents/skills/artifact-provenance-audit/SKILL.md`
