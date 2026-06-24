# PCR02 Vehicle OTA Orchestration

Date: 2026-06-06
Status: current orchestration policy

## Background

PCR02 发布链路不只包含 SoC 固件。整车 OTA 包需要同时约束 SoC OTA、主板 MCU、轮毂电机 MCU，以及 NAS 上的已发布制品来源。该结论来自近期发布脚本扩展、迁移/常规发布流讨论，以及 IMSSV05C13 SDK 迁移归档中已经沉淀的 `firmware-release-tools`、`ota-packager`、`vehicle-ota` 边界。

## Current Conclusion

- Vehicle OTA consumes prebuilt artifacts; it does not build MCU firmware inside the vehicle OTA step.
- SoC OTA is produced by the PCR02 SoC release flow.
- Mainboard MCU package is resolved from NAS and normalized as `mcu.bin`.
- Motor MCU package is resolved from NAS and normalized as `wheel_motor.bin`.
- The final package is assembled by the OTA packager with `guide.toml`, package manifest, and hash records.
- The vehicle OTA input manifest must record artifact path, version, size, and sha256 for SoC, mainboard MCU, and motor MCU.
- Production release must not silently float to an unreviewed "latest" MCU package. If latest resolution is used, the resolved path and hash become the reviewed release input.

## Implementation Boundary

The current logical boundaries are:

- `firmware-release-tools`: locate and resolve published MCU/SOC artifacts from release roots.
- `ota-packager`: assemble package payload and metadata.
- `vehicle-ota`: bind SoC OTA plus MCU artifacts into one release input set.
- `build.sh release-dual`: publish production/debug SoC artifacts and, when requested, trigger higher-level packaging.

Vehicle OTA tooling should fail closed when a required artifact, version, or checksum is missing. A dry-run may report candidate inputs, but a production package must carry pinned resolved inputs.

## Release Flow Mapping

`migration`:

- Used for old production layout to new layout migration.
- SoC package may contain rootfs and whole `ubia` replacement.
- `/data` preservation is not guaranteed because `ubia` is rewritten.
- Vehicle OTA may include MCU artifacts, but the migration meaning is owned by the SoC layout transition.

`regular`:

- Used after devices have completed migration.
- SoC package must not rebuild or rewrite whole `ubia`.
- `/factory` and `/data` must not be upgraded by default.
- Vehicle OTA may still include MCU artifacts when MCU versions need to move.

## Validation Checklist

- Check `guide.toml` contains expected SoC/MCU/motor sections and versions.
- Check `vehicle-ota-inputs.json` or equivalent manifest contains all resolved input paths and sha256 values.
- Check `SHA256SUMS.txt` covers the final package and major inputs.
- Check duplicate-package handling does not hide a changed MCU artifact.
- Check NAS publish layout keeps production and debug outputs separated.
- For production, check the resolved MCU package is an approved release, not an arbitrary build directory.

## Risks

- If "latest" is resolved late and not pinned, two package builds with the same command can produce different vehicle OTA contents.
- If SoC migration and regular flows are mixed, a regular release can accidentally rewrite `/factory` or `/data`.
- If the vehicle OTA manifest omits hashes, field failures cannot be traced back to exact MCU/SOC inputs.

## Provenance

- Current session archive audit on 2026-06-06.
- Prior PCR02 release discussions about `release-dual`, `migration`, `regular`, production/debug publish paths, and vehicle OTA boundaries.
- Existing archive: `source-audit/pcr02_imssv05c13_sdk_migration_plan_20260530.md`.

## Follow-up

- Keep vehicle OTA packaging tests separate from SoC-only publish tests.
- Add a release gate that rejects production vehicle OTA packages without a complete input manifest and sha256 coverage.
