# TOOLS 子仓库 AGENTS

## 1. 基本信息

- 子仓库：`tools`
- 角色定位：跨模块复用工具层
- 层级定位：公共工程效率支撑层

## 2. 职责范围

- 维护跨模块可复用的调试、诊断、构建辅助工具。
- 提供统一入口，避免工具散落在单模块目录。
- 保证工具文档、使用方式与输出格式稳定。
- 将高频、可流程化、可验证的工具使用方式沉淀为 Codex skill。

## 3. 依赖边界

- 允许依赖：`docs/standards`、`docs/governance`、`scripts/check-all.sh`。
- 禁止依赖：业务模块私有实现细节作为长期硬依赖。
- 禁止依赖：仅服务单模块的一次性临时脚本沉淀到公共工具层。
- 目标板脚本必须默认低依赖，优先兼容 BusyBox 常见命令；主机侧脚本可依赖 `bash`、`file`、`readelf`、`sha256sum` 等基础工具。

## 4. 禁止事项

- 禁止新增高耦合、不可复用工具到 `tools`。
- 禁止输出未经验证的“已定位/已修复”结论模板。
- 禁止默认产生超长日志输出导致 token 浪费。
- 禁止脚本默认删除、覆盖或移动用户数据；需要写文件时必须显式输出目标路径。
- 禁止把敏感日志、core、SDK 原包打包进 Git 管理目录。

## 5. 规范要求

- 设计规范：工具必须明确输入、输出、失败路径与最小验证步骤。
- 工程基线：遵循 `docs/standards/agent-skill-engineering-baseline.md`。
- 代码规范：遵循 `docs/standards/c-coding-standards.md`。
- Shell 规范：遵循 `docs/standards/shell-script-style-guide.md`。
- 路径规范：团队技能统一放在仓库根 `.agents/skills/`。
- 命令规范：命令必须使用 `rtk` 前缀。
- 脚本契约：公共脚本必须支持 `--help`，失败时非零退出，输出低噪音摘要，长日志写入文件。
- 脚本契约：有写入行为的脚本应支持 `--out`、`--out-dir` 或 `--dry-run` 中至少一种显式控制。
- 交付门禁：未给出复现命令与验证证据，不得声明“已定位完成”。

## 6. 最小验证

- 构建：`rtk bash scripts/check-all.sh`
- 边界扫描：`rtk python3 docs/governance/check_docs_links.py --changed-only`
- 规范检查：`rtk python3 docs/governance/check_agent_skill_consistency.py`

## 7. 推荐技能

- `.agents/skills/offline-gdb-core-debug/SKILL.md`
- `.agents/skills/asan-crash-triage/SKILL.md`
- `.agents/skills/sigbus-memory-triage/SKILL.md`
- `.agents/skills/crash-report-normalizer/SKILL.md`
- `.agents/skills/embedded-performance-triage/SKILL.md`
- `.agents/skills/yolo-ai-vision-triage/SKILL.md`
- `.agents/skills/voice-audio-normalizer/SKILL.md`
- `.agents/skills/sigmastar-media-pipeline-triage/SKILL.md`
- `.agents/skills/embedded-build-release-check/SKILL.md`
- `.agents/skills/sdk-upgrade-risk-review/SKILL.md`
- `.agents/skills/resource-leak-triage/SKILL.md`
- `.agents/skills/artifact-provenance-audit/SKILL.md`
- `.agents/skills/field-issue-intake-normalizer/SKILL.md`
