# 飞书 Codex 与 pcr02-demo 本地开发闭环

- captured_at: 2026-08-02T22:45:00+08:00
- last_verified: 2026-08-02
- source: 当前实施会话及 `docs/feishu-codex-bot-usage.md`
- project: codex
- status: reviewing candidate

## 背景与目标

公司飞书空间中的 AI 助手需要默认操作 `pcr02-demo` 仓库，个人阶段先运行，后续可扩展到团队。允许只读分析、代码审查以及显式写任务；写任务可以创建本地分支和提交，但禁止推送、合并、rebase、创建 PR 或修改远端。

## 已落地决策

1. 默认仓库别名为 `pcr02-demo`，用户不能通过消息传入任意文件系统路径。
2. `explain`、`review` 使用 read-only sandbox；只有显式 `mode=edit` 才构成单次写授权。
3. 写任务不进入用户当前工作区，而是从配置的已提交 `base_ref` 创建隔离 worktree，分支命名为 `codex/feishu-<任务号>`。
4. Codex 只负责修改和任务内验证，不自行提交；受控服务检查改动、执行配置的验证命令，再创建本地提交。
5. 禁止推送采用多层防线：Codex sandbox 禁止网络写、Git transport 默认禁用、受控 `pre-push` 钩子拒绝操作，提示词也明确禁止远端写入。
6. 飞书 App 凭据不会传给 Codex 子进程。Bubblewrap 将凭据、策略、状态库和锁文件所在目录从 Codex 文件系统视图中隐藏。
7. 当前触发消息自动成为审计锚点，执行结果回复原消息线程；SQLite 只保存引用 ID、任务状态、分支和提交哈希，不保存消息正文或 Codex 输出。

## 飞书关联协议

消息前缀可以组合使用：

```text
mode=edit task=<任务GUID> requirement=<需求ID> defect=<缺陷ID> log=<消息ID> <任务描述>
```

- `task`：通过飞书任务 v2 读取标题、状态和描述；需要任务只读权限和资源可见性。
- `log`：按飞书消息 ID 读取文本内容；需要消息历史读取权限且机器人必须在对应会话内。
- `requirement`、`defect`：记录飞书项目工作项关联。飞书项目是独立产品，未配置专用连接器时只保存引用并明确提示未读取正文。
- 关联正文被视为不可信数据证据，不执行其中携带的命令或指令。

## 验证证据

- 专项单元测试：18 项通过。
- 仓库全量单元测试：147 项通过。
- 隔离运行 smoke：Codex 在默认仓库返回预期标记 `PCR02-ISOLATED-OK`。
- 文件系统隔离负向验证：Bubblewrap 内无法看到飞书凭据文件。
- 禁止推送负向验证：`pre-push` 按策略返回非零退出码。
- 配置检查：默认仓库、三种模式、白名单、私有文件权限和 Codex CLI 均通过。
- 运行态：systemd user service 为 active/running，重启计数为 0。

## 风险与边界

- 尚未配置飞书项目专用连接器，因此需求、缺陷正文不会自动拉取。
- 尚未启用消息附件下载；日志优先使用文本消息引用。
- 真实 `pcr02-demo` 仓库没有为了测试而创建占位分支；首条真实 `mode=edit` 任务才会创建分支和提交。
- 每个隔离 worktree 默认保留，便于审查与继续处理；清理 worktree 或分支属于单独的破坏性操作，需要显式确认。
- 当前应用密钥曾进入交互会话，应在飞书后台轮换；归档中不保存任何密钥值。

## 运维与回退

- 修改私有策略后先运行机器人 `check`，再重启 systemd user service。
- 停止服务不会删除 SQLite、worktree、分支或本地提交。
- 回退写能力时，从仓库策略的 `allowed_modes` 移除 `edit` 并重启服务；只读模式仍可继续使用。

## 后续动作

1. 在飞书后台确认任务和消息只读权限。
2. 明确飞书项目空间与工作项 API 后，增加只读需求/缺陷连接器。
3. 团队阶段增加每仓库白名单、任务配额、保留期限和 worktree 清理审批。

## Provenance

- 实现：`tools/codex_assets/feishu_codex_bot.py`
- 使用指南：`docs/feishu-codex-bot-usage.md`
- 脱敏策略：不包含 App ID、App Secret、Open ID、chat ID、access token、完整原始日志、消息正文或运行时数据库内容。
- Memory candidate: no；本材料仅作为 archive-only reviewing candidate，不自动提升到 memory 或 AGENTS.md。
