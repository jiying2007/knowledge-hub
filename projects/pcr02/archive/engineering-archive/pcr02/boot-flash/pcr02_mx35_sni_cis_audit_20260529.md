# PCR02 MX35 SNI/CIS 配置核查归档

日期：2026-05-29

本文归档 PCR02 当前 MX35LF4GE4AD SPI NAND 的 SNI/CIS 参数核查结论，用于后续与厂商沟通、做降频/RIU/单线读 A/B 固件时保持参数基线清晰。

## 总体结论

当前未看到芯片型号、容量、页大小、OOB 大小、block 大小这类基础几何参数明显错配。

当前镜像和启动日志指向的芯片为：

```text
Vendor: MXIC
Part:   MX35LF4GE4AD
ID:     c2 37 03
```

基础几何为：

```text
Capacity:        512MiB
Page size:       4096
OOB/spare size:  128
Pages per block: 64
Block size:      256KiB
Block count:     2048
```

这些参数与项目 `spinand_MX35_512M.squashfs.partition.config` 方向一致。

## 当前高风险参数组合

虽然基础几何未见明显错配，但当前读路径参数组合偏激进：

```text
read command = 0x6b
dummy        = 8
max_clk      = 54
riu_read     = 0
have_phase   = 0
phase        = 0
flags        = SPINAND_NEED_QE 等
```

该组合意味着：

1. 使用 Quad Output Read。
2. 默认走 BDMA，而不是 RIU/PIO。
3. 使用 54MHz 读时钟。
4. 未显式启用 phase 调整。

在所有板子都有概率复现的背景下，这些参数比单颗 NAND 坏块更值得优先验证。

## 参数核查项

### 几何参数

| 项目 | 当前值 | 判断 |
| --- | --- | --- |
| ID | `c2 37 03` | 符合 MX35LF4GE4AD |
| 容量 | 512MiB | 符合当前分区布局 |
| page | 4096 | 与 `FLASH_PG_SIZE=0x1000` 一致 |
| spare/OOB | 128 | 与 `FLASH_SPARE_SIZE=128` 一致 |
| pages/block | 64 | 与 `FLASH_BLK_PAGE_CNT=64` 一致 |
| block size | 256KiB | 与 `FLASH_BLK_SIZE=0x40000` 一致 |
| block count | 2048 | 与 `FLASH_BLK_CNT=2048` 一致 |

### 读路径参数

| 项目 | 当前值 | 风险 |
| --- | --- | --- |
| `read command` | `0x6b` | Quad read，依赖 QE、dummy、lane mode |
| `dummy` | `8` | 与控制器采样裕量相关 |
| `max_clk` | `54` | 对 SI/phase/power margin 敏感 |
| `riu_read` | `0` | 默认 BDMA |
| `have_phase` | `0` | 未启用 phase 调整 |
| `phase` | `0` | 当前不生效或无显式配置 |

## `flash.sni` 与 `flash_list.sni/cis.bin` 的边界

曾观察到 `flash.sni` 中存在类似 `SIGMASTAR / SPINANDVER` 的占位信息，并出现异常-looking 字段。

当前归档结论是：

1. 当前内核/串口日志实际匹配的是 `c2 37 03` 对应条目。
2. 主要依据应是实际启动日志、`flash_list.sni`、`cis.bin` 和最终烧录产物。
3. 不应把通用占位 `flash.sni` 直接当作当前 MX35 实际运行参数。
4. 若早期 loader 阶段曾先依赖 `flash.sni`，需要单独确认 loader 选择逻辑。

## 与 UBIFS 问题的关系

基础几何正确，不代表读路径稳定。

当前更合理的解释是：

```text
几何参数基本正确
但读模式/时钟/BDMA/cache/phase 组合存在概率性风险
UBIFS/LZO 在读取到错误数据后报 bad node 或 decompress error
```

因此后续优化优先级不是继续改 UBIFS 挂载参数，而是：

1. RIU/BDMA A/B。
2. 降低 `max_clk`。
3. 禁用 quad read。
4. 修 ECC uncorrected 错误返回。
5. 抓启动日志确认实际芯片、读模式和时钟。

## 推荐启动日志关键词

设备侧或串口日志建议过滤：

```sh
dmesg | grep -Ei 'spinand|mx35|mxic|c2|37|03|fsp|qspi|bdma|riu|dummy|phase|clock|ecc|bbt|pni'
```

需要记录：

1. 实际识别 ID。
2. page/OOB/block 参数。
3. 读命令和 dummy。
4. BDMA/RIU 模式。
5. ECC corrected/failed 是否出现。
6. 是否有 BBT/PNI 重建或异常。

## 当前结论

MX35LF4GE4AD 的基础 SNI/CIS 几何配置不是当前首要疑点。首要疑点是读路径参数组合：

```text
BDMA + 0x6b Quad Read + dummy 8 + 54MHz + no phase
```

后续所有固件 A/B 和厂商沟通应围绕这组变量展开，避免把问题重新发散到已基本核对过的容量/page/OOB 几何参数。

