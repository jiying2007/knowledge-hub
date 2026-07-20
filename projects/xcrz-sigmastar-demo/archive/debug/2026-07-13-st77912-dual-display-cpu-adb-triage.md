---
related:
- xcrz-sigmastar-demo-dual-screen-animation-analysis-20260514
incident_id: xcrz-display-cpu-20260713
severity: performance-investigation
affected_version: prog_pcr02 BuildID 12b409b4155645bc19f5af5fb099d302d9663302
id: xcrz-sigmastar-demo-st77912-dual-display-cpu-adb-triage-20260713
title: PCR02 ST77912 双屏显示 CPU 热点 ADB 实机排障记录
kind: debug-record
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/archive/debug/2026-07-13-st77912-dual-display-cpu-adb-triage.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: session-debug-summary
  from: 2026-07-13 read-only ADB verification; endpoint and raw artifacts excluded
  source_sha256: a274ba6016d703aebbdf351fe24a832414ac1152f16d4ec8b20db7d127cc522a
review_after: '2026-08-13'
review_status: human-reviewed-accepted
content_review_status: accepted
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- pcr02
- display
- st77912
- lvgl
- spi
- performance
- adb
validation_refs:
- projects/xcrz-sigmastar-demo/archive/debug/2026-07-13-st77912-dual-display-cpu-adb-triage.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
artifact_refs:
- device:/customer/bin/prog_pcr02#buildid=12b409b4155645bc19f5af5fb099d302d9663302
evidence_strength: runtime-confirmed-with-scoped-limitations
evidence_refs:
- projects/xcrz-sigmastar-demo/archive/debug/2026-07-13-st77912-dual-display-cpu-adb-triage.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-07-13'
updated_at: '2026-07-19'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: OpenAI Codex
ai_generated_at: '2026-07-13'
manual_validation_pending: true
summary_zh: ADB 实机确认 sensor_disp0 是双屏 LVGL 渲染主线程、sensor_disp1 是共享 flush worker；部署版本 full_refresh=1，双屏共享 36 MHz SPI0 并发生理论带宽超订阅，整机高
  system CPU 则为多条媒体与传感器链路叠加。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
---

# PCR02 ST77912 双屏显示 CPU 热点 ADB 实机排障记录

## 摘要

本文记录 2026-07-13 对 PCR02 测试设备进行的只读 ADB 排障。实机证据确认：`sensor_disp0` 是双显示场景更新与 LVGL 软件渲染的主要线程，并非 `/dev/fb0` 的专属 flush 线程；`sensor_disp1` 才是两块显示设备共用的 flush worker。部署版本对两块 `240x240 RGB565` 屏均启用了 `full_refresh=1`，且 `/dev/fb0`、`/dev/fb1` 共用一个 36 MHz SPI 控制器，双屏全帧刷新需求超过总线理论吞吐。

本次也排除了“整机约 40% system CPU 主要由 SPI 显示造成”的说法。短时采样显示，系统态开销分布在摄像头、3A、VENC、音频、RTC、TOF、导航和显示等多条链路；显示是可确认的热点与带宽瓶颈，但不是整机高负载的唯一原因。

## 适用范围

- 项目：`xcrz-sigmastar-demo`。
- 模块：`modules/sensor/display`、Linux framebuffer、fbtft/ST77912、SPI0。
- 设备环境：ARMv7 双核 Linux 5.10.117 测试设备，ADB over TCP 地址已脱敏。
- 部署程序：`/customer/bin/prog_pcr02`，BuildID `12b409b4155645bc19f5af5fb099d302d9663302`。
- 结论只适用于上述部署程序与 2026-07-13 的运行配置，不直接代表工作区未部署代码，也不适用于假设的 54 MHz SPI 配置。

## 现象

- BusyBox `top` 的线程视图中，`sensor_disp0` 经常是 `prog_pcr02` 内最高的单个用户态线程，动画阶段出现明显突发。
- 整机 CPU 同时表现为用户态和系统态都高，短时区间约为 51% user、40.7% system、8.3% idle。
- load average 在观察期间约为 27 至 32，并伴随多个媒体相关任务处于 `D` 或 `DW` 状态。
- 现场最初将 `sensor_disp0` 理解为 `/dev/fb0` 专属显示线程，并据此推断高 system CPU 主要来自 SPI；该映射需要实机纠正。

