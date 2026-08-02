---
id: agent-dev-kit-token-context-governance-v2-20260801
title: ADK/Codex/Hub Token 与门禁优化 v2
kind: validation
domain: projects/agent-dev-kit
path: projects/agent-dev-kit/validation/2026-08-01-token-context-governance-v2.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: ephemeral-file-capture
  from: cross-repo implementation evidence
  source_sha256: c3d5ad5069dab1378c4bdd854400f315cf9967be145ceb15dbd3f647bf20435a
  temporary_source_retained: false
review_after: '2026-08-15'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- agent-dev-kit
- token-governance
- validation
validation_refs:
- projects/agent-dev-kit/validation/2026-08-01-token-context-governance-v2.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/agent-dev-kit/validation/2026-08-01-token-context-governance-v2.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-08-01'
updated_at: '2026-08-01'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-08-01'
manual_validation_pending: true
summary_zh: 低 Token task-cost、双模式门禁、plan v3、Hub receipt 与复审批次的跨仓验证候选。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
aliases:
- ADK/Codex/Hub Token 与门禁优化 v2
related:
- projects/agent-dev-kit/README.md
- indexes/obsidian-home.md
- indexes/project-readiness.md
---

# ADK / Codex / Knowledge Hub Token 与门禁优化 v2

## 结论

本轮把低 Token 使用从“文档建议”推进为可执行合同：ADK 增加确定性 task-cost receipt；根仓增加 release-clean / working-tree 双模式、同轮证据复用与稳定 fingerprint；Codex apply plan 升级为 v3 并覆盖 mutation/keep precondition；Knowledge Hub 增加 2 KiB capture summary、显式 context receipt 与只读 review SLA batch。

## 稳定决策

- `micro` 任务不加载 skill、不做 Hub preflight；高风险任务保持 raw evidence 与 full gate。
- working-tree 只证明“验证期间改动未变化”，不授予 release-clean、提交或发布声明。
- Codex plan v3 同时绑定 build tree、managed state、target mutation 与 keep path；keep 漂移 fail closed，已应用 plan 可安全判定 `already-applied`。
- context receipt 不保存 query 正文，并绑定 query SHA256、workspace HEAD、Hub registry 与选中原文 SHA256；任一变化重新装配。
- review packet 只提供 overdue/due-soon/missing-date、owner/domain 聚合与有界批次，不自动写 registry、owner decision 或 active promotion。
- 跨仓 bundle 只保存 HEAD、dirty fingerprint 与产物 hash，不保存 diff、prompt、query、日志或凭证，也不代表 release authorization。

## 验证证据

- ADK：Python 3.11 / 3.12 锁定 Docker parity 均通过 20/20 回归、30/30 deterministic routing、wheel 构建、target check 与 dependency audit。
- Codex：126 个 unit tests、governance、五 profile smoke、source-to-live plan/dry-run/apply、routing precedence 与 post-apply check 通过。
- Knowledge Hub：锁定 Python 3.14 full pytest 与 `knowledge-check --dry-run --summary-json` 通过。
- llm_agent：19/19 root regression 通过；working-tree full gate 首轮 60/61，唯一失败为 health 未接收 working-tree 模式，修复后 `check-workspace-entrypoints.sh --worktree-integration` 通过。
- smoke working-tree：13/13，真实 same-run reuse 7，整轮 27 秒；未达到 20 秒目标，最慢项为 evidence bundle 10 秒、runtime live 7 秒、routing 6 秒。

## 边界与剩余风险

- 当前四仓仍含本任务及用户已有 dirty changes；release-clean 模式应继续失败，不得据此声明可提交或可发布。
- 系统 Python 3.8 结果仅作 development-only；release 证据来自受支持的 3.11/3.12 容器。
- reviewing candidate 不是 active 事实，需人工复核后再决定是否提升。
