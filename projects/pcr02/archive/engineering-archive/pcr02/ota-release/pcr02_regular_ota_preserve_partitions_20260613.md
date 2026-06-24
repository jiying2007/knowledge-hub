# PCR02 Regular OTA Preserve Partitions

Date: 2026-06-13
Captured: 2026-06-15
Status: current regular OTA release note

## Source

- Codex session `019ec10a-a28f-79d0-8292-4ccb4113490a`.
- Context: `pcr02_ssc305_compile` published `v1.1.21` with `./build.sh release-dual --release-flow migration`, then published `v1.1.22` / `v1.1.23` with `./build.sh release-dual --release-flow regular`.
- Device-side evidence was summarized from OTA state files, `guide.toml`, `prog_ota.log`, mount table, MTD layout, and follow-up package tests.

## Sanitization

- Full `prog_ota.log`, serial boot logs, NAS paths, and large package artifacts are not copied here.
- Kept only version numbers, release-flow decisions, failure phase, mount/partition facts, and validation outcome.

## Background

After devices had migrated to the new layout, a regular OTA from SoC `1.1.21` to `1.1.22` / `1.1.23` failed. The failure happened after app-level extraction, MCU and motor checks, and SoC handoff:

```text
/ota/ota_phase  = WAIT_OTA_END
/ota/ota_status = FAILED
guide.toml soc.version = 1.1.23
current version before upgrade: soc=1.1.21, mcu=1.1.29, motor_left=0.4.5, motor_right=0.4.5
```

The runtime mount table on the migrated device showed:

```text
/dev/root on / type squashfs (ro)
ubi0:factory on /factory type ubifs
ubi0:miservice on /config type ubifs
ubi0:ota on /ota type ubifs
/dev/ubiblock0_3 on /customer type squashfs (ro)
ubi0:data on /data type ubifs
```

## Current Decision

- `regular` SoC OTA must preserve `/factory`, `/ota`, and `/data`.
- `regular` SoC OTA must not rebuild or rewrite the whole `ubia` container.
- `regular` SoC OTA may update `customer` only when the device layout and package path support the current customer format.
- On the current production SquashFS customer layout, formal regular OTA should be packaged without `ota` volume update.
- For production regular OTA, do not carry `customer_ro`-only assumptions unless the target production image actually mounts and uses `customer_ro`.
- `ubiblock.c` and `ota_start.sh` changes that only serve debug/customer_ro experiments should not be mixed into the formal production regular package.

## Validation Result

The immediate failure was resolved by generating a formal OTA package that did not include the `ota` partition. The follow-up test result recorded in the session was:

```text
regular OTA package without ota partition: upgrade succeeded
```

This validates the current release decision for post-migration regular OTA:

```text
preserve /factory
preserve /ota
preserve /data
do not rewrite ubia
```

## Release Guidance

Use `migration` only for the old-production to new-layout transition. Use `regular` after migration and keep the partition list narrow.

Before publishing a regular OTA:

```sh
rtk ./build.sh release-dual --release-flow regular ...
```

Then inspect the generated guide/manifest and package contents:

```sh
tar -tzf <sd_upgrade_or_vehicle_package>.tar.gz
grep -nE 'soc|mcu|wheel_motor|before_update' <extracted>/guide.toml
```

The expected post-migration regular package must not contain updates for `/factory`, `/ota`, or `/data`.

## Failure Triage Checklist

If regular OTA fails with `WAIT_OTA_END` and `FAILED`:

- Check `/ota/prog_ota.log` for app-level extraction success and SoC handoff.
- Check `guide.toml` versions and files actually loaded.
- Check whether the package contains `ota`, `factory`, `data`, or whole `ubia` content.
- Check current mount table and confirm whether `/customer` is UBIFS or SquashFS via `ubiblock`.
- Check whether the package assumes `customer_ro`; production builds may not expose that mount point.
- Rebuild a test package without `ota` and without debug-only `ubiblock/customer_ro` changes, then verify on a migrated device.

## Risks

- Mixing `migration` and `regular` semantics can accidentally rewrite preservation volumes.
- Updating `/ota` while running the upgrade flow from `/ota` can corrupt the control path or leave ambiguous status.
- A package that worked for old UBIFS customer may not be valid for the current SquashFS customer layout.
- Debug overlay/customer_ro behavior must not silently leak into production regular release assumptions.

## Provenance

- Session IDs: `019ec10a-a28f-79d0-8292-4ccb4113490a`.
- Related archive: `ota-release/pcr02-ota-ubia-resize-customer-squashfs-20260529/`.
- Related decisions: `decision-index.md`, `ubifs-squashfs/pcr02_customer_squashfs_overlay_flash_read_20260606.md`.

## Quality Gate

- Source: local Codex session history and summarized device-side evidence.
- Topic: ota-release.
- Archive Candidate Path: `archive/pcr02/ota-release/pcr02_regular_ota_preserve_partitions_20260613.md`.
- Sanitization: pass.
- Verification: upgrade success was reported for the package excluding `ota`; this note does not claim a full regression matrix across all package variants.
- Memory Candidate: yes, after human review this can be promoted to release-flow guidance.
- Gate Result: pass.
