# Codex archive token/patent 删除执行批次 2026-07-10

## 摘要

本批根据用户在当前会话的条件授权“如果旧源没用了，授权删除”，在两个只读子代理审计后删除 3 个旧 Codex archive 正文。

本批只删除以下 3 个旧正文：

- `domains/codex/archive/codex-archive/diag-architecture/20260511-112520-codex-token-optimization-roadmap.md`
- `domains/codex/archive/codex-archive/patent-disclosure/20260530-215617-patent_skill_archive_note_20260530215400.md`
- `domains/codex/archive/codex-archive/patent-disclosure/20260530-220612-patent_skill_archive_note_20260530215400.md`

本批不删除 `session-wrap`、`memory-curation`、其他旧 archive topic、`domains/patents/archive/patent-disclosure/**`、`domains/patents/artifacts/patent-disclosure-artifacts.ref.md` 或 `artifacts/vault/patent-disclosure/**`；不写 `~/.codex/memories`；不提升 active；不生成 owner decision；不修改源项目；不 push。

结构化台账：`artifacts/manifests/codex-archive-removal-execution-20260710-token-patent-004-006.jsonl`。

## 授权

| Field | Value |
| --- | --- |
| authorization_id | `auth-20260710-codex-archive-delete-carp-004-006` |
| authorized_by | `leiwenjun` |
| authorization_basis | 当前会话用户指令：如果旧源没用了，授权删除 |
| pre_delete_commit | `db07bd4839016d76f37218cd2b72857ed8575d48` |
| scope | exactly `CARP-20260710-004..006` and `CAMR-20260709-004..005` |

## 删除条目

| Row | Source | SHA256 | Disposition |
| --- | --- | --- | --- |
| `CARE-20260710-010` | `diag-architecture/20260511-112520-codex-token-optimization-roadmap.md` | `1caa3efc5d0c78b1aae5f769e93222800b919a3ba009512cee6c64ded37e6a83` | Codex token/context efficiency coverage audit 已迁移；旧正文 tombstone |
| `CARE-20260710-011` | `patent-disclosure/20260530-215617-patent_skill_archive_note_20260530215400.md` | `f56d0fa121fe06de11467018d8a8b98d0150b4679cca4cfc62b4ceb7a927d702` | 四件专利组合过程记录被后续三件组合 supersede；保留 safe OTA 组合变化 provenance |
| `CARE-20260710-012` | `patent-disclosure/20260530-220612-patent_skill_archive_note_20260530215400.md` | `df8bb624031b562bc117fae5e1e80ff67a963e12bdb299117fa7a141c5073199` | 与 patents canonical note 逐字重复；旧 Codex archive 副本 tombstone |

## Tombstone 摘要

`20260511-112520-codex-token-optimization-roadmap.md` 是 Codex token/context 使用效率路线图，旧路径误归在 `diag-architecture/`，不能由 PCR02 diag decision 覆盖。长期价值已迁移到 `artifacts/manifests/codex-token-efficiency-roadmap-coverage-20260710.md`：输出侧节流、分层读取、原文回退、usage telemetry 启发式归因、archive/search 回用和 memory/archive 边界。删除旧正文不代表采纳旧 Phase 1-4、P0/P1/P2 顺序，也不代表采纳 `code-review-graph` 或 `token-savior`；`structured-code-navigation-poc` 与 `long-term-usage-timeseries` 仍为 not-covered。

`20260530-215617-patent_skill_archive_note_20260530215400.md` 是 2026-05-30 四件专利组合过程记录，后续被三件组合 supersede。safe OTA 曾作为候选，材料包括 Disclosure/Claims Markdown、Word 与 `figures_ota/`；当时评价为工程可靠性/发布工程候选，但 UBI/SquashFS/ubiblock/block OTA 相关 prior-art 密度较高，应收窄到只读客户区与可写数据区协同迁移策略和验证闭环。后续按用户要求从 active patent portfolio 移除 safe OTA，保留三件：眼神动画、多传感器产测标定、端侧多模态陪伴行为。删除旧正文不代表法律复核完成、不代表正式提交、不代表否定 safe OTA 历史存在。

`20260530-220612-patent_skill_archive_note_20260530215400.md` 是 `domains/patents/archive/patent-disclosure/patent_skill_archive_note_20260530215400.md` 的逐字重复副本。canonical 文件保留三件专利组合、第三方 skill 只作参考未安装、CNIPA 脚本超时、npm audit 风险仅限临时工具链、三件 disclosure/claims Word 生成、safe OTA 已从 active delivery 移除等过程事实。删除旧 Codex archive 副本不代表法律审查完成。

## 保留边界

- token roadmap coverage audit 仍是 reviewing/audit，不是 active roadmap。
- `diag-architecture` topic 的 PCR02 decision 不能覆盖 Codex token efficiency 材料；本批以 corrected topic `codex/token-efficiency` 保留 provenance。
- 专利 canonical corpus 仍在 `domains/patents/archive/patent-disclosure/` 和 `domains/patents/artifacts/`；本批只删除 Codex archive 旧副本。
- CARP-005 的 safe OTA 组合变化只作为 provenance 保留，不恢复为 active patent portfolio。
- 本批不声明 legal review completed、attorney approval、patent filing completed 或 owner decision。

## 回滚

如需回滚本批，只恢复本批 3 个已删旧正文、`diag-architecture/index.md`、`patent-disclosure/index.md`、执行 manifest、`registry/authorizations.jsonl`、`registry/items.jsonl`、受影响索引以及 CARP/CAMR/CAEF/coverage audit 行。

不得使用全仓 reset 覆盖其他未提交归档工作。恢复锚点为 `pre_delete_commit=db07bd4839016d76f37218cd2b72857ed8575d48`。

## 验证计划

```bash
rtk jq -c . artifacts/manifests/codex-archive-removal-execution-20260710-token-patent-004-006.jsonl artifacts/manifests/codex-archive-removal-preflight-20260710.jsonl artifacts/manifests/codex-archive-phased-migration-removal-20260709.jsonl artifacts/manifests/codex-archive-extract-first-preflight-20260710.jsonl artifacts/manifests/codex-token-efficiency-roadmap-coverage-20260710.jsonl
rtk test ! -e domains/codex/archive/codex-archive/diag-architecture/20260511-112520-codex-token-optimization-roadmap.md
rtk test ! -e domains/codex/archive/codex-archive/patent-disclosure/20260530-215617-patent_skill_archive_note_20260530215400.md
rtk test ! -e domains/codex/archive/codex-archive/patent-disclosure/20260530-220612-patent_skill_archive_note_20260530215400.md
rtk bash tools/knowledge-search.sh "Codex token efficiency roadmap"
rtk bash tools/knowledge-search.sh "safe OTA 组合变化 provenance"
rtk bash tools/knowledge-search.sh "patent disclosure tombstone"
rtk bash tools/knowledge-check.sh --dry-run
rtk git diff --check
```
