---
human_reviewed_by: leiwenjun-via-codex-delegation
human_reviewed_at: 2026-07-13
human_review_decision: accept-as-review-record
review_authorization: auth-20260713-knowledge-hub-obsidian-audit-review
id: knowledge-hub-comprehensive-maturity-remediation-20260713
title: Knowledge Hub 全面成熟度治理与 Obsidian 集成审计 2026-07-13
kind: audit
domain: governance
path: artifacts/manifests/knowledge-hub-comprehensive-maturity-remediation-20260713.md
scope: team-general
visibility: team-internal
status: archived
owner: leiwenjun
source:
  type: manual
  from: Codex implementation and audit of user-requested Knowledge Hub comprehensive optimization
review_after: '2026-10-13'
review_status: human-reviewed-accepted
promotion: none
promotion_decision: none; governance audit candidate only, no owner decision, no active promotion, no memory write, no source
  project write and no remote publish
tags:
- knowledge-hub
- maturity
- body-coverage
- frontmatter
- artifact-vault
- search-ranking
- obsidian
- regression
- report-only
- no-active-promotion
- no-memory-write
validation_refs:
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics --as-of 2026-07-13
- rtk bash ~/knowledge-hub/tools/knowledge-orphan-files.sh --all --strict --json
- rtk bash ~/knowledge-hub/tools/knowledge-regression.sh --json --suite full --as-of 2026-07-13
- rtk bash ~/knowledge-hub/tools/knowledge-final-gate.sh --json --final-profile product --regression-suite full --as-of 2026-07-13
evidence_strength: implemented-control-plane-plus-full-regression-and-official-docs-review
evidence_refs:
- artifacts/manifests/knowledge-hub-comprehensive-maturity-remediation-20260713.md
- artifacts/manifests/knowledge-hub-comprehensive-maturity-remediation-20260713.jsonl
- registry/body-coverage.json
- governance/obsidian-integration.md
- indexes/obsidian-home.md
- tools/knowledge-check.sh
- tools/knowledge-orphan-files.sh
- tools/knowledge-search.sh
- tools/knowledge-regression.sh
created_at: '2026-07-13'
updated_at: '2026-07-13'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-07-13'
summary_zh: 记录 Knowledge Hub 全面成熟度治理：补正文冻结覆盖、frontmatter 生命周期镜像、专利附件 vault 身份门禁、可解释搜索排序和 Obsidian 安全呈现层；full regression 140/140
  通过，两个新增候选已按用户明确授权完成受托人工复核记录。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: reviewed
---

# Knowledge Hub 全面成熟度治理与 Obsidian 集成审计

> 历史基线说明：本记录封存的是 2026-07-13 较早阶段的治理闭环结论。后续产品化实现新增 31 项目 readiness、共享事务内核、FTS 检索、导出、恢复演练和产品成熟度门禁后，当前结论以 [Knowledge Hub 产品成熟度全面实现审计](knowledge-hub-product-maturity-implementation-20260713.md) 为准。本记录中的 `mature final_status=ok` 只证明当时的治理 profile，不再作为“目标、架构、功能、性能、维护和项目真实证据已全面终态成熟”的依据。

## 结论

Knowledge Hub 的目标架构已经收敛为“Markdown 唯一正文 + registry 权威账本 + gate 控制高风险动作 + Obsidian 可选呈现层”。本轮把此前“控制面成熟、全正文和附件边界仍有缺口”的状态推进到可验证闭环。

自动治理层已经成熟落地；两个新增候选已按用户明确授权完成 `accept-as-review-record`，但内容复核仍不等于 owner decision、active promotion 或发布签收。本记录不生成 owner decision、不关闭 owner gate、不提升 active、不写 memory、不修改源项目、不发布远端状态。

## 本轮落地

