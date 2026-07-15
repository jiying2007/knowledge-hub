# PCR02 regular OTA customer 分区 guard 归档

Date: 2026-06-25
Captured: 2026-07-11
Status: archive-only migrated coverage

## 边界

本文从旧 Codex archive `release-governance/20260625-124521-pcr02-ota-customer-ubifs-partition-preserve.md` 抽取。它补充 2026-06-25/28 关于 regular OTA、`customer`、protected partition 和版本哨兵的排障语境。当前有效 release/storage 口径仍以 `decision-index.md`、`pcr02_regular_ota_preserve_partitions_20260613.md` 和 2026-05-29 customer SquashFS migration 归档为准。

## 保留结论

- 对 PCR02 当时 target，regular OTA 不能排除 `customer`。`customer` 承载 `/customer` 静态资源和版本信息，排除后会出现 OTA 成功但版本仍旧的现象。
- `SStarOtaLayout.txt` 是判断实际升级分区的权威证据，高层 release flow 名称不足以证明升级了哪些分区。
- regular OTA 应保护 `rootfs`、`ubia`、`ota`、`factory`、`data`，但当发布目标是 customer 内容更新时，不能把 `customer` 也误排除。
- migration 用于首次迁移或布局切换；regular 用于后续常规升级，保留现场数据和维护分区。
- `/customer`、`/factory`、`/data`、`/ota` 的策略不能混为一谈：`/customer` 可作为静态资源升级内容，`/factory` 是设备个体/产测信息，`/data` 是运行态数据，`/ota` 是升级状态和维护分区。

## 推荐检查顺序

1. 比较 release bundle 中的 `README.txt`、`package_manifest.json`、`vehicle-ota-inputs.json`、`SStarOtaLayout.txt`。
2. 检查 image config，例如 `SourceCode/project/image/configs/general/spinand_MX35_512M.squashfs.partition.config` 和 debug customer overlay 相关 partition config。
3. 检查 runtime OTA script，例如 `SourceCode/project/image/ota_start.sh`。
4. 做 regular self-check，确认默认分区策略不包含 `ota/factory/data`，显式请求 protected partition 时应快速失败。

## 与现有归档的关系

- `pcr02_regular_ota_preserve_partitions_20260613.md` 已覆盖 post-migration regular OTA 应保护 `/factory`、`/ota`、`/data` 且不重写 `ubia`。
- `pcr02-ota-ubia-resize-customer-squashfs-20260529/` 已覆盖 migration、customer SquashFS、`SStarOtaLayout` 等主策略。
- 本文只补上“误排除 customer 导致看起来没升级”和 protected partition gate 的 file-level 覆盖，不提升为新的 current decision。

## 迁移记录

- Old source: `domains/codex/archive/codex-archive/release-governance/20260625-124521-pcr02-ota-customer-ubifs-partition-preserve.md`
- Old source SHA256: `eeaa441b617827e4377ebe0ff6f88e413c4f78bb366ffc1e3bc93c17797e6b71`
- Old source size: `3387` bytes
- Old source lines: `70`
- Final coverage row: `artifacts/manifests/codex-archive-final-body-coverage-20260711.jsonl#CAFC-20260711-006`
- Tombstone: `artifacts/manifests/codex-archive-removal-execution-20260711-final-bodies.jsonl#CARE-20260711-046`

## 风险

- 后续 profile 或 partition config 改动后，必须重新核对 `SStarOtaLayout.txt`。
- 涉及客户现场数据时，必须先明确 migration/regular 语义、回滚路径和 protected partition 自检。
