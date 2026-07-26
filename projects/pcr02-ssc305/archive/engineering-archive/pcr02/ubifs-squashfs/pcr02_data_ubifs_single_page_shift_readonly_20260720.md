---
related:
- pcr02-imssv06c11-three-way-sdk-audit-20260715
human_reviewed_by: null
human_reviewed_at: null
review_basis: null
incident_id: null
severity: null
affected_version: null
id: pcr02-data-ubifs-single-page-shift-readonly-20260720
title: PCR02 /data UBIFS 单页节点整体偏移 4 字节导致只读排障记录
kind: debug-record
domain: projects/pcr02-ssc305
path: projects/pcr02-ssc305/archive/engineering-archive/pcr02/ubifs-squashfs/pcr02_data_ubifs_single_page_shift_readonly_20260720.md
scope: project-specific
visibility: team-internal
status: draft
owner: leiwenjun
source:
  type: manual
  from: 2026-07-20 至 2026-07-22 板端命令、串口日志摘要、本地源码与 Git 历史审计、IMSSV06C11 SDK 对照
  source_sha256: 2ac1a69b133b7de95805111872a589982dcbc531b60f61c3e0f7e6c1ac0065fc
review_after: '2026-10-20'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- pcr02
- ubifs
- ubi-read-only
- data-partition
- spi-nand
- bdma
- fsp-qspi
- imssv06c11
- sdk-audit
- spi0-pad-drive
- abrupt-reboot
- manual-validation-pending
validation_refs:
- projects/pcr02-ssc305/archive/engineering-archive/pcr02/ubifs-squashfs/pcr02_data_ubifs_single_page_shift_readonly_20260720.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/pcr02-ssc305/archive/engineering-archive/pcr02/ubifs-squashfs/pcr02_data_ubifs_single_page_shift_readonly_20260720.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-07-20'
updated_at: '2026-07-22'
generated_by_ai: true
ai_role: summarized
ai_model_or_tool: Codex
ai_generated_at: '2026-07-20'
manual_validation_pending: true
summary_zh: 板端完整 page、节点 CRC 与冷启动复读证据确认，ubi0:data 的 LEB 122 内单个 4 KiB UBIFS page image 整体后移 4 字节：页首插入 4 个 0xCC，5 个 inode node
  与 1 个 PAD node 全部 CRC 正确，页尾 4 个 padding 字节被截断；该错位触发 inode 346 dead directory entry 并令 UBIFS ro_error=1。故障版本为 v1.1.34/c1c1d317f；该显示提交同时把 Linux
  SPI NAND PAD_SPI0_CK 强制设为 2mA，且显示 MSPI 与 Flash FSP 共用 BDMA CH0。异常重启、2mA 信号裕量和共享 BDMA 负载均为高价值触发假设，但最终根因仍未确认。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
---

# PCR02 `/data` UBIFS 单页节点整体偏移 4 字节导致只读排障记录

Captured at: 2026-07-20 Asia/Hong_Kong

状态：现场完整 page、节点 CRC、冷启动复读和本地源码审计已完成；已确认完整 4096 字节 UBIFS page image 被精确右移 4 字节，但最终根因仍待 RIU/BDMA 同页 A/B 和写入插桩验证。本文是 `draft` 排障候选，不是 active 决策。

## 现象

- `/data` 表面挂载为 `ubi0:data on /data type ubifs (rw,...)`，但 `touch /data/lei` 返回 `Read-only file system`。
- `mount -o remount,rw /data` 不能恢复写入。
- 访问 `/data/log/prog_pcr02/iot/iot.1.log` 时稳定报告：

  ```text
  ubifs_read_node: bad node type (160 but expected 0)
  bad node at LEB 122:241824
  ubifs_iget: failed to read inode 346, error -22
  ubifs_lookup: dead directory entry 'iot.1.log', error -22
  ```

- UBIFS 随后进入内部只读保护，后续 `/data` 写入返回 `EROFS`。

## 影响范围

- 项目：PCR02 SSC305 SDK。
- 分区：`ubi0:data` dynamic volume，挂载点 `/data`，文件系统 UBIFS。
- 直接暴露对象：`iot.1.log` 目录项及 inode 346；同页还包含 inode 414、340、482、301，相关目录项后续也可能读取失败。
- 业务影响：`/data` 下日志、缓存、运行态配置和调试 overlay 等持久写入全部失败。
- 当前只有一个现场样本，不外推为所有设备、所有 PEB 或所有写入都存在同类偏移。
- 故障固件版本已确认是 `v1.1.34`，kernel version string 包含 `gc1c1d317f`；应用层、显示路径和异常重启均只作为触发链分析，不据单样本提升为根因。

## 环境

- SoC：SigmaStar SSC305；内核 `5.10.117 #62`。
- 当前项目 Flash 目标：`MX35LF4GE4AD` SPI NAND；FSP/QSPI 当前基线为 54 MHz。
- 配置：`CONFIG_SSTAR_FSP_QSPI=y`、`CONFIG_SSTAR_FLASH=y`，`CONFIG_SSTAR_SOC_ECC` 未启用。
- UBI attach 摘要：1824 个 good PEB，启动日志未报告 bad/corrupted PEB。
- `ubi0:data` LEB size 为 253952 字节；UBIFS minimum I/O unit 为 4096 字节。
- 原始串口日志不复制进 Hub，只保留脱敏来源名：`Serial_2026-07-20_10_24_48_data_readonly.log`（共享工作区现场来源）。

