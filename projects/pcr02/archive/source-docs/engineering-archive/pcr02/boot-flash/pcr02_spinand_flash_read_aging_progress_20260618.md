# PCR02 SPI-NAND flash read aging progress

Date: 2026-06-18

Status: active investigation progress note.

Source: PCR02 SSC305 flash-read troubleshooting session on 2026-06-17 to 2026-06-18, selected serial-log summaries, board-side RIU readback, and repository state in `~/pcr02_ssc305_compile`.

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

## 2026-06-22 BDMA timeout / late IRQ / libmsc errno=5 status update

Status: active BSP-level investigation. The current evidence does not prove one final root cause, but it further concentrates the issue in the FSP/QSPI/BDMA/MTD read path.

Source:

- `Serial_2026-06-22_12_16_25.log`
- Current repository state under `~/pcr02_ssc305_compile`
- Prior 2026-06-17 to 2026-06-18 SquashFS/ubiblock/MTD diagnostic work

### Current interpretation

`libmsc.so warmup read failed`, `wait bdma done timeout`, and `CamOsTsemUp` / `hal_bdma_interrupt` are not all from the same reboot cycle and should not be treated as one direct per-cycle causal chain.

They are, however, strongly related as the same low-level failure family:

```text
SPI NAND -> FSP/QSPI -> BDMA/cache/completion -> MTD -> UBI/ubiblock -> SquashFS -> libmsc read
```

The practical interpretation is:

1. `libmsc.so warmup read failed errno=5` is the application-visible symptom. It means the `/customer` SquashFS read path returned `-EIO` while reading a large library during wakeup startup.
2. `wait bdma done timeout` is a lower-level controller signal. In the observed cycles it is immediately followed by `ubi_io_read error -5`, so it directly proves at least one failure mode in QSPI BDMA completion.
3. `CamOsTsemUp` with LR at `hal_bdma_interrupt` indicates a BDMA interrupt/completion lifecycle problem, such as late interrupt, duplicate completion, or callback/semaphore state already invalid when the IRQ arrives.
4. These three markers are not required to appear together. Any one of them is enough to keep FSP/QSPI/BDMA in the primary suspect set.

### 2026-06-22 log evidence

The log contains several independent reboot cycles:

- `wait bdma done timeout` appears in cycles where it is directly followed by `ubi_io_read error -5`.
- `CamOsTsemUp` / `hal_bdma_interrupt` appears in other cycles, including one cycle immediately after `SQUASHFS_FLASH_DIAG` / `UBIBLOCK_DIAG_VERIFY`.
- `libmsc.so warmup read failed ... errno=5 offset=786432 expected=3187400` appears in a different cycle that also contains SquashFS and ubiblock diagnostics.

The strongest `libmsc.so` cycle evidence is:

```text
SQUASHFS_FLASH_DIAG: read_fail index=0x30852f9 length=55366 compressed=1 res=-5
UBIBLOCK_DIAG_VERIFY: sector_range=99369-99478 latest_seq=293 candidates=2
UBIBLOCK_DIAG_VERIFY: seq=293 ubi_leb_read ret1=0 ret2=0 ... crc_match=0
UBIBLOCK_DIAG_VERIFY: seq=293 ubi_io_read  ret1=0 ret2=0 ... crc_match=0
UBIBLOCK_DIAG_VERIFY: seq=293 mtd_read     ret1=0 read1=57344 ret2=0 read2=57344 ... crc_match=0
UBIBLOCK_DIAG_VERIFY: seq=293 mtd_ecc valid=1 before(c=0 f=0 b=0 bbt=0) after1(c=0 f=0 b=0 bbt=0) after2(c=0 f=0 b=0 bbt=0)
SQUASHFS_FLASH_DIAG: retry_result ... retry_read_res=0 ... crc_match=0
libmsc.so warmup read failed: /customer/lib/libmsc.so errno=5 offset=786432 expected=3187400
```

This is currently stronger than an application-layer explanation:

```text
SquashFS read failed
  -> ubiblock matched the failing sector range
  -> UBI/MTD repeated reads returned ret=0 and full byte counts
  -> repeated-read CRCs did not match
  -> ECC counters did not change
  -> application saw errno=5 while reading libmsc.so
```

