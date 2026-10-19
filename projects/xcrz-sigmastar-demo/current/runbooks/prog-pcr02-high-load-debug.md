---
aliases:
- PCR02 prog_pcr02 高负载调试手段
related:
- projects/pcr02-ssc305/README.md
- indexes/obsidian-home.md
- indexes/project-readiness.md
id: pcr02-prog-pcr02-high-load-debug-runbook-20260702
title: PCR02 prog_pcr02 高负载调试手段
kind: runbook
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/current/runbooks/prog-pcr02-high-load-debug.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: generated-from-debug-session
  from: 2026-07-02 prog_pcr02 high-load monitoring and thread naming session
  evidence_item: pcr02-prog-pcr02-high-load-monitoring-20260702
review_after: '2026-10-02'
review_status: human-reviewed-accepted
content_review_status: accepted
evidence_validation_status: verified
promotion: none
promotion_decision: none; project-local reviewing runbook candidate derived from debug evidence, no active promotion, no release
  gate and no owner decision
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
validation_refs:
- projects/xcrz-sigmastar-demo/current/runbooks/prog-pcr02-high-load-debug.md
- rtk bash tools/knowledge-check.sh --dry-run --json --explain pcr02-prog-pcr02-high-load-debug-runbook-20260702
- rtk bash tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: derived-from-three-runtime-capture-windows
evidence_refs:
- projects/xcrz-sigmastar-demo/current/runbooks/prog-pcr02-high-load-debug.md
- projects/xcrz-sigmastar-demo/archive/debug/2026-07-02-prog-pcr02-high-load-monitoring.md
- field-capture-sha256:806c75829c9140bfdda99b3d7aea354dd0b176f7e137b0216d51dd294105d5fa; raw capture not retained
created_at: '2026-07-02'
updated_at: '2026-07-19'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-07-02'
summary_zh: 沉淀 PCR02 prog_pcr02 高负载现场只读调试手段：ADB 低扰动 10 分钟采集、线程 CPU jiffies 排序、上下文切换排序、wchan/state 判断、热点 TID 定向复采、源码级聚合计数建议和
  DDR/MIU 证据缺口边界。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
---

# PCR02 prog_pcr02 高负载调试手段

## Scope

本 runbook 适用于 PCR02/SigmaStar SSC305 设备上 `/customer/bin/prog_pcr02` 出现高 load、高 CPU、线程调度竞争或媒体链路疑似阻塞时的现场只读排查。设备端点由授权环境注入，不在长期正文保存。

本手段只做只读采集，不重启设备，不 kill 进程，不清缓存，不修改设备文件。

## Preconditions

- 已设置本次授权端点：`PCR02_ADB_ENDPOINT=<authorized-endpoint>`
- ADB 已连接：`rtk adb connect "${PCR02_ADB_ENDPOINT}"`
- 目标进程存在：`rtk adb -s "${PCR02_ADB_ENDPOINT}" shell "pidof prog_pcr02"`
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
rtk adb connect "${PCR02_ADB_ENDPOINT}"
rtk adb -s "${PCR02_ADB_ENDPOINT}" shell "date; uptime; pidof prog_pcr02; ps -T | grep prog_pcr02 | head -40"
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

**历史 TID 不能作为新设备的可执行目标。** 2026-07-02 记录里的 `807/785/735/820/781` 仅用于解释原始窗口；PID/TID 会退出、重新分配或重用。先用本次 `/proc/stat` 与线程 jiffies 差分排序确定热点，再在**同一个当前进程的** `/proc/<pid>/task/` 中复核身份。以下单次只读命令动态挑选常见候选线程，并对 `comm` 前后不一致或已经退出的线程跳过，**不是**对 CPU 热度的自动证明：

```bash
rtk adb -s "${PCR02_ADB_ENDPOINT}" shell '
pid=$(pidof prog_pcr02) || exit 1
case "$pid" in *" "*) echo "AMBIGUOUS_PID" >&2; exit 2 ;; esac
[ -d "/proc/$pid/task" ] || exit 2
found=0
for task in /proc/"$pid"/task/[0-9]*; do
  [ -r "$task/comm" ] || continue
  before=$(cat "$task/comm" 2>/dev/null) || continue
  case "$before" in
    hdi_vi_out*|sensor_disp0|hdi_ai_prc0|hdi_ai_cap0|nav.poll|ai-vi-capture|pool_*|sensor_tof0) ;;
    *) continue ;;
  esac
  tid=${task##*/}
  [ -r "$task/stat" ] || continue
  stat=$(cat "$task/stat" 2>/dev/null) || continue
  after=$(cat "$task/comm" 2>/dev/null) || continue
  [ "$before" = "$after" ] || continue
  echo "=== pid=$pid tid=$tid comm=$before ==="
  printf "%s\n" "$stat"
  grep -E "^State:|^voluntary_ctxt_switches:|^nonvoluntary_ctxt_switches:" "$task/status" 2>/dev/null || true
  cat "$task/wchan" 2>/dev/null || true
  if [ -r "$task/stack" ]; then cat "$task/stack" 2>/dev/null || true; fi
  found=$((found+1))
  [ "$found" -ge 16 ] && break
done
[ "$found" -gt 0 ] || { echo "NO_CURRENT_TARGET_THREADS" >&2; exit 2; }
'
```

- 命令最多输出 16 个实时匹配线程；实际热点仍以**本轮首尾 CPU jiffies 增量**排序，不能以命中线程名推断忙循环或根因。
- `NO_CURRENT_TARGET_THREADS`、线程消失、读取 `stack/wchan` 失败只能记为不可用，不能记为无故障；多进程 PID 歧义直接失败。
- 对没有命名、已经重命名或不在过滤集合中的热点，使用本轮 `ps -T` 和 `/proc/<pid>/task` 确认实时 TID 后另做定向读取，不要从下方历史证据表复制 TID。
- 即使两次读取 `comm` 一致，也不能完全排除极短窗口内 TID 重用；最终结论需要前后时间戳、进程/制品身份和完整采样窗口匹配。

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

- Raw artifact identity: `field-capture-sha256:7a3c8c6f166dfd2448fadaadeca87e92c424231a9198f7cc8867e7c42a4bb174`；raw capture 未长期保留。
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
- 设备端点和本机临时证据路径不得进入长期正文；只保留脱敏参数名、内容哈希和可复核结论。

## Provenance

- Generated from 2026-07-02 PCR02 high-load field monitoring session.
- Evidence record: `projects/xcrz-sigmastar-demo/archive/debug/2026-07-02-prog-pcr02-high-load-monitoring.md`
- Latest raw artifact identity: `field-capture-sha256:7a3c8c6f166dfd2448fadaadeca87e92c424231a9198f7cc8867e7c42a4bb174`; raw capture not retained.
