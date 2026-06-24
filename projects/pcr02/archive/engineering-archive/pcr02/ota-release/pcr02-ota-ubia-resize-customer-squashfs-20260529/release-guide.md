# Release Guide

## First Migration Release

Use this for old production devices that have not yet migrated to:

```text
customer SquashFS
ubiblock0_3
resized ota/customer/data UBI volumes
```

Command:

```bash
cd /vsdata/leiwenjun/pcr02_ssc305_compile

rtk bash ./build.sh release \
  --profile ap6303bh_512m_v20 \
  --ota-partitions rootfs,ubia \
  --vehicle-ota-version 1.1.14 \
  --publish-soc \
  --soc-release-root /mnt/mcu-release-nas/robot/soc \
  --soc-release-stage DVT_MIGRATION \
  --soc-product pcr02
```

Expected SOC OTA layout:

```text
0,kernel_otaenv.sh,kernel_otaenv.sh,0x1
1,rootfs.sqfs,/dev/mtd5,0x1
2,ubia.bin,/dev/mtd8,0x1
```

Important:

- This rewrites the whole `ubia` partition.
- `/data` is not preserved.
- Do not use `customer,miservice` for old production first migration.

## Follow-up Customer-only Release

Use this only after the device has completed migration.

```bash
cd /vsdata/leiwenjun/pcr02_ssc305_compile

rtk bash ./build.sh release \
  --profile ap6303bh_512m_v20 \
  --ota-partitions customer \
  --vehicle-ota-version 1.1.15 \
  --publish-soc \
  --soc-release-root /mnt/mcu-release-nas/robot/soc \
  --soc-release-stage DVT \
  --soc-product pcr02
```

Expected behavior:

```text
customer.sqfs -> /dev/ubi0_3
no full ubia rewrite
no /data wipe
```

## Follow-up Customer + Miservice Release

Use this if both `/customer` and `/config` content changed:

```bash
cd /vsdata/leiwenjun/pcr02_ssc305_compile

rtk bash ./build.sh release \
  --profile ap6303bh_512m_v20 \
  --ota-partitions customer,miservice \
  --vehicle-ota-version 1.1.15 \
  --publish-soc \
  --soc-release-root /mnt/mcu-release-nas/robot/soc \
  --soc-release-stage DVT \
  --soc-product pcr02
```

## Rootfs or Kernel Follow-up Release

Use this if rootfs startup scripts, kernel, or system mount logic changed:

```bash
cd /vsdata/leiwenjun/pcr02_ssc305_compile

rtk bash ./build.sh release \
  --profile ap6303bh_512m_v20 \
  --ota-partitions kernel,rootfs,customer,miservice \
  --vehicle-ota-version 1.1.15 \
  --publish-soc \
  --soc-release-root /mnt/mcu-release-nas/robot/soc \
  --soc-release-stage DVT \
  --soc-product pcr02
```

## Release Rules

Do not use these for normal upgrades unless intentionally rebuilding the whole UBI container:

```text
--ota-partitions ubia
--ota-partitions rootfs,ubia
--ota-partitions all
--include-data
```

Formal publish should avoid:

```text
--allow-dirty
--no-source-check
--force-publish-soc
```

