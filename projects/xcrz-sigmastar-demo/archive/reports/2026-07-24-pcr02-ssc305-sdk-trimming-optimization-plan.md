---
id: pcr02-ssc305-sdk-trimming-optimization-plan-20260724
title: PCR02 SSC305 SDK裁剪与启动、资源、功耗优化规划
kind: project-archive
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/archive/reports/2026-07-24-pcr02-ssc305-sdk-trimming-optimization-plan.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: source-code-build-and-vendor-doc-summary
  from: PCR02 SSC305 current build workspace and local SigmaStar SSC305/SSU9383CM documentation; runtime endpoints, raw logs
    and binaries excluded
  source_sha256: cae65752545350df03f4c9aa30e8fded24f506cd0e5cd3d119819ca5066e7d63
  temporary_source_retained: false
review_after: '2026-10-24'
review_status: human-reviewed-accepted
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- pcr02
- ssc305
- sdk-trimming
- boot-optimization
- resource-optimization
- power-optimization
validation_refs:
- projects/xcrz-sigmastar-demo/archive/reports/2026-07-24-pcr02-ssc305-sdk-trimming-optimization-plan.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/archive/reports/2026-07-24-pcr02-ssc305-sdk-trimming-optimization-plan.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-07-24'
updated_at: '2026-07-26'
generated_by_ai: true
ai_role: summarized
ai_model_or_tool: Codex
ai_generated_at: '2026-07-24'
manual_validation_pending: true
summary_zh: 归档PCR02 SSC305当前SDK静态基线，明确production profile、应用release构建、显式打包清单和启动关键路径为P0，MMA、MI时钟与runtime PM为数据驱动P1，架构快启为P2；板级与功耗验证待完成。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
---

# PCR02 SSC305 SDK 裁剪与启动、资源、功耗优化规划

## 归档目的与结论边界

本文归档 PCR02 SSC305 当前 SDK、生成镜像和 SigmaStar 本地原厂资料的静态分析结论，形成启动速度、资源消耗和功耗优化的实施顺序、风险边界与验收标准。

当前可确认的核心结论是：首要问题不是 BusyBox 或某个单独驱动过大，而是调试配置进入量产、应用以 `-O0` 构建、动态链接依赖过宽、customer 全量复制、旧 staging 残留，以及启动阶段无差别加载模块叠加造成的。应先完成 production profile、应用 release 构建、显式打包清单和启动关键路径治理，再依据实机数据调整 MMA、MI 时钟、runtime PM 和 CPU governor；只有常规优化仍无法满足指标时，才评估 ramfs、IPL 直启或 DualOS/earlyinit。

本轮是只读静态分析，没有修改源项目或设备。设备运行态基线、功耗仪数据、冷启动统计和板级回归尚未完成，因此本条目保持 `reviewing`，不得据此声明量产优化已完成或发布可用。

## 目标与非目标

### 目标

- 缩短上电到应用可用、首帧和运控 ready 的时间。
- 降低双核 Cortex-A32 上的 CPU 指令开销、动态装载成本、线程调度压力和稳态功耗。
- 缩小 rootfs、customer、miservice 和内核模块集合。
- 增加 Linux 可用内存，并在不破坏媒体 pipeline 的前提下重新评估 MMA 预留。
- 保留可审计的 debug/service/production 三类配置和独立符号包。
- 建立可重复的启动、资源、功耗和低功耗唤醒验收门禁。

### 非目标

- 不在缺少功能矩阵时直接删除 Wi-Fi、Bluetooth/BSA、Camera、Display、Audio、AI、Agora、AISpeech、二维码或 OTA 能力。
- 不把 SSU9383CM 的 CPU 频率、hotplug 或 DDR auto-STR 节点直接套用到 SSC305。
- 不在缺少 MMA 高水位证据时直接大幅缩减 96 MiB MMA。
- 不在双核 A32 已有调度压力的场景下盲目切换 `powersave` 或下线 CPU1。
- 不把 raw log、设备地址、二进制、凭证或一次性现场数据写入长期知识。

