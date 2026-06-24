# PCR02 IMSSV05C13 SDK migration plan

Date: 2026-05-30

Status: migration design plus current host-side execution record. Board acceptance evidence is still pending.

Project: PCR02 EVT2 / SSC305

Latest execution update: 2026-05-30 host-side migration and package validation evidence is archived at `archive/pcr02/validation/pcr02_imssv05c13_host_validation_20260530.md`. EVT2 board boot and real OTA upgrade remain first-round acceptance blockers.

Source SDKs:

| Path | Role | Current local state |
| --- | --- | --- |
| `Iford_IMSSV05C13` | New vendor SDK target | Git repository initialized locally; PCR02 migration commits are present through customer/packaging integration. |
| `Iford_IMD00V5.1.1_20250529` | Previous vendor SDK baseline | Not a Git repository at planning time. PCR02 product was ported from this SDK family. Vendor says this line is no longer maintained. |
| `Iford_IMD00V5.0.1` | Older vendor SDK reference | Historical reference only. Use only when a change origin is unclear. |
| `pcr02_ssc305_compile` | Current PCR02 product project | Git repository, branch `robot_pcr02`, based on old SDK with product changes. |

Hardware references:

- `PCR02 EVT2 系统框图-20251201.pdf`
- `PCR02_MAIN_V2.0_20251211.pdf`
- `PCR02 EVT2电源树-20251201.pdf`

## Goal

Initialize `Iford_IMSSV05C13` as a clean Git repository, then migrate all effective PCR02 product changes from `pcr02_ssc305_compile` into it as an ordered, module-oriented commit series. The first acceptance round must include PCR02 EVT2 board boot and OTA upgrade testing, not only host-side build success.

## Explicit decisions

1. `pcr02_ssc305_compile/SourceCode/project/configs/current.configs.in` is not an effective product change and must not be migrated unless a later review produces new evidence.
2. The final directory name is not important for the migration plan. The working target may remain `Iford_IMSSV05C13` during migration.
3. First-round acceptance requires PCR02 EVT2 board boot plus OTA upgrade real-device validation.
4. The migration must preserve new SDK fixes and replay PCR02 product intent; do not overwrite IMSSV05C13 files with old SDK files wholesale.
5. Generated build outputs must be excluded before product patches are imported.

## Non-goals

- Do not migrate build artifacts such as `.cmd`, `.o`, `built-in.a`, `modules.order`, `System.map`, `u-boot.cfg`, `autoconf.mk.dep`, image output directories, temporary OTA output, or generated dependency files.
- Do not treat current dirty files in `pcr02_ssc305_compile` as valid migration inputs without explicit review.
- Do not preserve old hand-written SPI-NAND USB upgrade scripts if IMSSV05C13 can generate scripts from the active image configuration.
- Do not claim completion without build logs, image layout evidence, EVT2 boot evidence, and OTA evidence.

## Current source facts

At planning time:

- `pcr02_ssc305_compile` is on `robot_pcr02`.
- Recent product commits include customer SquashFS static migration, ubia resize OTA, rootfs/customer mount fixes, release publishing, vehicle OTA, build entry consolidation, ADB/SSH/debug support, factory partition, MX35 partition sizing, and runtime I/O mitigation.
- `pcr02_ssc305_compile` has dirty changes:
  - `SourceCode/boot/include/autoconf.mk.dep`
  - `SourceCode/project/release/chip/iford/sigma_common_libs/glibc/11.1.0/release/dynamic/libss_mbx.so`
  - `SourceCode/project/configs/current.configs.in`
- `current.configs.in` has been explicitly classified as not effective for migration.
- `Iford_IMSSV05C13` already contains a newer vendor tree with `SourceCode/boot`, `SourceCode/kernel`, `SourceCode/project`, `SourceCode/sdk`, `Tools`, and `SGSDocs`.

## Effective PCR02 behavior to preserve

### Product profile

The PCR02 product profile is `ap6303bh_512m_v20`, mapped in the current project to:

- `CONFIG_BOARD="029C"`
- `CONFIG_BOARD_NAME="SSZ029C-S01B"`
- `CONFIG_TOOLCHAIN_VERSION_11.1.0=y`
- `CONFIG_KERNEL_VERSION_5.10=y`
- `CONFIG_UBOOT_CONFIG="iford_spinand_defconfig"`
- `CONFIG_KERNEL_CONFIG="iford_ssc029a_s01b_spinand_ap6303bh_defconfig"`
- `CONFIG_IMAGE_CONFIG="spinand_MX35_512M.squashfs.partition.config"`
- `CONFIG_VERIFY_ROBOT_PCR02=y`
- `CONFIG_VS_WIFI_AP6303BH=y`
- `CONFIG_VS_FLASH_PCR02_V20=y`

These values must be revalidated against IMSSV05C13 Kconfig names and defconfig expectations before committing.

### Storage and filesystem policy

The current effective storage decision remains:

```text
/customer = SquashFS on /dev/ubiblock0_3, mounted read-only
customer UBI volume type = static
first old-production migration OTA = rootfs,ubia
follow-up customer update after migration = customer-only is allowed
```

The PCR02 MX35 512MiB layout to preserve is based on:

`SourceCode/project/image/configs/general/spinand_MX35_512M.squashfs.partition.config`

Key expected mount truth table:

| Mount point | Expected filesystem | Expected source | Write policy |
| --- | --- | --- | --- |
| `/` | SquashFS | `/dev/mtdblock5` | Read-only |
| `/factory` | UBIFS | `ubi0:factory` | Low-frequency factory/device data |
| `/config` | UBIFS | `ubi0:miservice` | Writable service config |
| `/ota` | UBIFS | `ubi0:ota` | Writable OTA staging/status |
| `/customer` | SquashFS | `/dev/ubiblock0_3` | Read-only |
| `/data` | UBIFS | `ubi0:data` | Writable runtime data/logs/cache |

### Build and release policy

Preserve the root-level `build.sh` workflow from the product project:

- Team entrypoint is `./build.sh`.
- Default profile is `ap6303bh_512m_v20`.
- Compilation/release modes normally require clean source state.
- `--allow-dirty` is only for local validation.
- Build entry manages app build, SDK image build, SD package, SOC OTA, vehicle OTA, source lock, sysroot, toolchain path, and NAS publishing.
- SOC OTA default must not upgrade `rootfs` or `data` unless explicitly requested.
- Vehicle OTA consumes SOC OTA plus latest MCU packages from NAS; it does not build MCU firmware.

### OTA and release policy

Preserve:

- SOC OTA target name: `SStarOta.bin.gz`
- Mainboard MCU mapping: `gd32l235_app.bin -> mcu.bin`
- Motor MCU mapping: `mm32spin023c_app.bin` or `app.bin -> wheel_motor.bin`
- SOC NAS release root default: `/mnt/mcu-release-nas/robot/soc`
- MCU NAS release root default: `/mnt/mcu-release-nas/robot/mcu`
- Release bundle directories:
  - `01_line_flash_bootloader`
  - `02_sd_upgrade`
  - `03_soc_ota`
  - `04_vehicle_ota`
  - `99_trace`

## Commit sequence

Use small, reviewable commits. Suggested order:

1. `chore(import): 导入原厂 Iford_IMSSV05C13 基线`
2. `chore(repo): 忽略 SDK 构建产物`
3. `feat(build): 增加 PCR02 统一构建入口`
4. `feat(config): 增加 PCR02 EVT2 产品配置`
5. `feat(board): 适配 PCR02 EVT2 板级资源`
6. `feat(partition): 增加 PCR02 MX35 512M 分区布局`
7. `feat(app): 接入 PCR02 主应用构建`
8. `feat(runtime): 增加 PCR02 运行期挂载和调试配置`
9. `feat(ota): 增加 PCR02 整机 OTA 打包流程`
10. `fix(boot): 适配 PCR02 SPI-NAND 启动配置`
11. `fix(kernel): 适配 PCR02 内核配置`
12. `refactor(sdk): 适配 IMSSV05C13 构建接口`
13. `docs(migration): 记录 PCR02 新 SDK 迁移和验证结果`

Commit 1 must contain only the pristine vendor SDK. Commit 2 must happen before importing product changes to prevent generated files from entering the patch series.

Current local sequence after host-side migration work:

1. `chore(import): 导入原厂 Iford_IMSSV05C13 基线`
2. `chore(repo): 忽略 SDK 构建产物`
3. `feat(build): 增加 PCR02 统一构建入口`
4. `feat(config): 增加 PCR02 EVT2 产品配置`
5. `feat(partition): 增加 PCR02 MX35 512M 分区布局`
6. `feat(board): 适配 PCR02 EVT2 板级资源`
7. `feat(runtime): 增加 PCR02 rootfs 覆盖资源`
8. `feat(kernel): 增加 PCR02 S01B 内核板级配置`
9. `feat(customer): 接入 PCR02 客户区和打包规则`

Nested app repository sequence:

- `1e803f0b build(libs): 重建 PCR02 glibc 接口库`

Additional patches still expected after board validation:

- `docs(migration): 记录 PCR02 EVT2 启动和 OTA 实测结果`

## Execution phases

### Phase 0: preflight and baseline

Actions:

1. Record directory state and hashes for all four trees.
2. Confirm `pcr02_ssc305_compile` dirty files are excluded from migration unless reviewed.
3. Initialize Git in `Iford_IMSSV05C13`.
4. Commit the vendor SDK baseline.

Commands:

```bash
rtk git -C pcr02_ssc305_compile status --short --branch
rtk git -C pcr02_ssc305_compile log --oneline --decorate -40
cd ~/Iford_IMSSV05C13
rtk git init
rtk git add -A
rtk git commit -m "chore(import): 导入原厂 Iford_IMSSV05C13 基线"
```

Done criteria:

- `Iford_IMSSV05C13` has one clean vendor baseline commit.
- Dirty PCR02 source files are documented and not silently imported.

### Phase 1: repository hygiene

Actions:

1. Add or adapt `.gitignore` for SDK build outputs.
2. Run a status check after a local no-op or dry build command if available.
3. Confirm ignored outputs do not hide source/config files.

Common ignore classes:

- Kernel and boot `.cmd`, `.o`, `.a`, `built-in.*`, `modules.order`, `Module.symvers`, `System.map`
- `SourceCode/project/image/output/`
- Generated image files and OTA packages
- Temporary release staging directories
- Local toolchain cache if kept under the SDK tree

Done criteria:

- `rtk git status --short --ignored` shows generated outputs as ignored and source files still visible.

### Phase 2: build entry and source-state workflow

Actions:

1. Port root `build.sh` behavior conservatively.
2. Port `scripts/generate-build-info.sh`.
3. Port `scripts/update-readme-build-help.sh` only if still useful with IMSSV05C13.
4. Adapt hardcoded paths or make targets to the new SDK if they changed.

Validation:

```bash
rtk ./build.sh --help
rtk ./build.sh self-check --allow-dirty
```

Done criteria:

- Help output lists PCR02 modes and `ap6303bh_512m_v20`.
- Self-check does not require an unrelated build.

### Phase 3: Kconfig and defconfig

Actions:

1. Port PCR02 profile defconfigs except explicitly excluded `current.configs.in`.
2. Port `robot_pcr02` verify Kconfig.
3. Reconcile IMSSV05C13 Kconfig symbol changes.
4. Validate generated config selects the intended image config, kernel config, WiFi, sensor, IQ, and verify app option.

Validation:

```bash
rtk ./build.sh verify --profile ap6303bh_512m_v20 --allow-dirty
```

Done criteria:

- `CONFIG_VERIFY_ROBOT_PCR02=y` is effective.
- `CONFIG_IMAGE_CONFIG="spinand_MX35_512M.squashfs.partition.config"` is effective.
- No stale `current.configs.in` migration is present.

### Phase 4: board and hardware resources

Actions:

1. Build a PCR02 EVT2 hardware checklist from the three PDFs.
2. Port only board resources required by PCR02:
   - SPI-NAND MX35 geometry and boot chain resources
   - DDR and memory layout
   - WiFi/BT firmware and enablement
   - sensor module and IQ files
   - GPIO, PWM, UART, USB/SD, power rails, reset pins
   - required board-side tools such as MTD utilities, only if not already present or replaced by IMSSV05C13
3. Avoid migrating unrelated board folders or generated binaries.

Done criteria:

- Each migrated board resource maps to a hardware reference or an existing PCR02 behavior.
- Hardware checklist is attached to the migration review.

### Phase 5: partition, image, and mount layout

Actions:

