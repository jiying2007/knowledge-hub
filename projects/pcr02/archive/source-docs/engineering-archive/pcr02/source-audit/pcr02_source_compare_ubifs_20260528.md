# PCR02 SSC305 三套源码对比归档

日期：2026-05-28

状态：历史源码对比和移植偏离分析，最终发布决策已后续收敛。

当前口径：本文对三套源码的分区/OTA/UBIFS 差异对比仍有参考价值；但 `/customer` 风险缓解方案已从 UBIFS 参数收敛为 SquashFS on static UBI volume。当前有效方案见 `../decision-index.md` 与 `../ota-release/pcr02-ota-ubia-resize-customer-squashfs-20260529/README.md`。

本文归档本轮对 `Iford_IMD00V5.1.1_20250529`、`Iford_IMSSV05C13`、`pcr02_ssc305_compile` 三套代码在 SPI NAND、UBI/UBIFS 分区、OTA、rootfs/customer/data 布局方面的对比结论。重点是判断当前项目是否存在移植偏离，以及最新厂商代码是否提供了相关优化方向。

边界说明：本文是三套源码与项目移植偏离的综合对比，因此会少量提及项目 OTA 入口、应用资源和依赖管理作为偏离背景。SDK 专项分区、发布、文件放置和设备验证命令分别见同目录下的 `pcr02_sdk_*.md` 与 `pcr02_device_validation_commands_20260528.md`。

## 对比对象

| 对象 | 角色 | 说明 |
| --- | --- | --- |
| `Iford_IMD00V5.1.1_20250529` | 原始基线 | 当前项目最初应基于此厂商版本移植。 |
| `Iford_IMSSV05C13` | 最新厂商参考 | 用于查看厂商后续在分区、OTA、UBIFS 方面是否有新增设计或修正。 |
| `pcr02_ssc305_compile` | 当前项目 | PCR02 设备实际使用工程，目标介质为 MX35 SPI NAND Flash。 |

## 总体结论

1. `pcr02_ssc305_compile` 的分区设计已经不是厂商默认 `spinand.squashfs.partition.config` 的简单复制，而是针对 MX35 512MiB SPI NAND 做了项目级扩展：新增 `factory`、`ota`、`data`、`pstore` 等分区/卷，并扩大 `rootfs`、`miservice`、`customer`。
2. 这些偏离大部分是项目需求导致的预期差异，不应简单回退到厂商默认配置。
3. 已识别出一个高风险偏离：`/customer` 曾使用 UBIFS `bulk_read` 挂载选项，而厂商默认 squashfs 配置未对 `customer` 使用该优化。结合故障栈中 `ubifs_tnc_bulk_read` 报错，本轮已经建议并落地回退为 `ro,noatime`。
4. `/ota` 平时不是高频读路径，`bulk_read` 收益有限且会增加排查变量，本轮也建议回退为 `noatime`。
5. 最新 `Iford_IMSSV05C13` 提供了 `spinand.ubifs.partition.config` 这类 UBIFS-rootfs 参考设计，其中将 `rootfs` 与 `miservice/customer` 放在不同 UBI 容器上。这是可参考的厂商设计方向，但当前 PCR02 使用 squashfs rootfs + 单 `ubia` 多卷结构，不能直接照搬。
6. 当前 OTA、rootfs 升级、`app_ota` 调用 `/usr/bin/ota_upgrade.sh`、应用资源打包和 `dep.mk` 均为项目自定义链路，必须用项目文档和构建脚本约束，不能只依赖厂商原始 OTA 假设。

## 2026-05-29 后续修正

后续设备和代码排查将主线进一步收敛到底层 SPI-NAND 读路径：

1. 三套源码对比仍然有效：C13 未看到 UBIFS/MTD 核心层面的直接修复，C13 的主要价值是外围挂载/打包脚本优化。
2. 分区几何和 UBI volume 布局未再作为第一根因。当前更可疑的是 MX35 读路径参数和驱动链路。
3. 重点从“UBIFS 是否有移植偏离”转向“当前 SNI/CIS 读参数、BDMA/cache/FSP_QSPI、ECC 错误上报是否稳定”。
4. 相关新增归档：
   - `pcr02_spinand_read_path_bdma_riu_20260529.md`
   - `pcr02_mx35_sni_cis_audit_20260529.md`
   - `pcr02_ai_voice_ubifs_trigger_chain_20260529.md`

因此本文仍作为三套源码/分区/OTA 对比依据，但不应单独用来解释后续所有 `/customer` 读坏现象。

## 分区配置对比

### 厂商默认 squashfs 配置

`Iford_IMD00V5.1.1_20250529` 与 `Iford_IMSSV05C13` 的默认 `spinand.squashfs.partition.config` 在核心布局上基本一致：

