# APP 子仓库 AGENTS

## 1. 基本信息

- 子仓库：`modules/app`
- 角色定位：应用层与 diag runtime 托管层
- 层级定位：分层架构上层

## 2. 职责范围

- 托管 `app_diag` 运行时并连接 `cmd_node`。
- 维护 `registry/dispatcher/center` 命令闭环。
- 统一托管 APP/API/HDI 运行时 diag provider 生命周期与命令可见性。

## 3. 依赖边界

- 允许依赖：`modules/api`、`modules/hdi`、`modules/common`。
- 禁止依赖：反向泄漏到下层对 APP 运行时的编译耦合。

## 4. 禁止事项

- 禁止恢复全量 `diag_core` 一次性初始化路径。
- 禁止在 APP provider 中越权初始化非 owner 资源。
- 禁止保留历史兼容协议分支。

## 5. 规范要求

- 设计规范：canonical dispatch + APP runtime provider 收口；命令 owner 表达被诊断对象。
- 工程基线：遵循 `docs/standards/agent-skill-engineering-baseline.md`。
- 代码规范：遵循 `docs/standards/c-coding-standards.md`。
- 目录规范：`modules/app/include` 与 `include/app` 对外头保持同步一致。
- 编译规则：通过 `rtk make modules/app_obj_all -j20` 验证，命令必须使用 `rtk` 前缀。

## 6. 最小验证

- 构建：`rtk make modules/app_obj_all -j20`
- 边界扫描：`rtk python3 tools/diag/checks/check_diag_layer_deps.py`
- 规范检查：`rtk python3 tools/diag/checks/check_diag_naming.py`
- 覆盖审计：`rtk python3 tools/diag/checks/check_diag_interface_coverage.py`

## 7. 推荐技能

- `modules/app/.codex/skills/app-diag-runtime/SKILL.md`
