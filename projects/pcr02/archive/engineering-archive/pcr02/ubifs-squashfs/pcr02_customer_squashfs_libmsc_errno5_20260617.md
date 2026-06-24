# PCR02 customer SquashFS libmsc errno=5 与 wakeup 触发链排障进度

日期：2026-06-17

状态：当前排障进度归档。本文不替代 `pcr02_customer_squashfs_overlay_flash_read_20260606.md` 和 `decision-index.md`，只补充 2026-06-17 针对 `/customer/lib/libmsc.so`、wakeup 初始化、SquashFS `errno=5`、`spinand_recover_reads` 和应用侧降风险改动的阶段性结论。

## Source

- 当前会话排障和代码修改记录，范围包括：
  - `~/pcr02_ssc305_compile/SourceCode/sdk/verify/xcrz_sigmastar_demo/modules/ai`
  - `~/pcr02_ssc305_compile/SourceCode/sdk/verify/xcrz_sigmastar_demo/daemon`
  - `~/pcr02_ssc305_compile/SourceCode/project/pcr02_customer/prog_application.sh`
  - `~/pcr02_ssc305_compile/SourceCode/kernel/drivers/sstar/flash/nand/mdrv_spinand.c`
- 串口日志摘要：
  - `~/Serial_2026-06-17_15_20_17.log`
  - `~/Serial_2026-06-17_15_34_01.log`
  - `~/Serial_2026-06-17_19_50_14.log`
- 既有归档：
  - `ubifs-squashfs/pcr02_customer_squashfs_overlay_flash_read_20260606.md`
  - `boot-flash/pcr02_spinand_read_path_bdma_riu_20260529.md`

## Sanitization

- 未归档完整串口日志、core dump、网络信息、私有凭证或二进制内容。
- 仅保留关键症状、错误码、代码路径、验证结果和后续排查方向。

## 背景

`/customer` 已从 UBIFS 迁移到只读 SquashFS static UBI volume，用于降低运行期写入面风险。但近期重启压力下仍可见 `/customer` 读取异常，主要集中在启动后应用加载 AI/wakeup 资源阶段。

当前高价值触发链为：

```text
应用启动
  -> 视觉模型、标签、相机参数资源检查
  -> wakeupresource.jet 检查或预加载
  -> 延迟 MSPLogin
  -> dlopen /customer/lib/libmsc.so
  -> QIVWSessionBegin
  -> 偶发 SquashFS read/decompress errno=5 或应用 signal 7/signal 11
```

`libmsc.so` 和 `wakeupresource.jet` 文件本身不是稳定损坏：同一文件在重启后可正常读取，warmup checksum 多次稳定；异常更符合启动期或运行期读路径概率性返回错误数据。

## 当前已做应用侧收敛

### modules/ai

- `prog_pcr02` 已移除对 `libmsc.so` 的直接 `NEEDED` 依赖，wakeup 代码改为运行期 `dlopen`。
- `modules/ai/wakeup_test/chenyf` 下旧三方头文件、旧 `libmsc.so`、旧 `wakeupresource.jet` 已清理，避免模块内重复携带资源。
- wakeup 日志改为使用通用 `AI_LOG_*`，移除直接 `printf`/主动 `fflush` 的调试风格路径。
- 删除 Wakeup shell fallback，避免启动期额外 shell、管道和文件系统读取扰动。
- `MSPLogin` 前检查 `/data/msc`，不存在则创建。
- `MSPLogin` 增加延迟启动，降低应用启动峰值阶段与大量 `/customer` 资源读取、相机/音频/网络初始化的重叠。
- `wakeupresource.jet` 使用 tmpfs 预加载副本参与 `QIVWSessionBegin`，减少后续反复触碰 `/customer`。
- `libmsc.so` 增加 warmup read，失败日志直接记录 `errno`、offset、expected size；`errno=5` 日志不做限频，便于现场统计。
- `QIVWSessionBegin` 超时后标记 `libmsc.so` poisoned，deinit 中跳过 `MSPLogout`，避免进入已疑似异常的三方库清理路径。