Therefore `libmsc.so` remains a high-value trigger and observation point, not a proven root cause.

### Current code-side repair under validation

The current uncommitted BSP repair direction is to make BDMA timeout and late IRQ handling explicit instead of leaving a pending/late completion in the system:

- `drivers/sstar/bdma/iford/hal_bdma.c`
  - Add a helper to clear pending BDMA interrupt state while holding the channel lock.
  - Harden `hal_bdma_interrupt()` against inactive/free/null callback state.
  - Clear callback state before invoking completion.
  - Add `hal_bdma_cancel_transfer(u8 channel)`.
- `drivers/sstar/bdma/iford/hal_bdma.h`
  - Export `hal_bdma_cancel_transfer()`.
- `drivers/sstar/flash/os/drv_flash_os_impl.c`
  - Add `flash_impl_bdma_cancel_transfer()` wrapper.
- `drivers/sstar/flash/os/drv_flash_os_impl.h`
  - Export the wrapper.
- `drivers/sstar/fsp_qspi/hal/iford/hal_fsp_qspi.c`
  - On BDMA wait timeout, cancel the FSP/QSPI BDMA channel before returning error.

Host validation completed for this patch set:

```text
rtk git diff --check -- SourceCode/kernel/drivers/sstar/bdma/iford/hal_bdma.c SourceCode/kernel/drivers/sstar/bdma/iford/hal_bdma.h SourceCode/kernel/drivers/sstar/flash/os/drv_flash_os_impl.c SourceCode/kernel/drivers/sstar/flash/os/drv_flash_os_impl.h SourceCode/kernel/drivers/sstar/fsp_qspi/hal/iford/hal_fsp_qspi.c
rtk ./build.sh kernel --allow-dirty --no-sync-sources --no-clean --jobs 8
```

Both checks passed and `uImage` was generated. Board-side aging validation is still pending, so this must not be treated as a proven fix yet.

### Next aging判据

After flashing the kernel with BDMA timeout cancel / late IRQ hardening, classify results as follows:

1. `CamOsTsemUp` disappears but `libmsc.so errno=5` remains:
   - The patch likely fixed a secondary BDMA IRQ lifecycle crash.
   - Continue investigating data consistency in FSP/QSPI/BDMA/cache or force RIU/PIO A/B.
2. `wait bdma done timeout` disappears and `libmsc.so errno=5` disappears:
   - BDMA timeout/completion is likely one main trigger.
   - Continue longer aging before claiming closure.
3. `libmsc.so errno=5` remains without `wait bdma done timeout` or `CamOsTsemUp`:
   - The data inconsistency is not only a timeout/late-IRQ issue.
   - Next controlled A/B should be BDMA off / RIU or PIO read path, and SPI LCD/MSPI interference isolation.
4. `wait bdma done timeout` remains but no Oops appears:
   - Cancel/guard fixed late IRQ crash behavior, but underlying FSP/QSPI/BDMA timeout remains.
   - Continue down into FSP wait condition, BDMA interrupt routing, and controller busy/done status.

### Current working-tree caution

The main repo currently contains both useful diagnostic/repair changes and generated or unrelated build noise. Before committing, separate at least:

- Source repair/diagnostic files in `SourceCode/kernel/drivers/mtd/ubi/`, `SourceCode/kernel/fs/squashfs/`, `SourceCode/kernel/drivers/sstar/bdma/`, `SourceCode/kernel/drivers/sstar/flash/`, and `SourceCode/kernel/drivers/sstar/fsp_qspi/`.
- Runtime helper change in `SourceCode/project/pcr02_customer/prog_application.sh`.
- Generated/binary noise such as `SourceCode/boot/include/autoconf.mk.dep`, `SourceCode/kernel/include/generated/bounds.h`, and `libss_mbx.so`.

Do not submit the generated/binary noise as part of the BSP diagnosis patch unless there is a separate reason and validation for it.

## 2026-06-22 debug reboot hang note

`Serial_2026-06-22_14_20_24.log` records an aging interruption where the board stopped rebooting after many successful debug reboot cycles.

Key evidence:

```text
debug reboot now: prog_daemon pid=916
/ # ls /data/
...
/ # reboot
^Z^C^C
```

Earlier cycles in the same log show the normal path:

