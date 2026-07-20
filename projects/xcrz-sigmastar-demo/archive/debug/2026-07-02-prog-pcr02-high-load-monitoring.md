---
id: pcr02-prog-pcr02-high-load-monitoring-20260702
title: PCR02 prog_pcr02 高负载监控证据记录
kind: debug-record
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/archive/debug/2026-07-02-prog-pcr02-high-load-monitoring.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: manual
  from: field-runtime-monitoring via ADB; device endpoint deliberately not retained
review_after: '2026-10-02'
review_status: human-reviewed-accepted
content_review_status: accepted
evidence_validation_status: verified
promotion: none
promotion_decision: none; reviewing debug evidence only, source-level or driver-counter follow-up still required, no active
  promotion and no release gate
tags:
- pcr02
- prog_pcr02
- runtime-monitoring
- cpu-load
- adb
- reviewing-followup
- source-counter-required
- no-active-promotion
validation_refs:
- 'manual_validation_pending: true'
- 'reason: two runtime capture windows completed; source-level or driver-counter follow-up still required'
- 'required_followup: inspect nav.poll, VI/AI/audio/sensor hot paths and DDR/MIU counters'
evidence_strength: two-window-runtime-capture
evidence_refs:
- field-capture-sha256:ca15486ab2fb7db97dd30310f789ca4d7611b9cdc2100542af28259487553595; raw capture not retained
- field-capture-sha256:7985d21b0f107c8049b55454de596b7da3ba3a6e05dabbdc8864031b8a62c90d; raw capture not retained
created_at: '2026-07-02'
updated_at: '2026-07-19'
generated_by_ai: true
ai_role: summarized
ai_model_or_tool: Codex
ai_generated_at: '2026-07-02'
summary_zh: 2026-07-02 对 PCR02 设备 prog_pcr02 高负载进行两轮只读监控归档。两轮证据均显示高负载主要由 prog_pcr02 内部 CPU/调度压力驱动，块设备 IO 和短窗口 RSS 增长不是主因；根因仍需源码级或驱动计数进一步确认。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
---

# PCR02 prog_pcr02 高负载监控证据记录

## Source

- 设备：授权环境提供的 `<ADB_ENDPOINT>`；具体内部地址不进入长期知识正文。
- 连接方式：ADB
- 目标进程：`/customer/bin/prog_pcr02`
- PID：`916`
- 采集日期：2026-07-02
- 采集方式：只读 `/proc`、`top`、`iostat`、`ps` 快照；未重启设备，未 kill 进程，未清缓存，未修改设备文件。
- 归档方式：本条目只保存摘要和证据索引；原始 runtime log 只做 artifact 引用，不复制正文。

## Evidence

| Evidence | Time Window | Size | SHA256 | Notes |
| --- | --- | ---: | --- | --- |
| `field-capture:ca15486a…553595` | 2026-07-02 18:50:41-19:01:06 CST | 961241 bytes | `ca15486ab2fb7db97dd30310f789ca4d7611b9cdc2100542af28259487553595` | 第一轮完整采集，含 17 个样本；raw capture 未长期保留，只有哈希与本记录结论可恢复。 |
| `field-capture:7985d21b…62c90d` | 2026-07-02 19:29:08-19:39:20 CST | 893876 bytes | `7985d21b0f107c8049b55454de596b7da3ba3a6e05dabbdc8864031b8a62c90d` | 第二轮低扰动采集，20 个样本；raw capture 未长期保留。 |
| `field-capture:806c7582…05d5fa` | 2026-07-02 20:32:06-20:45:09 CST | 8247 lines | `806c75829c9140bfdda99b3d7aea354dd0b176f7e137b0216d51dd294105d5fa` | 第三轮新采集，27 个完整样本；raw capture 未长期保留。 |
| `field-capture:7a3c8c6f…4bb174` | 2026-07-02 20:56:33-21:02:51 CST | 1033 lines | `7a3c8c6f166dfd2448fadaadeca87e92c424231a9198f7cc8867e7c42a4bb174` | 第四轮源码可追热点线程定向采集，33 个样本；raw capture 未长期保留。 |

## First Capture Summary

- 采集窗口：2026-07-02 18:50:41 到 19:01:06，设备时间，持续约 `625s`。
- 完整样本：`17` 个。
- 首末样本跨度：`588s`。
- `loadavg` 长期处于高位：
  - 首样本：`29.41 28.91 21.11`
  - 末样本：`29.54 30.27 25.75`
  - 1 分钟 load：min `29.41`，avg `30.92`，max `34.29`
