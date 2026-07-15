---
id: codex-archive-removal-preflight-20260710
title: Codex archive 删除预检 2026-07-10
kind: audit
domain: codex
scope: team-general
visibility: team-internal
status: archived
owner: leiwenjun
review_after: '2026-11-10'
review_status: human-directed-delegated-retired
promotion: none
tags:
- codex-archive
- removal-preflight
- archive-governance
- subagents
- delete-blocked
- file-level-sha256
- no-memory-write
- no-active-promotion
generated_by_ai: true
ai_role: classified
ai_model_or_tool: Codex
ai_generated_at: '2026-07-10'
manual_validation_pending: false
summary_zh: 把 Codex archive 第一批移除队列压实到 file-level 删除预检：5 个 covered 文件和 3 个 provenance-only 文件进入删除预检候选，1 个 Codex token 路线图文件必须保留或重分类，memory-curation
  与 session-wrap 因大量高信号候选继续阻塞删除。旧 archive 正文未删除。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
promotion_decision: explicit human lifecycle decision delegated to Codex; direct content review not asserted; token=KH-ATTEST-0343cce247b981b12203;
  source=current-session exact hash-bound lifecycle attestation and reviewer binding on 2026-07-15
---

# Codex archive 删除预检 2026-07-10

## 摘要

本批把 `artifacts/manifests/codex-archive-phased-migration-removal-20260709.jsonl` 中 `CAMR-20260709-002..009` 从 topic 级队列压实到 file-level 删除预检。

本批不删除、移动或改写旧 archive 正文；不写 `~/.codex/memories`；不提升 active；不生成 owner decision。删除仍然阻塞，必须另有有效 `delete-or-prune` 授权、独立删除执行 manifest、回滚路径和门禁验证。

结构化台账：`artifacts/manifests/codex-archive-removal-preflight-20260710.jsonl`。

## 本批结论

| 范围 | 结论 |
| --- | --- |
| `CAMR-20260709-002..005` | 5 个文件可进入 removal-preflight candidate；1 个文件必须保留或重分类。 |
| `CAMR-20260709-006` | `control-archives` 两篇 bwrap 旧运行时快照可进入 tombstone-only preflight。 |
| `CAMR-20260709-007` | `memory-curation` 不能整 topic tombstone；40 篇中 34 篇命中高信号候选，需要先做 file-level extract-first 审查。 |
| `CAMR-20260709-008` | `session-wrap` 不能整 topic tombstone；25 篇中 21 篇命中 durable conclusion，需要先做 file-level extract-first 审查。 |
| `CAMR-20260709-009` | `tools` 一篇归档动作记录可进入 tombstone-only preflight。 |

## 可进入删除预检的文件

| ID | Source | Disposition | 边界 |
| --- | --- | --- | --- |
| `CARP-20260710-001` | `_registry/schema.md` | `removal-preflight-candidate` | 当前权威是 `registry/schema.md`；旧 schema 仅保留 provenance。 |
| `CARP-20260710-002` | `archive-governance/20260519-221757-archive-quality-remediation.md` | `tombstone-only-provenance` | 旧 archive v2 治理记录不可作为当前规则。 |
| `CARP-20260710-003` | `diag-architecture/20260510-000000-diag-command-architecture-v4-conclusion.md` | `removal-preflight-candidate` | PCR02 diag 结论已有项目 decision 覆盖；旧正文仅作历史收口。 |
| `CARP-20260710-005` | `patent-disclosure/20260530-215617-...md` | `superseded-by-later-patent-note` | 需要保留 safe OTA 从组合中移除的 provenance。 |
| `CARP-20260710-006` | `patent-disclosure/20260530-220612-...md` | `duplicate-of-canonical-patent-note` | 专利材料仍受 owner/legal review 边界约束。 |
| `CARP-20260710-007` | `control-archives/20260502-003500-bwrap-knowledge.md` | `tombstone-only-provenance` | 本机旧 bwrap 运行时快照，不提升为当前规则。 |
| `CARP-20260710-008` | `control-archives/20260502-003520-bwrap-knowledge.md` | `tombstone-only-provenance` | 与上一条同类重复快照。 |
| `CARP-20260710-009` | `tools/20260515-171959-tools-archive.md` | `tombstone-only-provenance` | 只是一次 tools 归档动作记录，当前事实以 live `tools/` 为准。 |

## 保留或重分类

`diag-architecture/20260511-112520-codex-token-optimization-roadmap.md` 不应跟随 `CAMR-20260709-004` 的 PCR02 diag 覆盖结论删除。它的主题是 Codex 长期省 Token 优化，不是 PCR02 diagnostic architecture；`projects/pcr02/decisions/diag-v4-hybrid-refcount-discovery-spec.md` 不能覆盖它。后续已按 corrected topic `codex/token-efficiency` 迁移 coverage audit，并在独立授权批次中删除旧正文、保留 tombstone。

该独立判断已落到 `artifacts/manifests/codex-token-efficiency-roadmap-coverage-20260710.md` 和 `artifacts/manifests/codex-archive-removal-execution-20260710-token-patent-004-006.md`；coverage audit 仍不构成 active roadmap。

## 阻塞范围

