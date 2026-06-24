# PCR02 IMSSV05C13 host validation evidence

Date: 2026-05-30

Target tree: `/vsdata/leiwenjun/Iford_IMSSV05C13`

Product profile: `ap6303bh_512m_v20`

Hardware target for first-round acceptance: PCR02 EVT2

## Scope

This note records host-side migration validation for the IMSSV05C13 SDK port. It is not board evidence.

First-round acceptance is still blocked until PCR02 EVT2 real board boot and real OTA upgrade are executed and archived.

## Source state

- Main SDK commit during latest validation: `4f49e49e2e011b4f106b702921594bcc873b5ce5`
- App repository: `SourceCode/sdk/verify/xcrz_sigmastar_demo`
- App commit during latest validation: `1e803f0bc035fb4a9e4ef5064a77a0c308e28b75`
- App repository status after committing PCR02 glibc interface libraries: clean.
- Full build and OTA validation used `--allow-dirty` because SDK build steps generate tracked artifacts in the vendor tree. This is acceptable for host bring-up evidence, but release-grade strict builds still require resolving the SDK source-check policy below.
- Explicit non-migration item remains excluded: `pcr02_ssc305_compile/SourceCode/project/configs/current.configs.in`

## Build validation

Command:

```bash
rtk ./build.sh compile --profile ap6303bh_512m_v20 --allow-dirty --no-copy-nfs --toolchain-root /vsdata/leiwenjun/pcr02_ssc305_compile/.toolchains/ssc305
```

Result: exit code `0`.

Key evidence:

- Build completed with `[build] done`.
- `customer.sqfs` rebuilt after migrating PCR02 customer resources.
- `customer.sqfs` size check passed: `DST:[0x2fdb000] THD:[0x7000000]`.
- `customer.sqfs` generated size: `50180096` bytes, about `47.85 MiB`.
- Version trace generated into `SourceCode/project/pcr02_customer/etc/version.ini`:

```text
commit_sdk=4f49e49e2
commit_app_name=xcrz_sigmastar_demo
commit_app=1e803f0b
hw_ver=v2.0
```

Known warning retained for board validation:

- `snigenerator: invalid option -- 'q'` appears during image script generation, but the make flow returned success.
- A no-clean rebuild before the final clean build failed on a host GCC plugin mismatch in `arm_ssp_per_task_plugin.so`; the subsequent clean build rebuilt the plugin and passed.

## Customer partition validation

Checked output files:

```text
SourceCode/project/image/output/customer/prog_application.sh
SourceCode/project/image/output/customer/bin/prog_pcr02
SourceCode/project/image/output/customer/bin/prog_daemon
SourceCode/project/image/output/customer/bin/prog_ota
SourceCode/project/image/output/images/customer.sqfs
```

Result: all files above exist in the generated customer output.

Checked generated `/customer/demo.sh` contains PCR02 boot actions after the 2026-05-31 module-list correction:

```text
gpio10, gpio11, gpio18 direction/value setup
gpio54, gpio55 AP6303BH setup sequence
insmod /config/modules/5.10/bcmdhd.ko
insmod /config/modules/5.10/pstore.ko
insmod /config/modules/5.10/pstore_zone.ko
cat /sys/bus/sdio/devices/mmc1:0001:1/uevent
cat /sys/kernel/debug/mmc1/ios
sh /customer/prog_application.sh
```

Cleanup check:

- No generated customer output was found for `flash_erase`, `nanddump`, `nandwrite`, `adbd`, `start_adbd.sh`, or `writeback.sh` under max depth 3.
- No generated customer `demo.sh` hit was found for `sstar_netphy`, `sstar_emac`, `gyro`, `light_sensor`, `mdev -s`, `writeback`, `start_adbd`, or `PACK_MOD_LIST`.

Clarification:

- `libbridge.so`, `libcommon.so`, and `libproto.so` are not part of `pcr02_customer`; they belong to the PCR02 app repository library overlays under `SourceCode/sdk/verify/xcrz_sigmastar_demo/libs/...`.

## Self-check validation

Command:

```bash
rtk ./build.sh self-check --toolchain-root /vsdata/leiwenjun/pcr02_ssc305_compile/.toolchains/ssc305
```

Result: exit code `0`.

Key output:

```text
[self-check] profile=ap6303bh_512m_v20 defconfig=xcrz_ipc_ap6303bh_512M_pcr02_v20_defconfig
[self-check] app_name=xcrz_sigmastar_demo
[self-check] app_build_system=make
[self-check] vehicle_ota_config=/vsdata/leiwenjun/Iford_IMSSV05C13/tools/vehicle-ota/pcr02.env
[self-check] ota_partitions=default_without_rootfs_data
[build] done
```

Strict compile without `--allow-dirty` was also attempted:

```bash
rtk ./build.sh compile --profile ap6303bh_512m_v20 --no-clean --no-copy-nfs --toolchain-root /vsdata/leiwenjun/pcr02_ssc305_compile/.toolchains/ssc305
```

Result: exit code `1`.

Reason:

