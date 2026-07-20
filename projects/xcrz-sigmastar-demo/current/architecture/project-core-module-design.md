---
doc_type: architecture
knowledge_type: model
maturity: verified
created: 2026-05-13
last_updated: 2026-05-13
related:
- project-overview-design.md
- project-detailed-design.md
- module-catalog.md
- hdi-api-app-functional-overview.md
id: pcr02-core-module-design
title: PCR02 核心模块设计
kind: project-current
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/current/architecture/project-core-module-design.md
scope: project-specific
visibility: team-internal
status: archived
owner: team-core
source:
  type: retired-source-provenance
  source_id: pcr02-project-docs
  source_path: architecture/project-core-module-design.md
  source_sha256: 46ab0cc328d076b216dd36cc7af7009b05c88d7744da008b64a4f1a28b21b207
review_after: '2026-10-16'
review_status: delegated-review-closed-reference-boundary
promotion: none
promotion_decision: none; archived reference boundary, no owner decision generated
tags:
- pcr02
- current
- modules
- core
validation_refs:
- projects/xcrz-sigmastar-demo/current/architecture/project-core-module-design.md
- rtk bash tools/knowledge-check.sh --dry-run
- artifacts/manifests/knowledge-hub-complete-delivery-closure-20260701.md
- artifacts/manifests/knowledge-hub-complete-delivery-closure-20260701.jsonl
evidence_refs:
- artifacts/manifests/knowledge-hub-complete-delivery-closure-20260701.md
- artifacts/manifests/knowledge-hub-complete-delivery-closure-20260701.jsonl
created_at: '2026-06-16'
updated_at: '2026-07-19'
summary_zh: 把“控制面”和“执行面”分离，保持命令系统可扩展。 - 通过 hdi/api/app 分层实现跨业务复用。 - 用模块化生命周期管理替代耦合式初始化逻辑。 - 明确仓库治理边界：仅纳管白名单模块，其余按外部依赖处理。该条目当前为
  archived retired-source provenance，仅作历史项目材料检索入口，不代表当前项目事实、active 决策或 owner 签收。
---

# PCR02 核心模块设计

## 1. 设计目标

- 把“控制面”和“执行面”分离，保持命令系统可扩展。
- 通过 `hdi/api/app` 分层实现跨业务复用。
- 用模块化生命周期管理替代耦合式初始化逻辑。
- 明确仓库治理边界：仅纳管白名单模块，其余按外部依赖处理。

## 2. 核心模块分组

## 2.1 诊断执行核心（`modules/app/src/app_diag`）

- `app_diag_center`：统一入口，编排上下线与分发。
- `app_diag_registry`：维护命令与 provider 注册关系。
- `app_diag_dispatcher`：按命令路由到对应处理函数。
- `provider/*`：面向业务能力封装执行单元（perf/ai/uart/archive 等）。

## 2.2 诊断数据提供者（`modules/app/src/app_diag/provider/api` + `modules/app/src/app_diag/provider/hdi`）

- `app_diag_api_*_provider`：APP runtime provider，通过 API 公共接口从网络、事件、媒体、DVR、WS 等子域提取指标。
- `app_diag_hdi_*_provider`：APP runtime provider，通过 HDI 公共接口从 OS、VI、AO、AI 等硬件/系统层提取指标。
- 组合方式：`app` 层统一编排，`api/hdi` 只负责提供能力，不反向依赖。

## 2.3 进程协作核心（`cmd_server` + `daemon`）

- `cmd_server`：路由、限流、超时、错误语义统一。
- `daemon`：模式切换与进程存活治理，避免业务进程自守护。

## 2.4 公共主应用核心（`pcr02`）

- `Application`：应用总生命周期钩子。
- `Sensor/Task/IoT/WiFi/Bridge/Navigation`：按序初始化，失败即回滚。
- 线程模型：主线程调度 + `common::ThreadPool` 常驻线程池。
- 角色定位：公共主应用，负责跨模块集成与运行编排。

## 2.5 模块治理边界

纳管白名单：

- `modules/hdi`
- `modules/api`
- `modules/app`
- `modules/sensor`
- `modules/proto`
- `modules/proto_c`

非纳管范围：

- 其他 `modules/*` 均按外部团队交付依赖处理，不纳入本仓库源码治理。

## 2.6 核心功能总览入口

- `hdi/api/app` 的功能级介绍统一维护在：
  - `docs/architecture/hdi-api-app-functional-overview.md`
- 本文只保留架构边界与层次关系，避免功能清单和架构约束分散。

## 3. 生命周期策略

1. 启动：
   - `daemon` 启动 `cmd_server` 与目标业务进程。
   - 业务进程启动后注册诊断 provider/commands。
2. 运行：
   - `cmd_server` 处理请求并将命令转发到活跃 provider。
   - `app_diag` 维护 provider 状态与命令可见性。
3. 停止：
   - SIGTERM 触发模块按逆序回收。
   - `cmd_server` 释放 pending 请求与 IPC 资源。

## 4. 可扩展规则

- 新增诊断能力：优先新增 provider 文件，不在 `cmd_server` 增业务分支。
- 新增模块：必须声明 `dep.mk`，并保证依赖方向不逆流。
- 新增第三方库：必须在构建说明与三方引用文档同步登记。
