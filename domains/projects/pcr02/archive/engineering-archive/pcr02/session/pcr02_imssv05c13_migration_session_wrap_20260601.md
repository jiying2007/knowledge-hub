# PCR02 IMSSV05C13 SDK Migration Session Wrap

- Captured at: 2026-06-01
- Source scope: current Codex session, `/vsdata/leiwenjun/Iford_IMSSV05C13`, PCR02 archive notes
- Topic: session-wrap
- Sanitization: credential material omitted, no full chat transcript, no bulk build logs
- Archive status: current session handoff
- Related validation note: `../validation/pcr02_imssv05c13_host_validation_20260530.md`
- Memory candidates: `pcr02_imssv05c13_memory_candidates_20260601.md`

## Goal

Migrate effective PCR02 product changes from `/vsdata/leiwenjun/pcr02_ssc305_compile` onto the new vendor SDK `/vsdata/leiwenjun/Iford_IMSSV05C13`, because the vendor stated `Iford_IMD00V5.1.1_20250529` and related older SDK lines are no longer maintained.

User constraints captured during the work:

- `pcr02_ssc305_compile/SourceCode/project/configs/current.configs.in` is not an effective product change and must not be treated as migration input.
- Directory naming is temporarily not important.
- First-round acceptance must include real PCR02 EVT2 board boot and real OTA upgrade test.
- Hardware reference set: `PCR02 EVT2 系统框图-20251201.pdf`, `PCR02_MAIN_V2.0_20251211.pdf`, `PCR02 EVT2电源树-20251201.pdf`.

## Repositories and Baselines

| Role | Path | Notes |
| --- | --- | --- |
| New SDK migration target | `/vsdata/leiwenjun/Iford_IMSSV05C13` | Git repository initialized and used for ordered commits. |
| Current product source | `/vsdata/leiwenjun/pcr02_ssc305_compile` | Effective product behavior source. |
| Older vendor baseline | `/vsdata/leiwenjun/Iford_IMD00V5.1.1_20250529` | Historical comparison source. |
| Nested app library repo | `/vsdata/leiwenjun/Iford_IMSSV05C13/SourceCode/sdk/verify/xcrz_sigmastar_demo` | Has a local app/library rebuild commit. |

## Commits Produced in Target SDK

Latest ordered target SDK commits:

```text
35645c874 fix(image): 修复 PCR02 SNI 生成参数
df4941268 fix(boot): 恢复 PCR02 启动配置
dc10c7dcd fix(customer): 恢复 PCR02 客户区打包行为
4878b78f0 fix(customer): 恢复 PCR02 模块清单策略
4f49e49e2 feat(customer): 接入 PCR02 客户区和打包规则
954b2615b feat(kernel): 增加 PCR02 S01B 内核板级配置
334fbf69a feat(runtime): 增加 PCR02 rootfs 覆盖资源
c0f80638a feat(board): 适配 PCR02 EVT2 板级资源
73876687c feat(partition): 增加 PCR02 MX35 512M 分区布局
0dd0cb211 feat(config): 增加 PCR02 EVT2 产品配置
1050c9959 feat(build): 增加 PCR02 统一构建入口
acc28d66f chore(repo): 忽略 SDK 构建产物
f08e4f209 chore(import): 导入原厂 Iford_IMSSV05C13 基线
```

Nested app/library repo commit:

```text
1e803f0b build(libs): 重建 PCR02 glibc 接口库
```

## Implemented Workstreams

| Workstream | Result |
| --- | --- |
| Build entry | Added PCR02 unified build entry and profile wiring for `ap6303bh_512m_v20`. |
| Product config | Added PCR02 EVT2 product config, excluding the ineffective old `current.configs.in`. |
| Partition layout | Added PCR02 MX35 512 MiB partition layout and customer/rootfs/data policy alignment. |
| Board resources | Ported board-level resources for PCR02 EVT2. |
| Runtime rootfs overlay | Added PCR02 rootfs overlay resources. |
| Kernel config | Added PCR02 S01B kernel board config. |
| Customer packaging | Ported customer area, module list policy, and packaging behavior from the current product. |
| Boot config | Restored old-product U-Boot disable set and corrected bootlogo RAM size to `0x0f600000`. |
| Image tools | Reintroduced `snigenerator -q` support required by IMSSV05C13 `image.mk`. |

