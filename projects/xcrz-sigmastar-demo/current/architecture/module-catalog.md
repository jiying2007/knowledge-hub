---
doc_type: architecture
knowledge_type: model
maturity: verified
created: 2026-05-13
last_updated: 2026-05-13
related:
- project-core-module-design.md
- hdi-api-app-functional-overview.md
- ../runbooks/project-build-and-deploy-guide.md
id: pcr02-module-catalog
title: PCR02 模块目录与职责清单
kind: project-current
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/current/architecture/module-catalog.md
scope: project-specific
visibility: team-internal
status: archived
owner: team-core
source:
  type: retired-source-provenance
  source_id: pcr02-project-docs
  source_path: architecture/module-catalog.md
  source_sha256: 7aecb49224bbf05951372c980c218c1a8ed12e34a5452bb48e0cb02e8f828bb5
review_after: '2026-10-16'
review_status: delegated-review-closed-reference-boundary
promotion: none
promotion_decision: none; archived reference boundary, no owner decision generated
tags:
- pcr02
- current
- module
- catalog
validation_refs:
- projects/xcrz-sigmastar-demo/current/architecture/module-catalog.md
- rtk bash tools/knowledge-check.sh --dry-run
- artifacts/manifests/knowledge-hub-complete-delivery-closure-20260701.md
- artifacts/manifests/knowledge-hub-complete-delivery-closure-20260701.jsonl
- modules
evidence_refs:
- artifacts/manifests/knowledge-hub-complete-delivery-closure-20260701.md
- artifacts/manifests/knowledge-hub-complete-delivery-closure-20260701.jsonl
created_at: '2026-06-16'
updated_at: '2026-07-19'
summary_zh: 1. modules 下仅纳管 hdi/api/app/sensor/proto/proto_c 六个模块。 2. 白名单外模块不纳入本仓库研发治理范围。 3. 白名单外模块统一按“外部团队二进制依赖”处理。该条目当前为
  archived retired-source provenance，仅作历史项目材料检索入口，不代表当前项目事实、active 决策或 owner 签收。
---

# PCR02 模块目录与职责清单

## 1. 纳管源码模块（治理白名单）

| 模块 | 目录 | 主要职责 | 产物/被依赖场景 |
|---|---|---|---|
| `hdi` | `modules/hdi` | 硬件与 OS 抽象层 | `libhdi.a`，被 app/api 与应用进程依赖 |
| `api` | `modules/api` | 基础能力（网络/容器/协议/算法） | `libapi.a`，被 app 与应用进程依赖 |
| `app` | `modules/app` | 业务聚合与诊断运行时 | `libapp.a`，被应用进程依赖 |
| `sensor` | `modules/sensor` | 传感器模块实现 | `libsensor.a` |
| `proto` | `modules/proto` | protobuf C++ 协议 | `libproto.a` |
| `proto_c` | `modules/proto_c` | nanopb C 协议 | `libproto_c.a` |

纳管边界（强制）：

1. `modules` 下仅纳管 `hdi/api/app/sensor/proto/proto_c` 六个模块。
2. 白名单外模块不纳入本仓库研发治理范围。
3. 白名单外模块统一按“外部团队二进制依赖”处理。

功能介绍索引：

- `hdi/api/app` 功能级说明：`docs/architecture/hdi-api-app-functional-overview.md`

## 2. 应用模块

| 应用 | 目录 | 可执行文件 | 描述 |
|---|---|---|---|
| `cli` | `cli` | `prog_cli` | 命令行客户端 |
| `cmd_server` | `cmd_server` | `prog_cmd_server` | 命令网关与路由 |
| `daemon` | `daemon` | `prog_daemon` | 进程守护与模式切换 |
| `app_product_test` | `app_product_test` | `prog_product_test` | 产测模式进程 |
| `app_ota` | `app_ota` | `prog_ota` | OTA 相关应用 |
| `pcr02` | `pcr02` | `prog_pcr02` | 公共主应用（集成入口） |

## 3. 非纳管外部模块（按外部团队依赖治理）

### 3.1 `pcr02/dep.mk` 声明但当前仓库缺失源码目录

- `modules/task`
- `modules/iot`
- `modules/ai`
- `modules/navigation`

实际通过预编译库提供（`libs/arm/libs/glibc/11.1.0/static`）：

- `libtask.a`
- `libiot.a`
- `libai.a`
- `libnavigation.a`

### 3.2 仓库可见但不纳管模块（仍按外部团队依赖治理）

- `modules/common`
- `modules/bridge`
- `modules/wifi_manager`
- `modules/wifi`
- `modules/mp4`

治理规则：

1. 这些模块在本仓库按“外部交付依赖”管理。
2. 接口变更必须在上游仓库完成并同步二进制与头文件。
3. 本仓库只维护链接顺序与集成验证，不直接修改其实现。
