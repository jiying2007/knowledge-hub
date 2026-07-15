---
id: codex-archive-memory-curation-file-level-audit-20260710
title: Codex archive memory-curation file-level audit 2026-07-10
kind: audit
domain: codex
scope: codex-memory-curation-governance
visibility: team-internal
status: archived
owner: leiwenjun
review_after: '2026-08-24'
review_status: human-directed-delegated-retired
promotion: none
tags:
- codex-archive
- memory-curation
- memory-candidates
- file-level-audit
- report-only
- no-memory-write
- no-active-promotion
- delete-blocked
- subagents
generated_by_ai: true
ai_role: classified
ai_model_or_tool: Codex
ai_generated_at: '2026-07-10'
manual_validation_pending: false
summary_zh: 对旧 Codex archive memory-curation 三篇代表阻塞文件做 file-level 审计：ADK hardcut 和 2026-07 usage records 进入候选报告，Knowledge
  Hub final hardcut 为 tombstone-only；所有候选仍需 owner review，不写 memory、不提升 active、不删除旧正文。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
promotion_decision: explicit human lifecycle decision delegated to Codex; direct content review not asserted; token=KH-ATTEST-a2e6d44d3e36023aa161;
  source=current-session exact hash-bound lifecycle attestation and reviewer binding on 2026-07-15
---

# Codex archive memory-curation file-level audit 2026-07-10

## 摘要

本记录承接 `codex-archive-extract-first-preflight-20260710` 中的三条 `memory-curation` 阻塞项，做 file-level 审计和候选分流。

本批只生成 report-only 审计产物：

- 不写 `~/.codex/memories`。
- 不把候选提升为 active rule。
- 不删除旧 Codex archive 正文。
- 不复制 raw history、raw session、设备日志、凭证、cache 或运行态输出。

结构化台账：`artifacts/manifests/codex-archive-memory-curation-file-level-audit-20260710.jsonl`。

## Source Identity

| 文件 | SHA256 | 行数 | 字节 | 分类 |
| --- | --- | ---: | ---: | --- |
| `memory-curation/20260602-132130-codex-adk-hardcut-memory-curation.md` | `4acd82fdb34b1d6d64b6ee6c80b06f40e62a8ab8f8e3df6c3f1c5e2549180799` | 54 | 3374 | `candidate-only` |
| `memory-curation/20260627-230744-knowledge-hub-final-hardcut-memory-curation.md` | `2d3a8addbc47682280080ffe827edff628ee5adaaf1dc977d289abf1eb3e9f0b` | 61 | 4334 | `tombstone-only` |
| `memory-curation/20260707-codex-usage-records-memory-curation.md` | `979b29680ad307167367c5cb9b9ada3997bf33cbf2a99e85d9ab9222639789ff` | 113 | 6862 | `candidate-only-review-required` |

## Sanitization Verdict

结论：三篇可进入候选审计报告，但不能直接写 memory 或删除。

- secret 风险：未发现真实密钥形态；命中内容是“不包含 secrets / token / credential”这类边界声明，或“后续提升前必须 secret scan”的风险提示。
- raw-log/raw-session 风险：未发现完整聊天、session JSONL、`.codex/sessions` 原文、运行态日志正文；命中内容是禁止复制 raw source 的治理边界。
- binary/artifact 风险：未发现二进制、压缩包、base64、release artifact 或 SDK 正文。
- path 风险：存在 `~/codex`、`~/.codex`、`~/knowledge-hub` 和旧 archive 路径等泛化路径；迁移时保留为 provenance，不展开机器绝对路径。

## File-Level Disposition

| Preflight | 文件 | 处置 |
| --- | --- | --- |
| `CAEF-20260710-005` | `20260602-132130-codex-adk-hardcut-memory-curation.md` | 已迁移为 memory candidate audit；候选包括 source-to-live freshness、live drift 后重跑 plan/apply/drift、active-only residual scan。 |
| `CAEF-20260710-006` | `20260627-230744-knowledge-hub-final-hardcut-memory-curation.md` | tombstone-only；长期规则已由 Hub governance、path routing、source boundaries 和 operational maturity 覆盖。 |
| `CAEF-20260710-007` | `20260707-codex-usage-records-memory-curation.md` | 已迁移为 memory candidate audit；候选混有 Codex 治理、OpenAI freshness、PCR02/MCU/ESP32 项目线索，必须逐条 owner review。 |

