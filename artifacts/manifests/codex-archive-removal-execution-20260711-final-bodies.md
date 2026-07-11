# Codex archive final bodies 删除执行批次 2026-07-11

## Scope

本批在 `codex-archive-final-body-coverage-20260711` 覆盖落地后，删除旧 Codex archive 剩余 7 个非 `index.md` / `README.md` 正文。

授权 ID：`auth-20260711-codex-archive-delete-final-bodies`

恢复锚点：`db07bd4839016d76f37218cd2b72857ed8575d48`

## Canonical / coverage 目标

- `projects/pcr02/archive/engineering-archive/pcr02/media-timing/pcr02_media_monotonic_pts_dvr_mp4_20260630.md`
- `projects/pcr02/archive/debug/2026-06-23-pcr02-core-gdb-triage.md`
- `projects/pcr02/archive/reports/2026-06-30-dvr-protocol-sync-build-fix.md`
- `projects/pcr02/archive/engineering-archive/pcr02/ota-release/pcr02_regular_ota_customer_partition_guard_20260625.md`
- `projects/pcr02/archive/debug/2026-07-08-pcr02-irlight-player-wifi-debug-summary.md`
- `projects/mcu/archive/2026-06-29-mcu-release-nas-guard-governance.md`
- `projects/mcu/archive/2026-07-10-mcu-release-ir-distance-session.md`
- `artifacts/manifests/codex-archive-final-body-coverage-20260711.md`

## 删除清单

| CARE | Old source | SHA256 | 覆盖目标 |
| --- | --- | --- | --- |
| `CARE-20260711-041` | `research-notes/20260630-103933-media-monotonic-pts-mp4-impact.md` | `136a6f155823f5f201b6da7f97812a294bfbed5f33762b78e7a3716806f561b0` | `projects/pcr02/archive/engineering-archive/pcr02/media-timing/pcr02_media_monotonic_pts_dvr_mp4_20260630.md` |
| `CARE-20260711-042` | `debug-notes/20260623-075032-pcr02-core-gdb-triage.md` | `88d4a2ab2ba7fc8a2039870f0d4135d545e90594709751b5ce6c179638b79c17` | `projects/pcr02/archive/debug/2026-06-23-pcr02-core-gdb-triage.md` |
| `CARE-20260711-043` | `debug-notes/20260630-034504-pcr02-dvr-protocol-sync-build-fix.md` | `e96038f4e2da3c46baa5ac26d23db4d9a8276c01d3c1325b63f66e21854db45b` | `projects/pcr02/archive/reports/2026-06-30-dvr-protocol-sync-build-fix.md` |
| `CARE-20260711-044` | `daily-summary/20260510-094820-codex-v2-knowledge-archive-summary.md` | `345f5204c6a281f7b5c1f6ed91b69b3403e911af9da7f5d04e6d860b6946c3ff` | `artifacts/manifests/codex-archive-final-body-coverage-20260711.md` |
| `CARE-20260711-045` | `daily-summary/20260708-211900-engineering-archive-summary.md` | `07d43e00e0dbfc5b1aeb676251c1919527dab7f2bb9e412243c6be5a2ddf3936` | `projects/mcu/archive/2026-07-10-mcu-release-ir-distance-session.md`; `projects/pcr02/archive/debug/2026-07-08-pcr02-irlight-player-wifi-debug-summary.md` |
| `CARE-20260711-046` | `release-governance/20260625-124521-pcr02-ota-customer-ubifs-partition-preserve.md` | `eeaa441b617827e4377ebe0ff6f88e413c4f78bb366ffc1e3bc93c17797e6b71` | `projects/pcr02/archive/engineering-archive/pcr02/ota-release/pcr02_regular_ota_customer_partition_guard_20260625.md` |
| `CARE-20260711-047` | `release-governance/20260629-040442-mcu-release-nas-guard-governance.md` | `fa9828b56e3dbc54689551b4a59dd5eecc3cce8b510065f2ee6cd61a8cfffef7` | `projects/mcu/archive/2026-06-29-mcu-release-nas-guard-governance.md` |

## Boundaries

- 删除范围只限上述 7 个旧正文。
- 不删除任何 topic `index.md`。
- 不删除 topic 目录。
- 不删除旧 Codex archive corpus。
- 不写 memory，不提升 active，不生成 owner decision。
- 不改源项目，不 commit，不 push。

## Validation Plan

```bash
rtk jq -c . artifacts/manifests/codex-archive-final-body-coverage-20260711.jsonl artifacts/manifests/codex-archive-removal-execution-20260711-final-bodies.jsonl
rtk bash -lc "test ! -e domains/codex/archive/codex-archive/research-notes/20260630-103933-media-monotonic-pts-mp4-impact.md && test ! -e domains/codex/archive/codex-archive/debug-notes/20260623-075032-pcr02-core-gdb-triage.md && test ! -e domains/codex/archive/codex-archive/debug-notes/20260630-034504-pcr02-dvr-protocol-sync-build-fix.md && test ! -e domains/codex/archive/codex-archive/daily-summary/20260510-094820-codex-v2-knowledge-archive-summary.md && test ! -e domains/codex/archive/codex-archive/daily-summary/20260708-211900-engineering-archive-summary.md && test ! -e domains/codex/archive/codex-archive/release-governance/20260625-124521-pcr02-ota-customer-ubifs-partition-preserve.md && test ! -e domains/codex/archive/codex-archive/release-governance/20260629-040442-mcu-release-nas-guard-governance.md"
rtk bash tools/knowledge-search.sh "PCR02 media monotonic PTS"
rtk bash tools/knowledge-search.sh "PCR02 core GDB triage"
rtk bash tools/knowledge-search.sh "DVR 协议手工同步"
rtk bash tools/knowledge-search.sh "PCR02 IR light wifi_detach"
rtk bash tools/knowledge-search.sh "MCU flash guard NAS"
rtk bash tools/knowledge-search.sh "Codex archive final body coverage"
rtk bash tools/knowledge-check.sh --dry-run
rtk git diff --check
```
