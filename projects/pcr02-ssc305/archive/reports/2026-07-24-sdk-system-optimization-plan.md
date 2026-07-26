---
id: pcr02-ssc305-sdk-system-optimization-plan-20260724
title: PCR02 SSC305 SDK系统优化实施计划
kind: project-archive
domain: projects/pcr02-ssc305
path: projects/pcr02-ssc305/archive/reports/2026-07-24-sdk-system-optimization-plan.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: source-code-runtime-and-vendor-doc-summary
  from: PCR02 SSC305 current build workspace, matched-device read-only runtime summary, local vendor documentation and existing
    Knowledge Hub evidence; endpoints, raw logs and binaries excluded
  source_sha256: 13b3575bf50c4f6fc1dae33de9c8fc2631680030219fa9d1e26214bc52961d55
  temporary_source_retained: false
review_after: '2026-10-24'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- pcr02
- ssc305
- sdk-optimization
- boot-optimization
- cpu-optimization
- resource-optimization
- power-optimization
validation_refs:
- projects/pcr02-ssc305/archive/reports/2026-07-24-sdk-system-optimization-plan.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/pcr02-ssc305/archive/reports/2026-07-24-sdk-system-optimization-plan.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-07-24'
updated_at: '2026-07-24'
generated_by_ai: true
ai_role: summarized
ai_model_or_tool: Codex
ai_generated_at: '2026-07-24'
manual_validation_pending: true
summary_zh: 基于当前编译树和匹配实机基线，归档PCR02 SSC305从Cortex-A32 Release构建、production打包、启动链、全局CPU线程、Kernel模块到功耗DVFS的分阶段优化计划、量化门槛和回退条件。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
---

# PCR02 SSC305 SDK 系统优化实施计划

## 归档目的与结论边界

本文归档 PCR02 SSC305 SDK 在启动速度、CPU 与内存资源、镜像体积和功耗方面的阶段性优化计划。计划以 2026-07-24 的编译树静态检查、与本地制品匹配的目标板只读运行基线及 SigmaStar 本地资料为依据。

当前结论是：首要收益不在 BusyBox、Kernel 文件大小或直接压缩 MMA，而在应用仍以 `-O0 -rdynamic` 构建、动态依赖和运行线程过多、production 配置仍带 Debug、customer 全量复制、启动阶段无差别加载模块，以及应用和媒体 pipeline 的周期唤醒与重复初始化。应先建立可信的 Cortex-A32 Release 基线，再依次治理镜像、启动链、全局 CPU/线程和 Kernel 模块；MI 时钟、runtime PM 与 DVFS 放在功能回归和硬件确认之后。

本文是 `reviewing` 归档候选，不代表优化已经实施、量产验证通过、owner 已签收或条目可提升为 active。

## 范围与非目标

### 范围

- PCR02 SSC305 当前 SDK 编译工作区对应的 Kernel、Boot、rootfs、customer、miservice 和 image 构建。
- 嵌套 `xcrz_sigmastar_demo` 的应用编译、链接依赖、启动关键路径和运行时 CPU/线程结构。
- 双核 Cortex-A32 上 IMU 100 Hz、TOF 15 Hz、视频、音频、AI、Agora、导航和显示的组合负载。
- production、service、factory 三类制品及其验证、符号和恢复边界。

### 非目标

- 不在缺少功能矩阵时直接删除 Wi-Fi、摄像头、显示、音频、AI、Agora、OTA、产测或售后能力。
- 不在缺少压力高水位时把 MMA 96 MiB 直接裁到 80 MiB。
- 不把 CPU affinity 或实时优先级作为高 CPU 的首要修复。
- 不在未确认板级 GPIO 和电压设计时启用 IDAC/DVS。
- 不归档设备地址、内网端点、raw log、二进制、凭证和一次性调试材料。

## 运行与构建基线

目标板关键制品 MD5 与当前编译目录输出匹配，以下数据可作为当前规划基线，但仍需在正式实施 S0 时用固定业务脚本重新采集。

