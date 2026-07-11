# Codex archive memory-curation 删除执行批次 2026-07-11

## 摘要

本记录按用户“旧源没用了可删除，但必须满足 canonical/coverage/tombstone/authorization/rollback/validation”的条件授权，删除旧 Codex archive `memory-curation` topic 下 40 个正文文件。

本批只删除旧正文：

- 保留 `domains/codex/archive/codex-archive/memory-curation/index.md`。
- 不删除 topic 目录。
- 不删除旧 Codex archive corpus。
- 不写 `~/.codex/memories`。
- 不提升 active/current fact。
- 不修改源项目。
- 不 commit、push、merge、rebase 或 tag。

结构化 tombstone 台账：`artifacts/manifests/codex-archive-removal-execution-20260711-memory-curation.jsonl`。

## 授权

| Field | Value |
| --- | --- |
| authorization_id | `auth-20260711-codex-archive-delete-memory-curation` |
| authorized_by | `leiwenjun` |
| authorized_at | `2026-07-11` |
| allowed_actions | `delete-or-prune` |
| scope | 删除 `domains/codex/archive/codex-archive/memory-curation` 下 40 个旧正文；保留 topic index 和目录 |

## Coverage

删除前已落地：

- `projects/llm-tools/archive/release/2026-05-17-llm-tools-normal-iteration-policy.md`
- `projects/llm-tools/archive/release/2026-05-19-llm-tools-v1-release-memory-review.md`
- `projects/mcu/archive/2026-05-18-mcu-memory-curation-coverage.md`
- `projects/pcr02/archive/engineering-archive/pcr02/ota-release/pcr02_release_validation_20260519.md`
- `artifacts/manifests/codex-archive-memory-curation-coverage-20260711.md`
- `artifacts/manifests/codex-archive-memory-curation-coverage-20260711.jsonl`

## Tombstone summary

| Category | Count |
| --- | ---: |
| deleted old source bodies | 40 |
| retained topic index | 1 |
| extract-first migrated | 6 |
| covered/provenance-only/candidate-demoted | 34 |

## Rollback

- Git-tracked deleted正文：从 pre-delete commit `db07bd4839016d76f37218cd2b72857ed8575d48` 恢复对应 source path，并同时恢复 topic index、registry、authorization、execution manifest 和 affected indexes。
- 未跟踪旧正文 `20260707-codex-usage-records-memory-curation.md`：删除前已写入本地 Git blob `ef6e321d832eacd394a344ed67697ad2c67bcee9`，恢复时以该 blob 内容和 tombstone SHA256 `979b29680ad307167367c5cb9b9ada3997bf33cbf2a99e85d9ab9222639789ff` 校验后通过 `apply_patch` 重建。
- 不使用 `git reset --hard` 或 `git checkout --` 回退整个工作区，避免覆盖无关用户改动。

## Validation commands

```bash
rtk jq -s length artifacts/manifests/codex-archive-removal-execution-20260711-memory-curation.jsonl
rtk test ! -e domains/codex/archive/codex-archive/memory-curation/20260510-104309-memory-curation.md
rtk test ! -e domains/codex/archive/codex-archive/memory-curation/20260707-codex-usage-records-memory-curation.md
rtk test -e domains/codex/archive/codex-archive/memory-curation/index.md
rtk rg --files domains/codex/archive/codex-archive/memory-curation
rtk bash tools/knowledge-search.sh "Codex archive memory-curation coverage"
rtk bash tools/knowledge-search.sh "llm_tools 正常迭代策略"
rtk bash tools/knowledge-search.sh "PCR02 SSC305 发布验证 2026-05-19"
rtk bash tools/knowledge-check.sh --dry-run
rtk git diff --check
```