- `/proc/stat` 计算的整机 CPU 忙碌率：
  - min `95.3%`
  - avg `97.5%`
  - max `98.6%`
- `prog_pcr02` 占整机 CPU：
  - min `71.9%`
  - avg `76.1%`
  - max `78.9%`
  - 2 核系统上约等价于持续占用 `1.5` 个 CPU core。
- `top` 中 `prog_pcr02` 瞬时 CPU：
  - 首样本：`65.0%`
  - 最大观测：`88.5%`
  - 采样后 19:03:08 快照：`72.7%`

## Thread Hotspots

按第一轮首尾线程 CPU tick 增量排序，主要热点如下：

| TID | Name | Estimated System CPU | Observation |
| ---: | --- | ---: | --- |
| `1012` | `prog_pcr02` | `12.02%` | 持续 running，第一热点。 |
| `1072` | `nav.poll` | `8.52%` | 高 CPU，高非自愿调度切换。 |
| `1070` | `hdi_vi_out3` | `5.85%` | 视频输入/输出链路相关。 |
| `1113` | `wakeup_audio_ta` | `5.28%` | 音频唤醒任务相关。 |
| `1026` | `hdi_ai_prc0` | `4.60%` | AI 处理链路相关。 |
| `1003` | `sensor_disp0` | `4.20%` | sensor/display 相关。 |
| `1056` | `CUS3A` | `4.10%` | 3A 相关。 |
| `1044` | `sensor_tof0` | `3.38%` | ToF sensor 相关。 |
| `1090` | `ai-vi-capture` | `2.87%` | 末样本处于 D 状态。 |

非自愿上下文切换增量很高，例如 `TID=1012` 约 `380490` 次，`nav.poll` 约 `281829` 次，提示 CPU 调度竞争严重。

## Memory And DDR-Relevant Evidence

- `prog_pcr02 VmRSS`：`74332 kB -> 75084 kB`，10 分钟内增加约 `752 kB`。
- `prog_pcr02 VmSize`：`1174596 kB -> 1174716 kB`，基本稳定。
- `MemAvailable`：min `42676 kB`，avg `43156.7 kB`，max `43824 kB`。
- `MemFree`：约 `7.8-9.1 MB`。
- `SwapTotal=0`。
- `CmaTotal=4096 kB`，`CmaFree=0`，首尾稳定。

结论：通用 Linux 内存指标未显示 10 分钟内快速内存泄漏。`CmaFree=0` 对媒体链路是风险信号，但不能单独解释当前高 load。当前证据不包含 SigmaStar/MIU/DDR bandwidth counter，因此不能证明或排除 DDR 带宽瓶颈。

## IO Evidence

- `mmcblk0` 区间读扇区增量：`0`。
- `mmcblk0` 区间写扇区增量：`0`。
- `mmcblk0` IO busy ms 增量：`0`。
- `Dirty` / `Writeback` 基本不变：`Dirty=8 kB`，`Writeback=0`。
- `top` 观测 `iowait=0.0%`。

结论：块设备 IO 不是第一轮高负载主因。线程中出现 D 状态更可能与媒体驱动、VI/VENC/LDC/ISP 等链路等待相关，不应直接解释为存储 IO 卡住。

## Current Working Hypothesis

高负载主要由 `prog_pcr02` 内部 CPU/调度压力驱动，重点可疑链路包括：

- `nav.poll`：需确认是否 busy-poll 或缺少阻塞等待。
- `hdi_vi_out3` / `ai-vi-capture`：需确认视频采集/输出链路是否积压、重试或驱动等待。
- `wakeup_audio_ta` / `hdi_ai_prc0`：需确认音频唤醒和 AI 处理链路是否持续占 CPU。
- `sensor_disp0` / `sensor_tof0` / `CUS3A`：需确认 sensor/display/3A 相关循环是否异常高频。

## Negative Findings

- 第一轮没有看到块设备 IO 打满。
- 第一轮没有看到 `prog_pcr02` RSS 在 10 分钟内快速增长。
- 第一轮 D 状态线程数量较少，末样本为 1 个，中间最高为 2 个；D 状态不是全局 load 的唯一解释。

## Second Capture Summary

第二轮低扰动采集已完成，采集命令退出码为 `0`。