## 时间线

| 时间 | 操作或观察 | 结果 |
| --- | --- | --- |
| 2026-07-16 14:27:24 | `c1c1d317f` / `v1.1.34` 提交 | 标题为固化 ST77912 参数，但同时重新把 boot/kernel 的 SPI NAND `PAD_SPI0_CK` 配为 2mA |
| 2026-07-17 16:33:54 | `iot.log` 的 Modify/Change 时间 | 可能接近日志轮转和 `iot.1.log` 元数据写入，只作线索，不证明因果 |
| 2026-07-20 | remount `/data` 为 RW 并新建文件 | mount 仍显示 `rw`，但 `touch` 返回 `EROFS` |
| 2026-07-20 | 读取 UBIFS/UBI 状态 | `ro_error=1`；UBI `ro_mode=0`；volume `corrupted=0`、`upd_marker=0` |
| 2026-07-20 | `stat`/`ls` 访问 `iot.1.log` | 稳定命中 inode 346、LEB 122:241824 和 dead directory entry |
| 2026-07-20 | 连续读取目标 4 KiB 区域 10 次 | SHA-256 完全一致，当前读取结果稳定 |
| 2026-07-20 | 扫描 LEB 122 内 UBIFS magic 对齐 | 只有一个 4 KiB 页内 6 个连续 node 全部 `mod8=4`，下一页恢复正常 |
| 2026-07-20 | 保存完整 4096 字节 page 并解析 | 页首为 `cc cc cc cc`；其后 5 个 inode node 和 1 个 PAD node 整体 `+4`，所有 node CRC 正确 |
| 2026-07-20 | 解析 PAD node | `len=28`、`type=5`、`pad_len=3268`；原始 `5*160+28+3268=4096`，与完整 page image 精确吻合 |
| 2026-07-20 | 冷启动后复读目标 page | SHA-256 仍完全一致，排除 Linux/UBIFS 单次启动缓存残留 |
| 2026-07-20 | 对照当前 SDK 源码 | 确认只读机制、整页写 `column=0` 和 NAND 状态传播缺口；RIU/BDMA A/B 尚未完成 |
| 2026-07-22 | 审计 `v1.1.34`、显示 MSPI、Flash FSP 和重启路径 | 确认故障镜像运行该 commit；Linux 阶段 SPI NAND CK 为 2mA；显示与 Flash 均使用 BDMA CH0；仓库存在不主动 sync 的调试强制重启路径 |

## 证据

### UBIFS 实例只读，不是整个 UBI device 只读

```text
/sys/kernel/debug/ubifs/ubi0_4/ro_error = 1
/sys/class/ubi/ubi0/ro_mode            = 0
/sys/class/ubi/ubi0_4/corrupted         = 0
/sys/class/ubi/ubi0_4/upd_marker        = 0
```

- `mount` 中的 `rw` 只是 VFS mount flag，不能覆盖 UBIFS 已置位的内部 `ro_error`。
- `assert=read-only` 是 UBIFS assert 处理策略，不是本次访问模式的直接判据。
- `corrupted=0` 和 `upd_marker=0` 不证明 volume 内部 UBIFS node 布局正确。

源码中，dead directory entry 会调用 `ubifs_ro_mode()`；该函数置位 `c->ro_error` 和 `SB_RDONLY`，写路径随后返回 `-EROFS`。相关文件：

- `workspace://pcr02-ssc305/SourceCode/kernel/fs/ubifs/dir.c`
- `workspace://pcr02-ssc305/SourceCode/kernel/fs/ubifs/io.c`

### inode 346 的 node header 位于预期位置后 4 字节

错误位置 `LEB 122:241824` 的前 24 字节为：

```text
00 00 00 00 31 18 10 06 59 78 30 ff 2c 62 00 00
00 00 00 00 a0 00 00 00
```

从 `241828`，即预期位置 `+4` 开始解释：

| 字段 | 值 | 解释 |
| --- | --- | --- |
| magic | `31 18 10 06` | 正确的 `UBIFS_NODE_MAGIC` |
| CRC | `59 78 30 ff` | 按 UBIFS `CRC32_INIT=0xFFFFFFFF` 规则复算正确 |
| sqnum | `0x622c` | node sequence number |
| len | `0xa0` | 160 字节 |
| node type | `0` | inode node |
| key/inum | `0x15a` | inode 346 |

这解释了 `bad node type (160 but expected 0)`：UBIFS 从预期位置解析时，把右移后 header 中的其他字段错当成 node type。

### 异常严格限定在一个 4 KiB minimum-I/O page

目标页基址：

```text
floor(241824 / 4096) * 4096 = 241664
```

该页内 5 个连续、长度均为 160 字节的 inode node 和末尾 1 个 PAD node 出现相同偏移：

