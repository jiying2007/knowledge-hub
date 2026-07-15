---
id: pcr02-imssv06c11-three-way-sdk-audit-20260715
title: PCR02 IMSSV06C11 三方 SDK 审计：摄像头 AE、SPI NAND、UBIFS 只读与时钟电气路径
kind: project-archive
domain: projects/pcr02-ssc305
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
review_after: '2026-10-13'
review_status: manual-entry-pending-review
promotion: none
tags:
- pcr02-ssc305
- source-audit
- imssv06c11
- camera-ae
- spi-nand
- fsp-qspi
- spi0-drive
- sensor-mclk
- ubifs
- ubi-read-only
- manual-validation-pending
generated_by_ai: true
ai_role: summarized
ai_model_or_tool: Codex
ai_generated_at: '2026-07-15'
manual_validation_pending: true
summary_zh: 三方静态审计确认新 SDK 含高相关 AE/ISP 修复，但没有 SC5336P 专用更新；SPI NAND 正常读写、UBIFS/UBI 只读保护路径无新增改善，且三方共同保留 NAND 状态错误传播缺口；当前项目 Flash 防护更完整；SPI0 pad drive 无改善，Sensor MCLK
  仅有 DFS 占空比修复。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
promotion_decision: none; capture does not authorize active promotion or owner decision
---

# PCR02 IMSSV06C11 三方 SDK 审计：摄像头 AE、SPI NAND、UBIFS 只读与时钟电气路径

Captured at: 2026-07-15 Asia/Hong_Kong

Status: 静态源码、提交和二进制哈希审计已完成；板端 A/B、波形和概率验证尚未完成。

Project: PCR02 SSC305 SDK

## 摘要

本记录比较三套本地 SDK：旧原厂 `Iford_IMD00V5.1.1_20250529`、当前 PCR02 项目 `pcr02_ssc305_release`、原厂新包 `Iford_IMSSV06C11_20260629/SW-SDK`。审计重点是：

1. 摄像头概率白屏是否可能从新 AE/ISP 栈获益。
2. SPI NAND 普通读写、异常关机、BDMA/FSP、ECC 和文件系统路径是否有改善。
3. SPI0 时钟或 Sensor MCLK 的驱动强度、相位、占空比和电气路径是否有改善。
4. `/data` UBIFS 概率进入只读保护、重启恢复且没有坏块时，新 SDK 是否包含相关修复。

结论：

| 问题 | 新 SDK 相对旧原厂 SDK | 新 SDK 相对当前项目 | 结论级别 |
| --- | --- | --- | --- |
| 摄像头概率白屏 / AE | 包含 AE 边界收敛、Sensor AE 时序、IQ/ISP Gain 同帧同步、OBC/ISP Gain 同步等高相关修复 | 当前项目摄像头闭源栈仍与旧原厂相同，因此存在明确增量 | `source-confirmed / board-unverified` |
| SPI NAND 普通读取 | 未发现 retry、reset、ECC、UBI、ubiblock 或 SquashFS 实质改善 | 当前项目已经回迁新版读链，且有更完整的超时清理和错误传播 | `no-incremental-improvement` |
| SPI NAND 普通 program/erase | 主逻辑无实质变化；shutdown 与擦除重叠时有边界改善 | 当前项目已包含对应链路，并将无界等待改为有限等待 | `edge-case-only` |
| `/data` UBIFS 概率只读 | UBIFS、UBI 和正常 NAND program/erase 没有修复；异常关机边界有所加强 | UBIFS/UBI 源码与新 SDK 相同，异常关机链已回迁；NEW 没有增量 | `no-incremental-improvement / root-cause-unconfirmed` |
| SPI0/FSP-QSPI pad drive | 无 drive、slew、phase、dummy、MX35 输出驱动改善 | 新版 stock 会丢失当前工作树中的 CK 2mA 定制 | `no-source-improvement` |
| Sensor `sr_mclk` | 移除 DFS，修复频率正确但占空比异常 | 当前项目仍保留旧 DFS 配置 | `duty-cycle-improvement-only` |

不能据此声明四项现场问题已解决。摄像头值得优先做完整新 ISP 栈 A/B；SPI NAND、UBIFS 只读和波形问题不能以整包升级代替板端闭环。

## 归档边界

- 本文是项目级 source audit，状态保持 `reviewing`。
- 本文不代表 owner 已签收，不代表新 SDK 已批准用于生产。
- 本文不把源码相关性提升为板端实测结论。
- 本文不复制 SDK、闭源二进制、完整日志、raw session 或凭证，只保留本机路径、哈希、commit 和摘要。
- 本文不 supersede 既有摄像头白屏、Flash 读异常、pad drive 和 IMSSV05C13 迁移记录；它们仍是相关 provenance。

## 审计基线与方法

### 三套基线

| 角色 | 本机路径 | 审计口径 |
| --- | --- | --- |
| OLD | `OLD/SourceCode` | 原厂旧基线；这是本文内的脱敏角色别名，不是 Hub canonical URI |
| CURRENT | `workspace://pcr02-ssc305/SourceCode` | 同时区分 Git clean HEAD 和当前 dirty working tree |
| NEW | `NEW/SW-SDK` | 原厂新包的脱敏角色别名；只使用各组件当前 HEAD 可达提交，不采用其他分支上的未合入修复 |

CURRENT 在审计时已有用户改动和构建产物噪音；本次审计未修改这些文件。与本主题直接相关的 dirty 行为是 boot/kernel 中仅把 `PAD_SPI0_CK` 设置为 2mA，其他五根 SPI0 IO 不写入。

### NEW 组件身份

