---
related: []
target_version: null
test_environment: null
human_reviewed_by: null
human_reviewed_at: null
review_basis: null
id: embedded-team-knowledge-promotion-20260821
title: 嵌入式团队知识提升闭环验证
kind: validation
domain: embedded
path: artifacts/manifests/embedded-team-knowledge-promotion-20260821.md
scope: team-general
visibility: team-internal
status: reviewing
owner: team-core
source:
  type: manual
  from: user-authorized-team-knowledge-maturation
  source_sha256: 21383d3c228cbf679e64e8ec1ed7ec35de74b1486fd8cf8889b7599425569f30
review_after: '2026-11-21'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- embedded
- team-knowledge
- promotion
validation_refs:
- artifacts/manifests/embedded-team-knowledge-promotion-20260821.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- artifacts/manifests/embedded-team-knowledge-promotion-20260821.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-08-21'
updated_at: '2026-08-21'
generated_by_ai: true
ai_role: summarized
ai_model_or_tool: Codex
ai_generated_at: '2026-08-21'
manual_validation_pending: true
summary_zh: 记录 Knowledge Hub 候选向 embedded/knowledge 团队发布面提升的治理契约、ASAN、X5、构建经验、门禁证据与未闭环实机边界。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
---

# 嵌入式团队知识提升闭环验证

## 目标与边界

- goal_statement：把个人 Knowledge Hub 中可复用的嵌入式知识提升到 `workspace://embedded-knowledge`，建立可执行的团队发布治理、内容入口、Owner、来源 hash、回滚和机器门禁。
- completion_claim：本地团队发布工作区已完成治理、内容、双仓技术门禁与候选恢复演练；未声明 commit、push、merge、X5 实机或外部下载服务通过。
- claimant：Codex 实施会话。
- verifier：团队仓 `scripts/check-all.sh`、Hub `knowledge-check` 与完成前独立核验。
- retry_budget：每类门禁最多两轮同类修复；首轮已发现命名和路径路由问题并更新假设后修复。
- staleness_threshold：团队工作区 HEAD、候选 source SHA256 或目标正文漂移即重新运行完整门禁。
- stop_condition：技术门禁 pass；外部/实机证据保持显式 pending，不以文档落盘替代。

## 变更对象

团队仓基线 HEAD：`cadbf4d6777319c8d43b15f842cbea002cd94cef`。本轮只形成未提交本地变更，没有自动 commit、push、merge 或 tag。

主要落地：

- `docs/governance/promotion-contract.md`：团队知识提升契约。
- `docs/governance/knowledge-repo-migration-map.csv`：扩展来源、hash、成熟度、验证、复核和回滚字段。
- `docs/standards/team-knowledge-catalog.md` 与 `x5-platform-topic-catalog.md`：消费导航。
- `docs/runbooks/asan-debug-guide.md`：去 PCR02 绑定的团队方法论。
- `docs/runbooks/x5-sdk-v1-1-2-source-build.md`：主机构建已验证、板级待验证。
- `docs/runbooks/x5-sdk-download.md` 与 `x5-evb-v2p0-first-boot.md`：draft/pending 边界。
- `docs/runbooks/embedded-build-reproducibility-guide.md`：吸收 `-MP` 增量依赖和 debug 符号分层。
- `docs/governance/tests/test_promotion_map.py`：机器校验 Hub 提升行。

Hub 侧同步了 `AGENTS.md`、路径路由、source 边界、promotion policy 和 embedded domain 入口：Hub 保存候选/provenance，团队发布正文由 `workspace://embedded-knowledge` 承担。

## 证据索引

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
| --- | --- | --- | --- | --- | --- |
| `rtk bash scripts/check-all.sh` | 0 | 34 tests；61 docs schema/link；14 skills；secret、shape、shell、artifact 门禁通过 | `workspace://embedded-knowledge` 本地输出 | Team Workflow | 团队全量门禁 |
| `rtk python3 -m unittest docs.governance.tests.test_promotion_map` | 0 | Hub 新增迁移行字段、hash、日期和目标路径通过 | `docs/governance/tests/test_promotion_map.py` | Team Governance | promotion map |
| `rtk bash tools/knowledge-check.sh --dry-run --summary-json --diagnostics` | 0 | Hub 技术检查 pass；0 error，保留 12 项既有过期复核 warning | `~/knowledge-hub` 本地输出 | Hub Workflow | source/path/frontmatter |
| `rtk env PYTHONPATH=~/knowledge-hub pytest -q` | 0 | Hub 全量测试通过 | `~/knowledge-hub` 本地输出 | Hub Engineering | shared unit tests |
| `rtk bash tools/knowledge-restore-drill.sh --source-mode candidate --summary-json` | 0 | 1556 个候选文件离线恢复；0 缺失、0 hash mismatch，全部 smoke gate 通过 | `.cache/knowledge-hub/restore-drill-candidate.json` | Hub Recovery | signature `35bb5db5...` |
| `rtk bash tools/knowledge-final-gate.sh --final-profile product --summary-json` | 0 | 19 项 hard check 全部通过；终态为 needs-review，仅保留 owner/真实证据、交付、远端发布与异地恢复边界 | `.cache/knowledge-hub/final-gate-product-quick.json` | Hub Product | product quick gate |
| `rtk bash tools/knowledge-orphan-files.sh --json` | 0 | changed-only 正文覆盖 ok，新增 validation 已精确登记 | `~/knowledge-hub` 本地输出 | Hub Governance | registry/body coverage |
| 首轮 `check_docs_naming.py --changed-only` | 1 | 证伪 `docs/catalog.md` 和带点号版本文件名；已迁移到合法 slug | 本记录 Deviation | Negative Evidence | naming repair |
| 首轮 Hub `knowledge-check --dry-run --json --diagnostics` | 1 | 证伪旧 canonical path 与 registry summary 漂移；更新路由与 registry 后复跑通过 | 本记录 Deviation | Negative Evidence | authority repair |