## 静态基线

分析基于 2026-07-24 的 PCR02 编译工作区和生成镜像。工作区存在未提交变更和生成物，以下数据用于规划，不等同于可重复构建证明。

### 配置与镜像

- 当前 `current.configs` 使用 `xcrz_ipc_ap6303bh_512M_pcr02_v20_debug_customer_defconfig`。
- image profile 为 `spinand_MX35_512M.debug_customer_overlay.partition.config`。
- `MI_DBG=1`、`DEBUG_SUPPORT=y`、`ENABLE_PROC_DEBUG=y`，各 MI 模块 debug、MI 文件日志和高日志等级均开启。
- 名义 production defconfig 与 debug defconfig当前仅有 customer overlay 差异，production 同样保留 `CONFIG_DEBUG_SUPPORT=y`，尚不是真正的量产 profile。
- 当前生成镜像约为：kernel 3.7 MiB、rootfs SquashFS 5.1 MiB、customer SquashFS 57 MiB、customer UBI 60 MiB、miservice UBIFS 19 MiB、ubia 88 MiB。
- rootfs 使用 XZ，customer 使用 LZO。启动速度优先时不应在没有实测的情况下把 customer 改为 XZ。

### 应用构建与动态依赖

- `prog_pcr02` 通过 `-g -O0 -rdynamic -funwind-tables -ffunction-sections -fdata-sections` 构建；最终 ELF 虽已 strip，但 `-O0` 的运行时低效代码仍然存在。
- `prog_pcr02` 大小约 9.3 MiB，`.text` 约 8.7 MiB，直接 `DT_NEEDED` 数量为 135。
- 链接清单手工列入整套 Abseil、四种 Paho MQTT、Agora、AISpeech、Live555、OpenSSL、mbedTLS、多套音频和图像库。
- `--gc-sections` 已启用，但未见 production 级 `-O2/-Os`、`--as-needed` 或显式 feature link manifest。
- 大量内部模块以静态库和 `--start-group` 链接，静态注册、全局构造或过宽依赖可能阻止 section GC。

这些配置会同时增加应用冷启动的文件映射、符号查找、重定位和缺页成本，并增加稳态 CPU cycles 和能耗。

### 打包与旧产物

- `customer.mk` 对 PCR02 `bin/*` 和 `lib/*` 采用全量复制，不是显式 allowlist。
- 当前 customer 包含 `prog_product_test`、`prog_tool`、`perf`、`addr2line`、`ethtool`、SSH、Wi-Fi 调试工具、射频/产测固件和多套模型/资源。
- 生成目录仍存在 `prog_daemon`，应用启动脚本又优先选择 `prog_daemon`，而源码发布依赖中该项已被注释。这说明 staging/output 存在旧产物污染和启动错误程序的风险。
- customer 中的 `yolov5.img` 与 miservice 中的 `zhangtao.img` 大小均为 7,781,632 字节，MD5 均为 `7ff308754f3c420f9c63b1496caf23ac`，属于已确认的重复模型。应在确认加载路径和 OTA 分区边界后统一存放或跨挂载点引用。

### 启动链与内核模块

- `rcS` 在 tmpfs `/dev` 挂载前后重复执行 `mdev -s`；创建 ubiblock 后还可能再次执行两次。
- debug profile 在启动关键路径中处理 customer overlay。
- `demo.sh` 在启动应用前同步加载 40 个模块，包括 NFS/CIFS、USB host/storage、SDMMC、Wi-Fi、pstore 和大量 MI 模块。
- `mi_dummy`、`mi_shadow`、`mi_vdisp`、`mi_debug` 也被启动时加载，之后还读取 SDIO 和 debugfs 节点。
- miservice 共打包 51 个 `.ko`，约 6.56 MiB，包含 9 个 MTD 测试模块。
- kernel defconfig 启用了 MTD tests、NFS/CIFS、USB host/storage、`DEBUG_INFO`、`DEBUG_FS`、锁调试、`PERF_EVENTS` 和 `MAGIC_SYSRQ`。