| 组件 | HEAD | 日期 | 摘要 |
| --- | --- | --- | --- |
| boot | `f028f84f0b42d0aeabf7306cd23138071b23ede5` | 2026-06-18 | XZDEC MIU 支持 |
| kernel | `fe4c3303d56a3a4cf2d658725a17ab169f0e06dd` | 2026-06-09 | IFORD GPIO 修复 |
| project | `9755ee56f5b7f2902ee888268713e20248552893` | 2026-06-23 | AUDIO 库修复 |
| sdk root | `a5ff65f42c203d598ab781e95005f09e5241ef42` | 2026-03-04 | sync to IMSSV05C13 |
| sdk/linux | `3226c7a4ff4f855087f9431e89e1d3ad0f74f7b1` | 2026-06-18 | OBC 与 ISP Gain 同步 |
| SensorDriver | `3753c10f527cb97b75cc1c723949747e1aa08f06` | 2026-06-09 | 新增其他 Sensor |
| Documents | `0a70b7710d69c1604e6625833f37602eadae5bc8` | 2026-04-02 | 文档批量更新 |

包目录名是 `Iford_IMSSV06C11_20260629`，但 `Documents` 下目录仍命名为 `Iford_IMSSV05C13_*`，`sdk` 根仓也停留在 V05C13 同步提交；其他组件包含 2026-06 后续提交。因此本次以组件 HEAD 为准，附带 Release Note 只作负面佐证，不能作为 V06C11 完整权威说明。

### 方法和真实性门禁

- 对开放源码执行定向 `diff`、`cmp`、Git history 和行级审计。
- 对闭源 `.so`、`.o` 和代表性资源执行 SHA256 比较。
- NEW Git 记录仅采用 `HEAD` 祖先链；其他产品分支上看似相关但未合入的 SPINAND commit 被排除。
- 结合 Knowledge Hub 既有 PCR02 白屏、SPI NAND 读路径和 pad drive 记录，但没有将历史假设当成当前事实。
- 没有运行硬件、构建、刷机、写 Flash 或示波器验证。

## 一、摄像头白屏与 AE/ISP

### 当前硬件和资产事实

PCR02 当前生产配置使用：

- Sensor：`sc5336p_mipi.ko`
- IQ：`sc5336P_iqfile.bin`
- API IQ：normal/night/picture 三套项目文件

当前项目定制 SC5336P IQ 只存在于 PCR02 项目中；OLD 和 NEW 原厂 SDK 均未提供 `project/board/iford/iqfile/sc5336P/`。迁移时必须保留当前项目 IQ，并验证新 ISP 栈对旧 IQ/API bin 的兼容性。

### 新 SDK 的确定改善

NEW 的组件记录和提交包含以下修复：

1. 开启 Sensor AE 时，避免实时模式 IQ/MMA 与 MI CMDQ 配置冲突。
2. 帧模式下优化 AE/AWB 设置时机，避免 ISP 正在处理一帧时被重配置。
3. IQ 参数与 ISP Gain 在同一帧生效。
4. 修复 AE 边界条件下无法收敛、数值稳定性不足和容差不合理。
5. 修复 OBC 与 ISP Gain 不同步导致的亮度异常或黑电平不稳。
6. 降低 Cus3A CPU 负载。
7. 修复 Sensor/ISP 同步以及 CMDQ reset 后部分寄存器恢复问题。

代表提交包括：

- `3597a275`：多项 ISP/Cus3A 修复。
- `2b14fc96`：FDAE 参数和最小快门相关修复。
- `0f80ff0f`：启用 FDAE、Sensor/ISP 同步和 CMDQ 恢复相关修复。
- `4364e6e9`：OBC/ISP Gain、Sensor AE 时序、IQ/ISP Gain 同帧和 AE 边界收敛修复。
- `3226c7a4`：sdk/linux OBC 与 ISP Gain 同步修复。

这些变化与“画面仍有输出，但曝光可能卡在高增益/长曝光并持续饱和发白，重启摄像头后恢复”的当前假设高度相关。

### SC5336P 专用路径未改善

OLD、CURRENT、NEW 的 `drv_ss_sc5336p_mipi.c` SHA256 完全相同：

```text
f7c9b1c555646c4d7ce1513e0561d5b07fc1b62e50a4fa76cdd4341d5a326068
```

因此 NEW 没有修改：

- SC5336P 初始化表。
- 24MHz Sensor MCLK 选择。
- Sensor I2C 写流程。
- SC5336P 曝光、增益和 VTS 寄存器提交逻辑。
- 初始化失败后的完整 power-cycle 或整表读回。

当前驱动的 AE notify 路径连续调用三次 `SensorRegArrayW()` 写 exposure、gain 和 VTS，但不检查返回值，随后无条件清除 `reg_dirty`。如果 I2C 写入偶发失败，软件仍会认为参数已经生效；NEW 没有修复这个诊断盲区。

### 闭源组件变化

| 组件 | OLD 与 CURRENT | NEW | 结论 |
| --- | --- | --- | --- |
| `libmi_isp.so` | SHA256 前缀 `12a200c3`，二者相同 | 前缀 `81fc91cc` | ISP 用户态栈已升级 |
| `libispalgo.so` | 前缀 `6c702162`，二者相同 | 前缀 `7b0006f8` | AE/ISP 算法已升级 |
| `libcus3a.so` | CURRENT 与 OLD 相同 | 不同 | Cus3A 已升级 |
| `libmi_sensor.so` | CURRENT 与 OLD 相同 | 不同 | Sensor 公共层已升级 |
| `libmi_vif.so` | CURRENT 与 OLD 相同 | 不同 | VIF 公共层已升级 |
| `isp.o`、`sensor.o`、`vif.o` | CURRENT 与 OLD 相同 | 2026 版本不同 | kernel 闭源对象已升级 |

常用 MI 公共接口未发现大面积删除，但新 `libispalgo.so` 删除了旧导出符号 `DivGTbl` 并增加新符号。仅复制单个 `.so` 不构成安全迁移；应使用新头文件、用户态库和 kernel module/object 作为一致版本完整重编。