### daemon

- daemon 检测 App signal 7 后保存 dmesg，且不再无限反复拉起应用。
- 后续日志显示 signal 11 仍可发生，说明应用侧 poison/跳过 logout 仍不足以完全隔离 `libmsc.so` 内部异常。

### prog_application.sh

- 内核 printk 控制改为由 `/data/debug_kernel_printk` 文件显式开启；默认不执行 `dmesg -c`，默认不把 console printk 提升到 8。
- `spinand_recover_reads` 通过 `/data/enable_spinand_recover_reads` 控制，不作为无条件默认行为。

## 关键日志证据

### Serial_2026-06-17_17_59_23.log

摘要：

- `libmsc.so warmup read failed ... errno=5` 再次复现。
- 失败前出现 `SQUASHFS_FLASH_DIAG`，同一 SquashFS block retry 后 CRC 不一致。
- 新增的 `UBIBLOCK_DIAG_VERIFY` 命中失败 block 对应的 ubiblock 请求，且同一 UBI LEB 范围连续两次 `ubi_leb_read(..., check=0)` 均返回成功但 CRC 不一致。
- 本轮没有出现 App `killed by signal`；应用 warmup 检测主动拦截了 MSPLogin，后续重启来自调试脚本的 40 秒计划重启。

关键证据：

```text
SQUASHFS_FLASH_DIAG: read_fail index=0x3180b6f length=46601 compressed=1 res=-5 first_crc=0x526245db
UBIBLOCK_DIAG_VERIFY: index=0x3180b6f length=46601 sector_range=101381-101473 latest_seq=316 candidates=2
UBIBLOCK_DIAG_VERIFY: seq=316 ... leb=204 offset=98304 bytes=53248 original_ret=0 check0_ret1=0 check0_ret2=0 check0_crc1=0x7e9cf25e check0_crc2=0x6bddb2b5 check0_crc_match=0
UBIBLOCK_DIAG_VERIFY: seq=313 ... leb=204 offset=97792 bytes=4608 original_ret=0 check0_ret1=0 check0_ret2=0 check0_crc1=0xdf0be916 check0_crc2=0xaa243249 check0_crc_match=0
SQUASHFS_FLASH_DIAG: retry_result index=0x3180b6f length=46601 compressed=1 first_res=-5 retry_res=-5 first_crc=0x526245db retry_crc=0xeb3f03e8 crc_match=0
libmsc.so warmup read failed: /customer/lib/libmsc.so errno=5 offset=2228224 expected=3187400
```

该日志把问题边界进一步下沉：

```text
SquashFS 解压失败
  -> SquashFS retry 同 block CRC 不一致
  -> ubiblock recent read 覆盖失败 sector
  -> UBI leb_read 连续两次 ret=0 但 CRC 不一致
  -> 读路径存在“返回成功但数据内容不稳定”的强证据
```

因此，`libmsc.so` 更明确地只是触发 `/customer` 读取的载体；当前证据不支持把根因归到三方库文件固定损坏、应用层读法或 SquashFS 解压器本身。

### Serial_2026-06-17_15_20_17.log

摘要：

- `SQUASHFS error` 出现 4 行。
- `libmsc.so warmup read failed ... errno=5` 出现 2 次。
- `libmsc.so warmup ready` 出现 9 次。
- `QIVWSessionBegin success` 出现 9 次。
- 未见 `killed by signal 7` 或 `killed by signal 11`。
- 未见 `SPI_NAND_DIAG`、`read_recover`、`retry_success`、`riu_fallback`。
- 未见 `SPI NAND read recovery enabled`。

代表性现象：

```text
SQUASHFS error: lzo decompression failed, data probably corrupt
SQUASHFS error: Failed to read block 0x3180a20: -5
libmsc.so warmup read failed: /customer/lib/libmsc.so errno=5 offset=2228224 expected=3187400
```

该日志还存在约 40 秒 debug reboot 触发，来自 `/data/debug_reboot_after` 空文件导致默认 40 秒调试重启；该重启不是 WDT，也不是 App signal。

