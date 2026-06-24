# PCR02 Rootfs, Customer, And Data Symlink Policy

Date: 2026-06-06
Status: current policy

## Background

PCR02 now uses a read-only rootfs and a production `/customer` SquashFS. Historical builds placed some files directly in rootfs, some in `/customer/etc`, and some runtime state under writable UBIFS volumes. Without a clear ownership rule, OTA can accidentally overwrite mutable provisioning data, while debug replacement of `/customer` becomes difficult to reason about.

## Current Conclusion

Use ownership, not convenience, to decide placement:

- `/` rootfs owns boot-critical executables, init scripts, library ABI, and compatibility symlinks.
- `/customer` owns versioned product content and static defaults shipped with the release.
- `/data` owns mutable runtime state, provisioning data, caches, logs, debug overlay upperdirs, and device-local changes.

Rootfs symlinks are compatibility shims. They should not be used to hide mutable state inside a read-only or version-owned partition.

## Placement Rules

Place in `/customer/etc`:

- Product default config shipped with a release.
- Static app resources and default templates.
- `/customer/etc/version.ini`, used as the customer content version sentinel.
- Config that may change only by OTA or SD upgrade.

Place in `/data`:

- Wi-Fi credentials, user binding data, and provisioning results.
- Runtime-generated network state.
- Logs, caches, crash dumps, and debug flags.
- Debug `/customer` overlay upperdir, usually `/data/customer_overlay`.
- Anything expected to survive a regular SoC OTA.

Keep in rootfs or rootfs symlink:

- Compatibility paths required by existing binaries.
- Boot scripts that mount `/customer`, `/factory`, `/config`, `/ota`, and `/data`.
- Symlinks from legacy paths to the canonical `/customer` or `/data` location.

## Examples

- `wpa_supplicant.conf`: product template can live in `/customer/etc`; real credentials should be generated or stored under `/data`.
- `hostapd.conf` and `dnsmasq.conf`: defaults can live in `/customer/etc`; runtime overrides should live under `/data`.
- `resolv.conf`: runtime generated state should not be treated as immutable release content.
- `localtime`: release default can live in `/customer/etc`; user/device-specific timezone state should be mutable if the product supports it.

## OTA Policy

`migration`:

- May rewrite whole `ubia`, so `/data` preservation is not guaranteed.
- Must document that device-local runtime state can be lost.

`regular`:

- Must not upgrade `/factory` or `/data` by default.
- May upgrade rootfs, kernel, `/customer`, and app resources according to package intent.
- Must preserve mutable provisioning and runtime data.

## Debug Policy

Debug builds should prefer:

```text
lowerdir=/customer_squashfs_lower
upperdir=/data/customer_overlay/upper
workdir=/data/customer_overlay/work
mountpoint=/customer
```

When `/customer/etc/version.ini` changes, the debug overlay upperdir should be archived or reset so old modified files do not mask the new lower version.

## Validation Checklist

- `mount` shows production `/customer` read-only and debug `/customer` as overlayfs only on debug builds.
- `/customer/etc/version.ini` is readable after boot.
- Regular OTA does not touch `/data` and does not reset provisioning files.
- Runtime config files that contain credentials are not shipped in release SquashFS images.
- Legacy symlinks resolve to the intended canonical path.

## Provenance

- Current session archive audit on 2026-06-06.
- Prior discussions on `/customer` SquashFS, debug overlay, `version.ini`, and migration/regular release flow.
- Supersedes the UBIFS-oriented portions of `partition-storage/pcr02_sdk_rootfs_customer_data_policy_20260528.md`; the rootfs/data responsibility split in that older note remains useful.