SigmaStar SSC305 功耗资料明确指出，部分模块在 probe 时即打开时钟，例如 USB；未使用的模块应避免装载。串流模块时钟应从 Sensor、VIF、ISP、SCL 等前端到后端逐步下调，出现降帧或 FIFO full 后回升一档并保留余量，最终通过 `modparam.json` 固化。

### 内存

- 当前 DRAM 为 256 MiB。
- MMA 预留 96 MiB，CMA 预留 4 MiB，Linux 最终可见内存约 156 MiB。
- MMA 占物理内存 37.5%，可能存在回收空间，但必须覆盖主/子码流、显示、音频、AI、网络、OTA 和传感器并发场景，采集 MMA 高水位后再逐级调整。
- 原厂建议通过 `/proc/mi_modules/mi_sys/mi_sys0` 和 `/proc/mi_modules/mi_sys_mma/mma_heap_name0` 观察 SYS/MMA 使用。

## 实施决策

### P0：低风险、高收益

#### 1. 建立三类配置

- `pcr02_debug`：保留 MI/proc/debugfs、overlay、ADB、SSH 和测试工具。
- `pcr02_service`：保留 pstore、ADB 和必要诊断，默认关闭高频日志。
- `pcr02_production`：非 overlay、无 SSH/telnet/测试工具、关闭 MI debug/proc debug/文件日志。

量产镜像仍需保留 BuildID，并在服务器端保存未 strip ELF、ko 和共享库符号包。关闭目标机调试信息不等于丢弃故障定位能力。

#### 2. 应用 release 构建

第一阶段采用：

```text
-O2
-DNDEBUG
-ffunction-sections
-fdata-sections
-Wl,--gc-sections
-Wl,--as-needed
```

量产移除 `-O0` 和 `-rdynamic`。启动速度和 CPU 优先时先评估 `-O2`，镜像大小优先时另测 `-Os`。LTO 暂不作为第一阶段要求，因为当前存在旧工具链、第三方预编译库和静态注册风险。

构建应生成 linker map，并对以下内容做门禁：

- `DT_NEEDED` 仅包含真实依赖。
- `dlopen()` 插件进入显式运行时清单，不能因 `--as-needed` 被错误裁剪。
- 四种 Paho MQTT 只保留实际模式所需集合。
- Abseil 不再手工链接完整 catalog，尤其是测试辅助库。

#### 3. 显式打包 manifest

将 customer 的 `bin/*`、`lib/*` 全量复制改为 production/service/factory 独立 allowlist，构建使用全新 staging，禁止继承旧 output。

门禁包括：

- 非 manifest 程序不得进入镜像。
- production 不得包含 product test、开发工具、SSH 和射频测试资产。
- 每个 ELF 的 `DT_NEEDED` 必须能在 rootfs、config 或 customer 中解析。
- 相同 MD5 的大文件不得重复进入多个分区，除非有明确升级隔离理由。
- launcher 目标必须来自 manifest，不能因旧文件残留改变启动程序。

#### 4. 精简启动关键路径

启动前只加载应用首业务真正需要的模块；USB、SD、NFS/CIFS、非首业务模型和诊断服务改为延迟或按需加载。pstore 建议保留早期加载以保障异常取证。

同时：

- 去除重复 `mdev -s`。
- production 不挂 customer overlay。
- 删除量产 SDIO/debugfs 探测。
- 明确 `/config`、`/customer`、`/data` 等强依赖挂载顺序。
- OTA 分区和维护服务是否延迟，应以应用实际启动依赖为准。

### P1：必须由设备数据驱动

#### 1. MMA/CMA 定容

覆盖最重并发业务采集高水位，按以下原则逐级试验：

```text
新 MMA = 最大实测高水位 + 固定缓冲 + 15%~25% 场景余量
```

