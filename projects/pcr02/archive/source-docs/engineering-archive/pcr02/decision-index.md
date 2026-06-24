# PCR02 Archive Decision Index

Date: 2026-05-29
Updated: 2026-06-23

This index records the currently effective PCR02 archive decisions and the status of historical notes. It is intended to prevent older investigation notes from being read as the latest release guidance.

## Current Effective Decisions

| Area | Current decision | Source |
| --- | --- | --- |
| `/customer` filesystem | SquashFS mounted read-only via `/dev/ubiblock0_3` | [OTA ubia resize and customer SquashFS migration](ota-release/pcr02-ota-ubia-resize-customer-squashfs-20260529/README.md) |
| `/customer` UBI volume type | `static` | [customer static-volume decision](ota-release/pcr02-ota-ubia-resize-customer-squashfs-20260529/decision-customer-squashfs-static-volume.md) |
| UBIFS volumes | Keep `factory`, `miservice`, `ota`, and `data` as `dynamic` | [verified layout](ota-release/pcr02-ota-ubia-resize-customer-squashfs-20260529/verified-layout.md) |
| First migration from old production layout | Use OTA package containing `rootfs.sqfs` and `ubia.bin`; publish/run as `rootfs,ubia` | [release guide](ota-release/pcr02-ota-ubia-resize-customer-squashfs-20260529/release-guide.md) |
| Follow-up `/customer` update after migration | May update `customer` without upgrading `data` | [release guide](ota-release/pcr02-ota-ubia-resize-customer-squashfs-20260529/release-guide.md) |
| `/data` preservation during first migration | Not preserved, because whole `ubia` is rewritten | [migration README](ota-release/pcr02-ota-ubia-resize-customer-squashfs-20260529/README.md) |
| `/customer` debug replacement | Use debug build with SquashFS lower plus persistent `/data/customer_overlay` upper; old debug-customer-UBIFS compatibility is removed | [customer SquashFS, overlay, and flash-read note](ubifs-squashfs/pcr02_customer_squashfs_overlay_flash_read_20260606.md) |
| `/customer` intermittent read corruption | SquashFS/static volume reduces writable filesystem risk but does not prove the SPI-NAND read path is healthy; 24M FSP QSPI downclock still reproduced the issue and should not be retained as a fix; 2026-06-22 evidence correlates `libmsc.so errno=5`, `wait bdma done timeout`, and `CamOsTsemUp` with the FSP/QSPI/BDMA/MTD read-path failure family, not with a fixed `libmsc.so` file corruption; 2026-06-23 four-device 12-hour debug auto-reboot aging on the current CK 2mA / IO 4mA plus BDMA hardening baseline showed no `libmsc.so warmup read failed` or App signal 7 recurrence, so the current baseline is the best stabilization candidate pending 24/48/72-hour confirmation | [SPI-NAND flash read aging progress](boot-flash/pcr02_spinand_flash_read_aging_progress_20260618.md) |
| SPI-NAND current electrical trial baseline | Current PCR02 software baseline is SoC SPI0 CK 2mA and IO 4mA plus `MX35LF4GE4AD.max_clk=54`; six-line 4mA improved but did not eliminate flash-read failures; Flash-side `E0h=80h` / 85ohm is historical experiment only, not the default baseline | [SPI0 pad drive RIU verification](boot-flash/pcr02_spi0_pad_drive_8ma_riu_verification_20260618.md) |
| Vehicle OTA artifact policy | Vehicle OTA consumes pinned SoC OTA, mainboard MCU, and motor MCU artifacts; final packages must carry manifest and sha256 coverage | [vehicle OTA orchestration](ota-release/pcr02_vehicle_ota_orchestration_20260606.md) |
| Regular SoC OTA preservation | After migration, regular SoC OTA must preserve `/factory`, `/ota`, and `/data`; do not rewrite whole `ubia` or include debug-only customer_ro/ubiblock assumptions in production regular packages | [regular OTA preserve partitions](ota-release/pcr02_regular_ota_preserve_partitions_20260613.md) |
| Rootfs/customer/data ownership | Rootfs owns boot and compatibility shims; `/customer` owns versioned defaults; `/data` owns mutable runtime/provisioning/debug overlay state | [rootfs/customer/data symlink policy](partition-storage/pcr02_rootfs_customer_data_symlink_policy_20260606.md) |
| Rootfs raw mtdblock status | `/dev/mtdblock5` SquashFS rootfs is current runtime truth but remains a tracked SPI-NAND/update-chain risk, not a proven root cause | [rootfs mtdblock and upgrade residue risks](partition-storage/pcr02_rootfs_mtdblock_upgrade_residue_risks_20260606.md) |
| SD/USB batch flashing | Use current profile-derived SD/USB package lists and classify failures by bootloader, rootfs, UBI, customer read, OTA workflow, or runtime app layer | [SD, USB, and serial batch flash runbook](validation/pcr02_sd_usb_batch_flash_runbook_20260606.md) |
| Power hold/shutdown path | PA11/SWITCH and PA15/KEEP_ON style paths are hardware-software contracts; software instrumentation is useful but board waveform verification is still pending | [power hold and shutdown path notes](hardware-power/pcr02_power_hold_shutdown_path_20260606.md) |
| GD32L235 UART/watchdog runtime | Mainboard MCU command timeouts can be caused by ACK send loss or main-loop blocking; keep UART TX counters, move protocol processing early, and make battery/CW2217 work nonblocking | [GD32L235 UART watchdog and nonblocking runtime notes](runtime-io/pcr02_gd32l235_uart_watchdog_nonblocking_20260612.md) |
| IMSSV05C13 migration first-round acceptance | Host compile/package validation is not sufficient; first-round acceptance requires real PCR02 EVT2 board boot and real OTA upgrade test | [IMSSV05C13 migration session wrap](session/pcr02_imssv05c13_migration_session_wrap_20260601.md) |
| IMSSV05C13 migration input exclusion | Do not migrate `pcr02_ssc305_compile/SourceCode/project/configs/current.configs.in` unless the user reverses the explicit exclusion | [IMSSV05C13 migration session wrap](session/pcr02_imssv05c13_migration_session_wrap_20260601.md) |