## Memory Candidate Review Queue

这些条目只进入候选审计队列。`write_route` 只能是 report-only 或 future owner-reviewed memory candidate。

| Scope | Candidate | Evidence | Risk | Confidence | Write Route |
| --- | --- | --- | --- | --- | --- |
| Codex asset governance | ADK asset apply 前确认 `~/codex` 已吸收目标 `agent-dev-kit` commit；source stale 时先同步，再走 build/doctor/plan/dry-run/apply/check。 | `20260602` high signal finding；live `~/codex/manifests/memory_candidates.json` 已有候选。 | 可能把一次 hardcut 经验过度泛化。 | high | future owner-reviewed memory candidate |
| Codex live drift | managed source 在 live apply 后又被格式修复时，必须重跑 plan/apply/drift。 | `20260602` live drift finding；live candidate 已存在。 | 只适用于 managed source，不适用于任意文件。 | high | future owner-reviewed memory candidate |
| Codex residual scan | 旧 ID / 残留扫描只基于 active source/runtime，不把 session/history/cache 当 active residual。 | `20260602` active-only scan finding；live candidate 已存在。 | 扫描范围错误会误判历史文本。 | high | future owner-reviewed memory candidate |
| Knowledge Hub route | 归档路径、项目入口、debug/release/decision/source 问题先跑 `knowledge-context.sh`。 | `20260627` memory candidate；已由 Hub path routing 覆盖。 | 已覆盖，重复写 memory 会制造噪音。 | high | report-only |
| Knowledge Hub final gate | standard gate、max-body/mature gate 和 owner decision gate 必须分层。 | `20260627` final gate finding；已由 operational maturity 和 final gate 记录覆盖。 | 误用会代签 owner gate。 | high | report-only |
| Path hardcut | 旧 archive 路径只作 retired provenance；runtime 影响用 path audit 判断。 | `20260627` path hardcut finding；已由 `governance/path-routing.md` 覆盖。 | 旧路径召回可能污染新会话。 | high | report-only |
| Review queue boundary | AI-human review 受托回填不等于 owner decision，不关闭 owner gate、不提升 active、不写 memory。 | `20260627` review queue finding；已由 governance 记录覆盖。 | 高风险治理边界。 | high | report-only |
| Codex usage route | Codex 使用记录先进入 Hub memory-curation/project archive，不直接写 memory。 | `20260707` memory candidate；live candidate 已存在。 | raw session 或 credential 污染风险。 | high | future owner-reviewed memory candidate |
| 86 盒 ODM 项目范围 | VS/INNO 责任边界、ESP32-S3、离线唤醒、BLE Mesh、IR、NFC、OTA 和客户风险需沉淀到项目需求/决策。 | `20260707` high signal finding；live candidate 已存在。 | 项目特定，需项目证据。 | medium | future owner-reviewed memory candidate |
| PCR02 sensor/stream 边界 | camera power 与 stream publish 是不同控制面，sensor 被动执行，上层 task 管业务策略。 | `20260707` high signal finding；live candidate 已存在。 | 需代码或项目文档确认。 | medium | future owner-reviewed memory candidate |
| PCR02 AI RGN 排查 | 检测框异常先核对消息、topic、输入尺寸、DS2 padding、RGN canvas/尺寸和时间戳。 | `20260707` high signal finding；live candidate 已存在。 | 需复现或修复证据。 | medium | future owner-reviewed memory candidate |
| ADK practice absorption | OpenAI/Codex 外部实践要落到 workflow、skill、agent 或 check，不只写文档。 | `20260707` high signal finding；live candidate 已存在。 | 需 source-to-live 和负例验证。 | high | future owner-reviewed memory candidate |
| MCU thermal triage | 充电温升日志优先查看 `CHG_SNAP`、`flag`、`pa7`、`pb10`、`temp_en`、`T/v/p/w/c` 状态转换。 | `20260707` high signal finding；live candidate 已存在。 | 需二次复现。 | low-medium | future owner-reviewed memory candidate |
| Official docs adoption | 官方资料 freshness 过期后进入 adoption review loop 和 target evidence check。 | `20260707` incremental candidate；live candidate 和 freshness gate 均存在。 | 时效性强，必须重新查官方源。 | medium-high | future owner-reviewed memory candidate |
| PCR02 AI SHM cutover | 共享内存切换需审计 audio/video 是否残留直调播放路径。 | `20260707` incremental candidate；live candidate 已存在。 | 项目代码验证缺失。 | medium | future owner-reviewed memory candidate |

