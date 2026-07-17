---
id: llm-agent-portable-full-gate-remediation-20260717
title: LLM Agent 可移植 Full 门禁修复验证 2026-07-17
kind: validation
domain: projects/llm-agent
path: projects/llm-agent/validation/2026-07-17-portable-full-gate-remediation.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: repository-report
  from: llm_agent@150fdee1509b899bbb0d8c0762b7a9313b63ba94/reports/wechat-intake-portable-full-gate-repair-2026-07-17.md
  source_sha256: 884d5f86911c5e630e453baaf607e4128e69a12a44c020ed841b046e10f2eff4
review_after: '2026-10-17'
created_at: '2026-07-17'
updated_at: '2026-07-17'
promotion: none
promotion_decision: none; local source remediation evidence does not authorize source remote push, release, evidence-ready
  status or active promotion
tags:
- llm-agent
- exact-source
- validation
- full-gate
- portability
- wechat
- ai-generated
- manual-validation-pending
related:
- projects/llm-agent/validation/2026-07-17-exact-source-full-gate-audit.md
- projects/llm-agent/validation/2026-07-15-exact-source-quick-gate-audit.md
- projects/llm-agent/validation/project-readiness.md
- governance/product/validation/project-readiness.md
validation_refs:
- rtk scripts/check-all.sh --full
- rtk tests/test_wechat_intake_ledger.sh
- rtk tests/test_file_modes_worktree.sh
- rtk scripts/check-wechat-intake-ledger.sh . --require-corpus
artifact_refs:
- llm_agent@150fdee1509b899bbb0d8c0762b7a9313b63ba94/reports/wechat-article-intake.manifest.json#sha256=93c926be842eb4480cce754a74f10f8e9fe5977f60cbce09c31d4320e2222e19
target_version: llm_agent@150fdee1509b899bbb0d8c0762b7a9313b63ba94 with unchanged seven gitlinks
test_environment: isolated linked worktree and exact local submodule clones under /tmp; main workspace live corpus; current
  host runtime dependencies; no remote network
summary_zh: 修复 WeChat intake 外部语料与纯 Git checkout 的输入契约，并补齐 linked worktree、submodule gitfile 与 ADK 临时精确克隆兼容性；隔离源码 Full 门禁
  62/62、主工作区 313 篇 live-corpus 校验均通过，源码远端发布与正式制品证据仍未闭环。
review_status: manual-entry-pending-review
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: checked
evidence_strength: direct-command
evidence_refs:
- projects/llm-agent/validation/2026-07-17-exact-source-full-gate-audit.md
- llm_agent@150fdee1509b899bbb0d8c0762b7a9313b63ba94
generated_by_ai: true
ai_role: drafted-and-verified
ai_model_or_tool: Codex
ai_generated_at: '2026-07-17'
human_reviewed_by: null
human_reviewed_at: null
review_basis: null
manual_validation_pending: true
manual_validation_reason: 源码修复已在本机完成，但 source remote publish、跨主机复现、正式 artifact、release record 与生产 rollback 仍未闭环。
aliases:
- LLM Agent 可移植 Full 门禁修复验证 2026-07-17
---

# LLM Agent 可移植 Full 门禁修复验证 2026-07-17

## 验证目标

验证 2026-07-17 精确源码 Full 审计发现的唯一失败，是否已在不提交原始公众号语料、不削弱 live-corpus 校验、不修改 gitlink 的前提下完成修复；同时验证标准 linked worktree 与 submodule gitfile 不再被 file-mode/harden 门禁误判。

本报告证明的是本机精确源码、隔离 worktree 和当前 live corpus 上的命令结果。它不证明源码已发布到远端，不证明正式 artifact、跨主机复现、生产采用或 rollback 已完成，也不构成 owner 内容签署或 lifecycle promotion。

## 验证对象

| 对象 | 基线 | 修复后 |
| --- | --- | --- |
| 根仓 `llm_agent` | `383274fed93ad143cabb1dbd977e1b766eca5c04` | `150fdee1509b899bbb0d8c0762b7a9313b63ba94` |
| 根仓改动 | 无 | 11 个文件，570 行新增、59 行删除 |
| 七个 gitlink | 基线 commit | 全部未变 |
| WeChat ledger | 313 条已跟踪记录 | 313 条，SHA256 `15f8f153dc09f19c12ce151e9e2801ed64f5c87db442143a2726473c5e16ad7f` |
| Decision overlay | 313 条决策加表头 | SHA256 `17ec7898faf903641965578a62176bf350f954f4795081574a7dd48b6d0f0a01` |
| Snapshot manifest | 不存在 | SHA256 `93c926be842eb4480cce754a74f10f8e9fe5977f60cbce09c31d4320e2222e19` |

