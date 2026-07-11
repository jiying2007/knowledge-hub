# Codex archive extract-first 预检 2026-07-10

## 摘要

本批承接 `codex-archive-removal-preflight-20260710` 的阻塞项，针对 `session-wrap`、`memory-curation` 和 `Codex 长期省 Token` 例外文件做 file-level extract-first 分流。

本预检本身不删除旧 archive 正文；后续独立删除执行批次已删除部分 covered/provenance-only 条目，并保留 tombstone。全流程仍不写 `~/.codex/memories`，不提升 active，不把 session wrap 或 memory candidate 直接改写为当前规则。

结构化台账：`artifacts/manifests/codex-archive-extract-first-preflight-20260710.jsonl`。

## 本批分流

| 范围 | 结论 |
| --- | --- |
| `session-wrap/20260602-132025-codex-adk-hardcut-session-wrap.md` | 已迁移为 `artifacts/manifests/codex-adk-hardcut-source-to-live-audit-20260710.md` coverage audit；live Codex 资产已覆盖核心 source-to-live 规则，旧正文已按 `CARE-20260710-013` 删除并保留 tombstone。 |
| `session-wrap/20260627-230744-knowledge-hub-final-hardcut-session-wrap.md` | 已压实为 `artifacts/manifests/codex-knowledge-hub-final-hardcut-tombstone-audit-20260710.md` tombstone-only audit；已有 Knowledge Hub 终态、路径和 owner/review 边界覆盖，旧正文已按 `CARE-20260710-014` 删除并保留 tombstone。 |
| `session-wrap/20260526-162109-pcr02-session-wrap-20260526-customer-ro-sd-upgrade.md` | 已抽取到 PCR02 历史 session 归档；旧正文已按 `CARE-20260710-015` 删除并保留 tombstone，不能声明当前 release truth。 |
| `session-wrap/20260524-231443-codex-session-wrap-20260524-openai-local-runtime-boundary.md` | 已抽取到 `archive-only + freshness-required` 治理记录；旧正文已按 `CARE-20260710-016` 删除并保留 tombstone，当前官方资料仍需重新 freshness review。 |
| `session-wrap/20260518-223626-mcu-session-wrap-firmware-release-nas.md` | 已抽取到 `projects/firmware-release-tools/archive/release/2026-05-18-nas-release-sync-session.md`；旧正文已按 `CARE-20260710-017` 删除并保留 tombstone，保留 NAS 发布同步历史链路，不声明当前 MCU 发布基线。 |
| `memory-curation/20260602-132130-codex-adk-hardcut-memory-curation.md` | 已进入 `artifacts/manifests/codex-archive-memory-curation-file-level-audit-20260710.md`；只进候选审计，不写 memory。 |
| `memory-curation/20260627-230744-knowledge-hub-final-hardcut-memory-curation.md` | 已进入 file-level audit；结论为 `tombstone-only`，已有治理路径覆盖，删除前仍需授权、hash/covered_by/rollback。 |
| `memory-curation/20260707-codex-usage-records-memory-curation.md` | 已进入 file-level audit；候选混有 project-specific 与低置信项，必须逐条 owner review。 |
| `diag-architecture/20260511-112520-codex-token-optimization-roadmap.md` | 已迁移为 `artifacts/manifests/codex-token-efficiency-roadmap-coverage-20260710.md` coverage audit；后续已按授权删除旧正文并保留 tombstone，不提升 active。 |
| `session-wrap/20260510-000000-diag-v4-hybrid-refcount-session-wrap.md` | 已由 PCR02 Diag V4 decision 与 archive plan 覆盖；旧正文已按 `CARE-20260710-018` 删除并保留 tombstone。 |
| `session-wrap/20260510-135300-session-wrap.md` | 已由 Codex V2 daily summary、memory-curation 与当前 no-memory-write 路由覆盖；旧正文已按 `CARE-20260710-019` 删除并保留 tombstone。 |
| `session-wrap/20260510-150728-session-wrap.md` | context handoff 已由当前工作流覆盖，bwrap 版本只作旧本机 provenance；旧正文已按 `CARE-20260710-020` 删除并保留 tombstone。 |
| `session-wrap/20260511-104901-session-wrap.md` | usage TUI 已由 token efficiency coverage 与 `codex-usage-telemetry` 覆盖；旧正文已按 `CARE-20260710-021` 删除并保留 tombstone。 |
| `session-wrap/20260511-132348-session-wrap.md` | token/context efficiency 核心结论已由 coverage audit 覆盖；旧正文已按 `CARE-20260710-022` 删除并保留 tombstone。 |
| `session-wrap/20260523-082158-wechat-absorption.md` | 被保留的最终 `20260523-135801-wechat-all-cleared-handoff.md` 覆盖；旧正文已按 `CARE-20260710-023` 删除并保留 tombstone。 |
| `session-wrap/20260523-085953-wechat-p0-batches.md` | 被保留的最终 `20260523-135801-wechat-all-cleared-handoff.md` 覆盖；旧正文已按 `CARE-20260710-024` 删除并保留 tombstone。 |
| `session-wrap/20260523-101841-wechat-p0-context-handoff.md` | 被保留的最终 `20260523-135801-wechat-all-cleared-handoff.md` 覆盖；旧正文已按 `CARE-20260710-025` 删除并保留 tombstone。 |
| `session-wrap/20260523-112927-context-compress-handoff-wechat-p0-after-006.md` | 被保留的最终 `20260523-135801-wechat-all-cleared-handoff.md` 覆盖；旧正文已按 `CARE-20260710-026` 删除并保留 tombstone。 |