1. Port `spinand_MX35_512M.squashfs.partition.config`.
2. Reconcile IMSSV05C13 image script and partition generator changes.
3. Ensure `customer` is SquashFS on static UBI volume and mounted read-only by ubiblock.
4. Ensure `factory`, `miservice`, `ota`, and `data` remain writable UBIFS volumes.
5. Ensure normal SOC OTA defaults skip `rootfs` and `data`.

Validation:

```bash
rtk ./build.sh package --profile ap6303bh_512m_v20 --pack ota --allow-dirty
```

Artifacts to inspect:

- `SourceCode/project/image/output/images/partinfo.pni`
- `SourceCode/project/image/output/images/image_config.cfg`
- `SourceCode/project/image/output/images/SStarOtaLayout.txt`
- generated mount table or startup scripts, depending on IMSSV05C13 layout

Done criteria:

- `/customer` maps to `/dev/ubiblock0_3`.
- `customer` UBI volume type is static.
- `data` is not included in default OTA.
- First migration package can include `rootfs,ubia`.

### Phase 6: application and runtime policy

Actions:

1. Decide whether IMSSV05C13 should continue with `xcrz_sigmastar_demo` priority or move to `gros`.
2. Port application build integration and resource installation.
3. Port `/customer/etc/version.ini` generation and install path.
4. Port runtime path, library, debug, ADB/SSH, and I/O mitigation behavior.
5. Validate runtime libraries against `readelf -d` instead of copying old dependency sets blindly.

Validation:

```bash
rtk ./build.sh app --profile ap6303bh_512m_v20 --allow-dirty
```

Done criteria:

- App binary and runtime resources install into the expected image staging tree.
- Required shared libraries are present.
- Debug facilities match PCR02 policy.

### Phase 7: OTA and release tooling

Actions:

1. Port `tools/firmware-release-tools/resolve-latest-release.sh`.
2. Port `tools/ota-packager/ota-packager.sh` and packaged CLI only if licensing and binary provenance are acceptable.
3. Port `tools/vehicle-ota/pcr02.env`.
4. Reconcile IMSSV05C13 release output paths.
5. Keep publish rules non-overwriting by default.

Validation:

```bash
rtk ./build.sh vehicle-ota --profile ap6303bh_512m_v20 --allow-dirty --force-vehicle-ota
rtk ./build.sh publish-soc --profile ap6303bh_512m_v20 --allow-dirty
```

If NAS or MCU packages are unavailable, create a controlled dry-run record and mark the release validation blocked, not passed.

Done criteria:

- `vehicle-ota-inputs.json` records SOC, mainboard MCU, and motor MCU sources and sha256.
- Package inspection validates target names.
- Publish flow writes `release_manifest.json` last and does not overwrite existing release bundles by default.

### Phase 8: boot and kernel adaptation

Actions:

1. Port source-level boot config changes only.
2. Port source-level kernel config or driver changes only.
3. Reconcile IMSSV05C13 vendor updates before changing driver code.
4. Exclude all generated kernel and boot outputs.

Validation:

```bash
rtk ./build.sh kernel --profile ap6303bh_512m_v20 --allow-dirty
rtk ./build.sh compile --profile ap6303bh_512m_v20 --allow-dirty --no-sync-sources
```

Done criteria:

- Kernel builds with PCR02 defconfig.
- Boot image and kernel image are generated.
- No generated boot/kernel artifacts are staged for commit.

### Phase 9: EVT2 board boot validation

Required evidence:

1. Flash method used and exact image paths.
2. Bootloader log with flash geometry and boot partition selection.
3. Kernel boot log to login or application start.
4. Runtime mount table.
5. UBI volume table.
6. Application start result.

Suggested board-side commands:

```sh
cat /proc/cmdline
cat /proc/mtd
mount
df -h
ubinfo -a
cat /etc/version.ini 2>/dev/null || true
cat /customer/etc/version.ini 2>/dev/null || true
dmesg | grep -Ei 'ubi|ubifs|squashfs|mtd|nand|ecc|error|fail'
ps | grep -E 'prog_pcr02|xcrz|gros' | grep -v grep
```

Pass criteria:

- EVT2 board boots without kernel panic.
- Root filesystem is mounted read-only SquashFS.
- `/customer` is mounted read-only from `/dev/ubiblock0_3`.
- `/data` is writable.
- Application starts or a known non-SDK blocker is documented separately.
- No new ECC/UBI/SquashFS fatal errors appear during boot.

