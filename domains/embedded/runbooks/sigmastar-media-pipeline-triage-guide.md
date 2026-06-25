---
title: SigmaStar 媒体链路排障指南
doc_type: runbook
knowledge_type: process
maturity: verified
status: active
owner: team-core
created: 2026-05-17
last_updated: 2026-05-17
tags: [sigmastar, media, pipeline, camera, audio]
related: [sigmastar-platform-development-workflow.md, ../architecture/sigmastar-platform-capability-matrix.md, yolo-ai-vision-deployment-guide.md, embedded-linux-performance-triage-guide.md]
validation_refs: [../archive/sigmastar/manifest.csv]
---

# SigmaStar 媒体链路排障指南

## 1. 目标

为 VIF、VPE、VENC、AI、Audio、Display 等媒体链路问题提供统一排查顺序，避免直接跳到单模块猜测。

## 2. 链路分层

1. Sensor / MIPI / VIF：图像输入、帧同步、分辨率、帧率。
2. VPE / DIVP：缩放、旋转、裁剪、像素格式转换。
3. VENC / JPEG：编码、码率、GOP、缓冲。
4. AI / YOLO：输入尺寸、预处理、推理、后处理。
5. Audio：采样率、声道、编码、播放/录音路径。
6. Display / OSD：输出尺寸、图层、叠加、刷新。

## 3. 排查顺序

| 阶段 | 关键问题 | 证据 |
| --- | --- | --- |
| 输入 | sensor 是否出帧 | 驱动日志、帧计数、分辨率 |
| 格式 | pixel format 是否一致 | 模块配置、dump 帧 |
| 缓冲 | 是否丢帧/阻塞 | 队列深度、返回码、时间戳 |
| 推理 | AI 输入是否匹配 | 模型尺寸、预处理参数 |
| 输出 | 编码/显示是否正常 | 码流、截图、帧率 |

## 4. 常见错误模式

1. 分辨率或 stride 不一致导致画面错位。
2. YUV/RGB 格式理解错误导致颜色异常。
3. 推理输入尺寸与模型不一致导致检测异常。
4. 队列阻塞导致帧率下降或延迟累积。
5. 音频采样率/声道不一致导致变速、噪音或无声。

## 5. 与性能排障联动

媒体链路问题经常表现为 CPU 高、内存涨、I/O 抖动或线程阻塞。出现系统级异常时，先采集：

```bash
rtk bash tools/debug/collect-runtime-baseline.sh --proc "$PROJECT_EXE" --duration 30
```

再按媒体链路定位单点。

## 6. 收口标准

输出结论时至少包含：

- 异常所在链路层级。
- 输入/输出格式与尺寸。
- 关键日志或 dump 证据。
- 是否影响 AI、编码、显示或音频。
- 最小复现与验证命令。
