---
id: codex-feishu-user-default-repo-command-20260807
title: 飞书 Codex 按用户持久化默认项目
kind: decision
domain: codex
path: domains/codex/decisions/feishu-user-default-repo-command-20260807.md
scope: feishu-codex-bot
visibility: private
status: reviewing
owner: pending-human-review
source: user-request-2026-08-07
review_after: 2026-09-07
created_at: 2026-08-07
updated_at: 2026-08-07
captured_at: 2026-08-07
promotion: none
promotion_decision: none
tags: [feishu, codex, repository, user-preference, sqlite]
related:
  - codex-feishu-edit-default-in-place-20260806
validation_refs:
  - ~/codex/tests/test_feishu_codex_bot.py
  - ~/codex/docs/feishu-codex-bot-usage.md
summary_zh: 飞书 Codex 系统默认项目设为 llm_apps，并允许白名单用户通过 /repo 按用户持久化个人默认项目。
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
ai_generated_at: 2026-08-07
human_reviewed_by:
human_reviewed_at:
review_basis:
decision_owner: project-owner
decision_status: implemented-pending-review
decision_date: 2026-08-07
---

# 飞书 Codex 按用户持久化默认项目

## 背景

飞书助手原先只有策略文件中的全局 `default_repo`。用户需要把系统默认项目切换为 `llm_apps`，并能从飞书中持久修改自己的默认项目，而不影响其他用户。

## 适用范围

- 适用于本机飞书 Codex 助手登记仓库的默认选择。
- 不扩大仓库白名单、允许模式、文件系统路径、推送、提交或外部写权限。
- 显式 `repo=<别名>` 仍只覆盖当前任务。

## 权威来源

- source_id：user-request-2026-08-07
- source_path：当前实施会话；长期实现见 `~/codex/tools/codex_assets/feishu_codex_bot.py`
- owner：project-owner
- source_status：implemented-pending-review

## 决策

1. 策略文件的系统默认项目设为 `llm_apps`。
2. `/repo` 显示发送者当前默认项目和系统默认项目。
3. `/repo <别名>` 在通过消息去重、别名和发送者白名单校验后，立即把发送者的个人默认项目写入 SQLite。
4. `/repo reset` 清除发送者的个人设置并恢复系统默认项目。
5. 未显式提供 `repo=` 的任务优先使用个人默认项目；个人别名已移除或权限失效时回退系统默认项目。
6. 个人偏好以 Open ID 为键隔离，不允许一个用户修改其他用户或全局策略。

## 兼容与迁移

- SQLite 使用 `CREATE TABLE IF NOT EXISTS user_preferences` 增量升级，不需要离线迁移。
- 原有任务、消息去重和结果表不变。
- 旧客户端和旧消息格式继续可用；`repo=<别名>` 语义不变。
- 回滚时可移除新指令处理并把策略 `default_repo` 改回原别名；新增偏好表可保留，不影响旧版本读取。

## 验证证据

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
| --- | --- | --- | --- | --- | --- |
| `rtk python3 -m unittest tests.test_feishu_codex_bot`（首次） | 1 | 负向证据：发现 `/repo reset` 错误沿用个人默认项目，修复为显式回到系统默认。 | `~/codex/tests/test_feishu_codex_bot.py` | Project | reset fallback |
| `rtk python3 -m unittest tests.test_feishu_codex_bot`（修复后） | 0 | 26 项专项测试通过，覆盖指令解析、偏好持久化、用户隔离、单次覆盖、reset 和失效别名回退。 | `~/codex/tests/test_feishu_codex_bot.py` | Project | feishu-codex-bot |
| `rtk python3 -m unittest discover -s tests -p 'test_*.py'` | 0 | 155 项全量测试通过。 | `~/codex/tests/` | Project | regression |
| `rtk bash scripts/feishu-codex-bot.sh check` | 0 | 真实策略加载 4 个仓库，系统默认项目为 `llm_apps`；敏感配置内容未归档。 | `~/codex/docs/feishu-codex-bot-usage.md` | Workflow | runtime-config |
| `rtk systemctl --user show feishu-codex-bot.service ...` | 0 | 服务 active/running，新进程零重启。 | systemd user service（不归档原始日志） | Runtime | feishu-codex-bot.service |

## 风险与限制

- 本次未发送真实飞书测试消息，避免产生非必要外部消息；消息解析、持久化和路由由专项测试覆盖。
- 如果系统默认项目本身对发送者不可用，消息仍按现有白名单规则拒绝，不会越权回退到任意路径。
- 个人偏好只存仓库别名，不存消息正文、任务正文或 Codex 输出。
- 本文不包含 Open ID、chat ID、App 凭据、消息正文、原始日志、状态库或完整私有策略。

## 当前结论

实现、脱敏示例、使用指南和本机私有策略已同步，服务运行态已加载新版本。条目保持 `reviewing`，不自动提升为 memory 或团队规则。

## Review 周期

- owner：project-owner
- review_after：2026-09-07
- 下一次复核内容：真实用户使用体验、连续消息顺序、失效别名回退和是否需要管理员级全局默认指令。
