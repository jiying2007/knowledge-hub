# embedded-performance-triage

## 触发词

- CPU 高、load 高、设备卡顿、I/O wait、线程阻塞、fd 泄漏、内存上涨。

## 工作流

1. 确认进程名/PID 和复现场景。
2. 运行 `tools/debug/collect-runtime-baseline.sh` 采集第一现场。
3. 根据症状分流到 CPU、I/O、内存、线程或 fd 路径。
4. 输出证据包路径和下一步验证命令。

## 验证

```bash
rtk bash scripts/check-all.sh
```
