# MCU release and IR distance session archive

- Topic: `mcu-release-ir-distance-session`
- Source: current Codex session in `<mcu-worktree>`
- Captured at: 2026-07-10 Asia/Hong_Kong
- Last verified: 2026-07-10
- Sanitization: credentials, raw logs, full command output, and private mount details omitted.
- Status: archive candidate; GD32L235 `1.1.36` withdrawn on 2026-07-10

## Scope

This note captures reusable facts from a short MCU release and firmware-inspection session:

- Published `mm32spin023c` firmware to the MCU NAS release root.
- Published `gd32l235` firmware to the MCU NAS release root.
- Confirmed the implemented GD32L235 IR distance valid range from source code.
- Recorded remaining repository and validation risks for follow-up.

## MM32SPIN023C NAS release

- Target: `mm32spin023c`
- Version: `0.4.9`
- Batch id: `20260708-174609`
- NAS release directory: `<mcu-release-nas>/robot/mcu/mm32spin023c_电机/mm32spin023c_firmware_bundle_v0.4.9_20260708-174609`
- Batch manifest: `<mcu-release-nas>/robot/mcu/_batches/20260708-174609/release_batch_manifest.json`
- Status: `published`
- Source digest: `bc1fb0a13077968fcf44401a894da33bcb6d8e554d4f77e217c6b47020a06076`

Validation evidence:

- NAS mount and release root check passed.
- `release-to-nas.sh --targets mm32spin023c --release-root <mcu-release-nas>/robot/mcu --dry-run` passed.
- `release-to-nas.sh --targets mm32spin023c --release-root <mcu-release-nas>/robot/mcu --publish` returned `READY`.
- NAS-side package check returned `[OK] package manifest and checksums are valid`.
- Package generated burn, full erase/burn, and readback verify dry-run scripts.
- Full hex/bin mapped compare reported `diff bytes : 0`.

Artifact facts:

- OTA payload: `mm32spin023c_app.bin`
- OTA size: `22028`
- OTA CRC32: `0x00F8A2E3`
- OTA MD5: `9f8fe2d9a63e5d031a30b44888ed93e6`
- Default programming image: `mm32spin023c_boot_flag_app_merged.hex`
- Factory/full recovery image: `mm32spin023c_flash_full.hex`

Boundary:

- No Git release tag was created or pushed.
- No real board flash/readback validation was performed in this session.

## GD32L235 NAS release and withdrawal

- Target: `gd32l235`
- Version: `1.1.36` withdrawn; current effective baseline is `1.1.35`
- Batch id: `20260709-123446`
- NAS debug directory retained: `<mcu-release-nas>/robot/mcu/gd32l235_设备/调试版本/gd32l235_firmware_bundle_v1.1.36_20260709-123446`
- Withdrawn batch manifest: `<mcu-release-nas>/robot/mcu/_batches/_withdrawn/20260709-123446/release_batch_manifest.json`
- Withdrawal note: `<mcu-release-nas>/robot/mcu/_batches/_withdrawn/20260709-123446/WITHDRAWN.txt`
- Status: `withdrawn`
- Source digest: `6655f25256f081c6bdfeaaa0aa608f24c4e07ee2359a36e50e96a6bb202defab`

Release decision:

- Initial dry-run was blocked because source version `1.1.35` conflicted with existing tag `v1.1.35`.
- `gd32l235/App/bsp.h` was bumped from `APP_FW_VERSION_PATCH 35` to `36`.
- This was a release version metadata change only; it did not change IAP layout, partition boundaries, or runtime logic.

Validation evidence:

- NAS mount and release root check passed.
- `release-to-nas.sh --targets gd32l235 --release-root <mcu-release-nas>/robot/mcu --dry-run` passed after version bump.
- `release-to-nas.sh --targets gd32l235 --release-root <mcu-release-nas>/robot/mcu --publish` returned `READY`.
- Fresh CMake/Ninja build passed.
- `fwtool.py check --scope all` reported build/package PASS.
- Flash and verify dry-run generated OpenOCD commands.
- Local source package check passed.
- NAS-side `sha256sum -c checksums.sha256.txt` passed for all files.
- `git -C gd32l235 diff --check` passed.

