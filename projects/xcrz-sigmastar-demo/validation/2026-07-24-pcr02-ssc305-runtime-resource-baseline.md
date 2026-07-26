---
aliases:
- PCR02 SSC305 SDK裁剪规划运行态基线验证
related:
- projects/xcrz-sigmastar-demo/README.md
- indexes/obsidian-home.md
- indexes/project-readiness.md
id: pcr02-ssc305-runtime-resource-baseline-20260724
title: PCR02 SSC305 SDK裁剪规划运行态基线验证
kind: validation
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/validation/2026-07-24-pcr02-ssc305-runtime-resource-baseline.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: matched-device-runtime-readonly-evidence
  from: PCR02 target runtime matched to local build artifacts; device address, raw logs, binaries and credentials excluded
  source_sha256: fa5a43e7a4f804562526aa7aba2e5b957f1ab93464e431196179dd11c3529d5b
  temporary_source_retained: false
review_after: '2026-08-24'
review_status: human-reviewed-accepted
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- pcr02
- ssc305
- runtime-baseline
- cpu
- memory
- mma
- boot-time
validation_refs:
- projects/xcrz-sigmastar-demo/validation/2026-07-24-pcr02-ssc305-runtime-resource-baseline.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/validation/2026-07-24-pcr02-ssc305-runtime-resource-baseline.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-07-24'
updated_at: '2026-07-26'
generated_by_ai: true
ai_role: summarized
ai_model_or_tool: Codex
ai_generated_at: '2026-07-24'
manual_validation_pending: true
summary_zh: 目标板只读基线确认当前固件与本地编译输出一致；prog_pcr02约占双核总容量48%、PSS约62MiB并映射139个共享库，MMA历史峰值约77MiB暂不宜缩减，启动主要空档位于用户态和应用pipeline。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
---

# PCR02 SSC305 SDK 裁剪规划运行态基线验证

## 验证目的与边界

本文为《PCR02 SSC305 SDK 裁剪与启动、资源、功耗优化规划》补充一轮目标板只读运行证据，用于校准启动、CPU、内存、MMA、动态链接和内核模块优化优先级。

本轮设备运行固件与本地当前编译输出的 `prog_pcr02`、`mi_sys.ko`、`mi_debug.ko` 校验值完全一致。采样未修改设备配置、服务、频率、模块或文件系统。

当前结论只代表一次约十分钟运行窗口，不等于冷启动统计、功耗仪验收、最大业务压力或长期老化结果。本条目保持 `reviewing`。

## 固件对应关系

- Kernel：Linux 5.10.117，SMP PREEMPT，构建时间为 2026-07-24。
- `prog_pcr02`：9,304,152 字节，设备与本地输出 MD5 均为 `9dadd3b61f28414382c56518472a3dd5`。
- `mi_sys.ko`：403,936 字节，设备与本地输出 MD5 均为 `2fd042dc966227ed099eb7abdf5ba9a9`。
- `mi_debug.ko`：470,240 字节，设备与本地输出 MD5 均为 `c4012b9f4267cf11a9d90b0c8762163e`。

校验值仅用于关联本次运行证据，不代表发布签名或安全校验。

## 启动阶段证据

`/sys/class/sstar/msys/booting_time` 的主要节点为：

| 节点 | 上电后时间 |
| --- | ---: |
| `start_kernel+` | 1.548 s |
| `do_basic_setup-` | 4.306 s |
| `ramdisk_execute_command+` | 4.331 s |
| `mi_common_init_start+` | 12.427 s |
| 第一组 `MI_SENSOR_IMPL_Init` | 19.839 s |
| 第一组 `VIF_FirstFrameDone` | 21.078 s |
| 第二组 `MI_VENC_IMPL_Init` | 32.050 s |
| 第二组 `VENC_FirstFrameDone` | 33.564 s |

据此可确认：

- `start_kernel` 到进入根文件系统约 2.78 秒。
- 根文件系统入口到第一条 MI common 初始化约 8.10 秒，是明显的用户态启动链空档。
- MI common 到第一组 Sensor 初始化约 7.41 秒，应用初始化仍有较大串行路径。
- 第一组 Sensor 初始化到第一帧约 1.24 秒。
- 第二组 VENC 首帧到达约 33.56 秒。