## Key Review Findings and Fixes

### Customer Packaging

The new SDK introduced active ADB packaging/start logic, `PACK_MOD_LIST` generation behavior, `mdev -s`, and raw flash `writeback.sh` packaging that did not match the current PCR02 product. These were removed or restored to old-product behavior in:

- `dc10c7dcd fix(customer): 恢复 PCR02 客户区打包行为`
- `4878b78f0 fix(customer): 恢复 PCR02 模块清单策略`

The generated customer `demo.sh` retained expected module entries only for:

```text
bcmdhd.ko
pstore.ko
pstore_zone.ko
```

No generated customer output hit was found for `sstar_netphy`, `sstar_emac`, `gyro`, `light_sensor`, `mdev -s`, `writeback`, `start_adbd`, or `PACK_MOD_LIST`.

### Rootfs ADB

`rootfs` still includes `/usr/sbin/adbd`. This was checked against the old product and found to be inherited old-product behavior, not an IMSSV05C13 migration residue. If product policy changes to "no ADB anywhere", handle it as a new explicit requirement.

### SNI Generator

During review, `image.mk` was found to call `snigenerator -q`, while the imported IMSSV05C13 `snigenerator` did not accept `-q`, producing:

```text
snigenerator: invalid option -- 'q'
```

The build still completed, so this was a silent packaging risk. Commit `35645c874` restored old-product `-q` / `block_page_cnt` support and rebuilt the tracked `snigenerator` binary.

## Host-Side Validation Evidence

Full compile command:

```bash
rtk ./build.sh compile --profile ap6303bh_512m_v20 --allow-dirty --no-copy-nfs --toolchain-root /vsdata/leiwenjun/pcr02_ssc305_compile/.toolchains/ssc305
```

Result: exit `0`, log ended with `[build] done`.

Observed image size checks passed:

```text
kernel DST:[0x3a2512] THD:[0xA00000]
boot.bin DST:[0x280000] THD:[0x380000]
rootfs.sqfs DST:[0x24f000] THD:[0x1600000]
misc.fwfs DST:[0x100000] THD:[0x200000]
pstore.fwfs DST:[0xc0000] THD:[0x200000]
factory.ubifs DST:[0x326000] THD:[0xC00000]
miservice.ubifs DST:[0x12a6000] THD:[0x3000000]
ota.ubifs DST:[0x326000] THD:[0x6000000]
customer.sqfs DST:[0x2fdb000] THD:[0x7000000]
data.ubifs DST:[0x326000] THD:[0x8C00000]
```

Direct SNI tool validation after `35645c874`:

```bash
rtk bash -lc "SourceCode/project/image/makefiletools/bin/snigenerator -q 64 -a 10 -b 24 -c 0 -d 3 -e 1 -p 4096 -s 128 -t 0 -i SourceCode/project/board/iford/boot/spinand/partition/flash.sni -o /tmp/pcr02_flash.sni"
```

Result: exit `0`; generated `/tmp/pcr02_flash.sni`.

OTA validation after SNI fix:

```bash
rtk ./build.sh ota --profile ap6303bh_512m_v20 --allow-dirty --skip-defconfig --no-clean --no-copy-nfs --ota-partitions rootfs,customer --toolchain-root /vsdata/leiwenjun/pcr02_ssc305_compile/.toolchains/ssc305
```

Result: exit `0`; `SStarOta.bin.gz` passed `gzip -t`; observed OTA log no longer showed `snigenerator: invalid option -- 'q'`.

Latest validated artifact hashes after SNI fix:

```text
cccc68cb8d29fc19a8ff16961085a35d9b1b910e4930c647b9f037303ec8f3a5  SStarOta.bin.gz
27a1691d91f428b4557ec3a2d089def4ff64bcb7f4d4fd51d48bf162e531ad37  rootfs.sqfs
a0e64ca2e882621fb1f95722c36c4fe23fa0a6e9ea7f01a295046b676fdeb2e7  customer.sqfs
```

