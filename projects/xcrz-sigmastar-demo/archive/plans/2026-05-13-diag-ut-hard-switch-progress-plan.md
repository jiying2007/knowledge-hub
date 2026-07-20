---
doc_type: plan
knowledge_type: process
maturity: verified
created: 2026-05-13
last_updated: 2026-05-14
related:
- ../runbooks/prog-tool-usage-guide.md
- ../reports/2026-05-14-prog-tool-terminal-release-report.md
id: pcr02-diag-ut-hard-switch-progress-archive-20260513
title: Diag UT 硬切进展
kind: project-archive
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/archive/plans/2026-05-13-diag-ut-hard-switch-progress-plan.md
scope: project-specific
visibility: team-internal
status: archived
owner: team-core
source:
  type: retired-source-provenance
  source_id: pcr02-project-docs
  source_path: plans/2026-05-13-diag-ut-hard-switch-progress-plan.md
  source_sha256: 22f034bd44bea7fb9519bbd63ed39cba796e124c810fd4d89dcb744597e2dcaa
review_after: '2026-10-16'
review_status: archive-only-historical-provenance
promotion: none
promotion_decision: none; archived historical diag UT progress only, no active promotion and no current test-pass claim
tags:
- pcr02
- archive-only
- historical-progress
- no-active-promotion
- diag
- ut
- hard-switch
validation_refs:
- projects/xcrz-sigmastar-demo/archive/plans/2026-05-13-diag-ut-hard-switch-progress-plan.md
- rtk bash tools/knowledge-check.sh --dry-run
created_at: '2026-06-16'
updated_at: '2026-07-19'
summary_zh: 归档 2026-05-13 Diag UT 硬切进展；仅作历史进展记录 provenance，不代表当前测试覆盖、当前通过状态或 active 发布门禁。
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
