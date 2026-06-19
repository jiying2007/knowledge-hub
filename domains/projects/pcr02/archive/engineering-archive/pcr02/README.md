# PCR02 Archive Index

This index groups PCR02 archive material by engineering topic. Existing historical notes keep their original filenames; complex workstreams use a topic directory with a local `README.md`.

## Current Decision Index

- [PCR02 archive decision index](decision-index.md)

Current effective release/storage decision:

```text
/customer = SquashFS on /dev/ubiblock0_3, mounted read-only
customer UBI volume type = static
debug /customer = SquashFS lower + /data/customer_overlay persistent overlay upper
first old-production migration OTA = rootfs,ubia
follow-up customer update after migration = customer-only is allowed
vehicle OTA = consume pinned SoC + mainboard MCU + motor MCU artifacts, with manifest/hash coverage
regular SoC OTA = preserve /factory, /ota, and /data by default
SPI-NAND current pad-drive baseline = SoC SPI0 CK 2mA + IO 4mA + MX35LF4GE4AD max_clk=54
```

Older UBIFS-focused notes remain preserved as historical analysis. When they conflict with the 2026-05-29 migration archive, prefer the migration archive and `decision-index.md`.
The 2026-06-06 flash-read note records a later risk correction: SquashFS/static-volume reduces the writable filesystem risk but does not by itself prove the low-level SPI-NAND read path is healthy.
The 2026-06-15 update clarifies that Flash-side `E0h=80h` / 85ohm is historical experiment only; it is not the current PCR02 default baseline.
The 2026-06-18 pad-drive update records that six-line 4mA improved but did not eliminate flash-read failures; the current software baseline is CK 2mA with IO 4mA.

## OTA and Release

- [PCR02 SDK OTA 与发布策略归档](ota-release/pcr02_sdk_ota_release_design_20260528.md)
- [PCR02 OTA ubia resize and customer SquashFS migration](ota-release/pcr02-ota-ubia-resize-customer-squashfs-20260529/README.md)
- [PCR02 Vehicle OTA orchestration](ota-release/pcr02_vehicle_ota_orchestration_20260606.md)
- [PCR02 regular OTA preserve partitions](ota-release/pcr02_regular_ota_preserve_partitions_20260613.md)

Use this topic for OTA packaging, vehicle OTA, SOC release to NAS, migration packages, release gates, and post-release artifact manifests.

## Partition and Storage Policy

- [PCR02 SDK MX35 512MiB 分区规划归档](partition-storage/pcr02_sdk_partition_plan_mx35_512m_20260528.md)
- [PCR02 SDK rootfs/customer/data 放置策略归档](partition-storage/pcr02_sdk_rootfs_customer_data_policy_20260528.md)
- [PCR02 rootfs/customer/data symlink policy](partition-storage/pcr02_rootfs_customer_data_symlink_policy_20260606.md)
- [PCR02 rootfs mtdblock and upgrade residue risks](partition-storage/pcr02_rootfs_mtdblock_upgrade_residue_risks_20260606.md)

Use this topic for flash layout, UBI volume sizing, rootfs/customer/data responsibilities, and capacity planning.

## UBIFS and SquashFS

- [PCR02 UBIFS 与运行库问题排查归档](ubifs-squashfs/pcr02_ubifs_troubleshooting_20260528.md)
- [PCR02 AI 语音助手与 UBIFS 触发链归档](ubifs-squashfs/pcr02_ai_voice_ubifs_trigger_chain_20260529.md)
- [PCR02 刷机后首次 UBIFS Fixup 验证规程](ubifs-squashfs/pcr02_factory_first_boot_fixup_protocol_20260529.md)
- [PCR02 customer SquashFS、调试 overlay 与 Flash 读异常归档](ubifs-squashfs/pcr02_customer_squashfs_overlay_flash_read_20260606.md)
- [PCR02 customer SquashFS libmsc errno=5 与 wakeup 触发链排障进度](ubifs-squashfs/pcr02_customer_squashfs_libmsc_errno5_20260617.md)

Use this topic for UBIFS recovery/fixup, SquashFS read-only migration, filesystem mount errors, and filesystem failure analysis.

## Boot and Flash

- [PCR02 MX35 SNI/CIS 配置核查归档](boot-flash/pcr02_mx35_sni_cis_audit_20260529.md)
- [PCR02 SPI-NAND 读路径 BDMA/RIU 排查归档](boot-flash/pcr02_spinand_read_path_bdma_riu_20260529.md)
- [PCR02 SPI0 pad drive RIU verification](boot-flash/pcr02_spi0_pad_drive_8ma_riu_verification_20260618.md)
- [PCR02 SPI-NAND flash read aging progress](boot-flash/pcr02_spinand_flash_read_aging_progress_20260618.md)

Use this topic for boot chain, SNI/CIS, SPI-NAND geometry, read-path diagnostics, and low-level flash behavior.

## Hardware Power

- [PCR02 power hold and shutdown path notes](hardware-power/pcr02_power_hold_shutdown_path_20260606.md)

Use this topic for power-hold GPIO contracts, shutdown sequencing, reset timing, low-battery reboot behavior, and hardware-verification notes.

## Runtime I/O

- [PCR02 运行期 I/O 压力收敛优化归档](runtime-io/pcr02_runtime_io_pressure_mitigation_20260529.md)
- [PCR02 GD32L235 UART watchdog and nonblocking runtime notes](runtime-io/pcr02_gd32l235_uart_watchdog_nonblocking_20260612.md)

Use this topic for runtime write pressure, logging paths, tmpfs migration, and I/O mitigation.

## Validation

- [PCR02 设备侧验证命令手册](validation/pcr02_device_validation_commands_20260528.md)
- [PCR02 IMSSV05C13 host validation](validation/pcr02_imssv05c13_host_validation_20260530.md)
- [PCR02 SD, USB, and serial batch flash runbook](validation/pcr02_sd_usb_batch_flash_runbook_20260606.md)

Use this topic for board-side command checklists and repeated validation recipes.

## Session Wraps

- [PCR02 IMSSV05C13 SDK migration session wrap](session/pcr02_imssv05c13_migration_session_wrap_20260601.md)
- [PCR02 IMSSV05C13 memory candidates](session/pcr02_imssv05c13_memory_candidates_20260601.md)

Use this topic for handoff notes, current-session conclusions, memory candidates, and acceptance blockers that should not be mixed into stable release decisions yet.

## Source Audit

- [PCR02 SSC305 三套源码对比归档](source-audit/pcr02_source_compare_ubifs_20260528.md)
- [PCR02 IMSSV05C13 SDK 迁移计划](source-audit/pcr02_imssv05c13_sdk_migration_plan_20260530.md)

Use this topic for source tree comparisons, SDK/app baseline reviews, and historical source audits.

## Migration Map

The archive was structured on 2026-05-29. Historical files were moved from the archive root into these topic directories without content rewrites.

## Drift Governance

The archive uses status notes instead of deleting historical material. Historical notes may describe pre-migration UBIFS behavior, old volume sizes, or earlier root-cause hypotheses; the current decision index records which conclusions are still effective.
