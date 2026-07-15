# PCR02 Rootfs MTDBlock And Upgrade Residue Risks

Date: 2026-06-06
Status: current risk note

## Background

The current PCR02 layout still mounts rootfs as read-only SquashFS from raw `/dev/mtdblock5`, while `/customer` moved to a UBI static volume exposed through ubiblock. During archive audit, several residual risks were identified around raw MTD access, old USB/SD scripts, image-list drift, and production content accidentally containing diagnostic/destructive tools.

## Current Facts

- Rootfs is currently mounted as SquashFS from `/dev/mtdblock5`.
- `/customer` production is mounted as SquashFS from `/dev/ubiblock0_3`.
- UBI volumes own `factory`, `miservice`, `ota`, `customer`, and `data`.
- `rootfs` is read-only at runtime, but its raw MTD placement means bad-block abstraction and update semantics differ from UBI/ubiblock volumes.

This is not by itself proof of a current rootfs bug. It is a release-chain and field-reliability risk that must be kept visible.

## Risks

Raw rootfs on SPI-NAND:

- Raw MTD block access is less tolerant of bad-block and ECC edge cases than UBI-managed volumes.
- Rootfs image updates must be checked against eraseblock alignment and actual partition size.
- If rootfs read errors appear, do not assume they have the same root cause as `/customer` ubiblock read errors.

Old USB/SD scripts:

- Legacy scripts can carry old partition names, stale image lists, or old volume sizes.
- Upgrade scripts must derive the active package list from the current profile/image config.
- `OTA_IMAGE_LIST` must exist for every generated partition config used by release profiles.

Wrong filesystem maintenance command:

- `resize2fs` is for ext filesystems and must not be generated for UBIFS, SquashFS, FWFS, or LittleFS paths.
- Filesystem-specific repair/resize commands must be gated by actual filesystem type.

Production customer content:

- Destructive flash tools such as raw erase/write/dump utilities should not ship in production `/customer`.
- Keep diagnostic tools in debug, factory, or production-test packages with explicit release metadata.
- Static `adbd` or `prog_tool-lite` style tools should have a release-kind gate.

## Build And Release Gates

- Check total UBI volume allocation plus reserve does not exceed the raw `ubia` partition.
- Check each image size fits its target volume or partition.
- Check `OTA_IMAGE_LIST`, guide metadata, and package contents agree.
- Check bootargs, DTS, and fallback boot scripts agree on rootfs and UBI layout.
- Check production/debug package manifests clearly state whether debug tools and overlay behavior are included.

## Validation Commands

Useful board-side checks:

```sh
cat /proc/cmdline
cat /proc/mtd
ubinfo -a
mount
sha256sum /dev/ubi0_3 /dev/ubiblock0_3
```

Useful host-side checks:

```sh
./build.sh self-check --allow-dirty
git diff --check
bash -n build.sh
```

Run the host-side commands through `rtk` in this workspace.

## Provenance

- Current session archive audit on 2026-06-06.
- Prior PCR02 migration release, `OTA_IMAGE_LIST` failure, customer SquashFS, rootfs bootargs, and SD/USB script drift discussions.
- Existing archive: `partition-storage/pcr02_sdk_partition_plan_mx35_512m_20260528.md` and `ota-release/pcr02-ota-ubia-resize-customer-squashfs-20260529/verified-layout.md`.

## Follow-up

- If rootfs read instability is observed, evaluate migrating rootfs to a UBI static volume plus ubiblock in a future layout migration.
- Add release checks that reject production packages containing debug-only destructive tools.
