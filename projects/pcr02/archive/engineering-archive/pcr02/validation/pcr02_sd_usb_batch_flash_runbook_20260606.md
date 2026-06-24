# PCR02 SD, USB, And Serial Batch Flash Runbook

Date: 2026-06-06
Status: operational runbook

## Background

PCR02 field validation uses several flashing paths: SD card upgrade, OTA upgrade, serial/U-Boot assisted boot interruption, and PC-side batch burning. The useful conclusion is not a specific transient command log, but the decision tree and verification evidence required after flashing.

## Supported Scenarios

Blank or nearly blank board:

- Use SD upgrade or PC-side low-level burning flow.
- Confirm IPL/IPL_CUST/UBOOT and upgrade payload are present.
- Capture serial boot log through U-Boot, kernel, mount, and app start.

Running application board:

- Prefer OTA or controlled reboot into upgrade path.
- If using SD card, ensure the board actually enters the second-stage OTA/application recovery flow.
- Removing the SD card before the intended second-stage flow can leave misleading residual status files and should not be treated as OTA root cause.

Debug or recovery board:

- Use serial console to stop autoboot when required.
- Keep exact bootargs and partition table in the validation record.
- Do not overwrite factory/data unless the runbook explicitly says the test is destructive.

## SD Upgrade Package Expectations

The SD upgrade directory should contain the board-required boot and payload files, typically including:

- `IPL`
- `IPL_CUST`
- `UBOOT`
- `SigmastarUpgradeSD.bin`
- SoC package or SD upgrade tarball required by the current release flow

The exact file set must be derived from the active board/profile image config, not copied from an older USB/SD script blindly.

## Batch Flash Evidence

For each device or representative sample, record:

- Board identifier or anonymized sample id.
- Build profile and release flow: `migration` or `regular`.
- Package path, size, and sha256.
- Serial log snippets for partition table, rootfs mount, UBI attach, `/customer` mount, and app start.
- Post-boot `mount` output.
- `/customer/etc/version.ini`.
- `sha256sum /dev/ubi0_3` and `/dev/ubiblock0_3` when validating customer SquashFS read stability.
- OTA status files under `/ota` when validating OTA behavior.

## Failure Classification

- Bootloader failure: no U-Boot or wrong board/profile boot image.
- Kernel/rootfs failure: cannot mount `/dev/mtdblock5` rootfs or rootfs checksum/read errors.
- UBI layout failure: missing expected UBI volumes or wrong volume types.
- Customer read failure: SquashFS decompression error or inconsistent `ubi0_3`/`ubiblock0_3` hash.
- OTA workflow failure: package preflight, duplicate detection, parent-process shutdown, phase/status persistence, or reboot handling.
- Runtime app failure: app crash after filesystems mounted correctly.

## Safety Rules

- Do not archive full serial logs by default.
- Do not archive Wi-Fi passwords, NAS credentials, tokens, or customer identity data.
- Do not classify a manually interrupted SD/OTA flow as an OTA package bug without reproducing the complete flow.
- Separate production flashing from debug flashing; debug overlay and core-dump flags must not leak into production release evidence.

## Provenance

- Current session archive audit on 2026-06-06.
- Prior PCR02 SD upgrade, OTA migration, manual SD-card removal, and board validation discussions.
- Existing archive: `validation/pcr02_device_validation_commands_20260528.md` and migration release checklist notes.

## Follow-up

- Convert this runbook into a machine-checkable validation script only after the board mode detection and destructive/non-destructive boundaries are explicit.