- 采集窗口：2026-07-02 19:29:08 到 19:39:20，设备时间，持续约 `612s`。
- 完整样本：`20` 个。
- 首末样本跨度：`583s`。
- 1 分钟 load：min `29.89`，avg `31.04`，max `32.28`。
- `/proc/stat` 计算的整机 CPU 忙碌率：min `95.9%`，avg `96.7%`，max `97.9%`。
- `prog_pcr02` 占整机 CPU：min `70.3%`，avg `72.8%`，max `74.4%`。
- `MemAvailable`：min `42180 kB`，avg `42337.8 kB`，max `42500 kB`。
- `prog_pcr02` 线程数全程稳定为 `127`。
- `mmcblk0` 区间读写扇区增量仍为 `0`，IO busy ms 增量为 `0`。
- 末样本线程状态：`S=121`，`R=5`，`D=1`；中间最高 `D=2`。

第二轮热点线程继续与第一轮吻合：

| TID | Name | Estimated System CPU | Observation |
| ---: | --- | ---: | --- |
| `1012` | `prog_pcr02` | `14.79%` | 持续 running，仍为第一热点。 |
| `1072` | `nav.poll` | `8.71%` | 高 CPU，高非自愿调度切换。 |
| `1113` | `wakeup_audio_ta` | `5.40%` | 音频唤醒任务相关。 |
| `1026` | `hdi_ai_prc0` | `4.62%` | AI 处理链路相关。 |
| `1003` | `sensor_disp0` | `4.60%` | sensor/display 相关。 |
| `1331` | `hdi_vi_sw_light` | `4.44%` | 第二轮新增热点，视频/光照链路相关。 |
| `1056` | `CUS3A` | `3.90%` | 3A 相关。 |
| `1045` | `prog_pcr02` | `3.45%` | 进程内部线程。 |
| `1044` | `sensor_tof0` | `3.36%` | ToF sensor 相关。 |
| `937` | `prog_pcr02` | `3.24%` | 进程内部线程。 |

## Third Capture Summary

第三轮采集用于验证线程命名后的新运行态热点，采集命令因已超过 10 分钟证据窗口并避免继续扰动设备而手动停止，保留已写入日志。

- 采集窗口：2026-07-02 20:32:06 到 20:45:09，主机时间，持续约 `783s`。
- 完整样本：`27` 个。
- 1 分钟 load：min `24.19`，avg `29.51`，max `31.53`。
- 5 分钟 load：min `24.99`，avg `28.17`，max `29.97`。
- `/proc/stat` 首尾计算的整机 CPU busy：约 `94.2%`。
- `MemAvailable`：min `49248 kB`，avg `52912 kB`，max `67032 kB`。
- 块设备和 VM 指标未体现为主导矛盾；本轮仍指向 CPU/调度压力主导。
- `prog_pcr02` 线程累计 CPU 增量约 `107298` jiffies。

第三轮热点线程按首尾 CPU jiffies 增量排序：

| TID | Name | CPU Jiffies Delta | Observation |
| ---: | --- | ---: | --- |
| `807` | `hdi_vi_out3` | `14982` | 第一热点，`state=R`，`wchan=0`。 |
| `785` | `nav.poll` | `14499` | 第二热点，持续高 CPU。 |
| `735` | `sensor_disp0` | `8986` | display update loop 相关，`state=R`。 |
| `867` | `wakeup_audio_ta` | `8216` | 音频唤醒链路相关，`state=R`。 |
| `762` | `hdi_ai_prc0` | `7473` | AI audio/process 链路相关。 |
| `801` | `CUS3A` | `6742` | 3A 相关。 |
| `820` | `ai-vi-capture` | `6739` | `state=D`，`wchan=down_timeout`。 |
| `781` | `prog_pcr02` | `5772` | 仍有未命名内部线程，需继续反查入口或确认设备版本。 |
| `676` | `pool_04` | `5440` | thread pool worker 热点。 |
| `838` | `sensor_tof0` | `5384` | ToF sensor 线程。 |
| `761` | `hdi_ai_cap0` | `3234` | AI capture 链路。 |
| `823` | `sensor_imu0` | `2925` | IMU sensor 线程。 |
| `744` | `app_uart_prs0` | `2331` | UART parser。 |
| `764` | `AgoraRTC` | `1878` | Agora RTC 线程。 |
| `782` | `app_loop0` | `1737` | 应用主循环线程。 |

第三轮和前两轮相比，热点从早期未命名 `TID=1012 prog_pcr02` 转向命名后的视频、导航、显示、音频和 sensor 链路。线程命名已显著改善可定位性，但 `TID=781 comm=prog_pcr02` 表明仍可能存在未命名入口，或设备运行版本未完整包含本地最新命名改动。

