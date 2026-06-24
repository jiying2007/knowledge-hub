# Memory Auto-Curation Report-Only Governance - 2026-06-18

## 摘要

本 manifest 固化 `runbooks/memory-auto-curation-guide.md` 的 report-only governance 终态。它不是自动化启用记录，不写 `~/.codex/memories`，不新增 team active index，也不复制源项目 runbook 正文。

## Scope

- Source id: `pcr02-project-docs`
- Source path: `runbooks/memory-auto-curation-guide.md`
- Source root: `~/work/sigmastar/pcr02_ssc305/SourceCode/sdk/verify/xcrz_sigmastar_demo/docs`
- Source sha256: `36e8529bff008fb42c90779f11724e020141e19d64a6533d6af99f70dfeedc91`
- Source size: `2060`
- Baseline package: `artifacts/manifests/pcr02-owner-review-package-20260618.md`
- Follow-up package: `artifacts/manifests/pcr02-owner-review-follow-up-20260618.md`
- Owner worksheet: `artifacts/manifests/pcr02-owner-decision-worksheets-20260618.md`

## 当前结论

`memory-auto-curation-guide.md` 继续保持 `blocked-personal-local`。本轮只批准治理边界落盘，不批准启用自动化，也不批准写 memory。

| 层级 | 状态 | 说明 |
| --- | --- | --- |
| registry item | `reviewing` | 登记本治理 manifest，便于检索和复核。 |
| row status | `blocked-personal-local` | 源流程仍需 owner 决策，不能进入 team active index。 |
| automation | `enabled=false` | 本轮不启用自动化。 |
| memory write | `writes_memory=false` | 包括正式 memory 和 curation inbox，均禁止写入。 |
| team active index | `writes_team_active_index=false` | 不把 personal/local workflow 加入团队 active index。 |

## Report-only automation boundary

固定字段：

- `automation_id=memory-auto-curation-report-only`
- `mode=report-only`
- `enabled=false`
- `sandbox=read-only`
- `approval_policy=manual`
- `writes_memory=false`
- `writes_team_active_index=false`
- `no_memory_write_gate=hard-block`
- `gate_failure_behavior=block`
- `secret_scan_required=true`
- `rollback_procedure_required=true`

## Allowed outputs

仅允许生成 owner 可审查的报告类产物：

- report artifact
- candidate list
- owner worksheet
- run summary
- archive-only note

这些产物不得自动进入正式 memory、AGENTS、skill、workflow、team active index 或团队标准。

## Denied targets

以下目标默认禁止写入：

- `~/.codex/memories/**`
- `~/.codex/memories/.codex/curation-inbox/**`
- `domains/embedded/**`
- team active index
- source project docs
- AGENTS、skill、workflow 或 automation enablement 入口

## Candidate classes

report-only 扫描只允许产生以下分类：

| class | 含义 | 默认处理 |
| --- | --- | --- |
| `memory-candidate` | 可能适合个人 memory 的候选 | 需要人工确认，不写 memory。 |
| `project-rule-candidate` | 可能适合项目规则的候选 | 需要 owner review，不进 team active index。 |
| `archive-only` | 只适合归档的材料 | 只保留引用或报告。 |
| `drop` | 一次性噪声或重复项 | 不提升。 |
| `needs-owner-review` | 证据或边界不足 | 阻塞。 |

## Owner approval points

以下动作必须另行人工批准：

- 启用自动化。
- 写 memory。
- 提升候选到 AGENTS、skill、workflow。
- 加入 team active index。
- 修改源项目 docs。
- 从 report-only 改为任何写入模式。

## Evidence

本轮只读证据：

| 证据 | 结果 |
| --- | --- |
| source hash | `36e8529bff008fb42c90779f11724e020141e19d64a6533d6af99f70dfeedc91` |
| source size | `2060` |
| source risk | 源流程写入 `~/.codex/memories/.codex/curation-inbox/`，必须被 no-memory-write gate 阻断。 |
| registry collision | 未发现正式 `memory-auto-curation` registry id 或目标路径冲突。 |
| target path state | `domains/codex/memory-curation` 目录存在但为空；本轮不写正文。 |

## Must not

- 不写 `~/.codex/memories`。
- 不写 curation inbox。
- 不启用自动化。
- 不自动 send、commit、publish、delete、promote。
- 不把 personal/local workflow material 加入 team active index。
- 不修改源项目 docs。
- 不提升到 `domains/embedded/standards/`。
- 不把 AI 分类结果当作 owner review。

## 后续条件

若 owner 后续选择 `teamized-report-only`，至少需要补齐：

- owner approval record。
- allowed report artifact path。
- review cadence。
- secret scan 命令与结果。
- rollback procedure。
- no-memory-write gate 的实现证据。
- `writes_memory=false` 与 `writes_team_active_index=false` 的运行态验证证据。

若 owner 选择 `personal-local`，则该流程只保留为 personal/local reference，不进入 team active index。

## Verification plan

```bash
rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run
rtk bash ~/knowledge-hub/tools/knowledge-search.sh "memory-auto-curation"
rtk bash ~/knowledge-hub/tools/knowledge-search.sh "no-memory-write"
rtk bash ~/knowledge-hub/tools/knowledge-search.sh "teamized-report-only"
rtk sha256sum ~/work/sigmastar/pcr02_ssc305/SourceCode/sdk/verify/xcrz_sigmastar_demo/docs/runbooks/memory-auto-curation-guide.md
rtk wc -c ~/work/sigmastar/pcr02_ssc305/SourceCode/sdk/verify/xcrz_sigmastar_demo/docs/runbooks/memory-auto-curation-guide.md
```

## Non-actions

- No source project file was edited.
- No memory was written.
- No curation inbox file was written.
- No automation was enabled.
- No team active index was updated.
- No candidate was promoted.

## Review

- owner：`leiwenjun`
- review_after：`2026-09-17`
- validation_refs：`tools/knowledge-check.sh --dry-run`