`memory-curation` 和 `session-wrap` 当前不能作为整 topic 删除候选。

- `memory-curation`：40 篇正文，34 篇命中 `Memory Candidates`、`High Signal Findings`、`Project Facts` 等信号。应先走 `adk-memory-curator` 或人工 review，筛出仍有效候选。
- `session-wrap`：25 篇正文，21 篇命中 `关键决策`、`Durable Lessons`、`Memory Candidate` 等信号。应先做 file-level `extract-first`，剩余过程噪音再 tombstone。

代表性 extract-first 风险文件：

- `session-wrap/20260602-132025-codex-adk-hardcut-session-wrap.md`：已在后续批次迁移为 source-to-live coverage audit，删除仍需授权和 tombstone。
- `session-wrap/20260627-230744-knowledge-hub-final-hardcut-session-wrap.md`：已在后续批次压实为 tombstone-only audit，删除仍需授权和删除执行 manifest。
- `session-wrap/20260526-162109-pcr02-session-wrap-20260526-customer-ro-sd-upgrade.md`
- `session-wrap/20260524-231443-codex-session-wrap-20260524-openai-local-runtime-boundary.md`
- `memory-curation/20260602-132130-codex-adk-hardcut-memory-curation.md`
- `memory-curation/20260627-230744-knowledge-hub-final-hardcut-memory-curation.md`
- `memory-curation/20260707-codex-usage-records-memory-curation.md`

## 删除门禁

后续真正删除旧 archive 正文前，必须同时满足：

1. `registry/authorizations.jsonl` 中存在未过期、`status=active`、覆盖本批范围的 `delete-or-prune` 授权。
2. 独立删除执行 manifest 逐文件列出 `source_path`、`source_sha256`、`size_bytes`、`covered_by`、`tombstone_as`、`rollback` 和 `authorization_id`。
3. 每个待删文件 `delete_ready=true`；本预检中所有删除相关行仍为 `delete_ready=false`。
4. `memory-curation`、`session-wrap` 完成 file-level extract-first 审查后，才能进入剩余 tombstone 批次。
5. 删除后必须运行 `knowledge-check`、目标搜索、敏感扫描和 `git diff --check`。

## 验证计划

```bash
rtk jq -c . artifacts/manifests/codex-archive-removal-preflight-20260710.jsonl
rtk bash ~/knowledge-hub/tools/knowledge-search.sh "Codex archive 删除预检"
rtk rg -n "(?i)(password|token|cookie|private[_ -]?key|secret)\\s*[:=]" artifacts/manifests/codex-archive-removal-preflight-20260710.md artifacts/manifests/codex-archive-removal-preflight-20260710.jsonl
rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run
```

## 当前状态

本批完成了删除前 file-level 风险分流，但没有完成旧 archive 删除。下一批应先处理 `session-wrap` 的 extract-first 审查，再处理 `memory-curation` 的 memory candidate 分流；删除执行必须等待授权。

2026-07-10 后续批次已新增 `artifacts/manifests/codex-archive-extract-first-preflight-20260710.md`，对 4 篇 `session-wrap`、3 篇 `memory-curation` 和 1 篇 `Codex 长期省 Token` 例外文件完成 file-level 分流。该分流仍不构成删除授权或 memory 写入授权。

同日后续批次已新增 `artifacts/manifests/codex-adk-hardcut-source-to-live-audit-20260710.md`，把 `session-wrap/20260602-132025-codex-adk-hardcut-session-wrap.md` 从 extract-first 阻塞压实为 coverage audit。该迁移仍不构成旧正文删除授权。

同日后续批次已新增 `artifacts/manifests/codex-knowledge-hub-final-hardcut-tombstone-audit-20260710.md`，把 `session-wrap/20260627-230744-knowledge-hub-final-hardcut-session-wrap.md` 从 covered-removal 压实为 tombstone-only audit。该审计仍不构成删除授权。

同日后续批次已新增 `artifacts/manifests/codex-archive-removal-execution-20260710.md`，在用户条件授权和两个只读子代理审计后，删除 `CARP-20260710-007..009` 对应的 3 个 provenance-only 旧正文：两篇 bwrap 本机运行时快照和一篇 tools 归档动作记录。`memory-curation`、`session-wrap` 和整库删除仍保持阻塞。

同日后续批次已新增 `artifacts/manifests/codex-archive-removal-execution-20260710-covered-tombstone-001-003.md`，在用户条件授权和两个只读子代理审计后，删除 `CARP-20260710-001..003` 对应的 3 个 covered/tombstone 旧正文：legacy archive schema、archive quality remediation 历史治理记录和 PCR02 diag v4 historical conclusion。`diag-architecture` 内 token roadmap 例外仍需独立 coverage audit 治理。

同日后续批次已新增 `artifacts/manifests/codex-archive-removal-execution-20260710-token-patent-004-006.md`，在用户条件授权和两个只读子代理审计后，删除 `CARP-20260710-004..006` 对应的 3 个旧正文：Codex token efficiency roadmap 旧正文和两篇 patent-disclosure 旧副本。该批保留 safe OTA 从四件组合到三件组合的 provenance，不声明 legal review 完成。`memory-curation`、`session-wrap` 和整库删除仍保持阻塞。
