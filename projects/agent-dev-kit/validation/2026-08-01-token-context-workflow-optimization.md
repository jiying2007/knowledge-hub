---
id: agent-dev-kit-token-context-workflow-optimization-20260801
title: ADK Token 与上下文工作流优化验证
kind: validation
domain: projects/agent-dev-kit
path: projects/agent-dev-kit/validation/2026-08-01-token-context-workflow-optimization.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: git-worktree
  from: agent-dev-kit change token-context-workflow-optimization-v1
  source_sha256: 2a39066750701dd4069ceb8041957cdad0c66aee2303f741174577c4eb0aa33e
review_after: '2026-10-30'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- adk
- token-context
validation_refs:
- projects/agent-dev-kit/validation/2026-08-01-token-context-workflow-optimization.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/agent-dev-kit/validation/2026-08-01-token-context-workflow-optimization.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-08-01'
updated_at: '2026-08-01'
generated_by_ai: true
ai_role: summarized
ai_model_or_tool: Codex
ai_generated_at: '2026-08-01'
manual_validation_pending: true
summary_zh: 记录 ADK、Codex 与 Knowledge Hub 默认上下文、路由、telemetry 和 source-to-live 去重优化的可复用验证结论。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
aliases:
- ADK Token 与上下文工作流优化验证
related:
- projects/agent-dev-kit/README.md
- indexes/obsidian-home.md
- indexes/project-readiness.md
---

# 验证证据：token-context-workflow-optimization-v1

## Evidence Index

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
|---|---:|---|---|---|---|
| `rtk bash scripts/check-token-budget.sh . --summary-json --global-agents ~/codex/src/codex-home/AGENTS.md` | 0 | root=3995、ADK=3010、global=4495、累计=11500/12000 | command output | Workspace | R2 |
| `rtk python3 -m unittest discover -s tests -p 'test_*.py'` | 0 | Codex 121 tests pass | `~/codex/tests/` | Codex | R3/R5/R6/R7 |
| `rtk bash scripts/check.sh --no-build --plan build/apply-plan.json --target ~/.codex` | 0 | source fingerprint、build/target receipt、121 tests、5 profile smoke、diff/drift pass；plan_state=already-applied | `~/codex/build/apply-plan.json` | Source-to-live | R3/R6/R7 |
| `rtk bash scripts/governance-report.sh --summary-json` | 0 | bounded summary 823 bytes | command output | Codex | R7 |
| `rtk bash tools/ci/python-runtime.sh -m pytest -q` | 0 | Knowledge Hub 314 tests pass | `~/knowledge-hub/tests/` | Hub | R4/R8 |
| `rtk bash tools/knowledge-check.sh --dry-run` | 0 | status=pass, errors=0, warnings=0 | command output | Hub | R4/R8 |
| `knowledge-context ... --project agent-dev-kit ... --summary-json` | 0 | explicit-project、telemetry disabled、validation candidate not required、1866 bytes | command output | Hub | R4/R7 |
| `rtk tests/run_all.sh --fail-fast` | 0 | ADK 57/57 pass | command output | ADK | R1/R8 |
| `rtk scripts/check-all.sh --quick --result-json /tmp/llm-agent-token-opt-quick.json` | 1 | 52/54；仅 strict ADK 工作树 dirty 导致 current-status/subrepo-state 失败 | `/tmp/llm-agent-token-opt-quick.json` | Workspace | R8 limitation |
| `rtk scripts/check-all.sh --smoke --result-json /tmp/llm-agent-token-opt-smoke.json` | 1 | 10/12、32s；evidence-bundle 与 subrepo-state 同受 ADK dirty 影响 | `/tmp/llm-agent-token-opt-smoke.json` | Workspace | R6 performance |

## Before / After

| Metric | Before | After |
|---|---:|---:|
| Codex global + root + ADK AGENTS | 约 21.8 KiB | 11,500 bytes |
| token-lean active skills | 20 | 11 |
| skill-search 默认候选/summary | 5 / 4,096 bytes | 3 / 2,048 bytes |
| Hub context summary | 4 KiB 级、默认写 telemetry | 1,866 bytes、默认不写 telemetry |
| governance report in check | 完整大 JSON | 823-byte summary |
| usage 缺少 `thread_goals` | 整体异常 | threads/token 正常，capability 标记 unavailable |
| post-apply 同 plan | 重规划/重复动作 | `already-applied`，effective changes=0 |
| root smoke | 32s、reuse=0 | 32s、reuse=0；瓶颈仍为 evidence 16s/live 7s/routing 5s |

root smoke 未达到 20s 目标。现有 full same-run evidence 不能安全跨到 smoke；本变更不伪造 reuse，也不并发共享 schema/runtime 检查。剩余性能项进入后续独立 change，不影响本次上下文、路由与 Codex source-to-live 优化。

## Prompt / Route Regression

- 通用 Python 单测失败：before 首选 embedded skill；after 合法 zero-hit，直接进入 micro debugging。
- 单行 README：before 返回无关候选；after zero-hit/no-skill。
- 嵌入式串口日志：after 仍命中 embedded 专用候选，未因抑制规则丢失能力。
- 显式 `--project agent-dev-kit`：稳定选择 exact route；未知 project 以无 traceback 的 CLI error fail closed。

## Installation Scope

- ADK：core task-cost/context contract，未新增 runtime dependency。
- Codex：global-ready source asset，已通过 `~/codex -> ~/.codex` plan/apply；从 token-lean 移除的 9 个入口均是受管 symlink，vendor 实体保留并可延迟发现。
- Hub：project-bound context CLI；不提升 active、不写 memory，telemetry 改为显式 opt-in。
