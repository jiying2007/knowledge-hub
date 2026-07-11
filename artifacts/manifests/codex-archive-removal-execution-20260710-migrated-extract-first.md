# Codex archive 已迁移旧源删除执行批次 2026-07-10

## 摘要

本批根据用户在当前会话的条件授权“如果旧源没用了，授权删除”，删除 3 个已经完成 extract-first 迁移、且经两个只读子代理确认无未迁移长期结论的旧 Codex archive 正文。

本批只删除以下 3 个旧正文：

- `domains/codex/archive/codex-archive/debug-notes/20260516-222503-windows-builder-runbook.md`
- `domains/codex/archive/codex-archive/release-governance/20260516-225144-llm-tools-release-governance-20260516.md`
- `domains/codex/archive/codex-archive/research-notes/20260514-102409-dual-screen-animation-analysis.md`

本批不删除 `memory-curation`、`session-wrap`、`patent-disclosure`、`diag-architecture` 或其他旧 archive 正文；不写 `~/.codex/memories`；不提升 active；不生成 owner decision；不修改源项目；不 push。

结构化台账：`artifacts/manifests/codex-archive-removal-execution-20260710-migrated-extract-first.jsonl`。

## 授权

| Field | Value |
| --- | --- |
| authorization_id | `auth-20260710-codex-archive-delete-migrated-extract-first-010-012` |
| authorized_by | `leiwenjun` |
| authorization_basis | 当前会话用户指令：如果旧源没用了，授权删除 |
| pre_delete_commit | `db07bd4839016d76f37218cd2b72857ed8575d48` |
| scope | exactly `CAMP-20260709-001..003` and `CAMR-20260709-010..012` |

## 删除条目

| Row | Source | SHA256 | Disposition |
| --- | --- | --- | --- |
| `CARE-20260710-004` | `debug-notes/20260516-222503-windows-builder-runbook.md` | `9834e36cff48c76b3022f2957c612a140b0f11e19a84281d023139d455a26109` | 已迁移为 llm_tools Windows builder runbook；目标仍为 reviewing |
| `CARE-20260710-005` | `release-governance/20260516-225144-llm-tools-release-governance-20260516.md` | `d67055f56fccc7b2210bd97b9a173f25291bbab872edfb06358a7d6349966a03` | 已迁移为 llm_tools release governance archive-only 历史记录 |
| `CARE-20260710-006` | `research-notes/20260514-102409-dual-screen-animation-analysis.md` | `26631926204833ea84e3e8705521cc0020d169c4d6a40aba6d3488d859a2c6a3` | 已迁移为 xcrz_sigmastar_demo historical code analysis |

## 保留边界

- `llm-tools-windows-builder-runbook-20260709` 仍是 `reviewing`，未基于当前 `llm_tools` 源仓重新验证，不声明 active/current verified。
- `llm-tools-release-governance-archive-20260516` 仍是 `archive-only` 历史记录，不声明当前发布基线。
- `xcrz-sigmastar-demo-dual-screen-animation-analysis-20260514` 仍是 historical code snapshot，不代表当前源码事实。
- 旧正文的 source path、source hash、size、迁移目标、rollback 和授权记录保留在本 manifest、`codex-archive-migration-preflight-20260709.jsonl`、`codex-archive-removal-preflight-20260710.jsonl` 和 `codex-archive-phased-migration-removal-20260709.jsonl`。

## 回滚

如需回滚本批，只恢复本批 3 个已删旧正文、三个 topic index、执行 manifest、`registry/authorizations.jsonl`、`registry/items.jsonl`、受影响索引以及 CAMP/CARP/CAMR 行。

不得使用全仓 reset 覆盖其他未提交归档工作。恢复锚点为 `pre_delete_commit=db07bd4839016d76f37218cd2b72857ed8575d48`。

## 验证计划

```bash
rtk jq -c . artifacts/manifests/codex-archive-removal-execution-20260710-migrated-extract-first.jsonl
rtk test ! -e domains/codex/archive/codex-archive/debug-notes/20260516-222503-windows-builder-runbook.md
rtk test ! -e domains/codex/archive/codex-archive/release-governance/20260516-225144-llm-tools-release-governance-20260516.md
rtk test ! -e domains/codex/archive/codex-archive/research-notes/20260514-102409-dual-screen-animation-analysis.md
rtk bash tools/knowledge-search.sh "llm_tools Windows 构建机 Runbook"
rtk bash tools/knowledge-search.sh "llm_tools 发布治理归档 2026-05-16"
rtk bash tools/knowledge-search.sh "Sigmastar 双屏动画实现分析 2026-05-14"
rtk bash tools/knowledge-check.sh --dry-run
rtk git diff --check
```