| 序号 | 正常期望偏移 | 实际 magic 偏移 | 对齐 |
| ---: | ---: | ---: | ---: |
| 1 | 241664 | 241668 | `mod8=4` |
| 2 | 241824 | 241828 | `mod8=4`，inode 346 |
| 3 | 241984 | 241988 | `mod8=4` |
| 4 | 242144 | 242148 | `mod8=4` |
| 5 | 242304 | 242308 | `mod8=4` |
| 6 | 242464 | 242468 | `mod8=4`，`UBIFS_PAD_NODE`，不是 inode node |

下一页从 `245760` 开始，node magic 恢复为 `mod8=0`；LEB 中此前的大量 node 也保持 `mod8=0`。

已确认的中间结论：异常不是单个 inode，也不是整个 LEB 或 volume 的全局对齐错误，而是一个完整 4 KiB UBIFS page image 整体后移 4 字节。

### 完整 page image、CRC 与截断关系

异常 page 已保存为 `/tmp/leb122_page59.bin`，大小 4096 字节；该 `/tmp` 文件只是现场临时证据，不复制进 Hub。SHA-256 为：

```text
7ae090b3b63cd31cda1198bd1e0127d739057bb27c9472d7dc28fef4fb56c917
```

页头实际内容为：

```text
cc cc cc cc 31 18 10 06 34 2d 9c fe 28 62 00 00 ...
```

按实际 magic 位置解析并依据 `UBIFS_CRC32_INIT=0xFFFFFFFF` 复算，5 个 inode node 和 1 个 PAD node 的 CRC 全部正确：

| 实际页内偏移 | 正常期望偏移 | 类型 | 长度 | 关键字段 | CRC |
| ---: | ---: | --- | ---: | --- | --- |
| 4 | 0 | inode node | 160 | inode 414 | 通过 |
| 164 | 160 | inode node | 160 | inode 346 | 通过 |
| 324 | 320 | inode node | 160 | inode 340 | 通过 |
| 484 | 480 | inode node | 160 | inode 482 | 通过 |
| 644 | 640 | inode node | 160 | inode 301 | 通过 |
| 804 | 800 | PAD node | 28 | `pad_len=3268` | 通过 |

正常 page image 长度恰好为：

```text
5 * 160 + 28 + 3268 = 4096
```

实际读取结果可精确表示为：

```text
actual[0..3]    = cc cc cc cc
actual[4..4095] = expected[0..4091]
expected[4092..4095] 被截断，且这 4 字节属于全零 padding 区域
```

`0xCC` 不是 UBIFS padding：短 padding pattern 为 `0xCE`，PAD node 后的大段区域由 `memset(..., 0, pad_len)` 填零。因此该 4 字节前缀来自 UBIFS page image 以外，强力指向 page buffer、DMA 地址或传输拼接边界发生精确 4 字节错误。

### 当前直接读取结果稳定

```text
122 * 253952 + 241824 = 31223968
floor(31223968 / 4096) = 7623
```

连续读取 `/dev/ubi0_4` 的第 7623 个 4 KiB block 共 10 次，SHA-256 均为：

```text
7ae090b3b63cd31cda1198bd1e0127d739057bb27c9472d7dc28fef4fb56c917
```

冷启动后再次读取仍得到完全相同的 SHA-256。这排除了 Linux page cache、UBIFS runtime cache 和单次启动缓冲残留；但 `/dev/ubi0_4` 仍经过相同 MTD/FSP/BDMA 链，逻辑上仍需 RIU 对照区分 NAND 已持久写偏和驱动对该页确定性读偏。

### 当前源码中的写入参数与错误传播缺口

MTD 整页写路径明确调用 `mdrv_spinand_page_program(..., page, 0, ...)`，正常请求 `column=0`。相关文件：

- `workspace://pcr02-ssc305/SourceCode/kernel/drivers/sstar/flash/nand/mtd_spinand.c`
- `workspace://pcr02-ssc305/SourceCode/kernel/drivers/sstar/flash/nand/mdrv_spinand.c`
- `workspace://pcr02-ssc305/SourceCode/kernel/drivers/sstar/fsp_qspi/drv_fsp_qspi.c`
- `workspace://pcr02-ssc305/SourceCode/kernel/drivers/sstar/fsp_qspi/hal/iford/hal_fsp_qspi.c`

同时确认两个错误传播缺口：

1. `drv_spinand_wait_device_available()` 返回 `void`，丢弃 `drv_spinand_check_status()` 的 timeout/device failure/program/erase failure。
2. page program 完成后只显式识别 `ERR_SPINAND_P_FAIL`，其他非 success 状态可能被当成成功。

这是源码确认事实，但不能单独证明它们直接制造了本次 `+4`。

### `v1.1.34/c1c1d317f` 不只是显示参数修改

现场串口日志确认故障固件为 `v1.1.34`，kernel version string 包含 `gc1c1d317f`。该 commit 标题是 `fix(display): 固化ST77912 SPI参数`，但实际同时修改两套独立 SPI 路径：

1. 显示 MSPI：ST77912 从 36MHz/30fps 改为 54MHz/25fps，`PAD_MSPI_CK` drive level 设为 2（源码注释为 12mA）。
2. SPI NAND FSP：boot 和 kernel 的 `hal_gpio_spi0_drv_set()` 都清零 `PAD_SPI0_CK` 的 `BIT7 | BIT8 | BIT10`，按仓库既有硬件注释对应 2mA。

