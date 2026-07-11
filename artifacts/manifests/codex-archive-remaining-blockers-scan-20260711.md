# Codex archive remaining blockers scan 2026-07-11

## 摘要

本记录在 `memory-curation` topic 删除收口后扫描 `domains/codex/archive/codex-archive` 剩余正文。结论：

- `memory-curation` topic 已只剩 tombstone `index.md`。
- 旧 Codex archive corpus 仍有 7 个非 index/README 正文。
- 因这些正文尚未逐文件完成 extract-first / coverage / tombstone，不允许整库删除。

结构化台账：`artifacts/manifests/codex-archive-remaining-blockers-scan-20260711.jsonl`。

## Remaining non-index bodies

| Path | Classification | Blocker |
| --- | --- | --- |
| `research-notes/20260630-103933-media-monotonic-pts-mp4-impact.md` | `extract-first-required` | PCR02 media/DVR/MP4 时间基准分析，应迁移到 project archive 或证明已有覆盖。 |
| `debug-notes/20260623-075032-pcr02-core-gdb-triage.md` | `extract-first-required` | PCR02 core/GDB 离线排障方法与崩溃证据，应迁移到 project debug archive 或证明已有覆盖。 |
| `debug-notes/20260630-034504-pcr02-dvr-protocol-sync-build-fix.md` | `extract-first-required` | DVR 协议手工同步和 include 修复，应迁移到 PCR02 project archive 或证明已有覆盖。 |
| `daily-summary/20260510-094820-codex-v2-knowledge-archive-summary.md` | `coverage-check-required` | Codex Home v2 / archive-note 历史日报，需确认是否已有 Codex governance 覆盖。 |
| `daily-summary/20260708-211900-engineering-archive-summary.md` | `split-or-coverage-required` | 混合 MCU release、PCR02 debug、WiFi、player 同步等多主题摘要，不能直接整篇删除。 |
| `release-governance/20260625-124521-pcr02-ota-customer-ubifs-partition-preserve.md` | `coverage-check-required` | PCR02 OTA/customer/UBIFS 分区策略，需确认是否由 PCR02 OTA archive 完整覆盖。 |
| `release-governance/20260629-040442-mcu-release-nas-guard-governance.md` | `extract-first-required` | MCU flash guard、NAS release、tag/gitlink 发布治理，需迁移到 MCU/release archive 或证明已有覆盖。 |

## Delete gate

旧 Codex archive corpus 仍为 `delete_ready=false`。后续整库删除前至少需要：

- 对上述 7 个正文逐文件完成 extract-first 或 coverage-check。
- 更新对应 topic index、registry/items、by-* indexes。
- 写入授权账本、tombstone execution manifest 和 rollback。
- 只在所有 topic index 均为 tombstone/index-only 后，才讨论 corpus 目录级删除。

## Validation evidence

已执行：

- `rtk rg --files domains/codex/archive/codex-archive`
- `rtk bash tools/knowledge-check.sh --dry-run`
- `rtk bash tools/knowledge-search.sh "Codex archive memory-curation coverage"`

本记录不删除任何剩余正文，不提升 active，不写 memory。