```text
debug reboot now: prog_daemon pid=916
Requesting system reboot
SWrst
```

The final failed cycle never prints `Requesting system reboot`, so it did not reach the kernel restart path. The aging launcher used `sync; reboot` after printing `debug reboot now`. The most likely failure mode is that `sync` or BusyBox `reboot`'s internal sync path blocked before calling the reboot syscall. No `SQUASHFS`, `wait bdma done timeout`, kernel Oops, or UBIFS assertion was captured around the final hang, so this log does not prove a new flash-read root cause.

Mitigation applied in `SourceCode/project/pcr02_customer/prog_application.sh` for the debug-only `/data/debug_reboot_after` path:

- remove the explicit `sync` before scheduled reboot;
- use `reboot -f`;
- if `reboot -f` returns, fall back to `echo b > /proc/sysrq-trigger`.

This change is only for aging-loop robustness. It should not be treated as a production shutdown policy.

## 2026-06-23 aging positive result

Status: positive aging progress, not yet final root-cause closure.

Source:

- Board-side aging feedback on 2026-06-23.
- Current PCR02 software baseline in `~/pcr02_ssc305_compile`.
- Aging trigger: `touch /data/debug_reboot_after`.

### Test condition

The current version was tested on four devices for about 12 hours with the debug auto-reboot flag enabled:

```sh
touch /data/debug_reboot_after
```

The debug reboot path currently uses `reboot -f` and falls back to SysRq reboot if needed. It does not perform the earlier explicit `sync` before scheduled reboot.

Assuming the default scheduled reboot delay is about 60 seconds, this run represents roughly:

```text
4 devices * 12 hours * about 60 reboot cycles/hour ~= 2880 reboot cycles
```

### Observed result

No recurrence was reported during this 4-device 12-hour run for:

- `libmsc.so warmup read failed`
- `killed by signal 7`
- signal-7-like App crash around wakeup startup

This is materially better than the earlier aging result where the issue reproduced frequently, including the 84-hour run with dozens of daemon fault events and the later runs that still produced `errno=5`.

### Current interpretation

The current combined software baseline is now the best candidate stabilization set:

```text
SoC SPI0 CK 2mA + IO 4mA
MX35LF4GE4AD max_clk = 54 MHz
CONFIG_HIGHMEM = off
CMA = 4M
BDMA wait return propagation
BDMA timeout cancel
BDMA late interrupt/callback hardening
mtd_spinand oops/shutdown bounded flash-lock wait
debug reboot-after path = reboot -f, without explicit sync
```

The 12-hour result strongly suggests the current set reduces the probability of the flash-read/wakeup crash family. It does not yet prove the low-level root cause is fully eliminated, because the historical issue was low-probability and reboot-cycle sensitive.

### Current guidance

Do not add new flash-path changes while this candidate is under aging validation. In particular:

- Do not restore UBI/SquashFS high-noise diagnostics as default behavior.
- Do not change SPI0 pad-drive settings again during this validation window.
- Do not revert the debug reboot path to `sync; reboot` for aging.
- Do not sync unrelated Iford_IMSSV05C13 SDK differences into the flash path without a new failure signal.

### Next acceptance checkpoints

Use the current image and the same aging trigger for staged confirmation:

1. Continue the same 4-device run to 24 hours.
2. If still clean, extend to 48 hours.
3. If resources allow, keep at least one or two devices running to 72 hours.

Classify the next result as follows:

- 24/48/72 hours all clean:
  - Treat the current baseline as the effective stabilization candidate.
  - Keep the root cause wording conservative: probability-reduction / stabilization, not a fully proven silicon-level root cause.
- A rare single recurrence appears after many cycles:
  - Keep the current baseline; compare recurrence rate against earlier high-frequency failures.
  - Re-enable only bounded evidence capture for FSP/QSPI/BDMA/MTD counters, not broad UBI/SquashFS CRC retry diagnostics.
- `wait bdma done timeout` or `CamOsTsemUp` reappears:
  - Continue from the FSP/QSPI/BDMA completion-state branch.
- `libmsc.so warmup read failed` reappears without BDMA/Oops markers:
  - Prioritize low-noise read-path counters and BDMA-vs-RIU/PIO A/B, while preserving the current drive and reboot baseline.
