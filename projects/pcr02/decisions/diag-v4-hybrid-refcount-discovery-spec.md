---
title: PCR02 Diag V4 终态设计（Hybrid RefCount + 发现先行）
doc_type: spec
knowledge_type: decision
maturity: verified
status: active
owner: team-core
created: 2026-05-10
last_updated: 2026-05-12
tags: [diag, v4, spec]
related: []
validation_refs: []
---

# PCR02 Diag V4 终态设计（Hybrid RefCount + 发现先行）

## 0. 文档信息
- 日期：2026-05-10
- 适用范围：`cmd_server`、`cli`、`modules/hdi`、`modules/api`、`modules/app`、`pcr02`、`app_product_test`
- 设计目标：在 V4 边界内建立可维护、可扩展、可观测的诊断体系，解决通用组件生命周期与 CLI 膨胀问题
- 强制规范基线：`~/knowledge-hub/domains/embedded/` 中的 C/C++ 编码规范（本设计所有实现细节若与其冲突，以该规范为准）

## 1. 已确认决策
1. 生命周期策略：`Hybrid`（默认 owner 驱动，同时允许外部 bring up/down）。
2. 防重策略：`RefCount`（运行时引用计数 + 模块内部引用计数双层防重）。
3. 发现能力策略：`发现先行`（借鉴 `ccli` 模式，CLI 从硬编码命令集合转为目录发现入口）。
4. 版本可观测策略：`分层版本清单`（借鉴 `version` 模式，按 HDI/API/APP 输出版本矩阵）。
5. 维护链路策略：`事务化 maint`（借鉴 updater 的阶段化思想，采用 `prepare/verify/commit/rollback`）。

## 2. 目标与非目标
### 2.1 目标
1. 消除重复初始化/重复反初始化风险（重点：`VSAPIDVR_RecordInit` 可重复初始化问题）。
2. 让命令可见性严格服从模块就绪状态与引用计数状态。
3. 让 CLI 不随模块增长无限膨胀，支持命令自注册、自发现、使用提示。
4. 形成可回归测试矩阵，覆盖 owner-only、ext-only、mixed、并发与异常恢复。

### 2.2 非目标
1. 不回退到 legacy 协议或双语义兼容。
2. 不在 `cmd_server` 引入业务执行逻辑。
3. 不引入独立 `diag-registryd` 进程。

## 3. 边界与分层
1. 控制面：`cmd_server` 仅 gateway/registry/router。
2. 执行面：业务命令仅在业务进程内 `app_diag runtime` 执行。
3. 分层依赖：`hdi -> api -> app` 单向依赖，不允许反向调用。
4. provider 约束：handler 仅访问本层与下层能力，不做跨 owner 资源生命周期管理。

## 4. 生命周期模型（Hybrid + RefCount）

### 4.1 provider 运行态模型（调度层）
每个 provider 维护：
- `state`: `DOWN | STARTING | UP | STOPPING | ERROR`
- `owner_ref`: owner 生命周期引用计数
- `ext_ref`: 外部 bring up/down 引用计数
- `gen`: 状态版本号（用于并发变更一致性）
- `last_error` / `last_actor` / `last_transition_ts`

### 4.2 事件入口
- `OwnerUp(provider)`：`owner_ref++`
- `OwnerDown(provider)`：`owner_ref--`（下限 0）
- `ExtUp(provider, actor)`：`ext_ref++`
- `ExtDown(provider, actor)`：`ext_ref--`（下限 0）

### 4.3 执行动作规则
- 当 `owner_ref + ext_ref` 从 `0 -> 1`：执行真实 `ProviderStart/Register`。
- 当 `owner_ref + ext_ref` 从 `1 -> 0`：执行真实 `ProviderStop/Unregister`。
- 其他变化仅更新计数与观测，不触发二次 Init/DeInit。

### 4.4 并发规则
- provider 级 mutex 保护状态迁移。
- `STARTING/STOPPING` 阶段拒绝反向重入，返回 `busy_retry`。
- 重复 up/down 幂等，不导致重复初始化。

## 5. 模块内部防重（资源层）