修复提交已经通过 `--ff-only` 快进到本地主分支；`origin/main` 仍停留在基线之前，本报告不授权源码远端推送。

## 修复契约

### WeChat 双层校验

- 纯 Git checkout 先校验 ledger JSON schema、连续 ID、安全相对路径、external-code policy、decision 引用、精确条数和 SHA256，再以 `mode=committed-snapshot` 通过。
- 明确提供 corpus，或工作区存在受约定目录时，重新从实际 Markdown 生成 ledger 并逐字节比对，以 `mode=live-corpus` 通过。
- `--require-corpus` 在 corpus 缺失时保持 fail closed；snapshot 不冒充原始 corpus 留存证明。
- generator 支持显式 `--articles-dir`、manifest 更新和 `--no-manifest`，保留既有调用兼容性。

### Worktree 与 ADK harden

- 根 file-mode checker 使用 `git rev-parse --show-toplevel` 识别仓库，兼容 `.git` 目录、linked-worktree `.git` 文件和 submodule gitfile。
- `--fix` 与 `100644/100755` 策略保持不变；新 fixture 覆盖 unexpected/missing executable 及修复后复验。
- harden 先用根仓修复后的 checker 校验真实 ADK 子模块，再从当前 clean ADK HEAD 创建 `--no-hardlinks` 临时本地 clone。
- 临时 clone 必须核对 HEAD 相等，只为六个已登记 sibling reference 建立临时只读入口，并运行 ADK 52 项完整测试；不修改 ADK、reference submodule 或 gitlink。

## 环境与边界

- 日期：2026-07-17。
- 隔离 worktree：`/tmp/llm-agent-portable-wechat-gate-20260717`。
- 主工作区：`~/bin/llm_agent`，用于集成后真实 313 篇 corpus 校验。
- 网络：验证过程不依赖远端网络。
- 工作树保护：集成前后均保留原有 `OpenSpec`、`superpowers`、`vibeflow` dirty 状态，以及 `hermes/`、`hermes_data/` 未跟踪目录；未执行 reset、clean 或删除。
- 分支保护：本地 `main` 仅做一次 fast-forward；未 merge commit、rebase、force push、tag 或 release。

## 验证命令

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
| --- | --- | --- | --- | --- | --- |
| `rtk shellcheck scripts/check-wechat-intake-ledger.sh scripts/generate-wechat-intake-ledger.sh scripts/check-file-modes.sh scripts/check-adk-harden-readiness.sh tests/test_wechat_intake_ledger.sh tests/test_file_modes_worktree.sh` | 0 | 六个变更 Shell 文件静态检查通过。 | 隔离 worktree | Source | 修复提交 |
| `rtk tests/test_wechat_intake_ledger.sh` | 0 | snapshot/live 正例及缺 corpus、live drift、ledger tamper、manifest 缺失、count mismatch 负例全部通过。 | 隔离 worktree与主工作区 | Project / Tool | snapshot manifest |
| `rtk tests/test_file_modes_worktree.sh` | 0 | linked worktree、两类 mode 漂移和两类 `--fix` 复验通过。 | 隔离 worktree与主工作区 | Project / Tool | file-mode checker |
| `rtk scripts/check-wechat-intake-ledger.sh .` | 0 | 纯 checkout 返回 `articles=313 mode=committed-snapshot`。 | 隔离 worktree | Project / Tool | ledger + manifest |
| `rtk scripts/check-wechat-intake-ledger.sh . --require-corpus` | 非 0（预期） | 纯 checkout 缺 corpus 时明确失败，不把 snapshot 冒充 live evidence。 | 隔离 worktree | Project / Tool | 无 |
| `rtk scripts/check-wechat-intake-ledger.sh . --articles-dir ~/bin/llm_agent/wechat-articles --require-corpus` | 0 | 对原工作区 313 篇真实 corpus 重生成并精确比对通过。 | 隔离 worktree | Project / Tool | ledger + live corpus |
| `rtk scripts/check-adk-harden-readiness.sh .` | 0 | exact ADK HEAD `0d25f3d...`，临时 clone 中 52/52 通过。 | 隔离 worktree | Project / Tool | ADK exact source |
| `rtk scripts/check-all.sh --full` | 0 | 根仓 Full 62/62 全部通过。 | 隔离 worktree | Project / Tool | 精确源码集合 |
| `rtk git merge --ff-only 150fdee1509b899bbb0d8c0762b7a9313b63ba94` | 0 | 本地主分支从基线快进到修复提交。 | 主工作区 | Source | 根 commit |
| `rtk scripts/check-wechat-intake-ledger.sh . --require-corpus` | 0 | 集成后主工作区返回 `articles=313 mode=live-corpus`。 | 主工作区 | Project / Tool | ledger + live corpus |
| `rtk git diff --submodule=short 383274f..150fdee -- <seven-gitlinks>` | 0 | 无输出，七个 gitlink 未变化。 | 主工作区 | Source | 根 commit |

