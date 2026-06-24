# HDI 子仓库 AGENTS

## 1. 基本信息

- 子仓库：`modules/hdi`
- 角色定位：硬件抽象与底层能力封装
- 层级定位：分层架构底层

## 2. 职责范围

- 提供稳定、可复用、可测试的硬件能力接口。
- 保留 HDI 业务实现、公共接口和模块级测试边界。
- HDI 运行时 diag provider 由 `modules/app/src/app_diag/provider/hdi/` 托管。

## 3. 依赖边界

- 允许依赖：`modules/common`、本层内部模块。
- 禁止依赖：`modules/api`、`modules/app`。

## 4. 禁止事项

- 禁止 include `api/*` 或 `app/*` 头文件。
- 禁止在 `modules/hdi/src` 新增运行时 `DIAGPROV_Register` provider。
- 禁止在聚合 provider 中直接 Init/DeInit 共享资源。
- 禁止以聚合测试入口替代 owner provider。

## 5. 规范要求

- 设计规范：保持 HDI 单向边界；运行时 diag 由 APP 托管，命令 owner 表达被诊断对象。
- 工程基线：遵循 `docs/standards/agent-skill-engineering-baseline.md`。
- 代码规范：遵循 `docs/standards/c-coding-standards.md`。
- 目录规范：`include/` 对外接口，`src/` 内部实现，按模块归属维护。
- 编译规则：通过 `rtk make modules/hdi_obj_all -j20` 验证，命令必须使用 `rtk` 前缀。

## 6. 最小验证

- 构建：`rtk make modules/hdi_obj_all -j20`
- 边界扫描：`rtk python3 tools/diag/checks/check_diag_layer_deps.py`
- 规范检查：`rtk python3 tools/diag/checks/check_diag_naming.py`
- 覆盖审计：`rtk python3 tools/diag/checks/check_diag_interface_coverage.py`

## 7. 推荐技能

- `modules/hdi/.codex/skills/hdi-layer-boundary/SKILL.md`
