---
maturity: candidate
id: pcr02-prog-pcr02-runtime-hot-thread-followup-20260710
title: PCR02 prog_pcr02 运行态热点线程跟进
kind: debug-record
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/archive/debug/2026-07-10-prog-pcr02-runtime-hot-thread-followup.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: manual
  from: codex-session-runtime-debug via adb on PCR02 device 172.16.16.133
review_after: '2026-10-10'
review_status: human-reviewed-accepted
content_review_status: accepted
evidence_validation_status: verified
promotion: none
promotion_decision: none; reviewing debug-record candidate, repeated same-condition sampling still required, no active promotion,
  no release gate and no owner decision
tags:
- pcr02
- prog_pcr02
- runtime-monitoring
- cpu-load
- adb
- hot-thread
- hdi_vi_out3
- hdi_vi_sw_light
- sensor_in0
- sensor_tof0
- reviewing-followup
- repeat-sampling-required
- no-active-promotion
validation_refs:
- rtk make modules/hdi_lib_all
- rtk bash ~/codex/scripts/final-ready.sh
- 'manual_validation_pending: true'
- 'reason: runtime follow-up is a single-window sample; needs repeated same-condition sampling after deployment'
evidence_strength: single-window-runtime-followup-plus-build-verification
evidence_refs:
- projects/xcrz-sigmastar-demo/archive/debug/2026-07-10-prog-pcr02-runtime-hot-thread-followup.md
- 'current Codex session: adb connect 172.16.16.133:5555; /proc status; task stat 1s delta'
- modules/hdi/src/hdi_video/hdi_vi.c _VI_IspSwLightSensor optimization
created_at: '2026-07-10'
updated_at: '2026-07-19'
generated_by_ai: true
ai_role: summarized
ai_model_or_tool: Codex
ai_generated_at: '2026-07-10'
summary_zh: 2026-07-10 对 PCR02 设备 172.16.16.133 进行只读运行态跟进采样：prog_cmd_server 和 prog_daemon 的 RSS 很小，高 VSZ 不是实际内存热点；主压力仍集中在
  prog_pcr02 内部，线程热点包括 AgoraRTC、hdi_vi_out3、ai-wakeup-aud、sensor_disp0、hdi_ai_prc0、CUS3A、sensor_in0 和 sensor_tof0。hdi_vi_sw_light
  去 1ms spin-wait 后已不再是前排热点。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
---

# PCR02 prog_pcr02 运行态热点线程跟进

## Source

- 设备：`172.16.16.133:5555`
- 连接方式：ADB
- 采集日期：2026-07-10
- 采集方式：只读 ADB shell、`/proc`、BusyBox `top`、进程 status 和线程 stat delta。
- 操作边界：未重启设备，未 kill 进程，未清缓存，未修改设备文件。
- 归档范围：记录当前会话中可复用的性能定位结论和后续验证项；不复制完整 raw 输出。

## Context

设备侧进程视图显示：

- `prog_pcr02` 为主负载进程，瞬时 CPU 约 `73.3%`。
- `prog_cmd_server` 瞬时 CPU 约 `1.8%`。
- `prog_daemon` 瞬时 CPU 约 `0.1%`。
- 设备 `load average` 长期高位，样本中可到 `33.13 25.75 21.91`。
- BusyBox `top` 的 `%VSZ` 是虚拟地址空间占比，不能等同于物理内存占用。

## Process Memory Evidence

2026-07-10 对 `172.16.16.133:5555` 只读采样：

| Process | PID | VmSize | VmRSS | RssAnon | Threads | Finding |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| `prog_cmd_server` | `1386` | `49116 kB` | `4212 kB` | `1220 kB` | `6` | 实际 RSS 很小，不是内存热点。 |
| `prog_daemon` | `1376` | `32112 kB` | `1328 kB` | `176 kB` | `4` | 实际 RSS 很小，不是内存热点。 |
| `prog_pcr02` | `1387` | `1302704 kB` | `67728 kB` | `48708 kB` | `140` | 主运行负载集中在该进程。 |

结论：`prog_cmd_server` 和 `prog_daemon` 的高 `%VSZ` 是虚拟空间现象，不代表真实 RAM 压力；当前主问题仍在 `prog_pcr02`。

## Hot Thread Evidence

由于设备 BusyBox `top` 不支持 `-H` 参数，本次使用 `/proc/1387/task/*/stat` 做 1 秒 CPU tick delta 排序。

`prog_pcr02` 热点线程样本：

| Delta Ticks | TID | Thread | Interpretation |
| ---: | ---: | --- | --- |
| `297` | `1509` | `AgoraRTC` | RTC 链路高负载。 |
| `296` | `1929` | `hdi_vi_out3` | DS2/raw 视频输出链路仍是核心热点。 |
| `248` | `1612` | `ai-wakeup-aud` | 音频唤醒链路高负载。 |
| `239` | `1461` | `sensor_disp0` | 显示 update loop 仍明显。 |
| `237` | `1484` | `hdi_ai_prc0` | AI 音频/处理链路高负载。 |
| `227` | `1924` | `CUS3A` | ISP 3A 线程明显。 |
| `221` | `1457` | `sensor_in0` | ZMQ 输入/AI detection 等消息处理仍明显。 |
| `175` | `1396` | `task_poller` | 任务调度/轮询线程明显。 |
| `158` | `1508` | `sensor_tof0` | ToF 轮询/发布链路仍有优化空间。 |
| `156` | `1470` | `media_poll0` | 媒体 poller 链路明显。 |
| `134` | `1536` | `nav.poll` | 导航 poller 仍明显。 |
| `119` | `1483` | `hdi_ai_cap0` | 音频采集链路明显。 |
| `115` | `1556` | `ai-vi-shm` | AI 视频共享内存链路明显。 |
| `91` | `1507` | `sensor_imu0` | IMU 发布链路有一定负载。 |
| `32` | `1933` | `hdi_vi_sw_light` | 已不再是前排热点。 |

