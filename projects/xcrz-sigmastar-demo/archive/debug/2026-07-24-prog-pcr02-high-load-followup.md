---
related:
- pcr02-prog-pcr02-high-load-monitoring-20260702
- pcr02-imu-tof-high-load-scheduling-triage-20260721
human_reviewed_by: null
human_reviewed_at: null
review_basis: null
incident_id: null
severity: null
affected_version: null
id: pcr02-prog-pcr02-high-load-followup-20260724
title: PCR02 prog_pcr02 高负载 2026-07-24 最新状态跟踪
kind: debug-record
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/archive/debug/2026-07-24-prog-pcr02-high-load-followup.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: manual
  from: 2026-07-24 Codex 只读源码与设备运行态跟踪；设备端点和 raw 输出不进入正文
  source_sha256: 2ac1a69b133b7de95805111872a589982dcbc531b60f61c3e0f7e6c1ac0065fc
review_after: '2026-10-24'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: verified
promotion: none
promotion_decision: none; 仅作为项目历史运行证据，不提升 active，不生成 owner decision，不作为发布门禁
tags:
- pcr02
- prog-pcr02
- cpu-load
- runtime-monitoring
- imu
- tof
- dirty-build-correlated
- no-active-promotion
validation_refs:
- projects/xcrz-sigmastar-demo/archive/debug/2026-07-24-prog-pcr02-high-load-followup.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --explain pcr02-prog-pcr02-high-load-followup-20260724
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: three-10-second-runtime-windows-plus-code-binary-identity-correlation
evidence_refs:
- projects/xcrz-sigmastar-demo/archive/debug/2026-07-02-prog-pcr02-high-load-monitoring.md
- projects/xcrz-sigmastar-demo/archive/debug/2026-07-21-pcr02-imu-tof-high-load-scheduling-triage.md
- projects/xcrz-sigmastar-demo/archive/debug/2026-07-24-prog-pcr02-high-load-followup.md
- 'runtime-capture-summary:2026-07-24T20:10+08:00; three 10-second windows; raw capture not retained'
- 'binary-identity:md5:6f5607824329854b65e0313cd53a8e35; release-build-id:862be98bb58fab31567245081ccfb76402e11c03'
- 'source-state:hdi=dcfa9ba21d018a858e15dfba079970a8daf026ec; sensor=22092f2a7c396b260315e554b84eacd9261bb3a9-dirty'
created_at: '2026-07-24'
updated_at: '2026-07-24'
generated_by_ai: true
ai_role: summarized
ai_model_or_tool: Codex
ai_generated_at: '2026-07-24'
manual_validation_pending: true
summary_zh: 2026-07-24 将 PCR02 当前 dirty 构建与设备运行二进制精确对齐，并完成三个 10 秒 CPU/线程/IRQ 窗口。IMU 由 100Hz 降至 50Hz 后线程 CPU 下降，但双核整机仍约 92%
  忙碌；主要热点转向 Agora、音频、AI 视频、3A 和媒体链路，ToF 仍以 system CPU 为主。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
---

# PCR02 prog_pcr02 高负载 2026-07-24 最新状态跟踪

## 现象

PCR02 双核 A32 设备运行最新构建时，三个连续 10 秒窗口的整机 CPU busy 为 `90.37%`、`93.06%`、`91.94%`，平均约 `91.79%`。负载仍由多个用户态与内核态线程叠加造成，不能只归因于 IMU 或 ToF。

相较前一轮基线，IMU 线程 CPU 有下降，但 ToF 线程仍稳定占用约 `7%/单核`，且主要为 system CPU。设备日志仍记录 SOC suspend 失败回滚，说明低功耗闭环尚未完成。

## 影响范围

- 项目：PCR02 / SigmaStar SSC305。
- 硬件：双核 Arm Cortex-A32。
- 进程：`/customer/bin/prog_pcr02`。
- 主要模块：Agora RTC、音频唤醒和处理、AI 视频、3A、媒体轮询、display、IMU、ToF、低功耗状态机。
- 本记录只覆盖 2026-07-24 当前 dirty 构建和当时运行场景，不代表 clean commit、量产版本或所有业务场景。

## 环境