## 影响范围

- 动画或频繁 invalidation 时，双屏 LVGL 全帧软件渲染会增加 `sensor_disp0` 用户态 CPU。
- 两块 ST77912 共用 SPI0，双屏全帧刷新存在确定的带宽超订阅，可能表现为等待、合并、丢帧或实际帧率下降。
- 整机高 system CPU 还包含摄像头、ISP/3A、编码、音频、RTC、TOF 和导航等路径，不能只通过显示优化解释或消除。
- 本次没有确认功能性故障，也没有执行重启、配置修改、二进制替换或发布动作。

## 环境

| 项目 | 实机值 | 证据性质 |
| --- | --- | --- |
| 内核 | Linux 5.10.117，ARMv7，双核 SMP | 运行时直接读取 |
| 主进程 | `prog_pcr02`，采样时 PID 928、117 个线程 | 运行时快照；PID 可变 |
| 显示线程 | TID 995=`sensor_disp0`，TID 994=`sensor_disp1` | 运行时快照；TID 可变 |
| framebuffer | `/dev/fb0`、`/dev/fb1`，驱动名均为 `fb_st77912` | sysfs 直接读取 |
| 分辨率 | 两屏均为 240×240、RGB565、115200 bytes/frame | 应用初始化日志与计算 |
| LVGL/flush 配置 | `double_buf=false`、`single_fb_direct=false`、`direct_mode=0`、`full_refresh=1`、`partial_enabled=0`、`vsync_supported=false` | 应用初始化日志 |
| SPI 拓扑 | `spi0.0` 与 `spi0.1` 共用 `1f222000.spi` | sysfs 与设备树直接读取 |
| SPI 频率 | `spi-max-frequency=36000000`，即 36 MHz | 设备树属性直接读取 |
| fbtft 帧率属性 | `fps=30` | 设备树属性；不是实际送达帧率测量 |
| 部署程序校验 | MD5 `903bf364b93a3874d6080f8d8b953dd5`；SHA256 `07a299a5536d211986d08a3bc235fb5d9891455b21027fb8da80e39d84f50c14` | 设备端与一次性本地 pull 交叉校验 |

## 时间线

| 时间 | 操作或观察 | 结果 |
| --- | --- | --- |
| 2026-07-13 | 通过已授权的 ADB 通道建立只读连接 | 设备可访问；未写配置、未重启进程 |
| 2026-07-13 | 核对进程、线程名、线程等待点和应用日志 | 确认 `sensor_disp0`/`sensor_disp1` 角色与运行时 full-refresh 配置 |
| 2026-07-13 | 首次临时拉取设备程序并核对文件长度与 hash | 拉取文件不完整，即使命令返回成功也不采信；该份证据被拒绝 |
| 2026-07-13 | 重试拉取并核对文件长度、MD5、SHA256、BuildID | 8,560,112 bytes，与设备 hash 一致；临时文件未进入源码仓或知识库 |
| 2026-07-13 | 对热点线程和全局 CPU 计数做约 7 秒差分 | `sensor_disp0` 为显示用户态主热点；整机 system CPU 来自多条链路 |
| 2026-07-13 | 核对 framebuffer、SPI sysfs 与设备树属性 | 两屏共用 36 MHz SPI0；纠正原先 54 MHz 假设 |
| 2026-07-13 | 计算双屏全帧吞吐并形成因果模型 | 25 fps 和 30 fps 两种目标下都超过总线理论吞吐 |

## 当前结论

### 已确认事实

1. `sensor_disp0` 是显示管理器的场景更新和 LVGL task/render 主循环，会驱动两块显示，不是 `/dev/fb0` 专属线程。
2. `sensor_disp1` 对应 `DisplayProvider::flushWorker()`，负责两块 framebuffer 的共享 flush 队列；空闲采样通常等待 futex，CPU 显著低于 `sensor_disp0`。
3. 部署版本两屏都使用单 framebuffer、无 direct mode、`full_refresh=1`、`partial_enabled=0`。动画触发 invalidation 时，每帧更容易产生整屏软件渲染。
4. `/dev/fb0` 和 `/dev/fb1` 分别映射到 `spi0.0` 和 `spi0.1`，但共享同一个 `1f222000.spi` 控制器。设备树实值是 36 MHz，而非此前假设的 54 MHz。
5. `sensor_disp0` 可在动画期间成为最显眼的单线程热点，但整机高 system CPU 还存在多个稳定热点，不能归因于显示单一路径。
6. load average 包含多个不可中断等待任务；不能把 load 数字直接等价为正在执行的 CPU 工作量。