| 指标 | 当前观测 |
| --- | --- |
| CPU | 双核 Cortex-A32，两个核心在线，当前只暴露 1 GHz |
| 系统 CPU busy | 5 秒快照约 68.75% |
| `prog_pcr02` CPU | 约占双核总容量 47.9%，约占系统 busy CPU 的 68% |
| 进程线程/FD/maps | 116 / 178 / 866 |
| 运行时共享库 | 约 139 个 |
| `prog_pcr02` PSS/RSS | 约 62.35/63.27 MiB |
| RAM Available | 约 61.7 MiB |
| MMA | 96 MiB，历史峰值约 76.8 MiB，峰值余量约 19.2 MiB |
| Kernel modules | 40 个 |
| `start_kernel` | 约 1.55 秒 |
| rootfs/ramdisk execute | 约 4.33 秒 |
| `mi_common` start | 约 12.43 秒，用户态空档约 8.1 秒 |
| 第一帧 VIF | 约 21.08 秒 |
| VENC 第一帧 | 约 33.56 秒 |
| customer squashfs | 约 57 MiB |

进程热点覆盖 AI wakeup、HDI audio、AgoraRTC、CUS3A、AI video shared memory、task poller、video preview、media poll、display、navigation、IMU 和 TOF，因此 CPU 优化必须覆盖整个应用，不限于传感器。

当前应用构建含 `-g -O0 -rdynamic`，直接 `DT_NEEDED` 为 135；production defconfig 仍启用 `CONFIG_DEBUG_SUPPORT=y`，当前 image 还是 debug customer overlay。customer 对 `bin/*` 和 `lib/*` 采用全量复制，并存在内容相同的大模型重复进入不同分区的情况。

## 关键技术决策

### Cortex-A32 编译目标

当前 GCC 11.1 工具链已确认支持：

```text
-mcpu=cortex-a32
-mfpu=neon-vfpv4
-mfloat-abi=hard
```

生成 ELF 的属性为 ARMv8、Thumb-2、VFPv4、NEON 和 hard-float。历史第三方优化基线中的 Cortex-A7 目标不应直接扩散到 PCR02 主应用；后续应单独修订该 runbook，避免产生 ABI/性能方向错误。

### 内存与 DVFS

- MMA 暂时保持 96 MiB；只有最大并发场景长期峰值稳定后，才先评估 88 MiB，不直接进入 80 MiB。
- CMA 当前仅 4 MiB 且运行态无空闲，暂不缩减。
- DTS 的多档 OPP 受 `CONFIG_SSTAR_VOLTAGE_IDAC_CTRL` 条件控制，当前该能力未启用，因此目标板固定 1 GHz。
- IDAC 节点涉及 PM_GPIO4/5，而当前 Wi-Fi wake 路径可能使用 PM_GPIO5。未核对原理图、管脚复用和电压范围前，不得直接启用。

## 分阶段实施计划

### S0：基线、可重复构建和功能矩阵

周期：0.5～1.5 天。

1. 固化 Git HEAD、dirty manifest、toolchain、current config、镜像 MD5 和关键 ELF/KO BuildID。
2. 从干净 staging 重建，解释与当前目标板制品的全部差异。
3. 固定空闲、音频唤醒、IMU+TOF、单双码流、AI、Agora、Wi-Fi 重连、STR、OTA 等业务场景。
4. 采集 10～30 分钟 CPU、线程 CPU、context switch、wakeups、PSS、maps、MMA/CMA、温度和功耗。
5. 完成 30 次冷启动分段统计，并恢复 IMU/TOF loop/publish/deadline 指标。

完成门槛：构建输入输出可追溯，测试场景可重复，所有必须保留功能有明确 owner 和验证方法。

### S1：应用 Release 构建和链接收缩

周期：2～4 天。

建立 `debug/release/service` 构建 profile。Release 第一阶段采用：

```text
-O2 -DNDEBUG
-mcpu=cortex-a32 -mfpu=neon-vfpv4 -mfloat-abi=hard
-ffunction-sections -fdata-sections
-Wl,--gc-sections -Wl,--as-needed
```

Release 移除 `-O0` 和全局 `-rdynamic`，保留独立 debug symbol。若主程序符号确实被插件通过 `dlsym` 使用，则采用显式 export symbol list。对完整 Abseil、四套 Paho、媒体、AI、音频和网络库按强依赖、特性依赖、`dlopen` 插件、Debug-only 分类；不能只根据 `ldd` 删除插件。

建议门槛：

- 相同场景 CPU 相对下降至少 10%～15%。
- `DT_NEEDED` 从 135 降到约 105 以下，或为保留项提供完整理由。
- file PSS 相对下降至少 15%，总 PSS 争取降至 55 MiB以内。
- IMU、TOF、音视频、AI、Agora 和 MCU 通信无功能回退。

