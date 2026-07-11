# Codex archive final body coverage 2026-07-11

## 摘要

本记录承接 `codex-archive-remaining-blockers-scan-20260711` 和三个只读 subagent 审计结果，对旧 Codex archive 剩余 7 个非 `index.md` / `README.md` 正文做终态 coverage 分流。

本批边界：

- 不写 `~/.codex/memories`。
- 不提升 active rule、current fact、owner decision 或 release approval。
- 不修改源项目。
- 不复制 raw session、完整日志、core、cache、binary、NAS release artifact、WiFi 凭据或私有路径。
- 只把仍有长期价值的内容迁移为 archive-only project record 或 coverage/tombstone manifest。

结构化台账：`artifacts/manifests/codex-archive-final-body-coverage-20260711.jsonl`。

## 新增 canonical / coverage targets

| Target | 覆盖内容 |
| --- | --- |
| `projects/pcr02/archive/engineering-archive/pcr02/media-timing/pcr02_media_monotonic_pts_dvr_mp4_20260630.md` | PCR02 MI_SYS monotonic PTS 对 DVR/MP4 相对时间线、wall-clock 分工和 first-sample rebase 的影响。 |
| `projects/pcr02/archive/debug/2026-06-23-pcr02-core-gdb-triage.md` | PCR02 core/GDB BuildID 配对、MotorTemperature `context_` 空指针、NaviCtrl/ObstacleMap 低置信边界。 |
| `projects/pcr02/archive/reports/2026-06-30-dvr-protocol-sync-build-fix.md` | DVR 协议手工同步、`DeviceType` 18..22、oneof 27..31 和 sensor include 修复。 |
| `projects/pcr02/archive/engineering-archive/pcr02/ota-release/pcr02_regular_ota_customer_partition_guard_20260625.md` | regular OTA 不能误排除 `customer`、`SStarOtaLayout.txt` 证据和 protected partition gate。 |
| `projects/pcr02/archive/debug/2026-07-08-pcr02-irlight-player-wifi-debug-summary.md` | 2026-07-08 PCR02 IR light ColorToGray、player start/wait、WiFi scan 和 `wifi_detach` 结论。 |
| `projects/mcu/archive/2026-06-29-mcu-release-nas-guard-governance.md` | MCU flash guard、NAS release、tag/gitlink 和 HC32 OpenOCD 证据边界。 |
| `projects/mcu/archive/2026-07-10-mcu-release-ir-distance-session.md` | 2026-07-08 `mm32spin023c` 0.4.9 NAS 发布事实的既有覆盖。 |
| `artifacts/manifests/codex-archive-final-body-coverage-20260711.md` | 2026-05-10 Codex V2 日总结的 governance/file-level coverage，以及本批 7 个旧正文最终分流。 |

## Disposition summary

| Disposition | Count | 说明 |
| --- | ---: | --- |
| `extract-first-migrated` | 5 | PCR02 media/core/DVR、PCR02 2026-07-08 debug split、MCU release guard 已落到项目归档。 |
| `partial-coverage-extract-delta` | 1 | PCR02 OTA/customer 主策略已有覆盖，本批补 delta 归档。 |
| `coverage-audit` | 1 | 2026-05-10 Codex V2 日总结已由当前 Codex/Hub governance 与本 coverage manifest 覆盖。 |

## Subagent audit integration

| Subagent | Scope | 结论使用方式 |
| --- | --- | --- |
| `019f4cec-70fd-7360-b598-3c358ba58009` | PCR02 media/core/DVR/OTA | 确认 4 个 PCR02 正文不能直接删，必须 extract-first 或补 delta coverage。 |
| `019f4cec-719d-70d2-a6d6-163a8edfedf2` | MCU release guard 与 2026-07-08 工程日报 | 确认 6/29 MCU 必须 extract-first；7/8 日报必须拆分 PCR02/WiFi/player。 |
| `019f4cec-7271-7370-afc7-4813869db32d` | Codex 日报与 corpus gate | 确认 2026-05-10 日报需要 file-level coverage，并指出 corpus deletion readiness 在删除前仍为 false。 |

## Codex V2 日总结 coverage

`daily-summary/20260510-094820-codex-v2-knowledge-archive-summary.md` 的可保留事实是历史边界，不是当前规则提升：

- `~/.codex` 是运行目录，不是长期知识库。
- `src/codex-home/` 是 Codex Home 资产源，不承载长期知识归档。
- 旧 `docs/archive/<topic>/` 和 `archive-note` 是 2026-05-10 的历史入口；当前长期知识控制面已转为 Knowledge Hub。
- 旧 session-wrap `CARE-20260710-019` 曾引用该日报作为覆盖锚点；本记录接替该 file-level coverage 锚点。

当前覆盖入口：

- `AGENTS.md`
- `governance/path-routing.md`
- `domains/codex/archive/codex-archive.ref.md`
- `domains/codex/archive/codex-archive/README.md`
- `artifacts/manifests/codex-archive-final-body-coverage-20260711.md`

## Delete gate

本记录将 7 个剩余正文推进到 `delete_ready=true`，前提是删除执行批次同时满足：

- 有当前会话用户授权或 registry authorization row，scope 精确到这 7 个旧正文。
- 有 tombstone execution manifest，逐文件记录 `source_path`、`source_sha256`、line count、size、covered_by、delete_reason 和 rollback。
- 删除只移除旧正文，不删除 topic `index.md`，不删除 topic 目录，不删除旧 Codex archive corpus。
- 删除后更新 topic index、session-wrap index 的旧 coverage 锚点、registry item、by-* 索引，并运行 JSONL、搜索、knowledge-check 和 diff 验证。

## Remaining blocker after this coverage

本 coverage 落地后，旧 Codex archive 剩余 7 个正文不再被内容覆盖阻塞；是否可以删除旧正文取决于独立 deletion execution 是否完成。本文不授权整库删除。
