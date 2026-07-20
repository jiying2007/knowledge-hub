---
doc_type: report
knowledge_type: decision
maturity: verified
created: 2026-05-13
last_updated: 2026-05-14
related:
- ../runbooks/prog-tool-usage-guide.md
- ../runbooks/examples/prog-tool-ci-smoke.session
id: pcr02-prog-tool-terminal-release-validation-report-20260514
title: prog_tool 终版发布说明
kind: validation
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/validation/reports/2026-05-14-prog-tool-terminal-release-report.md
scope: project-specific
visibility: team-internal
status: archived
owner: team-core
source:
  type: retired-source-provenance
  source_id: pcr02-project-docs
  source_path: reports/2026-05-14-prog-tool-terminal-release-report.md
  source_sha256: a4ac12a7e4962aedbadce5d1778c0c205fb9e4b8bdb441e03922c9ab9ede1492
review_after: '2026-10-16'
review_status: archive-only-historical-provenance
promotion: none
promotion_decision: none; archived historical prog_tool release evidence only, no active promotion and no current release
  baseline claim
tags:
- pcr02
- validation
- archive-only
- historical-evidence
- no-active-promotion
- prog-tool
- release
- diag
validation_refs:
- projects/xcrz-sigmastar-demo/validation/reports/2026-05-14-prog-tool-terminal-release-report.md
- rtk bash tools/knowledge-check.sh --dry-run
created_at: '2026-06-16'
updated_at: '2026-07-19'
summary_zh: 归档 2026-05-14 prog_tool 终版发布说明；仅作历史 release evidence，不代表当前 prog_tool 版本基线、当前发布许可或 active release decision。
---

# prog_tool 终版发布说明

> 归档说明：本文为历史报告，只记录当时结论与验证；当前执行以 Knowledge Hub active 文档、本仓实际脚本、`~/knowledge-hub/domains/embedded/` 和 `~/knowledge-hub/projects/pcr02-ssc305/` 的当前入口为准。

## 1. 发布目标

`prog_tool` 作为诊断统一执行器进入终版发布状态，满足：

- 本地与远端统一执行语义
- 交互与脚本会话统一命令解析
- 统一 JSON 事件协议，支持 CI/日志平台直接解析
- 失败策略可控（fail-fast / continue）

## 2. 已发布能力

1. 命令入口
- `list`
- `run <suite> [--mode=local|remote] [--continue] [--json]`
- `run-cmd <diag.command> [json] [--mode=local|remote] [--hold-ms=<N>] [--json]`
- `session [--mode=local|remote] [--session-id=<id>] [--script=<file>] [--continue] [--json]`

2. 统一事件协议
- `schema_version=diagut.v1`
- 固定字段：`event/type/session_id/mode/line/ret/ok/reason/cmd/suite/discovered/passed/failed/suite_cases/suite_passed/suite_failed`

3. suite 统计语义
- `type=end` 输出当前 suite 增量：`suite_cases/suite_passed/suite_failed`
- `type=summary` 输出全局统计：`discovered/passed/failed`

## 3. 验收命令

```bash
# 编译
make app_tool_app_all -j8

# suite 本地回归
/customer/bin/prog_tool run strict --mode=local --json

# suite 远端链路
/customer/bin/prog_tool run env --mode=remote --continue --json

# 单命令
/customer/bin/prog_tool run-cmd diag.sys.ping.run '{}' --mode=remote --json

# 会话脚本（fail-fast）
/customer/bin/prog_tool session --mode=remote --script=/customer/etc/diag_ut/ci_smoke.session --json

# 会话脚本（continue）
/customer/bin/prog_tool session --mode=remote --script=/customer/etc/diag_ut/ci_smoke.session --json --continue
```

## 4. 配套文档

- 使用手册：`docs/runbooks/prog-tool-usage-guide.md`
- CI 脚本模板：`docs/runbooks/examples/prog-tool-ci-smoke.session`

## 5. 版本结论

当前版本可作为 `prog_tool` 终版发布基线。