| 项目 | 厂商默认值 |
| --- | --- |
| `IMAGE_LIST` | `cis boot kernel rootfs misc ubia miservice customer` |
| `OTA_IMAGE_LIST` | `boot kernel misc miservice customer` |
| `USR_MOUNT_BLOCKS` | `misc miservice customer` |
| `FLASH_BLK_SIZE` | `0x20000` |
| `FLASH_PG_SIZE` | `0x800` |
| `FLASH_SPARE_SIZE` | `64` |
| `rootfs` 类型 | squashfs，原始 MTD 分区 |
| `rootfs$(PATSIZE)` | `0x600000` |
| `customer` 类型 | UBIFS volume |
| `customer$(PATSIZE)` | `0x35C0000` |
| `customer$(UBIVOLID)` | `1` |
| `customer$(MOUNTPT)` | `ubi0:customer` |
| `customer$(OPTIONS)` | `ubia` |
| `customer$(OTABLK)` | `/dev/ubi0_1` |
| `customer$(MOUNTPARAM)` | 默认未显式配置 |

结论：厂商默认 squashfs 路径中，`customer` 没有显式 `bulk_read` 优化；OTA 默认也不包含 `rootfs`。

### PCR02 MX35 512MiB 配置

当前项目关键文件：

`SourceCode/project/image/configs/general/spinand_MX35_512M.squashfs.partition.config`

| 项目 | 当前 PCR02 值 |
| --- | --- |
| `IMAGE_LIST` | `cis boot kernel rootfs misc pstore ubia factory miservice ota customer data` |
| `OTA_IMAGE_LIST` | `boot kernel rootfs misc miservice customer data` |
| `USR_MOUNT_BLOCKS` | `misc pstore factory miservice ota customer data` |
| `FLASH_BLK_SIZE` | `0x40000` |
| `FLASH_BLK_PAGE_CNT` | `64` |
| `FLASH_BLK_CNT` | `2048` |
| `FLASH_PG_SIZE` | `0x1000` |
| `FLASH_SPARE_SIZE` | `128` |
| `rootfs` 类型 | squashfs，原始 MTD 分区 |
| `rootfs$(PATSIZE)` | `0x1600000` |
| `rootfs$(OTABLK)` | `/dev/mtd5` |
| `misc$(PATSIZE)` | `0x200000` |
| `pstore$(PATSIZE)` | `0x200000` |
| `factory$(UBIVOLID)` | `0` |
| `factory$(PATSIZE)` | `0xC00000` |
| `miservice$(UBIVOLID)` | `1` |
| `miservice$(PATSIZE)` | `0x3000000` |
| `ota$(UBIVOLID)` | `2` |
| `ota$(PATSIZE)` | `0x9000000` |
| `ota$(MOUNTPARAM)` | `-o noatime` |
| `customer$(UBIVOLID)` | `3` |
| `customer$(PATSIZE)` | `0xB400000` |
| `customer$(MOUNTPARAM)` | `-o ro,noatime` |
| `data$(UBIVOLID)` | `4` |
| `data$(PATSIZE)` | `0x1800000` |

结论：PCR02 配置是面向 MX35 512MiB 的定制布局，Flash 几何参数、卷数量和卷大小均与厂商默认配置不同。这类差异属于必要移植差异，但需要被文档化并纳入 OTA 验证。

## 最新厂商 UBIFS-rootfs 参考

`Iford_IMSSV05C13` 还包含 `spinand.ubifs.partition.config` 一类参考配置，主要特征是：

| 项目 | 最新厂商 UBIFS-rootfs 参考 |
| --- | --- |
| rootfs | UBIFS，而不是 squashfs |
| UBI 容器 | 使用 `ubia` 与 `ubib` 分拆 |
| bootargs | 类似 `ubi.mtd=ubia ... ubi.mtd=ubib ... root=ubi:rootfs rw rootfstype=ubifs` |
| customer | 位于 `ubi1:customer` |
| customer OTA block | `/dev/ubi1_1` |

这个设计说明厂商支持另一条路线：rootfs 也放入 UBIFS，并将系统和业务数据卷分散到不同 UBI 容器。它对当前问题有参考价值，但不是 PCR02 当前 squashfs rootfs 设计的直接补丁。

## 移植偏离分类

### 预期偏离

| 偏离项 | 判断 | 原因 |
| --- | --- | --- |
| MX35 512MiB 几何参数 | 预期偏离 | 当前硬件使用 MX35，块大小、页大小、容量与厂商默认 128MiB 类配置不同。 |
| 增加 `factory` | 预期偏离 | 用于工厂校准、设备个体化数据或出厂配置。 |
| 增加 `ota` | 预期偏离 | 用于设备无 SD 卡时承载 OTA 中间文件或升级包处理。 |
| 增加 `data` | 预期偏离 | 用于运行期可写数据，减少 `/customer` 写入。 |
| 增加 `pstore` | 预期偏离 | 用于异常持久化日志。 |
| 扩大 `customer` | 预期偏离 | PCR02 应用资源量远大于厂商 demo。 |
| rootfs 支持 OTA 配置项 | 项目扩展 | 原始分区配置允许 rootfs OTA，但构建脚本默认不升级 rootfs。 |

### 已修正的风险偏离

