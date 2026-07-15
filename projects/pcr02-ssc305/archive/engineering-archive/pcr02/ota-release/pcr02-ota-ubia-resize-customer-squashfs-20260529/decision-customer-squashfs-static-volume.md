# Decision: customer SquashFS uses static UBI volume

## Decision

`/customer` is stored as `customer.sqfs` inside UBI volume `ubi0_3`, exposed through `ubiblock0_3`, and mounted read-only as SquashFS.

The `customer` UBI volume must be generated as:

```text
[customer]
mode=ubi
image=.../customer.sqfs
vol_id=3
vol_size=0x7000000
vol_type=static
vol_name=customer
vol_alignment=1
```

Other UBI volumes remain dynamic:

```text
factory   dynamic UBIFS
miservice dynamic UBIFS
ota       dynamic UBIFS
data      dynamic UBIFS
```

## Rationale

SquashFS is a compressed, read-only block filesystem. It expects stable block-device semantics. When it is accessed through `ubiblock`, the underlying UBI volume should be static so UBI records the image size and read-only image integrity semantics.

Using a dynamic UBI volume for `customer.sqfs` was observed to produce intermittent SquashFS read/decompression failures:

```text
SQUASHFS error: Unable to read page, block 1a88584, size 10b24
SQUASHFS error: Unable to read fragment cache entry [1a88584]
SQUASHFS error: xz decompression failed, data probably corrupt
```

After changing `customer` to `vol_type=static`, repeated reboot testing temporarily did not reproduce `SQUASHFS error`, and no UBIFS abnormality was observed.

## Implications

- `/customer` cannot be modified in place.
- Debugging must use `/data` overlays or bind mounts.
- Customer OTA must update the whole SquashFS image, not individual files in the UBI volume.
- Static volume type must be part of the release gate.

## Release Gate

On the target:

```sh
cat /sys/class/ubi/ubi0_3/type
cat /sys/class/ubi/ubi0_3/name
mount | grep customer
dmesg | grep -E "SQUASHFS|UBI error|ECC|I/O error|bitflip"
```

Expected:

```text
static
customer
/dev/ubiblock0_3 on /customer type squashfs (ro,...)
no new SQUASHFS or UBI errors
```

