# Codex archive session-wrap 删除执行批次 2026-07-10

## 摘要

本批根据用户在当前会话的条件授权“如果旧源没用了，授权删除”，在两个只读子代理审计后删除 5 个已完成 extract-first 或 tombstone-only 审计的旧 `session-wrap` 正文。

本批只删除以下 5 个旧正文：

- `domains/codex/archive/codex-archive/session-wrap/20260602-132025-codex-adk-hardcut-session-wrap.md`
- `domains/codex/archive/codex-archive/session-wrap/20260627-230744-knowledge-hub-final-hardcut-session-wrap.md`
- `domains/codex/archive/codex-archive/session-wrap/20260526-162109-pcr02-session-wrap-20260526-customer-ro-sd-upgrade.md`
- `domains/codex/archive/codex-archive/session-wrap/20260524-231443-codex-session-wrap-20260524-openai-local-runtime-boundary.md`
- `domains/codex/archive/codex-archive/session-wrap/20260518-223626-mcu-session-wrap-firmware-release-nas.md`

本批不删除 `memory-curation`、其他 `session-wrap` 正文或任何 canonical/migrated target；不写 `~/.codex/memories`；不提升 active；不生成 owner decision；不修改源项目；不 push。

结构化台账：`artifacts/manifests/codex-archive-removal-execution-20260710-session-wrap-caef-001-004-009.jsonl`。

## 授权

| Field | Value |
| --- | --- |
| authorization_id | `auth-20260710-codex-archive-delete-session-wrap-caef-001-004-009` |
| authorized_by | `leiwenjun` |
| authorization_basis | 当前会话用户指令：如果旧源没用了，授权删除 |
| pre_delete_commit | `db07bd4839016d76f37218cd2b72857ed8575d48` |
| scope | exactly `CAEF-20260710-001..004,009`, `CARP-20260710-011`, and `CAMR-20260709-008` file-level entries |

## 删除条目

| Row | Source | SHA256 | Disposition |
| --- | --- | --- | --- |
| `CARE-20260710-013` | `session-wrap/20260602-132025-codex-adk-hardcut-session-wrap.md` | `5e95b362b621e979797ad734f928dcc5cfa31d673adfe68fe4ac0f361c79cf10` | ADK hardcut source-to-live coverage audit 已迁移；旧正文 tombstone |
| `CARE-20260710-014` | `session-wrap/20260627-230744-knowledge-hub-final-hardcut-session-wrap.md` | `cdfca7188a356f269dc4513f79bf6238e20d8fc0080e4a5ff8acd424c8ef62e6` | Knowledge Hub final hardcut tombstone-only audit 已记录；旧正文 tombstone |
| `CARE-20260710-015` | `session-wrap/20260526-162109-pcr02-session-wrap-20260526-customer-ro-sd-upgrade.md` | `f5044d662e42b4e11b259ee2137b42be6774c3259fe7e3fb3fc7bbdb1ef01c62` | PCR02 `/customer` ro SD upgrade 历史阶段证据已迁移；旧正文 tombstone |
| `CARE-20260710-016` | `session-wrap/20260524-231443-codex-session-wrap-20260524-openai-local-runtime-boundary.md` | `b731c2ab6e95835b0c38c37241ebda5c5c8e903568a51f6ca49c274a91f82a79` | OpenAI local runtime boundary archive-only/freshness-required 审计已迁移；旧正文 tombstone |
| `CARE-20260710-017` | `session-wrap/20260518-223626-mcu-session-wrap-firmware-release-nas.md` | `f4b56957d2d216c1167215048add05d94c493aaaf9cdae110da1054c907fe33c` | firmware-release-tools NAS 发布同步历史会话已迁移；旧正文 tombstone |

## Tombstone 摘要

`20260602-132025-codex-adk-hardcut-session-wrap.md` 的长期价值已由 `artifacts/manifests/codex-adk-hardcut-source-to-live-audit-20260710.md` 和 live Codex source-to-live 规则覆盖。保留结论仅限 source freshness、声明式 source-to-live apply、active-only residual scan、managed source 格式修复后重跑 plan/apply/drift/check，以及 upstream 模板或 skill body residual 先在源头修复。`memory_candidates` 仍是候选，不写 memory、不提升 active。

