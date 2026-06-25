---
title: SigmaStar 平台能力矩阵与选型规则
doc_type: architecture
knowledge_type: decision
maturity: verified
status: active
owner: team-core
created: 2026-05-15
last_updated: 2026-05-15
tags: [sigmastar, capability, matrix, decision]
related: [sigmastar-platform-internal-overview.md, ../runbooks/sigmastar-platform-development-workflow.md, ../standards/sigmastar-platform-topic-catalog.md]
validation_refs: [examples/sigmastar/SSC305_sigdoc/platform, examples/sigmastar/SSU9383CM_sigdoc/platform, examples/sigmastar/SSU9383CM_sigdoc/customer]
---

# SigmaStar 平台能力矩阵与选型规则

## 1. 能力矩阵

| 能力域 | SSC305 | SSU9383CM | 选型建议 |
| --- | --- | --- | --- |
| 环境搭建与基础构建 | 完整 | 完整 | 两者均可，优先按现有产线与工具链一致性选择 |
| 启动链与分区治理 | 完整 | 完整 | 若强调 eMMC/分区量产流程，优先 SSU9383CM |
| 基础外设 BSP | 完整 | 完整 | 通用外设两者等价，按板级资源选型 |
| 双系统协同 | 强（DualOS/CM4/RTOS） | 中（RTOS/RISC-V） | 强实时协同优先 SSC305 |
| RISC-V 协处理 | 弱 | 强 | 需要 RISC-V 生态优先 SSU9383CM |
| 媒体 MI 接口 | 完整 | 完整 | 若涉及 GFX/IQServer/PSPI，优先 SSU9383CM |
| ISP/3A 调试 | 完整 | 完整 | 两者可用，按传感器与画质调参链选择 |
| 显示链路（Panel/DispCam） | 中 | 强 | 有显示终端与点屏需求优先 SSU9383CM |
| 音频算法库 | 强（算法种类更全） | 中 | 音频算法试验优先 SSC305 |
| 视觉 AI 算法 | 强（IPU_Algo 分类完整） | 中（样例导向） | 自研算法集成优先 SSC305 |
| 网络与无线运维 | 中 | 强（WLAN/P2P/DNS/DHCP/工具链） | 联网产品与远程运维优先 SSU9383CM |
| 工厂烧录与量产工具 | 中 | 强（vendor/usb factory tool） | 量产流程成熟度优先 SSU9383CM |
| 安全与存储加固 | 中 | 强（device mapper/加密链） | 强安全存储需求优先 SSU9383CM |

## 2. 快速决策树

1. 需求核心是“双系统与低功耗协同” -> 选 SSC305。
2. 需求核心是“显示+联网+量产交付” -> 选 SSU9383CM。
3. 需求核心是“音频/视觉算法快速接入” -> 先选 SSC305，再评估量产迁移成本。
4. 需求核心是“工厂化升级、Vendor 数据、运维工具链” -> 选 SSU9383CM。

## 3. 组合策略（推荐）

1. 研发验证阶段：优先使用 SSC305 快速验证算法与系统协同。
2. 量产工程阶段：优先切换/并行维护 SSU9383CM 交付链路。
3. 跨平台代码治理：抽象公共能力到 `modules/hdi`、`modules/api`，平台差异放在适配层。

## 4. 风险提示

1. 不同平台的启动参数、分区布局、升级方式不可直接复用。
2. 传感器、显示面板、音频链路配置存在板级耦合，迁移需重新校验。
3. RISC-V/CM4/RTOS 侧接口不可假设一致，必须按平台分治封装。

## 5. 验收基线

- 构建：`rtk make -j8 all`、`rtk make install` 成功。
- 运行：`daemon + cmd_server + 主业务进程` 可正常拉起。
- 功能：至少完成存储、传感器、音频/显示、网络四域 smoke 测试。
- 运维：完成升级回滚与日志回收路径验证。