### 带宽计算

单屏一帧原始像素量：

```text
240 × 240 × 2 = 115200 bytes/frame
```

36 MHz SPI 的理想字节吞吐上限：

```text
36000000 / 8 = 4.5 MB/s
```

双屏全帧 25 fps 的原始像素需求：

```text
115200 × 2 × 25 = 5.76 MB/s
5.76 / 4.5 = 128%
```

双屏全帧 30 fps 的原始像素需求：

```text
115200 × 2 × 30 = 6.912 MB/s
6.912 / 4.5 = 153.6%
```

不计命令、片选、D/C GPIO、调度、copy 和协议开销时，两屏平均可获得的理想全帧上限约为：

```text
4500000 / 115200 / 2 ≈ 19.5 fps/display
```

因此，只要两屏都持续全帧刷新，总线超订阅是确定事实；设备树 `fps=30` 只是驱动目标属性，不代表每块屏能实际稳定送达 30 fps。

### 因果模型

```text
动画或场景变化
  -> sensor_disp0 更新双屏场景并执行 LVGL 软件渲染
  -> full_refresh=1 放大为接近整屏的渲染与 flush 请求
  -> 请求进入共享 sensor_disp1 flush worker
  -> fb0/fb1 竞争同一个 36 MHz SPI0
  -> 等待、合并、降低有效帧率或丢弃过期帧
```

该模型解释了显示线程用户态热点和下游总线瓶颈，但不把整机全部 system CPU 都归入这条链路。

## 证据

### CPU 差分样本

采样窗口由设备时间戳确认约为 7 秒，系统 `CLK_TCK` 按实机计数解释。以下比例用于量级判断，不代表长时间平均值。

| 上下文 | 起点 user/system tick | 终点 user/system tick | 增量 | 解释 |
| --- | ---: | ---: | ---: | --- |
| `sensor_disp0` | 8044/205 | 8158/207 | 116 | 约占单核 16.6%，显示用户态主热点 |
| `sensor_disp1` | 409/236 | 417/239 | 11 | 约占单核 1.6%，多数时间等待 flush 条件 |
| 内核 `spi0` 线程 | 0/264 | 0/268 | 4 | 约占单核 0.6%；不包含可能落在通用 kworker/IRQ 的全部显示成本 |
| 全局 CPU | user +673、system +537、idle +109、softirq +1 | — | 1320 | 约 51% user、40.7% system、8.3% idle |

上述三个明确显示上下文合计 131 tick，约为该窗口全部 CPU tick 的 9.9%。这是已知线程的归属结果，不是显示总成本的严格上限，因为 fbtft deferred work、通用 kworker 和 IRQ 仍可能承载部分开销。

同一窗口内还观察到 `hdi_vi_preview`、`ai-wakeup-aud`、`CUS3A`、`AgoraRTC`、`hdi_ai_prc0`、`task_poller`、`ai-vi-shm`、`sensor_tof0`、`nav.poll`、`hdi_ai_cap0`、`venc0_P0_MAIN` 等持续消耗 CPU，支持“整机高系统态为多路径叠加”的结论。

### Evidence Index

命令中的 `<ADB_SERIAL>`、`<PID>` 和 `<TID>` 是脱敏或易变占位符。所有设备命令均为读取操作。

