---
id: pcr02-schematic-second-batch-static-optimization-20260802
title: PCR02 原理图第二批静态优化决策
kind: decision
domain: projects/pcr02-ssc305
path: projects/pcr02-ssc305/decisions/pcr02-schematic-second-batch-static-optimization-20260802.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: schematic-and-source-audit
  from: PCR02_MAIN_V2.0_20251211.pdf and pcr02_ssc305_compile static audit
  source_sha256: 44a39fc06886686e7915418eb5ab28c46cd733d2244c5e32e47aafbed8815666
review_after: '2026-11-02'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- pcr02
- ssc305
- kernel-trimming
- device-tree
- memory-layout
- low-power
validation_refs:
- projects/pcr02-ssc305/decisions/pcr02-schematic-second-batch-static-optimization-20260802.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/pcr02-ssc305/decisions/pcr02-schematic-second-batch-static-optimization-20260802.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-08-02'
updated_at: '2026-08-02'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-08-02'
manual_validation_pending: true
summary_zh: PCR02 第二批静态优化统一异常启动路径内存参数，显式关闭无硬件 EMAC/HDMITX/PNL，并在 production 裁剪纯诊断、PS2/UHID 及无产品消费者文件系统能力；CMA 保持 4MiB，板端 HIL
  待完成。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
aliases:
- PCR02 原理图第二批静态优化决策
related:
- projects/pcr02-ssc305/README.md
- indexes/obsidian-home.md
- indexes/project-readiness.md
---

# PCR02 原理图第二批静态优化归档候选

- Source: `PCR02_MAIN_V2.0_20251211.pdf`、PCR02 production/debug 配置、DTB、启动与打包脚本审计
- Topic: `pcr02-schematic-second-batch-static-optimization`
- Captured at: 2026-08-02 Asia/Hong_Kong
- Last verified: 2026-08-02
- Target route: `projects/pcr02-ssc305/decisions`
- Lifecycle: `reviewing candidate`
- Gate result: `needs-fix`（静态证据成立，板端 HIL 待完成）

## 背景与已确认事实

PCR02 V2.0 没有 USB 接口、外置以太网 PHY/RJ45 和 SATA/AHCI；两块显示屏走
MSPI/Fbtft ST77912。Wi-Fi 使用 SDIO，SD 卡、摄像头、音频、MCU 通信、传感器、
马达和 BLE 按需启用链路必须保留。production/debug 已分离，COMMON_CLK/CCF、
tickless、CPUFreq 和 PM 已生效，CMA 已统一为 4MiB。

本轮全面静态审计进一步确认：

- production/debug 产品配置声明 `LX_MEM=256MiB`、`MMA=96MiB`、`CMA=4MiB`，
  但 DTS fallback bootargs 仍保留约 `LX_MEM=510MiB`、`MMA=160MiB` 的旧值；
  正常启动通常由 U-Boot `KERNEL_BOOT_ENV` 覆盖，但恢复或直接 DTB 启动路径存在
  内存布局漂移风险。
- production DTB 中 `emac0`、`hdmitx`、`pnl` 仍为 enabled；当前产品无对应
  外部接口，双屏不依赖 MI_DISP/PNL，而是使用 Fbtft/ST77912。
- production 内核仍保留 `PERF_EVENTS`、`CPU_FREQ_STAT`、
  `SSTAR_MEASURE_CLK`、`MAGIC_SYSRQ`、MOUSEDEV/PS2/SERIO、UHID、JFFS2、
  CONFIGFS 和 FS_ENCRYPTION。仓内产品启动、配置和源码未发现 JFFS2、CONFIGFS、
  fscrypt、UHID 或 PS/2 消费者。
- 当前 SPI-NAND 产品分区使用 SquashFS、UBIFS 和 FWFS；OVERLAY_FS 用于
  `/customer` overlay，PSTORE 用于现场故障证据，EXT4/VFAT/EXFAT 用于 SD 卡，
  这些能力必须保留。
- 历史板端 `CmaTotal=4096 kB`、`CmaFree=0` 未伴随 CMA allocation failure。
  因此 4MiB 作为当前下限保留，不回退 2MiB，也不在无失败证据时扩大到 8MiB。

## 第二批决策边界

第二批只落地可由原理图、产品分区和仓内消费者审计共同支持的静态优化：

1. 统一 production/debug DTS fallback 与产品 `KERNEL_BOOT_ENV` 的 LX/MMA/CMA
   参数，消除异常启动路径漂移；继续由构建契约阻止 CMA 漂移。
2. 在 PCR02 production/debug DTS 中显式关闭 EMAC、HDMITX 和 PNL；保留
   ST77912、CSI/VIF/ISP、音频、SDMMC0/1 及所有未完成板级映射核验的
   UART/I2C/PWM。
3. production 内核关闭纯诊断能力 `PERF_EVENTS`、`CPU_FREQ_STAT`、
   `SSTAR_MEASURE_CLK` 和 `MAGIC_SYSRQ`，debug 保留诊断能力。
4. production 内核关闭 MOUSEDEV/PS2/SERIO、UHID、JFFS2、CONFIGFS 和
   FS_ENCRYPTION；保留基础 INPUT/EVDEV、SD 卡文件系统、OVERLAY_FS 和 PSTORE。
5. 不在本批启用 SD/Wi-Fi runtime PM，不修改 DVFS/OPP/IDAC，不关闭 UART、I2C、
   PWM，不改变 CMA 容量，不调整业务显示帧率和资源语义。

## 验证、风险与回退

- Source gate：双 profile `verify`、双内核/DTB 构建、expanded config 正反断言、
  DTB 状态反向扫描、完整 production/debug 镜像构建及分区尺寸检查。
- HIL gate：`/proc/cmdline`、`/proc/iomem`、`CmaTotal=4096 kB`、无 CMA/DMA
  分配失败；双屏、摄像头、音频、MCU、马达、传感器、Wi-Fi/SD、BLE 按需启停、
  OTA、PSTORE、冷启动 p95、待机电流与反复休眠恢复。
- 任一产品消费者、启动失败、CMA 分配失败、双屏/SD/OTA/恢复异常时，按单项
  恢复对应 DTS 或 defconfig 配置；debug 镜像保持诊断回退路径。
- 静态构建和产物门禁不能外推为实际功耗或启动收益，板端验证前整体状态保持
  `needs-fix`。

## 脱敏与 provenance

- 不包含设备地址、业务端点、凭证、raw log、cache、runtime state 或二进制。
- 原理图只记录文件名与既有受控 SHA256 provenance，不复制原理图正文。
- 本候选不自动提升 active、memory 或 AGENTS 规则，待 owner 复核。
- Memory candidate: no
- AGENTS candidate: no
- Supersedes: none；作为首批决策的后续批次。