### Serial_2026-06-17_15_34_01.log

摘要：

- `SQUASHFS error` 出现 2 行。
- `libmsc.so warmup read failed ... errno=5` 出现 1 次。
- `libmsc.so warmup ready` 出现 2 次。
- `QIVWSessionBegin success` 出现 1 次。
- `SPI NAND read recovery enabled` 出现 4 次，且手动读取参数显示 `Y`。
- 未见 `SPI_NAND_DIAG`、`read_recover`、`retry_success`、`riu_fallback`。
- 出现 1 次 `Process App ... killed by signal 11`。

代表性现象：

```text
SQUASHFS error: lzo decompression failed, data probably corrupt
SQUASHFS error: Failed to read block 0x3043cb6: -5
libmsc.so warmup read failed: /customer/lib/libmsc.so errno=5 offset=393216 expected=3187400
```

同一日志还显示：

```text
QIVWSessionBegin timed out
libmsc.so marked poisoned: QIVWSessionBegin timed out
MSPLogout skipped because libmsc.so is poisoned
QIVWSessionBegin failed: err=-1 session=(nil)
Process App ... killed by signal 11
```

这说明 `QIVWSessionBegin` 超时后的 poisoned 策略降低了清理路径风险，但没有彻底避免三方库或调用线程后续崩溃。

## 对 spinand_recover_reads 的阶段判断

`spinand_recover_reads` 对当前场景有诊断价值，但从 `Serial_2026-06-17_15_34_01.log` 看，它没有覆盖这类失败路径。

驱动源码中该开关主要覆盖 `mdrv_spinand` 明确返回失败的路径，例如：

- `read_from_cache` 失败后尝试 RIU fallback。
- page read/cache read 失败后 reset、reg init、setup，再重读。
- buf/without_buf read 失败后执行 recover。

但最新日志中已经确认：

- `spinand_recover_reads=Y`。
- 仍出现 SquashFS LZO decompress failed 和 user-space `read()` 返回 `errno=5`。
- 未出现 `SPI_NAND_DIAG` 或 recovery 成功/失败日志。

因此当前更合理的解释是：

```text
低层 flash 读函数可能返回成功
  -> 上层拿到的压缩块内容偶发错误
  -> SquashFS LZO 校验/解压失败
  -> SquashFS 返回 -EIO
  -> libmsc.so warmup read 看到 errno=5
```

也就是说，现有 recovery 更像捕捉“显式读失败”，而当前更像“读成功但数据内容异常”的路径。该结论仍需 BSP 在 SquashFS/ubiblock/MTD 层补证据。

## 当前结论

1. `libmsc.so` 文件本身不像永久损坏；不同重启中可稳定 warmup ready，异常 block/offset 也不固定。
2. `errno=5` 是 SquashFS 层对底层异常数据或解压失败的上抛结果，不能直接等同于三方库逻辑错误。
3. wakeup/libmsc 是高价值触发器，因为它在启动阶段读取较大的 `/customer` 动态库和资源，并很快进入音频、相机、AI、网络等并发初始化窗口。
4. `spinand_recover_reads` 已开启时仍有 `errno=5` 且无 `SPI_NAND_DIAG`，说明当前故障可能绕过 `mdrv_spinand` 显式错误返回路径。
5. `Serial_2026-06-17_17_59_23.log` 已证明同一 UBI LEB 范围连续读返回成功但 CRC 不一致，问题边界已经下沉到 UBI/MTD/SPI-NAND/FSP/BDMA 读链路。
6. `QIVWSessionBegin` 超时后仍可能 signal 11，说明继续在同一进程内使用或清理 `libmsc.so` 风险较高。
7. 继续把问题只归因于应用层不充分；应用可以降低触发概率和改善证据，但根因需要 BSP 继续在 UBI EBA、MTD、SPI-NAND、FSP/QSPI、BDMA/cache coherency 读链路补仪表。

## 2026-06-17 BSP 诊断推进

已在 kernel 侧增加 fail-only 诊断，不改变正常读路径行为：

