# PCR02 SPI-NAND flash read aging progress

Date: 2026-06-18

Status: active investigation progress note.

Source: PCR02 SSC305 flash-read troubleshooting session on 2026-06-17 to 2026-06-18, selected serial-log summaries, board-side RIU readback, and repository state in `/vsdata/leiwenjun/pcr02_ssc305_compile`.

Scope: This note records the current low-level flash-read investigation state, software baseline, aging-test configuration, and remaining BSP questions. It does not archive full serial logs or claim a final root cause.

## Current Symptom

The remaining issue is still flash-read instability, not a persistent damaged file:

- `/customer` is SquashFS on `ubiblock0_3`.
- `libmsc.so` and `wakeupresource.jet` are high-value stress triggers because wakeup startup reads them during a busy boot window.
- After reboot, the same file can read normally again, so the file image itself is not proven corrupt.
- Observed failures include `libmsc.so warmup read failed ... errno=5`, `SQUASHFS error`, decompression failure, and App `killed by signal 7` / `signal 11` near the wakeup startup window.
- Earlier `UBIBLOCK_DIAG_VERIFY` evidence showed repeated UBI/MTD read paths could return success while data CRC differed, so the active hypothesis remains unstable read data below the SquashFS application layer.

## Disproved Or Weak Fixes

The following changes should not be treated as closed fixes:

1. `spinand_recover_reads` was tested and did not eliminate the failure.
2. Forced 24 MHz SPI-NAND/FSP-QSPI did not eliminate the issue.
3. Moving `/customer` from UBIFS to SquashFS/static volume reduced writable-filesystem risk but did not prove the low-level read path healthy.
4. Six-line SPI0 4mA improved probability but still reproduced failures.
5. CK 2mA plus IO 4mA improved probability further, but long aging still reproduced `errno=5` warmup failures.
6. `libmsc.so` is not considered uniquely corrupt; it is a reproducible read-pressure trigger during wakeup startup.

## Current Software Baseline

The current committed low-drive baseline is:

```text
fccecef83 fix(flash): 将SPI0时钟驱动降至2mA
5ea9e7519 fix(flash): 将SPI0驱动能力调整为4mA
```

Effective baseline:

```text
MX35LF4GE4AD max_clk = 54 MHz
SoC SPI0 CK          = 2mA
SoC SPI0 DO/DI/HLD/WPZ/CZ = 4mA
CMA                  = 4M
CONFIG_HIGHMEM       = off
```

Expected boot confirmation:

```text
U-Boot: SPI0 pad drive: CK 2mA, IO 4mA
Kernel: SPI0 pad drive: CK 2mA, IO 4mA
```

Expected RIU-drive field interpretation:

```text
riu_r 103e 23/24/25/26/27 -> bit7 and bit8 are 0 for IO 4mA
riu_r 103e 28             -> bit7, bit8, and bit10 are 0 for CK 2mA
```

The whole 16-bit register value can contain non-drive bits. Do not require the whole word to be zero.

## Current Uncommitted Aging Instrumentation

There are useful but not-yet-committed aging aids in the worktree:

- `SourceCode/sdk/verify/xcrz_sigmastar_demo/daemon/daemon_main.c`
  - Records abnormal App exits under `/data/daemon_fault`.
  - Counts App signal 7, signal 11, total App faults, and dmesg flash-read evidence.
  - Dumps a bounded dmesg tail to `/data/daemon_fault/app_fault_dmesg.log` when App signal or flash-read evidence is detected.
  - Does not repeatedly restart App after abnormal App exit.
- `SourceCode/kernel/fs/squashfs/block.c`
  - Adds low-count `SQUASHFS_FLASH_DIAG` read-failure diagnostics.
  - Diagnostics are gated by `/data/debug_kernel_printk`.
- `SourceCode/kernel/drivers/mtd/ubi/block.c`
  - Adds `UBIBLOCK_DIAG` and `UBIBLOCK_DIAG_VERIFY` recent-read and repeated-read verification helpers.
- `SourceCode/project/pcr02_customer/prog_application.sh`
  - Supports `/data/debug_kernel_printk` to clear dmesg and raise console printk.
  - Supports `/data/debug_reboot_after` to schedule whole-device reboot after App launch.

These aids are for aging evidence collection and should be reviewed before production submission.

## Recommended Aging Modes

Default low-interference aging:

```sh
rm -rf /data/daemon_fault
rm -f /data/debug_kernel_printk
echo 90 > /data/debug_reboot_after
sync
reboot
```

Use this when the goal is probability and signal counting without changing timing too much.

Short evidence-capture aging:

```sh
rm -rf /data/daemon_fault
touch /data/debug_kernel_printk
echo 120 > /data/debug_reboot_after
sync
reboot
```

Use this only when kernel evidence is needed. It enables console printk and low-count SquashFS/ubiblock diagnostics, so it can change timing and increase serial noise.

Stop auto reboot:

```sh
rm -f /data/debug_reboot_after
sync
```

Post-aging data to collect:

```sh
cat /data/daemon_fault/*.count
cat /data/daemon_fault/app_fault_events.log
tail -n 200 /data/daemon_fault/app_fault_dmesg.log
dmesg | grep -E "SQUASHFS|UBIBLOCK|UBI|mtd_read|ubi_io_read|SPINAND|FLASH|decompression|Failed to read block"
```

## BSP Investigation Direction

The next BSP-level work should focus below SquashFS:

1. Confirm whether FSP/QSPI BDMA cache maintenance covers unaligned buffers correctly in all read paths.
2. Compare BDMA and RIU read paths for the same physical flash range under stress.
3. Add low-count ECC status capture around failed reads, including corrected-bit and failed-bit visibility if the driver can expose it.
4. Verify whether the active boot SPI0 function path uses the same pad-drive control registers already validated by RIU readback.
5. Check reset, power, and flash-ready timing around rapid reboot aging.
6. Keep 54 MHz as the current SNI clock unless a controlled A/B test proves a supported alternative improves behavior.

## Current Conclusion

The active conclusion is unchanged:

```text
The issue is still best treated as low-probability SPI-NAND read-path instability.
SquashFS/libmsc/wakeup are triggers and observation points, not proven root causes.
CK 2mA + IO 4mA is the current aging baseline because it improves probability, but it is not a proven complete fix.
```

## Provenance And Sanitization

- Full serial logs are intentionally not copied into this archive.
- No credentials, private keys, tokens, or NAS secrets are included.
- File paths are local engineering paths used for reproducibility.
- Last local validation before this note: `rtk ./build.sh compile --allow-dirty --no-sync-sources --no-clean --jobs 8` completed successfully after reverting temporary 12mA repro settings back to CK 2mA / IO 4mA.

Related notes:

- `pcr02_spi0_pad_drive_8ma_riu_verification_20260618.md`
- `pcr02_spinand_read_path_bdma_riu_20260529.md`
- `../ubifs-squashfs/pcr02_customer_squashfs_overlay_flash_read_20260606.md`
- `../ubifs-squashfs/pcr02_customer_squashfs_libmsc_errno5_20260617.md`
