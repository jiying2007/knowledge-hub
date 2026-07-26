---
related:
- projects/agent-dev-kit/README.md
- indexes/obsidian-home.md
- indexes/project-readiness.md
human_reviewed_by: null
human_reviewed_at: null
review_basis: null
decision_status: null
decision_date: null
aliases:
- Agent Dev Kit 团队 Harness Readiness v1 吸收决策候选
id: agent-dev-kit-harness-readiness-decision-20260717
title: Agent Dev Kit 团队 Harness Readiness v1 吸收决策候选
kind: decision
domain: projects/agent-dev-kit
path: projects/agent-dev-kit/decisions/harness-readiness-v1-candidate.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: manual
  from: 源证据保留在 agent-dev-kit change artifact 与官方 OpenAI URL；不复制二级文章正文或图片。
  source_sha256: 7ce01cdbf3966fc66fbc75c3898372a31cc330dbd363f561e64b2c16eadeb1ed
review_after: '2026-10-15'
review_status: human-reviewed-accepted
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- agent-dev-kit
- harness-readiness
- ai-coding
- decision
validation_refs:
- projects/agent-dev-kit/decisions/harness-readiness-v1-candidate.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: reviewing-validation-pending
evidence_refs:
- projects/agent-dev-kit/decisions/harness-readiness-v1-candidate.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-07-17'
updated_at: '2026-07-26'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-07-17'
manual_validation_pending: true
summary_zh: 以无权重七维证据投影吸收团队 Harness Engineering，复用 ADK 现有 workflow、Skill 和 capability health；候选保持 reviewing，不启用外部 runtime、MCP
  或 active promotion。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
---

# Agent Dev Kit 团队 Harness Readiness v1 吸收决策候选

## 背景

团队 Harness Engineering 文章提出用上下文、工具、编排、记忆、评估和约束把“好代码”的标准固化到 Agent 运行环境。`agent-dev-kit` 已有 requirements、planning、review、verification、knowledge archive、capability health 等治理能力，但此前缺少一个跨项目、可重复、无厂商绑定的 readiness 投影，无法用同一证据模型回答“项目是否已为可靠 AI Coding 做好准备”。

本候选记录 2026-07-17 的吸收结论。它只保存可复用决策和验证摘要；实现细节与当前事实仍以源项目为准。

## 适用范围

- 适用：`agent-dev-kit` 的项目 readiness 检查、团队 Harness 基线复核、后续跨仓试点。
- 不适用：衡量个人绩效、AI 代码占比、PR 数量或 Token 消耗；替代人工架构评审；自动安装 MCP；自动修改目标项目。
- 运行边界：本地、只读、确定性扫描；默认 report-only，只有显式 `--gate` 才根据结论返回非零状态。
- 权限边界：不需要外部网络、凭证或登录态，不启用外部 runtime，不授权 active promotion。

## 权威来源

- primary source：OpenAI《Harness engineering: leveraging Codex in an agent-first world》，`https://openai.com/index/harness-engineering/`。
- secondary source：用户提供的 atreusliu 团队规范摘录；原始文章 URL 未提供，因此保留 `review-required`，不作为唯一权威来源。
- project decision：`agent-dev-kit/docs/harness-engineering-analysis.md`。
- change artifact：`agent-dev-kit/docs/changes/harness-team-readiness-v1/`。
- implementation contract：`agent-dev-kit/manifests/harness_readiness_contracts.json`。
- source owner：`agent-dev-kit` maintainers；本 Hub 条目不覆盖源项目当前事实。

## 决策问题

是否把文章中的 Harness 思路吸收为 ADK 的无权重、证据驱动 readiness 能力，同时拒绝评分 KPI、厂商绑定和“缺 MCP 即不合格”等不可迁移假设？

## 选项

| 选项 | 影响范围 | 成本 | 风险 |
| --- | --- | --- | --- |
| A. 原样复制文章体系 | 引入 CodeBuddy/Knot、100 分审计和固定目录 | 高 | 厂商绑定、刷分、与 ADK 既有能力重复 |
| B. 只保留理念，不做可执行检查 | 文档层 | 低 | 规范仍不可验证，团队容易回到主观审查 |
| C. 选择性吸收为七维证据投影（候选建议） | ADK CLI、manifest、测试、capability health、文档 | 中 | 初始启发式仍需跨仓试点校准 |

## 吸收与拒绝边界

### 吸收

1. 用渐进式上下文和仓库内记录维持项目可理解性。
2. 把 Spec、执行、验证、Review、恢复和知识连续性串成闭环。
3. 将工具接入与权限边界作为显式证据，而不是隐式假设。
4. 用 owner、`last_verified_at`、blocker 和 next action 表达可治理状态。
5. 增加 freshness / entropy control，避免 Rules、Skills 和知识资产只增不减。

### 拒绝或降级

