# Codex ADK hardcut source-to-live 覆盖审计 2026-07-10

## 摘要

本记录承接 `codex-archive-extract-first-preflight-20260710` 中的 `CAEF-20260710-001`，对旧 Codex archive 文件 `session-wrap/20260602-132025-codex-adk-hardcut-session-wrap.md` 做选择性回填。

本批只生成 archive-only 覆盖审计产物：

- 不修改 `~/codex` 或 `~/.codex`。
- 不写 `~/.codex/memories`。
- 不提升 active rule、skill、workflow 或 AGENTS 规则。
- 不删除旧 Codex archive 正文。
- 不复制 raw session、运行态日志、cache、token、cookie、private key 或本机私有运行态文件。

结构化台账：`artifacts/manifests/codex-adk-hardcut-source-to-live-audit-20260710.jsonl`。

## Source Identity

| 文件 | SHA256 | 行数 | 字节 | 分类 |
| --- | --- | ---: | ---: | --- |
| `session-wrap/20260602-132025-codex-adk-hardcut-session-wrap.md` | `5e95b362b621e979797ad734f928dcc5cfa31d673adfe68fe4ac0f361c79cf10` | 85 | 4249 | `migrated-coverage-audit-not-delete-ready` |

## Sanitization Verdict

结论：可进入 archive-only 覆盖审计，但不能直接写 memory、提升 active 或删除旧源。

- secret 风险：未发现真实 token、cookie、private key、password 或 credential；旧源中的敏感词只出现在“不包含 secrets / token”的边界声明或普通命令名称中。
- raw-log/raw-session 风险：未发现完整聊天记录、session JSONL、`.codex/sessions` 原文、运行态日志正文或 cache 正文。
- binary/artifact 风险：未发现二进制、压缩包、base64、release artifact 或 SDK 正文。
- path 风险：仅保留 `~/codex`、`~/.codex`、`agent-dev-kit`、`.codex/sessions` 等泛化路径作为治理边界；不写入本机绝对个人路径。

## 保留结论

| 主题 | 旧 archive 中的长期价值 | 当前覆盖 | 处置 |
| --- | --- | --- | --- |
| Source freshness | ADK 上游资产更新后，必须先确认 `~/codex` source 已吸收目标变更，再执行 source-to-live 链路。 | `codex-live:docs/codex-asset-management.md`、`codex-live:manifests/memory_candidates.json#adk-asset-apply-source-freshness-gate` | 保留为 coverage audit；不再重复提升。 |
| Source-to-live boundary | `~/.codex` 只通过声明式资产链路 apply，不直接手改 live。 | `codex-live:AGENTS.md`、`codex-live:docs/design.md`、`codex-live:docs/codex-cli-config-guide.md` | 已由 live Codex 规则覆盖。 |
| Active-only residual scan | hard-cut 后的旧 ID 残留结论只基于 active source/runtime；历史 session、cache、聊天记录中的旧文本不视为 active residual。 | `codex-live:manifests/memory_candidates.json#active-runtime-residual-scan-scope` | 候选已存在；本记录只做 provenance 映射。 |
| Drift after format fix | managed source 在 live apply 后又做 EOF/格式修复，必须重新 plan、dry-run、apply、drift/check。 | `codex-live:docs/design.md`、`codex-live:docs/codex-asset-management.md`、`codex-live:manifests/memory_candidates.json#managed-source-live-drift-after-format-fix` | 候选已存在；不写 memory。 |
| Upstream-first cleanup | 上游 ADK 正文模板或 naming 残留应优先在上游修复，再同步到 `~/codex`，避免单侧 drift。 | `codex-live:docs/codex-asset-management.md` 的 agent-dev-kit 应用链路 | 作为历史经验保留，不直接变更当前资产。 |

## Current Coverage

当前更权威的入口是 live Codex source，不是旧 archive：

- `codex-live:AGENTS.md`：记录 `build -> doctor -> plan/dry-run -> apply -> check` 的 source-to-live 链路，并禁止绕过声明式资产仓直接手改 live。
- `codex-live:docs/codex-asset-management.md`：记录 agent-dev-kit handoff 进入 `manifests/` 与 `src/codex-home/vendor/` 后再执行完整 build/apply/drift/check 链路。
- `codex-live:docs/design.md`：记录 `apply.sh` 只从 build 注入、protected paths 跳过、doctor/drift/check 分层。
- `codex-live:docs/session-continuity-coach.md`：在 final、commit、push、apply 和 asset-update 边界提示 build/live drift、归档和上下文收口。
- `codex-live:manifests/memory_candidates.json`：已有三条候选：`adk-asset-apply-source-freshness-gate`、`managed-source-live-drift-after-format-fix`、`active-runtime-residual-scan-scope`。它们仍是 candidate，不是 memory 或 active rule。

## Archive-Only Items

以下内容只保留为 provenance，不迁移为长期正文：

- 一次性提交号、push 结果和当日具体旧 skill ID 清单。
- apply summary、测试数量、smoke 输出和 final-ready 的会话长度提示。
- 已随上游和 live source 演进而过期的下一步安排。
- 针对特定文件 EOF 修复的运行细节。

## Delete Gate

`delete_ready=false` 保持不变。未来删除旧正文前至少需要：

- 有有效 delete-or-prune 授权记录。
- 有独立删除执行 manifest，逐文件记录 `source_path`、`source_sha256`、size、line count、covered_by/migrated_as、删除原因和 rollback。
- 有 tombstone row，说明旧正文已由本记录和 live Codex source 覆盖，且不再含未抽取长期结论。
- 删除前重跑 secret、raw session、raw log、binary、cache 和绝对个人路径扫描。
- 不用本地 commit、covered_by、preflight row 或 subagent 报告替代 owner authorization。

## Evidence Commands

```bash
rtk sha256sum domains/codex/archive/codex-archive/session-wrap/20260602-132025-codex-adk-hardcut-session-wrap.md
rtk wc -c -l domains/codex/archive/codex-archive/session-wrap/20260602-132025-codex-adk-hardcut-session-wrap.md
rtk rg -n "source-to-live|source.*live|drift|memory_candidates|active source|runtime|旧 ID|stale source|apply" ~/codex/AGENTS.md ~/codex/README.md ~/codex/docs ~/codex/manifests/memory_candidates.json
rtk rg -n -i "(api[_-]?key|secret|password|passwd|cookie|authorization|bearer|private[_ -]?key|credential|凭证|密钥|口令)" domains/codex/archive/codex-archive/session-wrap/20260602-132025-codex-adk-hardcut-session-wrap.md artifacts/manifests/codex-adk-hardcut-source-to-live-audit-20260710.md
rtk jq -c . artifacts/manifests/codex-adk-hardcut-source-to-live-audit-20260710.jsonl artifacts/manifests/codex-archive-extract-first-preflight-20260710.jsonl artifacts/manifests/codex-archive-removal-preflight-20260710.jsonl artifacts/manifests/codex-archive-phased-migration-removal-20260709.jsonl
rtk bash ~/knowledge-hub/tools/knowledge-search.sh "Codex ADK hardcut source-to-live"
rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run
```