- Linux：`5.10.117`，ARMv7，SMP PREEMPT。
- CPU：2 核，采集期间均为 `1GHz`。
- 设备程序与本地 release 制品 MD5 均为 `6f5607824329854b65e0313cd53a8e35`。
- release BuildID：`862be98bb58fab31567245081ccfb76402e11c03`。
- 本地 `.debug` BuildID：`c88798081d70b6553aa94aee3e701719c75247cd`，与运行程序不匹配。
- hdi：`dcfa9ba21d018a858e15dfba079970a8daf026ec`。
- sensor：`22092f2a7c396b260315e554b84eacd9261bb3a9-dirty`。
- 设备端点、完整 raw 日志和本机绝对源码路径不进入长期正文。

## 时间线

| 时间 | 操作或观察 | 结果 |
| --- | --- | --- |
| 2026-07-24 19:27 | hdi 合入 QMI8658 普通模式 ODR `250Hz -> 125Hz`，关闭 Acc/Gyro LPF | 驱动配置发生变化 |
| 2026-07-24 19:28 | sensor 将 IMU worker/publish 循环 `100Hz -> 50Hz` | 当前实现不再满足先前 100Hz 发布目标 |
| 2026-07-24 19:36 | 生成并部署当前 release 制品 | 本地和设备 MD5 完全一致 |
| 2026-07-24 20:10 起 | 采集版本、内存、日志、三个连续 10 秒 CPU/线程/IRQ 窗口 | 完成运行态和源码版本关联 |

## 证据

### 二进制与源码关联

- 本地和设备程序 MD5 完全一致。
- 运行程序内嵌 sensor 版本为 `22092f2-dirty`。
- 当前运行证据能够关联到本地 dirty 工作树，但不能仅靠 Git commit 重建完全相同的程序。
- `.debug` BuildID 不匹配，当前证据不能用于可靠的地址级符号解释。

### CPU 窗口

| 窗口 | 整机 busy | idle |
| --- | ---: | ---: |
| 1 | 90.37% | 9.63% |
| 2 | 93.06% | 6.94% |
| 3 | 91.94% | 8.06% |
| 平均 | 91.79% | 8.21% |

三个窗口的主要线程占单核 CPU 近似范围：

| 线程 | CPU | 观察 |
| --- | ---: | --- |
| `AgoraRTC` | 25.7%～26.4% | 第一热点，`SCHED_RR/96` |
| `ai-wakeup-aud` | 12.0%～12.4% | 音频唤醒 |
| `hdi_ai_prc0` | 10.4%～10.7% | 音频处理 |
| `ai-vi-shm` | 9.6%～10.3% | AI 视频共享链路 |
| `CUS3A` | 9.4%～9.8% | system CPU 约 6.6%，`SCHED_RR/95` |
| `task_poller` | 8.5%～9.1% | 疑似短周期轮询热点 |
| `hdi_vi_preview` | 8.4%～8.6% | 视频预览 |
| `media_poll1` | 7.3%～7.4% | 媒体轮询 |
| `sensor_tof0` | 6.9%～7.2% | 主要为 system CPU |
| `nav.poll` | 5.4%～5.9% | 持续热点 |
| `sensor_disp0` | 4.4%～5.0% | 较前一轮约 8.2% 下降 |
| `sensor_imu0` | 3.0%～3.1% | 较前一轮约 4.8% 下降 |

### IRQ 与资源

- Function-call IPI：`2586～2837/s`，与前一轮约 `2740/s` 接近。
- Reschedule IPI：约 `316/s`，调度竞争仍明显。
- I2C1：`246～256/s`；I2C2：`208～215/s`。
- BDMA：`203～210/s`；MSPI：`201～207/s`。
- `VmRSS=64708kB`，`MemAvailable=59044kB`，无 swap，`CmaFree=0`。
- SoC 健康日志显示温度由启动后的 `57℃` 上升并稳定在 `67℃`。

### 日志边界

- display 启动时两次报告 `FBIO_FBTFT_BLIT` 不可用，回退到 mmap partial refresh。
- 当前部署后多次出现 `audio_player scene=2 player is not exist`。
- 19:39 出现一次 SOC suspend 失败并回滚；IMU、ToF、TCPKA 和同步准备步骤均报告已完成，最终 suspend 返回 `-1`。
- 生产构建未输出 `sensor loop stats`，无法从应用聚合日志直接确认 IMU 50Hz 与 ToF 15Hz 的长期发布稳定性。

## 假设与排除

