---
title: SSC305 媒体 Sensor 与 AI 链路排障方法
doc_type: runbook
knowledge_type: process
maturity: draft
status: active
owner: team-core
created: 2026-05-28
last_updated: 2026-05-28
tags: [ssc305, media, sensor, isp, ipu, ai]
related: [../standards/ssc305-feishu-knowledge-map.md, ../standards/sigmastar-platform-topic-catalog.md, sigmastar-media-pipeline-triage-guide.md, yolo-ai-vision-deployment-guide.md, embedded-linux-performance-triage-guide.md]
validation_refs: [../archive/sigmastar/manifest.csv, ../standards/sigmastar-platform-topic-catalog.md]
---

# SSC305 媒体 Sensor 与 AI 链路排障方法

## 1. 适用范围

本文用于 SSC305 上 Sensor、VIF、ISP、SCL、VENC、RGN、IPU、AI 算法链路的问题定位。

典型现象：

1. Sensor 无图、黑屏、花屏、偏色。
2. 帧率低、延迟高、丢帧、队列阻塞。
3. 编码无码流或码率异常。
4. OSD/RGN 显示异常。
5. AI 无检测结果、误检、推理耗时异常。
6. 夜视、IR、AE 亮度统计和日夜切换异常。

## 2. 链路模型

推荐按以下顺序定位：

```text
Sensor/Clock/Power/I2C
  -> MIPI/VIF
  -> ISP/3A/IQ
  -> SCL/LDC/IVE
  -> VENC/JPEG/RGN
  -> IPU/AI Algo
  -> App/Business Logic
```

不要从业务层现象直接跳到算法或驱动。先确认上游是否提供了正确帧。

## 3. Sensor 无图定位

先查资料主题：

1. `customer.Common.Development.Sensor_Porting_Guide_zh`
2. `platform.BSP.sensor_support_list_zh`
3. `platform.MI.sensor_zh`
4. `platform.MI.vif_zh`

设备侧检查顺序：

1. sensor 电源、reset、PWDN、MCLK 是否正确。
2. I2C 是否能读到 chip id。
3. 初始化寄存器表是否与 sensor 型号和模式一致。
4. MIPI lane、data rate、RAW 格式、分辨率、帧率是否匹配。
5. VIF 是否有帧计数。
6. ISP 是否完成 bind 和 start。

输出结论时避免只写“sensor 不出图”，应写：

```text
sensor 型号 + 输入接口 + 分辨率 + 帧率 + I2C 读写结果 + VIF 帧计数 + ISP 状态
```

## 4. 画面异常定位

| 现象 | 优先检查 |
| --- | --- |
| 黑屏 | sensor 出帧、ISP start、曝光、镜头遮挡、IQ bin |
| 花屏 | RAW 格式、lane 顺序、stride、buffer 对齐 |
| 偏色 | Bayer order、YUV/RGB 格式、AWB、IQ |
| 闪烁 | AE、帧率、电源纹波、灯光频率 |
| 裁切错位 | crop 参数、SCL 输出尺寸、stride |
| OSD 错位 | RGN 坐标系、旋转、缩放后坐标 |

证据至少包含：

1. 原始帧或截图。
2. sensor 模式配置。
3. VIF/ISP/SCL 输出尺寸和格式。
4. IQ 版本或配置路径。

## 5. 编码与码流问题

查资料主题：

1. `platform.MI.venc_zh`
2. `platform.MI.scl_zh`
3. `platform.MI.rgn_zh`

定位顺序：

1. VENC 输入帧是否到达。
2. 编码格式、分辨率、帧率、GOP、码率是否符合需求。
3. buffer 和队列是否阻塞。
4. IDR 触发和关键帧间隔是否合理。
5. 下游 RTSP/MP4/网络发送是否造成反压。

常见误判：

1. 无码流不一定是 VENC 问题，可能是上游无帧。
2. 码率高不一定是编码器异常，可能是场景复杂度、GOP 或 QP 策略。
3. 延迟高不一定是编码器，可能是下游写盘或网络阻塞。

## 6. AI/IPU 异常定位

查资料主题：

1. `platform.MI.ipu_zh`
2. `platform.IPU_Algo.det_zh`
3. `platform.IPU_Algo.cls_zh`
4. `platform.IPU_Algo.fr_zh`
5. `platform.CV_guide.IS_user_guide_zh`

定位顺序：

1. 模型文件、label、配置文件是否来自同一版本。
2. 输入尺寸、颜色空间、归一化、mean/std 是否匹配训练配置。
3. 前处理 resize/crop/letterbox 是否与后处理坐标还原一致。
4. IPU buffer 生命周期是否安全。
5. 推理耗时是否被上游取帧或下游后处理放大。
6. 多线程调用是否符合 IPU runtime 约束。

AI 问题结论必须包含：

```text
模型版本、输入尺寸、输入格式、前处理、后处理、单帧耗时、样例图片或帧 dump
```

## 7. 日夜切换与 IR 问题

IR、日夜切换和 AE 亮度统计要同时看硬件、ISP 和业务策略：

1. AE 统计值范围受 sensor、IQ、镜头、场景光影响。
2. 阈值必须基于实测，不可直接复用其他板型。
3. IR-cut、补光灯、曝光收敛存在时间延迟。
4. 从 VENC 或 ISP 回调里执行阻塞动作会引入帧链路抖动。

建议输出：

| 字段 | 内容 |
| --- | --- |
| 场景 | 白天、夜晚、暗箱、强逆光 |
| AE 统计 | 切换前后最小/最大/平均值 |
| 阈值 | day-to-night、night-to-day、迟滞区间 |
| 动作 | IR 灯、IR-cut、IQ 切换、曝光收敛 |
| 验证 | 连续切换次数、误切换次数、恢复时间 |

## 8. 工具与证据

媒体快照：

```bash
rtk bash tools/debug/project-knowledge-debug.sh media-snapshot --out-dir /tmp/ssc305-media
```

运行期基线：

```bash
rtk bash tools/debug/project-knowledge-debug.sh runtime-baseline --duration 30 --out-dir /tmp/ssc305-runtime
```

若项目没有 wrapper，使用知识库公共脚本并显式传入目标进程和输出目录。

## 9. 收口标准

媒体/AI 问题收口至少包含：

1. 异常所在链路层级。
2. 输入和输出格式、尺寸、帧率。
3. 关键日志、帧 dump 或截图。
4. 是否影响编码、显示、AI、音频或业务逻辑。
5. 根因是配置、代码、资源、驱动、硬件还是模型。
6. 最小复现和回归方法。
