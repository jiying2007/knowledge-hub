---
title: SigmaStar 平台内部技术总览
doc_type: architecture
knowledge_type: model
maturity: verified
status: archived
searchable: false
owner: team-core
created: 2026-05-15
last_updated: 2026-05-15
tags: [sigmastar, ssc305, ssu9383cm, architecture]
related: [../runbooks/sigmastar-platform-development-workflow.md, ../standards/sigmastar-platform-topic-catalog.md, ../archive/sigmastar/manifest.md]
validation_refs: [examples/sigmastar/SSC305_sigdoc, examples/sigmastar/SSU9383CM_sigdoc]
---

# SigmaStar 平台内部技术总览

## 1. 文档目标

- 将 `SSC305` 与 `SSU9383CM` 两套平台资料统一为团队内部知识模型。
- 面向后续 Codex 调用提供稳定的“能力域 + 路径 +决策规则”入口。
- 不复述外部文档原文，统一改写为团队可执行表达。

## 2. 平台画像

### 2.1 SSC305 平台定位

- 面向 IPC/IoT 场景，覆盖 Linux + DualOS + CM4 协作能力。
- 在团队嵌入式项目中更偏“低功耗、双系统协同、诊断能力扩展”路线。
- 重点能力域：`DualOS`、`CM4`、`RTOS`、`IPU_Algo`、`Audio_algo`。

### 2.2 SSU9383CM 平台定位

- 面向显示与多媒体集成场景，覆盖 Linux + RISC-V/RTOS + DispCam 方案。
- 在团队嵌入式项目中更偏“显示链路、网络接入、工厂化交付”路线。
- 重点能力域：`DispCam`、`DisplayPanels`、`WLAN/P2P`、`vendor_burn`、`usb_factorytool_update`。

## 3. 统一技术分层

1. 硬件抽象层：`platform/BSP`（GPIO/UART/I2C/SPI/PWM/RTC/存储/USB/传感器/寄存器）。
2. 媒体接口层：`platform/MI`（SYS、SCL、VIF、ISP、IPU、DISP、RGN、FB、IVE 等）。
3. 算法能力层：`platform/Audio_algo`、`platform/IPU_Algo`、`platform/CV_guide`。
4. 系统协同层：`DualOS/CM4/RTOS`（SSC305）与 `RISC-V/RTOS`（SSU9383CM）。
5. 产品工程层：环境搭建、编译打包、升级烧录、功耗调优、日志与排障。

## 4. 典型开发闭环

1. 环境准备：工具链、SDK 目录、构建变量、目标板连接。
2. 系统构建：按芯片与产品配置执行 `rtk make` 构建与安装。
3. 启动与分区：确认启动链、分区布局、升级包结构与回滚策略。
4. 子系统拉通：存储、传感器、音频、显示、网络逐域验证。
5. 算法接入：音频/视觉算法按模型输入输出约束完成接入测试。
6. 诊断与调优：功耗、内存、时延、稳定性、异常恢复闭环。
7. 量产交付：工厂烧录、版本发布、现场升级、问题回收。

## 5. 平台差异主线

1. 多核协作路线不同：SSC305 侧重 `CM4 + DualOS`，SSU9383CM 侧重 `RISC-V + RTOS`。
2. 显示链路侧重点不同：SSU9383CM 提供更完整的 panel/点屏与 DispCam 方案。
3. 网络与运维能力密度不同：SSU9383CM 在 WLAN/P2P/SSH/SCP/FactoryTool 资料更集中。
4. AI 能力组织不同：SSC305 单独提供 `IPU_Algo` 分类体系，SSU9383CM 更偏应用样例。

## 6. 内部知识组织规范（供 Codex 调用）

- 统一使用“能力域”作为一级索引：`bsp`、`mi`、`isp`、`audio_algo`、`ai_algo`、`system_coop`、`product_ops`。
- 需求解析先判断“平台 + 能力域 + 阶段（开发/调试/交付）”。
- 涉及跨域问题时，先完成依赖顺序判断：`BSP -> MI/ISP -> Algo -> App`。
- 进入修改前先检查具体项目仓的实现目录与构建手册，本知识库只提供平台模型、流程和工具入口。

## 7. 与仓库现有文档关系

- 构建与部署执行细节：以具体项目仓的构建手册为准。
- 项目分层与治理边界：以具体项目仓的架构文档为准。
- 核心模块职责：以具体项目仓的架构文档为准。
- 平台完整主题索引：`docs/standards/sigmastar-platform-topic-catalog.md`。