Earlier old-production migration OTA validation before SNI fix:

```text
rootfs,ubia OTA: exit 0, gzip -t passed
SStarOta.bin.gz sha256: 5449e673178b0780468ec29fe7bb0c9b04df97bd87ba732782cff8d038f4dec4
rootfs.sqfs sha256: 9a8efd010418492c2226210a2b9f2790bb7068154b8a8142a21a231170a099f7
customer.sqfs sha256: 6fa7e5cca0565f22b36d031f50ca160f309199b432e5771903698e8ca7245ca0
ubia.bin sha256: 1b384eba1b5609a656cee5aef933f4ac0b9e224dda306838a6aa8dd539176401
```

Important warning for the first migration package: `ubia` block-update rewrites the whole UBI container. Run from SD/external storage and set `OTA_UMOUNT_OTA=1` on target.

## Current Dirty Worktree

`/vsdata/leiwenjun/Iford_IMSSV05C13` is dirty because compile/OTA generated or refreshed tracked and untracked artifacts. Representative categories:

- `SourceCode/boot/.config`, generated boot include files and build tools
- `SourceCode/kernel/.config`, `Module.symvers`, `uImage.*`, generated scripts/tools/config headers
- `SourceCode/project/.config`, `SourceCode/project/configs/current.configs`, generated project include files
- `SourceCode/project/release/.../*.ko`, `libcam_*`, `libss_mbx.*`
- untracked kernel include/config directories, ASN.1 generated files, and boot helper tools

These were not cleaned or reverted. Treat them as generated build state unless explicitly reviewed and approved for cleanup.

## Remaining Blockers and Risks

| Item | Status | Risk |
| --- | --- | --- |
| PCR02 EVT2 board boot | Not executed in this host session | Required for first-round acceptance. |
| PCR02 EVT2 real OTA upgrade | Not executed in this host session | Required for first-round acceptance. |
| `rootfs,ubia` OTA after SNI fix | Recommended but not rerun after `35645c874` | First migration path should be regenerated and hash-recorded before target execution. |
| Generated dirty worktree cleanup | Deferred | Cleaning requires explicit approval or a controlled generated-artifact policy. |
| Hardware PDF cross-check | Not fully evidenced in this wrap | Board validation should cross-check boot logs, power rails, flash geometry, and device-tree assumptions against the named hardware docs. |

## Next Session Resume

Recommended starting checks:

```bash
rtk git -C /vsdata/leiwenjun/Iford_IMSSV05C13 log --oneline -14
rtk git -C /vsdata/leiwenjun/Iford_IMSSV05C13 status --short
rtk git -C /vsdata/leiwenjun/Iford_IMSSV05C13/SourceCode/sdk/verify/xcrz_sigmastar_demo log --oneline -3
rtk git -C /vsdata/leiwenjun/Iford_IMSSV05C13/SourceCode/sdk/verify/xcrz_sigmastar_demo status --short
```

Recommended host-side preparation before board validation:

```bash
rtk ./build.sh ota --profile ap6303bh_512m_v20 --allow-dirty --skip-defconfig --no-clean --no-copy-nfs --ota-partitions rootfs,ubia --toolchain-root /vsdata/leiwenjun/pcr02_ssc305_compile/.toolchains/ssc305
```

First-round acceptance checklist:

1. Flash or otherwise provision the PCR02 EVT2 board with the generated IMSSV05C13 PCR02 image set.
2. Capture serial boot log from ROM/U-Boot/kernel/userspace until application/service startup.
3. Verify flash geometry, partition table, rootfs/customer/data mounts, and required kernel modules.
4. Run the first migration OTA package from SD/external storage with `OTA_UMOUNT_OTA=1` if `ubia` is included.
5. Reboot after OTA and verify the same boot/mount/service checks.
6. Archive logs, hashes, exact commands, board identifier, and pass/fail result under `archive/pcr02/validation/`.

## Gate Result

- Archive candidate: pass
- Memory candidate: yes, see `pcr02_imssv05c13_memory_candidates_20260601.md`
- Completion status: host-side migration and review are committed; first-round acceptance remains blocked on real PCR02 EVT2 board boot and OTA validation.