### 判断边界

- “NEW 存在通用 AE/ISP 改善”：高置信、源码和提交记录支持。
- “NEW 能降低 PCR02 白屏概率”：中等置信、需要严格 A/B。
- “白屏根因已经证明是 AE”：未证明。
- “NEW 已彻底解决白屏”：无证据。
- 如果白屏来自 SC5336P I2C 写失败、Sensor 初始化、MIPI 无帧、应用管线或显示输出，NEW 没有看到完整闭环。

## 二、SPI NAND、FSP 和 BDMA

### NEW 相对 OLD 的确定改善

NEW 的变化主要集中于异常场景：

- Kernel panic/Oops 写入时通过 `oops_panic_write` 切到 polling/non-OS BDMA。
- shutdown 时检查 NAND busy，降低 program/erase 尚未完成就复位的风险。
- FSP/BDMA 增加基础 polling/wait-done 链路。

这可以改善 panic 写入和 shutdown 与写/擦除重叠，但不能直接证明改善正常业务态读取、上电后重复读取不一致或 SquashFS 解压错误。

### 正常路径没有发现实质改善

OLD 与 NEW 的正常 page read、page program、block erase 主流程未发现新增 retry、controller reset、重新采样或错误恢复。以下层级没有针对当前故障的实质变化：

- IFORD SoC ECC。
- BBT。
- UBI 和 ubiblock。
- UBIFS。
- SquashFS。
- Boot 侧 NAND 主驱动的核心普通读写逻辑。

因此 NEW 没有直接修复 `/dev/ubi0_3`、`/dev/ubiblock0_3` 重启后 hash 偶发变化或 SquashFS 解压失败的源码证据。

### CURRENT 已回迁新版链路且部分更稳

CURRENT 已包含：

- `c2ac630e7 fix(flash): 同步新版SDK读链路`
- `ca80fab53 fix(flash): 避免重启路径无界等待`
- `4f4864dd2 fix(flash): 收敛BDMA超时状态`
- `6613b9229 fix(flash): 防护BDMA不支持路径`

其中前两项导入新版 read/panic/shutdown 链路；后两项是 CURRENT 相对 NEW 的额外加强：

- 将 BDMA polling 的真实超时/错误向上传播。
- 不支持路径返回错误，而不是成功。
- FSP/BDMA 超时后主动 cancel 并清理状态。
- panic/shutdown 的锁等待有上限，避免 NEW 中的无界等待。

因此，不得用 NEW flash 目录整体覆盖 CURRENT，否则可能丢失当前更完整的错误处理。

### MX35LF4GE4AD 参数没有改善

三方目标条目的关键访问字段仍为：

```text
JEDEC ID: c2 37 03
max_clk: 54 MHz
read command: 0x6B
dummy: 8
program command: 0x32
random program: 0x34
phase: disabled
init_set: none
external ECC: disabled
```

因此 NEW 没有：

- 降低 MX35 时钟。
- 改用 RIU read。
- 启用采样 phase。
- 通过 `SET FEATURE E0h` 调节 Flash 输出驱动。
- 调整 dummy cycle。
- 增加扩展 ECC 解释规则。

当前项目已有 `e98e74939`，明确支持 MX35LF4GE4AD 4K page / 256K block。NEW 原厂 board 列表与当前 PCR02 xcrz 512M 列表的几何和尾部字段不能证明等价，不能直接覆盖当前 `flash_list.sni`。

解析工具对三方 SNIF 都报告 CRC mismatch。因为 OLD、CURRENT、NEW 都存在，不能认定为 NEW 新引入的退化；正式迁移前应向原厂确认 CRC 覆盖范围和尾部字段定义。

### 新 U-Boot 坏块加载接口的代码疑点

NEW 增加 `sstar_part_block_isbad()`，设计意图是启动加载时跳过坏块。但 `loados.c` 调用端传入 `part.offset + partition_off`，接口内部又再次执行 `u32_offset += part->offset`。从同模块其他接口语义看，存在重复叠加分区 offset 或提前触发边界判断的风险。

这项只能标记为“改善意图存在、实现待原厂确认和板测”，不能计入可靠改善，也不属于 Linux `/customer` 的 UBI 运行时读链路。

### 已证伪或降级的假设

- NEW 含未在当前分支生效的其他产品 SPINAND busy/BDMA 修复：证伪。相关 commit 不在 NEW IFORD kernel HEAD 祖先链上。
- NEW 通过 24MHz 解决 MX35 读取：证伪。NEW 仍为 54MHz；既有板测也已证明强制 24MHz 不能消除故障。
- NEW 修改了 UBI/ubiblock/UBIFS/SquashFS：证伪。
- NEW 能通过整体覆盖改善 CURRENT flash：证据相反，CURRENT 的错误处理部分更完整。

## 三、SPI0、MSPI 与 Sensor MCLK

### SPI NAND `PAD_SPI0_CK`

OLD 与 NEW 的 boot/kernel GPIO drive 定义没有新增 SPI0 调节策略。NEW FSP 初始化没有调用 SPI0 pad drive setter，也没有新增：

- drive strength 策略。
- slew rate。
- Schmitt trigger。
- sampling phase。
- MX35 输出驱动。
- dummy/read-mode 优化。

NEW 有一项窄范围 pinmux 变化：SPI0 pad 被显式切换到 GPIO mode 时同步设置 `SPI_EN_DISABLE`。这可能减少控制器仍在输出时的瞬态争用或毛刺，但正常 FSP/QSPI 持续传输不走该场景，不能视为 SCLK Vmax、rise/fall 或 ringing 改善。

### CURRENT clean HEAD 与 dirty working tree

CURRENT clean HEAD `43fe9e2ac` 恢复平台默认 SPI0 驱动能力。