`prog_cmd_server` / `prog_daemon` 线程 delta：

| Process | Hot Threads | Finding |
| --- | --- | --- |
| `prog_cmd_server` | `cmd_net0=5`, `cmd_route0=5` | 低负载。 |
| `prog_daemon` | `daemon_key0=1` | 低负载。 |

## Code Change Evidence

本会话已对 `modules/hdi/src/hdi_video/hdi_vi.c` 的 `_VI_IspSwLightSensor()` 做低风险优化：

- 原逻辑：内部 `while (1)` 等待 AE count 更新，每轮 `usleep(1000 * 1)`，可能导致 `hdi_vi_sw_light` 1ms 粒度反复唤醒。
- 新逻辑：每次 task 唤醒只检查一次 `MI_ISP_CUS3A_GetDoAeCount()`；AE count 没变化直接返回；AE count 变化才继续查询曝光信息和执行软光敏判定。
- 验证：
  - `rtk git -C modules/hdi diff --check -- src/hdi_video/hdi_vi.c` 通过。
  - `rtk make modules/hdi_lib_all` 通过。
  - `hdi_vi_sw_light` 在后续设备线程 delta 样本中降到后排，样本 delta 为 `32`。

注意：该后续样本只是单次运行态证据，不能单独证明长期稳定收益；需要多轮同条件采样确认。

## Current Diagnosis

当前主压力不是 `prog_cmd_server` 或 `prog_daemon`，而是 `prog_pcr02` 内部多条周期链路叠加：

- 视频/RTC：`AgoraRTC`、`hdi_vi_out3`、`ai-vi-shm`、`media_poll0`。
- 音频/AI：`ai-wakeup-aud`、`hdi_ai_prc0`、`hdi_ai_cap0`。
- sensor/UI：`sensor_disp0`、`sensor_in0`、`sensor_tof0`、`sensor_imu0`。
- ISP/3A：`CUS3A`。
- 导航/任务：`nav.poll`、`task_poller`。

`hdi_vi_sw_light` 的 1ms spin-wait 优化方向有效，但不是当前剩余 CPU 的主要矛盾。

## Next Actions

建议后续按以下优先级继续：

1. `hdi_vi_out3`
   - 确认设备端是否已部署 DS2 NV12 优化版本。
   - 确认 DS2 输出 FPS 是否真实按 20fps。
   - 采集每秒输出帧数、取帧失败次数、normalize 耗时、下游订阅数。
2. `sensor_in0`
   - 给每类 ZMQ 消息增加低频计数和耗时统计。
   - 重点确认 AI detection 消息是否高频触发 protobuf parse。
   - 评估在 `DetectionRgnRenderer::handleDetectionMessage()` 入口节流或只处理最新帧。
3. `sensor_tof0`
   - 统计 ToF ready/no-ready 比例、I2C ready check 耗时、整帧 read 耗时、protobuf serialize 耗时。
   - 若 no-ready 比例高，评估把 20ms 轮询调到更贴近 15Hz，或按业务降到 10Hz。
4. `sensor_disp0`
   - 先加 `currentScene_->update()`、`displayProvider.taskHandler()`、flush queue 长度和耗时统计。
   - 再评估 dirty 更新、flush 背压或双 worker。

## Evidence Index

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
| --- | ---: | --- | --- | --- | --- |
| `rtk adb connect 172.16.16.133:5555` | 0 | ADB 连接成功。 | 当前 Codex 会话输出 | Debug Transport | `pcr02-prog-pcr02-runtime-hot-thread-followup-20260710` |
| `rtk adb -s 172.16.16.133:5555 shell 'pidof prog_pcr02 prog_cmd_server prog_daemon'` | 0 | 识别到 `prog_pcr02=1387`、`prog_cmd_server=1386`、`prog_daemon=1376/1374`。 | 当前 Codex 会话输出 | Debug Transport | same |
| `rtk adb -s 172.16.16.133:5555 shell 'grep -E "Name|State|VmSize|VmRSS|RssAnon|RssFile|RssShmem|VmData|VmStk|Threads" /proc/<pid>/status'` | 0 | 确认 `cmd_server` 与 `daemon` RSS 很小，主 RSS 在 `prog_pcr02`。 | 当前 Codex 会话输出 | Runtime Evidence | same |
| `rtk bash -lc '<proc task stat 1s delta sampler>'` | 0 | 获取 `prog_pcr02` 热点线程 delta，主热点为 `AgoraRTC`、`hdi_vi_out3`、`ai-wakeup-aud`、`sensor_disp0` 等。 | 当前 Codex 会话输出 | Runtime Evidence | same |
| `rtk make modules/hdi_lib_all` | 0 | `_VI_IspSwLightSensor()` 去 spin-wait 后 HDI 模块构建通过。 | 当前 Codex 会话输出 | Build Verification | same |

## Boundary

- 本条目为 candidate/debug-record，不是 owner decision，不代表 release gate 已关闭。
- 不包含完整 raw log、设备敏感材料、二进制或 customer 文件。
- 后续若要提升为稳定 runbook 或决策，需要至少两轮同条件采样和对应补丁验证结果。
