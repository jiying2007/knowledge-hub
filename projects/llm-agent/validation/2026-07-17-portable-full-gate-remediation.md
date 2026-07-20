---
related:
- projects/llm-agent/validation/2026-07-17-exact-source-full-gate-audit.md
- projects/llm-agent/validation/2026-07-15-exact-source-quick-gate-audit.md
- projects/llm-agent/validation/project-readiness.md
- governance/product/validation/project-readiness.md
target_version: llm_agent@150fdee1509b899bbb0d8c0762b7a9313b63ba94 with unchanged seven gitlinks
test_environment: isolated linked worktree; main workspace live corpus; fresh GitHub root clone with seven exact remote submodules
  and a temporary SSH override for private agent-dev-kit; current host runtime dependencies
human_reviewed_by: null
human_reviewed_at: null
review_basis: null
aliases:
- LLM Agent 可移植 Full 门禁修复验证 2026-07-17
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
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; source remote publish and current-host remote-clone verification do not authorize release, evidence-ready
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
validation_refs:
- projects/llm-agent/validation/2026-07-17-portable-full-gate-remediation.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
- rtk scripts/check-all.sh --full
- rtk tests/test_wechat_intake_ledger.sh
- rtk tests/test_file_modes_worktree.sh
- rtk scripts/check-wechat-intake-ledger.sh . --require-corpus
- rtk git fetch origin main
- rtk git push origin main
artifact_refs:
- llm_agent@150fdee1509b899bbb0d8c0762b7a9313b63ba94/reports/wechat-article-intake.manifest.json#sha256=93c926be842eb4480cce754a74f10f8e9fe5977f60cbce09c31d4320e2222e19
evidence_strength: direct-command
evidence_refs:
- projects/llm-agent/validation/2026-07-17-exact-source-full-gate-audit.md
- llm_agent@150fdee1509b899bbb0d8c0762b7a9313b63ba94
created_at: '2026-07-17'
updated_at: '2026-07-19'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-07-17'
manual_validation_pending: true
manual_validation_reason: 源码已 fast-forward 发布并在当前主机完成远端纯 clone Full 复验；私有 submodule 零配置跨主机恢复、正式 artifact、release record 与生产
  rollback 仍未闭环。
summary_zh: 修复 WeChat intake 外部语料与纯 Git checkout 的输入契约，并补齐 linked worktree、submodule gitfile 与 ADK 临时精确克隆兼容性；源码已 fast-forward
  发布到 origin/main，隔离与远端恢复 Full 均为 62/62，主工作区 313 篇 live-corpus 通过，正式制品、release 与 rollback 仍未闭环。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: checked
---

# LLM Agent 可移植 Full 门禁修复验证 2026-07-17

## 验证目标

验证 2026-07-17 精确源码 Full 审计发现的唯一失败，是否已在不提交原始公众号语料、不削弱 live-corpus 校验、不修改 gitlink 的前提下完成修复；同时验证标准 linked worktree 与 submodule gitfile 不再被 file-mode/harden 门禁误判。

本报告证明本机精确源码、隔离 worktree、当前 live corpus，以及授权后从远端重新 clone 的精确源码集合在当前主机上的命令结果。它证明 `origin/main` 已包含目标提交并可在当前 SSH 凭证环境恢复，不证明任意新主机零配置复现、正式 artifact、生产采用或 rollback 已完成，也不构成 owner 内容签署或 lifecycle promotion。

## 验证对象

| 对象 | 基线 | 修复后 |
| --- | --- | --- |
| 根仓 `llm_agent` | `383274fed93ad143cabb1dbd977e1b766eca5c04` | `150fdee1509b899bbb0d8c0762b7a9313b63ba94` |
| 根仓改动 | 无 | 11 个文件，570 行新增、59 行删除 |
| 七个 gitlink | 基线 commit | 全部未变 |
| WeChat ledger | 313 条已跟踪记录 | 313 条，SHA256 `15f8f153dc09f19c12ce151e9e2801ed64f5c87db442143a2726473c5e16ad7f` |
| Decision overlay | 313 条决策加表头 | SHA256 `17ec7898faf903641965578a62176bf350f954f4795081574a7dd48b6d0f0a01` |
| Snapshot manifest | 不存在 | SHA256 `93c926be842eb4480cce754a74f10f8e9fe5977f60cbce09c31d4320e2222e19` |

修复提交先通过 `--ff-only` 快进到本地主分支；随后依据 `auth-20260717-llm-agent-source-remote-push`，`origin/main` 从 `383274fed93ad143cabb1dbd977e1b766eca5c04` fast-forward 到 `150fdee1509b899bbb0d8c0762b7a9313b63ba94`。推送后 fresh fetch 确认本地与远端分叉为 `0 0`。

