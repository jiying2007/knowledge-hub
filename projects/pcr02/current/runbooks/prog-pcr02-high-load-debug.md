---
id: pcr02-prog-pcr02-high-load-debug-runbook-20260702
title: PCR02 prog_pcr02 高负载调试手段
kind: runbook
domain: projects/pcr02
status: reviewing
owner: leiwenjun
created_at: 2026-07-02
updated_at: 2026-07-02
review_after: '2026-10-02'
tags:
- pcr02
- prog_pcr02
- high-load
- runtime-debug
- adb
- runbook
- thread-analysis
- reviewing-followup
- candidate-runbook
- no-active-promotion
summary_zh: 沉淀 PCR02 prog_pcr02 高负载现场只读调试手段：ADB 低扰动 10 分钟采集、线程 CPU jiffies 排序、上下文切换排序、wchan/state 判断、热点 TID 定向复采、源码级聚合计数建议和
  DDR/MIU 证据缺口边界。
path: projects/pcr02/current/runbooks/prog-pcr02-high-load-debug.md
scope: project-specific
visibility: team-internal
review_status: human-reviewed-accepted
promotion: none
aliases:
- PCR02 prog_pcr02 高负载调试手段
related:
- projects/pcr02/README.md
- indexes/obsidian-home.md
- indexes/project-readiness.md
---

# PCR02 prog_pcr02 高负载调试手段

## Scope

本 runbook 适用于 PCR02/SigmaStar SSC305 设备上 `/customer/bin/prog_pcr02` 出现高 load、高 CPU、线程调度竞争或媒体链路疑似阻塞时的现场只读排查。默认设备通过 ADB 连接，例如 `172.16.16.27:5555`。

本手段只做只读采集，不重启设备，不 kill 进程，不清缓存，不修改设备文件。

## Preconditions

- ADB 已连接：`rtk adb connect 172.16.16.27:5555`
- 目标进程存在：`rtk adb -s 172.16.16.27:5555 shell "pidof prog_pcr02"`
- 设备负载较高时，ADB 单轮 shell 可能显著慢于采样间隔；判断采集时长应以首尾样本墙钟时间为准，不只看样本数。

## Low-Overhead 10-Minute Capture

采集目标：

- `/proc/loadavg`、`uptime`
- `/proc/stat`
- `/proc/meminfo`、`/proc/vmstat`
- `/proc/diskstats`
- `/proc/<pid>/status`
- `ps -T`
- `/proc/<pid>/task/<tid>/{comm,status,stat,wchan}`

建议采集时长不少于 10 分钟。若设备高负载导致单轮 ADB shell 变慢，可以降低样本数但必须保留首尾样本时间和 sha256。

最小手工流程：

```bash
rtk adb connect 172.16.16.27:5555
rtk adb -s 172.16.16.27:5555 shell "date; uptime; pidof prog_pcr02; ps -T | grep prog_pcr02 | head -40"
```

采集完成后必须计算：

```bash
rtk sha256sum /tmp/<capture-log>.log
rtk rg -n "^===== SAMPLE" /tmp/<capture-log>.log | rtk head
rtk rg -n "^===== SAMPLE" /tmp/<capture-log>.log | rtk tail
```

## Hot Thread Ranking

用首尾样本计算线程增量，优先排序：

- `utime + stime` 增量：判断 CPU 热点。
- `nonvoluntary_ctxt_switches` 增量：判断调度竞争。
- `state` 和 `wchan`：区分 running、sleep、D 状态和等待点。

结论表达建议：

- 如果 `/proc/stat` busy 高、`prog_pcr02` 线程 CPU jiffies 高，同时 diskstats/Dirty/Writeback 没明显增长，优先判断为 CPU/调度压力主导。
- 如果 `D` 状态线程集中在媒体链路，例如 `ai-vi-capture` 且 `wchan=down_timeout`，需要转向 VI/AI/audio driver wait reason 或队列积压计数。
- 如果线程名仍为 `prog_pcr02`，需要继续补线程入口命名，或确认设备运行版本是否包含最新命名改动。

## Targeted Follow-Up

对热点 TID 做短周期二次采集：

```bash
rtk adb -s 172.16.16.27:5555 shell "pid=\$(pidof prog_pcr02); for tid in 807 785 735 820 781; do echo === \$tid ===; cat /proc/\$pid/task/\$tid/comm; cat /proc/\$pid/task/\$tid/status | egrep 'State|voluntary|nonvoluntary'; cat /proc/\$pid/task/\$tid/wchan; cat /proc/\$pid/task/\$tid/stat; done"
```

若内核启用了 stack：