### Phase 10: EVT2 OTA validation

Test at least two OTA paths:

1. First migration package from old production layout:
   - package contents: `rootfs,ubia`
   - expected result: new rootfs plus resized/rebuilt ubia with static customer volume
   - data preservation: not expected if whole ubia is rewritten
2. Follow-up customer-only package:
   - package contents: `customer`
   - expected result: `/customer` content updates, `/data` preserved

Required evidence:

- OTA package path and sha256.
- `SStarOtaLayout.txt`.
- Upgrade command or application-triggered OTA log.
- Pre-upgrade and post-upgrade `cat /proc/mtd`, `ubinfo -a`, `mount`, and version checks.
- Power-cycle boot after OTA.

Pass criteria:

- OTA upgrade completes and reboots successfully.
- Post-upgrade mount truth table matches this plan.
- `customer` static volume and ubiblock mount are preserved.
- Follow-up customer-only OTA does not erase `/data`.
- Failed upgrade path has recovery instructions or rollback decision.

## Conflict matrix

| Area | Shared files | Parallel suitability | Notes |
| --- | --- | --- | --- |
| Vendor baseline and `.gitignore` | Repository root | No | Must be serialized before any import. |
| Build entry | `build.sh`, `scripts/*`, README | Limited | Can be reviewed separately, but later phases depend on it. |
| Kconfig/defconfig | `SourceCode/project/configs/**` | No | Shared contract for all later builds. |
| Partition/image config | `SourceCode/project/image/**` | No | Must be serialized with OTA behavior. |
| Board resources | `SourceCode/project/board/iford/**` | Yes, after checklist | Can be split by WiFi, sensor/IQ, tools, boot resources. |
| App/runtime | `SourceCode/sdk/verify/**`, rootfs/customer staging | Yes, after build entry | Keep app build and runtime policy separate. |
| OTA/release tools | `tools/**`, release scripts | Yes | Depends on image output names. |
| Boot/kernel | `SourceCode/boot/**`, `SourceCode/kernel/**` | Limited | Avoid conflicting with defconfig and generated files. |

## Risk ledger

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Old SDK file overwrites new SDK vendor fixes | Regression or hidden incompatibility | Use semantic porting and three-way review, not directory copy. |
| Build outputs enter Git | Polluted patch series and unreviewable diffs | Commit `.gitignore` before migration and inspect `git status`. |
| `current.configs.in` is accidentally migrated | Stale config behavior | Explicitly exclude it; check final patch series. |
| Partition layout differs from actual MX35 geometry | Boot/OTA failure or data loss | Cross-check PDF, CIS/SNI, `partinfo.pni`, and board logs. |
| OTA first migration erases data unexpectedly | Field data loss | Document first migration `ubia` rewrite behavior and require sign-off. |
| Vehicle OTA depends on unavailable NAS packages | Incomplete validation | Use dry-run only as blocked evidence; real acceptance requires actual package input. |
| App build depends on old SDK libraries | Runtime startup failure | Validate with `readelf`, staged libraries, and board run. |

## Final acceptance gate

The migration can be called first-round accepted only when all of the following are true:

1. `Iford_IMSSV05C13` has an ordered commit series with clean vendor baseline and module-level product commits.
2. `current.configs.in` is not present as a migrated product change.
3. Host build produces expected boot, kernel, rootfs, ubia, SOC OTA, and trace artifacts.
4. EVT2 board boots from the migrated IMSSV05C13 build.
5. EVT2 board passes the first migration OTA path.
6. EVT2 board passes follow-up customer-only OTA without erasing `/data`.
7. Runtime mount truth table matches the effective PCR02 decision index.
8. Validation evidence is archived with exact image paths, package sha256, logs, and command outputs.

## Suggested follow-up artifacts

- `archive/pcr02/validation/pcr02_imssv05c13_evt2_boot_validation_<date>.md`
- `archive/pcr02/ota-release/pcr02_imssv05c13_ota_validation_<date>.md`
- `archive/pcr02/source-audit/pcr02_imssv05c13_patch_series_review_<date>.md`

These should contain evidence after implementation. This document is only the plan and gate definition.