审计时 CURRENT dirty working tree 的真实语义是：

- CK：明确设置为 2mA。
- DO/DI/HLD/WPZ/CZ：不写，保留 ROM/IPL/平台前级值。

它不是历史记录中的“CK 2mA + IO 4mA”。NEW stock 没有这个 CK 2mA hook，直接迁移会回到所有线由 ROM/IPL/平台默认决定。

由于 OLD、CURRENT、NEW 的代表性 IPL 二进制哈希不同，源码审计无法排除 IPL 在 U-Boot 前修改 pad drive。最终必须通过 U-Boot/Linux 前后 RIU readback 和示波器确认。

### 通用 MSPI

NEW 的 MSPI 变化主要涉及 BDMA channel、callback/semaphore、trigger/wait-done 顺序和 cache invalidate 时机，可能改善 generic MSPI DMA 完成或超时处理，但没有修改 `PAD_MSPI_CK` 的 drive、slew、polarity 或 phase。因此它不是时钟幅值或过冲改善。

### Sensor `sr_mclk`

NEW kernel 提交 `54c7793d0` 明确记录：启用 `sr_mclk` DFS 后，频率值正确但占空比异常，因此移除了 SR00～SR03 MCLK 的 DFS 配置。CURRENT 仍保留旧 DFS 字段。

这是确定的 Sensor MCLK duty-cycle 改善，可能值得与摄像头白屏一起 A/B，但它：

- 不改变 pad drive strength。
- 不能证明改善 overshoot、undershoot 或 ringing。
- 是否命中 PCR02 取决于运行时是否真正使用对应 DFS 路径。

## 四、`/data` UBIFS 概率进入只读保护

### 现象、影响和根因状态

补充现象为：可读写 `/data` UBIFS 在运行期概率进入只读保护，重启后恢复读写，现场没有观察到坏块。

- 当前 `/data` 是 `ubi0:data`、volume ID 4，文件系统为 UBIFS；当前分区配置没有 `-o ro`。
- 生产配置中 `/data` 保存运行态数据；debug customer overlay 配置还把 `/data/customer_overlay` 用作 overlay upper/work/state，会增加 `/data` 的元数据、rename、unlink、writeback 和 commit 压力，但不是主动切只读逻辑。
- 在项目脚本和可读源码中没有找到对 `/data` 的 `remount,ro`、`mount -o remount` 或等价 `MS_REMOUNT` 操作。预编译应用仍需用故障态判据排除，不能只凭源码搜索完全否定。
- 根因仍为 **未确认**。缺少故障发生前后的首个 `dmesg` 错误、UBIFS `ro_error` 和 UBI `ro_mode`，不能把底层 Flash、UBIFS、应用 remount 或掉电时序中的任一项写成已证实根因。

### 三方源码和配置结论

定向逐文件比较得到：

1. OLD 与 NEW 的 `kernel/fs/ubifs/` 完全相同。
2. OLD 与 NEW 的 `kernel/drivers/mtd/ubi/` 完全相同。
3. CURRENT 与 NEW 的上述源码也相同；CURRENT 目录仅多出构建生成的 `.o`、`.cmd`、`built-in.a` 和 `modules.order`。
4. NEW kernel 当前 HEAD 在 `fs/ubifs`、`drivers/mtd/ubi` 路径上只有基线同步提交 `2c9aeba1c`，没有后续 UBIFS/UBI 修复；CURRENT 也没有 PCR02 专用 UBIFS/UBI 修复。
5. NEW 的项目变更记录只发现新增 XT26G01F Flash 支持，没有 UBIFS、UBI、只读保护、program/erase 稳定性或恢复修复说明。
6. NEW 随包 `.config` 对应 `iford-ssz029c-s01a-dualos_demo`，并且关闭 `CONFIG_MTD_UBI`；它不是 PCR02 可用配置，也不能作为 `/data` 已改善的证据。迁移测试必须继续使用 PCR02 的 UBI/UBIFS、分区和 NAND 配置。
7. NEW 没有 PCR02 定制的 `data` volume 配置；当前项目的 `/data` 挂载策略和 `0x8C00000` 容量是项目层资产，不会因换用 NEW 自动得到修复。

因此，NEW **没有 UBIFS/UBI 层增量改善**。相对 OLD 新增的 panic/Oops polling 和 shutdown busy/互斥处理，只可能降低异常写入或关机与 program/erase 重叠的边界风险；CURRENT 已回迁这条链路，并把 NEW 的无界锁等待改成有限等待，所以相对 CURRENT 也没有新增收益。

### “只读保护”存在两个层级

当前内核中需要区分两个不同状态：

| 层级 | 内核状态 | 典型触发 | 影响范围 | 故障态判据 |
| --- | --- | --- | --- | --- |
| UBIFS | `c->ro_error=1`，同时设置 `SB_RDONLY` | LEB write/change/unmap/map 失败，write-buffer sync、journal、commit、GC、orphan 或文件 writeback 失败 | 通常是单个 UBIFS 实例，例如 `ubi0_4` | `/sys/kernel/debug/ubifs/ubi0_4/ro_error=1`，日志含 `switched to read-only mode, error ...` |
| UBI | `ubi->ro_mode=1` | dynamic volume 写失败、atomic change 失败、PEB move/erase/WL 连续失败、映射不一致 | 整个 `ubi0` 的写路径；其他可写 volume 也会受影响 | `/sys/class/ubi/ubi0/ro_mode=1`，日志含 `UBI warning: ... switch to read-only mode` |

UBIFS 的 `ubifs_leb_write()`、`ubifs_leb_change()`、`ubifs_leb_unmap()` 和 `ubifs_leb_map()` 对任何下层错误都会调用 `ubifs_ro_mode()`；后台 write-buffer sync 或 commit 失败也会直接置只读。UBI 的 dynamic volume 写入在重试或恢复后仍失败时会调用 `ubi_ro_mode()`。因此 `/data` 最终报 `-EROFS` 只是保护结果，**首个 I/O、commit、GC、erase 或映射错误才是根因证据**。

