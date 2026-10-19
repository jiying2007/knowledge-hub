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
id: agent-dev-kit-codex-team-runtime-distribution-v1
title: Agent Dev Kit 团队 Codex Runtime Bundle 分发决策候选
kind: decision
domain: projects/agent-dev-kit
path: projects/agent-dev-kit/decisions/codex-team-runtime-distribution-v1-candidate.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: manual
  from: 源证据位于私有 agent-dev-kit change/runbook 与团队资产仓；候选仅保存脱敏设计和验证摘要。
  source_sha256: 7ce01cdbf3966fc66fbc75c3898372a31cc330dbd363f561e64b2c16eadeb1ed
review_after: '2026-11-21'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- agent-dev-kit
- codex
- team-distribution
validation_refs:
- projects/agent-dev-kit/decisions/codex-team-runtime-distribution-v1-candidate.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/agent-dev-kit/decisions/codex-team-runtime-distribution-v1-candidate.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-08-21'
updated_at: '2026-08-21'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-08-21'
manual_validation_pending: true
summary_zh: 私有 ADK 通过精简、可校验 Runtime Bundle 进入独立团队 Codex 资产仓，再以双 plan/apply/rollback 事务交付成员运行态；Skill 内容对成员可读，ADK 实现源码不进入团队仓。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
aliases:
- Agent Dev Kit 团队 Codex Runtime Bundle 分发决策候选
---

# Agent Dev Kit 团队 Codex Runtime Bundle 分发方案（待 owner 签收）

> **证据范围：** 2026-10-19 只读核对 `agent-dev-kit` 的确切 GitHub source revision `38e80d7ba045f9a8c1d5d7e311b830f1f37c517a` 中已提交的设计、验证说明、审查报告和运行手册。以下引用只证明这些*文档载明*的历史设计与结果；没有在本轮运行其测试、进入团队私有仓或验证真实成员的新 Codex session。本条保持 `reviewing`，`decision_status`/`decision_date` 仍为空。

## 背景和范围

- 目标：从 ADK 输出仅包含可向成员披露的 Skill support tree、manifest、校验和与许可证的 Runtime Bundle，由独立团队资产仓导入并事务性安装到成员 Codex Home。
- 边界：ADK 不直接修改成员运行态、不输出内部实现源码；团队仓负责 bundle 验证、版本化 vendor、build/install receipt 和回滚。仓库当前 visibility 由实际平台设置决定，本条不据历史“私有”文字推定永久权限。

## 精确来源（源侧文档，并非 owner 签名）

- [设计 design.md](https://github.com/jiying2007/agent-dev-kit/blob/38e80d7ba045f9a8c1d5d7e311b830f1f37c517a/docs/changes/codex-team-runtime-distribution-v1/design.md)：Runtime Bundle 内容、确定性打包、路径/链接约束及双事务交付。
- [验证记录 verification-evidence.md](https://github.com/jiying2007/agent-dev-kit/blob/38e80d7ba045f9a8c1d5d7e311b830f1f37c517a/docs/changes/codex-team-runtime-distribution-v1/verification-evidence.md)：历史测试、fresh clone smoke、未完成项。
- [审查报告 review-report.md](https://github.com/jiying2007/agent-dev-kit/blob/38e80d7ba045f9a8c1d5d7e311b830f1f37c517a/docs/changes/codex-team-runtime-distribution-v1/review-report.md)：自审而非独立审阅，并区别 source-ready 与 delivery-open。
- [运行手册 codex-team-runtime-distribution.md](https://github.com/jiying2007/agent-dev-kit/blob/38e80d7ba045f9a8c1d5d7e311b830f1f37c517a/docs/runbooks/codex-team-runtime-distribution.md)：publisher/member 操作与 fail-closed rollback；手册所含内网地址和本机路径不在本文复制。

## 决策问题与可选路径

| 方案 | 优点 | 风险与待定 |
| --- | --- | --- |
| Runtime Bundle → 团队发行仓 → 成员 Codex | 有明确 manifest/完整性与两段可回滚事务，不向成员提供 ADK 内部源码 | 依赖团队仓控制、Source-to-live、成员授权与版本兼容验证 |
| ADK 直接写成员运行态 | 少一层发行仓 | 破坏设计中的分责、审计和隔离边界，未被当前源侧设计采纳 |
| 直接分发完整 ADK 源码 | 实现路径直观 | 泄露内部实现/测试和扩大可见范围，未被本候选授权 |

## 已保存的历史验证证据（仅文本引用）

- 源侧 `verification-evidence.md` 记录：Runtime Bundle 定向测试 3 cases、团队 assets 回归 4 cases、真实 RC7 team-core Bundle 32 skills/63 source files、完整 `tests/run_all.sh` 59/59 pass。
- 同一历史记录注明一个 quick matrix 因三条 source freshness 过期而 overall fail；不能以其他绿项覆盖该负结果。
- `review-report.md` 记载本地源实现作者自审已关闭代码 finding、内部团队仓 fresh clone smoke 完成；但“独立 reviewer”并未完成，当前新成员会话的 Skill discovery/自然语言触发以及 source-to-live 实测仍缺。
- 2026-10-19 的本次复核只读 GitHub 文档，不把历史 `pass` 当作当前 runner、release、发布或成员采用的 SUCCESS。

## 决策、授权与发布门禁

- **本条决定：待真实 owner 审核。** 本次 AI 补录不构成授权、激活 team-core profile、写团队仓、发布 Release 或覆盖任何成员本地目录。
- 候选实施路径：锁定 source SHA 与 Runtime Bundle digest → 分别校验 ADK 与团队发行仓 → source-to-live plan/apply/rollback 演练 → 新 Codex session discovery/trigger pilot → owner 审核适用范围。
- Bundle 坚持完整性、仅普通文件/目录、拒绝 symlink/hardlink/special file、路径越界和额外源码，发布时还要核验可读 Skill 与保密服务端执行逻辑的分界。

## 回滚与长期维护

- 团队发行仓导入失败须先校验 previous manifest、receipt 和原有树，再事务回滚；成员安装失败先检查 drift/backup，不应直接覆盖本地修改。
- 若新会话未发现 Skill、manifest 摘要不符、旧版本回归失败或无法证明成员身份，应保持 `blocked/needs-review`，不得静默升级。
- 沿用 `owner=leiwenjun`、`review_after=2026-11-21` 的既有待审边界；原始底层团队仓凭据、内网 URI、私人 Code Home 和真实成员会话均未读取。
