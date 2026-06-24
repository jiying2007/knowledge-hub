---
title: YOLO / AI Vision 部署与排障指南
doc_type: runbook
knowledge_type: process
maturity: verified
status: active
owner: team-core
created: 2026-05-17
last_updated: 2026-05-17
tags: [yolo, ai, vision, deployment, triage]
related: [sigmastar-media-pipeline-triage-guide.md, embedded-linux-performance-triage-guide.md, ../architecture/sigmastar-platform-capability-matrix.md]
validation_refs: []
---

# YOLO / AI Vision 部署与排障指南

## 1. 目标

统一 YOLO 类检测在嵌入式设备上的部署、验证与排障路径，覆盖模型加载失败、帧率低、误检、漏检、后处理异常和运行期资源问题。

## 2. 部署检查

| 项目 | 检查点 |
| --- | --- |
| 模型文件 | 路径、hash、版本、输入尺寸 |
| 输入图像 | 尺寸、颜色空间、stride、归一化 |
| 推理后端 | NPU/CPU、线程数、内存池 |
| 后处理 | 阈值、NMS、类别映射、坐标缩放 |
| 输出 | bbox 坐标、类别、置信度、时间戳 |

## 3. 首次上线验证

1. 固定一组测试图片或短视频。
2. 输出模型元信息、输入尺寸、阈值、类别数。
3. 记录单帧耗时、平均 FPS、最大耗时。
4. 保存至少 3 张带框截图或结构化检测结果。
5. 记录运行 10 分钟后的 CPU、内存、线程和 fd 基线。

## 4. 排障路径

| 现象 | 首查项 | 处理方向 |
| --- | --- | --- |
| 模型加载失败 | 路径、权限、格式、runtime 版本 | 核对部署包与模型转换版本 |
| 全部漏检 | 输入尺寸、颜色空间、阈值 | 降低阈值，检查预处理 |
| 坐标偏移 | letterbox、缩放比例、stride | 校验坐标反算 |
| 误检多 | 类别映射、阈值、NMS | 固定样本集对比 |
| FPS 低 | 推理耗时、预处理耗时、队列阻塞 | 分段计时 |
| 内存上涨 | 输入缓存、输出 vector、模型上下文 | 运行期基线采集 |

## 5. 与媒体链路联动

YOLO 检测异常不一定发生在模型层。必须确认媒体链路输入帧稳定：

1. VIF/VPE 输出尺寸稳定。
2. 像素格式与预处理一致。
3. 送入 AI 的帧不是过期帧或空帧。
4. 队列阻塞不会导致延迟累积。

## 6. 收口标准

结论至少包含：

- 模型版本与输入尺寸。
- 触发样本或场景。
- 分段耗时。
- 阈值与 NMS 配置。
- 检测结果样例。
- 下一步最小验证动作。
