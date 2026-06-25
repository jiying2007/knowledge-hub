# Changelog

## 2026-05-16

- 初始化嵌入式研发团队知识库。
- 增加团队 onboarding、Codex skills 安装与贡献规范。
- 增加统一门禁入口 `scripts/check-all.sh`。
- 将调试工具默认路径参数化，减少 PCR02 项目耦合。
- 将 SigmaStar 归档 URI 从本机 `/tmp` 示例迁移为团队制品 URI。

## 2026-05-17

- 增加 `CODEOWNERS`、`.githooks/pre-commit` 与项目 profile 示例。
- 增加归档 manifest 校验脚本并纳入统一门禁。
- 增加知识库发布与 tag 规范。
- 将 docs lint 报告生成纳入 `scripts/check-all.sh`。
- 增加 CI 模板、服务端 hook 脚本、MR/PR 模板与变更申请模板。
- 增加 skill 元数据完整性门禁、secret scan、可选 shellcheck/shfmt 检查与 release 脚本。
- 增加个人开发增强建议与 artifact 实体校验脚本。
- 安装 shellcheck/shfmt 后补齐脚本静态检查修复，并统一格式化 shell 脚本。
- 增加个人开发工具 bootstrap、工具状态检查、文档生成脚本、EditorConfig 与 Shell 脚本风格规范。
- 全盘补齐性能、媒体链路、AI Vision 技术 runbook，新增运行期基线采集工具与对应分诊 skill。
- 将根 `AGENTS.md` 纳入统一 AGENT/SKILL 基线机检，并增加 AGENT/SKILL 模板与 skill 脚手架。
- 删除旧项目迁移残留表，新增仓库结构规范与机器门禁，禁止项目生命周期目录回流。