| 假设 | 验证动作 | 结果 | 状态 |
| --- | --- | --- | --- |
| IMU 降频降低线程 CPU | 对比前一轮约 4.8% 与当前三个窗口 3.0%～3.1% | 方向一致，但同时改变 ODR、LPF 和业务场景 | 相关性成立，因果待受控 A/B |
| ToF 是整机第一热点 | 排序全部线程 CPU | ToF 约 7%，低于 Agora、音频、AI 视频和 3A | 排除 |
| 当前高负载仅由 sensor 导致 | 聚合线程热点 | 主要 CPU 分布在 RTC、音频、视频、3A、媒体和导航 | 排除 |
| 块设备 I/O 或短期内存泄漏主导 | 对照历史多窗口和当前内存快照 | 未发现块设备 I/O 主导或短期 RSS 快速增长证据 | 当前证据不支持 |
| display 新 ioctl 已生效 | 检查启动日志 | ioctl 不可用，实际走 mmap partial refresh | 排除 |

## 根因

未确认单一根因。

当前证据支持的工作结论是：双核 A32 的高负载由 Agora RTC、音频唤醒/处理、AI 视频、3A、媒体轮询、导航和 sensor I/O 等多条链路叠加造成。IMU 降频只释放了少量 CPU，ToF 仍有明显内核态 I/O 成本，但两者都不是当前整机第一热点。

## 修复或规避

本次跟踪没有修改源码、设备配置或运行状态。设备中已存在的改动包括：

- QMI8658 普通模式 Acc/Gyro ODR 从 250Hz 降到 125Hz并关闭 LPF。
- IMU worker/publish 循环从 100Hz 降到 50Hz。
- display 合入局部刷新，但当前内核缺少 BLIT ioctl，使用 mmap 回退路径。

IMU 降为 50Hz 的副作用是偏离此前运控要求的 100Hz 发布频率。是否接受该降级必须由产品/运控需求确认，不能仅以 CPU 收益自动视为最终方案。

## 验证

- 通过 `/proc/stat` 对三个连续 10 秒窗口计算整机 busy。
- 通过 `/proc/<pid>/task/*/stat` 计算每线程 `utime/stime` 增量。
- 通过 `/proc/interrupts` 计算 IPI、I2C、ISP、BDMA、MSPI 和 SCL IRQ 频率。
- 通过 MD5 和 ELF BuildID 验证本地 release 与设备程序身份。
- 通过源码 commit 和程序内嵌版本字符串关联 hdi/sensor 状态。
- 通过 sensor 日志核对 display fallback、audio player 错误、SoC 温度和 suspend 回滚。

本记录的命令证据已在采集会话中核验；短窗口因果判断和发布频率长期稳定性仍待验证。

### 离线待验证

```yaml
manual_validation_pending: true
manual_validation_reason: 短窗口结果仍需相同业务负载下的受控 A/B、源码聚合计数和匹配 BuildID 的 debug symbols 复核
required_followup: rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
owner: leiwenjun
review_after: 2026-10-24
```

## 后续动作

1. 明确 IMU 发布目标是继续保持 100Hz，还是接受 50Hz 功耗/CPU 降级。
2. 优先对 `AgoraRTC`、音频链路、`ai-vi-shm`、`CUS3A`、`task_poller` 和媒体轮询做源码级计数。
3. 为 ToF 记录 I2C transaction、ready/not-ready、drop 和 ioctl 耗时，验证可丢帧策略是否减少无效 I/O。
4. 在同一动画和媒体场景下对 display mmap partial refresh 做受控 A/B。
5. 重新生成与 release BuildID 匹配的 `.debug` 后再做符号级热点定位。
6. 单独定位最终 SOC suspend 返回 `-1` 的内核/驱动原因。

本条目保持 `reviewing`，仅作为历史运行证据；不提升为 active fact、decision 或 release gate。

## 归档门禁

- Source：2026-07-24 当前会话的只读源码、制品和设备运行态检查。
- Topic：PCR02 双核 A32 高负载最新状态与 IMU/ToF 关联。
- Archive Candidate Path：`projects/xcrz-sigmastar-demo/archive/debug/2026-07-24-prog-pcr02-high-load-followup.md`。
- Sanitization：通过；未保存设备端点、raw 日志、二进制、本机绝对工作区路径或凭证。
- Provenance：关联 2026-07-02 高负载基线与 2026-07-21 IMU/ToF 调度分析。
- Memory Candidate：no。
- Gate Result：pending governance validation。