重启会重新初始化这些内存状态并重新 attach UBI、mount/replay UBIFS；如果当时底层瞬态异常已消失，文件系统可以恢复 RW。这与现象相符，但不证明介质和链路健康。`bad_peb_count=0` 只说明 UBI 没有把 PEB 记为永久坏块，不能排除：

- program/erase/read 的瞬态 timeout 或 controller failure。
- FSP/QSPI、BDMA、pad 信号完整性、供电或复位瞬态。
- 返回码为成功但数据不一致的 silent corruption。
- UBI wear-leveling、PEB move 或 erase 工作失败。
- UBIFS journal/commit/GC 读取到 CRC、node 或索引不一致。

同平台既有证据曾记录同一 UBI LEB 连续读取 `ret=0` 但 CRC 不同，说明“无坏块、下层返回成功”并不能排除 Flash 读路径瞬态不一致。该历史证据提高了底层链路假设的优先级，但不是本次 `/data` 只读事件的直接日志。

### 三方共同保留的 NAND 错误传播缺口

OLD、CURRENT、NEW 的 `mdrv_spinand.c` 正常 program/erase 实现相同，并共同存在以下静态风险：

1. `drv_spinand_wait_device_available()` 返回 `void`，丢弃 `drv_spinand_check_status()` 的 `TIMEOUT`、`DEVICE_FAILURE`、`P_FAIL` 或 `E_FAIL`。
2. page program 完成后的状态只显式匹配 `ERR_SPINAND_P_FAIL`；如果查询返回 `ERR_SPINAND_TIMEOUT` 或 `ERR_SPINAND_DEVICE_FAILURE`，代码会继续返回 `ERR_SPINAND_SUCCESS`。
3. block erase 完成后的状态只显式匹配 `ERR_SPINAND_E_FAIL`；`TIMEOUT` 或 controller failure 同样可能落入成功返回。
4. `sstar_spinand_cmdfunc()` 的 `NAND_CMD_ERASE1` 调用没有保存 `mdrv_spinand_block_erase()` 的直接返回值，主要依赖随后 `waitfunc` 再读状态，错误上下文和首次失败点可能丢失。

这是 **source-confirmed 的错误传播缺口**，但它是否触发当前现场问题仍是 hypothesis。可能链路是：program/erase 状态查询异常被当成成功，上层 UBI/UBIFS 继续运行，随后在 readback、journal、commit 或 GC 中发现不一致并进入只读保护。NEW 没有修复这条链路，CURRENT 的 BDMA 超时清理加强也没有覆盖上述 NAND status 返回语义。

### 假设矩阵

| 假设 | 当前优先级 | 支持证据 | 反证或缺口 | 可证伪动作 |
| --- | --- | --- | --- | --- |
| UBIFS commit/write-buffer/GC 收到下层 I/O 错误后自保护 | 高 | 源码机制与“运行期只读、重启恢复”直接匹配 | 没有故障态首个错误码 | 采集 `ro_error`、`ro_mode`、完整首错和 stack |
| SPI NAND program/erase/status 的瞬态失败或错误被丢弃 | 中高 | 三方共同存在明确错误传播缺口；Flash 读路径已有瞬态不一致历史证据 | 尚无 `/data` program/erase timeout 直接日志 | 增加 op/page/block/status 计数和错误日志，修正返回传播后做 A/B |
| UBI WL、PEB move 或 background erase 失败进入全局只读 | 中 | UBI 源码中存在明确 `ubi_ro_mode()` 路径，不要求先出现永久坏块 | 未确认其他 UBI volume 是否同时只读 | 故障态读取 `/sys/class/ubi/ubi0/ro_mode`，检查 `ubi_bgt` 首错 |
| 信号完整性、供电或复位瞬态导致下层 I/O 异常 | 中 | 当前已有 SPI NAND 稳定性问题；无坏块不排除电气瞬态 | 缺示波器和电源同步触发证据 | 同工作负载下做 pad/频率/E0h 单变量及示波器 A/B |
| 异常关机或 reboot 与未完成写/擦除重叠 | 中低 | NEW 相对 OLD 确有 shutdown/panic 边界加强 | CURRENT 已包含并加强；现场若在正常运行期变只读则解释力弱 | 区分正常运行、warm reboot、掉电三类复现，记录最后一次 sync/shutdown |
| 应用或预编译组件主动 remount `/data` 为只读 | 低 | 重启恢复表面上相容 | 可读项目源码无命中；无法解释 UBIFS/UBI warning | 两个内核只读标志均为 0 时，再追踪 mount syscall 和进程 |
| 单纯 `/data` 文件空间耗尽 | 低 | 高写入压力可能相关 | UBIFS 对正常 `-ENOSPC/-EAGAIN` 有专门处理，通常不会直接进入 fatal RO | 同时记录 `df`、UBIFS budget 和 UBI `avail_eraseblocks`；区分文件空间与 PEB/保留池耗尽 |
| 永久坏块是唯一根因 | 低 | NAND 介质仍可能发生后期坏块 | 现场 `bad_peb_count=0` 且重启恢复 | 继续监控 MTD/UBI bad block、ECC 与 erase/program fail；不能仅凭当前计数彻底排除 |

### 结论边界

- “NEW 没有 UBIFS/UBI 修复”：高置信，三方逐文件比较和 HEAD history 支持。
- “NEW 能解决 `/data` 概率只读”：没有源码或板端证据支持。
- “CURRENT 已包含 NEW 唯一相关的 shutdown/panic 边界处理”：高置信。
- “NAND 状态错误传播缺口是当前根因”：尚未证明，只能作为优先修复和插桩候选。
- “没有坏块即可排除 SPI NAND/FSP/供电/信号问题”：错误。

