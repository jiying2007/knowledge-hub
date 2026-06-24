# Diag Command Metadata Standard

使用侧指南见 [Diag 使用指南](../runbooks/diag-usage-guide.md)。本文只定义命令元数据和 provider 生命周期标准。

## 目标

`cli` 和 `app_tool` 只提供通用 diag 入口，不承载业务命令参数说明。所有业务命令的参数、示例和用途必须由运行时 `diag.sys.catalog.run` / `diag.sys.help.run` 返回。

## 入口职责

- `cli diag run <diag.command> '<json>'`：只负责透传命令和 JSON 参数。
- `cli diag catalog`：展示动态 catalog，不硬编码业务命令。
- `cli diag help <diag.command>`：查询单命令运行时元数据。
- `app_tool run-cmd <diag.command> '<json>' --mode=<local|remote>`：只负责本地或远端执行。

## Provider 职责

每个通过 `DIAGPROV_Register` 注册命令的 provider 都必须实现 `pfnCollectMeta`，并确保每条 `DIAG_CommandInfo_t.pcCommand` 都有对应 `DIAG_CommandMeta_t`。

## Provider 生命周期

- `bAutoUpOnInit = VS_TRUE` 只允许用于纯注册 provider；`ModuleUp()` 不得初始化业务硬件、启动线程、连接网络、注册会覆盖业务行为的 callback。
- `ModuleUp()` 的终态职责是注册命令和元数据；命令执行态资源必须放到显式 `*.run` 命令及其 stop/cleanup 路径中管理。
- 自动自启 provider 必须由 `cmd_node` 托管，`bAllowExternalControl` 应为 `VS_FALSE`，避免 `diag.provider.down.run` 手动卸载自动 provider 导致引用计数不平衡。
- 维护类、高风险类、会改变设备状态或占用业务资源的 provider 默认不自启，只允许显式 `diag.provider.up.run` 后使用。
- owner 模块已经自行管理的 provider 不应再由 `cmd_node` 自启，避免双 owner 管理同一 provider 生命周期。
- 需要设置业务 callback 的诊断能力必须放在显式 diag command 中，不能放在 provider `ModuleUp()` 中。
- 如果 callback API 是单槽位 setter，不允许新增只覆盖业务 callback 且无法恢复原值的 diag 命令；确需诊断监听时，应先扩展业务 API 支持 observer/callback chain。
- `cmd_node` 托管的 provider 必须记录最近一次 up/down 返回码；`diag.provider.manager.state.list.run` 用于查看托管状态和失败原因。
- `app_tool --mode=local` 拉起 provider 失败时必须返回失败，不得继续伪装成 command-not-found。

## 终态分层

- 运行时 diag provider 统一放在 `modules/app/src/app_diag/provider/` 下，由 APP 的 `cmd_node` 或本地诊断工具托管生命周期。
- API/HDI 模块只保留业务实现、公共接口和模块级测试，不在模块 init/deinit 中注册运行时 diag 命令。
- `diag.api.*` / `diag.hdi.*` 命令名和 `pcOwner` 仍表达被诊断对象，例如 `API_DVR`、`HDI_AO`；源码位置不再代表命令 owner。
- 不向 `modules/common` 下沉 diag runtime、JSON helper 或 provider 封装；`modules/common` 视为第三方维护边界。
- 若后续需要跨产品复用 diag framework，应新建自维护的 `modules/diag` 或 `libs/diag`，不修改 `modules/common`。

元数据字段要求：

- `pcCommand`：必须与注册命令完全一致。
- `pcOwner`：使用注册命令的模块/owner，如 `APP_UART`、`API_DVR`、`HDI_AO`。
- `enLayer`：使用真实层级，必须与命令归属一致。
- `pcSummary`：一句话说明命令效果；会改变设备状态的命令要明确动作。
- `pcArgsSchemaJson`：列出必填/可选字段、类型、范围、默认值和顺序约束；无参数命令填 `{}`。
- `pcExampleJson`：给出完整可运行示例，格式为 `diag run <command> '<json>'`。

系统命令 `diag.sys.*` 和 `diag.provider.*` 不走 provider 收集，但也必须在系统命令元数据表中维护同等质量的提示。

系统 provider 状态命令分工：

- `diag.provider.registry.state.list.run`：查看 registry 中已经注册的 provider 引用计数、状态和最近错误。
- `diag.provider.manager.state.list.run`：查看 `cmd_node` 托管表、auto/external 策略和最近一次 up/down 返回码。

## 禁止项

- 不在 `cli` / `app_tool` usage 中加入 UART、DVR、WiFi、OTA 等业务示例。
- 不为带必填字段的命令返回通用 `json_object` 或空 `{}` 示例。
- 不新增 `pfnCollectMeta = NULL` 的 provider。
- 不让 catalog/help 依赖离线文档才能知道必填字段。
- 不在 `modules/api/src` 或 `modules/hdi/src` 新增运行时 `DIAGPROV_Register` provider。
- 不把带业务副作用的 provider 配置为自动自启。
- 不在 `ProviderModuleUp()` 中调用 `Init/Create/Connect/Start/Subscribe/*SetCallback/*Register*Callback` 这类业务副作用接口。
- 不保留无恢复路径的单槽 callback 覆盖型 diag 命令。
- 不保留含义不清的兼容命令名；provider registry 状态和 `cmd_node` manager 状态必须使用不同命令。

## 门禁

新增或修改 diag 命令后至少运行：

```bash
rtk python3 tools/diag/checks/check_diag_metadata.py
rtk python3 tools/diag/checks/check_diag_command_quality.py
rtk python3 tools/diag/checks/check_diag_naming.py
rtk python3 tools/diag/checks/check_diag_interface_coverage.py
rtk python3 tools/diag/checks/check_diag_layer_deps.py
```

涉及 C 代码时，还需要运行对应模块构建或定向语法检查。