```text
ERROR: sdk has no upstream branch configured: /vsdata/leiwenjun/Iford_IMSSV05C13
```

Decision:

- This is a repository policy blocker from the freshly initialized local SDK tree, not a PCR02 source migration failure.
- Before release-grade CI, configure the SDK repository upstream branch/remote or adjust the build source-check policy for local vendor SDK import repositories.

## OTA validation: content package

Command:

```bash
rtk ./build.sh ota --profile ap6303bh_512m_v20 --allow-dirty --skip-defconfig --no-clean --no-copy-nfs --ota-partitions rootfs,customer --toolchain-root /vsdata/leiwenjun/pcr02_ssc305_compile/.toolchains/ssc305
```

Result: exit code `0`.

Layout:

```text
0,kernel_otaenv.sh,kernel_otaenv.sh,0x1
1,rootfs.sqfs,/dev/mtd5,0x1
2,customer.sqfs,/dev/ubi0_3,0x1
```

Package check:

```bash
rtk gzip -t SourceCode/project/image/output/images/SStarOta.bin.gz
```

Result: exit code `0`.

Hashes from the latest post-app-commit package:

```text
75dab36c7bde246dc12e3984bec04535339ce9da5a55b6c5cec292332e055587  SStarOta.bin.gz
44cd2c41f3f45ae6e18560b82a426062d9336d107e82a12fa7ec0317119c0d92  rootfs.sqfs
ae619ec737e6c55d0f6775906efa9f3e72fafba52b7c91600d7f120a8f1ec836  customer.sqfs
c5215a2d76914b6b9baf1eea5f58163f4896c2980c7bc19e325183667635e6a2  ubia.bin
```

Size captured:

```text
SStarOta.bin.gz  52.6M
rootfs.sqfs       2.3M
customer.sqfs    47.9M
ubia.bin         78.2M
```

## OTA validation: old-production migration package

Command:

```bash
rtk ./build.sh ota --profile ap6303bh_512m_v20 --allow-dirty --skip-defconfig --no-clean --no-copy-nfs --ota-partitions rootfs,ubia --toolchain-root /vsdata/leiwenjun/pcr02_ssc305_compile/.toolchains/ssc305
```

Result: exit code `0`.

Layout:

```text
0,kernel_otaenv.sh,kernel_otaenv.sh,0x1
1,rootfs.sqfs,/dev/mtd5,0x1
2,ubia.bin,/dev/mtd8,0x1
```

Package check:

```bash
rtk gzip -t SourceCode/project/image/output/images/SStarOta.bin.gz
```

Result: exit code `0`.

Hashes from the latest post-app-commit package:

```text
1dd2ffa7e0dc9dee6644d80f0072b318a1466fb54a8603319fe393638df5ec93  SStarOta.bin.gz
f0057b0cef02fe738916773a304b57ce8a0f23a71c7355400a70c62c53f70d46  rootfs.sqfs
b5b259a71a3ed57049f7dde9f83cb842d909f03646b93d3e78ebab10c10dcd16  ubia.bin
5fb5b86e95e72358cca2c676e0b9e12b4ee1a734efaae2a4f0e3b4aa324bba0d  customer.sqfs
```

Important warning:

```text
[ota] WARNING: ubia block-update rewrites the whole UBI container; run this package from SD/external storage and set OTA_UMOUNT_OTA=1 on target
```

## Revalidation after module-list correction

Date: 2026-05-31

Reason:

- A full review found that the active IMSSV05C13 path still carried new-SDK module-list behavior that diverged from the old PCR02 product.
- The corrected behavior restores the old product's explicit customer module loading and avoids `PACK_MOD_LIST` rewriting of `/customer/demo.sh`.

Commands:

```bash
rtk ./build.sh compile --profile ap6303bh_512m_v20 --allow-dirty --no-copy-nfs --toolchain-root /vsdata/leiwenjun/pcr02_ssc305_compile/.toolchains/ssc305
rtk ./build.sh ota --profile ap6303bh_512m_v20 --allow-dirty --skip-defconfig --no-clean --no-copy-nfs --ota-partitions rootfs,customer --toolchain-root /vsdata/leiwenjun/pcr02_ssc305_compile/.toolchains/ssc305
rtk ./build.sh ota --profile ap6303bh_512m_v20 --allow-dirty --skip-defconfig --no-clean --no-copy-nfs --ota-partitions rootfs,ubia --toolchain-root /vsdata/leiwenjun/pcr02_ssc305_compile/.toolchains/ssc305
```

Result:

- Full compile returned exit code `0` and ended with `[build] done`.
- `rootfs,customer` OTA returned exit code `0`; package size: `52608035` bytes; `gzip -t` returned exit code `0`.
- `rootfs,ubia` OTA returned exit code `0`; package size: `66364865` bytes; `gzip -t` returned exit code `0`.

Generated `/customer/demo.sh` check:

```text
SourceCode/project/image/output/customer/demo.sh:47:insmod /config/modules/5.10/bcmdhd.ko
SourceCode/project/image/output/customer/demo.sh:48:insmod /config/modules/5.10/pstore.ko
SourceCode/project/image/output/customer/demo.sh:49:insmod /config/modules/5.10/pstore_zone.ko
```

