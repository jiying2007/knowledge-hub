# 项目 Tools Agent 规则

## 1. 基本信息

- 子目录：`tools`
- 角色定位：当前项目工具适配层
- 团队知识库：`~/embedded/knowledge`

## 2. 职责范围

- 维护当前项目专用的工具入口、环境默认值和 wrapper。
- 仅封装与当前项目强绑定的参数，例如 `prog_pcr02`、`out/arm/app`、`out/arm/target`。
- 公共排障脚本、通用发布脚本、Codex skill 和模板统一由 `~/embedded/knowledge` 维护。

## 3. 依赖边界

- 允许依赖 `$EMBEDDED_KNOWLEDGE_HOME/tools` 和 `$EMBEDDED_KNOWLEDGE_HOME/docs`。
- 禁止复制团队知识库中的通用脚本实现到当前项目。
- 禁止把一次性临时命令沉淀为项目公共工具。
- 当前项目 wrapper 只负责默认参数、命令分发和前置检查；公共采集、分析、归档逻辑必须留在知识库。

## 4. 禁止事项

- 禁止脚本默认删除、覆盖、移动用户数据。
- 禁止把 core、日志包、SDK 原包、客户信息或未脱敏现场材料写入 Git。
- 禁止绕过 `rtk` 执行 shell 命令。

## 5. 规范要求

- 项目工具必须支持 `--help`。
- 写入文件时必须显式输出目标路径。
- 默认输出低噪音摘要，长日志写入 `/tmp` 或调用者指定目录。
- 无法找到 `$EMBEDDED_KNOWLEDGE_HOME` 时必须明确报错。
- 调用知识库脚本前必须检查目标脚本是否存在且可执行，避免出现隐式 `No such file`。
- 传递用户参数时必须保留原始顺序；项目默认参数只在调用者未显式覆盖时补入。

## 6. 最小验证

- 语法：`rtk bash -n tools/debug/project-knowledge-debug.sh`
- 帮助：`rtk bash tools/debug/project-knowledge-debug.sh --help`
- dry-run：`rtk bash tools/debug/project-knowledge-debug.sh media-snapshot --dry-run`

## 7. 推荐入口

- 项目工具入口：`tools/README.md`
- 公共工具入口：`$EMBEDDED_KNOWLEDGE_HOME/tools/README.md`
