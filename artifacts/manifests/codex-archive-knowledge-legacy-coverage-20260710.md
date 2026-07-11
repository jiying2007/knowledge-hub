# Codex archive Knowledge legacy coverage 2026-07-10

## Scope

本记录从旧 Codex archive `session-wrap/20260517-180051-knowledge-session-wrap.md` 迁移 Embedded Knowledge Base 独立建库历史。本文是 coverage audit，不是 current rule、owner decision、memory 或 active promotion。

## 历史事实

- 日期：2026-05-17。
- 旧本机路径：`[REDACTED_HOME]/embedded/knowledge`。
- 旧远端：`private git remote [REDACTED_PRIVATE_REMOTE]/embedded/knowledge.git`。
- 历史 baseline commit：`a2ee7f7 chore: 建立知识库质量基线`。
- 当时为单一根提交，`git rev-list --count HEAD = 1`。
- 当时目标是把原项目中的 `docs`、`tools` 技术沉淀独立为团队共享知识库，并治理仓库结构、规范、脚本、技能、验证门禁和长期维护边界。
- 历史仓库边界：团队共享知识库作为独立 Git 仓库演进，业务项目只引用或链接，不直接承载长期研发知识沉淀。

## 历史质量门禁

旧源记录当时 `scripts/check-all.sh` 通过，摘要包括：

- Python 测试：`32 tests OK`
- 命名检查：`checked 46 files`
- Schema 检查：`checked 43 documents`
- 链接检查：`checked 43 documents`
- AGENT/SKILL 一致性：`agents=3, skills=8`
- Shellcheck：`checked 27 scripts`
- Shfmt：`checked 27 scripts`
- Secret scan、Docs lint、Skills dry-run、Artifact check、Tools check strict 均通过。

这些结果只代表旧会话当时状态。本次迁移没有重新运行旧仓库检查，也不恢复旧仓库作为当前 authority。

## 当前覆盖边界

- 当前 Hub 已将 `embedded-knowledge` 作为 retired source 管理。
- 当前知识入口不再使用旧外部路径；权威入口在 Hub 内 `domains/embedded/`、`sources/embedded-knowledge/`、`registry/sources.json` 和 `registry/retired-sources.jsonl`。
- 旧建库过程中的个人路径、私有远端、一次性执行细节和低复用环境现象不得提升为 memory。

## 风险

- 旧 clone 同步、server hook、CI runner、NAS artifact 根路径等旧未决项只保留为历史风险。
- 不能把 2026-05-17 的旧 `embedded/knowledge` 事实误提升为当前 `knowledge-hub` 事实。
- 工具版本、CI runner、NAS 环境均可能漂移。

## Source identity

- Source: `domains/codex/archive/codex-archive/session-wrap/20260517-180051-knowledge-session-wrap.md`
- Source SHA256: `963923625ccdbece2548b4315ab4f9a907e6f6ed908d1afffc504a996626b266`
- Source size: `4810` bytes
- Preflight row: `CAEF-20260710-026`
- Tombstone: `CARE-20260710-034`

## Decision

旧正文可在本 coverage audit、registry、index、tombstone 和授权账本落地后删除。删除不代表旧 Knowledge Base 恢复为 source authority，不写 memory，不关闭 owner gate，不生成 owner decision。
