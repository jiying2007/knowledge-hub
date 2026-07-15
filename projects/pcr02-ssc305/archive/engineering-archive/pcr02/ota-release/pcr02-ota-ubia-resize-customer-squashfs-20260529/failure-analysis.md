# Failure Analysis

## Failure 1: changing inner UBI volumes only was insufficient

The early attempt only changed `/ota`, `/customer`, and `/data` volume sizing. Upgrade failed because the target boot/runtime pieces were not updated consistently with the new UBI layout and `/customer` filesystem type.

Conclusion:

```text
Old production migration requires rootfs + ubia together.
```

## Failure 2: customer changed to SquashFS but rootfs still mounted UBIFS

Observed symptom:

```text
mount: mounting ubi0:customer on /customer failed: Invalid argument
```

Root cause:

```text
customer volume content was SquashFS, but old rootfs still tried:
mount -t ubifs ubi0:customer /customer
```

Fix:

```text
Rebuild rootfs and mount:
mount -t squashfs -o ro /dev/ubiblock0_3 /customer
```

## Failure 3: bootargs update erased mtdparts

Observed symptom:

```text
Kernel command line: ... mtdparts= nohz=off
mtd: no mtd-id
UBI error: cannot open mtd ubia, error -2
VFS: Cannot open root device "mtdblock5"
```

Root cause:

`kernel_otaenv.sh` wrote U-Boot-style variable text from `set_config` directly:

```sh
/etc/fw_setenv bootargs ... mtdparts=${mtdparts} ...
```

That script runs under Linux shell, so `${mtdparts}` expanded to an empty string.

Fix:

Generate `kernel_otaenv.sh` to read current `/proc/cmdline`, preserve the already-expanded `mtdparts=nand0:...`, remove any old `ubi.block`, and inject `ubi.block=0,3`.

Final script behavior:

```sh
bootargs=$(cat /proc/cmdline 2>/dev/null)
bootargs=$(printf "%s\n" "$bootargs" | sed "s/ ubi.block=[^ ]*//g; s/^ubi.mtd=ubia,[^ ]*/ubi.mtd=ubia,4096 ubi.block=0,3/")
if [ -n "$bootargs" ]; then /etc/fw_setenv bootargs "$bootargs"; fi
```

## Failure 4: customer dynamic volume caused intermittent SquashFS errors

Observed symptoms:

```text
SQUASHFS error: Unable to read page, block 1a88584, size 10b24
SQUASHFS error: Unable to read fragment cache entry [1a88584]
SQUASHFS error: xz decompression failed, data probably corrupt
Process App killed by signal 7
Process App killed by signal 11
```

Root cause direction:

`customer.sqfs` was stored in a dynamic UBI volume:

```text
vol_type=dynamic
```

This is not the appropriate UBI semantic for a read-only SquashFS image exposed through `ubiblock`.

Fix:

```text
customer vol_type=static
```

Validation observation:

After changing to static, the issue was not reproduced during temporary repeated reboot testing, and no new SquashFS or UBIFS abnormality was observed.