## 迁移策略建议

1. 不为解决四项问题而直接整包覆盖 CURRENT。
2. 以 NEW 为独立迁移基线，按模块语义回放 PCR02 产品修改，不复制旧目录覆盖原厂新文件。
3. 摄像头优先迁移一致版本的新 `libmi_isp`、`libispalgo`、`libcus3a`、`libmi_sensor`、`libmi_vif`、kernel ISP/Sensor/VIF object/module 和对应头文件。
4. 保留当前 SC5336P 驱动和项目 IQ；另行补 Sensor I2C 写返回值、寄存器读回和故障遥测。
5. 保留 CURRENT 的四组 flash 修复，尤其是错误传播、超时 cancel、状态清理、不支持路径防护和有限锁等待。
6. 把 NAND status/busy 错误传播修复和计数插桩作为独立候选：任何非 `SUCCESS` 都应保留原始 op、page/block、status 并向上返回；先在实验板验证 UBI recovery 行为，不能直接用于生产。
7. 保留并重新验证 PCR02 MX35 4K/256K `flash_list.sni`；不得用 NEW vendor board 列表直接替换。
8. SPI0 pad drive、Flash `E0h` 输出驱动和频率作为独立电气变量；不要与 SDK 软件栈同时变化。
9. 向原厂索取 V06C11 固定 manifest、正式 Release Note、闭源组件 build ID/SHA256、MX35 SNI/SNIF 说明和已知问题清单，并明确询问 UBIFS RO、program/erase timeout 和状态传播已知问题。

## 板端验证门槛

### 摄像头严格 A/B

- 同一块板、同一 Sensor、同一光照、电源、应用、SC5336P 驱动和 IQ。
- A 使用当前完整 camera stack；B 使用完整 NEW camera stack。
- 每帧记录 AE `bIsStable`、`bIsReachBoundary`、曝光时间、SensorGain、ISPGain、平均亮度和目标值。
- 自动曝光与固定安全手动曝光对照。
- 故障现场同时采集 Sensor ID、VIF RAW、ISP/YUV 和最终显示帧。
- 读回 `0x3107/0x3108`、`0x0100`、`0x320e/0x320f`、`0x3e00~0x3e02` 及 gain 寄存器。
- 如果目标是证明故障率低于 0.1%，零失败情况下约需 3000 次样本，才能把单侧 95% 上界压到约 0.1%。

分层判定：

- 无 RAW：Sensor/MIPI/MCLK/供电时序。
- RAW 饱和且手动曝光恢复：支持 AE 根因。
- RAW 正常但 YUV 白：ISP/IQ。
- YUV 正常但最终屏白：显示链。

### SPI NAND 软件 A/B

保持 SNI、54MHz、pad drive、Flash 批次、分区和应用一致，只切换 flash 软件栈：

- A：CURRENT clean HEAD，保留四组 flash 修复。
- B：NEW stock flash 栈。
- C：NEW 基线重新叠加 CURRENT 超时 cancel、错误传播和有限锁等待。

最低验证：

- 每组 200 次 cold boot。
- 每组 200 次 warm reboot。
- 连续固定文件和 raw block hash 至少 2 小时。
- BDMA 与 RIU read 独立对照。
- 统计 ECC corrected/uncorrectable、FSP/BDMA timeout、I/O error 和首个 SquashFS error。
- program/erase 只能在实验板 scratch MTD/UBI 上执行。
- shutdown 与写/擦除交叠单独验证。
- 新 U-Boot 坏块接口使用非零 offset 分区和已知坏块验证实际访问地址。

### `/data` UBIFS 故障态取证与 A/B

只读一旦出现，先不要重启。重启会清空最关键的内存状态和早期日志。当前 kernel 已启用 `CONFIG_DEBUG_FS`，并编译 UBIFS debugfs 节点；建议通过串口持续 `dmesg -w`，或把以下结果先保存到 tmpfs 再立即导出。以下是板端建议命令，不是本次已执行证据：

```sh
grep ' /data ' /proc/mounts
cat /sys/kernel/debug/ubifs/ubi0_4/ro_error
cat /sys/class/ubi/ubi0/ro_mode
cat /sys/class/ubi/ubi0/bad_peb_count
cat /sys/class/ubi/ubi0/avail_eraseblocks
cat /sys/class/ubi/ubi0/reserved_for_bad
cat /sys/class/ubi/ubi0/max_ec
ubinfo -a
df -h /data
dmesg > /tmp/data-ro-dmesg.txt
dmesg | grep -Ei 'UBIFS|UBI|SPINAND|NAND|FSP|QSPI|BDMA|ECC|program|erase|timeout|read-only'
```

如果 debugfs 未挂载，先确认 `/sys/kernel/debug` 后再执行 `mount -t debugfs debugfs /sys/kernel/debug`。通过 `/sys/class/ubi/ubi0/mtd_num` 找到底层 MTD 编号，并同步读取该 `mtdX` 的 `corrected_bits`、`ecc_failures`、`bad_blocks` 和 `bbt_blocks`。判定矩阵：

| `/proc/mounts` | UBIFS `ro_error` | UBI `ro_mode` | 首要判断 |
| --- | --- | --- | --- |
| `/data` 为 `ro` | 1 | 0 | 单个 UBIFS 因 journal/commit/GC/LEB I/O 错误自保护 |
| `/data` 为 `ro` | 1 或 0 | 1 | UBI 全局只读，优先追查 write/erase/WL/PEB move 和底层错误 |
| `/data` 为 `ro` | 0 | 0 | 优先追查应用 remount、VFS 或实际 mount/bind/overlay 层级 |
| `/data` 为 `rw` | 0 | 0 | 应用报错未必来自 `/data` 本身，应核对真实路径、overlay upper 和打开的文件描述符 |

