---
id: codex-feishu-controlled-artifact-upload-20260807
title: 飞书 Codex 显式受控构建产物回传
kind: decision
domain: codex
path: domains/codex/decisions/feishu-controlled-artifact-upload-20260807.md
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
tags: [feishu, codex, artifact, apk, upload, safety]
related:
  - codex-feishu-user-default-repo-command-20260807
  - codex-feishu-edit-default-in-place-20260806
validation_refs:
  - ~/codex/tests/test_feishu_codex_bot.py
  - ~/codex/docs/feishu-codex-bot-usage.md
summary_zh: 飞书 Codex 仅在 edit 任务显式声明 artifact 时回传仓库策略允许的构建产物，当前仅 llm_apps 的 APK 目录启用。
review_status: pending
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: reviewed
evidence_strength: tested-runtime-external-smoke-pending
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

# 飞书 Codex 显式受控构建产物回传

## 背景

项目 owner 希望把 `llm_apps` 构建产生的 APK 回传到触发任务的飞书消息线程。原机器人仅支持文本回复，且不应自动发现或外传任意文件。

## 决策

1. 任务使用 `artifact=<仓库相对路径>` 显式授权一次文件回传，只允许与 `mode=edit` 组合。
2. 仓库策略默认禁用上传；当前仅 `llm_apps` 启用一个 Android 交付目录及 `.apk` 扩展名。
3. 策略限制非空普通文件、相对目录、扩展名和最大 30 MiB；拒绝绝对路径、`..`、非规范路径、符号链接和目录逃逸。
4. 产物准备阶段计算 SHA-256 与 inode/size/mtime 快照，流式上传前再次核对；文件在验证后或上传期间变化时不发送文件消息。
5. 上传先调用飞书文件接口取得 `file_key`，再以 `file` 类型回复原消息线程；日志不记录绝对路径、`file_key` 或文件正文。
6. 显式 artifact 任务允许只构建而不修改源码，解决 Git 忽略目录中的 APK 无法通过普通 edit 变更门禁的问题；普通 edit 仍要求工作区变化。
7. 入站附件下载不在本次范围内。

## 官方契约

- 上传文件：`https://open.feishu.cn/document/uAjLw4CM/ukTMukTMukTM/reference/im-v1/file/create`
- 回复消息：`https://open.feishu.cn/document/server-docs/im-v1/message/reply?lang=zh-CN`
- retrieved_at：2026-08-07
- 版权边界：仅记录接口参数、大小限制和调用关系的事实摘要，不复制官方正文。

官方接口要求文件非空且不超过 30 MB，通用二进制可使用 `file_type=stream`；回复文件消息前需要先上传并取得文件 Key。

## 验证证据

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
| --- | --- | --- | --- | --- | --- |
| 首轮专项/全量与私有策略断言 | 1 | 负向证据：测试夹具提前命中 mode 拒绝，且私有配置误把上传开关放到 x5；服务尚未重启，二者均已修复。 | `~/codex/tests/test_feishu_codex_bot.py` | Project | repair-ledger |
| `rtk python3 -m unittest tests.test_feishu_codex_bot` | 0 | 33 项专项测试通过，真实加载 lark-oapi 1.7.1 请求模型并替换网络客户端。 | `~/codex/tests/test_feishu_codex_bot.py` | Project | artifact-upload |
| `rtk python3 -m unittest discover -s tests -p 'test_*.py'` | 0 | 162 项全量测试通过。 | `~/codex/tests/` | Project | regression |
| 真实 APK 只读 ArtifactManager 预检 | 0 | 现有 llm_apps Debug APK 通过路径、普通文件、大小和摘要校验；未联网、未上传。 | `~/codex/docs/feishu-codex-bot-usage.md` | Workflow | apk-preflight |
| `rtk bash scripts/feishu-codex-bot.sh check` | 0 | 真实配置确认仅 `llm_apps` 启用 artifact upload。 | `~/codex/docs/feishu-codex-bot-usage.md` | Runtime | runtime-config |
| `rtk bash scripts/doctor.sh --scope repo` | 0 | 0 error、0 warning。 | `~/codex/` | Workflow | repo-health |
| `rtk systemctl --user show feishu-codex-bot.service ...` | 0 | 服务 active/running、零重启；启动日志加载 `artifact_uploads=llm_apps`。 | systemd user service（不归档原始日志） | Runtime | feishu-codex-bot.service |

## 风险与未闭环项

- 为避免未经确认的外部消息，本次未向真实飞书会话上传或发送 APK；飞书应用的“获取与上传图片或文件资源”权限需由首次显式任务验证。
- 上传成功但文件消息发送失败时，平台可能保留一个未在会话中引用的上传资源；任务会标记失败并回复错误类型。
- 本候选不包含 APK、SHA-256 全值、Open ID、chat ID、App 凭据、`file_key`、消息正文、原始日志或完整私有策略。

## 回滚

将目标仓库的 `artifact_upload.enabled` 设为 `false` 或移除配置，执行机器人 `check` 后重启服务。解析器仍可识别 `artifact`，但门禁会在任务入队前拒绝，其他文本、review、edit 和 `/repo` 行为不受影响。

## 当前结论

本地实现、SDK 请求模型、策略、真实 APK 预检和服务加载均已验证；真实飞书外部上传 smoke 保持待 owner 显式触发。条目保持 `reviewing`，不自动注册为 active 规则或 memory。