### S2：production/service/factory 配置与打包清单

周期：2～4 天。

建立真正的三类制品：

- production：无 debug overlay、SSH/Telnet、产测和研发工具，MI 日志降为 warning/error。
- service：保留最小 ADB、pstore、perf/debugfs 等售后能力。
- factory：保留产测、射频和校准资产。

将 customer 的 `bin/*`、`lib/*` 全量复制改为显式 allowlist；每次从全新 staging 生成。排除 production 中的 product test、`prog_tool`、`perf`、`addr2line`、SSH 等研发资产；重复模型只保留一份，并验证加载路径和 OTA 分区边界。应用后编译不会进入已生成 image/OTA，任何应用变化都必须重生制品。

建议门槛：customer squashfs 从约 57 MiB降至 45 MiB以内；所有 ELF 依赖闭包通过；launcher 目标不受旧 staging 文件影响。

### S3：启动和媒体关键路径

周期：2～5 天。

从 `rootfs.mk`、`customer.mk`、`MISC_MOD_LIST`、`MI_MOD_LIST` 和应用初始化流程治理生成逻辑，不直接修改生成后的 `rcS/demo.sh`。

- production 去除 Telnet、常驻 ADB、Debug overlay、SDIO/debugfs 探测和重复 `mdev`。
- 模块分成启动必需、首帧必需、首次使用加载和 service/factory-only。
- 分析 rootfs 到 `mi_common` 的约 8.1 秒空档。
- 为 MI SYS、VIF、ISP/VPE、VENC、display、AI、audio、network 增加统一低开销时间线。
- 独立初始化最多双路并行，避免双核 A32 上形成启动风暴。
- 排查相机 pipeline 多次打开；非首屏 Agora、AI、次码流、OTA 等延迟到首帧后。

建议门槛：rootfs 到 `mi_common` 降至 4 秒以内；VENC 第一帧由约 33.56 秒降至 27 秒以内；30 次冷启动 p95 达标且无初始化竞态。

### S4：全局 CPU、线程和周期唤醒

周期：1～2 周。

按 AI/audio、Agora、CUS3A、video shared memory、task poller、preview/media poll、display、navigation、IMU/TOF 的顺序分析。统一原则：

- 周期轮询改为 `cond`、`eventfd`、消息队列或中断驱动。
- 合并同数据源和同周期线程；消费者慢时采用 latest-value/backpressure。
- 减少热路径 malloc/free、日志格式化、序列化重建和锁竞争。
- 采集与发布必要时解耦，但队列必须有严格上限。
- 定时器使用绝对 deadline。
- 先消除忙轮询和锁竞争，最后才评估 affinity 和实时优先级。

传感器门槛：

- IMU 10 分钟平均发布不低于 98 Hz，目标 100 Hz；使用采样时间戳。
- TOF 平均 14～15 Hz，允许丢旧帧，不允许积压补发。
- IMU/TOF 统一 Unix 微秒时钟域。
- `IMU_UPDATE_SUCCESS == VS_SUCCESS`，TOF 保持相同公共返回语义。
- 初始化失败清空 `pstDeviceOps`。
- 运行态关闭 IMU AMD 低功耗中断，休眠态再启用。
- MCU 只读取中断和锁存事件，SoC 唤醒后恢复传感器 I2C。

建议总门槛：`prog_pcr02` CPU 相对当前下降 25%～30%，即由双核总容量约 47.9% 降至约 34%～36%；116 个线程均可解释，活跃唤醒和 context switch 明显下降。

### S5：Kernel、模块和 Debug 裁剪

周期：3～5 天。

先建立功能—模块矩阵，再从 production 自动加载列表取消 NFS/CIFS、USB storage/EHCI、`mi_debug`、`mi_vdisp`、`mi_shadow`、`mi_ive`、`mi_dummy` 等候选，完成动态加载和 STR 回归后才关闭编译配置。Kernel DEBUG、debugfs、perf、sysrq、MTD tests 等按 production/service 分离；production 保留 pstore、BuildID 和最小 crash 取证。

不在运行设备上批量卸载模块，不把仅 3.7 MiB 的 Kernel 文件尺寸作为主优化方向。

### S6：MI 时钟、runtime PM 与 CPU DVFS

周期：1～2 周，依赖板级确认和功耗仪。