| 层级 | 命令或证据路径 | 退出码 | 摘要 |
| --- | --- | ---: | --- |
| 运行时 | `rtk adb -s '<ADB_SERIAL>' shell 'cat /proc/<PID>/task/<TID>/comm'` | 0 | 读取线程名，确认 `sensor_disp0` 和 `sensor_disp1` |
| 运行时 | `rtk adb -s '<ADB_SERIAL>' shell 'cat /proc/<PID>/task/<TID>/wchan'` | 0 | 空闲样本分别出现 `hrtimer_nanosleep` 与 `futex_wait_queue_me`，未观察到无条件忙循环 |
| 运行时 | `rtk adb -s '<ADB_SERIAL>' shell 'cat /proc/<PID>/task/<TID>/stat'` | 0 | 两个时间点读取线程 tick，形成约 7 秒 CPU 差分 |
| 运行时 | `rtk adb -s '<ADB_SERIAL>' shell 'cat /proc/stat'` | 0 | 同期读取全局 CPU tick，计算 user/system/idle 比例 |
| 运行时 | `rtk adb -s '<ADB_SERIAL>' shell 'grep "fb init" /data/log/prog_pcr02/sensor/sensor.log'` | 0 | 两屏均为 240×240 RGB565、`full_refresh=1`、`partial_enabled=0` |
| 运行时 | `rtk adb -s '<ADB_SERIAL>' shell 'readlink -f /sys/class/graphics/fb0/device'` | 0 | `fb0` 映射到 `spi0.0`；对 `fb1` 同法确认 `spi0.1` |
| 运行时 | `rtk adb -s '<ADB_SERIAL>' shell 'od -An -tx1 /sys/firmware/devicetree/base/soc/spi@1f222000/st77912@0/spi-max-frequency'` | 0 | 大端字节 `02 25 51 00`，即 36,000,000 Hz；`@1` 同值 |
| 运行时 | `rtk adb -s '<ADB_SERIAL>' shell 'od -An -tx1 /sys/firmware/devicetree/base/soc/spi@1f222000/st77912@0/fps'` | 0 | 大端字节 `00 00 00 1e`，即 30；`@1` 同值 |
| 制品 | `rtk adb -s '<ADB_SERIAL>' shell 'sha256sum /customer/bin/prog_pcr02'` | 0 | 设备 SHA256 与完整的临时 pull 一致 |
| 制品 | `rtk readelf -n /tmp/<TRANSIENT_BINARY>` | 0 | BuildID 为 `12b409b4155645bc19f5af5fb099d302d9663302`；临时二进制不归档 |
| 源码 | `rtk rg -n 'sensor_disp0|sensor_disp1|flushWorker|taskHandler' modules/sensor/display` | 0 | 工作区快照将 `sensor_disp0` 映射到场景/LVGL 更新循环，将 `sensor_disp1` 映射到共享 flush worker |

注意：首次 `adb pull` 虽返回成功，但文件长度小于设备端长度，因而被判为无效证据。只有重试后文件长度、MD5 和 SHA256 全部一致的副本才用于 BuildID 识别。这说明传输命令退出码不能替代制品完整性校验。

## 假设与排除

| 假设 | 验证动作 | 结果 | 状态 |
| --- | --- | --- | --- |
| `sensor_disp0` 存在异常死循环 | 读取 `wchan`、线程 tick，并观察 BusyBox 线程 top | 可见 `hrtimer_nanosleep`，CPU 随动画突发，不符合无条件忙循环 | 已排除 |
| `sensor_disp0` 是 `/dev/fb0` 专属 flush 线程 | 对照线程命名、二进制字符串和显示源码 | 它驱动双屏场景/LVGL；共享 flush worker 是 `sensor_disp1` | 已排除 |
| 设备正在使用 54 MHz SPI、25 fps fbtft 配置 | 读取两块 ST77912 设备树属性 | 实机为 36 MHz、`fps=30` | 已排除 |
| 整机约 40% system CPU 主要由 SPI 显示造成 | 对线程 tick、内核线程和其他热点做同期差分 | 多媒体、传感器和通信线程均有显著消耗；显示已知上下文只占总 tick 的一部分 | 已排除单因归因 |
| `full_refresh=1` 放大显示用户态和总线负载 | 核对运行时初始化配置、帧大小和 SPI 理论吞吐 | 机制与带宽超订阅已确认；精确收益仍需部署 partial-refresh 版本做 A/B | 部分确认 |
| 工作区当前 partial-refresh 改动可以直接解决问题 | 本次未部署、未重启，且部署 BuildID 与工作区代码状态不同 | 尚无实机前后对比 | 未确认 |

## 根因

根因状态：**部分确认**。

- `sensor_disp0` 高用户态 CPU 的直接原因，是它承担双屏场景更新和 LVGL 软件渲染；部署版本的 `full_refresh=1` 使动画期间的渲染范围接近整屏。
- 显示链路的下游约束，是两块屏共享 36 MHz SPI0。双屏全帧 25 fps 或 30 fps 的原始像素需求都超过理论总线吞吐，因此总线竞争与有效帧率受限不可避免。
- 整机高 system CPU 与高 load 的根因不是单一显示路径，而是显示、摄像头/ISP/3A、VENC、音频、RTC、TOF、导航等链路叠加。尚未通过 ftrace/perf 将所有通用 kworker 与 IRQ 成本精确归属。