Git 历史显示该 Flash 电气改动曾经独立引入并撤销：

| Commit | 标题 | SPI NAND CK 行为 |
| --- | --- | --- |
| `fccecef83` | `fix(flash): 将SPI0时钟驱动降至2mA` | 强制 2mA |
| `43fe9e2ac` | `fix(flash): 恢复SPI0默认驱动能力` | 不改平台默认值 |
| `c1c1d317f` | `fix(display): 固化ST77912 SPI参数` | 在显示提交中再次强制 2mA |

现场启动顺序进一步确认修改实际生效：

```text
bootloader: SPI0 pad drive: default
Linux:     SPI0 CK pad drive: 2mA
display:   PAD_MSPI_CK drive level: 2
display:   ST77912 54MHz, fps=25
```

因此系统可以先由 bootloader 在默认 drive 下正常读取 kernel/rootfs，随后 Linux 把 SPI NAND CK 改为 2mA，`/data` 后续读写、UBIFS commit 和 UBI 搬移均运行在新电气参数下。该相关性强，但单样本仍不能证明 2mA 直接制造了 `+4`；更保守的解释是 2mA 可能降低 54MHz 下的信号裕量，进而触发 FSP/BDMA transaction framing 或完成时序缺陷。

### 显示 MSPI 与 Flash FSP 共用 BDMA CH0

源码确认：

- ST77912 framebuffer 写入通过 MSPI DMA，IFORD `hal_mspi_get_bdma_ch(0)` 返回 `HAL_BDMA_CH0`。
- SPI NAND FSP 的 `flash_impl_bdma_transfer()` 同样固定调用 `hal_bdma_transfer(HAL_BDMA_CH0, ...)`。
- IFORD BDMA HAL 使用 channel semaphore 串行正常 transfer，因此不能据此断言显示和 Flash 正常并发覆盖寄存器。

该共享关系仍有排障价值：显示刷新会让同一 BDMA channel 在 `MIU_TO_MSPI0` 与 `MIU_TO_SPI/FSP` 等 path 间频繁切换；timeout、cancel、pending interrupt、外设完成时序或异常出口若清理不完整，可能暴露 stale word 或 path state 问题。现场前缀恰好是一个 32-bit word，但尚无故障发生时的寄存器 trace，故此项保持 hypothesis。

### 应用层只能作为间接触发负载

- `iot` 日志写入、rename、unlink、fsync 和目录操作不能指定 NAND column、BDMA source 或 UBIFS node 页内偏移，不能正常生成整页 `mod8=4`。
- 高频日志轮转会增加 UBIFS journal commit、page program、GC 和 UBI wear-leveling 次数，因此可能提高底层缺陷命中率。
- framebuffer 应用写入会触发 ST77912/MSPI BDMA，可能增加 BDMA CH0 path 切换压力，但不能直接写 SPI NAND page buffer。
- 普通用户态内存越界受进程地址空间隔离，除非同时存在驱动 ioctl、共享物理内存、`/dev/mem` 或内核模块缺陷，否则不应破坏 NAND DMA buffer。

结论：应用是工作负载或时序触发器候选，不是当前字节形态所支持的直接根因。

### 异常重启是高风险触发器或暴露点

现场日志在重启前出现 `Sent SIGKILL to all processes` 和 `Requesting system reboot`；下次启动时 `factory`、`miservice`、`ota`、`data` 四个 UBIFS volume 均报告 `recovery needed`，SD FAT 也提示未正常卸载。项目脚本还存在 `/data/debug_reboot_after` 开关：命中后不主动 sync，执行 `reboot -f`，失败再写 SysRq `b`。

这些证据支持关机流程存在非干净窗口，但不能证明现场重启一定由该调试开关发起。重启可能扮演三种角色：

1. 打断正在进行的 FSP/BDMA/NAND transaction，触发底层错误路径。
2. 在下次 UBIFS recovery 或 UBI wear-leveling 中增加读写与搬移，从而放大瞬态错误。
3. 仅清空缓存并重新访问已损坏 inode，使此前已存在的坏页首次暴露并令 UBIFS 只读。

普通掉电更常形成 torn page、`0xFF` 混合、node CRC 错误或最后一次提交丢失，不能自然解释 5 个 inode node 和 PAD node 全部 CRC 正确、完整 page image 精确右移 4 字节。因此异常重启是中高概率触发器/暴露点，不是已确认的直接变形机制。

### UBI 搬移可能把一次瞬态错读固化

UBI EBA 在 wear-leveling/scrub 搬移动态卷 LEB 时，会把旧 PEB 读入 `ubi->peb_buf`，对当前 buffer 计算 CRC，再写入新 PEB；默认运行配置不会为每次搬移执行独立内容语义校验。若 FSP/BDMA 某次 silent read 已经把 page 变成 `+4` 且返回成功，UBI 可能为错读内容生成匹配 CRC 并将其持久化，解释冷启动后 hash 稳定。

