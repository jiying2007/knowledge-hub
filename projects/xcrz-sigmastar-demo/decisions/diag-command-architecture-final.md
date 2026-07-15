---
title: PCR02 诊断命令架构终版（唯一主文档）
doc_type: architecture
knowledge_type: decision
maturity: verified
status: archived
owner: team-core
created: 2026-05-12
last_updated: 2026-05-13
tags: [diag, architecture, pcr02]
---

# PCR02 诊断命令架构终版（唯一主文档）

## 1. 目的与范围

本文件是诊断命令体系的唯一主文档，用于定义当前生效的终态架构、边界约束、生命周期语义、测试门禁与演进规则。  
项目级架构与构建主文档统一维护在 `docs/architecture/` 与 `docs/runbooks/`。

配套文档：

- 项目概要：`docs/architecture/project-overview-design.md`
- 项目详设：`docs/architecture/project-detailed-design.md`
- 核心模块：`docs/architecture/project-core-module-design.md`
- 模块目录：`docs/architecture/module-catalog.md`
- `hdi/api/app` 功能总览：`docs/architecture/hdi-api-app-functional-overview.md`

适用范围：

- `cli`
- `cmd_server`
- `daemon`
- `modules/hdi`
- `modules/api`
- `modules/app`
- `pcr02`
- `app_product_test`

说明：

- `modules/sensor`、`modules/proto`、`modules/proto_c` 属于项目纳管模块，
  但不属于本“诊断命令架构”主文档的核心覆盖对象，相关设计见项目架构文档。

## 2. 架构终态

### 2.1 控制面与执行面分离

- `cmd_server`：仅承担 gateway/registry/router；不执行业务诊断逻辑。
- 业务执行：仅在业务进程内 `app_diag runtime` 完成。
- `daemon`：仅负责进程编排，不承载诊断业务。

### 2.2 分层边界

- 允许依赖方向固定为：`app -> api -> hdi`（`app` 可按需直连 `hdi`）。
- `hdi` 不得调用 `api/app`。
- `api` 不得调用 `app`。
- 诊断能力由 owner 模块声明并管理生命周期，不允许聚合模块跨 owner 直接管理共享资源 Init/DeInit。

### 2.3 协议与命令模型

- 统一协议入口：`CMD_SYS_DYNAMIC_CMD`。
- 统一 payload：`<diag.command> [json]`（canonical text payload）。
- `cli` 只做发现、参数规范化与 payload 发送，不维护持续膨胀的业务分支语法。

## 3. 生命周期与可观测语义

### 3.1 Provider 生命周期

- provider 上线：`ModuleUp`
- provider 下线：`ModuleDown`
- 命令上线：`CommandUp`
- 命令下线：`CommandDown`

所有命令可见性必须与 owner 生命周期一致，禁止“命令在线但资源未就绪”。

### 3.2 错误语义

- 无活跃处理者：`no_active_handler`
- 请求参数不合法：`bad_request`
- 路由超时：`route_timeout`

不保留 legacy 兼容错误语义与双协议分支。

## 4. Provider 组织与实现约束

### 4.1 文件组织

- provider 采用“按 owner 模块独立实现”。
- 禁止聚合式测试 provider 继续扩张。
- 新增命令必须落在 owner provider 对应文件，不得写入网关层。

### 4.2 资源初始化约束

- 模块资源只由 owner 模块生命周期驱动。
- 需要外部 bring-up/down 的能力，必须通过显式状态机与引用计数保护，禁止重复初始化和野蛮反初始化。

## 5. 测试与门禁

### 5.1 最小验收

1. 构建（按变更子仓库定向执行）
2. 边界扫描（确认无越层依赖/无 gateway 业务执行）
3. 规范检查（命名、目录、接口一致性）

### 5.2 运行验证

- APP 模式：`diag.sys.list.run`、核心业务命令、owner 上下线、异常回收。
- PRODUCT_TEST 模式：白名单命令、资源隔离、无越权模块初始化。

## 6. 变更治理规则

1. 本文件维护“当前生效终态”，不记录阶段性迁移细节。
2. 阶段性内容以 `docs/plans/`、`docs/reports/` 记录，稳定后回写架构主文档。
3. 新变更采用增量文档记录，并在稳定后回写本文件。
4. 不因短期兼容需求破坏边界；若必须临时策略，需明确过期条件与清理计划。

## 7. 历史文档归档索引

- 2026-05-07 早期诊断阶段历史资料：已按治理策略清理，不再保留