## Current Runtime Truth Table

| Mount point | Current filesystem | Current device/source | Runtime write policy |
| --- | --- | --- | --- |
| `/` | SquashFS | `/dev/mtdblock5` | Read-only |
| `/factory` | UBIFS | `ubi0:factory` | Low-frequency write, device-specific data |
| `/config` | UBIFS | `ubi0:miservice` | Writable system/service config |
| `/ota` | UBIFS | `ubi0:ota` | Writable OTA staging/status |
| `/customer` production | SquashFS | `/dev/ubiblock0_3` | Read-only |
| `/customer` debug | overlayfs | SquashFS lower plus `/data/customer_overlay` upper | Writable for development only |
| `/data` | UBIFS | `ubi0:data` | Writable runtime data/logs/cache |

## Historical Notes Status

| File | Status | Current interpretation |
| --- | --- | --- |
| [partition-storage/pcr02_sdk_partition_plan_mx35_512m_20260528.md](partition-storage/pcr02_sdk_partition_plan_mx35_512m_20260528.md) | Historical baseline | Useful for pre-migration MX35 layout and capacity reasoning; current volume sizes are superseded by the migration archive. |
| [partition-storage/pcr02_sdk_rootfs_customer_data_policy_20260528.md](partition-storage/pcr02_sdk_rootfs_customer_data_policy_20260528.md) | Partially superseded | Rootfs/data responsibility split remains useful; `/customer` as UBIFS is superseded by SquashFS static volume. |
| [partition-storage/pcr02_rootfs_customer_data_symlink_policy_20260606.md](partition-storage/pcr02_rootfs_customer_data_symlink_policy_20260606.md) | Current policy | Use as current placement rule for rootfs symlinks, versioned `/customer` defaults, mutable `/data` state, and debug overlay upperdirs. |
| [partition-storage/pcr02_rootfs_mtdblock_upgrade_residue_risks_20260606.md](partition-storage/pcr02_rootfs_mtdblock_upgrade_residue_risks_20260606.md) | Current risk note | Keep `/dev/mtdblock5` rootfs as runtime truth while tracking raw MTD, old upgrade-script, image-list, and production diagnostic-tool risks. |
| [validation/pcr02_device_validation_commands_20260528.md](validation/pcr02_device_validation_commands_20260528.md) | Needs context | General commands remain useful; `/customer` mount expectation must use SquashFS/ubiblock for migrated devices. |
| [validation/pcr02_sd_usb_batch_flash_runbook_20260606.md](validation/pcr02_sd_usb_batch_flash_runbook_20260606.md) | Current runbook | Use for SD/USB/serial batch flash evidence and failure classification. |
| [source-audit/pcr02_source_compare_ubifs_20260528.md](source-audit/pcr02_source_compare_ubifs_20260528.md) | Historical analysis | Source comparison remains useful; final mitigation moved from UBIFS-only tuning to SquashFS static volume. |
| [ubifs-squashfs/pcr02_ubifs_troubleshooting_20260528.md](ubifs-squashfs/pcr02_ubifs_troubleshooting_20260528.md) | Historical troubleshooting | Retain as investigation chain; not the current release decision. |
| [ubifs-squashfs/pcr02_ai_voice_ubifs_trigger_chain_20260529.md](ubifs-squashfs/pcr02_ai_voice_ubifs_trigger_chain_20260529.md) | Historical trigger analysis | AI voice path remains a useful stress trigger; current mitigation is `/customer` SquashFS static volume. |
| [boot-flash/pcr02_spinand_read_path_bdma_riu_20260529.md](boot-flash/pcr02_spinand_read_path_bdma_riu_20260529.md) | Fallback hypothesis | Keep for low-level read-path investigation if static SquashFS still fails. |
| [ubifs-squashfs/pcr02_customer_squashfs_overlay_flash_read_20260606.md](ubifs-squashfs/pcr02_customer_squashfs_overlay_flash_read_20260606.md) | Current risk correction | Static SquashFS still has low-probability reboot-time read inconsistency; treat SPI-NAND read path, reset/power timing, ECC reporting, UBI/ubiblock mapping, and DMA/cache coherency as active investigation areas. |
| [ota-release/pcr02_vehicle_ota_orchestration_20260606.md](ota-release/pcr02_vehicle_ota_orchestration_20260606.md) | Current release policy | Use for SoC + mainboard MCU + motor MCU package orchestration and manifest/hash gates. |
| [ota-release/pcr02_regular_ota_preserve_partitions_20260613.md](ota-release/pcr02_regular_ota_preserve_partitions_20260613.md) | Current release policy | After migration, regular OTA preserves `/factory`, `/ota`, and `/data`; an OTA package excluding `ota` was reported to upgrade successfully after failures that ended in `WAIT_OTA_END` / `FAILED`. |
| [hardware-power/pcr02_power_hold_shutdown_path_20260606.md](hardware-power/pcr02_power_hold_shutdown_path_20260606.md) | Verification pending | Keep as software-design and hardware-contract note; do not treat as confirmed board-level shutdown proof. |
| [runtime-io/pcr02_gd32l235_uart_watchdog_nonblocking_20260612.md](runtime-io/pcr02_gd32l235_uart_watchdog_nonblocking_20260612.md) | Current troubleshooting guidance | Use for mainboard MCU UART timeout, ACK-loss, watchdog-loop, battery initialization blocking, and 60Hz loop timing diagnostics. |

## Supersession Rule

When PCR02 archive notes disagree, prefer this order:

1. `ota-release/pcr02-ota-ubia-resize-customer-squashfs-20260529/`
2. This `decision-index.md`
3. Topic README files
4. Historical single-file notes from 2026-05-28 and early 2026-05-29

Older notes should not be deleted unless a replacement preserves the evidence and the user explicitly approves deletion.
