# PCR02 SPI-NAND 读路径 BDMA/RIU 排查归档

日期：2026-05-29

状态：底层读路径 fallback 假设。

当前口径：本文保留用于 static SquashFS 方案后续仍复现时继续排查 BDMA/RIU/FSP_QSPI/ECC 返回路径；当前发布主线以 `/customer` SquashFS on static UBI volume 为优先结论。当前有效方案见 `../decision-index.md` 与 `../ota-release/pcr02-ota-ubia-resize-customer-squashfs-20260529/README.md`。

本文归档 PCR02 在 MX35 SPI NAND 上出现 `/customer` UBIFS 偶发异常后，根因方向从 UBIFS/分区层继续收敛到 SPI-NAND 读路径的分析结论和 A/B 验证设计。

## 适用边界

本文只讨论底层 SPI-NAND 读路径、BDMA/RIU、FSP_QSPI、cache、读时钟和 quad read 风险。UBIFS 分区、OTA、rootfs/customer/data 归档见同目录其他 `pcr02_sdk_*.md` 和 `pcr02_ubifs_troubleshooting_20260528.md`。

## 当前判断

截至 2026-05-29，当前更准确的判断是：

1. UBIFS 异常大概率是表现层，不一定是根因层。
2. 所有板子都有概率复现，更像共用软件/时序链路问题，不像单板 NAND 坏块。
3. 同一文件有时读坏、后续又可读出正确 hash，更像偶发读路径错误或 ECC 错误未正确上报。
4. 优先怀疑链路为：

```text
MX35 SPI-NAND -> SStar NAND driver -> FSP_QSPI -> BDMA/cache -> UBIFS/LZO
```

当前最高优先级假设是：

```text
BDMA + 0x6b Quad Read + dummy 8 + 54MHz + have_phase=0
```

在部分负载、温度、电源、DDR/cache 或启动时序条件下存在读稳定性边界。

## 关键证据

### 异常表现不像稳定文件损坏

已观察到的典型现象：

1. `libmsc.so` 或语音资源可能先报错。
2. 某些文件一轮校验失败，后续重新读取可能恢复正确。
3. `sync; echo 3 > /proc/sys/vm/drop_caches; sha256sum ...` 更容易暴露问题。
4. 用户态命令也可能出现 `Segmentation fault` 或 `Bus error`。

这类表现比“UBIFS 文件永久损坏”更接近“冷读 Flash 时偶发返回错误数据”。

### UBI/坏块统计未呈现典型坏块问题

已采集过的设备侧状态包括：

```text
bad_peb_count=0
corrupted PEBs=0
volume corrupted=0
upd_marker=0
ro_error=0
```

这些状态不能排除底层读路径错误，但不支持“当前已经存在明显坏块/UBI 卷损坏”的判断。

### ECC 错误返回路径存在放大风险

源码侧曾看到 `sstar_spinand_ecc_read_page()` 和 subpage read 路径在发现 `ERR_SPINAND_ECC_NOT_CORRECTED` 后，主要做计数和日志，存在仍向上层返回成功的风险。

该问题会导致 UBIFS 拿到错误数据后才表现为：

```text
ubifs_decompress: cannot decompress
bad data node
bad node type
cannot read page
```

需要注意：现场不一定总能看到 `ecc_failures` 增长，因此 ECC 返回值问题可能是放大器，不一定是唯一根因。

## 风险链路

### 1. BDMA 默认启用

SNI 中 `riu_read=0` 时，驱动会选择 BDMA 读路径。若 BDMA/cache 一致性或地址/长度对齐存在边界，可能造成概率性错误数据。

关键关注点：

1. BDMA buffer 地址是否 cache line 对齐。
2. invalidate 地址是否向下对齐。
3. invalidate 长度是否覆盖尾部未对齐区域。
4. BDMA 完成后是否存在同步屏障。
5. 错误返回是否被上层识别。

### 2. 54MHz + Quad Read + 无 phase

当前风险组合：

```text
read command = 0x6b
dummy        = 8
max clock    = 54MHz
have_phase   = 0
riu_read     = 0
```

这类组合对 SI margin、dummy、phase、QE 和板级供电/负载更敏感。

### 3. Quad Read/QE 配置边界

MX35LF4GE4AD 当前使用 quad output read。若 QE 设置、状态寄存器解释、dummy cycle 或 lane mode 与控制器实际行为存在偏差，可能导致少量数据错误且不一定稳定复现。

## A/B 验证顺序

### A. 强制 RIU/PIO，关闭 BDMA

目标：只改一个变量，验证 BDMA/cache/FSP_QSPI DMA 路径是否是主触发因素。

预期：

1. 启动日志从 BDMA 模式变为 RIU/PIO 模式。
2. 反复 reboot + drop cache + hash 校验不再复现，或复现率显著下降。

若成立，根因基本收敛到 BDMA/cache/FSP_QSPI DMA 链路。

### B. 保持 BDMA，降低读时钟

目标：验证 SPI-NAND 读时序裕量。

建议从当前 54MHz 降一档或多档，保持其他变量不变。

若降频后复现率明显下降，优先检查：

1. SNI `max_clk`。
2. phase 配置。
3. dummy cycle。
4. board SI margin。
5. 电源/温度/DDR 带宽对读裕量的影响。

### C. 保持 BDMA，禁用 Quad Read

目标：验证 `0x6b` quad read/QE 路径是否存在兼容边界。

若 single/fast read 稳定，应重点检查：

1. QE enable 流程。
2. status register bit 定义。
3. dummy cycle。
4. FSP_QSPI lane mode。
5. pad driving 和相位。

### D. 修正 ECC uncorrected 返回值

目标：避免 uncorrectable 数据被当作成功数据交给 UBIFS。

建议：

1. page read 和 subpage read 均需修。
2. 遇到不可纠正 ECC 错误时返回负错误，例如 `-EBADMSG` 或驱动体系约定错误码。
3. 临时增加 page、column、size、status、read command、clock、phase、bdma/riu 日志。

## 推荐验证命令

设备侧可用如下命令做只读复验：

```sh
sync
echo 3 > /proc/sys/vm/drop_caches
sha256sum /customer/lib/libmsc.so
sha256sum /customer/bin/resource/msc/res/ivw/wakeupresource.jet
dmesg | grep -Ei 'spinand|fsp|bdma|riu|ubi|ubifs|ecc|bitflip|uncorrect|bad data node|decompress|readpage' | tail -120
```

反复 reboot 后建议优先抓完整 boot log，不要只看当前 shell 的尾部日志。

## 当前结论

截至本归档，不能声明根因已经最终确定。更准确的状态是：

1. 已基本排除单板个体坏块作为主解释。
2. UBIFS 更像读错数据后的表现层。
3. SPI-NAND 读路径是最高优先级验证方向。
4. 第一刀应是 RIU/BDMA A/B，其次是降频和禁用 quad read。
5. AI 语音路径可能是高价值触发器，但它更可能触发底层读路径问题，而不是直接写坏 `/customer`。
