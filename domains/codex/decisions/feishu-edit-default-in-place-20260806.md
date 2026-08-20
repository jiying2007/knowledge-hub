---
id: codex-feishu-edit-default-in-place-20260806
title: 飞书 Codex edit 默认直接工作区
kind: decision
domain: codex
path: domains/codex/decisions/feishu-edit-default-in-place-20260806.md
scope: feishu-codex-bot
visibility: private
status: reviewing
owner: pending-human-review
source: user-request-2026-08-06
review_after: 2026-09-06
created_at: 2026-08-06
updated_at: 2026-08-06
promotion: none
promotion_decision: none
tags: [feishu, codex, in-place, worktree, safety]
related: []
validation_refs:
  - ~/codex/tests/test_feishu_codex_bot.py
  - ~/codex/docs/feishu-codex-bot-usage.md
summary_zh: 飞书 Codex 的 edit 缺省改为直接修改登记仓库，worktree 保留为显式可选策略；直接模式禁止自动提交。
review_status: pending
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: reviewed
evidence_strength: tested-runtime
evidence_refs:
  - ~/codex/tests/test_feishu_codex_bot.py
generated_by_ai: true
ai_role: implementation-summary
ai_model_or_tool: Codex
ai_generated_at: 2026-08-06
human_reviewed_by:
human_reviewed_at:
review_basis:
decision_owner: project-owner
decision_status: implemented-pending-review
decision_date: 2026-08-06
---

# 飞书 Codex edit 默认直接工作区

## 背景

飞书助手原先把 `edit` 与独立 Git worktree、任务分支和受控本地提交强绑定。项目 owner 要求默认直接修改登记仓库，使本地可以立即看到改动，并让没有初始提交的仓库也能使用 `edit`。

## 适用范围

- 适用于本机飞书 Codex 助手的仓库级 `edit` 执行。
- 不改变 `explain`、`review` 的只读行为。
- 不授权 push、PR、远端修改、凭据读取或工作目录外写入。

## 权威来源

- source_id：user-request-2026-08-06
- source_path：当前实施会话；长期实现见 `~/codex/tools/codex_assets/feishu_codex_bot.py`
- owner：project-owner
- source_status：implemented-pending-review

## 决策问题

飞书助手的 `edit` 是否应默认直接修改当前仓库，同时保留可选 worktree 隔离路径。

## 选项

| 选项 | 影响范围 | 成本 | 风险 |
| --- | --- | --- | --- |
| 默认 `in_place` | 所有未显式配置策略的可写仓库 | 低 | 任务失败可能留下部分改动 |
| 默认 `worktree` | 所有可写仓库 | 中 | 本地不易直接看到改动，要求有效基线提交 |
| 仓库级显式选择 | 特殊高隔离仓库 | 中 | 配置复杂度增加 |

## 证据

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
| --- | --- | --- | --- | --- | --- |
| `rtk env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_feishu_codex_bot` | 0 | 23 项专项测试通过，覆盖默认直接模式、显式 worktree、脏工作区快照和禁止自动提交。 | `~/codex/tests/test_feishu_codex_bot.py` | Project | feishu-codex-bot |
| `rtk env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p 'test_*.py'` | 0 | 152 项全量测试通过。 | `~/codex/tests/` | Project | regression |
| `rtk bash scripts/doctor.sh --scope repo` | 0 | 仓库级 doctor 为 0 error、0 warning。 | `~/codex/` | Workflow | repo-health |
| `rtk bash scripts/feishu-codex-bot.sh check` | 0 | 私有策略加载为三个 `in_place` 可写仓库；敏感配置未归档。 | `~/codex/docs/feishu-codex-bot-usage.md` | Workflow | runtime-config |
| `rtk systemctl --user show feishu-codex-bot.service ...` | 0 | 服务 active/running，重启计数为 0；启动摘要确认 `in_place` 已加载。 | systemd user service（不归档原始日志） | Runtime | feishu-codex-bot.service |

## 决策

1. `edit_strategy` 缺省为 `in_place`。
2. 直接模式在登记仓库内执行，不创建 worktree 或任务分支。
3. 直接模式强制 `commit_enabled=false`，禁止受控服务自动提交。
4. 同一仓库沿用仓库级串行锁；执行前后比较 Git 工作区快照，避免把既有脏状态误判为当前任务产出。
5. `edit_strategy: worktree` 保留原隔离分支、验证和可选本地提交流程。
6. 直接模式失败后不自动回滚，避免破坏用户工作区；残留改动由 owner 本地审查。

## 当前结论

实现、脱敏示例、使用文档和本机私有策略已同步；服务运行态已加载默认直接模式。该条目保持 `reviewing`，不自动提升为 memory 或团队标准。

## 生效条件

- 专项与全量测试通过。
- 私有策略检查通过。
- systemd user service 重启后保持 active/running。

## 回滚条件

若直接模式产生不可接受的工作区干扰，为对应仓库显式设置 `edit_strategy: worktree`、仓库外部 `worktree_root`，并按需启用 `commit_enabled`；检查配置后重启服务。

## 风险与限制

- 直接模式会保留成功或失败任务产生的文件改动，不做自动清理。
- 验证命令会看到仓库已有改动，可能因既有问题失败。
- 未发送飞书测试消息，也未对真实项目执行测试性 edit；运行链路由专项测试、真实仓库只读快照和服务加载证据覆盖。
- 本文不包含 Open ID、chat ID、App 凭据、消息正文、原始日志、状态库或完整私有策略。

## Review 周期

- owner：project-owner
- review_after：2026-09-06
- 下一次复核内容：直接模式失败残留、并发串行效果、验证命令误报和是否需要仓库级恢复 worktree。