`20260627-230744-knowledge-hub-final-hardcut-session-wrap.md` 已由 `artifacts/manifests/codex-knowledge-hub-final-hardcut-tombstone-audit-20260710.md`、Hub final goal、path routing、operational maturity 和 `codex-archive.ref.md` 覆盖。该 tombstone 只保留旧入口 provenance、project README/registry 路由、review/owner 边界和 historical session text 不等于 runtime rule 的结论；不得作为 owner decision、active promotion 或 memory 写入证据。

`20260526-162109-pcr02-session-wrap-20260526-customer-ro-sd-upgrade.md` 已迁移到 `projects/pcr02/archive/engineering-archive/pcr02/session/pcr02_customer_ro_sd_upgrade_20260526.md`。该记录只保留 2026-05-26 历史阶段证据：`/customer ro,noatime`、dirty build、SD 包构建命令、`SigmastarUpgradeSD.bin` SHA256 和未上板验证风险；不得声明当前 PCR02 `/customer` 或 release truth。

`20260524-231443-codex-session-wrap-20260524-openai-local-runtime-boundary.md` 已迁移到 `artifacts/manifests/codex-openai-local-runtime-boundary-20260524.md`。该记录只作为 archive-only/freshness-required 治理记录，保留 official docs freshness gate、小 manifest/contract 先行、hook contract 非完整 enforcement、automation report-only、Docs MCP read-only 和 source-to-live health chain 等历史边界；不得声明 OpenAI 或 Codex 官方事实当前有效。

`20260518-223626-mcu-session-wrap-firmware-release-nas.md` 已迁移到 `projects/firmware-release-tools/archive/release/2026-05-18-nas-release-sync-session.md`。该记录只保留 2026-05-18 NAS 发布同步历史会话：`release-to-nas`、staging/checksum、防覆盖、tag 顺序、三固件历史版本和敏感信息边界；不得声明当前 MCU 发布基线或当前 NAS/版本状态。

## 保留边界

- 本批只删除 5 个 file-level old source；`session-wrap` topic 仍保持 blocked，因为还有其它未覆盖正文。
- 迁移目标的 status、review_status、active/current 结论不因旧源删除而升级。
- 不写 memory、不提升 active、不生成 owner decision、不修改源项目、不 push。
- OpenAI/Codex 官方当前事实必须重新 freshness review；本批只保留历史治理边界。
- PCR02 和 firmware-release-tools 记录均为历史阶段证据，不声明当前 release truth。

## 回滚

如需回滚本批，只恢复本批 5 个已删旧正文、`session-wrap/index.md`、执行 manifest、`registry/authorizations.jsonl`、`registry/items.jsonl`、受影响索引以及 CAEF/CARP/CAMR 行。

不得使用全仓 reset 覆盖其他未提交归档工作。恢复锚点为 `pre_delete_commit=db07bd4839016d76f37218cd2b72857ed8575d48`，且 canonical/migrated target 不随本批回滚删除。

## 验证计划

```bash
rtk jq -c . artifacts/manifests/codex-archive-removal-execution-20260710-session-wrap-caef-001-004-009.jsonl artifacts/manifests/codex-archive-extract-first-preflight-20260710.jsonl artifacts/manifests/codex-archive-removal-preflight-20260710.jsonl artifacts/manifests/codex-archive-phased-migration-removal-20260709.jsonl
rtk bash -lc "test ! -e domains/codex/archive/codex-archive/session-wrap/20260602-132025-codex-adk-hardcut-session-wrap.md"
rtk bash -lc "test ! -e domains/codex/archive/codex-archive/session-wrap/20260627-230744-knowledge-hub-final-hardcut-session-wrap.md"
rtk bash -lc "test ! -e domains/codex/archive/codex-archive/session-wrap/20260526-162109-pcr02-session-wrap-20260526-customer-ro-sd-upgrade.md"
rtk bash -lc "test ! -e domains/codex/archive/codex-archive/session-wrap/20260524-231443-codex-session-wrap-20260524-openai-local-runtime-boundary.md"
rtk bash -lc "test ! -e domains/codex/archive/codex-archive/session-wrap/20260518-223626-mcu-session-wrap-firmware-release-nas.md"
rtk bash tools/knowledge-search.sh "Codex ADK hardcut source-to-live"
rtk bash tools/knowledge-search.sh "Knowledge Hub final hardcut tombstone"
rtk bash tools/knowledge-search.sh "PCR02 customer ro SD upgrade"
rtk bash tools/knowledge-search.sh "OpenAI local runtime boundary"
rtk bash tools/knowledge-search.sh "firmware-release-tools NAS 发布同步"
rtk bash tools/knowledge-check.sh --dry-run
rtk git diff --check
```
