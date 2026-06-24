# CMD Server 子仓库 AGENTS

## 1. 基本信息

- 子仓库：`cmd_server`
- 角色定位：diag gateway + registry + router（单进程）
- 层级定位：控制面核心（不执行业务）

## 2. 职责范围

- 处理动态命令接入、注册、路由与回包。
- 维护节点注册、心跳、超时摘除与模块状态观测。
- 对外提供统一错误语义（含无活跃处理者）。

## 3. 依赖边界

- 允许依赖：IPC 协议、路由注册表、公共基础库。
- 禁止依赖：`app_diag` 业务执行逻辑与业务资源初始化路径。

## 4. 禁止事项

- 禁止调用 `VSAPPDIAGIPC_Init/Handle/DeInit`。
- 禁止在 `CMD_SYS_DYNAMIC_CMD` 路径执行本地业务命令。
- 禁止保留历史兼容协议路径。

## 5. 规范要求

- 设计规范：仅接受 canonical command 并按路由执行转发。
- 工程基线：遵循 `docs/standards/agent-skill-engineering-baseline.md`。
- 代码规范：遵循 `docs/standards/c-coding-standards.md`。
- 目录规范：网关/注册/路由职责在 `cmd_server/` 内按文件分层清晰。
- 编译规则：通过 `rtk make cmd_server_app_all -j20` 验证，命令必须使用 `rtk` 前缀。

## 6. 最小验证

- 构建：`rtk make cmd_server_app_all -j20`
- 边界扫描：`rtk rg "VSAPPDIAGIPC_|app_diag/diag_ipc_adapter" cmd_server -n`
- 规范检查：`rtk rg "compat_protocol|legacy_protocol" cmd_server -n`

## 7. 推荐技能

- `cmd_server/.codex/skills/cmd-server-boundary/SKILL.md`
