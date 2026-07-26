---
aliases:
- llm-agent adk 3.1 rc3 release closure
- llm-agent-adk-v3-1-rc3-release-closure
related:
- projects/llm-agent/README.md
- indexes/project-readiness.md
- projects/llm-agent/validation/project-readiness.md
- projects/llm-agent/validation/adk-v3-1-rc2-release-closure-20260714.md
- projects/agent-dev-kit/README.md
id: llm-agent-adk-v3-1-rc3-release-closure-20260718
title: LLM Agent 与 ADK 3.1 RC3 本地发布候选闭环验证
kind: validation
domain: projects/llm-agent
path: projects/llm-agent/validation/adk-v3-1-rc3-release-closure-20260718.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: repository-report
  from: llm_agent committed RC3 closure evidence at root a1f6fa0 and ADK a1b5e2f
  source_sha256: 6744d481fb17d865c490b470b48d02dd25826aa32fa1309aed80ba06eb16f933
review_after: '2026-10-18'
review_status: human-reviewed-accepted
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- llm-agent
- agent-dev-kit
- release-candidate
- rc3
- validation
- no-active-promotion
validation_refs:
- projects/llm-agent/validation/adk-v3-1-rc3-release-closure-20260718.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: reviewing-validation-pending
evidence_refs:
- projects/llm-agent/validation/adk-v3-1-rc3-release-closure-20260718.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-07-18'
updated_at: '2026-07-26'
generated_by_ai: true
ai_role: summarized
ai_model_or_tool: Codex
ai_generated_at: '2026-07-18'
manual_validation_pending: true
summary_zh: 记录 ADK 3.1.0-rc.3 本地提交、可复现制品、RC2 到 RC3 升级回滚、完整门禁及 M5 外部阻塞；本地候选闭环通过，不声明远端发布、M5 认证或终态成熟。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
---

# LLM Agent 与 ADK 3.1.0-rc.3 本地发布候选闭环验证

## 归档元数据

- Captured at：2026-07-18。
- Last verified：2026-07-18。
- Topic：release-validation。
- Source：`llm_agent` 与 `agent-dev-kit` 已提交的 RC3 状态、发布证据、迁移说明和 rehearsal 报告。
- Sanitization：未收录凭证、私有端点、完整聊天记录、原始日志、cache、runtime state 或二进制内容；本机绝对路径已省略。
- Provenance：根仓 HEAD `a1f6fa0f12b861d9139939b2acc054d0c4d7fb19`；根产品基线 `d47e0cc821fb9821ed23105b072f7090a873d6e2`；ADK HEAD `a1b5e2fed679d8002b21567103c6366c57236915`；ADK release source `defe8a078b9693b6963e434f3131891ebbcf5d62`。
- Memory candidate：no。本记录只作长期验证 provenance，不静默提升为规则、active knowledge 或 memory。
- Gate result：本地 RC3 release-candidate closure 为 pass；Software M5 certification 与 terminal maturity 为 blocked。

## 结论

`agent-dev-kit 3.1.0-rc.3` 已完成授权范围内的本地 version、原子 commit、精确 commit 制品构建、RC2 到 RC3 安装与回滚演练，以及 ADK/根仓集成门禁。其真实状态是 **M3 / M5-ready 的本地 release candidate**，不是最终 `3.1.0`、Software M5 正式认证或产品终态。

本轮未执行 push、tag、远端 Release、制品上传、远程 CI/attestation、真实双 runtime campaign、长期现场试点或 live apply。缺少这些证据时，`software_m5_certified=false` 与 `terminal_mature=false` 必须保持不变。

## 提交与版本边界

### agent-dev-kit

1. `57291d6177a9d9d3d4740c686293c02e4ff9af4c`：固化 RC3 终态合同。
2. `defe8a078b9693b6963e434f3131891ebbcf5d62`：排除本地日志污染发布制品；作为精确制品对应的 source/release commit。
3. `a1b5e2fed679d8002b21567103c6366c57236915`：记录本地升级回滚证据；作为归档时 ADK HEAD。

### llm_agent

1. `d47e0cc821fb9821ed23105b072f7090a873d6e2`：固化 ADK 3.1.0 RC3 产品基线。
2. `a1f6fa0f12b861d9139939b2acc054d0c4d7fb19`：锁定已验证产品基线；作为归档时根仓 HEAD。

ADK 相对远端 ahead 3，根仓相对远端 ahead 2；均未推送。根仓已有 `OpenSpec`、`superpowers`、`vibeflow` dirty submodule 和未跟踪 `hermes/`、`hermes_data/` 属于既有用户状态，本轮未回退、清理或纳入提交。

## 可复现制品与 rehearsal

