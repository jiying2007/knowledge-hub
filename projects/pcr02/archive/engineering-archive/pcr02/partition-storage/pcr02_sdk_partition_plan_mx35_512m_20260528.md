# PCR02 SDK MX35 512MiB 分区规划归档

日期：2026-05-28

状态：迁移前分区规划基线，部分尺寸和 `/customer` 文件系统结论已被后续方案替代。

当前口径：本文保留用于理解旧生产布局和 MX35 容量规划；当前已验证迁移布局为 `ota=0x6000000`、`customer=0x7000000`、`data=0x8C00000`，且 `/customer` 为 SquashFS on static UBI volume。当前有效方案见 `../decision-index.md` 与 `../ota-release/pcr02-ota-ubia-resize-customer-squashfs-20260529/verified-layout.md`。

本文只归档 SDK 侧 MX35 512MiB SPI NAND 分区布局、UBI volume 职责、挂载参数和调整建议。不包含业务应用目录、应用侧 OTA 服务或运行库依赖内容。

## 配置来源

```text
SourceCode/project/image/configs/general/spinand_MX35_512M.squashfs.partition.config
```

## Flash 几何参数

| 配置项 | 当前值 |
| --- | --- |
| `FLASH_TYPE` | `spinand` |
| `FLASH_BLK_SIZE` | `0x40000` |
| `FLASH_BLK_PAGE_CNT` | `64` |
| `FLASH_BLK_CNT` | `2048` |
| `FLASH_PG_SIZE` | `0x1000` |
| `FLASH_SPARE_SIZE` | `128` |
| `BAKCNT` | `3` |
| `BAKOFS` | `1` |

判断：当前配置面向 MX35 512MiB SPI NAND，不能直接套用厂商默认小容量配置。

## 镜像与挂载列表

```make
IMAGE_LIST = cis boot kernel rootfs misc pstore ubia factory miservice ota customer data
BOOT_IMAGE_LIST = ipl ipl_cust uboot
OTA_IMAGE_LIST = boot kernel rootfs misc miservice customer data
USR_MOUNT_BLOCKS = misc pstore factory miservice ota customer data
```

说明：

1. `IMAGE_LIST` 定义完整烧录镜像布局。
2. `OTA_IMAGE_LIST` 定义 SDK OTA 可选分区集合，不等于默认全部升级。
3. `USR_MOUNT_BLOCKS` 定义系统启动后需要挂载的用户空间分区。

## MTD 分区布局

| 分区 | 类型 | 大小/来源 | 说明 |
| --- | --- | --- | --- |
| `cis` | raw | `FLASH_BLK_SIZE * 10` | 启动和系统分区表相关信息。 |
| `boot` | raw | `ipl + ipl_cust + uboot` | 包含 IPL、IPL_CUST、U-Boot，并有备份布局。 |
| `env` | raw | `0x80000` | U-Boot 环境。 |
| `kernel` | raw | `0xA00000` x 2 | kernel 与 kernel backup。 |
| `rootfs` | squashfs | `0x1600000` | 只读根文件系统，挂载为 `/`。 |
| `misc` | fwfs | `0x200000` | `/misc`。 |
| `pstore` | fwfs | `0x200000` | `/pstore`。 |
| `ubia` | UBI container | 剩余空间 | 承载多个 UBIFS volume。 |

## UBI volume 布局

| Volume | `UBIVOLID` | `PATSIZE` | 挂载点 | `OTABLK` | 建议职责 |
| --- | --- | --- | --- | --- | --- |
| `factory` | `0` | `0xC00000` | `/factory` | `/dev/ubi0_0` | 出厂、校准、设备个体化数据。 |
| `miservice` | `1` | `0x3000000` | `/config` | `/dev/ubi0_1` | SDK 服务配置和系统配置。 |
| `ota` | `2` | `0x9000000` | `/ota` | `/dev/ubi0_2` | OTA 下载包、升级中间文件、升级状态。 |
| `customer` | `3` | `0xB400000` | `/customer` | `/dev/ubi0_3` | 只读资源和业务发布内容。 |
| `data` | `4` | `0x1800000` | `/data` | `/dev/ubi0_4` | 运行期可写数据。 |