| 方面 | 落地结果 | 边界 |
|---|---|---|
| 正文覆盖 | `registry/body-coverage.json` 冻结 12 个历史/基线集合；全量 212 份 Markdown 中 80 份精确登记、132 份集合覆盖、0 缺失 | 集合只覆盖固定路径 inventory，不创建 status/owner/promotion |
| 生命周期 | `knowledge-check` 校验已声明 frontmatter 的 `status`、`owner`、`review_after` 与 registry 一致；历史 20 处漂移已按 registry 收口 | 没有自动提升 active；canonical `current/` 路径不隐含 active |
| 附件资产 | 专利附件清单固定 181 行身份：178 个 vault 文件逐一校验 size/SHA256，3 个 RAR 标为 `external-reference-only` | 不伪造缺失 RAR 的本地存在性；vault 禁止额外文件、symlink 和路径穿越 |
| 搜索 | 中英文 term AND 匹配，按 canonical path、registry、status、title/id/tags/summary/path/body 排序并输出 `score`/`why_selected` | 历史 manifest 和机器 registry 降权，不改变权威状态 |
| Obsidian | 新增 `indexes/obsidian-home.md`、`governance/obsidian-integration.md`、本机私有 `.obsidian/` 边界和附件 intake | Obsidian 不是 registry/gate；暂不提交不完整 `.base`，CLI 不进入必需依赖 |
| 可维护性 | 工具文档、schema、artifact/vault 规则、稳定命令和负向回归同步更新 | 不做无关泛化重构 |

## Obsidian 关系

Obsidian 是 Knowledge Hub 的本地交互客户端，不是另一个知识库。它直接消费同一份 Markdown，通过 links、backlinks、Graph、Properties 和未来只读 Bases 改善人工阅读；生命周期、责任、授权和终态仍由 registry 与 Hub 工具决定。

官方资料复核见 `governance/obsidian-integration.md`。截至本轮，本机未发现 `obsidian` CLI，因此没有引入 CLI 自动化或 community plugin 供应链。

## 验证证据

- `rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics --as-of 2026-07-13`：pass；errors=0；warnings=0。
- `rtk bash ~/knowledge-hub/tools/knowledge-orphan-files.sh --all --strict --json`：212 checked；80 exact；132 collection；0 missing；coverage contract pass。
- artifact vault：181 identity rows；178 required present；3 external-reference-only；missing/hash/size/extra/duplicate/symlink 均为 0。
- `rtk bash ~/knowledge-hub/tools/knowledge-search.sh ASAN --json --limit 5`：团队级 active ASAN runbook 排名第一。
- `rtk bash ~/knowledge-hub/tools/knowledge-search.sh "ST77912 决策" --json --limit 5`：两条 reviewing 决策候选排名前二。
- `rtk bash ~/knowledge-hub/tools/knowledge-regression.sh --json --suite full --as-of 2026-07-13`：137 test function、140 result、4 worker、failed_ids=[]。
- `rtk bash ~/knowledge-hub/tools/knowledge-final-gate.sh --json --final-profile mature --full-regression --as-of 2026-07-13`：授权复核后 `final_status=ok`；`automatic_governance.status=complete`；check/regression 均 pass；blockers=[]；gap_count=0。

## Full regression slowest 10

| 排名 | result id | 秒 | 状态 |
|---:|---|---:|---|
| 1 | `review-after-as-of-deterministic` | 12.827 | pass |
| 2 | `source-coverage-date-filename-selection` | 9.475 | pass |
| 3 | `review-queue-json-contract` | 9.002 | pass |
| 4 | `review-queue-apply-tool-contract` | 8.192 | pass |
| 5 | `final-gap-readability-positive-contracts` | 7.874 | pass |
| 6 | `final-gate-default-regression-path` | 5.697 | pass |
| 7 | `final-gate-mature-review-queue-owner-review-blocker` | 5.660 | pass |
| 8 | `final-gate-owner-review-blocker` | 5.578 | pass |
| 9 | `final-gate-skip-regression-blocker` | 5.464 | pass |
| 10 | `final-gate-source-final-state-field-gap` | 5.421 | pass |

本表是后续性能优化唯一 watchlist；本轮未做泛化重构。

## 剩余人工项

1. PCR02 三条 owner-ready candidate 仍按 `pcr02-owner-ready-validation-paths-20260713` 等待真实 owner、实机和发布验证，尤其 ST77912 高温老化、SCLK/EMI 和端到端显示证据。
2. 本轮两个 Knowledge Hub candidate 的内容复核已经关闭，但 push/merge/release 仍需单独授权。

## 授权复核闭环

- authorization：`auth-20260713-knowledge-hub-obsidian-audit-review`
- queue coverage：3/3 complete
- decision：`accept-as-review-record`
- item status：Obsidian 规范保持 `reviewing`；本审计保持 `archived`
- must-not：不生成 owner decision、不提升 active、不写 memory、不修改源项目、不改变远端状态

## 回滚

- 工具和 registry 改动可按本地 Git commit 回滚。
- `registry/body-coverage.json` 不得单独删除；回滚时必须同时回滚 orphan/check 契约和文档。
- 不通过删除 `external-reference-only` 行或弱化 hash 校验来制造附件全绿。