远端恢复验证从 GitHub 新 clone 根仓并按 gitlink 初始化七个子仓。公开子仓直接恢复；私有 `agent-dev-kit` 的 tracked HTTPS URL 在非交互环境因无法读取用户名而失败，临时 clone 仅在本地 `.git/config` 将该单一 URL 改为 SSH 后成功。该临时配置没有修改 `.gitmodules` 或任何 tracked 文件；七个子仓精确匹配后，远端 clone Full 为 62/62。

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
- 网络：修复验证不依赖远端网络；发布与远端恢复阶段访问 GitHub/Gitee，只执行授权的 Git push 和只读 clone/fetch。
- 工作树保护：集成前后均保留原有 `OpenSpec`、`superpowers`、`vibeflow` dirty 状态，以及 `hermes/`、`hermes_data/` 未跟踪目录；未执行 reset、clean 或删除。
- 分支保护：本地 `main` 与 `origin/main` 均只做一次 fast-forward；未 merge commit、rebase、force push、tag 或 release。

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
| `rtk git fetch origin main` + 精确基线/分叉检查 | 0 | 推送前 `origin/main=383274f`、`HEAD=150fdee`、直接父子关系成立、分叉 `0 1`。 | 主工作区 | Source | 授权账本 |
| `rtk git push origin main` | 0 | 唯一一次授权 source push 成功；推送后 fetch 确认 `HEAD=origin/main=150fdee`、分叉 `0 0`。 | 主工作区与 GitHub remote | Source | 根 commit |
| `rtk git submodule update --init` | 1 | 远端恢复首轮在私有 `agent-dev-kit` HTTPS URL 处失败；非交互环境无法读取 GitHub 用户名。 | 新建远端 clone | Source / Negative | `.gitmodules` |
| 临时 `submodule.agent-dev-kit.url=git@github.com:jiying2007/agent-dev-kit.git` 后复跑初始化 | 0 | 七个 gitlink 全部从远端取回并精确匹配；临时配置只写 clone 的 `.git/config`，tracked `.gitmodules` 无变化。 | 新建远端 clone | Source | 七个 gitlink |
| `rtk scripts/check-all.sh --full` | 0 | 纯远端来源 clone 的根仓 Full 62/62；完成后根仓与七个子仓均 clean。 | 新建远端 clone | Project / Tool | 远端恢复源码集合 |

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
| Source remote publish | 远端包含修复 commit | `HEAD=origin/main=150fdee`，分叉 `0 0` | 通过 | 授权账本 + fresh fetch |
| Current-host remote restore | 从声明远端恢复根仓与七个 gitlink并复跑 Full | 临时 SSH override 后七个 gitlink 精确匹配，Full 62/62 | 通过（有凭证前置条件） | 新建远端 clone |
| Artifact / release / rollback | 可校验且可恢复 | 本轮未生成或执行 | 待验证 | evidence contract 继续 pending |

## 结论

2026-07-17 Full 审计发现的源码可移植性阻塞已经在本地闭环：纯 checkout 不再依赖被忽略的原始 corpus，live 模式仍保持严格再生成验证；linked worktree 与 submodule gitfile 也不再被 file-mode/harden 误判。隔离精确源码 Full 从 61/62 提升为 62/62，主工作区真实 corpus 校验通过。

这使 `llm-agent` 达到“精确源码已远端保留，并可在当前主机从远端恢复后通过 Full”的状态，但仍未达到项目 evidence-ready 或 Knowledge Hub 长期资产终态。正式 artifact、release record、任意新主机零配置恢复和生产 rollback 仍缺真实证据。

## 剩余风险

- `origin/main` 已包含 `150fdee`；但私有 `agent-dev-kit` 的 tracked HTTPS URL 在无交互凭证时不能直接恢复，当前主机依赖已有 SSH 身份和临时 URL override。
- 原始公众号 corpus 继续是本地外部输入；manifest 只绑定 ledger/decision snapshot，不替代 corpus 的独立留存、隐私和恢复策略。
- 远端 clone 已证明不借用原工作区对象库也可复验，但仍未在另一台独立主机验证凭证、依赖和 runtime 状态。
- 正式 artifact、release record、远端 retention、生产采用和 rollback drill 仍为空。
- 本报告由 Codex 起草并验证，保持 `reviewing` 与人工内容复核队列；当前泛化执行授权不等于正文签收。

## 后续动作

1. 真人按精确正文与 hash 完成普通内容复核；不要求或暗示 active promotion。
2. 评审并固化私有 `agent-dev-kit` 的非交互凭证/URL bootstrap，避免依赖临时 clone 配置。
3. 在另一台独立主机从远端 clone 精确 commit，初始化七个 gitlink并复跑 Full，补真正跨主机恢复证据。
4. 建立正式 artifact、release record 与 rollback drill，再评估 `llm-agent` evidence contract。

```yaml
manual_validation_pending: true
manual_validation_reason: source remote publish 与当前主机远端恢复 Full 已通过；私有 submodule 零配置跨主机恢复、正式 artifact、release record 和生产 rollback 仍未闭环。
required_followup:
  - 真人复核本报告正文与精确 hash
  - 固化私有 agent-dev-kit 的非交互远端恢复 bootstrap，并在另一台主机复验
  - 生成 checksum-bound 正式 artifact 与 release record
  - 执行远端留存恢复和生产 rollback drill
owner: leiwenjun
review_after: 2026-10-17
```