| 偏离项 | 风险 | 当前处理 |
| --- | --- | --- |
| `/customer` 使用 `bulk_read` | 故障栈出现 `ubifs_tnc_bulk_read`，可能放大异常读路径的问题 | 已回退为 `customer$(MOUNTPARAM) = -o ro,noatime`。 |
| `/ota` 使用 `bulk_read` | `/ota` 非高频读路径，收益有限，增加变量 | 已建议并调整为 `ota$(MOUNTPARAM) = -o noatime`。 |
| 应用运行库依赖未与 `readelf NEEDED` 对齐 | 可导致启动阶段缺库 | 已将 mbedtls 相关 so 加入 `pcr02/dep.mk`。 |

### 仍需关注的设计差异

| 差异 | 风险 | 建议 |
| --- | --- | --- |
| PCR02 将多个 UBIFS volume 放在同一 `ubia` 容器 | 当前无直接证据证明这是根因，但与最新厂商 UBIFS-rootfs 分拆设计不同 | 保留现状，先完成无 `bulk_read`、干净 customer、关闭 core dump 的复测；若仍复现，再评估拆分 UBI 容器或重新规划 volume。 |
| `/customer` 作为只读业务资源区，但应用崩溃 core dump 会读取其 mmap 页 | 不是写入压力，但会触发 UBIFS 读路径 | 关闭 core dump 或限制 core dump；长期减少大文件 mmap 与启动时集中读。 |
| rootfs、customer、data 的 OTA 策略为项目自定义 | rootfs 升级中断风险更高，data 默认升级会破坏用户数据 | 构建脚本默认跳过 `rootfs,data`，需要完整发布时显式指定。 |

## OTA 与发布策略对比

| 项目 | 厂商默认 | PCR02 当前策略 |
| --- | --- | --- |
| 默认 OTA 分区 | `boot kernel misc miservice customer` | 构建脚本默认排除 `rootfs,data`，常规包包含 SoC 必需分区，不默认升级用户数据。 |
| rootfs OTA | 厂商默认 squashfs 配置未纳入默认 OTA | PCR02 配置支持，但 `build.sh` 默认跳过，需要 `--ota-partitions all` 或显式列表。 |
| data OTA | 厂商默认无独立 data | PCR02 有 data，默认不升级，避免覆盖运行期数据。 |
| OTA 执行入口 | 厂商 otaunpack/脚本链路 | PCR02 应用侧 `app_ota` 调用 rootfs 中 `/usr/bin/ota_upgrade.sh`。 |
| 无 SD 卡 OTA | 厂商默认假设不完全匹配 PCR02 | PCR02 需要 `/ota` 分区承载下载和解压空间，但单个 `/ota` 同时放压缩包和解压产物可能不足，需要包格式和空间策略约束。 |

常用完整发布命令：

```bash
cd ~/pcr02_ssc305_compile
./build.sh release --profile ap6303bh_512m_v20 --ota-partitions all --publish-soc
```

严格显式分区写法：

```bash
./build.sh release --profile ap6303bh_512m_v20 --ota-partitions boot,kernel,rootfs,misc,miservice,customer,data --publish-soc
```

常规 OTA 包不升级 rootfs/data 时，沿用默认行为即可。

## 已落地的关键决策

1. `/customer` 保持只读挂载：`-o ro,noatime`。
2. `/customer` 不再使用 `bulk_read`，也不建议显式保留 `no_bulk_read`，因为 UBIFS 默认即为非 bulk read，配置越简洁越利于排查。
3. `/ota` 调整为 `-o noatime`，不再把 `bulk_read` 作为优化项。
4. rootfs、data 默认不升级；完整发布或工厂升级需要显式指定。
5. 应用运行库由 `pcr02/dep.mk` 与 `readelf -d prog_pcr02` 的 `NEEDED` 对齐，避免 `/customer/bin/prog_pcr02` 启动缺库。
6. 已损坏的 `/customer` 不能仅靠重启验证，需要通过干净镜像重刷或 OTA 恢复后再做可靠性复测。

## 后续建议

1. 以干净 `/customer` 镜像、无 `bulk_read` 挂载、关闭 core dump 作为下一轮基线。
2. 复测时同时记录：
   - `/proc/mounts`
   - `dmesg`
   - `/sys/kernel/debug/ubi`
   - `/sys/kernel/debug/ubifs/ubi0_3`
   - `prog_pcr02` 是否产生 signal 7 或 core dump
3. 若无 core dump 后 UBIFS 问题消失，优先继续定位应用崩溃和 mmap/资源加载路径。
4. 若仍复现，再扩大到 SPI NAND 驱动、UBI volume 拆分、ECC/debugfs、厂商最新 NAND/UBIFS patch 的代码级对比。

2026-05-29 补充：后续已经进入第 4 类方向，并且优先级应排序为：

1. RIU/BDMA A/B，确认是否为 BDMA/cache/FSP_QSPI 读路径问题。
2. 降低 MX35 读时钟，验证 SI/phase/dummy 读裕量。
3. 禁用 quad read 或改 single/fast read，验证 QE/0x6b 路径。
4. 修 ECC uncorrected 返回值，避免坏数据被当成功数据交给 UBIFS。
5. AI 语音助手分阶段开关，定位 `libmsc.so`、`wakeupresource.jet`、audio reader、`QIVWAudioWrite` 的触发边界。