如峰值长期低于 64 MiB，可依次试验 80、72、64 MiB；每档都必须做媒体、AI、OTA、老化和 suspend/resume 回归。

#### 2. MI runtime PM

当前开启 MI normal STR，但未确认启用 `CONFIG_ENABLE_MI_RTPM`。应先裁剪 MI 模块，再启用 runtime PM，验证摄像头、显示、音频和 IPU 反复启停以及 suspend/resume，重点观察首帧、花屏、音频 pop 和恢复超时。

#### 3. MI 时钟

用 debug profile 找到 Sensor、VIF、ISP、SCL、VENC、IPU、IVE 等模块的稳定最低档位，保留业务和带宽余量后写入 production `modparam.json`。production 不应为了保留调频节点而继续开启全套 MI debug。

#### 4. CPU governor

当前默认 `ondemand`。优先通过 `-O2`、减少动态链接和减少无效唤醒降低完成同一任务所需 cycles，再评估：

- 启动阶段短时提高最小频率。
- 应用 ready 后恢复 `ondemand`。
- 活跃视频/AI阶段设置满足 deadline 的最小频率。
- 待机阶段降低频率。
- 不以关闭 CPU1 换取表面功耗下降。

CPU 调优必须与运行队列、上下文切换、IMU/TOF deadline miss、视频帧率和音频 underrun 一起验收。

#### 5. BusyBox/rootfs

BusyBox 当前约 675 KiB，只属于次要空间优化。可按功能矩阵裁剪编辑器、非必需压缩工具、桌面兼容、UTMP 和诊断 applet，但其收益远小于应用 release 构建、模块加载和显式打包治理。

### P2：架构级方案

只有 P0/P1 后仍无法满足启动指标时，才评估：

- IPL_CUST 直接启动 Linux、跳过 U-Boot。
- ramfs/ramdisk 快速启动。
- Sensor earlyinit、stream on/off、FastAE。
- DualOS/RTOS preload。
- DTR Flash。
- 启动阶段临时提高 CPU/DDR 频率。

这些方案会影响 Secure Boot、OTA/recovery、U-Boot 调试入口、内存布局、Linux/RTOS 驱动所有权和故障恢复，必须单独立项。

## 与 MCU、IMU、TOF 低功耗方案的关系

现有边界保持不变：

- IMU、TOF 在 SoC suspend/deinit 后进入低功耗保活状态。
- 中断接入 MCU，MCU 不访问传感器 I2C。
- MCU 锁存事件并唤醒 SoC，SoC 恢复后读取 MCU 事件源并访问传感器。
- IMU 由 SoC 根据唤醒后的采样判断行为；MCU 不判断拿起或翻转。
- TOF 负责目标距离内的出现/变化事件。

需要增加事件 ACK 和掉电窗口防重入机制。SigmaStar 原厂资料指出，RTCIO 事件若发生在 SoC 尚未完全下电阶段，可能导致异常上电或事件丢失；应使用 MCU/SOC 状态握手、事件锁存以及硬件或协议屏蔽窗口。

最终应比较 STR 与完整下电的总能量：

```text
STR 总能量 = STR 静态功耗 × 待机时长 + resume 能量
完整下电总能量 = MCU/传感器功耗 × 待机时长 + 冷启动能量
```

模式选择应由实际唤醒间隔和 break-even 决定，不能只比较瞬时功耗。

## 验收门禁

