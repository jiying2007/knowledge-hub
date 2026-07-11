# Codex Knowledge Hub final hardcut tombstone audit 2026-07-10

## 摘要

本记录承接 `codex-archive-extract-first-preflight-20260710` 中的 `CAEF-20260710-002`，对旧 Codex archive 文件 `session-wrap/20260627-230744-knowledge-hub-final-hardcut-session-wrap.md` 做 tombstone-only 审计。

本批只生成 tombstone audit 产物：

- 不迁移旧正文为新的 active rule。
- 不写 `~/.codex/memories`。
- 不生成 owner decision，不关闭 owner gate。
- 不删除旧 Codex archive 正文。
- 不复制 raw session、运行态缓存、外部源正文、token、cookie、private key 或本机私有运行态文件。

结构化台账：`artifacts/manifests/codex-knowledge-hub-final-hardcut-tombstone-audit-20260710.jsonl`。

## Source Identity

| 文件 | SHA256 | 行数 | 字节 | 分类 |
| --- | --- | ---: | ---: | --- |
| `session-wrap/20260627-230744-knowledge-hub-final-hardcut-session-wrap.md` | `cdfca7188a356f269dc4513f79bf6238e20d8fc0080e4a5ff8acd424c8ef62e6` | 80 | 4200 | `covered-tombstone-audit-not-delete-ready` |

## Sanitization Verdict

结论：可进入 tombstone-only 审计，但不能直接删除旧源。

- secret 风险：未发现真实 token、cookie、private key、password 或 credential；旧源中的敏感词只出现在“不包含 secrets / token”的边界声明中。
- raw-log/raw-session 风险：未发现完整聊天记录、session JSONL、运行态缓存正文或外部源正文。
- binary/artifact 风险：未发现二进制、压缩包、base64、release artifact 或 SDK 正文。
- path 风险：仅保留 `~/knowledge-hub`、`~/codex`、`~/.codex` 和旧 `~/codex/docs/archive` 这类泛化路径作为治理边界；不写入本机绝对个人路径。

## Coverage Verdict

旧源中的长期结论已经由当前 Hub 覆盖：

| 旧源结论 | 当前覆盖 | 处置 |
| --- | --- | --- |
| `~/knowledge-hub` 是统一知识控制面，旧入口不再作为当前运行入口。 | `docs/goals/knowledge-hub-simplified-final-version.md`、`governance/path-routing.md` | covered，旧源只保留 provenance。 |
| 项目入口固定到 `projects/<project>/README.md`，项目界定优先按 registry/remote/component。 | `registry/project-routes.json`、`registry/repositories.json`、`governance/path-routing.md` | covered，不从旧 session 重新提升。 |
| 旧 `~/embedded/engineering_archive`、`~/codex/docs/archive` 只保留 canonical policy 或 provenance。 | `domains/codex/archive/codex-archive.ref.md`、`governance/path-routing.md` | covered，适合 tombstone audit。 |
| AI-human review 不等于 owner approval，不关闭 owner gate，不提升 active，不写 memory。 | `docs/goals/knowledge-hub-simplified-final-version.md`、`governance/status/knowledge-hub-operational-maturity.md` | covered，旧源不得作为 owner decision。 |
| path audit 要区分 runtime rules 和 historical session text。 | `governance/path-routing.md`、`tools/knowledge-path-audit.sh`、`governance/status/knowledge-hub-operational-maturity.md` | covered，保留为删除前 provenance。 |

## Archive-Only Items

以下内容只保留为 provenance，不迁移为长期正文：

- 当日 commit hash、final gate 输出摘要、review queue 清零数量和临时状态。
- 旧 gate 输出与当时长跑进程风险提示。
- 一次性下一步建议和会话恢复说明。
- `pcr02-core-sensor_in0` 当时的检索确认记录；它不能替代项目级根因结论。

## Delete Gate

`delete_ready=false` 保持不变。未来删除旧正文前至少需要：

- 有有效 delete-or-prune 授权记录。
- 有独立删除执行 manifest，逐文件记录 `source_path`、`source_sha256`、size、line count、covered_by/tombstone_as、删除原因和 rollback。
- 删除前重跑 secret、raw session、raw log、binary、cache 和绝对个人路径扫描。
- 确认旧源中没有仍未抽取的长期结论；covered/tombstone audit 不等于删除授权。
- 不用本地 commit、covered_by、preflight row、subagent 报告或本 tombstone audit 替代 owner authorization。

## Evidence Commands

```bash
rtk sha256sum domains/codex/archive/codex-archive/session-wrap/20260627-230744-knowledge-hub-final-hardcut-session-wrap.md
rtk wc -c -l domains/codex/archive/codex-archive/session-wrap/20260627-230744-knowledge-hub-final-hardcut-session-wrap.md
rtk rg -n "Knowledge Hub 终态|final hardcut|终态硬切换|path hardcut|review queue|owner|review|codex-archive|source coverage|operational maturity|path-routing|final gate" docs/goals/knowledge-hub-simplified-final-version.md governance/path-routing.md governance/status/knowledge-hub-operational-maturity.md artifacts/manifests/knowledge-hub-source-coverage-closeout-20260624.md domains/codex/archive/codex-archive.ref.md
rtk rg -n -i "(api[_-]?key|secret|password|passwd|cookie|authorization|bearer|private[_ -]?key|credential|凭证|密钥|口令)" domains/codex/archive/codex-archive/session-wrap/20260627-230744-knowledge-hub-final-hardcut-session-wrap.md artifacts/manifests/codex-knowledge-hub-final-hardcut-tombstone-audit-20260710.md
rtk jq -c . artifacts/manifests/codex-knowledge-hub-final-hardcut-tombstone-audit-20260710.jsonl artifacts/manifests/codex-archive-extract-first-preflight-20260710.jsonl artifacts/manifests/codex-archive-removal-preflight-20260710.jsonl artifacts/manifests/codex-archive-phased-migration-removal-20260709.jsonl
rtk bash ~/knowledge-hub/tools/knowledge-search.sh "Knowledge Hub final hardcut tombstone"
rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run
```
