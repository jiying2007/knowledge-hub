---
id: pcr02-schematic-first-batch-optimization-20260802
title: PCR02 原理图首批系统优化落地
kind: decision
domain: projects/pcr02-ssc305
path: projects/pcr02-ssc305/decisions/pcr02-schematic-first-batch-optimization-20260802.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: schematic-and-implementation
  from: PCR02_MAIN_V2.0_20251211.pdf and pcr02_ssc305_compile
  source_sha256: dfaf9d47470314bb1ea65dd7a5805f714bd084bfc09e950a3f6c74f99e4f7f34
review_after: '2026-11-02'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; reviewing capture does not authorize deployment
tags:
- pcr02
- ssc305
- tickless
- kernel-trimming
- mi-module
- image-size
- boot-time
- low-power
validation_refs:
- projects/pcr02-ssc305/decisions/pcr02-schematic-first-batch-optimization-20260802.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: schematic-plus-source-build-image-hil-pending
created_at: '2026-08-02'
updated_at: '2026-08-02'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-08-02'
manual_validation_pending: true
summary_zh: PCR02 首批明确优化将 production 与 debug 启动参数隔离，production 启用 tickless、关闭测试和网络文件系统能力，并按现有双屏依赖移除未用 MI display 模块及工厂通用资源；源码和镜像门禁通过，板端功耗、启动与功能回归待完成。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
aliases:
- PCR02 schematic first batch optimization
related:
- projects/pcr02-ssc305/decisions/pcr02-unused-io-ble-kernel-policy-20260802.md
- projects/pcr02-ssc305/README.md
---

# PCR02 原理图首批系统优化落地

## 决策

第一批只落地硬件与当前依赖证据明确、可由 production/debug 对照回退的项目：

- 将共享板级 DTS 拆为 common dtsi，并为 production/debug 提供独立 wrapper。
  production 删除 `nohz=off`、`user_debug=31` 和冗余 android console 参数，
  保留业务串口 console；debug 保持原诊断参数。
- production 内核关闭 MTD tests、JBD2 debug、NFS 与 CIFS；debug 保留维护能力。
- production 镜像不打包 `mi_disp`、`mi_fb`、`mi_vdisp`、`mi_debug`。现有
  两块 ST77912 屏使用 fbtft/SPI；依赖扫描仅发现被裁组内部的
  `mi_fb -> mi_disp`，未发现保留模块反向依赖。
- production 不打包 `wcnmodem.bin`、AP6303 mfg RF 固件、UWE Bluetooth
  目录、通用 LCM 和 test 目录；正常 Wi-Fi 固件、BLE HCD 和源码资产保留。

## 证据和边界

- 原理图来源 SHA256：
  `dfaf9d47470314bb1ea65dd7a5805f714bd084bfc09e950a3f6c74f99e4f7f34`。
- production profile verify、kernel build 和完整镜像构建通过；分区尺寸、启动
  环境一致性、load-address check 均通过。
- production 生成产物反向扫描确认四个 MI 模块、五类通用/工厂资源和相关
  启动项不存在；`mi_common`、`mi_sys`、`kdrv_sdmmc` 等核心模块保留。
- 四个 MI 模块未 strip 源文件合计 881,044 字节；资源源文件约 1.25 MiB。
  最终分区使用压缩和固定布局，因此不能把两者简单相加作为 OTA 减小量。
- source/build/image gate 不证明功耗或启动收益；未自动刷机、未测待机电流、
  冷启动 p95、温升或完整业务矩阵。

## 运行态风险与回退

- 项目存在独立 U-Boot `KERNEL_BOOT_ENV`，可能覆盖 DTS bootargs。板端必须以
  `/proc/cmdline` 确认 `nohz=off` 已消失，并通过 timer/idle 统计确认 tickless。
- 刷机后验证双屏显示/动画/休眠恢复、Wi-Fi/SDIO、BLE 按需启停、OTA、维护
  能力、30 次冷启动 p95 和待机电流。任一失败即恢复 production 删除清单或
  使用 debug 镜像定位。
- 产测或维修若依赖 mfg/UWE/LCM/test 资源，应由 owner 明确归属；不能因为
  production 裁剪而删除源码资产或 debug 维护路径。

## CMA 4MiB 一致性补充

2026-08-02 复核发现 CMA 曾存在三层声明：产品/U-Boot boot env 为 4M、PCR02
kernel fallback 为 2M、DT `linux,cma-default` 动态池为 16M。内核源码确认，
命令行存在 `cma=` 时会绕过 DT CMA 初始化，失败清理路径释放已动态预留的 DT
区域，再由命令行建立 4M 默认池。因此正常设备不是 20M 双重占用，但 bootargs
缺失或直接 DTB 启动会落到 16M，属于异常路径配置漂移。

现已把 production/debug 产品配置、内核 fallback、DTS bootargs 和 DT reserved
CMA 全部统一为 4MiB，并在 `build.sh verify` 增加七项一致性检查。双 profile
verify、双内核和双 DTB 构建通过。历史板端记录曾显示 `CmaTotal=4096 kB`、
`CmaFree=0` 稳定；零空闲是容量风险信号，但没有 CMA/DMA 分配失败证据，当前不
盲目扩到 8M/16M。后续以媒体全负载、反复启停和休眠恢复的分配失败日志与峰值
决定是否扩容。

## Archive evidence

- Captured at: 2026-08-02 Asia/Hong_Kong.
- Sanitization: 不保存 raw build log、设备地址、凭证、二进制或 runtime state。
- Provenance: 原理图哈希、仓库相对路径、配置/DTS、双 profile 构建与产物断言。
- Memory candidate: no; reviewing decision only.
- Gate result: pass for archive candidate; HIL and owner review pending.
