# Codex archive 删除执行批次 2026-07-10

## 摘要

本批根据用户在当前会话的条件授权“如果旧源没用了，授权删除”，删除 3 个已由 file-level 预检和两个只读子代理确认的 provenance-only 旧 Codex archive 正文。

本批只删除以下 3 个旧正文：

- `domains/codex/archive/codex-archive/control-archives/20260502-003500-bwrap-knowledge.md`
- `domains/codex/archive/codex-archive/control-archives/20260502-003520-bwrap-knowledge.md`
- `domains/codex/archive/codex-archive/tools/20260515-171959-tools-archive.md`

本批不删除 `memory-curation`、`session-wrap`、`patent-disclosure`、`diag-architecture`、`debug-notes` 或其他旧 archive 正文；不写 `~/.codex/memories`；不提升 active；不生成 owner decision；不修改源项目；不 push。

结构化台账：`artifacts/manifests/codex-archive-removal-execution-20260710.jsonl`。

## 授权

| Field | Value |
| --- | --- |
| authorization_id | `auth-20260710-codex-archive-delete-carp-007-009` |
| authorized_by | `leiwenjun` |
| authorization_basis | 当前会话用户指令：如果旧源没用了，授权删除 |
| pre_delete_commit | `db07bd4839016d76f37218cd2b72857ed8575d48` |
| scope | exactly `CARP-20260710-007..009` |

## 删除条目

| Row | Source | SHA256 | Disposition |
| --- | --- | --- | --- |
| `CARE-20260710-001` | `control-archives/20260502-003500-bwrap-knowledge.md` | `5749c9343df9dd7c641c40c3e6c6f774c797971332af2cfac508bdb53eccd961` | 2026-05-02 本机 bwrap 运行时快照，tombstone-only provenance |
| `CARE-20260710-002` | `control-archives/20260502-003520-bwrap-knowledge.md` | `461ffd876201edb88decf09e39dd670b75b8b397f417711fd553bf5477f9a1b9` | 与上一条高度重复的本机 bwrap 快照，tombstone-only provenance |
| `CARE-20260710-003` | `tools/20260515-171959-tools-archive.md` | `17180085b85b89da1a71db491befefe21ab9dbb6288bcf72363d45e0732b84ab` | 一次 tools 主题归档动作记录，tombstone-only provenance |

## 保留边界

- `control-archives/index.md` 和 `tools/index.md` 保留 topic 级 tombstone 索引，避免断链。
- 旧正文的 source path、source hash、size、covered_by、rollback 和授权记录保留在本 manifest、`codex-archive-removal-preflight-20260710.jsonl` 和 `codex-archive-phased-migration-removal-20260709.jsonl`。
- 整个 `codex-archive` corpus 仍是 `delete-blocked`，因为 `memory-curation` 和 `session-wrap` 仍未完成 file-level extract-first。

## 回滚

如需回滚本批，只恢复本批 3 个已删旧正文、两个 topic index、执行 manifest、`registry/authorizations.jsonl`、`registry/items.jsonl`、受影响索引以及 CARP/CAMR 行。

不得使用全仓 reset 覆盖其他未提交归档工作。恢复锚点为 `pre_delete_commit=db07bd4839016d76f37218cd2b72857ed8575d48`。

## 验证计划

```bash
rtk jq -c . artifacts/manifests/codex-archive-removal-execution-20260710.jsonl
rtk test ! -e domains/codex/archive/codex-archive/control-archives/20260502-003500-bwrap-knowledge.md
rtk test ! -e domains/codex/archive/codex-archive/control-archives/20260502-003520-bwrap-knowledge.md
rtk test ! -e domains/codex/archive/codex-archive/tools/20260515-171959-tools-archive.md
rtk bash tools/knowledge-search.sh "Codex archive bwrap tombstone"
rtk bash tools/knowledge-search.sh "Codex archive tools tombstone"
rtk bash tools/knowledge-check.sh --dry-run
rtk git diff --check
```
