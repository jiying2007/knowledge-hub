# PCR02 设备侧验证命令手册

日期：2026-05-28

状态：历史通用命令手册，部分挂载预期已被后续迁移方案替代。

当前口径：迁移后的设备应以 `/customer` 为 `/dev/ubiblock0_3` SquashFS 只读挂载作为验收条件；本文中 `/customer` 为 UBIFS 的检查项仅适用于迁移前基线。当前有效方案见 `../decision-index.md` 与 `../ota-release/pcr02-ota-ubia-resize-customer-squashfs-20260529/README.md`。

本文归档 PCR02 设备侧验证命令，重点覆盖 SDK 镜像、分区挂载、UBI/UBIFS 状态、OTA 空间和基础系统健康检查。本文不归档业务应用仓实现细节、应用侧 OTA 服务端逻辑或应用运行库依赖；这些内容应单独成文。

## 适用范围

| 项目 | 说明 |
| --- | --- |
| 设备 IP | `172.16.16.203` |
| 连接方式 | ADB |
| 介质 | MX35 SPI NAND Flash |
| rootfs | squashfs，只读根文件系统 |
| UBI 容器 | `ubia`，运行时通常为 `ubi0` |
| 重点 volume | `factory`、`miservice`、`ota`、`customer`、`data` |

## 使用原则

1. 先采集状态，再执行会改变状态的命令。
2. 默认不要使用 `dmesg -c`，因为它会清空内核日志；只有做循环压力测试并明确需要清空增量日志时才使用。
3. `/customer` 出现 UBIFS 错误后，不要继续用该分区做可靠性结论，应先恢复干净镜像。
4. 检查 OTA 包和分区时，要区分“SDK OTA 可选分区”和“本次实际 selected partitions”。
5. 设备侧命令尽量保持只读；涉及删除、格式化、重刷、重建 UBI volume 的操作不纳入本手册。

## ADB 连接

主机侧连接设备：

```bash
rtk adb connect 172.16.16.203
rtk adb devices
```

进入 shell：

```bash
rtk adb shell
```

快速执行单条设备命令：

```bash
rtk adb shell cat /proc/mounts
```

## 基础系统状态

查看内核版本与启动时间：

```sh
uname -a
cat /proc/uptime
date
```

查看内存：

```sh
cat /proc/meminfo
free
```

查看进程概况：

```sh
ps
ps -A
```

查看设备节点：

```sh
ls -l /dev/mtd*
ls -l /dev/ubi*
```

## 挂载状态检查

查看所有挂载：

```sh
cat /proc/mounts
mount
```

重点确认：

```sh
cat /proc/mounts | grep -E ' /customer | /ota | /data | /factory | /config | / '
```

预期重点：

| 挂载点 | 预期 |
| --- | --- |
| `/` | squashfs，只读 |
| `/customer` | UBIFS，`ro,noatime`，不带 `bulk_read` |
| `/ota` | UBIFS，`noatime`，不带 `bulk_read` |
| `/data` | UBIFS，可写 |
| `/factory` | UBIFS |
| `/config` | UBIFS |

确认 `/customer` 只读：

```sh
cat /proc/mounts | grep ' /customer '
```

若输出中没有 `ro`，或出现 `bulk_read`，需要回到 SDK 分区配置和启动挂载脚本确认。

## 空间检查

查看文件系统空间：

```sh
df -h
df -h / /customer /ota /data /factory /config
```

查看 inode：

```sh
df -i
```

查看重点目录大小：

```sh
du -sh /customer /ota /data /factory /config 2>/dev/null
```

判断要点：

1. `/ota` 必须能容纳 OTA 下载包和升级中间文件。
2. `/data` 不能长期接近满盘。
3. `/customer` 为只读资源区，使用率过高会影响后续资源扩展。

## UBI 状态检查

查看内核启动和 UBI attach 信息：

```sh
dmesg | grep -Ei 'ubi|ubifs|mtd|nand|ecc|bad block|corrupt|error'
```

查看 debugfs 是否挂载：

```sh
mount | grep debugfs
ls /sys/kernel/debug
```

若 debugfs 未挂载，可尝试：

```sh
mount -t debugfs debugfs /sys/kernel/debug
```

查看 UBI/UBIFS debugfs 入口：

```sh
find /sys/kernel/debug -maxdepth 3 -iname '*ubi*' -o -iname '*ubifs*' -o -iname '*mtd*' -o -iname '*nand*' -o -iname '*ecc*' 2>/dev/null
```

查看 UBI 目录：

```sh
ls -R /sys/kernel/debug/ubi 2>/dev/null
ls -R /sys/kernel/debug/ubifs 2>/dev/null
```

如果系统提供标准 ECC 统计，查看：

```sh
for f in /sys/class/mtd/mtd*/ecc_stats; do
    echo "### $f"
    cat "$f"
done
```

当前设备曾出现无该路径的情况：

```text
cat: can't open '/sys/class/mtd/mtd*/ecc_stats': No such file or directory
```

