---
id: llm-agent-exact-source-quick-gate-audit-20260715
title: LLM Agent 精确源码 Quick 门禁审计 2026-07-15
kind: validation
domain: projects/llm-agent
path: projects/llm-agent/validation/2026-07-15-exact-source-quick-gate-audit.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source: null
review_after: '2026-10-15'
created_at: null
updated_at: null
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- llm-agent
- exact-source
- validation
- quick-gate
related:
- projects/llm-agent/validation/project-readiness.md
- governance/product/validation/project-readiness.md
validation_refs:
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
artifact_refs: []
target_version: llm_agent@1d7730af7afe0217fd387533cd490d64eca51e7e with seven exact gitlinks
test_environment: isolated local clones under /tmp; current host runtime dependencies; no remote network
summary_zh: 在根仓与 7 个 gitlink 精确 commit 的隔离克隆中执行 smoke 和 quick 聚合门禁；12/12 与 56/56 通过，但 full、正式 artifact、release 和 rollback
  仍待闭环。
review_status: human-reviewed-accepted
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: None
evidence_strength: null
evidence_refs: []
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-07-15'
human_reviewed_by: null
human_reviewed_at: null
review_basis: null
manual_validation_pending: true
aliases:
- LLM Agent 精确源码 Quick 门禁审计 2026-07-15
---

# LLM Agent 精确源码 Quick 门禁审计 2026-07-15

## 验证目标

验证已登记的 `llm-agent` 根仓 commit 及其 7 个 gitlink commit，在排除原工作区脏子仓后，能否通过仓库定义的 smoke 与 quick 聚合门禁。

本报告证明的是“精确源码复合克隆 + 当前本机依赖环境”中的两组命令结果。它不证明 full 门禁、跨主机可复现性、正式 artifact、远端发布、现场采用或 rollback 已完成，也不构成 owner 决策。

## 精确源码集合

| 仓库路径 | Commit |
|---|---|
| 根仓 `llm_agent` | `1d7730af7afe0217fd387533cd490d64eca51e7e` |
| `OpenSpec` | `3c7a05c5dc88b2397c478805890b55ed392b19e8` |
| `agent-dev-kit` | `0d25f3da7ac1f141a5172d62cfc7b6f4bfbd93b1` |
| `scale-engine` | `ace49169c4191db656989b738f31edb19a380a63` |
| `superpowers` | `6efe32c9e2dd002d0c394e861e0529675d1ab32e` |
| `vibeflow` | `0df764eff5e7b034611540da8d9f8367dfae55b2` |
| `oh-my-codex` | `f947e3a41c062c25fd107686862b68ee5d1b66a5` |
| `planning-with-files` | `d71b3be47b62fe49d60fb2ede800e1907ebea3d9` |

上述身份来自根 commit 的 `git ls-tree`，不是从当前子仓 HEAD 推断。原工作区的 `OpenSpec`、`superpowers`、`vibeflow` 显示脏状态，因此本轮在 `/tmp` 分别从本机对象库克隆并 checkout 精确 gitlink commit；原工作区内容和未提交修改未进入验证树。

## 环境与边界

- 日期：2026-07-15。
- cwd：`/tmp/kh-llm-agent-exact-20260715-1220`。
- 构造方式：根仓和每个子仓均使用本机路径执行 `git clone --no-hardlinks --no-checkout`，随后 `git checkout --detach <exact-commit>`；未访问远端网络。
- 子仓登记：在临时根仓执行 `git submodule init`，只修改临时 `.git/config`；`git submodule status` 显示 7 个 commit 均与根仓 gitlink 一致。
- 源项目边界：未修改 `~/bin/llm_agent` 或其子仓，未写远端、运行目标、memory 或发布系统。
- 运行依赖：部分门禁读取当前本机 `~/codex`、`~/.codex` 或其他已声明 runtime 状态；因此通过结果绑定本机验证环境，不能外推为任意主机均通过。
- 证据保留：长期层保存输入 commit、命令与汇总结果；临时 clone、缓存和原始长输出不进入 Hub。

## 验证命令

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
|---|---:|---|---|---|---|
| `rtk git submodule status` | 0 | 7 个子仓均显示根 gitlink 所要求的精确 commit，无 `+` 漂移。 | `/tmp/kh-llm-agent-exact-20260715-1220` | Source | 无 |
| `rtk bash scripts/check-all.sh --smoke` | 0 | 12/12 通过；覆盖 ADK lock/target evidence、adoption real assets、doc sync、evidence bundle、phase gate、reference dirty triage、runtime health/live footprint/routing/targets 和 subrepo state。 | 同上 | Project / Tool | 无正式 artifact |
| `rtk bash scripts/check-all.sh --quick` | 0 | 56/56 通过；包含 governance、adoption、runtime、OSS intake、repo quality、routing、skill metadata 等 quick 聚合检查。 | 同上 | Project / Tool | 无正式 artifact |

## Quick 模式排除项

`--quick` 按仓内脚本定义显式跳过以下耗时或环境型门禁：

- `check-adk-harden-readiness.sh`
- `check-adk-performance-ops.sh`
- `check-evidence-bundle.sh`
- `check-token-budget.sh`
- `check-wechat-intake-ledger.sh`
- `check-workspace-entrypoints.sh`

其中 `check-evidence-bundle.sh` 已由单独的 smoke 聚合执行并通过；其余五项本轮未执行。不能用 56/56 quick 结果推断 full 聚合也通过。

## 结果矩阵

| 层级 | 结果 | 状态 | 边界 |
|---|---|---|---|
| 根仓与 gitlink 身份 | 1 + 7 个精确 commit 已核对 | 通过 | 只覆盖登记 commit |
| Smoke | 12/12，退出码 0 | 通过 | 最小健康面 |
| Quick | 56/56，退出码 0 | 通过 | 跳过 6 个脚本，其中 evidence bundle 已在 smoke 覆盖 |
| Full / harden | 未执行 | 待验证 | 不得推断通过 |
| Artifact / release / rollback | 未生成或未执行 | 待验证 | evidence contract 继续 pending |

## 结论

本轮结论为“软件验证层部分通过”：`llm-agent@1d7730a…` 与根仓固定的 7 个子仓 commit 组成的精确复合克隆，通过 12/12 smoke 和 56/56 quick 门禁。这一结果可绑定为 `llm-agent` validation contract 的真实 `validation-report`。

由于 full/harden、正式 artifact、release record 和 rollback drill 尚未闭环，且部分 runtime 检查依赖当前本机状态，本报告不支持把 `llm-agent` evidence contract 标为 `ready`。

## 剩余风险与后续动作

```yaml
manual_validation_pending: true
manual_validation_reason: full/harden、性能、token、WeChat、workspace aggregate、正式 artifact、release 与 rollback 未全部验证。
required_followup:
  - 在同一精确复合克隆中执行 check-all.sh --full，并单独记录耗时门禁结果
  - 将依赖 live runtime 的检查与纯源码检查分层，记录环境身份和可移植边界
  - 生成可校验的正式 artifact 与 release record
  - 执行并记录可恢复 rollback drill
owner: leiwenjun
review_after: 2026-10-15
```
