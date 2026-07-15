---
id: codex-archive-migration-preflight-20260709
title: Codex archive 迁移预检批次 2026-07-09
kind: audit
domain: codex
scope: team-general
visibility: team-internal
status: archived
owner: leiwenjun
review_after: '2026-11-09'
review_status: human-directed-delegated-retired
promotion: none
tags:
- codex-archive
- migration-preflight
- archive-governance
- subagents
- delete-blocked
- no-memory-write
- no-active-promotion
generated_by_ai: true
ai_role: classified
ai_model_or_tool: Codex
ai_generated_at: '2026-07-09'
manual_validation_pending: false
summary_zh: 压实 Codex archive phased migration/removal 台账中的三条 extract-first 记录：迁移 llm_tools Windows 构建机 runbook、llm_tools 发布治理历史记录和
  xcrz_sigmastar_demo 双屏动画历史分析；旧 Codex archive 正文仍未删除。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
promotion_decision: explicit human lifecycle decision delegated to Codex; direct content review not asserted; token=KH-ATTEST-e8016ab8b78ce7a04418;
  source=current-session exact hash-bound lifecycle attestation and reviewer binding on 2026-07-15
---

# Codex archive 迁移预检批次 2026-07-09

## 摘要

本批次压实 `codex-archive-phased-migration-removal-20260709` 中 3 条 `extract-first` 记录，将旧 Codex archive 正文迁移到项目 canonical 路径。旧 Codex archive 正文仍未删除；删除前还需要独立 `delete-or-prune` 授权、file-level 删除 manifest、回滚方式和门禁验证。

## 本批迁移

| 源文件 | 目标 | 状态 |
| --- | --- | --- |
| `debug-notes/20260516-222503-windows-builder-runbook.md` | `projects/llm-tools/current/runbooks/windows-builder-runbook.md` | migrated-reviewing |
| `release-governance/20260516-225144-llm-tools-release-governance-20260516.md` | `projects/llm-tools/archive/release/2026-05-16-llm-tools-release-governance.md` | migrated-archive-only |
| `research-notes/20260514-102409-dual-screen-animation-analysis.md` | `projects/xcrz-sigmastar-demo/archive/reports/2026-05-14-dual-screen-animation-analysis.md` | migrated-archive-only |

## 子代理证据

- llm-tools 子代理结论：`projects/llm-tools` 已注册但只有 README；两条旧 llm_tools archive 未被 canonical 覆盖，应迁移后再允许旧正文进入删除前候选。
- xcrz-sigmastar-demo 子代理结论：双屏动画分析无等价 Hub 覆盖，目标应为 `projects/xcrz-sigmastar-demo/archive/reports/`，且只能作为 historical code analysis。
- governance 子代理结论：当前 phased 台账不足以直接支持删除；本批只能做迁移/预检，不删除旧正文。

## 删除阻塞

旧 Codex archive 正文删除在本预检批次中仍阻塞，原因：

- 缺独立删除授权。
- 尚未为 covered/tombstone topic 展开完整 file-level source SHA256 清单。
- 多个 topic 的 `tombstone_as` 仍是 `pending`。
- 删除批次还缺回滚方式、删除清单和最终门禁证据。

## 后续删除执行

2026-07-10 后续批次 `codex-archive-removal-execution-20260710-migrated-extract-first` 已在新授权 `auth-20260710-codex-archive-delete-migrated-extract-first-010-012` 下删除本批 3 个已迁移旧正文，并保留 file-level tombstone、hash、rollback 和验证计划。

删除不改变迁移目标状态：

- `projects/llm-tools/current/runbooks/windows-builder-runbook.md` 仍为 `reviewing`，不是 active/current verified。
- `projects/llm-tools/archive/release/2026-05-16-llm-tools-release-governance.md` 仍为 archive-only 历史记录。
- `projects/xcrz-sigmastar-demo/archive/reports/2026-05-14-dual-screen-animation-analysis.md` 仍为 historical code analysis。

## 验证计划

```bash
rtk jq -c . artifacts/manifests/codex-archive-migration-preflight-20260709.jsonl
rtk bash ~/knowledge-hub/tools/knowledge-search.sh "llm_tools Windows 构建机 Runbook"
rtk bash ~/knowledge-hub/tools/knowledge-search.sh "Sigmastar 双屏动画实现分析"
rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run
rtk rg -n "(?i)(password|token|cookie|private[_ -]?key|secret)\\s*[:=]" projects/llm-tools/current/runbooks/windows-builder-runbook.md projects/llm-tools/archive/release/2026-05-16-llm-tools-release-governance.md projects/xcrz-sigmastar-demo/archive/reports/2026-05-14-dual-screen-animation-analysis.md artifacts/manifests/codex-archive-migration-preflight-20260709.md artifacts/manifests/codex-archive-migration-preflight-20260709.jsonl
```
