# PCR02 UBIFS 与运行库问题排查归档

日期：2026-05-28

状态：历史排障链路，当前不作为最终发布决策入口。

当前口径：本文保留 UBIFS 异常、AI 触发和底层读路径排查证据；当前规避和发布方案已收敛为 `/customer` SquashFS on static UBI volume。若 static 方案后续仍复现，再回退使用本文和 SPI-NAND 读路径文档继续排查。当前有效方案见 `../decision-index.md` 与 `../ota-release/pcr02-ota-ubia-resize-customer-squashfs-20260529/README.md`。

本文归档 PCR02 在 MX35 SPI NAND 上出现 `/customer` UBIFS 异常、应用压力触发路径、OTA/rootfs/customer/data 调整，以及 `prog_pcr02` 运行库缺失问题的排查证据和处理结论。

边界说明：本文是 UBIFS 问题的综合排查归档，包含应用崩溃、core dump 和运行库缺失这些触发条件或伴随问题。SDK-only 的分区、OTA、rootfs/customer/data 策略和设备侧验证命令已拆分到同目录下的 `pcr02_sdk_*.md` 与 `pcr02_device_validation_commands_20260528.md`。

## 2026-05-29 结论修正

后续调试信息对本文早期结论做了重要修正：

1. `/customer` 不带 `bulk_read` 后仍有复现线索，因此 `bulk_read` 应视为高风险放大器，不再视为根因。
2. `free space fixup` 是首启动风险窗口，但不再作为当前最高概率根因。它应沉淀为产线/测试规程，见 `pcr02_factory_first_boot_fixup_protocol_20260529.md`。
3. 当前更强证据指向底层 SPI-NAND 读路径：BDMA/cache/FSP_QSPI、54MHz quad read、phase/dummy/QE 或 ECC 错误上报。
4. AI 语音助手路径是高价值触发器。关闭业务应用只做 reboot + md5 不复现，屏蔽 `start_ai_voice_thread` 后暂未复现；首坏点经常集中在 `libmsc.so` 或语音资源。详见 `pcr02_ai_voice_ubifs_trigger_chain_20260529.md`。
5. 因此本问题当前更准确的表达是：UBIFS 是错误数据的表现层，`/customer` 只读 UBIFS 不是单独根因；应优先验证 SPI-NAND RIU/BDMA A/B、降频、禁用 quad read 和 ECC uncorrected 返回值。

后续引用本文时，应以本节作为最新判断入口。

## 问题背景

设备烧录启动后运行主应用：

```text
/customer/bin/prog_pcr02
```

主应用工程路径：

```text
~/pcr02_ssc305_compile/SourceCode/sdk/verify/xcrz_sigmastar_demo
```

设备调试方式：

```text
adb connect 172.16.16.203
```

已知现象：

1. `/customer` 分区偶发 UBIFS 异常。
2. 初期异常后重启可能恢复，但发生过异常后后续更容易复现。
3. 长时间单纯只读遍历 `/customer` 未复现。
4. `prog_pcr02` 异常退出并产生 core dump 时，内核日志中出现 UBIFS readpage、bulk_read、decompress 相关错误。
5. 某次操作后 `/customer` 挂载失败，提示 `Structure needs cleaning`。
6. 后续发现 `/customer/bin/prog_pcr02` 还存在 `libmbedtls.so.14` 缺失问题。

## 关键现象与证据

### 只读压力未复现

曾使用如下只读压力脚本长时间读取 `/customer`：

```sh
while true; do
    find /customer -type f -exec cat {} >/dev/null \;
    dmesg -c | grep -Ei 'ubi|ubifs|ecc|uncorrect|crc|corrupt|error' | tail -50
done
```

结果：长时间未出现异常。

判断：单纯顺序读取 `/customer` 文件并不足以稳定触发问题，纯只读压力不是当前最强根因证据。

### ECC 统计路径缺失

设备上检查：

```sh
for f in /sys/class/mtd/mtd*/ecc_stats; do
    echo "### before $f"
    cat "$f"
done
```

结果：

