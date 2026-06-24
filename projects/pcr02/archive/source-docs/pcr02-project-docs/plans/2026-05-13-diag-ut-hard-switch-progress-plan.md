---
title: Diag UT 硬切进展
doc_type: plan
knowledge_type: process
maturity: verified
status: archived
owner: team-core
created: 2026-05-13
last_updated: 2026-05-14
tags: [diag, ut, hard-switch]
related: [../runbooks/prog-tool-usage-guide.md, ../reports/2026-05-14-prog-tool-terminal-release-report.md]
validation_refs: []
---

# Diag UT 硬切进展（2026-05-13）

> 归档说明：本文为历史计划，未勾选步骤不代表当前待办；重新执行前必须重新核对源码、构建脚本和验证命令。

## 本次落地

1. app_tool 已硬切为 prog_diag_ut，不再保留旧的 stdin 命令解释分支。
2. 执行模型改为 diag canonical command 驱动：
   - run <suite|all|strict|env>
   - --mode=local|remote
3. 用例由执行器运行时动态生成，不依赖外部 suite 文件。
4. 用例分层：
   - strict：强断言（expect=0）
   - env：环境容忍（expect=any）

## 追加更新（动态发现终态）

1. 已进一步硬切：取消 suite 文件依赖，全部改为运行时动态发现命令。
2. 命令发现来源：
   - local 模式：直接读 registry 命令表
   - remote 模式：调用 diag.sys.list.run 解析 commands
3. strict/env 由执行器按规则动态生成：
   - strict：仅执行可稳定给默认参数的命令（expect=0）
   - env：按模块自动挑选安全探测命令（expect=any）
4. app_tool/suites 目录及 *.suite 文件已删除。

## 文件级变更

- app_tool/app_tool.c
- app_tool/app_tool.mk

## 验证

- make app_tool_app_all -j8 通过。

## 下一批建议

1. 在发布打包流程中增加 suite 文件安装目标（例如 /customer/etc/diag_ut/suites）。
2. 按模块补齐 strict 用例覆盖率，减少 expect=any 比例。
3. 增加 junit/json 报告输出，接入 CI 门禁。
