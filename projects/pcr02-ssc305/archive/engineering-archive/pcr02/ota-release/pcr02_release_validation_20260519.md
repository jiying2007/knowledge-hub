# PCR02 SSC305 发布验证历史记录 2026-05-19

## 摘要

本文从旧 Codex archive `memory-curation` 选择性迁移而来，保留 2026-05-19 PCR02/SSC305 发布验证会话中的长期可追溯事实。本文是 archive-only 历史记录，不代表当前 SOC/MCU 版本、当前 OTA 包或当前发布状态。

## 历史验证命令

旧 memory-curation 记录的历史命令：

```bash
rtk ./build.sh release --profile ap6303bh_512m_v20 --sync-sources --publish-soc --force-vehicle-ota
```

旧记录显示该命令当时退出码为 0。该结果只证明 2026-05-19 会话中的一次发布链路通过，不替代当前发布验证。

## 历史版本线索

| Component | Historical version |
| --- | --- |
| SOC | `1.1.8` |
| Mainboard MCU | `1.1.18` |
| Motor MCU | `0.0.8` |

## 历史发布边界

- 旧记录使用 `--sync-sources`，说明发布前同步源状态是当时流程的一部分。
- 旧记录包含 SOC OTA 发布路径和整车 OTA 选项；路径和 NAS 细节只保留为 provenance，不在本文展开为当前发布入口。
- SOC OTA 默认分区、整车 OTA 从 NAS 读取 MCU 版本等结论只能作为历史线索；当前发布必须使用当前 `build.sh`、当前 layout、当前 NAS 和当前签核记录重新验证。
- 本文不保存 OTA 包、release binary、完整日志、NAS 凭据、token、cookie、private key 或 raw session。

## 迁移边界

| Source | SHA256 | 行数 | 字节 | 处置 |
| --- | --- | ---: | ---: | --- |
| `domains/codex/archive/codex-archive/memory-curation/20260519-221757-pcr02-ssc305-post-release-memory-review.md` | `fc6a3c698d7d1937b8977da93d043d467210beacf3fc3f163b723dfd6bf92b32` | 78 | 3889 | extract-first migrated |

## 关联覆盖

- `projects/pcr02-ssc305/archive/engineering-archive/pcr02/session/pcr02_build_gros_hdi_history_20260517_20260521.md`
- `projects/pcr02-ssc305/archive/engineering-archive/pcr02/ota-release/pcr02_sdk_ota_release_design_20260528.md`
- `projects/pcr02-ssc305/archive/engineering-archive/pcr02/source-audit/pcr02_imssv05c13_sdk_migration_plan_20260530.md`
- `artifacts/manifests/codex-archive-memory-curation-coverage-20260711.md`

## 风险

- 当前发布状态、OTA layout、NAS 路径和 MCU 版本必须重新从当前源项目与发布账本确认。
- 本记录不构成 release approval、owner decision、active runbook 或 current project fact。