```text
cat: can't open '/sys/class/mtd/mtd*/ecc_stats': No such file or directory
```

debugfs 中可见：

```text
/sys/kernel/debug/ubi
/sys/kernel/debug/ubifs
/sys/kernel/debug/ubifs/ubi0_4
/sys/kernel/debug/ubifs/ubi0_3
/sys/kernel/debug/ubifs/ubi0_2
/sys/kernel/debug/ubifs/ubi0_1
/sys/kernel/debug/ubifs/ubi0_0
/sys/kernel/debug/mtd
```

判断：当前系统没有标准 `/sys/class/mtd/mtd*/ecc_stats` 统计入口，后续需要依赖 debugfs、dmesg、UBI/UBIFS 运行状态和必要时驱动日志判断 NAND/ECC 健康状态。

### 应用崩溃与 UBIFS 错误高度相关

故障日志中出现：

```text
Process App killed by signal 7
core-prog_pcr02-...
```

随后 UBIFS 报错集中在 `ubi0:3`，即 `/customer` 对应 volume：

```text
UBIFS error (ubi0:3): do_readpage: cannot read page ...
UBIFS error (ubi0:3): ubifs_tnc_bulk_read: bad node type
UBIFS error (ubi0:3): ubifs_tnc_bulk_read: bad node at LEB ...
UBIFS error (ubi0:3): ubifs_decompress: cannot decompress ... compressor lzo
UBIFS error (ubi0:3): do_readpage: bad data node
```

内核调用栈包含：

```text
filemap_fault
get_dump_page
dump_user_range
elf_core_dump
do_coredump
```

判断：

1. 该证据链比普通只读压力更强。
2. core dump 过程中，内核会读取进程映射的用户页；如果 `prog_pcr02` 或其资源/动态库来自 `/customer`，即使 core 文件写在 `/tmp`，也会触发对 `/customer` 后备页的读取。
3. 故障栈中出现 `ubifs_tnc_bulk_read`，说明当时 `/customer` 的 UBIFS bulk read 路径被卷入异常。

### `/customer` 挂载失败

后续启动日志中出现：

```text
UBIFS error (ubi0:3): ubifs_check_node: bad magic ...
mount: mounting ubi0:customer on /customer failed: Structure needs cleaning
```

判断：这已经不是单次应用读失败，而是 `/customer` 文件系统状态已经不干净或存在实际损坏。此状态下继续用该分区做复测会污染结论，应先恢复干净 `/customer`。

## 根因判断

当前证据不足以给出“唯一根因”，但可以对候选项排序。

| 候选项 | 当前判断 | 依据 |
| --- | --- | --- |
| 单纯 `/customer` 只读压力 | 可能性降低 | 顺序 `find + cat` 长时间未复现。 |
| 应用崩溃 + core dump 触发大范围映射页读取 | 高风险路径 | UBIFS 错误栈包含 `elf_core_dump`、`get_dump_page`、`filemap_fault`。 |
| `/customer` UBIFS `bulk_read` 放大问题 | 高风险放大器 | 报错点直接包含 `ubifs_tnc_bulk_read`；厂商默认 squashfs 配置未使用该优化。 |
| `/customer` 已有损坏导致后续更易复现 | 高可能 | 已出现 `Structure needs cleaning`。 |
| NAND/ECC/驱动问题 | 未排除 | 当前缺少标准 ecc_stats，需要进一步从 debugfs 和厂商驱动差异确认。 |
| 应用本身 signal 7 崩溃 | 需继续定位 | 它可能是 UBIFS 异常的触发条件，也可能是独立问题。 |

## 已采取或建议落地的处理

### 1. 回退 `/customer` bulk_read

当前建议配置：

```make
customer$(MOUNTPARAM) = -o ro,noatime
```

不建议继续带 `bulk_read`。如需显式写清楚，也可以使用：

```make
customer$(MOUNTPARAM) = -o ro,noatime,no_bulk_read
```

但更推荐简洁写法 `ro,noatime`，因为 `no_bulk_read` 是 UBIFS 默认行为。