先建立启动、亮眼、灭屏、音频唤醒、单双码流、AI、Agora、STR 和完整关机的功耗基线；再逐级降低未使用 MI 时钟、引入 runtime PM 和严格引用计数。串流时钟按 Sensor/VIF/ISP/SCL/VENC 前后级逐项调整，出现降帧或 FIFO full 即回升并留余量。

DVFS 分两条路线：

1. 固定合格电压下评估 600/800/1000 MHz。
2. 原理图和 GPIO/电压确认后，评估 IDAC 电压频率联合调节。

建议目标：空闲亮眼功耗下降至少 15%，灭屏待机下降至少 20%，相同环境温度下降 3～5℃，满负载性能和实时性不回退。

### S7：条件性架构快启

只有 S0～S6 后仍不满足指标时，单独立项评估 IPL 直启、ramfs、early-init、DualOS 和更激进分区布局。该阶段会影响 Secure Boot、OTA/recovery、内存布局和故障恢复，不与普通优化提交混合。

## 总体验收目标

| 指标 | 当前 | 完整目标 |
| --- | ---: | ---: |
| `prog_pcr02` CPU | 双核总容量约 47.9% | 约 34%～36% |
| PSS | 约 62.35 MiB | 50～55 MiB |
| 共享库映射 | 约 139 | 90～100 |
| VENC 第一帧 | 约 33.56 秒 | 不高于 27 秒 |
| rootfs 到 MI 空档 | 约 8.1 秒 | 不高于 4 秒 |
| customer squashfs | 约 57 MiB | 不高于 45 MiB |
| RAM Available | 约 61.7 MiB | 不低于 70 MiB |
| IMU | 目标 100 Hz | 10 分钟平均不低于 98 Hz |
| TOF | 目标 15 Hz | 平均 14～15 Hz，无积压 |
| MMA 峰值裕量 | 约 19.2 MiB | 保持至少 15%安全余量 |

## 回退、停止和恢复

每个阶段保存修改前后 BuildID/MD5、配置 diff、功能矩阵、CPU/内存/启动/功耗结果和可恢复镜像。每个独立优化项最多修正两轮；出现冷启动失败、p95 回退超过 5%、传感器频率或时间戳异常、音视频持续丢帧、suspend/resume/MCU 唤醒异常、OTA/产测缺失、MMA/CMA 分配失败、Kernel panic 或文件系统损坏时立即回退该项。

代码基线、产品功能矩阵、板级 GPIO 或电压设计变化时，相关结论视为过期并重新执行 S0、S5 或 S6。

## 首个实施迭代

首轮控制在 3～5 个工作日，只做：

1. 建立 `debug/release/service` 应用 profile。
2. Release 使用 `-O2 + cortex-a32` 并保留独立 symbol。
3. 引入 `--as-needed` 和链接依赖报告，不激进手删库。
4. 建立关闭 Debug overlay/MI Debug 的 production defconfig。
5. 建立 production customer allowlist 并排除明显研发工具。

首轮不做 DVFS/IDAC、MMA/CMA 缩减、批量 Kernel 删除、全局 LTO/`-O3`/`fast-math`、大规模线程重构或启动架构变更。

## Provenance、替代关系与验证状态

- captured_at：2026-07-24。
- source：PCR02 SSC305 当前编译树静态检查、与本地制品匹配的目标板只读运行摘要、SigmaStar 本地资料和已有 Knowledge Hub 规划/验证条目。
- related evidence：
  - `projects/xcrz-sigmastar-demo/validation/2026-07-24-pcr02-ssc305-runtime-resource-baseline.md`
  - `projects/pcr02-ssc305/current/runbooks/thirdparty-build-optimization-baseline.md`
- successor candidate：本文是 `projects/xcrz-sigmastar-demo/archive/reports/2026-07-24-pcr02-ssc305-sdk-trimming-optimization-plan.md` 的正确项目路由和运行基线更新版。旧条目暂作历史来源；未执行 retire/supersede 生命周期变更。
- sanitization：已移除设备地址、内网端点、raw log、二进制和临时调试过程，只保留可复用汇总。
- verification：静态配置、ELF 属性、制品匹配和运行摘要已只读核对；优化实施、功耗仪、30 次冷启动、长期老化、1000 次 suspend/resume 和 OTA 回归仍待完成。
- memory candidate：否。
