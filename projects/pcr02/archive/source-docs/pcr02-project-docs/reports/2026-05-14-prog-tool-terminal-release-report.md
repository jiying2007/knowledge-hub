---
title: prog_tool 终版发布说明
doc_type: report
knowledge_type: decision
maturity: verified
status: archived
owner: team-core
created: 2026-05-13
last_updated: 2026-05-14
tags: [diag, prog-tool, release]
related: [../runbooks/prog-tool-usage-guide.md, ../runbooks/examples/prog-tool-ci-smoke.session]
validation_refs: []
---

# prog_tool 终版发布说明

> 归档说明：本文为历史报告，只记录当时结论与验证；当前执行以 active 文档、本仓实际脚本和 ~/embedded/knowledge 的当前入口为准。

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