A/B 必须保持同一板、Flash 批次、SNI、54MHz、pad、供电、分区镜像和业务 workload。建议至少包含：

- A：CURRENT 现状。
- B：NEW kernel 源码，但继续使用 PCR02 kernel config、SNI、分区和产品层；不能使用 NEW 随包关闭 UBI 的 demo `.config`。
- C：B 加回 CURRENT 的 BDMA/FSP 超时清理与有限锁等待。
- D：C 再加入 NAND status/busy 完整错误传播与 op/page/block 计数，验证是否从 silent corruption 转为可恢复、可定位的 `-EIO`。

工作负载使用实验板和专用测试目录，覆盖小文件反复创建/rename/unlink、顺序和随机写、`fsync`、`sync`、log rotation、接近容量水位、UBIFS commit/GC 以及 warm reboot。不要在量产数据或原始 `/dev/mtd`、`/dev/ubi0_4` 上做破坏性写测。每组记录首次只读前的原始错误、累计写入量、运行时长和重启次数；若目标失败率为 `p`，零失败时约需 `3/p` 个独立样本才能给出单侧 95% 上界。

### SPI0 电气 A/B

建议单变量矩阵：

- 平台默认。
- CK 2mA、IO 默认。
- CK 2mA、IO 4mA。
- CK 4mA、IO 4mA。
- 可选：独立修改 MX35 `E0h` 输出驱动。

每组记录：

- U-Boot 和 Linux 初始化后的 RIU readback。
- MX35 `GET FEATURE E0h`。
- NAND pin 端 SCLK、CS#、IO0/IO1 的 Vmax/Vmin、10–90% rise/fall、overshoot、undershoot、ringing、duty、jitter、setup/hold。
- 同步执行相同 cold boot、hash 和 ECC 压力。

波形改善和 Flash 数据稳定必须分别验收，不能相互替代。

## 关键证据索引

### 摄像头

- PCR02 配置：`workspace://pcr02-ssc305/SourceCode/project/configs/verify/defconfigs/xcrz_ipc_ap6303bh_512M_pcr02_v20_defconfig`
- SC5336P 驱动：`workspace://pcr02-ssc305/SourceCode/sdk/driver/SensorDriver/drv/src/drv_ss_sc5336p_mipi.c`
- PCR02 IQ：`workspace://pcr02-ssc305/SourceCode/project/board/iford/iqfile/sc5336P/`
- NEW ISP 记录：`NEW/SW-SDK/sdk/linux/git_commit_records.md`
- NEW project 记录：`NEW/SW-SDK/project/git_commit_records.md`

### SPI NAND

- CURRENT BDMA：`workspace://pcr02-ssc305/SourceCode/kernel/drivers/sstar/bdma/iford/hal_bdma.c`
- CURRENT FSP：`workspace://pcr02-ssc305/SourceCode/kernel/drivers/sstar/fsp_qspi/hal/iford/hal_fsp_qspi.c`
- CURRENT SPI NAND：`workspace://pcr02-ssc305/SourceCode/kernel/drivers/sstar/flash/nand/mtd_spinand.c`
- NEW BDMA：`NEW/SW-SDK/kernel/drivers/sstar/bdma/iford/hal_bdma.c`
- NEW SPI NAND：`NEW/SW-SDK/kernel/drivers/sstar/flash/nand/mtd_spinand.c`
- CURRENT SNI：`workspace://pcr02-ssc305/SourceCode/project/board/xcrz_iford_512Mflash/flash_list.sni`
- NEW SNI：`NEW/SW-SDK/project/board/iford/boot/spinand/partition/flash_list.sni`
- NEW U-Boot load：`NEW/SW-SDK/boot/cmd/sstar/loados.c`

### UBIFS、UBI 与 `/data`

- CURRENT `/data` 配置：`workspace://pcr02-ssc305/SourceCode/project/image/configs/general/spinand_MX35_512M.squashfs.partition.config`
- CURRENT UBIFS 只读入口：`workspace://pcr02-ssc305/SourceCode/kernel/fs/ubifs/io.c`
- CURRENT UBIFS commit：`workspace://pcr02-ssc305/SourceCode/kernel/fs/ubifs/commit.c`
- CURRENT UBI dynamic write：`workspace://pcr02-ssc305/SourceCode/kernel/drivers/mtd/ubi/eba.c`
- CURRENT UBI `ro_mode` sysfs：`workspace://pcr02-ssc305/SourceCode/kernel/drivers/mtd/ubi/build.c`
- CURRENT NAND program/erase：`workspace://pcr02-ssc305/SourceCode/kernel/drivers/sstar/flash/nand/mdrv_spinand.c`
- NEW UBIFS：`NEW/SW-SDK/kernel/fs/ubifs/`
- NEW UBI：`NEW/SW-SDK/kernel/drivers/mtd/ubi/`
- NEW NAND program/erase：`NEW/SW-SDK/kernel/drivers/sstar/flash/nand/mdrv_spinand.c`
- NEW 随包 kernel config：`NEW/SW-SDK/kernel/.config`
- NEW 项目变更记录：`NEW/SW-SDK/project/git_commit_records.md`

### 时钟和 drive

- CURRENT SPI0 GPIO：`workspace://pcr02-ssc305/SourceCode/boot/drivers/sstar/gpio/iford/hal_gpio.c`
- NEW FSP init：`NEW/SW-SDK/boot/drivers/sstar/fsp_qspi/hal/iford/hal_fsp_qspi.c`
- CURRENT clock tree：`workspace://pcr02-ssc305/SourceCode/kernel/arch/arm/boot/dts/iford-clks.dtsi`
- NEW clock tree：`NEW/SW-SDK/kernel/arch/arm/boot/dts/iford-clks.dtsi`