| 维度 | 方法 | 第一阶段建议目标 |
| --- | --- | --- |
| 冷启动 | 断电启动 30 次，测上电到应用 ready | p95 缩短至少 20% |
| 应用启动 | launcher 到显示、视频、运控 ready | p95 缩短至少 20% |
| CPU | 固定业务脚本运行 30 分钟 | `prog_pcr02` CPU 降低至少 15% |
| 传感器 | IMU/TOF loop/publish/deadline stats | IMU 接近 100 Hz、TOF 接近 15 Hz，deadline miss 不增加 |
| Linux 内存 | PSS、MemAvailable、slab | MemAvailable 增加至少 10 MiB |
| 镜像 | rootfs/customer/miservice 大小 | customer SquashFS 从约 57 MiB 降至 40-45 MiB |
| 功耗 | 电源分析仪积分 | 活跃、空闲和低功耗均无回退 |
| 稳定性 | 24-72 小时老化 | 无 OOM、MMA 失败、花屏、音频异常 |
| 低功耗 | 至少 1000 次 suspend/resume | 唤醒成功率 100%，事件源正确 |
| OTA | 全量、差分、断电恢复 | 升级、回滚和恢复正常 |

启动时间使用 `/sys/class/sstar/msys/booting_time` 分阶段分析，并在应用增加 `main entered`、pipeline ready、display ready、first frame 和 control ready 等低开销时间点。不能用“串口出现日志”代替业务 ready。

## 原厂资料适用边界

主要依据：

- SSC305 `TTFF-TTUFF-TTCL_guide_zh.html`：启动阶段时间戳、镜像大小、Flash、Sensor stream on/off 与 TTFF/TTCL。
- SSC305 `bootflow_zh.html`：Pure Linux、快速启动和 DualOS 启动路径。
- SSC305 `power_zh.html`：CCF、无用模块装载、串流模块调频和 CPU cpufreq。
- SSC305 `Memory_layout_zh.html`：Linux、MMA、RTOS 布局和运行时观察节点。
- SSC305 `SOC_power_scheme_zh.html`：MCU 唤醒、SoC 掉电窗口、RTCIO 事件丢失和防重入。
- SSU9383CM `busybox_zh.html`、`makefile_rootfs_zh.html` 和 `power_zh.html`：仅借鉴 BusyBox、打包和通用功耗调试方法。

SSU9383CM 的具体 CPU 档位、hotplug、DDR auto-STR 和节点路径不构成 SSC305 的直接配置依据；只有 SSC305 实机存在对应节点并完成原厂确认后才能采用。

## 验证状态与后续动作

### 已完成

- 读取当前生成配置、kernel defconfig、rootfs/customer/miservice 内容和启动脚本。
- 统计镜像、应用、模块和主要资源大小。
- 读取 `prog_pcr02` ELF 动态段、BuildID、strip 状态和 `DT_NEEDED` 数量。
- 校验重复 DLA 模型的大小和 MD5。
- 对照 SSC305 与 SSU9383CM 本地原厂资料核对通用方法和芯片适用边界。
- 会话 final-ready 检查通过。

### 未完成

- 目标设备 ADB 连接超时，未取得实时进程、PSS、模块、MMA、DVFS、启动和功耗基线。
- 未执行 production profile、`-O2`、`--as-needed` 或打包 manifest 的试构建。
- 未完成冷启动 30 次统计、功耗仪测量、板级老化、低功耗 1000 次循环和 OTA 回归。
- 当前编译工作区存在未提交变更，未验证 clean build 可重复性。

### 下一步

1. 新会话先实施 production profile、应用 release 构建、显式打包 manifest 和启动模块清单。
2. 连接设备后采集冷启动、PSS/MMA、CPU/DVFS、传感器 deadline 和功耗基线。
3. 用同一功能脚本完成 debug 与 production A/B，对满足门禁的结果生成独立 validation 条目。

## Provenance 与脱敏

- `captured_at`：2026-07-24。
- 来源：PCR02 SSC305 当前编译工作区静态内容、生成镜像、ELF/模块只读检查，以及仓库内 SigmaStar SSC305/SSU9383CM 原厂文档。
- 证据等级：源码和生成物静态分析；设备运行和板级验证缺失。
- 已脱敏：未保存设备地址、内网端点、凭证、raw log、二进制或本机绝对工作路径。
- memory candidate：否。本文仅为 Knowledge Hub `reviewing` archive candidate，不做 active promotion、owner decision 或 memory 写入。