该链条需要通过 LEB 122 当前映射 PEB 的 VID header、`copy_flag`、`sqnum`、`data_crc` 和 erase counter 进一步判别：`copy_flag=1` 支持经历过搬移，但不能证明错位源头；`copy_flag=0` 会降低该放大路径优先级。

## 假设与排除

| 假设 | 验证动作 | 结果 | 状态 |
| --- | --- | --- | --- |
| 整个 UBI device 进入只读 | 读取 `ubi0/ro_mode` | 值为 0 | 排除 |
| 只有 inode 346 随机损坏 | 扫描 LEB 122 magic 对齐并校验完整 page | 同页 5 个 inode node 和 1 个 PAD node 均 `+4` 且 CRC 正确 | 排除 |
| 整个 LEB/volume 统一偏移 | 比较异常页前后 node | 其他页为 `mod8=0`，下一页恢复正常 | 排除 |
| 当前随机读取波动 | 连续读取 10 次并计算 hash | hash 完全一致 | 优先级显著降低，未排除固定读偏 |
| UBIFS/TNC 全局计算错误 | 对照单页边界、相邻页和整页写参数 | 异常严格限于一个 minimum-I/O page | 低优先级 |
| 单次 page program 的 buffer/DMA source `-4` 或 WBF/payload 拼接异常 | 页首 `0xCC*4`、完整 page image 后移、全部 CRC 正确且冷启动稳定 | 与 DMA 从 `buf-4` 传输 4096 字节高度吻合，但缺少故障发生时 trace/read-back | 第一优先假设，待验证 |
| NAND 内容正常，但该物理页被 FSP/BDMA 稳定读成 `+4` | 当前 UBI cdev 仍走相同读取链 | 现有 hash 循环不能排除 | 必须做 RIU/BDMA A/B |
| 介质、掉电、复位或信号异常触发 program 异常 | 当前没有 P_FAIL/ECC/bad-block 证据 | 不像普通随机 bit corruption，但可能是异常 transaction 的触发条件 | 次级假设 |
| `iot` 日志轮转是底层根因 | 对照 inode 名称和时间线 | 应用无法决定 UBIFS node 的 NAND column | 仅可能是触发负载 |
| `v1.1.34` 的 SPI NAND CK 2mA 降低信号裕量 | Git history、commit diff 与现场启动日志交叉核验 | 修改实际生效且时间相关；无法单独解释完整 32-bit word shift | 高价值触发假设，优先做单变量 A/B |
| 显示 MSPI 与 Flash FSP 共用 BDMA CH0 导致 path 状态泄漏 | 审计 MSPI、Flash OS glue 和 BDMA semaphore | 共享 channel 已确认，正常 transfer 有 semaphore；异常路径和硬件 errata 未排除 | 中优先假设 |
| 异常重启直接生成 `+4` page | 对照关机日志、四卷 recovery 和页面字节形态 | 非干净重启证据成立，但普通掉电不符合完整 page image 精确平移特征 | 仅作触发器、放大器或暴露点 |
| UBI 搬移把一次 silent shifted read 固化 | 对照 EBA copy 流程和冷启动稳定 hash | 机制可成立，缺少 LEB→PEB、VID `copy_flag` 和故障时 trace | 中高优先放大路径 |

## 根因

根因尚未确认。

已确认的故障机制：

1. LEB 122 中单个完整 4 KiB UBIFS page image 位于预期位置 `+4`：5 个 inode node 和 1 个 PAD node CRC 全部正确，页首插入 `0xCC*4`，页尾 4 个 padding 字节被截断。
2. TNC/目录项仍按预期位置 `241824` 查找 inode 346。
3. `ubifs_read_node()` 因 header 错位返回 `-EINVAL`。
4. `ubifs_lookup()` 识别 dead directory entry 并调用 `ubifs_ro_mode()`。
5. `ro_error=1` 令整个 `/data` UBIFS 实例拒绝后续写入。

根因候选优先级：

1. 单次 NAND page program 的 page buffer、BDMA source、FSP outside-WBF/payload 拼接或控制器状态异常；其中多拼接一个 32-bit word 或 BDMA source 实际从 `buf-4` 发送 4096 字节最符合当前字节形态。
2. `v1.1.34` 在 Linux 阶段把 SPI NAND CK 强制设为 2mA，可能在 54MHz 下触发命令/数据边界或完成时序异常；这是当前第一优先单变量回归项，但不是独立根因证明。
3. NAND 内容正常，但同一物理页在当前 FSP/BDMA read path 下稳定出现 4 字节偏移；或者一次瞬态 shifted read 被 UBI wear-leveling/scrub 搬移固化。
4. 显示 MSPI 与 Flash FSP 共用 BDMA CH0，在 timeout/cancel/pending interrupt 或 path 切换异常时泄漏旧状态。
5. 异常重启、复位、忙状态或信号完整性问题触发异常 transaction，或在重启后的 recovery 中暴露已损坏页面；驱动错误传播缺口未把失败上报给 MTD/UBI。

节点 CRC 已完成且全部通过；在 SPI0 CK 单变量 A/B、显示/BDMA 负载矩阵、重启矩阵以及底层路径取证完成前，仍不得把上述任一项写成最终根因。用户当前明确暂缓增加 4 KiB program 后读回和 RIU/BDMA 对比实现，归档仅保留其诊断价值，不把它们列为当前代码交付项。