- `fs/squashfs/block.c`
  - SquashFS 读/解压失败后打印 `SQUASHFS_FLASH_DIAG`。
  - 对失败 block 做一次受控 retry，打印 retry 前后 CRC 是否一致。
  - 调用 ubiblock recent read dump 和 verify。
- `drivers/mtd/ubi/block.c`
  - 记录最近 32 次 ubiblock read 请求。
  - SquashFS 失败时按 sector 范围匹配最近请求，最多验证 8 条。
  - 对匹配的 LEB/offset/bytes 做两次 `ubi_leb_read(..., check=0)`，打印 ret 和 CRC。
  - 后续补充 `pnum`、`peb_size`、`leb_start`、`raw_addr`、`data_addr`，便于 BSP 把失败 LEB 映射到物理 PEB 和 NAND 地址范围。

已验证：

```text
rtk git diff --check -- SourceCode/kernel/drivers/mtd/ubi/block.c SourceCode/kernel/fs/squashfs/block.c
rtk ./build.sh kernel --allow-dirty --no-sync-sources --no-clean --jobs 8
```

两项均通过，`uImage` 已生成。

下一轮日志判读：

- `check0_crc_match=0`：同一 UBI LEB 范围连续读内容不一致，问题下沉到 UBI EBA/MTD/SPI-NAND/FSP/BDMA。
- `check0_ret1/ret2 < 0`：UBI 层已经能直接返回错误，继续看 UBI/MTD/ECC 日志。
- `check0_crc_match=1` 但 SquashFS retry CRC 不一致：可能在 bio/page/SquashFS 层，或 recent read 没覆盖失败请求。
- `pnum/raw_addr/data_addr` 可用于 BSP 定位具体 PEB、页、列地址和读命令路径。

## 建议的下一步

### 应用侧

1. `QIVWSessionBegin` 超时后，不再继续保留 wakeup 线程运行；更稳妥的策略是 fail fast，由 daemon 做一次受控重启，或把 wakeup/libmsc 隔离到独立子进程。
2. 保留 `libmsc.so` warmup errno=5 日志，不限频；该日志是应用层捕捉 SquashFS read EIO 的关键证据。
3. 避免启动阶段重复 guard 同一批 `/customer` 资源；`ai_flash_resource_guard` 使用 boot 内 cached result 即可。
4. 保持 `/data/debug_kernel_printk` 和 `/data/enable_spinand_recover_reads` 文件开关，不把高噪声内核打印或 recovery 策略变成无条件默认。

### BSP 侧

1. 继续把诊断下移到 `ubi_io_read -> mtd_read -> spinand/fsp/bdma`：同一 `pnum/raw_addr/data_addr` 连续读，确认不一致首次出现在哪一层。
2. 检查 SPI-NAND 驱动是否吞掉 ECC、timeout、DMA 异常，导致上层看到 `ret=0`。
3. 检查 BDMA buffer/cache coherency、DMA completion、alignment、MIU/cache invalidate 是否可能让同一读返回旧数据或混合数据。
4. 检查 FSP/QSPI read cache、dummy cycle、pad drive、command `0x6b`、54M 时序是否存在边界问题。
5. 若同一 `pnum` 反复出现，优先锁定该物理块；若 `pnum` 分散，优先查控制器、BDMA、cache coherency 或时序。
6. 对“读函数返回成功但数据错误”的路径补强：仅依赖 `mdrv_spinand` 返回错误后的 recover 不够，需要在上层发现数据不一致时能触发重读或至少留下定位证据。

## 验证与证据状态

- Host 侧已完成应用和脚本相关构建验证：
  - `rtk bash -n SourceCode/project/pcr02_customer/prog_application.sh`
  - `rtk git diff --check` 针对应用与脚本改动
  - `rtk make modules/ai_lib_all -j8`
  - `rtk make pcr02_app_all -j8`
  - `rtk make pcr02_install`
  - `readelf -d release/bin/prog_pcr02` 未再发现 `NEEDED libmsc.so`
