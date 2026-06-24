# API 子仓库 AGENTS

## 1. 基本信息

- 子仓库：`modules/api`
- 角色定位：中间业务能力封装层
- 层级定位：分层架构中层

## 2. 职责范围

- 对 HDI 能力做业务化封装并提供稳定 API。
- 保留 API 业务实现、公共接口和模块级测试边界。
- API 运行时 diag provider 由 `modules/app/src/app_diag/provider/api/` 托管。
- 模块 init/deinit 保持幂等并使用 RefCount 防重复初始化。

## 3. 依赖边界

- 允许依赖：`modules/hdi`、`modules/common`。
- 禁止依赖：`modules/app`。

## 4. 禁止事项

- 禁止在 `modules/api/src` 新增运行时 `DIAGPROV_Register` provider。
- 禁止聚合 provider 承担多个模块生命周期。
- 禁止跨 owner 直接管理他模块资源。
- 禁止恢复临时测试入口语义回流。

## 5. 规范要求

- 设计规范：API 业务生命周期与 APP diag runtime 生命周期解耦。
- 工程基线：遵循 `docs/standards/agent-skill-engineering-baseline.md`。
- 代码规范：遵循 `docs/standards/c-coding-standards.md`。
- 目录规范：`include/` 对外接口，`src/` 业务实现，按模块维护 provider。
- 编译规则：通过 `rtk make modules/api_obj_all -j20` 验证，命令必须使用 `rtk` 前缀。

## 6. 最小验证

- 构建：`rtk make modules/api_obj_all -j20`
- 边界扫描：`rtk python3 tools/diag/checks/check_diag_layer_deps.py`
- 规范检查：`rtk python3 tools/diag/checks/check_diag_naming.py`
- 覆盖审计：`rtk python3 tools/diag/checks/check_diag_interface_coverage.py`

## 7. 推荐技能

- `modules/api/.codex/skills/api-layer-boundary/SKILL.md`