### 2. 回退 `/ota` bulk_read

`/ota` 平时不是高频读路径，OTA 时更关心可靠性和空间，读性能收益有限。建议配置：

```make
ota$(MOUNTPARAM) = -o noatime
```

### 3. 恢复干净 `/customer`

一旦出现：

```text
Structure needs cleaning
```

后续复测必须先通过以下方式之一恢复：

1. 重新烧录包含干净 `customer` 的完整镜像。
2. 使用可靠 OTA 包重写 `customer` volume。
3. 必要时重新生成 UBI/UBIFS 镜像，避免在已损坏 volume 上继续判断根因。

### 4. 降低 core dump 对 `/customer` 的影响

短期建议：

1. 复测 UBIFS 时关闭 core dump。
2. 若必须保留 core dump，限制 core 大小，避免应用崩溃时对大量 `/customer` mmap 页触发读取。
3. core 文件存放在 `/tmp` 只能避免写 `/customer`，不能避免内核读取 `/customer` 后备页。

长期建议：

1. 定位 `prog_pcr02` signal 7 的真实原因。
2. 审查启动阶段是否集中 mmap 或读取 `/customer/bin/resource` 下的大文件。
3. 将高频小配置或启动必需资源尽量迁移到 rootfs 或内存缓存。
4. `/customer` 保持只读资源区，运行期写入集中到 `/data`。

## rootfs、customer、data 优化结论

| 分区 | 当前角色 | 建议 |
| --- | --- | --- |
| `rootfs` | 基础系统、启动脚本、OTA 执行脚本 | 可放稳定系统工具和 `/usr/bin/ota_upgrade.sh`；默认 OTA 不升级。 |
| `customer` | 只读应用和资源 | 保持 `ro,noatime`，避免写入，移除非必需大文件和未使用工具。 |
| `data` | 运行期可写数据 | 放日志、配置、缓存、用户数据；默认 OTA 不升级。 |
| `ota` | OTA 中间区 | 存放下载包和升级中间文件；需要控制空间，不建议依赖 SD 卡作为唯一升级路径。 |

已经明确不需要继续携带：

```text
ffmpeg
ffprobe
sqlite3 工具程序
```

但注意：`prog_pcr02` 运行时仍依赖 `libsqlite3.so`，删除的是命令行工具，不等于删除动态库。

## OTA 策略结论

1. `rootfs` 和 `data` 默认不升级。
2. 常规 SoC OTA 包只包含必要系统和业务分区。
3. 需要完整发布时才显式包含 `rootfs,data`。
4. `app_ota` 是独立仓库，应用侧升级流程调用 rootfs 中的：

```text
/usr/bin/ota_upgrade.sh
```

5. OTA 执行脚本放在 rootfs 中可行，但升级 rootfs 本身时，脚本必须在真正改写 rootfs 前已经完成关键准备；更稳妥的方式是由脚本将关键执行逻辑放到 RAM/tmpfs 或使用不依赖被改写分区的执行路径。

## 运行库缺失问题

### 现象

设备启动应用时报错：

```text
/customer/bin/prog_pcr02: error while loading shared libraries: libmbedtls.so.14: cannot open shared object file: No such file or directory
```

### 证据

`pcr02/pcr02.mk` 直接链接 mbedtls：

```make
LIBS += -L$(BUILD_TOP)/libs/3rdparty/mbedtls/lib
LIBS += -lmbedtls -lmbedcrypto -lmbedx509
```

本地 `readelf -d release/bin/prog_pcr02` 显示直接 `NEEDED`：

```text
libmbedtls.so.14
libmbedcrypto.so.7
libmbedx509.so.1
```

ADB 检查设备 `/lib`、`/usr/lib`、`/config/lib`、`/customer/lib` 后，缺失项只剩：

```text
libmbedtls.so.14
libmbedcrypto.so.7
libmbedx509.so.1
```

使用临时目录推送这三个库并加入 `LD_LIBRARY_PATH` 后，`LD_TRACE_LOADED_OBJECTS=1 /customer/bin/prog_pcr02` 不再出现 `not found`。

