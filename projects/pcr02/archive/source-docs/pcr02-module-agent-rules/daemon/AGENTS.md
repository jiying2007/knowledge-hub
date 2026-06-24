# Daemon 子仓库 AGENTS

## 1. 基本信息

- 子仓库：`daemon`
- 角色定位：进程编排器
- 层级定位：系统守护层（不处理诊断业务）

## 2. 职责范围

- 按运行模式编排进程组合并负责拉起/回收。
- 维护守护、热插拔、看门狗等运行期机制。
- 保证模式切换与异常恢复流程可重复执行。

## 3. 依赖边界

- 允许依赖：进程管理、系统事件、守护相关公共能力。
- 禁止依赖：`hdi/api/app` 业务模块细节与 diag 业务执行链路。

## 4. 禁止事项

- 禁止在 daemon 内处理 diag 命令。
- 禁止在 daemon 内初始化业务资源。
- 禁止耦合业务模块私有状态机。

## 5. 规范要求

- 设计规范：仅做编排，不做业务执行。
- 工程基线：遵循 `docs/standards/agent-skill-engineering-baseline.md`。
- 代码规范：遵循 `docs/standards/c-coding-standards.md`。
- 目录规范：守护主流程与子功能文件边界清晰。
- 编译规则：通过 `rtk make daemon_app_all -j20` 验证，命令必须使用 `rtk` 前缀。

## 6. 最小验证

- 构建：`rtk make daemon_app_all -j20`
- 边界扫描：`rtk rg "diag|VSAPPDIAG|CMD_SYS_DYNAMIC_CMD" daemon -n`
- 规范检查：`rtk rg "prog_cmd_server|prog_pcr02|prog_product_test" daemon -n`

## 7. 推荐技能

- `daemon/.codex/skills/daemon-orchestrator/SKILL.md`
