# PCR02 SDK OTA 与发布策略归档

日期：2026-05-28

本文只归档 SDK 侧 OTA、发布、rootfs/data 默认升级策略。范围限定为 `build.sh`、`README.md`、SDK image 配置与发布产物约定；不包含业务应用仓、应用侧 OTA 服务和运行库依赖内容。

2026-06-06 细化：整车 OTA 的 SoC + 主板 MCU + 电机 MCU 编排、NAS latest 解析边界、manifest/hash 门禁，以 `pcr02_vehicle_ota_orchestration_20260606.md` 为准。本文仍保留 SDK 侧 OTA 和分区选择历史口径。

## 归档范围

| 类型 | 路径 |
| --- | --- |
| 发布入口 | `build.sh` |
| 发布说明 | `README.md` |
| MX35 分区配置 | `SourceCode/project/image/configs/general/spinand_MX35_512M.squashfs.partition.config` |
| SDK OTA 产物 | `SourceCode/project/image/output/` 下生成的 SDK 镜像与 OTA 包 |

## 当前结论

1. SDK 分区配置中的 `OTA_IMAGE_LIST` 包含 `rootfs` 和 `data`，但 `build.sh` 默认 SOC OTA 会自动排除这两个分区。
2. `rootfs` 属于高风险系统根文件系统升级项，只在明确需要升级系统基础内容时显式纳入。
3. `data` 属于运行期可写数据分区，默认不升级，避免覆盖设备数据。
4. 常规 SOC OTA 应优先覆盖 `boot`、`kernel`、`misc`、`miservice`、`customer` 等分区。
5. 完整发布和 NAS 发布必须使用 `release --publish-soc` 或单独 `publish-soc`，正式发布默认不覆盖已有 bundle。
6. `ota`、`package`、`vehicle-ota` 等模式只消费已有 SDK 镜像产物，不重新编译系统。

## SDK OTA 分区选择

当前 MX35 512MiB 配置：

```make
OTA_IMAGE_LIST = boot kernel rootfs misc miservice customer data
```

`build.sh` 的默认选择规则：

| 分区 | 默认 SOC OTA | 显式启用方式 | 原因 |
| --- | --- | --- | --- |
| `boot` | 包含 | 默认或显式列表 | 启动链升级项。 |
| `kernel` | 包含 | 默认或显式列表 | 内核升级项。 |
| `rootfs` | 不包含 | `--ota-partitions ...rootfs` 或 `--ota-partitions all` | 根文件系统升级风险高。 |
| `misc` | 包含 | 默认或显式列表 | SDK 配置/杂项分区。 |
| `miservice` | 包含 | 默认或显式列表 | 系统服务配置分区。 |
| `customer` | 包含 | 默认或显式列表 | 只读业务资源分区。 |
| `data` | 不包含 | `--include-data`、显式 `--ota-partitions ...data` 或 `--ota-partitions all` | 运行期数据分区，不应默认覆盖。 |

`build.sh` 中对应规则：

```sh
default_include_ota_partition() {
    local part="$1"
    case "$part" in
        rootfs)
            return 1
            ;;
        data)
            [[ "$OTA_INCLUDE_DATA" -eq 1 ]]
            return
            ;;
        *)
            return 0
            ;;
    esac
}
```

## 常用 SDK 命令

常规发布并发布 SOC bundle 到 NAS：

```bash
./build.sh release --profile ap6303bh_512m_v20 --publish-soc
```

只生成常规 SOC OTA 包，不重新编译系统：

```bash
./build.sh ota --profile ap6303bh_512m_v20 --skip-defconfig
```

需要升级 `rootfs` 时，必须显式指定：

```bash
./build.sh ota --profile ap6303bh_512m_v20 --skip-defconfig --ota-partitions boot,kernel,rootfs,misc,miservice,customer
```

需要升级 `data` 时，必须显式指定：

```bash
./build.sh ota --profile ap6303bh_512m_v20 --skip-defconfig --include-data
```

需要完整分区 OTA 时：

```bash
./build.sh ota --profile ap6303bh_512m_v20 --skip-defconfig --ota-partitions all
```

仅发布已有 SOC 产物到 NAS：

```bash
./build.sh publish-soc --profile ap6303bh_512m_v20
```

## 发布审计点

每次 SDK OTA 或发布需要记录：

1. 完整命令行。
2. `profile`，例如 `ap6303bh_512m_v20`。
3. `version.ini`。
4. SOC bundle 输出目录。
5. OTA 日志中的 `sdk_ota_images`。
6. OTA 日志中的 `selected_partitions`。
7. OTA 日志中的 `skipped_partitions`。
8. 是否显式包含 `rootfs`。
9. 是否显式包含 `data`。
10. 是否发布到 NAS。

其中 `selected_partitions` 与 `skipped_partitions` 是判断 rootfs/data 是否被错误纳入 OTA 的核心证据。

## rootfs 与 data 的默认策略

### rootfs 默认不升级

原因：

1. `rootfs` 是系统根文件系统，升级失败会直接影响启动。
2. 当前 rootfs 为 squashfs 原始 MTD 分区，不是普通可写数据卷。
3. 常规业务资源变更不应强制升级 rootfs。
4. 只有改动基础系统、启动脚本、系统工具或根文件系统内容时，才应纳入。

### data 默认不升级

原因：

1. `data` 是运行期可写数据分区。
2. 覆盖 `data` 可能清除设备状态、缓存、运行期配置或现场数据。
3. 只有工厂恢复、数据结构重置或明确需要清空/重建数据时才应升级。

## NAS 发布约束

1. SOC NAS 发布必须显式使用 `--publish-soc` 或 `publish-soc` 模式。
2. 正式发布默认不覆盖已有 bundle。
3. `--force-publish-soc` 只用于本地重复验证，不应用于正式发布。
4. 发布产物默认设置团队可清理权限；若 NAS 侧仍无法删除，应检查共享 ACL 和 CIFS 挂载参数。

## 风险与建议

| 风险 | 建议 |
| --- | --- |
| 误把 `rootfs` 纳入常规 OTA | 默认行为继续排除；发布审计必须检查 `selected_partitions`。 |
| 误把 `data` 纳入常规 OTA | 仅在明确需要覆盖数据时使用 `--include-data` 或 `--ota-partitions all`。 |
| 只打 OTA 但镜像产物陈旧 | 若改动系统内容，先执行 `compile` 或 `full`。 |
| NAS 发布覆盖正式包 | 正式发布不使用 `--force-publish-soc`。 |
| 同一版本重复 OTA | 版本策略上不支持同版本 OTA，应提升版本号后发布。 |

## 后续待补充

1. 将每次正式 SOC 发布的命令、版本、bundle 路径和分区选择写入发布记录。
2. 对 `SStarOtaLayout.txt` 增加归档检查，确保 `rootfs.sqfs` 和 `data.ubifs` 只在显式要求时出现。
3. 对无 SD 卡场景继续评估 `/ota` 分区容量是否足够容纳下载包和升级中间文件。
4. 设备侧验证命令见 `pcr02_device_validation_commands_20260528.md`。
