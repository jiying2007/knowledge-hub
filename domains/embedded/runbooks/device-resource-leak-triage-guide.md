---
title: 设备资源泄漏排查指南
doc_type: runbook
knowledge_type: process
maturity: draft
status: archived
searchable: false
owner: team-core
created: 2026-05-18
last_updated: 2026-05-18
tags: [embedded, leak, fd, memory, thread, buffer]
related: [embedded-linux-performance-triage-guide.md, sigmastar-media-pipeline-triage-guide.md, crash-triage-checklist.md]
validation_refs: [../../tools/debug/collect-runtime-baseline.sh, ../../tools/debug/collect-media-pipeline-snapshot.sh]
---

# 背景

资源泄漏通常表现为长跑后卡死、获取帧超时、创建线程失败、打开文件失败、VENC/AI 无输出或系统 OOM。本文用于在未拿到 core 前先做趋势证据采集。

# 前置条件

1. 已知目标进程名或 PID。
2. 设备允许读取 `/proc`、`dmesg` 和目标进程 fd。
3. 采样期间避免重启进程，否则趋势会失真。

# 操作步骤

## 1. 采集基线

```bash
rtk bash tools/debug/collect-runtime-baseline.sh --proc prog_pcr02 --duration 60 --out-dir /tmp/runtime-baseline
rtk bash tools/debug/collect-media-pipeline-snapshot.sh --proc prog_pcr02 --out-dir /tmp/media-snapshot
```

## 2. 判断泄漏类型

| 类型 | 证据 | 常见根因 |
| --- | --- | --- |
| FD 泄漏 | `/proc/<pid>/fd` 数量持续上涨 | socket/file/device 未关闭 |
| 线程泄漏 | `/proc/<pid>/task` 数量持续上涨 | 重复启动工作线程，退出未 join |
| 内存泄漏 | VmRSS/VmData 持续上涨 | malloc/new、SDK buffer、图像缓存未释放 |
| buffer 泄漏 | get/put 计数不匹配，媒体链路阻塞 | 异常路径未归还帧 |
| 日志泄漏 | 日志文件快速增长 | 高频错误或循环打印 |

## 3. 做趋势采样

建议按 1 分钟、10 分钟、30 分钟、2 小时四个节点采样。若问题只在高负载出现，必须同时记录输入源、码率、帧率、AI 开关状态。

## 4. 收敛到代码路径

1. FD 泄漏：按 fd 目标路径分组，反查打开代码路径。
2. 线程泄漏：按线程名或 wchan 分组，反查启动条件。
3. 内存泄漏：优先检查循环分配、异常 return、队列无限增长。
4. buffer 泄漏：检查每个 `Get` 是否有配对 `Put/Release`，特别是超时和错误分支。

# 回滚方案

1. 发现资源持续上涨时，先保存 `/proc`、dmesg、日志和配置，再重启止损。
2. 若临时降级功能可恢复服务，必须记录关闭了哪些链路，避免误判问题已修复。

# 验证记录

修复后至少跑一轮长跑对比：

1. FD 数量稳定。
2. 线程数量稳定。
3. VmRSS 不持续单调上涨。
4. 媒体帧计数持续增长且无阻塞。
5. dmesg 无新增相关错误。