### 5.1 硬规则
每个 owner 模块的 `*Init/*DeInit` 必须实现本地 `init_ref`。

### 5.2 统一语义
- `Init`：
  - `init_ref==0` 时执行真实初始化，然后 `init_ref++`
  - `init_ref>0` 时仅 `init_ref++`，直接返回成功
- `DeInit`：
  - `init_ref>1` 时仅 `init_ref--`
  - `init_ref==1` 时执行真实反初始化后归零
  - `init_ref==0` 时返回 `invalid_state`

### 5.3 重点整改对象
- `VSAPIDVR_RecordInit/DeInit`：按 RefCount 改造，避免重复线程/句柄/订阅初始化。

## 6. 命令发现与帮助体系（CLI 去膨胀）

### 6.1 CLI 角色收敛
CLI 仅保留稳定入口：
- `diag list`
- `diag run <command> [json]`
- `diag provider up/down ...`
- `diag help [command]`

逐步移除业务硬编码分支（如 `diag uart ...` 参数拼装分支）。

### 6.2 目录服务接口（runtime 提供）
1. `diag.sys.catalog.run {}`
- 返回全部命令目录（含 owner/layer/summary/args_schema/examples/lifecycle）。

2. `diag.sys.catalog.run {"prefix":"diag.api.event."}`
- 返回前缀过滤目录。

3. `diag.sys.help.run {"command":"diag.api.event.start.run"}`
- 返回单命令帮助（参数约束 + 示例 + 生命周期属性）。

4. `diag.provider.registry.state.list.run {}`
- 返回 registry provider 运行态：`state/owner_ref/ext_ref/last_error`。

5. `diag.provider.manager.state.list.run {}`
- 返回 `cmd_node` 托管 provider 策略和最近 up/down 返回码：`auto_up/allow_external_control/managed_up/last_up_ret/last_down_ret`。

### 6.3 CommandMeta 建议字段
- `command`
- `owner`
- `layer`
- `summary`
- `args_schema`
- `examples[]`
- `lifecycle`（`owner_managed` / `external_manageable`）

## 7. 分层版本矩阵
新增：`diag.sys.version.matrix.run {}`

输出按层分组：
- `hdi`: 模块版本集合
- `api`: 模块版本集合
- `app`: 模块版本集合

每项至少包含：
- `module`
- `version`
- `build_time`
- `state`（`up/down`）

用途：发布核对、现场排障、兼容性定位。

## 8. maint 事务化语义（借鉴 updater 思想）

### 8.1 事务阶段
- `prepare`
- `verify`
- `commit`
- `rollback`

### 8.2 规则
1. 同一资源同一时刻仅允许一个活跃事务（互斥锁）。
2. `verify` 失败必须可回滚。
3. `commit` 后必须可审计（事务 ID、时间、校验结果）。
4. 重复 `verify/commit` 必须幂等。

## 9. 测试体系（必须覆盖）

### 9.1 生命周期与防重复
1. owner-only（仅 owner up/down）
2. ext-only（仅 provider up/down）
3. mixed（owner 与 external 混合顺序）
4. 重复 init/deinit 越界

### 9.2 并发与故障
1. 并发 up/down 竞争
2. STARTING/STOPPING 期间反向操作
3. 启动失败进入 ERROR 与恢复路径

### 9.3 发现与帮助
1. catalog 全量与过滤输出正确
2. help 单命令 schema 与示例正确
3. CLI 不依赖硬编码命令表

### 9.4 版本矩阵
1. 分层输出完整
2. 未上线模块标 `down` 而非缺失

### 9.5 maint 事务
1. 正向流程：prepare->verify->commit
2. 异常流程：prepare->verify_fail->rollback
3. 并发互斥与幂等重试

## 10. 代码规范与工程门禁（强制）
0. 规范基线与优先级：
- 必须严格遵循 `~/knowledge-hub/domains/embedded/` 中的 C/C++ 编码规范。
- 本节是 V4 诊断域的补充约束，不替代 C 代码总规范；冲突时以 Hub 中的 C/C++ 编码规范为最高优先级。