### Knowledge Hub 相关来源

- `projects/xcrz-sigmastar-demo/archive/debug/2026-07-03-pcr02-camera-whiteout-ae-exposure-analysis.md`
- `projects/pcr02-ssc305/archive/engineering-archive/pcr02/boot-flash/pcr02_spinand_read_path_bdma_riu_20260529.md`
- `projects/pcr02-ssc305/archive/engineering-archive/pcr02/boot-flash/pcr02_spi0_pad_drive_8ma_riu_verification_20260618.md`
- `projects/pcr02-ssc305/archive/engineering-archive/pcr02/boot-flash/pcr02_spinand_flash_read_aging_progress_20260618.md`
- `projects/pcr02-ssc305/archive/engineering-archive/pcr02/ubifs-squashfs/pcr02_customer_squashfs_libmsc_errno5_20260617.md`
- `projects/pcr02-ssc305/archive/engineering-archive/pcr02/ubifs-squashfs/pcr02_ubifs_troubleshooting_20260528.md`
- `projects/pcr02-ssc305/archive/engineering-archive/pcr02/source-audit/pcr02_source_compare_ubifs_20260528.md`
- `projects/pcr02-ssc305/archive/engineering-archive/pcr02/partition-storage/pcr02_sdk_rootfs_customer_data_policy_20260528.md`
- `projects/pcr02-ssc305/archive/engineering-archive/pcr02/source-audit/pcr02_imssv05c13_sdk_migration_plan_20260530.md`

## 验证记录

- Knowledge Hub 上下文预检：`selected_project_id=pcr02-ssc305`。
- 三方定向源码、Git history、commit reachability 和 SHA256 审计：完成。
- OLD 与 NEW 的 `fs/ubifs`、`drivers/mtd/ubi` 递归比较：无差异，退出码 0。
- CURRENT 与 NEW 的 `fs/ubifs`、`drivers/mtd/ubi` 递归比较：源码无差异；唯一差异为 CURRENT 构建生成物。
- CURRENT 与 NEW 的 `mdrv_spinand.c`：完全相同；OLD 到 NEW 的变化只有 polling/shutdown 辅助接口，不涉及正常 program/erase 状态语义。
- NEW kernel HEAD 的 UBIFS/UBI/NAND 路径提交审计：只有 `2c9aeba1c` 基线同步，没有后续相关修复。
- 当前项目 remount 关键词审计：没有 `/data` 主动切只读命中；仅有无关 systemtap 常量。
- Knowledge Hub `knowledge-check --dry-run --json --diagnostics`：通过。
- 条目 ID 精确检索：通过，命中本归档且 registry、title、tags 与正文一致。
- `knowledge-orphan-files --changed-only`：`needs-fix`；命中的是当前 Hub 中既有 PCR02 canonical hardcut 迁移的旧路径缺口，本条目已登记且不在缺失列表中。
- Knowledge Hub product final gate：`needs-fix`；repo-wide shared unit/retrieval/restore/Obsidian 及 owner review 尚未闭环，不是本条目 source audit 结论失败。
- CURRENT `git diff --check`：通过。
- `final-ready.sh`：通过；session coach 的其他 Codex asset dirty 提示与本项目审计无关。
- 本次审计改动项目文件：无。
- 板端摄像头 A/B：未执行。
- 板端 Flash A/B：未执行。
- `/data` 故障态 `ro_error`、`ro_mode`、首个 `dmesg` 错误和 MTD ECC 计数：未采集。
- 示波器和 RIU readback：未执行。

## 当前状态与复核条件

Gate result: `pass-as-source-audit / knowledge-check-pass / hub-product-gate-needs-fix / manual-validation-pending`

本文可用于：

- 设计新 SDK 迁移分支。
- 评审摄像头 AE/ISP A/B 范围。
- 阻止 NEW flash 文件整体覆盖 CURRENT 项目修复。
- 区分 UBIFS 单 volume 自保护、UBI 全局只读和应用 remount，并设计 `/data` 故障取证。
- 评审 NAND status/busy 错误传播修复和插桩候选。
- 设计 SPI0/Sensor MCLK 电气与软件分离验证。

本文不可用于：

- 宣称摄像头白屏已修复。
- 宣称 SPI NAND 普通读写已修复。
- 宣称 `/data` 概率只读已由 NEW 修复，或宣称其根因已经确定。
- 宣称波形已满足 datasheet margin。
- 批准生产发布或自动提升为 active 项目事实。

下一次复核应补充：

1. camera stack A/B 统计和故障现场分层证据。
2. `/data` 只读现场的 `/proc/mounts`、UBIFS `ro_error`、UBI `ro_mode`、首次错误 stack 和完整重启前日志。
3. CURRENT/NEW flash 固定变量 A/B 的 hash、ECC、program/erase status 和超时统计。
4. NAND busy/status 完整错误传播与原始代码的 D/A-B 对照，确认是否改变 UBI recovery 和只读概率。
5. SPI0 RIU readback、MX35 E0h 和示波器结果。
6. 原厂 V06C11 manifest、正式 Release Note、MX35 SNI/SNIF 解释及 UBIFS RO/program/erase 已知问题答复。
7. 对 NEW `sstar_part_block_isbad()` offset 语义的原厂确认或板端验证。

## Sanitization 与 provenance

- Source：2026-07-15 当前 Codex 会话中的本地三方 SDK 静态审计结果。
- Sanitization：未复制完整聊天、raw log、SDK、二进制、客户信息、凭证或网络端点；只保留内部本机路径、commit、哈希前缀和可复用结论。
- Provenance：本机只读源码、组件 Git history、闭源文件哈希和 Knowledge Hub 既有 PCR02 记录。
- Memory candidate：no。
- Owner decision：none。
- Active promotion：none。
