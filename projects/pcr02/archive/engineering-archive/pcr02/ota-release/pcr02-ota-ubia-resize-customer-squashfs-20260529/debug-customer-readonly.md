# Debugging read-only customer

## Background

After migration, `/customer` is read-only:

```text
/dev/ubiblock0_3 on /customer type squashfs (ro,relatime)
```

Direct modification is not possible:

```sh
cp file /customer/...
vi /customer/...
rm /customer/...
```

## Directory Overlay Debugging

Use `/data` as a writable debug copy:

```sh
mkdir -p /data/customer_debug
cp -a /customer/. /data/customer_debug/
sync
```

Replace files:

```sh
cp -f /var/run/media/mmcblk0p1/prog_pcr02 /data/customer_debug/bin/prog_pcr02
chmod 755 /data/customer_debug/bin/prog_pcr02
sync
```

Stop application and bind mount:

```sh
killall prog_daemon
killall prog_pcr02
mount -o bind /data/customer_debug /customer
```

Recover original `/customer`:

```sh
killall prog_daemon
killall prog_pcr02
umount /customer
```

Reboot also restores the original SquashFS view.

## Single-file Replacement

For an existing file:

```sh
mkdir -p /data/customer_patch/bin
cp -f /var/run/media/mmcblk0p1/prog_pcr02 /data/customer_patch/bin/prog_pcr02
chmod 755 /data/customer_patch/bin/prog_pcr02
sync

killall prog_daemon
killall prog_pcr02
mount -o bind /data/customer_patch/bin/prog_pcr02 /customer/bin/prog_pcr02
```

Recover:

```sh
umount /customer/bin/prog_pcr02
```

The target file must already exist in SquashFS. For new files, use a directory bind mount.

## Finalizing Debug Changes

Debug overlays are temporary. To ship a change, rebuild and publish a `customer` OTA:

```bash
rtk bash ./build.sh release \
  --profile ap6303bh_512m_v20 \
  --ota-partitions customer \
  --vehicle-ota-version 1.1.15 \
  --publish-soc \
  --soc-release-root /mnt/mcu-release-nas/robot/soc \
  --soc-release-stage DVT \
  --soc-product pcr02
```