## 修复或规避

本次只读排障没有实施修复。可按以下优先级进行后续实验：

1. 在明确授权后，对部署版本 `full_refresh=1` 与工作区 `full_refresh=0` 加 dirty-area 合并方案做同场景 A/B；同时记录视觉残留、线程 tick、SPI IRQ 和实际送达帧率。
2. 在 flush 队列中合并相邻 dirty area，并在积压时丢弃过期帧、只保留最新状态。
3. 将两屏刷新节拍错开，避免同一时刻竞争 SPI0；静止场景改为按需刷新，动画帧率与驱动上限解耦。
4. 如果产品要求双屏持续全帧 25 fps，需重新核对可稳定工作的 SPI 时钟、协议开销和控制器能力，或评估具有硬件扫描输出的显示路径；36 MHz 原始带宽不足以满足该目标。
5. 若要解释剩余 system CPU，应使用 ftrace/perf 或等价内核观测工具分别归属 fbtft deferred work、kworker、IRQ、VENC、ISP 和音频路径，不能继续用线程名推断。

## 验证

本次验证通过以下判据：

- 线程名、等待点、CPU tick、应用初始化日志和 sysfs/设备树信息来自同一台设备、同一部署程序的只读快照。
- 接受的本地临时程序副本与设备文件长度、MD5、SHA256 一致，BuildID 可追溯；不完整的首次 pull 被显式拒绝。
- 带宽结论只使用实机 36 MHz 属性和明确的像素格式计算，不把设备树 `fps` 当作实际测得帧率。
- 结论区分了已知显示线程成本与未归属的 kworker/IRQ 成本，也区分了显示热点与整机多路径高负载。
- 未执行部署 A/B，因此不声明 partial refresh 已经降低 CPU 或已经解决残影。

### 离线待验证

```yaml
manual_validation_pending: true
manual_validation_reason: 尚未获得部署、重启和同场景 A/B 测试授权，partial-refresh 收益与视觉正确性未验证。
required_followup: 在相同动画与媒体负载下，对 full_refresh=1 和 full_refresh=0 版本采集线程 tick、SPI IRQ、实际帧率、残影与丢帧结果。
owner: leiwenjun
review_after: 2026-08-13
```

## 风险与限制

- CPU 计数窗口约 7 秒，只能说明该场景的量级，不能替代长时间、多动画状态统计。
- `sensor_disp0` 的源码角色映射参考了工作区快照和部署二进制字符串；工作区含未部署改动，因此不把当前源码行号视为部署 BuildID 的逐字匹配证明。
- fbtft deferred work 可能运行在通用 kworker 或 IRQ 上，`sensor_disp0 + sensor_disp1 + spi0` 的 9.9% 不能作为显示总成本上限。
- 设备树 `fps=30` 是配置值，不是面板实际完成刷新率；本次没有逻辑分析仪或帧完成 trace。
- 应用工作区可见约 40 ms 的节拍设计，但本次没有反汇编确认部署程序的精确动画周期，因此带宽表同时给出 25 fps 与 30 fps 两种边界。
- 本文不保存设备地址、现场凭据、原始日志、core、拉取二进制或客户数据。

## 后续动作

- 取得状态变更授权后执行 partial-refresh A/B，验收指标至少包括：双屏残影、动画完整性、`sensor_disp0`/`sensor_disp1` CPU、全局 user/system/idle、SPI IRQ、有效帧率和 flush 队列积压。
- A/B 结果通过后，再决定是否将 dirty-area 合并和刷新节拍写入项目 runbook 或 validation；本条在人工复核前只保留为 `reviewing` 归档候选。
- 本条与 `xcrz-sigmastar-demo-dual-screen-animation-analysis-20260514` 相关，但后者是 2026-05-14 的历史源码分析，两者证据时间和性质不同，不互相 supersede。

## Review

- owner：`leiwenjun`
- review_after：`2026-08-13`
- 复核重点：部署 BuildID 与源码映射、partial-refresh A/B、视觉正确性、显示内核成本归属。
- 复核命令：`rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics`
- 当前状态：AI 起草、实机证据已采集、人工复核与状态提升待完成。