The same grep found no hit for:

```text
sstar_netphy
sstar_emac
gyro
light_sensor
mdev -s
writeback
start_adbd
PACK_MOD_LIST
```

Content OTA hashes, `rootfs,customer`:

```text
d2a3e5068aa884f4c6c63f67052496115e649395d07305dea32c3d21c6097ea4  SStarOta.bin.gz
2810abb6710d539591f2c5fbc4fc69ed10e98902d2c5f90cb322e4faf5d7e80c  rootfs.sqfs
4dd36c96980fae33c5f0f04e1f48851cd3d72be97242b264d56d1818e49851fd  customer.sqfs
12cc5d9eb7568d948bdf28f70378d3a72856ce2b7f45a53a2db5861ee57db4bc  ubia.bin
```

Old-production migration OTA hashes, `rootfs,ubia`:

```text
5449e673178b0780468ec29fe7bb0c9b04df97bd87ba732782cff8d038f4dec4  SStarOta.bin.gz
9a8efd010418492c2226210a2b9f2790bb7068154b8a8142a21a231170a099f7  rootfs.sqfs
6fa7e5cca0565f22b36d031f50ca160f309199b432e5771903698e8ca7245ca0  customer.sqfs
1b384eba1b5609a656cee5aef933f4ac0b9e224dda306838a6aa8dd539176401  ubia.bin
```

## Revalidation after SNI generator compatibility fix

Date: 2026-05-31

Issue found during review:

- IMSSV05C13 `image.mk` still invokes `snigenerator -q`, but the imported IMSSV05C13 `snigenerator` source and binary no longer accepted `-q`.
- The make flow still returned success, leaving the warning easy to miss:

```text
snigenerator: invalid option -- 'q'
```

Fix:

- Restored the old PCR02/IMD00V5.1.1-compatible `-q` option in `SourceCode/project/image/makefiletools/src/snigenerator/snigenerator.c`.
- Rebuilt `SourceCode/project/image/makefiletools/bin/snigenerator`.

Tool check:

```bash
rtk bash -lc "SourceCode/project/image/makefiletools/bin/snigenerator -q 64 -a 10 -b 24 -c 0 -d 3 -e 1 -p 4096 -s 128 -t 0 -i SourceCode/project/board/iford/boot/spinand/partition/flash.sni -o /tmp/pcr02_flash.sni"
```

Result: exit code `0`; output file `/tmp/pcr02_flash.sni` generated.

OTA recheck:

```bash
rtk ./build.sh ota --profile ap6303bh_512m_v20 --allow-dirty --skip-defconfig --no-clean --no-copy-nfs --ota-partitions rootfs,customer --toolchain-root /vsdata/leiwenjun/pcr02_ssc305_compile/.toolchains/ssc305
```

Result:

- Exit code `0`.
- `snigenerator` emitted normal output paths for `flash.sni` and `flash_list.sni`.
- No `invalid option -- 'q'` warning appeared in the observed OTA log.
- `gzip -t SourceCode/project/image/output/images/SStarOta.bin.gz` returned exit code `0`.

Hashes after the SNI generator fix, `rootfs,customer`:

```text
cccc68cb8d29fc19a8ff16961085a35d9b1b910e4930c647b9f037303ec8f3a5  SStarOta.bin.gz
27a1691d91f428b4557ec3a2d089def4ff64bcb7f4d4fd51d48bf162e531ad37  rootfs.sqfs
a0e64ca2e882621fb1f95722c36c4fe23fa0a6e9ea7f01a295046b676fdeb2e7  customer.sqfs
```

## Invalid OTA combination

Command:

```bash
rtk ./build.sh ota --profile ap6303bh_512m_v20 --allow-dirty --skip-defconfig --no-clean --no-copy-nfs --ota-partitions rootfs,ubia,customer --toolchain-root /vsdata/leiwenjun/pcr02_ssc305_compile/.toolchains/ssc305
```

Result: exit code `1`.

Reason:

```text
ERROR: cannot select both ubia and its inner UBI volume for one OTA package: customer
hint: use --ota-partitions ubia for volume resize validation, or select inner volumes for content-only OTA
```

Decision:

- Use `rootfs,ubia` for old-production migration where UBI layout and customer volume need container-level replacement.
- Use `rootfs,customer` or `customer` for later content-level updates when the target already has the expected UBI layout and `/customer` is mounted through `ubiblock`.

## First-round acceptance gate

Not completed in this host validation session:

- PCR02 EVT2 board flash or boot.
- UART boot log capture.
- `/proc/mtd`, `mount`, `ubinfo`, and `/customer/demo.sh` runtime verification.
- Wi-Fi/AP6303BH SDIO bring-up on EVT2 hardware.
- Real OTA upgrade execution from an old production image to this IMSSV05C13 image.
- Post-OTA reboot and application health check.

These items must be executed on actual PCR02 EVT2 hardware before the migration can be accepted.