## IMSSV06C11 最新 SDK 对照

### 对照基线

- CURRENT：`workspace://pcr02-ssc305/SourceCode`
- NEW：本机 `Iford_IMSSV06C11_20260629/SW-SDK` 的 IFORD 组件 HEAD；kernel HEAD 为 `fe4c3303d56a3a4cf2d658725a17ab169f0e06dd`，2026-06-09。
- 方法：只读比较 SPI NAND、FSP/QSPI、IFORD BDMA、UBIFS 和 UBI 关键文件的 SHA256、diff、HEAD ancestry 与相关 Git history；没有构建、刷机或板端 A/B。

### IFORD HEAD 没有针对单页 `+4` 的直接修复

| 层级 | CURRENT 与 NEW | 判断 |
| --- | --- | --- |
| `kernel/drivers/sstar/flash/nand/mdrv_spinand.c` | 字节级相同，SHA256 前缀均为 `e6683a6a201b` | 正常 page read/program、busy/status 检查无增量 |
| `kernel/drivers/sstar/fsp_qspi/drv_fsp_qspi.c` | 字节级相同，SHA256 前缀均为 `52f7588bcbc6` | FSP transaction 编排无增量 |
| `kernel/fs/ubifs/io.c`、`dir.c` | 字节级相同 | UBIFS node 写入、dead entry 和只读保护无增量 |
| `kernel/drivers/mtd/ubi/eba.c` | 字节级相同 | UBI EBA 写路径没有新增 read-back 或内容验证 |
| `mtd_spinand.c` | 文件不同，但正常整页复制和 `page_program(..., column=0, ...)` 语义相同 | 差异主要在 panic/shutdown 锁与 polling 处理，不修复 page buffer 偏移 |
| IFORD FSP/BDMA HAL | 核心地址转换、cache flush、outside-WBF 和传输宽度保持相同 | 没有地址低位 guard、bounce buffer、shift 检测或 program read-back |

NEW 仍保留两个源码确认的错误传播缺口：

1. `drv_spinand_wait_device_available()` 返回 `void`，丢弃 `drv_spinand_check_status()` 的 timeout、device failure、program/erase failure。
2. page program 完成后只显式识别 `ERR_SPINAND_P_FAIL`；其他非 success 状态可能被当成成功。

NEW 没有增加：

- MTD 输入 buffer、固定 `bdma_buf`、虚拟地址、物理地址或 MIU 地址低位验证。
- FSP outside-WBF command/address/payload 的 4 字节边界检查。
- page program 后立即 read-back。
- `actual[4..] == expected[..-4]` 的 shift 检测。
- NAND program retry、controller reset 或 UBI 内容校验。

### CURRENT 的异常处理比 NEW 更完整

CURRENT 已包含以下项目补丁：

- `c2ac630e7 fix(flash): 同步新版SDK读链路`
- `ca80fab53 fix(flash): 避免重启路径无界等待`
- `4f4864dd2 fix(flash): 收敛BDMA超时状态`
- `6613b9229 fix(flash): 防护BDMA不支持路径`

与 NEW 相比，CURRENT 会传播 polling/non-OS BDMA 的真实超时或错误，对不支持路径返回失败，并在 FSP/BDMA timeout 后执行 cancel 清理；panic/shutdown 的锁等待也有上限。整体覆盖 NEW 的 flash/bdma/fsp 目录不仅没有单页 `+4` 修复证据，还会丢失这些防护。

### 其他 SoC 分支只提供线索，不能当作 IFORD 修复

NEW kernel 仓库的非 HEAD refs 中存在两个高相关提交：

- `9f5bfa5ae`：Maruko/infinity6c 修复 `hal_bdma_transfer()` 参数指针仍指向栈内存导致的并发内存访问异常。
- `6e504c3d1`：Maruko/infinity6c 禁用 SPI-to-MIU 的 BDMA offset mode，原因是单次触发会导致 SPI 重复发送两次指令。

边界：

- 两个提交均不在 IFORD HEAD ancestry，只存在于 `rel_cn_Maruko_linux_tiny`。
- 修改的是 `drivers/sstar/bdma/infinity6c/`，不是 SSC305 使用的 `drivers/sstar/bdma/iford/`。
- IFORD 正常 interrupt SPI-to-MIU 路径当前未对该 path 设置自动 `wlast_loss` offset mode；polling/non-OS 路径才启用。因此 `6e504c3d1` 不能直接解释正常业务态日志轮转期间的现场样本。
- 这些提交证明原厂近期处理过 BDMA 参数生命周期和 SPI-to-MIU 重复命令问题，适合作为向 SigmaStar 询问 IFORD 等价 errata 的证据，不适合作为未经验证的直接移植补丁。

### SDK 对照结论

- `source-confirmed`：最新 IFORD HEAD 没有针对本次完整 4 KiB page image `+4`、`0xCC*4` 前缀或尾部截断的直接修复。
- `source-confirmed`：CURRENT 的 BDMA 超时传播、cancel 和有限等待比 NEW 更完整。
- `hypothesis`：其他 SoC 的 BDMA并发与 SPI-to-MIU 重复命令修复可能提示同类控制器风险，需要原厂确认 IFORD errata 和板端单变量实验。
- `prohibited inference`：不能把 NEW 整包升级、其他 SoC commit 或源码相关性表述为 SSC305 已修复或根因已确认。