## 结果矩阵

| Case | 期望 | 实际 | 状态 | 证据 |
| --- | --- | --- | --- | --- |
| 纯 checkout WeChat gate | 不依赖未跟踪 corpus，仍严格校验已提交证据 | committed snapshot 通过 | 通过 | targeted checker + fixture |
| Live corpus gate | 实际 corpus 与 ledger/manifest 不一致时失败 | 313 篇重生成精确匹配 | 通过 | `--require-corpus` |
| Linked worktree | 合法 `.git` 文件可被识别 | fixture 全绿 | 通过 | file-mode fixture |
| ADK harden | 不改子模块仍运行完整回归 | ADK 52/52 | 通过 | harden gate |
| Root Full | 62/62 | 62/62 | 通过 | `check-all.sh --full` |
| Gitlink integrity | 七个指针不变 | diff 为空 | 通过 | commit diff |
| Dirty state preservation | 原有非本次状态不被覆盖 | 前后集合一致 | 通过 | 主工作区 status |
| Source remote publish | 远端包含修复 commit | 未执行、未授权 | 待验证 | `main...origin/main [ahead 1]` |
| Artifact / release / rollback | 可校验且可恢复 | 本轮未生成或执行 | 待验证 | evidence contract 继续 pending |

## 结论

2026-07-17 Full 审计发现的源码可移植性阻塞已经在本地闭环：纯 checkout 不再依赖被忽略的原始 corpus，live 模式仍保持严格再生成验证；linked worktree 与 submodule gitfile 也不再被 file-mode/harden 误判。隔离精确源码 Full 从 61/62 提升为 62/62，主工作区真实 corpus 校验通过。

这使 `llm-agent` 达到“本地精确源码 Full 可恢复、可复验”的状态，但仍未达到项目 evidence-ready 或 Knowledge Hub 长期资产终态。源码远端尚未发布，正式 artifact、release record、跨主机恢复和生产 rollback 仍缺真实证据。

## 剩余风险

- 本地 `main` 比 `origin/main` 领先 1 个提交；没有 source remote write 授权，不能把本地闭环表述为远端已恢复。
- 原始公众号 corpus 继续是本地外部输入；manifest 只绑定 ledger/decision snapshot，不替代 corpus 的独立留存、隐私和恢复策略。
- harden 使用当前主机已初始化的 sibling reference 内容；尚未证明任意新主机能在无本地对象库时复现。
- 正式 artifact、release record、远端 retention、生产采用和 rollback drill 仍为空。
- 本报告由 Codex 起草并验证，保持 `reviewing` 与人工内容复核队列；当前泛化执行授权不等于正文签收。

## 后续动作

1. 真人按精确正文与 hash 完成普通内容复核；不要求或暗示 active promotion。
2. 如需发布源码，另行登记 exact commit、remote、fast-forward 前置检查和回滚边界后推送 `150fdee`。
3. 在独立环境从远端 clone 精确 commit，初始化七个 gitlink 并复跑 Full，补跨主机恢复证据。
4. 建立正式 artifact、release record、remote retention 与 rollback drill，再评估 `llm-agent` evidence contract。

```yaml
manual_validation_pending: true
manual_validation_reason: 本地源码 Full 已通过；source remote publish、跨主机恢复、正式 artifact、release record 和生产 rollback 仍未闭环。
required_followup:
  - 真人复核本报告正文与精确 hash
  - 单独授权并发布 llm_agent@150fdee 后执行远端纯 clone Full 验证
  - 生成 checksum-bound 正式 artifact 与 release record
  - 执行远端留存恢复和生产 rollback drill
owner: leiwenjun
review_after: 2026-10-17
```
