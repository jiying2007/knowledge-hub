# PCR02 SDK rootfs/customer/data 放置策略归档

日期：2026-05-28

状态：部分被后续迁移方案替代。

当前口径：rootfs、data、ota 的职责边界仍可参考；`customer` 从 UBIFS 只读卷迁移为 UBI static volume 承载的 SquashFS，只读挂载到 `/customer`。当前有效方案见 `../decision-index.md` 与 `../ota-release/pcr02-ota-ubia-resize-customer-squashfs-20260529/README.md`。

2026-06-06 细化：rootfs/customer/data 的 symlink 和配置归属以 `pcr02_rootfs_customer_data_symlink_policy_20260606.md` 为准；rootfs raw `/dev/mtdblock5` 的升级链路风险以 `pcr02_rootfs_mtdblock_upgrade_residue_risks_20260606.md` 为准。

本文只归档 SDK 侧 rootfs、customer、data、ota 的职责边界和升级策略。不包含业务应用仓、应用侧 OTA 服务、运行库依赖或具体业务资源清单。

## 目标

1. 明确 SDK 分区的职责边界。
2. 降低 `/customer` 读写和 UBIFS 风险。
3. 避免 rootfs 和 data 在常规 OTA 中被误升级。
4. 给后续瘦身、发布和现场排查提供统一口径。

## 分区职责

| 分区 | 文件系统 | 挂载点 | 读写属性 | 主要职责 |
| --- | --- | --- | --- | --- |
| `rootfs` | squashfs | `/` | 只读 | 基础系统、启动链依赖、系统脚本、稳定系统工具。 |
| `miservice` | ubifs | `/config` | 可写/按系统策略 | SDK 服务配置、系统配置、平台配置文件。 |
| `factory` | ubifs | `/factory` | 通常低频写 | 出厂配置、校准数据、设备个体化数据。 |
| `ota` | ubifs | `/ota` | 可写 | OTA 下载包、中间文件、升级状态。 |
| `customer` | ubifs | `/customer` | 只读挂载 | 业务发布内容和只读资源。 |
| `data` | ubifs | `/data` | 可写 | 运行期数据、缓存、日志、状态。 |

## rootfs 放置原则

适合放入 `rootfs`：

1. 启动前期必须存在的系统脚本。
2. 挂载其他分区之前必须使用的工具。
3. 与 SDK 启动链、系统初始化、基础网络或平台服务强相关的稳定文件。
4. OTA 执行所需的稳定入口脚本，但脚本应避免在升级自身所在分区时依赖正在被改写的文件。
5. 很少变化、且一旦缺失会导致系统无法进入维护状态的基础组件。

不适合放入 `rootfs`：

1. 高频变化内容。
2. 运行期产生的数据。
3. 现场配置、用户数据、缓存和日志。
4. 大体积且经常更新的资源。
5. 仅为某个发布版本临时存在的文件。

升级策略：

1. `rootfs` 默认不进常规 SOC OTA。
2. 只有修改基础系统内容时才显式升级。
3. 显式升级时必须检查 OTA 包布局，确认 `rootfs.sqfs` 是否符合预期。

## customer 放置原则

适合放入 `customer`：

1. 发布时确定、运行期不写入的只读内容。
2. 可通过 SOC OTA 整体替换的发布内容。
3. 不属于设备个体化、不属于现场运行期状态的数据。

不适合放入 `customer`：

1. 运行期写入文件。
2. 日志、缓存、临时文件。
3. OTA 下载包和解压中间文件。
4. 设备个体化校准数据。
5. 可以放到 rootfs 的基础系统文件。

挂载策略：

```make
customer$(MOUNTPARAM) = -o ro,noatime
```

原因：

1. `ro` 可以阻断运行期误写。
2. `noatime` 减少访问时间更新。
3. 不使用 `bulk_read`，避免在当前 UBIFS 问题排查中引入高风险放大器。

## data 放置原则

适合放入 `data`：

1. 运行期生成的数据。
2. 日志、缓存、状态文件。
3. 现场配置和用户数据。
4. 可在异常恢复时保留或按策略清理的数据。

不适合放入 `data`：

1. 启动早期必须存在且影响系统进入维护状态的基础文件。
2. 发布版本固定且可通过 OTA 替换的只读内容。
3. 出厂校准和设备个体化关键数据。

升级策略：

1. `data` 默认不进常规 SOC OTA。
2. 只有明确需要清空、重建或迁移数据结构时才显式纳入。
3. 显式纳入时必须在发布说明中标注会覆盖运行期数据。

## ota 放置原则

适合放入 `ota`：

1. 网络下载的 SOC OTA 包。
2. OTA 解压中间文件。
3. OTA 状态文件。
4. 升级前后的校验记录。

风险：

1. 单个 `/ota` 分区同时容纳压缩包和解压产物时可能空间不足。
2. 若依赖 SD 卡作为下载目录，无 SD 卡场景会存在升级链路隐患。
3. OTA 中间文件清理不彻底会影响下一次升级。

挂载策略：

```make
ota$(MOUNTPARAM) = -o noatime
```

## 文件移动和瘦身原则

SDK 侧瘦身和调整遵循以下顺序：

1. 先确认文件属于系统基础、只读发布内容、运行期数据还是升级中间文件。
2. 系统基础且稳定的内容优先放 `rootfs`。
3. 只读发布内容放 `customer`。
4. 运行期写入内容放 `data`。
5. OTA 下载和中间文件放 `ota`。
6. 删除不需要的工具前，区分“可执行工具”和“运行时动态库”。
7. 每次移动后都要通过 SDK 镜像布局和设备挂载结果验证。

## 验证清单

每次调整 SDK 文件放置策略后，至少检查：

```sh
cat /proc/mounts
df -h
dmesg | grep -Ei 'ubi|ubifs|ecc|uncorrect|crc|corrupt|error'
```

SDK 产物侧检查：

1. OTA 包中是否错误包含 `rootfs.sqfs`。
2. OTA 包中是否错误包含 `data.ubifs`。
3. `/customer` 是否按 `ro,noatime` 挂载。
4. `/ota` 是否不带 `bulk_read`。
5. `/data` 是否保持可写。

## 后续待补充

1. 增加 SDK 打包后分区内容清单，按 rootfs/customer/data/ota 分类输出。
2. 增加 OTA 包布局检查脚本，明确 rootfs/data 是否被纳入。
3. 统计各分区实际使用率，为后续调整 customer/data/ota 大小提供依据。
4. 将“可执行工具删除”和“动态库保留”拆成独立应用侧归档，避免与本 SDK 文档混淆。
5. 设备侧验证命令见 `pcr02_device_validation_commands_20260528.md`。