## Source-Mapped Hot Thread Capture

第四轮采集聚焦本地源码可追的热点线程，避免再次全量扫描所有 `/proc/<pid>/task/*` 造成额外扰动。采集窗口为 2026-07-02 20:56:33 到 21:02:51，主机时间，持续约 `378s`，完整样本 `33` 个。

- 1 分钟 load：min `28.55`，avg `29.26`，max `29.88`。
- `/proc/stat` 首尾计算的整机 CPU busy：约 `93.4%`。
- `MemAvailable`：min `49048 kB`，avg `49237 kB`，max `49424 kB`。
- 本轮结论继续指向 CPU/调度压力；未显示内存或块设备 IO 主导迹象。

源码可追热点线程按首尾 CPU jiffies 增量排序：

| TID | Name | CPU Jiffies Delta | Source Mapping |
| ---: | --- | ---: | --- |
| `807` | `hdi_vi_out3` | `9550` | `modules/hdi/src/hdi_video/hdi_vi.c`，`VSHDIOS_TaskOpen` 创建的 VI output loop。 |
| `735` | `sensor_disp0` | `4529` | `modules/sensor/display/display_manager.cpp`，`DisplayManager::updateLoop`。 |
| `762` | `hdi_ai_prc0` | `3614` | `modules/hdi/src/hdi_audio/hdi_ai.c`，audio process task。 |
| `676` | `pool_04` | `2663` | `modules/common/thread_pool/thread_pool.cpp`，thread pool worker。 |
| `838` | `sensor_tof0` | `2611` | `modules/sensor/common/sensordev_base.cpp` 和 ToF sensor path。 |
| `761` | `hdi_ai_cap0` | `1660` | `modules/hdi/src/hdi_audio/hdi_ai.c`，audio capture task。 |
| `823` | `sensor_imu0` | `1470` | `modules/sensor/common/sensordev_base.cpp` 和 IMU sensor path。 |
| `744` | `app_uart_prs0` | `1157` | `modules/app/src/app_uart/app_uart.c`，`_UART_RecvParserTask`。 |
| `782` | `app_loop0` | `878` | `pcr02/core/application.cpp`，`Application::run`。 |
| `743` | `app_uart_rx0` | `794` | `modules/app/src/app_uart/app_uart.c`，`_UART_RecvTask`。 |
| `707` | `api_event0` | `345` | `modules/api/src/api_ipc/api_event.c`，`_EVENT_Thread`。 |
| `742` | `app_uart_tx0` | `338` | `modules/app/src/app_uart/app_uart.c`，`_UART_SendTask`。 |

对照热点：

- `nav.poll`：CPU jiffies delta `7097`，仍是全局第二热点，但本地 `rg` 暂未确认对应源码入口。
- `ai-vi-capture`：CPU jiffies delta `4158`，出现 `D (disk sleep)`，本地源码映射未确认，仍需查三方库、驱动线程或符号来源。

第四轮把后续源码插桩优先级收敛为：`hdi_vi_out3`、`sensor_disp0`、`hdi_ai_prc0`、`pool_04`、`sensor_tof0`、`hdi_ai_cap0`、`sensor_imu0`。其中 `hdi_vi_out3` 是当前最强源码可追热点。

## Continuing Capture

已完成多轮运行态采集。若继续追根因，下一步应转为源码级和驱动级计数：

- 对 `nav.poll` 增加源码级或运行态计数，确认是否 busy-poll。
- 对 VI/AI/audio/sensor 线程增加帧队列、重试、超时、驱动 wait reason 计数。
- 查找 SigmaStar/MIU/DDR bandwidth counter 或 debugfs 节点，补足 DDR 带宽证据。
- 新增调试手段已沉淀到 `projects/xcrz-sigmastar-demo/current/runbooks/prog-pcr02-high-load-debug.md`。

## Verification

- ADB 连接曾出现短暂 `offline`，重启本机 adb server 后恢复；未重启目标设备。
- 第一轮采集命令退出码：`0`。
- `final-ready` 在上一轮收口时通过，但提示本地 `~/codex` 存在与本任务无关的既有 asset 脏改动。

## Archive Gate

- Sanitization: pass。正文不包含 secret、token、cookie、客户私密材料或完整 raw log。
- Raw log policy: pass。原始日志仅以本机 `/tmp` 路径和 hash 引用，不复制正文。
- Scope: project-specific。不得提升为 embedded 通用规则。
- Gate result: reviewing。两轮运行态证据已完成；根因仍需源码级或驱动计数进一步确认。
