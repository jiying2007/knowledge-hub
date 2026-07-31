---
title: 命令与工具入口规范
summary_zh: 约束 Hub 命令、工具入口、report-only 行为、rtk 包装和证据采集方式，降低维护时的误写、越权和不可复现风险。该 active 规范不授权自动发布、删除、远端 Git 写入、owner gate 关闭或
  memory 写入。
tags:
- governance
- tools
- rtk
- report-only
- zh-cn
id: knowledge-hub-command-tooling-rules
kind: standard
domain: governance
path: governance/command-tooling-rules.md
scope: team-general
visibility: team-internal
status: active
owner: leiwenjun
review_after: '2026-09-18'
review_status: human-reviewed-accepted
promotion: none
aliases:
- 命令与工具入口规范
related:
- indexes/obsidian-home.md
---

# 命令与工具入口规范

## 目标

Knowledge Hub 的命令和工具必须保守、可复查、可回滚。用户和自动化都应通过稳定入口调用，不直接绕过治理边界。

## 调用入口

- 所有 shell 命令通过 `rtk` 执行。
- 仓库工具优先使用 `rtk bash ~/knowledge-hub/tools/<tool>.sh ...`。
- 文档、README、模板和 runbook 不直接要求用户调用内部 Python 文件。
- 新增脚本入口后，至少从非仓库 cwd 做一次帮助或 dry-run 验证。

## 工具分类

只读工具：

- `knowledge-check.sh`
- `knowledge-context.sh`
- `knowledge-search.sh`
- `knowledge-inventory.sh`

这里的“只读”表示不修改 tracked/managed 知识资产。`knowledge-context.sh` 和 `knowledge-search.sh` 可以向忽略提交的 `.cache/knowledge-hub/` 写入可重建索引或脱敏 telemetry，但这些观测写入不是业务结果的硬依赖：只读文件系统、权限受限沙箱或 cache 故障必须返回 `telemetry.status=degraded` 并保留预检/检索结果；`--no-telemetry` 和 `KNOWLEDGE_TELEMETRY=off` 显式关闭观测写入。只允许捕获存储层 `OSError`，编程错误和业务错误不得被 telemetry 降级逻辑吞掉。

写入计划工具：

- `knowledge-capture.sh`
- `knowledge-review-attest.sh generate`
- `knowledge-promote.sh`
- `knowledge-retire.sh`

写入计划工具默认 dry-run。`knowledge-review-attest.sh generate --apply` 只把已经明确的真人决定机械写入忽略提交的本地表单，不创建执行授权或改变生命周期；`promote` / `retire --apply` 仍必须分别满足 execution authorization、content review attestation、rollback policy、hash 校验和验证命令。

工具资产候选采用双轨存储：源码、测试和 fixture 留在源仓 `codex_assets/`、`tools/` 或 `scripts/`；Hub 只保存项目路由、commit、相对路径、SHA256、候选评分、验证摘要、脱敏状态、风险和 promotion 建议。`knowledge-capture.sh --tool-asset-candidate <path>` 只接收 `knowledge-hub.tool-asset-candidate.v1`，默认生成事务计划；显式 `--apply` 也只能创建 `reviewing` validation，不能复制源码、raw log、core、二进制和现场信息，不能自动创建 decision 或提升 active。

项目会话使用 `knowledge-capture.sh --scan-tool-assets` 做 report-only 发现。扫描器不得执行候选代码或猜测验证通过；`unit_tests`、`cli_help`、`dry_run`、`non_repo_cwd` 只有存在当前会话证据时才允许显式传入 `pass`。`--hub-dry-run` 可以在 candidate 生成后自动规划 Hub 导入，但不能与 `--apply` 组合，并且必须用一个或多个 `--session-path` 限定当前会话实际修改的工具，避免吸收既有用户 dirty 变更。dirty worktree 必须分别绑定基线 HEAD 和当前文件 SHA256。

跨会话自动发现使用 `--tool-asset-session-start` / `--tool-asset-session-close`。baseline 和 observation 都是忽略提交的 runtime metadata：禁止保存会话全文、prompt、命令参数值、环境变量和工具输出正文。Observation ledger 必须有去重 ID、previous hash 和 content hash；同项目两个不同会话或跨两个项目的三个不同会话达到阈值后，才允许 session close 串联 Hub dry-run。`used-unchanged-in-session` 只能来自显式 `--used-tool-path`，不得从 shell history 或 raw session 猜测。

## 证据记录

命令类文档必须记录：

- 执行目录。
- 完整 `rtk ...` 命令。
- 执行日期。
- 退出码。
- 结果摘要。
- 失败时的阻塞原因和下一步。

## 禁止事项

- 不裸跑 `bash`、`git`、`python`、`rg`、`sed` 等命令。
- 不用 shell 重定向或 heredoc 写仓库文件。
- 不让无人值守自动化执行 `--apply`。
- 不绕过 registry 直接提升或退役条目。
- 不把工具输出中的敏感信息保存为长期正文。

## Review

- owner：`leiwenjun`
- review_after：`2026-09-18`
- validation_refs：`rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics`