- 板端仍需继续验证：
  - 无 debug reboot 干扰的连续重启日志。
  - `/data/debug_kernel_printk` 开启与关闭两种模式下的内核证据。
  - BSP 新增 SquashFS/ubiblock/MTD 重读诊断后的对比日志。

## 2026-06-17 代码隐患排查与修复进展

本轮沿 `SquashFS -> ubiblock -> UBI -> MTD -> SPI NAND -> FSP/QSPI -> BDMA/cache` 继续排查“读函数返回成功但数据内容不稳定”的可能代码路径，新增两个需要优先验证的修复点。

### 已修复：SquashFS fail-only retry 不再写 page actor

`fs/squashfs/block.c` 的失败后 retry 原先会再次进入解压或 copy actor 路径。该行为对诊断不够干净，存在两个风险：

- 在同一个 `page_actor` 上二次写入，可能改变上层看到的失败现场。
- 如果 retry 成功，可能把原始失败语义变成隐式 recover，干扰定位。

已调整为：

- 第一次失败后释放原 bio。
- 重新读同一 block 只计算 `retry_crc`。
- 不再调用 `squashfs_decompress()` 或 `copy_bio_to_actor()`。
- 最终仍返回第一次失败的 `first_res`，保持 fail-only 诊断语义。

### 已修复：FSP/QSPI BDMA read cache invalidate 范围

`drivers/sstar/fsp_qspi/hal/iford/hal_fsp_qspi.c` 中 `hal_fsp_qspi_bdma_read()` 原逻辑：

```c
flash_impl_mem_invalidate((void *)buf, FLASH_IMPL_CACHE_LINE_ALIGN_UP(size));
```

风险点：

- `buf` 不保证 cache line 对齐。
- `CONFIG_FLASH_CACHELINE_SIZE` 为 64。
- SPI NAND 的 `bdma_buf` 由普通 `kzalloc(page_size + oob_size)` 分配，没有显式 cacheline 对齐保证。
- 只对 size 向上对齐但不对起始地址向下对齐，可能导致首个 cacheline 没有被完整 invalidate。

已按同文件 write 路径风格修复：

- `cache_base = ALIGN_DOWN(buf, 64)`。
- `cache_size = size + (buf - cache_base)`。
- read 前和 read 后都 invalidate `ALIGN_UP(cache_size, 64)`。

该修复直接对应当前现象中的一种高可疑路径：BDMA 已完成、底层返回成功，但 CPU 读到的 buffer 不是本次 DMA 完整结果，从而在 SquashFS LZO 解压或应用 warmup read 中暴露 `errno=5`。

### 已修复：SPI NAND 不可纠 ECC 返回语义

`drivers/sstar/flash/nand/mtd_spinand.c` 中 `sstar_spinand_ecc_read_page()` 和 `sstar_spinand_ecc_read_subpage()` 原逻辑在 `ERR_SPINAND_ECC_NOT_CORRECTED` 时只增加 `mtd->ecc_stats.failed` 并打印日志，最后仍可能返回 0。

虽然 raw NAND 框架后续会观察 `ecc_stats.failed` 并返回 `-EBADMSG`，但驱动回调直接返回 0 不是常规 MTD 语义，也会让失败页的数据先被 memcpy 到上层 buffer。

已调整为：

- 保留 `SPI_NAND_DIAG` 日志。
- 增加 `mtd->ecc_stats.failed` 后立刻 unlock 并返回 `-EBADMSG`。
- timeout/device failure 仍返回 `-EIO`。

这不是当前日志的唯一解释，因为异常日志中没有看到 `SPI_NAND_DIAG`；但该修复可以消除“ECC 不可纠但驱动回调返回成功”的隐患。

### 验证

Host 侧已通过：

```text
rtk git diff --check -- SourceCode/kernel/drivers/sstar/fsp_qspi/hal/iford/hal_fsp_qspi.c SourceCode/kernel/drivers/sstar/flash/nand/mtd_spinand.c SourceCode/kernel/drivers/mtd/ubi/block.c SourceCode/kernel/fs/squashfs/block.c
rtk ./build.sh kernel --allow-dirty --no-sync-sources --no-clean --jobs 8
```