## 修复或规避

当前没有执行破坏性修复，也没有格式化或重建 `data` volume。

- remount 不能清除 UBIFS 内部 `ro_error`，不是有效修复。
- 直接 unlink `iot.1.log` 会再次访问损坏 inode，且只读状态下不能完成。
- 重启可能暂时清除内存状态，但 committed TNC/LEB 内容仍在；再次访问 dead entry 时大概率重新只读。
- 保存异常页和关键日志前不应重建 `/data`，否则会丢失根因证据。
- 恢复前先备份仍可读取的重要文件；若最终重建 UBIFS，必须另行获得数据清除授权并记录恢复方案。

## 验证

### 已完成

| 验证 | 结果 | 结论 |
| --- | --- | --- |
| UBIFS/UBI 状态 | `ro_error=1`、UBI `ro_mode=0` | 只读保护位于 UBIFS 实例 |
| dead entry 重复访问 | 稳定命中 inode 346、LEB 122:241824 | TNC/目录项定位稳定 |
| 4 KiB block 连续读取 10 次 | SHA-256 完全一致 | 当前读取稳定 |
| LEB 122 magic 扫描 | 单页 5 个 inode node 和 1 个 PAD node 为 `mod8=4`，相邻页正常 | 异常边界收敛到单个 4 KiB page |
| 完整 4096 字节 page 保存和解析 | 页首 `0xCC*4`，其后为右移的完整 UBIFS page 前 4092 字节 | 确认精确插入/截断模型 |
| 5 个 inode node 与 1 个 PAD node CRC | 全部通过 | 排除节点 payload 随机损坏，确认 page image 原本结构正确 |
| PAD node 长度闭合 | `5*160+28+3268=4096` | 确认被移动的是完整 UBIFS minimum-I/O page image |
| 冷启动后复读 | SHA-256 仍相同 | 排除单次启动缓存残留，现象跨冷启动稳定 |
| 当前 SDK 源码审计 | 确认 UBIFS 只读链、整页写 `column=0` 和状态传播缺口 | 下一轮插桩路径明确 |
| `v1.1.34/c1c1d317f` commit 与 Git history 审计 | 确认显示提交重新引入 SPI NAND CK 2mA；前一版本 `v1.1.33` 为平台默认 drive | SPI0 CK 2mA 成为第一优先单变量回归项 |
| 故障串口版本与启动日志核验 | 运行版本为 `v1.1.34/gc1c1d317f`；bootloader 为 default，Linux 为 2mA | 排除“代码未生效”，但仍只是单样本相关性 |
| MSPI/Flash/BDMA 源码交叉审计 | 显示 MSPI 与 Flash FSP 均使用 BDMA CH0；HAL 存在 semaphore | 共享 channel 已确认，正常并发覆盖未证实 |
| 关机与恢复日志核验 | 重启前 SIGKILL/reboot；下次启动四个 UBIFS volume recovery；仓库存在强制重启调试开关 | 非干净重启是触发/暴露假设，不足以解释精确 `+4` |

### 离线待验证

1. 第一优先做 SPI NAND CK drive 单变量 A/B：保持 `v1.1.34` 的显示参数和业务负载不变，只比较平台默认 drive 与 2mA；使用新测试设备、试验卷或已取得数据清除授权的环境，不能用当前已损坏 page 判断修复效果。

2. 分离显示/BDMA 变量：比较显示开启、显示关闭以及 MSPI DMA 关闭/PIO；保持 SPI NAND CK、日志写入和重启方式不变。

3. 分离重启变量：比较停止写入并完成 sync/卸载的干净重启、`reboot -f`、watchdog 和受控掉电；每轮记录 UBIFS recovery、`ro_error`、ECC、UBI scrub/WL 和 FSP/BDMA timeout。

4. 解析 LEB 122 当前映射 PEB 的 VID header，记录 `copy_flag`、`sqnum`、`data_crc` 和 erase counter，判断 UBI 搬移固化路径的权重。

5. 在不增加 page 内容读回的前提下，先为 FSP/BDMA timeout/error 增加轻量现场信息：src/dst 地址低位、长度、path、outside-WBF、switch mode、trigger/done/pending interrupt、NAND status/config，并统一清理所有异常出口。

6. 以下两项保留为后续高判别力实验，但按用户当前边界暂缓代码实现：

   对同一物理 NAND page 做单变量 RIU/BDMA A/B：

   - A：当前 BDMA read。
   - B：只切换 RIU/PIO read；时钟、command、dummy、phase 等保持不变。
   - RIU 仍为 `+4`：优先确认 NAND 中已持久写偏。
   - RIU 恢复正常：确认 FSP/BDMA read path 问题。

7. 冷启动复读已经完成且 hash/偏移不变；该结果证明现象持久或高度确定，但不能替代底层读引擎对照。

