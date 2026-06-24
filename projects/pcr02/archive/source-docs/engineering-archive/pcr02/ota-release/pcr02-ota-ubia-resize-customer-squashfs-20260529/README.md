# PCR02 OTA ubia resize and customer SquashFS migration

## Source

- Project: `~/pcr02_ssc305_compile`
- Date: 2026-05-29
- Profile: `ap6303bh_512m_v20`
- Product: `pcr02`
- Target version: `1.1.14`

## Goal

Validate and implement an OTA path that can change UBI volume sizes inside the `ubia` MTD partition and migrate `/customer` from UBIFS to SquashFS.

## Final Result

- `ubia` full rebuild OTA works when the package includes `rootfs.sqfs` and `ubia.bin`.
- `/customer` is mounted as SquashFS through `ubiblock`.
- `/customer` UBI volume must be `static`.
- UBIFS volumes remain `dynamic`.
- The migration package rewrites the whole `ubia` partition, so `/data` is not preserved.

## Final Runtime Layout

```text
rootfs:    /dev/mtdblock5 squashfs ro
factory:   ubi0:factory UBIFS
miservice: ubi0:miservice UBIFS mounted at /config
ota:       ubi0:ota UBIFS
customer:  /dev/ubiblock0_3 SquashFS ro
data:      ubi0:data UBIFS
```

Observed after successful migration:

```text
/ota       84.0M
/customer 46.0M squashfs ro
/data      123.7M
```

## Key Decisions

- First migration from old production layout must use `--ota-partitions rootfs,ubia`.
- Follow-up customer updates can use `--ota-partitions customer` only after the device has completed migration.
- UBI-hosted SquashFS volumes must use `vol_type=static`.
- UBI-hosted UBIFS volumes should keep `vol_type=dynamic`.
- `/customer` debugging should use `/data` bind mounts, not direct writes.

## Files in This Archive

- `decision-customer-squashfs-static-volume.md`
- `failure-analysis.md`
- `verified-layout.md`
- `release-guide.md`
- `debug-customer-readonly.md`
- `artifact-manifest.md`
- `board-validation-checklist.md`
- `artifacts/SHA256SUMS.txt`