因此不能把缺少该路径误判为无 ECC 问题，只能说明当前内核未暴露此标准统计入口。

## UBIFS 错误检查

非破坏性检查：

```sh
dmesg | grep -Ei 'ubi|ubifs|ecc|uncorrect|crc|corrupt|error|bad node|bad magic|decompress|readpage'
```

重点错误：

```text
Structure needs cleaning
bad node
bad magic
cannot decompress
do_readpage
ubifs_tnc_bulk_read
uncorrect
CRC error
```

判断：

1. `Structure needs cleaning` 表示文件系统已经不干净或损坏，不能仅靠重启当作恢复完成。
2. `ubifs_tnc_bulk_read` 出现时，需要确认挂载参数是否仍带 `bulk_read`。
3. 如果错误集中在 `ubi0:3`，通常对应 `/customer` volume。

## SPI-NAND 读路径专项检查

当 `/customer` 文件出现一时校验失败、后续又恢复，或 drop cache 后更容易复现时，应优先检查 SPI-NAND 读路径，而不是只看 UBIFS 挂载参数。

关键词：

```sh
dmesg | grep -Ei 'spinand|mx35|mxic|c2|37|03|fsp|qspi|bdma|riu|dummy|phase|clock|ecc|bitflip|uncorrect|ubi|ubifs|decompress|bad data node|readpage'
```

重点确认：

1. 实际识别的 NAND ID 是否为 `c2 37 03`。
2. 是否走 BDMA mode，还是 RIU/PIO。
3. read command、dummy、clock、phase 是否有日志。
4. 是否出现 ECC corrected/failed、bitflip、uncorrectable。
5. UBIFS 报错是否集中在 `ubi0:3`，并能否反查到具体 inode 文件。

关键文件冷读校验：

```sh
sync
echo 3 > /proc/sys/vm/drop_caches
md5sum /customer/lib/libmsc.so
md5sum /customer/bin/resource/msc/res/ivw/wakeupresource.jet
dmesg | grep -Ei 'spinand|fsp|bdma|riu|ubi|ubifs|ecc|uncorrect|decompress|bad data node|readpage' | tail -120
```

如果出现 inode 报错，反查文件：

```sh
find /customer -type f -exec ls -li {} \; 2>/dev/null | grep '^[[:space:]]*<inode>[[:space:]]'
```

注意：如果同一文件本轮 md5 失败、下一轮又成功，不要直接判定为文件永久损坏，应优先怀疑底层读路径偶发返回错误数据。

## 只读压力检查

仅用于确认普通顺序读取是否容易触发问题：

```sh
find /customer -type f -exec cat {} >/dev/null \;
```

循环观察时可以使用：

```sh
while true; do
    find /customer -type f -exec cat {} >/dev/null \;
    dmesg | grep -Ei 'ubi|ubifs|ecc|uncorrect|crc|corrupt|error|bad node|bad magic|decompress|readpage' | tail -50
    sleep 1
done
```

注意：

1. 默认不使用 `dmesg -c`，避免清空重要历史日志。
2. 该测试长时间不复现，只能说明普通顺序只读压力不是稳定触发条件，不能证明 UBIFS 完全无风险。

## AI 语音触发链验证

如果关闭业务应用后反复 reboot + md5 不复现，而打开业务应用或 AI 语音后复现，应对语音助手做分阶段验证。

高风险文件：

```text
/customer/lib/libmsc.so
/customer/bin/resource/msc/res/ivw/wakeupresource.jet
/customer/bin/resource/msc/res/audio/wake_up_sound_1.mp3
/customer/bin/resource/msc/res/audio/wake_up_sound_2.mp3
/customer/bin/resource/msc/res/audio/wake_up_sound_3.mp3
```

建议阶段：

```text
off      关闭 start_ai_voice_thread
thread   只启动线程，不调用 ai_websocket_init
login    只 MSPLogin
session  只 QIVWSessionBegin，加载 wakeupresource.jet
reader   打开 audio reader，但跳过 QIVWAudioWrite
write    完整 QIVWAudioWrite
```

每阶段执行：

```sh
sync
echo 3 > /proc/sys/vm/drop_caches
md5sum /customer/lib/libmsc.so >/dev/null 2>/dev/null || echo FAIL:/customer/lib/libmsc.so
md5sum /customer/bin/resource/msc/res/ivw/wakeupresource.jet >/dev/null 2>/dev/null || echo FAIL:wakeupresource.jet
dmesg | grep -Ei 'ubi|ubifs|spinand|fsp|bdma|riu|ecc|uncorrect|decompress|bad data node|readpage' | tail -80
```

判断原则：

1. 如果 `session` 阶段开始复现，重点看 `wakeupresource.jet` 和 `libmsc.so` 冷读。
2. 如果 `reader` 或 `write` 阶段才复现，重点看音频线程、第三方库执行、DMA/cache/DDR/电源负载。
3. AI 语音路径没有直接写 `/customer` 的证据时，不应归因为应用写坏 `/customer`。

## OTA 空间与文件检查

查看 `/ota`：