构建日志确认重新编译了：

- `drivers/sstar/fsp_qspi/hal/iford/hal_fsp_qspi.o`
- `drivers/sstar/flash/nand/mtd_spinand.o`
- `fs/squashfs/block.o`

并生成 `arch/arm/boot/uImage`。

### 板端待验证

下一轮板端日志重点：

- 若 `warmup read failed errno=5` 消失或明显下降，优先怀疑 FSP/QSPI BDMA cache coherency 是主因之一。
- 若仍出现 `errno=5` 且有 `SPI_NAND_DIAG ... ecc_uncorrected`，说明 ECC 不可纠路径已经被显式暴露。
- 若仍出现 `errno=5` 但无 `SPI_NAND_DIAG`，继续用 `SQUASHFS_FLASH_DIAG` + `UBIBLOCK_DIAG_VERIFY` 看 `check0_crc_match`，排查 UBI/MTD/FSP/BDMA 返回成功但内容不一致的更低层路径。
- 若新增 `FSP_QSPI_DIAG`，优先检查 wait done、BDMA completion、read size 与 command/dummy cycle。

## 2026-06-17 19:50 日志与 MTD 双读诊断

### Serial_2026-06-17_19_50_14.log

摘要：

- 当前 kernel bootargs 已生效 `cma=4M`。
- `libmsc.so warmup read failed ... errno=5` 仍复现，说明 CMA 从 8M 调到 4M 不是充分修复。
- 失败点仍是 `/customer/lib/libmsc.so` warmup read，触发 SquashFS LZO 解压失败。
- 同一 UBI LEB/PEB 范围连续两次 `ubi_leb_read(..., check=0)` 返回 0，但 CRC 不一致。
- 未见 `SPI_NAND_DIAG`、`FSP_QSPI_DIAG`、`BDMA_DIAG`、App `killed by signal 7/11`。

关键证据摘要：

```text
Kernel command line: ... cma=4M ...
SQUASHFS error: lzo decompression failed, data probably corrupt
SQUASHFS_FLASH_DIAG: read_fail index=0x319967f length=58071 compressed=1 res=-5 first_crc=0x4a7ac19d
UBIBLOCK_DIAG_VERIFY: index=0x319967f length=58071 sector_range=101579-101693 latest_seq=322 candidates=3
UBIBLOCK_DIAG_VERIFY: seq=322 ... leb=205 pnum=308 ... data_addr=0x4d02000 ... check0_ret1=0 check0_ret2=0 check0_crc1=0xe770e8d1 check0_crc2=0x495bf1be check0_crc_match=0
UBIBLOCK_DIAG_VERIFY: seq=321 ... leb=204 pnum=307 ... data_addr=0x4cf3000 ... check0_ret1=0 check0_ret2=0 check0_crc1=0x1e554c35 check0_crc2=0x26eaeb9f check0_crc_match=0
UBIBLOCK_DIAG_VERIFY: seq=320 ... leb=204 pnum=307 ... data_addr=0x4cec000 ... check0_ret1=0 check0_ret2=0 check0_crc1=0xe837be91 check0_crc2=0xe5abff1d check0_crc_match=0
SQUASHFS_FLASH_DIAG: retry_result index=0x319967f length=58071 compressed=1 first_res=-5 retry_read_res=0 first_crc=0x4a7ac19d retry_crc=0x4578e125 crc_match=0
libmsc.so warmup read failed: /customer/lib/libmsc.so errno=5 offset=2752512 expected=3187400
```

该日志把问题进一步收敛到：

```text
SquashFS block read/decompress errno=-5
  -> ubiblock recent read 覆盖失败 sector
  -> UBI LEB 连续双读 ret=0 但 CRC 不一致
  -> 失败集中在 pnum=307/308，raw_addr=0x4cc0000/0x4d00000 附近
  -> 需要继续下沉到 MTD/SPI-NAND/FSP/QSPI/BDMA 层确认首次不一致点
```

### 已新增：MTD/SPI NAND 成功读双读 CRC 诊断

