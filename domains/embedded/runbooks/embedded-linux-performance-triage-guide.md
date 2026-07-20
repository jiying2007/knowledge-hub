---
title: 嵌入式 Linux 性能排障总线
doc_type: runbook
knowledge_type: process
maturity: verified
status: archived
searchable: false
owner: team-core
created: 2026-05-17
last_updated: 2026-05-17
tags: [embedded-linux, performance, triage, runtime]
related: [thread-crash-correlation-guide.md, crash-triage-checklist.md, ../standards/thread-troubleshooting-optimization.md, ../../tools/debug/busybox-kernel-io-watch.sh, ../../tools/debug/collect-runtime-baseline.sh]
validation_refs: [../../tools/debug/collect-runtime-baseline.sh, ../../tools/debug/busybox-kernel-io-watch.sh]
---

# 嵌入式 Linux 性能排障总线

## 1. 目标

把 CPU 高、load 高、内存上涨、I/O wait、线程阻塞、fd 泄漏等运行期问题收敛到统一入口，先采集基线，再按症状分流。

## 2. 第一现场基线

优先执行：

```bash
rtk bash tools/debug/collect-runtime-baseline.sh --proc "$PROJECT_EXE" --duration 30
```

若只知道 PID：

```bash
rtk bash tools/debug/collect-runtime-baseline.sh --pid <PID> --duration 30
```

最少保留：

1. `top` 与 `ps` 输出。
2. `/proc/<pid>/status`、`io`、`limits`。
3. 线程数、fd 数、wchan 摘要。
4. `free`、`df`、`mount`、`dmesg tail`。

## 3. 症状分流

| 症状 | 首查证据 | 下一步 |
| --- | --- | --- |
| CPU 高 | `top -H`、线程名、调用栈 | 采样热点线程，检查忙等与锁竞争 |
| load 高但 CPU 不满 | `ps` state、`wchan` | 查 D 态、I/O 阻塞、驱动等待 |
| 内存上涨 | `/proc/<pid>/status`、`smaps` | 区分堆、mmap、文件缓存 |
| I/O wait 高 | `/proc/<pid>/io`、`dmesg` | 使用 `busybox-kernel-io-watch.sh` |
| fd 增长 | `/proc/<pid>/fd` 计数 | 查打开路径与泄漏周期 |
| 线程数增长 | `/proc/<pid>/task` | 查线程创建路径与退出条件 |

## 4. 证据规则

1. 不只描述“卡顿/慢”，必须附采集时间、PID、版本、负载场景。
2. 不把单次瞬时值写成结论，至少需要两次采样或持续采样。
3. 优先保留原始采集包，再输出摘要。
4. 若涉及 core 或崩溃，切换到 `docs/runbooks/crash-triage-checklist.md`。

## 5. 收口标准

排障结论至少包含：

- 现象分类。
- 关键证据文件。
- 可复现命令或场景。
- 根因置信度。
- 下一步最小验证动作。
