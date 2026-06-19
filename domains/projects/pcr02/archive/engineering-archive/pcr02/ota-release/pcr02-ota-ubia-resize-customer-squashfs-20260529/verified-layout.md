# Verified Layout

## OTA Layout

Migration package layout:

```text
0,kernel_otaenv.sh,kernel_otaenv.sh,0x1
1,rootfs.sqfs,/dev/mtd5,0x1
2,ubia.bin,/dev/mtd8,0x1
```

This layout is required for first migration from old production versions because it updates both:

- rootfs mount logic
- the whole `ubia` container and UBI volume sizing

## Bootargs

Verified successful command line:

```text
ubi.mtd=ubia,4096 ubi.block=0,3 root=/dev/mtdblock5 rootfstype=squashfs ro init=/linuxrc LX_MEM=0x10000000 mma_heap=mma_heap_name0,miu=0,sz=0x6000000 mma_memblock_remove=1 cma=2M mtdparts=nand0:3584k@2560k(BOOT),3584k(BOOT_BAK),512k(ENV),10m(KERNEL),10m(KERNEL_BACKUP),22m(rootfs),2m(MISC),2m(PSTORE),456m(ubia) nohz=off
```

Important fields:

```text
ubi.mtd=ubia,4096
ubi.block=0,3
root=/dev/mtdblock5
mtdparts=nand0:...456m(ubia)
```

## Kernel/MTD/UBI Evidence

Successful boot evidence:

```text
9 cmdlinepart partitions found on MTD device nand0
Creating 9 MTD partitions on "nand0":
0x000000380000-0x000020000000 : "ubia"
ubi0: attached mtd8 (name "ubia", size 456 MiB)
block ubiblock0_3: created from ubi0:3(customer)
VFS: Mounted root (squashfs filesystem) readonly on device 31:5.
```

## Mount Evidence

Expected mount output:

```text
/dev/root on / type squashfs (ro,relatime)
ubi0:factory on /factory type ubifs
ubi0:miservice on /config type ubifs
ubi0:ota on /ota type ubifs
/dev/ubiblock0_3 on /customer type squashfs (ro,relatime)
ubi0:data on /data type ubifs
```

## Space Evidence

Observed after migration:

```text
/ota                 84.0M
/dev/ubiblock0_3     46.0M mounted at /customer
/data               123.7M
```

## UBI Volume Types

Expected:

```text
factory   dynamic
miservice dynamic
ota       dynamic
customer  static
data      dynamic
```

