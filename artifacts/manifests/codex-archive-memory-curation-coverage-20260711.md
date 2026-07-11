# Codex archive memory-curation coverage 2026-07-11

## 摘要

本记录承接 `codex-archive-memory-curation-file-level-audit-20260710` 和四个只读 subagent 审计结果，对旧 Codex archive `memory-curation` topic 的 40 个正文做终态 coverage 分流。

本批产物的边界：

- 不写 `~/.codex/memories`。
- 不提升 active rule、current fact、owner decision 或 release approval。
- 不修改源项目。
- 不复制 raw session、完整日志、cache、binary、release artifact、token、cookie、private key、PFX、NAS 凭据或私有 package index。
- 只把仍有长期价值的内容迁移为 archive-only project record 或 coverage/tombstone manifest。

结构化台账：`artifacts/manifests/codex-archive-memory-curation-coverage-20260711.jsonl`。

## 新增 canonical / coverage targets

| Target | 覆盖内容 |
| --- | --- |
| `projects/llm-tools/archive/release/2026-05-17-llm-tools-normal-iteration-policy.md` | `llm_tools` 三仓从单提交初始化进入正常迭代的历史策略，以及 release governance 边界。 |
| `projects/llm-tools/archive/release/2026-05-19-llm-tools-v1-release-memory-review.md` | `llm_tools` v1.0.0 发布审计历史、Windows x64 portable/installer、PDF-first 和 Authenticode 范围。 |
| `projects/mcu/archive/2026-05-18-mcu-memory-curation-coverage.md` | HC32F072、MM32SPIN023C memory layout 线索和 firmware-release-tools NAS 发布治理历史。 |
| `projects/pcr02/archive/engineering-archive/pcr02/ota-release/pcr02_release_validation_20260519.md` | PCR02/SSC305 2026-05-19 发布命令、历史版本和 OTA 发布边界。 |
| `artifacts/manifests/codex-archive-memory-curation-coverage-20260711.md` | 40 个旧 `memory-curation` 正文的终态分流、候选降级、delete gate 和 tombstone 依据。 |

## Subagent audit integration

| Subagent | Scope | 结论使用方式 |
| --- | --- | --- |
| `019f4cd3-704f-7561-a6ec-eb11be94ad45` | 20260510 至 20260517-180100 | 标记早期重复/过程记录为 provenance-only 或 covered；抽取 `llm_tools` 正常迭代策略。 |
| `019f4cd3-af29-7572-90c1-53a3aa37962d` | 20260517-220525 至 20260519-133320 | 标记中段重复/过程记录为 covered；抽取 MCU memory-curation 关键线索。 |
| `019f4cd3-f500-7b83-b59d-fc08a70ceaac` | 20260519-221757 至 20260524-231343 | 抽取 `llm_tools` v1 和 PCR02 发布验证；标记后续重复文件为 covered/provenance-only。 |
| `019f4cd4-2a28-7133-b33f-f9afec629c89` | 20260524-231447 至 20260707 与既有 audit | 确认尾部 hardcut/usage 文件不能直接提升 memory；本记录将其降级为 archive-only/future owner review/drop，并提供删除前 coverage。 |

## Disposition summary

| Disposition | Count | 说明 |
| --- | ---: | --- |
| `extract-first-migrated` | 6 | 已落到项目 archive 或本 coverage manifest。 |
| `covered-delete-ready` | 18 | 已由现有 project archive、governance record、memory-curation file-level audit 或本 coverage 覆盖。 |
| `provenance-only-delete-ready` | 13 | 只保留 hash/tombstone/rollback，不保留旧正文。 |
| `candidate-demoted-delete-ready` | 3 | `20260602`、`20260627`、`20260707` 中候选不写 memory、不提升 active；仅保留为 future owner review 或 drop/noise。 |

## Candidate demotion

旧 `memory-curation` 文件中出现的 memory candidate 按以下口径处理：

- Codex/ADK source-to-live、drift、active-only residual scan：已有 live candidate 或治理覆盖；本轮不写 memory，旧正文可 tombstone。
- Knowledge Hub route、final gate、path hardcut、review queue 边界：已由 Hub governance、path routing、operational maturity 和 20260710 tombstone audit 覆盖；本轮只保留 provenance。
- Codex usage、OpenAI official docs freshness、PCR02 sensor/stream、PCR02 AI RGN、MCU thermal、86 盒 ODM、ESP32 等线索：不作为 current fact 迁移；只记录“future owner review / project evidence required”，删除旧正文时不丢失已审计边界。
- 一次性数量、会话统计、raw-ish command output、低置信 debug 线索和未复现项目判断：归入 drop/noise，不迁移正文。

## Delete gate

本记录将 40 个正文统一推进到 `delete_ready=true`，前提是删除执行批次同时满足：

- 有当前会话用户授权或 registry authorization row，且 scope 精确到 `memory-curation` 旧正文。
- 有 tombstone execution manifest，逐文件记录 `source_path`、`source_sha256`、line count、size、covered_by、delete_reason 和 rollback。
- 删除只移除旧正文，不删除 `memory-curation/index.md`，不删除 topic 目录，不删除旧 Codex archive corpus。
- 删除后更新 topic index、registry item、by-* 索引并运行 JSONL、搜索、knowledge-check 和 diff 验证。

## Remaining blocker after this coverage

`memory-curation` 正文删除不再被未抽取内容阻塞；旧 Codex archive corpus 仍需单独扫描其他 topic 是否残留正文或 blocker。本文不授权整库删除。
