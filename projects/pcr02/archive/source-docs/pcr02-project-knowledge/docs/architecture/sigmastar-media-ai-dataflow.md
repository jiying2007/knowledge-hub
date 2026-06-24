---
title: SigmaStar 媒体与 AI 数据流模型
doc_type: architecture
knowledge_type: model
maturity: verified
status: active
owner: team-core
created: 2026-05-18
last_updated: 2026-05-18
tags: [sigmastar, media, ai, dataflow, buffer]
related: [sigmastar-platform-internal-overview.md, sigmastar-platform-capability-matrix.md, ../runbooks/sigmastar-media-pipeline-triage-guide.md, ../runbooks/yolo-ai-vision-deployment-guide.md]
validation_refs: [../runbooks/sigmastar-media-pipeline-triage-guide.md, ../runbooks/yolo-ai-vision-deployment-guide.md]
---

# 背景

本文定义 SigmaStar 媒体链路与 AI 推理链路的统一数据流模型，用于排查黑屏、花屏、延迟、掉帧、模型输入异常和 buffer 泄漏。本文不替代 SDK API 文档，只固定团队排查时的抽象边界。

# 数据流分层

典型链路按职责分为七层：

1. Sensor：输出原始帧，关注供电、时钟、I2C、MCLK、分辨率、帧率。
2. VIF：接收 sensor 数据，关注 lane、format、drop、overflow。
3. ISP：完成 3A、降噪、HDR、颜色空间处理，关注 tuning 与帧同步。
4. SCL/LDC/DISP/VENC：完成缩放、畸变矫正、显示或编码，关注尺寸、stride、buffer queue。
5. IPU/IVE/AI Runtime：消费帧或图像块，关注输入格式、模型尺寸、量化类型、推理耗时。
6. Application：完成线程调度、队列、业务状态机、异常恢复。
7. Output：RTSP、文件、UI、告警或上报，关注端到端时延和输出一致性。

# Buffer 生命周期

排查时优先确认每个 buffer 的所有权：

1. 创建：由 SDK 模块、公共 buffer pool 或应用层分配。
2. 填充：Sensor/VIF/ISP/SCL 或应用预处理写入。
3. 消费：VENC、IPU、IVE、业务算法或显示模块读取。
4. 归还：必须回到对应模块或 pool，不能跨模块重复释放。
5. 异常路径：超时、丢帧、线程退出、模型错误时仍要释放或归还。

常见错误不是单点 API 失败，而是异常路径未归还 buffer，导致后续链路阻塞。

# 时间与线程边界

媒体链路排障至少记录四类时间：

1. Sensor 帧周期。
2. ISP/SCL/VENC 队列耗时。
3. AI 预处理、推理、后处理耗时。
4. 应用线程间排队耗时。

线程边界建议按“采集线程、编码线程、AI 线程、业务线程、输出线程”建模。若端到端延迟升高，先区分是 SDK 内部阻塞还是应用队列积压。

# 关键观测点

1. `/proc/<pid>/status`：线程数、VmRSS、FD 规模。
2. `/proc/<pid>/task/*/status`：线程状态与调度异常。
3. `/proc/<pid>/fd`：设备节点、socket、日志文件是否泄漏。
4. `dmesg`：sensor、VIF、ISP、VENC、IPU 相关错误。
5. SDK 日志：模块 bind、unbind、create、destroy、get、put 成对关系。
6. 模型与配置：输入尺寸、format、stride、量化信息、类别表版本。

# 排查顺序

1. 先确认链路拓扑：哪些模块实际启用，是否存在旁路或双路输出。
2. 再确认帧格式：width、height、format、stride、crop、rotate 是否一致。
3. 再看队列与线程：是否有线程阻塞在 get/put、select、poll、mutex。
4. 再看资源规模：FD、RSS、buffer pool、线程数是否持续增长。
5. 最后定位业务逻辑：异常路径是否释放，状态切换是否重复初始化。

# 失败归类

| 现象 | 优先怀疑 | 证据 |
| --- | --- | --- |
| 黑屏 | Sensor/VIF/ISP 无帧或格式错 | dmesg、SDK log、帧计数 |
| 花屏 | stride/format/crop 不一致 | dump 帧、模块参数、图像尺寸 |
| 延迟升高 | 队列积压或 AI 耗时升高 | 队列长度、线程状态、耗时日志 |
| AI 误检 | 预处理与训练输入不一致 | resize、color、normalize、model metadata |
| 长跑卡死 | buffer/FD/线程泄漏 | `/proc` 快照、get/put 计数 |

# 验证方式

1. 使用 `tools/debug/collect-media-pipeline-snapshot.sh` 采集第一现场。
2. 使用 `tools/debug/collect-ai-vision-bundle.sh` 采集模型与推理证据。
3. 结合 `docs/runbooks/sigmastar-media-pipeline-triage-guide.md` 完成模块级归因。
4. 结合 `docs/runbooks/yolo-ai-vision-deployment-guide.md` 验证 AI 输入输出一致性。