## 结果矩阵

| case | 期望 | 实际 | 状态 |
| --- | --- | --- | --- |
| 团队发布治理 | 有 contract、Owner、source hash、rollback 和机器门禁 | 已落地并通过团队全量门禁 | pass |
| ASAN 团队化 | 去除项目构建变量、二进制名和部署路径 | 已替换旧项目强绑定正文 | pass |
| X5 主机构建 | 固定版本、构建证据、边界清晰 | 主机构建已验证；板级未声明 | pass-with-boundary |
| X5 首启/恢复 | 资料可执行且不伪造设备结果 | draft；真实 EVB 待验证 | pending-device |
| X5 SDK 下载 | 不保存凭据并标注外部时效 | secret scan 通过；服务可用性待复核 | pending-external |
| 项目经验提炼 | 合并现有通用入口而非复制事故正文 | 已合并构建可复现指南 | pass |
| 双仓权威 | Hub 候选/provenance 与团队发布面分离 | 规则和团队契约已同步；目标尚未 commit | pass-local-only |

## Deviation 与修复记录

1. 团队命名门禁拒绝根 `docs/catalog.md` 和 `x5-sdk-v1.1.2-source-build.md`。修复为 `docs/standards/team-knowledge-catalog.md` 与 `x5-sdk-v1-1-2-source-build.md`，并全量更新链接和迁移映射。
2. Hub 路径门禁把 `~/embedded/knowledge` 识别为旧外部默认路径。修复为稳定逻辑 URI `workspace://embedded-knowledge`，避免个人绝对路径进入运行规则。
3. `knowledge-new.sh` 文档示例中的 `--ai-model-or-tool` 与当前 CLI 不一致，首轮 dry-run 失败；按实际 `--help` 去掉未知参数后事务化创建 validation。未修改 CLI，本记录保留为负证据。
4. 产品终检并发运行时，健康 pytest 首轮超过固定 90 秒并触发 `TimeoutExpired`。将门禁超时提取为有界 `UNIT_TEST_TIMEOUT_SECONDS=180` 后，定向测试 16 项通过，候选恢复演练和产品终检复跑通过；没有放宽测试断言或接受失败退出码。

## 剩余证据与风险

- X5 EVB 上电、网络/ADB、Fastboot/DFU 未执行；对应文档保持 `maturity: draft`。
- SDK 下载 HTTP/FTP 入口、账号有效性和远端文件完整性未联网复核；下载文档设置短期 `review_after=2026-09-05`。
- 团队仓变更尚未 commit/push；没有目标 commit hash，Hub 只能声明本地发布候选已闭环，不能声明远端团队库已发布。
- Hub 还有 12 项与本任务无关的过期复核 warning；未借本轮范围清零或改写。
- 旧 Hub embedded 正文可继续作为候选/provenance；其 lifecycle 状态不得替代团队仓发布状态。删除或 retire 仍需独立 hash-bound 授权。

## Recovery Prompt

```text
Goal: 完成 embedded/knowledge 本地变更的人审、commit 和远端发布，并回写目标 commit/hash。
Completed: 治理、ASAN、X5、构建经验、目录、Owner、迁移账本和本地门禁。
Do not repeat: 不再创建非法 docs 根 catalog；不使用带点号 slug；不把 Hub 旧路径恢复为团队默认入口。
Next action: 团队 Owner 审阅 diff；需要发布时显式授权 commit/push。
Required verification: scripts/check-all.sh；Hub knowledge-check；发布后重算目标文件 hash。
Retry budget: 每类失败 2 次，连续失败两次先 replan。
Staleness threshold: HEAD/source/target 任一漂移即全量重跑。
Open items: X5 device、external endpoint、target commit/push。
```

## 结论

当前结论为“本地技术闭环达到可评审成熟态，发布与外部/实机证据待完成”。产品终检 19 项 hard check 全部通过，整体状态按治理契约保持 `needs-review`、非 terminal。本记录保持 `reviewing` 和 `manual_validation_pending`；它不生成 owner lifecycle decision，不自动提升 Hub active，不授权远端写入。
