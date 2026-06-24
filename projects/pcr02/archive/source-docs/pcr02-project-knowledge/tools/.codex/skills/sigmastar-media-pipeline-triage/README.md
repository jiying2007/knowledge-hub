# sigmastar-media-pipeline-triage

## 触发词

- SigmaStar 媒体链路排查
- 黑屏、花屏、掉帧、VENC/AI 无输出
- Sensor/VIF/ISP/SCL/VENC/IPU buffer 阻塞

## 工作流

1. 对齐链路拓扑。
2. 采集媒体链路快照。
3. 分层归因并输出证据。

## 验证

```bash
rtk bash scripts/check-all.sh
```
