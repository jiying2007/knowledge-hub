---
title: SigmaStar 平台开发与交付工作流
doc_type: runbook
knowledge_type: process
maturity: verified
status: active
owner: team-core
created: 2026-05-15
last_updated: 2026-05-15
tags: [sigmastar, workflow, build, debug, release]
related: [../architecture/sigmastar-platform-internal-overview.md, ../architecture/sigmastar-platform-capability-matrix.md, ../standards/sigmastar-platform-topic-catalog.md, ../archive/sigmastar/manifest.md]
validation_refs: [Makefile, examples/sigmastar/SSC305_sigdoc, examples/sigmastar/SSU9383CM_sigdoc]
---

# SigmaStar 平台开发与交付工作流

## 1. 适用范围

- 适用于本仓库基于 `SSC305` / `SSU9383CM` 的开发、调试、交付。
- 目标是把平台能力转化为本项目可重复执行流程。

## 2. 阶段 0：任务分流

1. 明确目标平台：`ssc305` 或 `ssu9383cm`。
2. 明确任务域：`bsp / mi / isp / algo / system / delivery`。
3. 明确验收标准：功能、性能、稳定性、可维护性。

## 3. 阶段 1：环境与构建

1. 检查工具链、环境变量、第三方依赖路径。
2. 执行标准构建：

```bash
rtk make -j8 all
rtk make install
```

3. 若为平台专项改动，新增定向构建与最小可运行镜像验证。

## 4. 阶段 2：系统基线拉通

1. 启动链验证：上电 -> 引导 -> 根文件系统 -> 业务进程。
2. 分区与升级基线：镜像布局、版本号、回滚策略。
3. 进程基线：`prog_daemon`、`prog_cmd_server`、`prog_pcr02/prog_product_test`。

## 5. 阶段 3：能力域联调

1. BSP：GPIO/UART/I2C/SPI/PWM/RTC/USB/存储/传感器。
2. MI/ISP：VIF、SCL、ISP、IPU、DISP、RGN、FB 等链路按依赖顺序联调。
3. 算法：音频/视觉算法单元测试 + 端到端场景验证。
4. 系统协同：
- SSC305：DualOS/CM4/RTOS 协作、低功耗与快启路径。
- SSU9383CM：RISC-V/RTOS 协作、显示与网络运维链路。

## 6. 阶段 4：调优与问题闭环

1. 性能：启动时延、关键链路延迟、资源占用。
2. 稳定性：长稳、压力、异常恢复。
3. 可靠性：断电、重启、升级失败回滚、配置损坏恢复。
4. 常见排障入口：
- 构建失败：依赖/链接顺序/工具链版本。
- 运行失败：进程编排、设备节点、权限与驱动初始化。
- 算法异常：输入格式、模型版本、线程并发与内存布局。

## 7. 阶段 5：交付与量产准备

1. 版本封版：产物、配置、升级包、变更说明一致。
2. 工厂流程：烧录脚本、序列号、校验流程、回读校验。
3. 现场运维：日志收集、远程升级、紧急回滚方案。

## 8. 验收检查清单

1. 构建通过：全量 + 定向。
2. 基线通过：启动、核心进程、关键外设。
3. 场景通过：业务关键路径。
4. 质量通过：性能、稳定性、安全项。
5. 文档通过：本次变更已回写 `architecture/runbooks/standards`。