## Archive-Only Items

- `20260602` 中的 apply summary、测试细节、提交日志、具体旧 ID 列表和一次性命令输出。
- `20260627` 中的完整 gate JSON、review queue 长输出、提交统计和具体 registry 行级内容。
- `20260707` 中的使用记录数量、低置信项目线索、一次性 session 统计和未复现 debug 线索。

## Drop/Noise Items

- 完整聊天记录、raw session、`.codex/sessions`、cache、运行态日志原文。
- 一次性命令输出、旧 gate 过期输出、临时 session id、提交统计明细。
- 没有二次证据的单次报错线索。
- 未经 owner review 的 direct memory write 建议。

## Current Coverage

- `20260602` 的三条高信号候选已在 live `~/codex/manifests/memory_candidates.json` 中存在对应候选，但仍是 candidate，不是 memory 写入或 active rule。
- `20260627` 的 Knowledge Hub route、path hardcut、final gate 和 review queue 边界已由 Hub governance/current docs 覆盖，旧文件只保留 provenance。
- `20260707` 的 Codex/ADK 候选已有部分 live candidate 覆盖；PCR02、MCU、ESP32 项目候选仍需项目侧二次证据或 owner review。

## Delete Gate

`delete_ready=false` 保持不变。未来删除任一旧正文前至少需要：

- 有有效 delete-or-prune 授权记录。
- 有 tombstone row，记录 `source_path`、`source_sha256`、size、line count、covered_by/migrated_as 和删除原因。
- 有 rollback 说明：从 pre-delete git commit 恢复 source path，且不影响本审计产物。
- 删除前重跑 secret/raw-log/binary/path 扫描。
- 候选已被明确分类为 archive-only、owner-reviewed memory candidate 或 drop/noise。
- 不用本地 commit、covered_by、preflight row 或 subagent 报告替代 owner authorization。

## Evidence Commands

```bash
rtk sha256sum domains/codex/archive/codex-archive/memory-curation/20260602-132130-codex-adk-hardcut-memory-curation.md domains/codex/archive/codex-archive/memory-curation/20260627-230744-knowledge-hub-final-hardcut-memory-curation.md domains/codex/archive/codex-archive/memory-curation/20260707-codex-usage-records-memory-curation.md
rtk wc -c -l domains/codex/archive/codex-archive/memory-curation/20260602-132130-codex-adk-hardcut-memory-curation.md domains/codex/archive/codex-archive/memory-curation/20260627-230744-knowledge-hub-final-hardcut-memory-curation.md domains/codex/archive/codex-archive/memory-curation/20260707-codex-usage-records-memory-curation.md
rtk rg -n -i "(api[_-]?key|secret|password|passwd|cookie|authorization|bearer|private[_ -]?key|credential|凭证|密钥|口令)" domains/codex/archive/codex-archive/memory-curation/20260602-132130-codex-adk-hardcut-memory-curation.md domains/codex/archive/codex-archive/memory-curation/20260627-230744-knowledge-hub-final-hardcut-memory-curation.md domains/codex/archive/codex-archive/memory-curation/20260707-codex-usage-records-memory-curation.md
rtk rg -n -i "(raw session|raw log|完整聊天|完整日志|session transcript|session json|history\\.jsonl|\\.codex/sessions|runtime output|运行态日志|运行态缓存|cache|日志片段)" domains/codex/archive/codex-archive/memory-curation/20260602-132130-codex-adk-hardcut-memory-curation.md domains/codex/archive/codex-archive/memory-curation/20260627-230744-knowledge-hub-final-hardcut-memory-curation.md domains/codex/archive/codex-archive/memory-curation/20260707-codex-usage-records-memory-curation.md
rtk jq -c . artifacts/manifests/codex-archive-memory-curation-file-level-audit-20260710.jsonl artifacts/manifests/codex-archive-extract-first-preflight-20260710.jsonl artifacts/manifests/codex-archive-removal-preflight-20260710.jsonl artifacts/manifests/codex-archive-phased-migration-removal-20260709.jsonl
rtk bash ~/knowledge-hub/tools/knowledge-search.sh "Codex archive memory-curation file-level audit"
rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run
```