Artifact facts:

- OTA payload: `gd32l235_app.bin`
- OTA size: `46284`
- OTA CRC32: `0x9C2DC880`
- OTA MD5: `f357f5f6650799433162f3b2b77e2e6f`
- Merged image: `gd32l235_stage0_stage1_app_merged.bin`
- Full flash image: `gd32l235_flash_full.bin`

Withdrawal update:

- On 2026-07-10, `gd32l235 v1.1.36` was reported as problematic and rolled back locally to `v1.1.35`.
- The 1.1.36 bundle was moved/kept under `调试版本` and must not be treated as the current published production package.
- The active batch record was moved from `_batches/20260709-123446` to `_batches/_withdrawn/20260709-123446`.
- Empty staging directory `.staging/20260709-123446` was removed.
- Local and remote `gd32l235` tags were checked; `v1.1.36` did not exist.
- `gd32l235` working tree was checked out at tag `v1.1.35`, commit `555eded00292581755cdbad6baad343066f46a6a`.

Boundary:

- No Git release tag was created or pushed; `v1.1.36` did not exist at withdrawal close.
- No source commit was made for `1.1.36`.
- `gd32l235/App/bsp.h` is no longer modified after rollback; version macros resolve to `1.1.35`.
- The MCU root no longer reports `M gd32l235` after rollback to the root gitlink commit.
- No real board flash/readback validation was performed in this session.
- GD32 `fwtool.py check --scope package` directly against the timestamped NAS directory fails because the checker expects a same-name zip beside the directory. The NAS release itself publishes the package directory; NAS directory contents were independently verified by `checksums.sha256.txt`.

## IR distance finding

Implemented GD32L235 IR distance range comes from `gd32l235/App/ir_detect_dist.c`.

Relevant constants:

- `IR_ADC_25CM = 11`
- `IR_ADC_8CM = 1278`
- `IR_DISTANCE_INVALID_CM = 255`
- Normal conversion: `8 + 1155 / (adc + 56)`

Conclusion:

- Effective calibrated range: `8cm..25cm`.
- If ADC is below the 25cm threshold, firmware returns `255`, meaning invalid or over range.
- If ADC is above the 8cm threshold, firmware returns `5`, meaning near-range saturation.
- Normal in-range return value is in centimeters.

Protocol mismatch to track:

- `Docs/串口通信协议规范.md` describes `CMD_IR_DISTANCE_DATA (0x41)` as `Format V1` with `distance_mm` and validity fields.
- Current `bsp.c` implementation sends two bytes and places the centimeter distance in `data[1]`.
- This documentation/implementation mismatch should be resolved before treating the protocol document as authoritative.

## Working tree state at archive time

Root repository:

- Untracked local reference/material paths remain: `CW221X/`, `gd32l235_dev/`, `gd32l235_reconfiguration/`, `mm32_ota_retry.log`

`gd32l235` subrepo:

- Detached at `v1.1.35`, commit `555eded00292581755cdbad6baad343066f46a6a`
- No tracked working-tree changes after rollback

## Follow-up candidates

- Do not use `gd32l235 v1.1.36` as a production release candidate unless the reported issue is root-caused and a new release decision is made.
- If a replacement release is needed, build from the accepted fix and use the next approved version instead of reusing the withdrawn `1.1.36` published status.
- Decide whether NAS publishing should also copy the source package zip for GD32 packages, or whether GD32 package checker should support timestamped NAS package directories without adjacent zip.
- Align `CMD_IR_DISTANCE_DATA` documentation with the current two-byte cm payload or update firmware to match documented `Format V1`.
