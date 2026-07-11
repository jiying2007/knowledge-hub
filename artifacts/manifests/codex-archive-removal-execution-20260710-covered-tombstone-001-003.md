# Codex archive covered/tombstone 删除执行批次 2026-07-10

## 摘要

本批根据用户在当前会话的条件授权“如果旧源没用了，授权删除”，删除 3 个已由 file-level preflight 和两个只读子代理确认可 tombstone 的旧 Codex archive 正文。

本批只删除以下 3 个旧正文：

- `domains/codex/archive/codex-archive/_registry/schema.md`
- `domains/codex/archive/codex-archive/archive-governance/20260519-221757-archive-quality-remediation.md`
- `domains/codex/archive/codex-archive/diag-architecture/20260510-000000-diag-command-architecture-v4-conclusion.md`

本批当时不删除 `diag-architecture/20260511-112520-codex-token-optimization-roadmap.md`，不删除 `patent-disclosure`、`session-wrap`、`memory-curation` 或其他旧 archive 正文；不写 `~/.codex/memories`；不提升 active；不生成 owner decision；不修改源项目；不 push。token roadmap 与 patent-disclosure 旧正文已在后续独立批次 `codex-archive-removal-execution-20260710-token-patent-004-006` 中处理。

结构化台账：`artifacts/manifests/codex-archive-removal-execution-20260710-covered-tombstone-001-003.jsonl`。

## 授权

| Field | Value |
| --- | --- |
| authorization_id | `auth-20260710-codex-archive-delete-covered-tombstone-001-003` |
| authorized_by | `leiwenjun` |
| authorization_basis | 当前会话用户指令：如果旧源没用了，授权删除 |
| pre_delete_commit | `db07bd4839016d76f37218cd2b72857ed8575d48` |
| scope | exactly `CARP-20260710-001..003` and `CAMR-20260709-002..004` |

## 删除条目

| Row | Source | SHA256 | Disposition |
| --- | --- | --- | --- |
| `CARE-20260710-007` | `_registry/schema.md` | `b35368a2cbbe984223bcb8e59ad52c79adf8e5347427f178e76f4ab4709053a2` | legacy Codex archive v2 schema；当前权威为 `registry/schema.md` |
| `CARE-20260710-008` | `archive-governance/20260519-221757-archive-quality-remediation.md` | `b43beb473c448f82dc1246847de729d090ba5bf079e9c1444753534ba432975a` | 2026-05-19 archive quality remediation 历史治理记录，tombstone-only provenance |
| `CARE-20260710-009` | `diag-architecture/20260510-000000-diag-command-architecture-v4-conclusion.md` | `199408d300b5c456f13662dfd8f1db9c4211f723ac443f6cd7ff67e416f3aa08` | PCR02 Diag V4 历史收口；当前设计权威为 PCR02 decision/spec |

## Tombstone 摘要

`_registry/schema.md` 是 legacy Codex archive v2 human-readable schema，记录 registry files、meta v2 必填字段、topic 物理布局、project matching 顺序和 archive-check gate。当前权威为 `registry/schema.md`、archive README 和 `codex-archive.ref.md`；旧 schema 仅保留 provenance。

`archive-quality-remediation.md` 记录 2026-05-19 archive quality remediation：范围仅 `docs/archive/`，不写 memory、不提升 AGENTS；当时确立 topic index 标题保持 topic-level、每条正文配 meta、project-specific 不提升全局、重复历史先 superseded；验证摘要为 missing/orphan/invalid meta 和 secret marker 均为 0，47 entries/47 meta，8 个 superseded。

`diag-command-architecture-v4-conclusion.md` 是 PCR02 诊断架构 V4 终态收口历史记录：`cmd_server` 只做 gateway/registry/router，业务执行只在 `app_diag runtime`，`hdi -> api -> app` 单向依赖，provider owner 化和扁平化；当时核对到 `modules/app/src/app_diag/{framework,provider,ipc,core}`、APP/HDI/API provider 文件归拢、`VSAPPDIAG_CmdNodeInit/DeInit` 命名收敛。当前设计权威为 PCR02 decision/spec，旧文只作历史收口，不代表当前源码事实。

## 保留边界

- 不能用旧 archive schema 覆盖当前 Hub registry/source 规则。
- 旧 archive governance 记录不能成为当前规则、owner approval、active promotion 或 memory 写入依据。
- PCR02 decision 不等于新的 owner review 或 active promotion；旧正文不能替代当前源码验证。
- `diag-architecture/20260511-112520-codex-token-optimization-roadmap.md` 已在后续独立批次删除并 tombstone，继续由 `CAEF-20260710-008`、`codex-token-efficiency-roadmap-coverage-20260710` 和 `CARE-20260710-010` 保留 provenance。

## 回滚

如需回滚本批，只恢复本批 3 个已删旧正文、`archive-governance/index.md`、`diag-architecture/index.md`、执行 manifest、`registry/authorizations.jsonl`、`registry/items.jsonl`、受影响索引以及 CARP/CAMR 行。

不得使用全仓 reset 覆盖其他未提交归档工作。恢复锚点为 `pre_delete_commit=db07bd4839016d76f37218cd2b72857ed8575d48`。

## 验证计划

```bash
rtk jq -c . artifacts/manifests/codex-archive-removal-execution-20260710-covered-tombstone-001-003.jsonl
rtk test ! -e domains/codex/archive/codex-archive/_registry/schema.md
rtk test ! -e domains/codex/archive/codex-archive/archive-governance/20260519-221757-archive-quality-remediation.md
rtk test ! -e domains/codex/archive/codex-archive/diag-architecture/20260510-000000-diag-command-architecture-v4-conclusion.md
rtk bash tools/knowledge-search.sh "Legacy Codex archive registry schema"
rtk bash tools/knowledge-search.sh "Archive Quality Remediation"
rtk bash tools/knowledge-search.sh "PCR02 诊断架构 V4"
rtk bash tools/knowledge-check.sh --dry-run
rtk git diff --check
```
