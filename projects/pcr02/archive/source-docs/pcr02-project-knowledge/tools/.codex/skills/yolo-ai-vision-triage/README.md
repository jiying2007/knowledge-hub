# yolo-ai-vision-triage

## 触发词

- YOLO、AI Vision、模型加载失败、误检、漏检、框偏移、FPS 低。

## 工作流

1. 确认模型、输入尺寸、类别、阈值和 NMS。
2. 确认媒体链路输入帧格式和尺寸。
3. 分段拆分采集、预处理、推理、后处理和输出耗时。
4. 输出最小复现样本与验证动作。

## 验证

```bash
rtk bash scripts/check-all.sh
```