1. 命名规范：
- 运行时诊断 provider 统一由 APP 托管：API owner 使用 `app_diag_api_*_provider`，
  HDI owner 使用 `app_diag_hdi_*_provider`，APP owner 使用 `app_diag_*_provider`。
- 禁止引入历史中性承载命名（如 `diag_case_*`、`diag_runtime_*`、`*_test_aggregate_*`）。
- 对外导出符号遵循“模块前缀 + 语义动作”风格，避免混合旧前缀与缩写漂移。
- 函数命名单轨：统一采用 `VSAPPDIAG_CmdNodeInit` 风格，禁止同模块并存 `VSAPPDIAGCMDNODE_*` 与 `VSAPPDIAG_*` 双风格。
- `_` 前缀函数必须 `static`，非 `static` 函数禁止 `_` 前缀。

2. 目录规范：
- 业务 provider 不使用多级嵌套目录，统一在各层 provider 目录扁平管理。
- `modules/app/src/app_diag` 仅承载 APP 运行时与 APP owner provider，不回流 API/HDI owner 代码。
- 目录变更仅做结构收敛，不允许借机引入行为变更。

3. 头文件规范：
- `modules/app/include` 与 `include/app` 必须逐文件一致（发布契约单轨）。
- 新增/修改公共契约时，必须同步双路径头文件并完成一致性检查。
- 禁止跨层 include（例如 HDI include APP 头、API include APP 私有实现头）。

4. 并发与状态机编码规范：
- 所有 provider 状态迁移必须在互斥区内完成，禁止无锁读改写 `owner_ref/ext_ref/state`。
- `STARTING/STOPPING` 分支必须显式返回可观测错误码，不允许静默吞错。
- 所有 `Init/DeInit` 必须实现 RefCount 语义并防越界。
- 局部变量与返回值组织遵循 C 规范：变量在代码块头部集中定义，返回值使用统一 `s32Ret` 路径收口。

5. 错误语义与结果格式规范：
- 统一 JSON 响应格式：`{\"code\":<int>,\"msg\":\"<string>\",\"data\":<json|null>}`。
- 新增命令必须声明稳定错误码集合（`invalid_param/invalid_state/not_supported/busy_retry` 等）。
- 禁止保留或新增 legacy 兼容语义分支。

6. 测试与提交门禁：
- 任何行为改动必须附对应测试点（至少覆盖正常/异常/并发三类之一，核心路径需全覆盖）。
- 静态门禁至少包含命名检查、分层依赖检查、legacy 语义检查。
- 未通过门禁不得宣称完成；无法执行验证必须明确记录阻塞原因与风险。
- 代码风格门禁必须包含：Yoda 条件、布尔判断风格、`(VS_VOID)` 显式忽略返回值、日志宏替代 `printf`、Allman 大括号与 120 列限制。

## 11. 验收标准（DoD）
1. `VSAPIDVR_RecordInit` 等关键模块完成内部 RefCount 防重。
2. provider 运行态可观测，`owner_ref/ext_ref/state` 可查询。
3. CLI 具备目录发现与单命令帮助，不再依赖持续增长的硬编码业务分支。
4. 版本矩阵命令可输出分层状态。
5. maint 命令域具备事务化语义与回滚路径。
6. 静态门禁、契约门禁、运行回归门禁全部通过。

## 12. 迁移顺序（建议）
1. 先落 `provider state + refcount` 中心能力。
2. 再改 `VSAPIDVR_RecordInit/DeInit` 等模块内部 RefCount。
3. 再落 `catalog/help/version_matrix` 并收敛 CLI。
4. 最后完成 maint 事务化与回归收口。

## 13. 风险与应对
1. 风险：owner 与 external 并发下状态抖动。
- 应对：provider 级 mutex + 显式状态机 + `busy_retry`。

2. 风险：历史模块未做内部防重导致“外层正确、内层重复”。
- 应对：模块内 RefCount 作为硬门禁，优先 DVR/VIDEO/AI 等高风险模块。

3. 风险：CLI 改造期间用户命令习惯迁移成本。
- 应对：保留 `diag run` 稳定入口，`diag help` 提供自动提示与示例。
