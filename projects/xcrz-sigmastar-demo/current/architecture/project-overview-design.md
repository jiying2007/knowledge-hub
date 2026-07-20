---
doc_type: architecture
knowledge_type: model
maturity: verified
created: 2026-05-13
last_updated: 2026-05-13
related:
- diag-command-architecture-final.md
- project-detailed-design.md
- project-core-module-design.md
id: pcr02-project-overview-design
title: PCR02 项目概要设计
kind: project-current
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/current/architecture/project-overview-design.md
scope: project-specific
visibility: team-internal
status: archived
owner: team-core
source:
  type: retired-source-provenance
  source_id: pcr02-project-docs
  source_path: architecture/project-overview-design.md
  source_sha256: 784ec0d2e2eb3eaee647ab0fdc7d4d9dadf8a43d54f1cbb7293de2c92f44bc34
review_after: '2026-10-16'
review_status: delegated-review-closed-reference-boundary
promotion: none
promotion_decision: none; archived reference boundary, no owner decision generated
tags:
- pcr02
- current
- architecture
- overview
validation_refs:
- projects/xcrz-sigmastar-demo/current/architecture/project-overview-design.md
- rtk bash tools/knowledge-check.sh --dry-run
- artifacts/manifests/knowledge-hub-complete-delivery-closure-20260701.md
- artifacts/manifests/knowledge-hub-complete-delivery-closure-20260701.jsonl
- Makefile
evidence_refs:
- artifacts/manifests/knowledge-hub-complete-delivery-closure-20260701.md
- artifacts/manifests/knowledge-hub-complete-delivery-closure-20260701.jsonl
created_at: '2026-06-16'
updated_at: '2026-07-19'
summary_zh: 本文档定义当前仓库的最终态总体结构，覆盖以下范围：。该条目当前为 archived retired-source provenance，仅作历史项目材料检索入口，不代表当前项目事实、active 决策或 owner 签收。
---

# PCR02 项目概要设计

## 1. 目标与范围

本文档定义当前仓库的最终态总体结构，覆盖以下范围：

- 应用层：`cli`、`cmd_server`、`daemon`、`app_product_test`、`app_ota`、`pcr02`
- 公共模块层（纳管）：`modules/hdi`、`modules/api`、`modules/app`、`modules/sensor`、`modules/proto`、`modules/proto_c`
- 构建交付层：`Makefile` + `build/*.mk` + `release/` 装配路径

说明：需求中提到的 `app_product` 在本仓库对应目录为 `app_product_test/`，产物为 `prog_product_test`。
说明：`pcr02` 是公共主应用（集成入口），并非单一业务私有应用。

## 2. 运行体拓扑

主运行体由 `daemon` 编排：

- `prog_daemon`：常驻进程，读取 `/var/run/media/mmcblk0p1/vstrong/daemon.ini` 决定模式。
- `prog_cmd_server`：命令网关与路由中心，提供 IPC 命令通道。
- `prog_pcr02`：APP 模式主业务进程。
- `prog_product_test`：PRODUCT_TEST 模式进程。
- `prog_cli`：运维/调试命令行客户端，按需调用。

模式切换关系：

1. `RUN_MODE_APP`：`CmdServer + App(prog_pcr02)`。
2. `RUN_MODE_PRODUCT_TEST`：`CmdServer + ProductTest(prog_product_test)`。

## 3. 分层与依赖边界

稳定边界：

- `hdi`：硬件与 OS 适配层（GPIO/UART/I2C/VI/AI/AO/OS 包装）。
- `api`：基础算法、容器、网络、协议、配置与工具能力层。
- `app`：应用聚合与诊断编排层（`app_diag` 运行时、provider 注册、命令桥接）。

依赖方向：

1. `hdi ->` 不依赖 `api/app`。
2. `api ->` 不依赖 `app`。
3. `app ->` 可依赖 `hdi` 与 `api`。
4. `cli/cmd_server/daemon/app_product_test` 通过 `dep.mk` 统一依赖 `hdi+api+app`。

模块治理边界：

1. `modules` 下仅 `hdi/api/app/sensor/proto/proto_c` 纳入本仓库治理。
2. 其他 `modules/*` 视为外部团队交付依赖，不在本仓库内做源码治理。

## 4. 构建与交付骨架

`make all` 总流程（根 `Makefile`）：

1. 执行依赖模块构建（`depend_internal`）。
2. 执行应用模块 `*_app_all`（格式检查 + 链接可执行文件）。
3. 生成产物到 `out/<arch>/app/`。

`make install` 总流程：

1. 装配二进制到 `release/`。
2. 同步 `MODULE_REL_FILES/MODULE_REL_LIB/MODULE_REL_BIN` 到交付目录。
3. 输出部署目录 `.../release/bin/robot_pcr02/`。

## 5. 核心设计约束

- 进程职责单一：`cmd_server` 不承载业务实现，`daemon` 不承载业务命令处理。
- 协议统一：控制面以 IPC 消息头+payload 传递命令，CLI 不内嵌业务实现。
- 文档终态化：历史方案不再作为生效依据，所有新变更回写 `docs/architecture/` 与 `docs/runbooks/`。
