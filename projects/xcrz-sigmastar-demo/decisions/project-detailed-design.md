---
doc_type: architecture
knowledge_type: decision
maturity: verified
created: 2026-05-13
last_updated: 2026-05-13
related:
- project-overview-design.md
- project-core-module-design.md
- diag-command-architecture-final.md
- hdi-api-app-functional-overview.md
id: pcr02-project-detailed-design
title: PCR02 项目详细设计
kind: decision
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/decisions/project-detailed-design.md
scope: project-specific
visibility: team-internal
status: archived
owner: team-core
source:
  type: retired-source-provenance
  source_id: pcr02-project-docs
  source_path: architecture/project-detailed-design.md
  source_sha256: 7ce3a10fa39f8d686c096de77bfa29a697d2cd181dcc536cbb0ef4370b273f81
review_after: '2026-10-16'
review_status: delegated-review-closed-reference-boundary
promotion: none
promotion_decision: none; archived reference boundary, no owner decision generated
tags:
- pcr02
- decisions
- architecture
- detailed
validation_refs:
- projects/xcrz-sigmastar-demo/decisions/project-detailed-design.md
- rtk bash tools/knowledge-check.sh --dry-run
- artifacts/manifests/knowledge-hub-complete-delivery-closure-20260701.md
- artifacts/manifests/knowledge-hub-complete-delivery-closure-20260701.jsonl
evidence_refs:
- artifacts/manifests/knowledge-hub-complete-delivery-closure-20260701.md
- artifacts/manifests/knowledge-hub-complete-delivery-closure-20260701.jsonl
created_at: '2026-06-16'
updated_at: '2026-07-19'
summary_zh: 入口：cli/cli.c - 通道：ipc:///tmp/cmd_server.ipc、ipc:///tmp/cmd_event.ipc - 关键职责： - 组包并发送命令请求（VSIPC_MsgHeader_t + payload）。
  - 对 JSON 回复做格式化展示（紧凑/pretty）。 - 提供命令发现与可读。该条目当前为 archived decision provenance，仅作历史决策材料检索入口，不代表新的 owner decision、active 规则或当前发布状态。
---

# PCR02 项目详细设计

## 1. 可执行体职责设计

## 1.1 `cli`（`prog_cli`）

- 入口：`cli/cli.c`
- 通道：`ipc:///tmp/cmd_server.ipc`、`ipc:///tmp/cmd_event.ipc`
- 关键职责：
  - 组包并发送命令请求（`VSIPC_MsgHeader_t` + payload）。
  - 对 JSON 回复做格式化展示（紧凑/pretty）。
  - 提供命令发现与可读输出，不承载业务逻辑。

## 1.2 `cmd_server`（`prog_cmd_server`）

- 入口：`cmd_server/cmd_main.c`
- 核心：`cmd_server/cmd_router.c`
- 关键职责：
  - 初始化路由与网关（`VSCMD_RouterInit` / `VSCMD_GatewayInit`）。
  - 请求挂起池管理（`CMD_PENDING_MAX=128`）与超时回收（`CMD_ROUTE_TIMEOUT_MS=3500`）。
  - 调用方+命令维度限流（`CMD_RATE_MAX_PER_WINDOW=16`）。
  - 统一错误返回（`bad_request`/`route_timeout` 等）。

## 1.3 `daemon`（`prog_daemon`）

- 入口：`daemon/daemon_main.c`
- 关键职责：
  - 读取 `daemon.ini` 解析运行模式（APP / PRODUCT_TEST）。
  - 守护并拉起目标进程，异常退出按策略重启。
  - OTA 期间通过 `/tmp/prog_ota.lock` 抑制 App 异常重启，降低升级冲突风险。

## 1.4 `app_product_test`（`prog_product_test`）

- 目录：`app_product_test/`
- 依赖：`modules/hdi`、`modules/api`、`modules/app`、`modules/proto_c`
- 关键职责：
  - 生产测试模式业务流程。
  - 复用主链路通用基础设施，但运行权限与命令集受模式限制。

## 1.5 `pcr02`（`prog_pcr02`）

- 入口：`pcr02/main.cpp`
- 初始化序列：`Application -> Sensor -> Task -> IoT -> WiFi -> Bridge -> Navigation`
- 关键职责：
  - 作为公共主应用，承担跨模块集成入口职责。
  - 主业务逻辑承载与模块生命周期编排。
  - 处理 SIGINT/SIGTERM，执行模块反初始化和资源回收。

## 2. 模块层详细设计

## 2.1 `modules/hdi`

- 作用：统一 OS/硬件与 SigmaStar 平台能力封装。
- 目录骨架：
  - `src/hdi_os/`：线程、锁、内存、文件、时间等基础抽象。
  - `src/hdi_hw/`：GPIO/UART/I2C/ADC/PWM/WDT 等硬件抽象。
  - `src/hdi_video|hdi_audio|hdi_plat_ss/`：多媒体与平台适配。
  - `src/hdi_diag/`：诊断 provider（OS/VI/AO/AI）。

## 2.2 `modules/api`

- 作用：跨业务复用基础能力层。
- 子域：
  - 容器与数据结构：`api_container/*`
  - 网络与协议：`api_network/*`、`api_protocol/*`、`api_ipc/*`
  - 配置与编解码：`api_config/*`、`api_codec/*`
  - 诊断支持：`api_diag/*`
  - 业务算法：`api_ai/*`、`api_robot/*`

## 2.3 `modules/app`

- 作用：应用运行时聚合与诊断命令编排层。
- 关键子域：
  - `framework`：`app_diag_center`、`app_diag_registry`、`app_diag_dispatcher`
  - `ipc`：与 cmd_server 协议桥接
  - `provider`：`perf`、`ai`、`uart`、`archive_maint` 等命令提供者
  - `core`：参数解析与结果 JSON 生成

## 2.4 模块治理边界（强制）

纳管模块白名单：

- `modules/hdi`
- `modules/api`
- `modules/app`
- `modules/sensor`
- `modules/proto`
- `modules/proto_c`

非纳管模块：

- 其余 `modules/*` 目录及其同名能力，统一按外部团队二进制依赖处理。
- 本仓库只维护链接、部署和集成验证，不维护其源码实现。

## 2.5 模块功能介绍入口

- `hdi`、`api`、`app` 的功能清单与能力分解，统一见：
  - `docs/architecture/hdi-api-app-functional-overview.md`

## 3. 控制链路设计（CLI -> CMD_SERVER -> APP）

1. `cli` 封装命令 payload 并发送到 `cmd_server`。
2. `cmd_server` 鉴权/限流/路由，写入 pending 表。
3. 目标业务进程（`prog_pcr02` 或 `prog_product_test`）消费命令并执行 provider。
4. `cmd_server` 回收 pending，响应给 `cli`。
5. 若超时或无 handler，返回统一错误语义。

## 4. 构建设计要点

- 根 `Makefile` 自动发现 `*.mk` 模块并生成目标。
- app 模块统一走 `build/app_common.mk + app_3rdparty.mk + app_sigmastar.mk`。
- 白名单外模块（如 `wifi_manager`）即使参与构建，也按外部依赖处理，不纳入本仓库源码治理。

## 5. 当前边界风险与约束

- `pcr02/dep.mk` 声明了 `modules/task|iot|ai|navigation`，当前仓库目录缺失；实际由 `libs/arm/libs/.../static/*.a` 提供。
- `pcr02/main.cpp` 直接 include 缺失目录头文件，要求构建环境提供外部头文件映射。
- 结论：该仓库是“源码 + 预编译库”混合交付形态，不能按纯源码仓库治理。