8. page program 后立即读回并检测 `actual[4..] == expected[..-4]` 仍是区分 silent write corruption 的有效实验，但当前明确不加入代码；现阶段只记录 MTD 输入 buffer、固定 `bdma_buf` 和 HAL/BDMA 物理源地址低位及摘要。

9. 检查 2026-07-17 16:33:54 前后的日志轮转、watchdog、掉电、重启、OTA、BDMA/FSP timeout 和 NAND program failure。该时间只是候选窗口。

```yaml
manual_validation_pending: true
manual_validation_reason: 完整 page、节点 CRC、冷启动复读、v1.1.34 commit、共享 BDMA CH0 和异常重启路径审计已完成；尚未完成 SPI0 CK、显示/BDMA、重启方式单变量板端矩阵及故障发生时现场取证
required_followup:
  - 比较平台默认 SPI0 CK drive 与 2mA，保持显示和业务负载不变
  - 分离显示开启、显示关闭及 MSPI DMA/PIO，确认共享 BDMA CH0 是否参与
  - 完成干净重启、reboot -f、watchdog 和受控掉电矩阵
  - 解析 LEB 122 对应 PEB 的 VID copy_flag、sqnum、data_crc 和 erase counter
  - 统一 FSP/BDMA 异常出口清理并记录轻量寄存器现场
deferred_by_user_scope:
  - 4 KiB page program 后立即读回与 shift 检测
  - RIU/BDMA 同物理 page 对比实现
owner: leiwenjun
review_after: 2026-10-20
```

## 后续动作

1. 以 `v1.1.34` 为共同基线，优先比较 SPI NAND CK 平台默认 drive 与 2mA；不要同时改变显示频率、fps、MSPI drive、Flash clock 或日志负载。
2. 在 SPI0 CK drive 固定后，分离显示关闭、显示开启+BDMA、显示开启+PIO，验证共享 BDMA CH0 是否参与。
3. 在电气参数和显示负载固定后，运行干净重启、`reboot -f`、watchdog 和受控掉电矩阵；测试必须使用可牺牲设备或已授权环境。
4. 取得 LEB 122 对应 PEB/physical page，解析 VID header；RIU/BDMA 同页 A/B 和 4 KiB program 后读回按用户当前范围暂缓，不在本轮代码修改中加入。
5. 先统一 FSP/BDMA timeout/error cleanup，并记录低开销地址、path 和寄存器现场；继续保留 NAND busy/status 错误传播修复。
6. 根因确认前，不把 24 MHz 降频、格式化 `/data`、关闭日志、恢复 OTP 默认或单纯改成正常重启表述为正式修复。
7. 若确认写路径错位，另建修复验证报告；若确认读路径问题，更新 `boot-flash` 下的 BDMA/RIU 记录并反向链接本文。
8. 当前保持 `draft`，不提升 active，不形成生产发布决策。

## 向 SigmaStar/原厂提问要点

问题单应按“SPI NAND/FSP-BDMA silent page corruption”提交，不只描述“UBIFS 只读”。至少要求原厂确认：

1. IFORD FSP outside-WBF、BDMA 32-bit data depth、0x6B command/address/dummy 四字节协议阶段是否存在 stale word 或 framing errata。
2. `hal_fsp_qspi_bdma_read/write()` timeout/error 时是否必须统一清 trigger、outside-WBF、switch mode、read mode 和 pending interrupt。
3. `PAD_SPI0_CK=2mA` 在 MX35LF4GE4AD、54MHz 和当前板级负载下是否属于受支持配置；需要哪些 setup/hold、波形和 drive 验收条件。
4. MSPI display 与 FSP Flash 共用 `HAL_BDMA_CH0` 是否受官方支持，path 高频切换和异步完成是否有已知限制。
5. IMSSV06C11 是否存在未合入 IFORD HEAD 的 patch、chip stepping errata，或需要 IPL/U-Boot/Linux 同步修改的方案。

需附带完整 4096-byte page、SHA-256、node offset/CRC 表、串口日志摘要、kernel config、SNI 配置以及 `v1.1.33..v1.1.34` 最小 diff；不要发送设备凭证、登录 Cookie、客户数据或完整未脱敏 Flash image。

## 关联材料与边界

- `projects/pcr02-ssc305/archive/source-audit/pcr02_imssv06c11_three_way_sdk_audit_20260715.md`
- `projects/pcr02-ssc305/archive/engineering-archive/pcr02/boot-flash/pcr02_spinand_read_path_bdma_riu_20260529.md`
- `projects/pcr02-ssc305/archive/engineering-archive/pcr02/ubifs-squashfs/pcr02_customer_squashfs_overlay_flash_read_20260606.md`
- 源码 provenance：`pcr02_ssc305_compile` commits `c1c1d317f`、`43fe9e2ac`、`fccecef83`；只读审计，不在归档复制 SDK 源码。
- 现场 provenance：`Serial_2026-07-20_10_24_48_data_readonly.log` 的脱敏摘要；原始日志不复制进 Hub。
- Captured/updated at: 2026-07-22 Asia/Hong_Kong。
- 本记录不复制 raw 串口日志、Flash image、设备凭证或客户信息。
- 本记录不授权格式化 `/data`、修改生产固件、刷机、发布、owner decision、active promotion 或 memory 写入。
