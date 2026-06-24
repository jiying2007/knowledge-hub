# CLI 子仓库 AGENTS

## 1. 基本信息

- 子仓库：`cli`
- 角色定位：命令行入口与 canonical payload 组装器
- 层级定位：控制面入口（不执行业务）

## 2. 职责范围

- 负责 `diag/maint` 命令输入规范化。
- 统一输出 canonical payload：`<command> [json]`。
- 提供 `help/list/discovery` 交互能力，不承担业务执行。

## 3. 依赖边界

- 允许依赖：`include/*` 公共协议与 CLI 自身代码。
- 禁止依赖：`modules/hdi`、`modules/api`、`modules/app` 业务实现。

## 4. 禁止事项

- 禁止在 `cli` 中硬编码持续膨胀的业务子命令矩阵。
- 禁止引入业务模块初始化、资源持有或生命周期管理逻辑。
- 禁止保留历史语法兼容分支。

## 5. 规范要求

- 设计规范：保持 discovery-first 与 canonical-only 语义。
- 工程基线：遵循 `docs/standards/agent-skill-engineering-baseline.md`。
- 代码规范：遵循 `docs/standards/c-coding-standards.md`。
- 目录规范：仅在 `cli/` 维护 CLI 逻辑，不跨目录承载业务实现。
- 编译规则：通过 `rtk make cli_app_all -j20` 验证，命令必须使用 `rtk` 前缀。

## 6. 最小验证

- 构建：`rtk make cli_app_all -j20`
- 边界扫描：`rtk rg "diag run|diag list|maint" cli/cli.c`
- 规范检查：`rtk rg "app_tool|prog_tool|compat" cli -n`

## 7. 推荐技能

- `cli/.codex/skills/cli-boundary/SKILL.md`