因此第一阶段应优先分析 `rcS`、分区挂载、模块加载、supervisor、应用动态装载和 pipeline 初始化，不应把主要精力放在继续压缩 3.7 MiB kernel。

## CPU、调度和温度

### CPU OPP

- CPU0、CPU1 均在线。
- governor 为 `ondemand`。
- `cpuinfo_min_freq`、`cpuinfo_max_freq`、`scaling_min_freq`、`scaling_max_freq` 和 `scaling_available_frequencies` 均只有 1,000 MHz。
- 当前固件虽然标记 dynamic frequency，但实际只暴露单一 OPP，`ondemand` 没有可选择的低频档位。
- 采样温度为 68°C；健康日志窗口记录 56-69°C。

在补齐 SSC305 的 OPP/电压配置之前，单纯切换 governor 不会获得有效降频收益。应先确认板级电压、IDAC、DTS/频率表和原厂限制，不得直接套用 SSU9383CM 档位。

### 五秒 CPU tick 差分

- 双核系统总 tick 增量：1,024。
- idle tick 增量：320。
- 系统约 68.75% busy、31.25% idle。
- `prog_pcr02` 增量：479 tick，即约占用一个 CPU 的 95.8%，或双核总容量的 47.9%。
- `prog_pcr02` 约贡献系统非 idle CPU 的 68%。
- 五次即时 `top` 中 `prog_pcr02` 为 24.7%-53.8%；采样工具和业务状态会引入波动，正式基线应使用固定场景和更长窗口。

系统 load average 约为 25-30，但同时存在多个 MI 内核线程的 `D` 状态。load average 会计入不可中断任务，不能直接解释为 25-30 个 CPU runnable；CPU tick 差分应作为利用率依据。

### 线程累计热点

`prog_pcr02` 有 116 个线程。累计 CPU ticks 排名前列包括：

- `ai-wakeup-aud`
- `hdi_ai_prc0`
- `AgoraRTC`
- `CUS3A`
- `ai-vi-shm`
- `task_poller`
- `hdi_vi_preview`
- `sensor_tof0`
- `sensor_disp0`
- `media_poll1`
- `hdi_ai_cap0`
- `nav.poll`
- `sensor_imu0`

这说明 CPU 优化不能只看 IMU/TOF：AI 音频、Agora、CUS3A、视频 SHM/preview、通用 poller、显示、导航和传感器线程都应进入统一唤醒率与执行周期审计。

## 进程内存与动态链接

`prog_pcr02` 当前：

- 线程：116
- 文件描述符：178
- `/proc/<pid>/maps` 条目：866
- 已映射唯一共享库：139
- PSS：约 62.35 MiB
- RSS：约 63.27 MiB
- Anonymous PSS：约 43.41 MiB
- File PSS：约 17.47 MiB
- 无 swap

运行态确认完整 Abseil 集合、四个 Paho MQTT 变体及 Agora、AISpeech、Live555、音频、图像、TLS 等共享库实际被动态装载。静态 ELF 的 135 个 `DT_NEEDED` 已转化为真实的映射、符号和页表成本，因此 `-O2`、`--as-needed`、feature link manifest 和减少不必要动态依赖仍是 P0。

设备实际进程链为：

```text
prog_daemon
  ├─ prog_cmd_server
  └─ prog_pcr02
```

因此静态分析中“可能只启动旧 daemon”的结论需要收窄：当前设备确实通过 daemon supervisor 启动了主程序。仍需用显式打包 manifest 防止非预期旧产物改变 future image 行为。

## Linux、CMA 与 MMA

### Linux 内存

- `MemTotal`：约 151.5 MiB
- `MemAvailable`：约 60.3 MiB
- `Slab`：约 17.9 MiB
- `SUnreclaim`：约 13.8 MiB
- CMA：4 MiB，当前 `CmaFree=0`
- 无 swap

Linux 尚未处于直接 OOM 状态，但主程序 PSS 约占 Linux 总内存 41%。减少主程序匿名内存、线程栈/缓存、共享库映射和未使用内核模块，优先级高于 BusyBox 的数百 KiB 裁剪。