在 `drivers/sstar/flash/nand/mtd_spinand.c` 新增可开关诊断，默认关闭，不改变正常读路径：

- `diag_double_read`
  - 默认 `0`。
  - 置 `1` 后，在 `sstar_spinand_ecc_read_page()` 和 `sstar_spinand_ecc_read_subpage()` 的成功路径，对同一 page/column/size 立即执行第二次 `mdrv_spinand_page_read()`。
  - 仅在二次读 ECC uncorrected、二次读 error、或两次 CRC 不一致时打印 `SPI_NAND_DIAG`。
- `diag_page_start`
  - 默认 `0`，表示不设置下限。
- `diag_page_end`
  - 默认 `0`，表示不设置上限。

本轮日志命中的 `pnum=307/308`，PEB size 256 KiB，page size 4 KiB，每 PEB 64 pages。对应建议定向页范围：

```text
pnum 307 -> page 19648..19711
pnum 308 -> page 19712..19775
combined -> page 19648..19775
```

板端建议启用命令：

```sh
echo 19648 > /sys/module/sstar_spinand/parameters/diag_page_start
echo 19775 > /sys/module/sstar_spinand/parameters/diag_page_end
echo 1 > /sys/module/sstar_spinand/parameters/diag_double_read
```

如果目标板 sysfs 模块名不同，先查找参数路径：

```sh
find /sys/module -path '*/parameters/diag_double_read'
```

下一轮日志判读：

- 出现 `SPI_NAND_DIAG ... double_read_mismatch`：不一致已经在 `mtd_spinand -> mdrv_spinand_page_read` 层复现，优先查 SPI NAND controller/FSP/QSPI/BDMA/cache coherency。
- 出现 `SPI_NAND_DIAG ... double_read_ecc_uncorrected`：第二次读显式暴露 ECC 不可纠，继续查 ECC status 读取、块健康和 ECC 返回语义。
- 仍只有 `UBIBLOCK_DIAG_VERIFY check0_crc_match=0`，但没有 `SPI_NAND_DIAG double_read_*`：不一致可能发生在 MTD 以上或未命中定向 page 范围；扩大 page 范围或补 `ubi_io_read/mtd_read` 层双读。
- `SQUASHFS_FLASH_DIAG` 消失或显著下降：说明本轮修改可能改变了时序或降低了触发概率，但还不能判定根因消失，需要连续启动统计。

Host 侧已验证：

```text
rtk git diff --check -- SourceCode/kernel/drivers/sstar/flash/nand/mtd_spinand.c
rtk ./build.sh kernel --allow-dirty --no-sync-sources --no-clean --jobs 8
```

构建通过，日志确认重新编译 `drivers/sstar/flash/nand/mtd_spinand.o` 并生成 `arch/arm/boot/uImage`。

## 2026-06-18 低噪声 UBI/MTD 分层诊断推进

### 背景

CK 2mA + IO 4mA 后，160 次连续测试仍出现 2 次：

```text
libmsc.so warmup read failed: /customer/lib/libmsc.so errno=5 offset=3014656 expected=3187400
```

这说明当前 pad drive 配置降低了问题概率，但没有根治。结合此前已证据化的 `ubi_leb_read(..., check=0)` 双读 ret=0 但 CRC 不一致，下一步不再扩大应用层日志，而是控制内核日志数量并继续下沉到 UBI IO / MTD 层。

### 已调整：SquashFS 诊断受 `/data/debug_kernel_printk` 控制

`fs/squashfs/block.c`：

- 只有 `/data/debug_kernel_printk` 存在时，才打印 `SQUASHFS_FLASH_DIAG` 并触发 ubiblock 分层 verify。
- 每次启动最多输出 4 个 SquashFS 失败事件的详细诊断。
- 同一失败事件内只消耗一次预算，`read_fail`、`retry_result` 共用该事件开关。
- 不再在 SquashFS 失败时 dump 最近 32 条 ubiblock 请求；改为只验证和失败 block 重叠的少量候选。

### 已调整：ubiblock 候选数量受限