```sh
df -h /ota
ls -lah /ota
find /ota -maxdepth 3 -type f -ls 2>/dev/null
```

查看升级目录：

```sh
find /ota -maxdepth 4 -type d -print 2>/dev/null
find /ota -maxdepth 4 -type f -print 2>/dev/null
```

判断：

1. 下载包和解压产物不能长期同时挤满 `/ota`。
2. OTA 失败后应确认中间文件是否残留。
3. 如果无 SD 卡也要支持 OTA，不能把 SD 卡作为唯一下载和解压空间。

## SDK 分区验证

查看 MTD 分区：

```sh
cat /proc/mtd
```

查看启动参数：

```sh
cat /proc/cmdline
```

重点确认：

1. rootfs 是否为 `/dev/mtdblock5` squashfs。
2. 是否包含 `ubi.mtd=ubia`。
3. UBI attach 的 mtd 是否与 SDK 分区表一致。

查看 dmesg 中 rootfs 与 UBI attach：

```sh
dmesg | grep -Ei 'Mounted root|ubi0: attached|user volume|available PEBs|bad PEBs|corrupted PEBs'
```

## pstore 与崩溃信息

查看 pstore：

```sh
ls -lah /pstore 2>/dev/null
find /pstore -maxdepth 2 -type f -print 2>/dev/null
```

查看临时目录是否有 core 文件：

```sh
ls -lah /tmp 2>/dev/null
find /tmp -maxdepth 1 -type f -name 'core-*' -ls 2>/dev/null
```

判断：

1. core 文件写在 `/tmp` 不代表不会读取 `/customer` 映射页。
2. 排查 UBIFS 时建议关闭或限制 core dump，避免崩溃路径放大 `/customer` 读取。

## 推荐采集包

一次完整设备状态采集至少包含以下输出：

```sh
date
uname -a
cat /proc/cmdline
cat /proc/mtd
cat /proc/mounts
df -h
df -i
dmesg | grep -Ei 'ubi|ubifs|mtd|nand|ecc|uncorrect|crc|corrupt|error|bad node|bad magic|decompress|readpage'
find /sys/kernel/debug/ubi -maxdepth 3 -type f -print 2>/dev/null
find /sys/kernel/debug/ubifs -maxdepth 3 -type f -print 2>/dev/null
ls -lah /ota /customer /data /factory /config 2>/dev/null
```

如需保存到主机侧文件，使用主机侧 ADB 命令采集；文件命名建议包含设备、版本、时间和场景。

## 异常分流

| 现象 | 优先判断 | 下一步 |
| --- | --- | --- |
| `/customer` 挂载失败，`Structure needs cleaning` | 文件系统已不干净或损坏 | 恢复干净 `/customer` 后再复测。 |
| dmesg 出现 `ubifs_tnc_bulk_read` | 仍可能走 bulk read 路径 | 检查 `/proc/mounts` 与 SDK 挂载参数。 |
| `/ota` 空间不足 | OTA 空间规划问题 | 清理残留或调整包格式/分区规划。 |
| `/data` 满 | 运行期数据管理问题 | 清理策略或扩大 data。 |
| 无 `/sys/class/mtd/mtd*/ecc_stats` | 内核未暴露标准 ECC 统计 | 使用 debugfs、dmesg 和驱动日志替代。 |
| `bad PEBs` 增长 | NAND 健康风险 | 记录批次和复现条件，必要时对比驱动和硬件。 |
| 同一 `/customer` 文件有时 md5 失败、有时恢复 | 底层读路径偶发错误风险 | 优先做 RIU/BDMA、降频、single read A/B。 |
| 关闭业务应用 reboot + md5 不复现，打开 AI 语音后复现 | AI 语音是高价值触发器 | 按阶段验证 `MSPLogin`、`QIVWSessionBegin`、audio reader、`QIVWAudioWrite`。 |

## 与其他归档的关系

1. 三套源码和分区差异：见 `pcr02_source_compare_ubifs_20260528.md`。
2. UBIFS 问题证据链：见 `pcr02_ubifs_troubleshooting_20260528.md`。
3. SDK OTA 发布策略：见 `pcr02_sdk_ota_release_design_20260528.md`。
4. MX35 分区规划：见 `pcr02_sdk_partition_plan_mx35_512m_20260528.md`。
5. rootfs/customer/data 放置策略：见 `pcr02_sdk_rootfs_customer_data_policy_20260528.md`。
6. SPI-NAND 读路径 A/B：见 `pcr02_spinand_read_path_bdma_riu_20260529.md`。
7. MX35 SNI/CIS 核查：见 `pcr02_mx35_sni_cis_audit_20260529.md`。
8. AI 语音触发链：见 `pcr02_ai_voice_ubifs_trigger_chain_20260529.md`。
9. 首启动 fixup 规程：见 `pcr02_factory_first_boot_fixup_protocol_20260529.md`。

应用侧启动、业务进程、运行库依赖和应用 OTA 服务端验证应单独归档，避免与 SDK 设备基础验证混淆。