## 不变边界

- topic/corpus 级 `delete_ready=false` 仍然保持；只有已登记授权和 tombstone 的 file-level 条目可删除。
- `memory-candidate-report` 不是 memory 写入批准；不得写 `~/.codex/memories`。
- `extract-first` 只是确定后续迁移方向，不代表正文已迁移完成。
- `covered-removal` 也必须等独立删除执行 manifest、source hash、tombstone、rollback 和验证命令闭合。

## 下一批建议

1. 已覆盖 session-wrap 旧正文已完成两批 file-level 删除和 tombstone：`CARE-20260710-013..017`、`CARE-20260710-018..026`。后续继续处理 session-wrap 里尚未迁移的高信号文件，优先做 file-level extract-first。
2. `memory-curation` 三篇代表文件已进入 file-level audit；后续继续分流剩余 memory-curation 高信号文件，或把已确认噪音项放入未来 tombstone 批次，但仍不得写 memory 或整 topic 删除。
3. `Codex 长期省 Token` 已补 coverage/audit 记录；后续只处理仍未覆盖的结构化代码导航 PoC 和长期 usage 时序候选，不把旧路线图直接提升 active。
4. PCR02 /customer ro SD upgrade 已迁移到 `projects/pcr02/archive/engineering-archive/pcr02/session/pcr02_customer_ro_sd_upgrade_20260526.md`；删除旧正文仍需另批授权、tombstone 和 rollback。
5. OpenAI local runtime boundary 已迁移到 `artifacts/manifests/codex-openai-local-runtime-boundary-20260524.md`；如要提升为当前 Codex workflow，必须另做官方资料 freshness review 和 source-to-live 验证。
6. MCU NAS 发布同步历史会话已迁移到 `projects/firmware-release-tools/archive/release/2026-05-18-nas-release-sync-session.md`；后续若要提升为 current runbook，必须基于当前 `firmware-release-tools` 源仓重新验证。

## 验证计划

```bash
rtk jq -c . artifacts/manifests/codex-archive-extract-first-preflight-20260710.jsonl
rtk bash ~/knowledge-hub/tools/knowledge-search.sh "Codex archive extract-first 预检"
rtk rg -n "(?i)(password|token|cookie|private[_ -]?key|secret)\\s*[:=]" artifacts/manifests/codex-archive-extract-first-preflight-20260710.md artifacts/manifests/codex-archive-extract-first-preflight-20260710.jsonl
rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run
```
