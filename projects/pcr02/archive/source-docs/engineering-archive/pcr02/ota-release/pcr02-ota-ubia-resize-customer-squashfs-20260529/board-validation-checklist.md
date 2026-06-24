# Board Validation Checklist

## Bootargs

```sh
cat /proc/cmdline
```

Must include:

```text
ubi.mtd=ubia,4096
ubi.block=0,3
root=/dev/mtdblock5
mtdparts=nand0:...456m(ubia)
```

## UBI volume type

```sh
cat /sys/class/ubi/ubi0_3/type
cat /sys/class/ubi/ubi0_3/name
cat /sys/class/ubi/ubi0_3/data_bytes 2>/dev/null
```

Expected:

```text
static
customer
```

## Mounts and space

```sh
mount | grep customer
df -h
```

Expected:

```text
/dev/ubiblock0_3 on /customer type squashfs (ro,relatime)
```

## Error scan

```sh
dmesg | grep -E "SQUASHFS|UBI error|ECC|I/O error|bitflip"
```

Expected:

```text
no new SQUASHFS or UBI errors
```

## Full customer read test

```sh
find /customer -type f -exec dd if={} of=/dev/null bs=64k \; 2>/tmp/customer_read.err
cat /tmp/customer_read.err
dmesg | grep -E "SQUASHFS|UBI error|ECC|I/O error|bitflip"
```

Expected:

```text
/tmp/customer_read.err has no read errors
dmesg has no new SQUASHFS or UBI errors
```

## Version

```sh
cat /customer/etc/version.ini
```

Expected version should match the release being validated.