### MMA

- 预留：96 MiB。
- 当前使用：约 69.77 MiB。
- 历史高峰：约 76.77 MiB。
- 当前可用：约 26.23 MiB。
- 相对历史峰值余量：约 19.23 MiB，约为峰值的 25%。

当前证据不支持把 MMA 直接降至 80 MiB：按历史峰值计算只剩约 3.2 MiB 余量，无法覆盖场景变化和碎片。现阶段保持 96 MiB；只有覆盖所有最大业务组合并得到更长时间高水位后，才可单独评估 88 MiB。

CMA 当前无空闲，也不应先行缩减。

## 模块运行态

设备加载 40 个模块。以下候选引用计数为 0：

- NFS v2/v3、CIFS 及相关模块
- USB storage、EHCI
- `mi_debug`
- `mi_vdisp`
- `mi_shadow`
- `mi_ive`
- `mi_dummy`

引用计数为 0 不等于一定可卸载或删除，但结合量产功能矩阵，它们是启动时不加载、按需加载或 production 不打包的首批候选。NFS/CIFS 还创建了 `rpciod`、`xprtiod`、`cifsiod`、`nfsiod` 等后台线程。

## 传感器证据边界

本次 sensor 日志中没有 `sensor loop stats` 周期统计，无法从当前固件确认：

- IMU publish 是否稳定达到 100 Hz。
- TOF publish 是否稳定达到 15 Hz。
- deadline miss、wake late、acquire/publish 最大耗时。

日志仅确认 IMU、TOF 初始化和启动成功。下一版 profiling/service 镜像应恢复低频汇总统计，避免逐帧日志。

## 更新后的优化优先级

### P0

1. `prog_pcr02` 从 `-O0` 切换至经验证的 `-O2`，保留独立符号包。
2. 使用 `--as-needed` 和 feature link manifest，把 139 个运行态共享库缩减到真实所需集合。
3. 审计 116 个线程的周期、阻塞方式和唤醒率，重点处理 AI 音频、Agora、CUS3A、视频 SHM/preview、通用 poller、显示和导航。
4. 从启动关键路径移除 NFS/CIFS、USB 和未使用 MI debug/dummy/shadow/vdisp/ive。
5. 定位根文件系统入口到 MI common 的 8.10 秒，以及 MI common 到 Sensor 初始化的 7.41 秒。
6. 建立 production/service/debug 显式打包和模块 manifest。

### P1

1. 核对 SSC305 CPU OPP、电压和 IDAC 配置，恢复经过原厂确认的多档 DVFS；在此之前不把 governor 切换列为有效优化。
2. 保持 MMA 96 MiB，完成最大场景高水位后再评估 88 MiB。
3. 评估 `SUnreclaim`、线程栈、匿名内存、缓存池和共享库 PSS。
4. 用固定业务脚本进行 10-30 分钟 CPU、上下文切换和温度 A/B。
5. 恢复 IMU/TOF 低频周期汇总统计。

### P2

只有 P0/P1 后仍不能满足指标时，才评估 ramfs、IPL 直启、Sensor earlyinit 或 DualOS。

## 未完成验证

- 未进行 30 次冷启动 p50/p95。
- 未使用功耗分析仪。
- 未覆盖 AI、主/子码流、音频、OTA、移动导航和休眠唤醒全部组合。
- 未测试移除模块、`-O2`、`--as-needed`、DVFS 或 MMA 调整后的 A/B。
- 未取得 IMU/TOF 周期统计。
- 未完成 24-72 小时老化和 1000 次 suspend/resume。

## Provenance 与脱敏

- `captured_at`：2026-07-24。
- 关联规划：`projects/xcrz-sigmastar-demo/archive/reports/2026-07-24-pcr02-ssc305-sdk-trimming-optimization-plan.md`。
- 来源：与本地当前编译输出校验一致的 PCR02 目标板，只读采集 booting_time、procfs、sysfs、MI SYS/MMA、模块和进程统计。
- 已脱敏：正文不保存设备地址、网络配置、raw log、二进制、凭证或本机绝对工作路径。
- evidence strength：匹配构建产物的单次设备只读基线；长期与功耗验证待完成。
- memory candidate：否。
