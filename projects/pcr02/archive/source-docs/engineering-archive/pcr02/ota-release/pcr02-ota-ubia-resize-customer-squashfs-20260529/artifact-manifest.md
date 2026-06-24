# Artifact Manifest

## Current Local Artifacts

These paths are the local build outputs at the time this archive was created. NAS should remain the source of truth for formal release packages.

## Vehicle OTA package

```text
path: ~/pcr02_ssc305_compile/SourceCode/project/image/output/vehicle_ota_soc_only_v1.1.14.tar.gz
size: 66791684 bytes
md5: 0db977a1255c7dc37d5689511d35084d
sha256: 23d5725d19a4b4fd772a293b2679f12f9dbccab59320a9333ca925159e98b739
```

## Inner SOC OTA

```text
path: ~/pcr02_ssc305_compile/SourceCode/project/image/output/images/SStarOta.bin.gz
size: 66798337 bytes
md5: a450099b88eda77fac52ac6d5b5f21b3
sha256: 06de027dd227207f99ac38f87f9040bf5a16e74da1c17cc2ff3d476e6d5b7ada
crc32 in guide.toml: 766483cc
```

## Customer SquashFS

```text
path: ~/pcr02_ssc305_compile/SourceCode/project/image/output/images/customer.sqfs
size: 48218112 bytes
sha256: a3faae5481d72a2bd1c030fbddc2ad7914237cba434058211a25b3174b7496a7
```

## ubia image

```text
path: ~/pcr02_ssc305_compile/SourceCode/project/image/output/images/ubia.bin
size: 80216064 bytes
sha256: 1f07d1a1a02e87379f541aab9f4dc6985b054fa6815dd642b77027a9f949a75a
```

## Layout

```text
path: ~/pcr02_ssc305_compile/SourceCode/project/image/output/images/SStarOtaLayout.txt
sha256: a4bbbe255eeeff93b90866464d4d467dc4c4eee07e709b85b4eecd78216fdfac
```

Content:

```text
0,kernel_otaenv.sh,kernel_otaenv.sh,0x1
1,rootfs.sqfs,/dev/mtd5,0x1
2,ubia.bin,/dev/mtd8,0x1
```

## Ubinize config

```text
path: ~/pcr02_ssc305_compile/SourceCode/project/image/output/images/ubinizea.cfg
sha256: 4f7bb85b38650a46de718b6d3de26c0287cf9f58258081d34f9066ae6feb789b
```

Customer section:

```text
[customer]
mode=ubi
image=~/pcr02_ssc305_compile/SourceCode/project/image/output/images/customer.sqfs
vol_id=3
vol_size=0x7000000
vol_type=static
vol_name=customer
vol_alignment=1
```
