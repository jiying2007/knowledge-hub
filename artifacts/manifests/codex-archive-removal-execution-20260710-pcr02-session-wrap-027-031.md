# Codex archive PCR02 session-wrap 删除执行批次 2026-07-10

## Scope

本批完成 5 个 PCR02 相关 `session-wrap` 旧正文的 extract-first 后删除。

授权 ID：`auth-20260710-codex-archive-delete-pcr02-session-wrap-027-031`

恢复锚点：`db07bd4839016d76f37218cd2b72857ed8575d48`

## Canonical 目标

- `projects/pcr02/archive/debug/2026-05-15-pcr02-sigbus-core-debug-tools-history.md`
- `projects/pcr02/archive/engineering-archive/pcr02/session/pcr02_build_gros_hdi_history_20260517_20260521.md`

## 删除清单

| CARE | Old source | SHA256 | 覆盖目标 |
| --- | --- | --- | --- |
| `CARE-20260710-027` | `session-wrap/20260515-142200-session-wrap-crash-debug-tools.md` | `8dde26d0cd2f20b08e82d3c6b2dfb6654c2b52633a9aea23171ebcf77240d862` | `projects/pcr02/archive/debug/2026-05-15-pcr02-sigbus-core-debug-tools-history.md` |
| `CARE-20260710-028` | `session-wrap/20260515-154658-session-wrap-core-debug-and-busybox-tools.md` | `d4e13137ee5d6a9b280706ce9a40dc773ff82e8c655fcf4110add2edd2b916f9` | `projects/pcr02/archive/debug/2026-05-15-pcr02-sigbus-core-debug-tools-history.md` |
| `CARE-20260710-029` | `session-wrap/20260517-154205-pcr02-gros-session-wrap.md` | `680438b0e528a0ccd7392e3b698983cfcec5cc1fefc0c27220dbd2783c13d6b4` | `projects/pcr02/archive/engineering-archive/pcr02/session/pcr02_build_gros_hdi_history_20260517_20260521.md` |
| `CARE-20260710-030` | `session-wrap/20260518-223733-pcr02-ssc305-session-wrap.md` | `46a823463ea651802830f2c88eb29a3dfa6f4f1a96941633a2df43974d8d632f` | `projects/pcr02/archive/engineering-archive/pcr02/session/pcr02_build_gros_hdi_history_20260517_20260521.md` |
| `CARE-20260710-031` | `session-wrap/20260521-091035-session-wrap-hdi-warning-zero.md` | `e33675294c1a583f4e51b787b71df19f475d51292beb65e29e0c1b95e77b14c9` | `projects/pcr02/archive/engineering-archive/pcr02/session/pcr02_build_gros_hdi_history_20260517_20260521.md` |

## Boundaries

- 不删除剩余 `session-wrap`：llm_tools、GD32/MCU、Knowledge Base、WeChat final handoff、GD32L235 app boot。
- 不删除 `session-wrap` topic 或旧 archive corpus。
- 不写 memory，不提升 active，不生成 owner decision。
- 不改源项目，不 commit，不 push。

## Validation Plan

```bash
rtk jq -c . artifacts/manifests/codex-archive-removal-execution-20260710-pcr02-session-wrap-027-031.jsonl
rtk bash -lc "test ! -e domains/codex/archive/codex-archive/session-wrap/20260515-142200-session-wrap-crash-debug-tools.md && test ! -e domains/codex/archive/codex-archive/session-wrap/20260515-154658-session-wrap-core-debug-and-busybox-tools.md && test ! -e domains/codex/archive/codex-archive/session-wrap/20260517-154205-pcr02-gros-session-wrap.md && test ! -e domains/codex/archive/codex-archive/session-wrap/20260518-223733-pcr02-ssc305-session-wrap.md && test ! -e domains/codex/archive/codex-archive/session-wrap/20260521-091035-session-wrap-hdi-warning-zero.md"
rtk bash tools/knowledge-search.sh "PCR02 SIGBUS core debug tools"
rtk bash tools/knowledge-search.sh "PCR02 GROS SSC305 HDI warning zero"
rtk bash tools/knowledge-check.sh --dry-run
rtk git diff --check
```