### 处理

在：

```text
SourceCode/sdk/verify/xcrz_sigmastar_demo/pcr02/dep.mk
```

补充 mbedtls 运行库及其 soname 链接：

```make
MODULE_REL_LIB += libs/3rdparty/mbedtls/lib/libmbedcrypto.so
MODULE_REL_LIB += libs/3rdparty/mbedtls/lib/libmbedcrypto.so.7
MODULE_REL_LIB += libs/3rdparty/mbedtls/lib/libmbedcrypto.so.2.28.9
MODULE_REL_LIB += libs/3rdparty/mbedtls/lib/libmbedtls.so
MODULE_REL_LIB += libs/3rdparty/mbedtls/lib/libmbedtls.so.14
MODULE_REL_LIB += libs/3rdparty/mbedtls/lib/libmbedtls.so.2.28.9
MODULE_REL_LIB += libs/3rdparty/mbedtls/lib/libmbedx509.so
MODULE_REL_LIB += libs/3rdparty/mbedtls/lib/libmbedx509.so.1
MODULE_REL_LIB += libs/3rdparty/mbedtls/lib/libmbedx509.so.2.28.9
```

验证：

1. `make pcr02_app_all` 通过。
2. `make pcr02_install` 通过。
3. `release/lib` 生成 mbedtls 三组库和 soname 链接。
4. 递归检查 `release/bin` 与 `release/lib` 的 ELF 依赖后，设备缺失项仅为上述三个 mbedtls 库。

## 当前推荐复测基线

复测前置条件：

1. 使用干净 `/customer`。
2. 确认 `/customer` 挂载为：

```text
ro,noatime
```

3. 确认 `/ota` 挂载不带 `bulk_read`。
4. 确认 mbedtls 三个运行库已进入 `/customer/lib`。
5. 关闭或限制 core dump。
6. 确认 `prog_pcr02` 不再因缺库立即失败。

建议采集：

```sh
cat /proc/mounts
dmesg | grep -Ei 'ubi|ubifs|ecc|uncorrect|crc|corrupt|error'
find /sys/kernel/debug/ubi -maxdepth 3 -type f -print
find /sys/kernel/debug/ubifs -maxdepth 3 -type f -print
```

如果复现，重点记录：

1. `prog_pcr02` 是否先 signal 7。
2. 是否产生 core dump。
3. UBIFS 报错是否仍出现 `ubifs_tnc_bulk_read`。
4. 报错 volume 是否仍是 `ubi0:3`。
5. 报错 inode/LEB 是否固定。

## 剩余风险

1. 当前已损坏过的 `/customer` 不能作为可靠验证样本。
2. `prog_pcr02` signal 7 尚未完成根因定位。
3. NAND/ECC 健康状态缺少标准 `ecc_stats` 证据。
4. 最新厂商代码是否包含 NAND 驱动层修复，需要进一步对比 kernel/drivers/mtd、SPI NAND ID 表、ECC 配置和 UBIFS 相关 patch。
5. 即使去掉 `bulk_read` 后稳定，也只能说明该选项是高风险放大器，不等于 NAND/应用崩溃根因完全关闭。

## 结论

本轮早期最重要的判断是：`/customer` UBIFS 问题不应继续按“普通只读压力”处理，而应按“应用崩溃 + core dump + UBIFS 映射页读取 + bulk_read 放大 + 已损坏 customer”这条路径收敛。当时优先动作是恢复干净 `/customer`、去掉 `bulk_read`、关闭或限制 core dump、补齐 mbedtls 运行库，然后再观察是否仍有 UBIFS 错误。

截至 2026-05-29，该结论需要更新：上述动作仍有工程价值，但已不是根因主线。当前主线应改为“AI 语音路径触发底层 SPI-NAND 读路径偶发错误，UBIFS/LZO 在读取到错误数据后报错”。下一轮优先验证 RIU/BDMA、降频、single read 和 ECC 返回值，而不是继续围绕 UBIFS 挂载参数做优化。