- RC3 version：`3.1.0-rc.3`。
- RC3 artifact SHA256：`46afbb507f61fce8facffbfa36c23f59fe3f5498e3f1843ceaa53f2507d8fcd8`。
- RC3 source file count：576。
- Candidate manifest digest：`3836581349363acc56c72f7c99406ef884976ebc4a6478d58b1806ef1ebb9f94`。
- Rehearsal report SHA256：`1526ac3aaeb275c4c34da79419e2aed9588620c6487ee6b8805232de31096de9`。
- 历史 RC2 实际 artifact SHA256：`8571134df515289d32905961ae78d5e5c2dd308d2771691690594a85c76142ac`。

RC3 从 release source commit 的 Git archive 独立构建两次，结果字节级一致。RC2 与 RC3 各安装 39 项；RC3 rollback 移除并恢复 39 项；两个 checksum sidecar 均验证通过，migration mode 为 `in-place-replacement`。

## RC2 provenance 缺口与 RC3 修复

复核发现，从 RC2 声明的 release commit 重建只能得到 520 个 source files，历史最终制品则包含 521 个文件。唯一额外文件是 Git 忽略的 `history.log`，因此历史 RC2 checksum 有效，但不能仅从声明 commit 精确复现。

RC3 没有改写旧 RC2 证据，而是采用以下修复：

1. 发布组装器排除所有 `*.log`。
2. 增加归档负向回归测试。
3. 使用 checksum 有效的历史 RC2 实际制品作为 rehearsal 起点。
4. 证明 RC3 精确 commit 双构建字节一致。

可复用原则是：历史负证据必须保留；新候选应修复 reproducibility 合同，不能通过重写旧 provenance 制造一致性。

## 验证证据

- ADK manifest sync、strict validation、release check：PASS。
- ADK source quick suite：17/17 PASS。
- ADK release-tree full suite：54/54 PASS。
- Security scan：695 files，0 failures，0 warnings。
- 根仓 quick suite：56/56 PASS。
- 根仓 full suite：62/62 PASS。
- Harden readiness、performance operations、evidence bundle、Software M5 contracts、token、WeChat、workspace aggregate：PASS。
- Product maturity contracts、current-status consistency、Software M5 declaration、ADK lock、subrepo state、`git diff --check`：PASS。
- `final-ready.sh`：PASS。

远程 CI 根据 owner 的临时绕过授权未执行，也未声称通过。替代证据为受控本地 Python 3.11 与 3.12 环境：两者 full suite 均为 54/54，并覆盖 wheel、dependency audit、security、release、performance 与 eval；该证据只关闭本地 CI parity，不替代远程 workflow 与 attestation。

## source-to-live 决策

release source commit 到 evidence commit 在 `agents`、`skills`、`optional-skills`、`workflows`、`templates` 等映射路径无变化。因此本轮 source-to-live 状态是 `not-required-mapped-no-change`，不是“执行 apply 后通过”。本轮未修改 `~/codex` 或 `~/.codex`。

## Software M5 阻塞条件

本地 integrity、declaration 与 readiness 已通过，但正式 certification 仍受以下真实外部条件阻塞：

1. `final_version`：当前仍是 prerelease。
2. `independent_repository`：缺少独立真实仓库认证。
3. `operator_count`：真实操作人员数量不足。
4. `pilot_duration`：真实试点周期不足。
5. `real_repository_count`：真实仓库样本不足。
6. `required_field_events`：要求的现场事件证据不足。
7. `runtime_campaign`：真实长期运行 campaign 尚未完成。

这些条件不能通过增加本地测试、放宽门禁或修改状态文件替代。

## 后续恢复点

1. 从根仓 `a1f6fa0` 与 ADK `a1b5e2f` 开始远程发布前复核；制品必须继续锚定 ADK release source `defe8a0`。
2. 获得明确授权后再执行 push、tag、远端 CI/attestation 和制品发布，并记录不可变远端证据。
3. 通过独立仓库、第二操作者、足够试点周期、field events 与 runtime campaign 逐项关闭 Software M5 blocker；全部证据满足后才评估最终 `3.1.0`。

## 仓库证据索引

- `reports/terminal-closure-remediation-2026-07-18.md`
- `reports/adk-v3-1-rc3-release-evidence-2026-07-18.json`
- `reports/current-status.md`
- `manifests/software_m5_policy.json`
- `agent-dev-kit/docs/changes/adk-terminal-contract-hardening/release-rehearsal.json`
- `agent-dev-kit/docs/migrations/3.1.0-rc.3.md`

本归档不替代上述机器可读证据；若正文与仓库当前状态冲突，应以对应不可变 commit、制品 checksum 和最新受治理 current/validation 事实为准。