1. 不采用 100 分加权总分和 S/A/B/C/D 等级；七个维度均不加权，状态为 `pass | partial | needs-review | blocked | not-applicable`。
2. 不把 AI 代码占比、Token、PR 数量或提交速度作为质量 KPI。
3. 不把缺少 MCP 自动判为缺陷；没有必要的外部上下文时应为 `not-applicable`。
4. 不把 CodeBuddy、Knot、特定目录和特定模型写入 ADK core。
5. 不要求所有小改动都创建完整 Spec；沿用 ADK 的风险分级与小任务轻流程。
6. 不把静态配置存在等同于生产有效；field evidence 只能是 `not-verified`，直到后续试点提供独立证据。

## 证据

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
| --- | ---: | --- | --- | --- | --- |
| `rtk agent-dev-kit/tests/test_harness_readiness.sh` | 0 | 定向契约、负例、预算、脱敏和 gate 语义通过。 | `agent-dev-kit/tests/test_harness_readiness.sh` | Project | readiness implementation |
| `rtk agent-dev-kit/tests/run_all.sh --fail-fast --timing-json /tmp/harness-readiness-full-timing.json` | 0 | 完整回归 53/53 通过。 | `/tmp/harness-readiness-full-timing.json`（临时证据，不归档） | Tool | verification evidence |
| `rtk agent-dev-kit/scripts/devkit.sh validate --strict` | 0 | manifest、workflow、skill 与 schema 严格验证通过。 | `agent-dev-kit/docs/changes/harness-team-readiness-v1/verification-evidence.md` | Project | change artifact |
| `rtk scripts/check-all.sh --quick` | 1 | 54/56；仅根仓 current-status/subrepo-state 因本次 `agent-dev-kit` 未提交变更而失败，不是实现回归。 | `agent-dev-kit/docs/changes/harness-team-readiness-v1/negative-results.md` | Project | known dirty-worktree condition |
| `rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics --as-of 2026-07-17` | 0 | Hub 结构检查 0 error、0 warning。 | 本候选与 Hub registry/index 变更 | Knowledge Hub | transaction `kh-20260717T151518Z-12bd8c2e` |

## 候选决策

建议批准选项 C：以 `devkit.sh harness readiness` 作为可执行入口，将七维证据投影纳入 `team-harness-readiness` capability health，并复用 ADK 现有 workflow、Skill 和验证闭环。该建议不授权发布、source-to-live 刷新、外部写入或 active promotion。

## 当前结论

- 源项目实现与 change artifact 已完成独立 review，最终 finding 为 blocker 0、major 0、minor 0。
- 完整回归 53/53 通过；定向 readiness、strict validation、capability health、CLI 文档对齐、format、file mode 和 `diff --check` 均通过。
- 对 `agent-dev-kit` 自身的 report-only 基线为 `partial`：六维 `partial`，MCP 维度 `not-applicable`。主要缺口是根 `AGENTS.md` 超过当前预算、缺少 `.adk/harness-readiness.json` owner/验证日期、缺少 CODEOWNERS、没有 field evidence。
- Hub 状态仍为 `reviewing`，`manual_validation_pending=true`，没有 active promotion；以上均不是 owner 已批准结论。

## 生效条件

1. owner 复核并签收本候选的吸收/拒绝边界。
2. 在至少两个不同类型仓库、由至少两位操作者完成不少于 30 天的 report-only 试点。
3. 记录误报、漏报、扫描预算和实际 next action 可执行性，并据此评审 contract 调整。
4. 补充用户提供文章的原始 URL，完成 secondary source provenance 复核。
5. 需要进入运行资产时，另走 `agent-dev-kit -> ~/codex -> ~/.codex` 的 source-to-live 门禁；本候选不替代该链路。

## 回滚条件

- 出现秘密值泄露、越界扫描、非确定性结果或目标仓被修改时，立即停止试点并回滚 readiness 入口。
- 两仓试点显示关键维度高误报/漏报且无法通过 contract 修正时，将本候选标为 `superseded` 或 `rejected`。
- 官方 Harness 定义或 ADK 权威工作流发生实质变化时，以新决策候选替代本记录，不静默改写历史结论。

## 风险与限制

- 当前证据主要是 fixture 与 ADK 自检，不代表真实团队采用效果。
- readiness 只证明仓库中存在可核验信号，不证明代码、架构或线上运行必然正确。
- 启发式证据可能被模板、示例或过期文件误导；实现已排除常见 decoy，但仍需现场样本校准。
- 当前工作区存在用户原有 dirty 子仓；本次未清理、覆盖或提交这些变更。
- 临时 timing JSON 不进入长期知识；长期结论以本候选和源 change artifact 为准。
- 不保存密钥、raw session、完整日志或用户文章正文。

## Review 周期

- owner：leiwenjun（待人工确认）。
- review_after：2026-10-15。
- 下一次复核：两仓/两操作者/30 天试点证据、误报漏报、secondary source URL、owner 是否批准 active 或维持 reviewing。