`drivers/mtd/ubi/block.c`：

- recent ring 仍保留 32 条，用于覆盖失败窗口。
- `ubiblock_diag_dump_recent()` 最多打印 8 条，当前 SquashFS 失败路径默认不调用该 dump。
- `ubiblock_diag_verify_recent()` 最多验证 2 条与失败 sector 重叠的候选，避免每次失败输出过多。

### 已新增：同一候选的三层双读 CRC

每条候选现在输出分层结果：

```text
ubi_leb_read ret1/ret2 crc1/crc2
ubi_io_read  ret1/ret2 crc1/crc2
mtd_read     ret1/ret2 read1/read2 crc1/crc2
```

判读规则：

- `ubi_leb_read crc_match=0`，`ubi_io_read crc_match=0`，`mtd_read crc_match=0`：
  问题已经下沉到 MTD/SPI NAND/FSP/QSPI/BDMA/cache 读链路。
- `ubi_leb_read crc_match=0`，但 `ubi_io_read/mtd_read crc_match=1`：
  优先查 UBI EBA、volume desc、LEB 到 PEB 映射、buffer 生命周期或 verify 时机。
- `ubi_io_read crc_match=0`，但 `mtd_read crc_match=1`：
  优先查 UBI IO 层 buffer、offset、headers/data offset 处理。
- `mtd_read crc_match=0`：
  优先查 SPI NAND driver、FSP/QSPI、BDMA/cache coherency、ECC 状态和读时序。

### 本轮 host 验证

```text
rtk git diff --check -- SourceCode/kernel/fs/squashfs/block.c SourceCode/kernel/drivers/mtd/ubi/block.c SourceCode/kernel/drivers/sstar/fsp_qspi/hal/iford/hal_fsp_qspi.c
rtk ./build.sh kernel --allow-dirty --no-sync-sources --no-clean --jobs 8
```

结果：

- `diff --check` 通过。
- kernel 增量构建通过。
- 日志确认重新编译：
  - `fs/squashfs/block.o`
  - `drivers/mtd/ubi/block.o`
  - `drivers/sstar/fsp_qspi/hal/iford/hal_fsp_qspi.o`
- `arch/arm/boot/uImage` 已生成。

### 板端下一轮验证开关

仅在需要采集内核证据的测试轮启用：

```sh
touch /data/debug_kernel_printk
echo 8 > /proc/sys/kernel/printk
dmesg -c
```

复现后保存：

```sh
dmesg > /data/flash_diag_dmesg.log
```

不需要内核详细诊断时：

```sh
rm -f /data/debug_kernel_printk
echo 4 > /proc/sys/kernel/printk
```

当前建议先使用该低噪声分层诊断确认首次不一致层；广泛的 `SPI_NAND_DIAG` / double-read page 扫描不作为默认主线，除非 `mtd_read crc_match=0` 后需要继续下沉到具体 page/cache/status。

## Memory / AGENTS 候选

- PCR02 `/customer` SquashFS 的 `errno=5` 可能来自底层读成功但数据内容异常，不能只等待 `mdrv_spinand` 显式错误日志。
- `libmsc.so`/wakeup 路径是高价值 flash 读问题触发器，但不是已证明的根因。
- `spinand_recover_reads` 可保留为现场诊断开关，但不能作为当前 `errno=5` 场景的充分修复结论。

## Quality Gate

- Source：当前会话、两份串口日志摘要、相关源码路径和既有归档。
- Topic：ubifs-squashfs，关联 boot-flash。
- Archive Candidate Path：`archive/pcr02/ubifs-squashfs/pcr02_customer_squashfs_libmsc_errno5_20260617.md`。
- Sanitization：pass，未归档完整日志、二进制、core dump、凭证或私有运行态信息。
- Provenance：串口日志摘要 + 源码路径 + 既有归档。
- Verification：归档文件创建后做路径和内容检查；板端 BSP 重读诊断尚未完成。
- Memory Candidate：yes，需人工审查后再提升。
- Gate Result：pass for archive, needs-follow-up for BSP root cause.