## 当前挂载参数

| Volume | 当前挂载参数 | 判断 |
| --- | --- | --- |
| `factory` | 默认 | 保持默认。 |
| `miservice` | 默认 | 保持默认。 |
| `ota` | `-o noatime` | 去掉 `bulk_read`，降低 UBIFS 排查变量。 |
| `customer` | `-o ro,noatime` | 保持只读，并去掉 `bulk_read`。 |
| `data` | 默认 | 保持可写默认行为。 |

关键决策：

```make
ota$(MOUNTPARAM) = -o noatime
customer$(MOUNTPARAM) = -o ro,noatime
```

## customer、data、ota 大小关系

当前规划：

| 分区 | 十六进制大小 | 十进制约值 |
| --- | --- | --- |
| `ota` | `0x9000000` | 144 MiB |
| `customer` | `0xB400000` | 180 MiB |
| `data` | `0x1800000` | 24 MiB |

判断：

1. `customer` 当前明显大于 `data`，适合“只读资源较多、运行期数据较少”的设备模型。
2. 如果后续运行期日志、缓存、用户配置、状态数据增长，`data` 可能偏小。
3. `ota` 需要同时考虑压缩包、解压产物、升级状态文件和失败回滚空间。若升级包变大，144 MiB 可能成为瓶颈。

## 是否建议调整大小

短期建议：不立即调整 UBI volume 大小，把变量收敛到 UBIFS 问题复测。

原因：

1. 当前首要问题是 `/customer` 已出现 UBIFS 异常，需要先用干净分区和无 `bulk_read` 基线复测。
2. 调整 volume 大小会引入新的 OTA/烧录/兼容风险。
3. 若现场已有设备，volume 扩缩容升级需要确认 otaunpack 和升级脚本是否支持 resize 或重建 volume。

中期建议：

| 条件 | 建议 |
| --- | --- |
| `/customer` 实际使用率长期低于 60% | 可评估缩小 `customer`。 |
| `/data` 使用率持续高于 70% | 可评估增大 `data`。 |
| `/ota` 无法同时容纳下载包和中间文件 | 优先优化 OTA 包格式；必要时增大 `ota`。 |
| OTA 流程不支持在线调整 volume | 分区大小调整仅用于完整烧录或工厂升级，不用于普通 OTA。 |

## OTA 调整 UBI volume 大小的风险

调整 UBI volume 大小不是普通文件替换，风险点包括：

1. 需要确认升级工具是否能删除、重建或 resize UBI volume。
2. 需要确认 volume ID 与名称是否保持一致。
3. 需要确认升级过程中不能破坏正在使用的挂载点。
4. 需要确认断电恢复策略。
5. 需要确认坏块预留和 available PEB 变化。
6. 需要确认老设备从旧布局升级到新布局的兼容路径。

当前建议：在没有明确工具链支持证据前，不把普通 OTA 作为分区大小调整手段。分区重规划优先用于完整镜像烧录或受控工厂升级。

## 复测建议

分区规划变更前，先完成以下稳定性基线：

1. 干净烧录当前布局。
2. 确认 `/customer` 挂载为 `ro,noatime`。
3. 确认 `/ota` 挂载为 `noatime`，不带 `bulk_read`。
4. 记录 `ubi0` good/bad/corrupted PEB。
5. 记录各 volume 实际空闲空间。
6. 记录 `/proc/mounts`。
7. 运行目标业务场景并观察 dmesg 中 UBIFS/UBI 错误。

## 后续待补充

1. 生成当前设备 `df -h` 与 UBI debugfs 快照。
2. 记录每个 volume 实际使用率。
3. 对比最新厂商 UBIFS-rootfs 分拆 UBI 容器方案，评估是否有必要从单 `ubia` 多卷演进到多 UBI 容器。
4. 明确 OTA 工具是否支持 UBI volume resize；若不支持，在发布规范中明确禁止普通 OTA 调整分区大小。
5. 设备侧验证命令见 `pcr02_device_validation_commands_20260528.md`。
