---
title: SSC305 sigdoc 资料定位方法
doc_type: runbook
knowledge_type: process
maturity: draft
status: active
owner: team-core
created: 2026-05-28
last_updated: 2026-05-28
tags: [ssc305, sigdoc, lookup, topic-catalog]
related: [../standards/ssc305-feishu-knowledge-map.md, ../standards/sigmastar-platform-topic-catalog.md, ../architecture/sigmastar-platform-internal-overview.md, ../archive/sigmastar/manifest.md]
validation_refs: [../archive/sigmastar/manifest.csv, ../standards/sigmastar-platform-topic-catalog.md]
---

# SSC305 sigdoc 资料定位方法

## 1. 适用场景

当问题来自 SSC305 平台能力、官方接口、工具链或移植流程时，先按本文定位资料，再进入代码或设备调试。

典型场景：

1. 不确定某个能力属于 BSP、MI、ISP、算法还是 DualOS/CM4。
2. 需要知道 `SSC305_sigdoc` 中对应主题路径。
3. 需要把现场问题转成可检索、可追溯的知识库条目。
4. 需要给测试、现场或新成员指明应该先看哪篇资料。

## 2. 输入材料

定位前至少收集：

| 输入 | 示例 |
| --- | --- |
| 平台 | `SSC305` |
| 能力域 | `BSP`、`MI`、`ISP`、`IPU_Algo`、`Audio_algo`、`DualOS`、`CM4`、`RTOS` |
| 问题类型 | 移植、构建、调试、优化、交付、回归 |
| 设备证据 | 启动日志、模块日志、返回码、配置片段、现象截图 |
| 项目上下文 | 目标进程、构建产物路径、设备型号、sensor 或外设型号 |

## 3. 总体定位流程

1. 先判断能力域。
2. 在 `docs/standards/sigmastar-platform-topic-catalog.md` 查 SSC305 主题清单。
3. 记录内部主题 ID、主题名称和 sigdoc 路径。
4. 对照项目仓源码、构建脚本或设备日志验证是否适用。
5. 输出资料定位结论，不直接把官方原文复制到知识库。

## 4. 能力域判定表

| 现象或需求 | 优先能力域 | 典型主题 |
| --- | --- | --- |
| GPIO、I2C、SPI、PWM、UART、RTC、USB、Flash、SD/eMMC | `platform/BSP` | `platform.BSP.*_zh` |
| Sensor 驱动、sensor 支持列表、MIPI 输入 | `platform/BSP` + `platform/MI` | `Sensor_Porting_Guide_zh`、`sensor_support_list_zh`、`platform.MI.sensor_zh` |
| VIF、SCL、ISP、VENC、RGN、LDC、IVE | `platform/MI` + `platform/ISP` | `platform.MI.vif_zh`、`platform.MI.isp_zh`、`platform.ISP.iford.*` |
| AI 推理、分类、检测、人脸、姿态、人像分割 | `platform/IPU_Algo` | `platform.IPU_Algo.det_zh`、`platform.IPU_Algo.cls_zh` |
| AEC、AGC/APC、BF、KWS、SSL、VAD、SRC | `platform/Audio_algo` | `platform.Audio_algo.*_zh` |
| 快启、STR、TTFF、RTOS early init | `customer/DualOS` | `STR_Time_consuming_Guide_zh`、`rtos_earlyinit_guide_zh` |
| CM4 GPIO/I2C/PWM/RTC/PM power | `platform/CM4` | `platform.CM4.*_zh` |
| Boot、分区、OTA、安全启动 | `customer/Common/Development` | `bootflow_zh`、`partitionfile_zh`、`ota_zh`、`Security_Boot_zh` |

## 5. 常用定位卡片

### 5.1 Sensor 移植

查找顺序：

1. `customer.Common.Development.Sensor_Porting_Guide_zh`
2. `platform.BSP.sensor_support_list_zh`
3. `platform.MI.sensor_zh`
4. `platform.MI.vif_zh`
5. `platform.ISP.iford.api_zh`

输出结论时写清：

1. sensor 型号与接口。
2. MCLK、reset、power、I2C 地址和上电顺序。
3. VIF/ISP 输入分辨率、帧率、格式。
4. 当前项目实际配置路径和日志证据。

### 5.2 媒体链路异常

查找顺序：

1. `platform.MI.vif_zh`
2. `platform.MI.scl_zh`
3. `platform.MI.isp_zh`
4. `platform.MI.venc_zh`
5. `platform.MI.rgn_zh`

排查重点：

1. 输入是否出帧。
2. pixel format、stride、分辨率是否一致。
3. 队列是否阻塞或丢帧。
4. 编码、OSD、显示或 AI 是否消费异常。

### 5.3 AI 算法接入

查找顺序：

1. `platform.MI.ipu_zh`
2. `platform.IPU_Algo.det_zh`
3. `platform.IPU_Algo.cls_zh`
4. `platform.IPU_Algo.fr_zh`
5. `platform.CV_guide.*`

排查重点：

1. 模型输入尺寸、颜色空间、归一化参数。
2. 前处理和后处理是否与模型一致。
3. IPU 内存、线程、buffer 生命周期。
4. 模型版本和运行库版本是否匹配。

### 5.4 DualOS/CM4/低功耗

查找顺序：

1. `customer.DualOS.Development.arch_zh`
2. `customer.DualOS.Development.dualos_customer_development_guide_zh`
3. `customer.DualOS.Development.TTFF-TTUFF-TTCL_guide_zh`
4. `customer.DualOS.Development.rtos_earlyinit_guide_zh`
5. `platform.CM4.pm_power_zh`

排查重点：

1. Linux、RTOS、CM4 的职责边界。
2. 资源归属与多进程管理。
3. 快启阶段耗时拆分。
4. 电源域、唤醒源和 PM 交互。

## 6. 输出模板

定位结论建议使用以下模板：

```md
## 资料定位结论

- 平台：SSC305
- 归档实体：sigmastar-ssc305-20260516-v2
- 能力域：
- 问题类型：
- 命中的主题 ID：
- sigdoc 路径：
- 项目验证入口：
- 仍需补充的证据：
```

## 7. 失败路径

1. 主题目录中找不到：先换能力域搜索，再查相邻域，不要直接假设“不支持”。
2. 官方主题存在但项目无实现：输出为“平台资料存在，项目适配待确认”。
3. 项目行为与官方资料不一致：优先检查 SDK 版本、芯片配置、板级差异和项目补丁。
4. 需要引用原文细节：只在受控内部环境查看归档实体，知识库正文保留摘要和路径。

## 8. 验证方式

资料定位本身不等于功能验证。完成定位后必须进入对应方法文档：

1. 构建和交付问题：`ssc305-build-burn-upgrade-method.md`
2. 运行期工具和 crash 问题：`ssc305-debug-toolchain-method.md`
3. 媒体、Sensor、AI 问题：`ssc305-media-sensor-ai-triage-method.md`
4. DualOS、CM4、低功耗问题：`ssc305-dualos-cm4-low-power-method.md`
5. 自动化回归问题：`ssc305-diag-regression-method.md`