```bash
rtk adb -s 172.16.16.27:5555 shell "pid=\$(pidof prog_pcr02); for tid in 807 785 735 820 781; do echo === \$tid stack ===; cat /proc/\$pid/task/\$tid/stack 2>/dev/null; done"
```

## Source-Mapped Hot Thread Capture

当已经确认热点线程名，并希望只跟踪本地源码可追入口时，使用 5 分钟定向采集。它只读取目标线程的 `comm/status/stat/wchan/schedstat`，避免全量 task 扫描。

推荐目标线程：

- `hdi_vi_out3`：`modules/hdi/src/hdi_video/hdi_vi.c`
- `sensor_disp0`：`modules/sensor/display/display_manager.cpp`
- `hdi_ai_prc0` / `hdi_ai_cap0`：`modules/hdi/src/hdi_audio/hdi_ai.c`
- `sensor_tof0` / `sensor_imu0`：`modules/sensor/common/sensordev_base.cpp` 和对应 sensor path
- `app_uart_tx0` / `app_uart_rx0` / `app_uart_prs0`：`modules/app/src/app_uart/app_uart.c`
- `app_loop0`：`pcr02/core/application.cpp`
- `api_event0`：`modules/api/src/api_ipc/api_event.c`
- `pool_XX`：`modules/common/thread_pool/thread_pool.cpp`

`nav.poll`、`ai-vi-capture` 等没有确认本地源码入口的线程可以作为对照保留，但不要误标为已确认源码可追。

采集后按首尾样本计算：

- `utime + stime` delta：CPU 热度。
- `nonvoluntary_ctxt_switches` delta：调度竞争。
- `state/wchan`：等待点和 D 状态。
- `schedstat`：如果设备内核提供有效内容，可辅助判断 runtime 和 wait time；若为空，不作为阻塞证据。

第四轮基线证据：

- Raw artifact ref: `/tmp/pcr02_source_hot_threads_20260702_205632.log`
- SHA256: `7a3c8c6f166dfd2448fadaadeca87e92c424231a9198f7cc8867e7c42a4bb174`
- Window: 2026-07-02 20:56:33-21:02:51 CST
- Result: `hdi_vi_out3`、`sensor_disp0`、`hdi_ai_prc0`、`pool_04`、`sensor_tof0` 是源码可追优先插桩对象。

## Source-Level Instrumentation

线程名必须尽量短于 Linux `comm` 的 15 字节有效长度。推荐策略：

- 视频输出：`hdi_vi_out0`、`hdi_vi_out1`、`hdi_vi_out2`、`hdi_vi_out3`
- display loop：`sensor_disp0`
- ToF/IMU：`sensor_tof0`、`sensor_imu0`
- thread pool：`pool_00` 或 `hdi_pool_wkr`
- app loop：`app_loop0`
- 临时 release worker：`sensor_tof_rel`、`sensor_imu_rel`

建议追加计数：

- `nav.poll`：poll 次数、timeout 次数、收到事件次数、空转次数、单轮耗时分布。
- `hdi_vi_out3` / `ai-vi-capture`：帧输入、帧输出、drop、timeout、驱动返回码、队列深度。
- `sensor_disp0`：scene update 次数、LVGL flush 次数、单轮耗时、最长耗时。
- `hdi_ai_prc0` / `wakeup_audio_ta`：帧处理量、唤醒检测次数、超时次数、队列深度。
- `pool_XX`：job 类型、job 执行耗时、排队长度。

调试日志应做周期聚合，例如 30 秒输出一次，避免把日志本身变成负载来源。

## DDR/MIU Evidence Gap

Linux 通用 `/proc/meminfo` 只能说明内存容量、缓存、Dirty/Writeback 和 RSS 趋势，不能证明 DDR bandwidth 是否打满。需要另外查 SigmaStar/MIU/DDR counter、debugfs 或 vendor 工具。没有这类 counter 时，结论只能写为“未发现内存泄漏或块设备 IO 主导，DDR 带宽未被证明或排除”。

## Archive Policy

- 原始日志不复制进 Knowledge Hub 正文。
- 归档正文只保存：时间窗口、样本数、sha256、负载摘要、热点表、负面发现、下一步。
- 设备 IP、进程路径和本机 `/tmp` 证据路径可作为项目本地证据引用；不得提升为团队通用规则。

## Provenance

- Generated from 2026-07-02 PCR02 high-load field monitoring session.
- Evidence record: `projects/pcr02/archive/debug/2026-07-02-prog-pcr02-high-load-monitoring.md`
- Latest raw artifact ref: `/tmp/pcr02_source_hot_threads_20260702_205632.log`, sha256 `7a3c8c6f166dfd2448fadaadeca87e92c424231a9198f7cc8867e7c42a4bb174`.
