---
id: llm-agent-spec-kit-reference-onboarding-validation-20260723
title: github/spec-kit正式登记验证
kind: validation
domain: projects/llm-agent
path: projects/llm-agent/validation/2026-07-23-spec-kit-reference-onboarding-validation.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: generated
  from: llm_agent-repository
  source_sha256: e8ffc2ea1ebc9d2c7d97b5e78fc1f7ce69009bb76ec774bb63b061ea22ce9bb8
  temporary_source_retained: false
review_after: '2026-10-23'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- llm-agent
- spec-kit
- reference-repository
validation_refs:
- projects/llm-agent/validation/2026-07-23-spec-kit-reference-onboarding-validation.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/llm-agent/validation/2026-07-23-spec-kit-reference-onboarding-validation.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-07-23'
updated_at: '2026-07-23'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-07-23'
manual_validation_pending: true
summary_zh: spec-kit已在隔离分支正式登记为P1 observe-first active-reference，登记范围门禁通过，全仓quick为52/53且唯一失败是既有dirty baseline过期。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
aliases:
- github/spec-kit正式登记验证
related:
- projects/llm-agent/README.md
- indexes/obsidian-home.md
- indexes/project-readiness.md
---

# github/spec-kit 长期跟踪落地记录

## 状态

- 决策：`ADOPT / target=reference-repository`
- 目标定位：`P1 / observe-first / active-reference`
- 当前状态：`applied / scoped-verification-passed`
- 正式登记：已在隔离分支 `codex/spec-kit-reference-onboarding-20260723` 完成，尚未合并到 `main`
- 隔离原因：根工作区存在用户/既有未提交变更；通过独立 worktree 和两阶段提交满足 `apply_workspace_gate`，未 stash、清理、回退或混合提交。
- 仓库全量门禁：`52/53`；唯一失败为三个既有 known-dirty baseline 于 2026-07-20 到期，与本次登记变更无因果关系。

## Source 与版权边界

- source：`https://github.com/github/spec-kit`
- retrieved_at：`2026-07-23`
- stable tag：`v0.13.4`
- reviewed commit：`ee883a1d4ecee9afe06a81f1bd38a0b745a8d059`
- reviewed tree：`b27f6e7260f477ee70d7ad1854a63b04689e98b4`
- license：MIT
- candidate：`epc-2ab9c988520526e1e0e0`
- 只保存 metadata、分析、决策和本地治理计划；未复制上游正文、模板、catalog 内容或二进制。
- 未安装/执行 `specify-cli`、workflow、extension、preset、bundle、hook 或 Git automation。

## 已落地产物

1. `reports/external-practice-candidates-spec-kit-2026-07-23.jsonl`
2. `reports/external-practice-evidence-spec-kit-2026-07-23.json`
3. `reports/external-practice-decisions-spec-kit-2026-07-23.jsonl`
4. `reports/reference-analysis-spec-kit-2026-07-23.md`
5. `reports/reference-duplicate-review-spec-kit-2026-07-23.md`
6. `reports/reference-security-review-spec-kit-2026-07-23.md`
7. `reports/reference-repository-onboarding-spec-kit-2026-07-23.json`
8. `reports/reference-repository-onboarding-spec-kit-2026-07-23.md`

## Dry-run 结果

onboarding dry-run 的 13 项 gate 全部通过：

- candidate contract
- owner decision
- repository metadata
- source risk
- analysis report
- duplicate check
- security review
- phase gate
- registry conflict
- target path
- local-submodule materialization
- dry-run workspace
- rollback plan

计划固定：

- registry repo：`spec-kit`
- group：`workflow-core`
- priority：`P1`
- sync mode：`fetch`
- branch：`main`
- enabled/status：`yes / active`
- owner：`llm-agent-governance-owner`
- intake policy：`observe-first`
- grade：`A`
- materialization：`local-submodule`
- source HEAD：`ee883a1d4ecee9afe06a81f1bd38a0b745a8d059`

`check-reference-repository-registration.sh` 对本计划及 fixtures 检查通过，`checked=3`。

## 正式 Apply 与修复证据

| Command | Exit Code | Result |
|---|---:|---|
| `rtk scripts/onboard-reference-repository.sh . ... --materialization local-submodule` | 0 | dry-run 计划生成 |
| `rtk scripts/check-reference-repository-registration.sh . --plan reports/reference-repository-onboarding-spec-kit-2026-07-23.json` | 0 | registration plan/fixtures 通过 |
| 原 dirty `main` 上增加 `--apply` | 2 | `[FAIL] reference onboarding gates failed: apply_workspace_gate`；事务写入前终止 |
| 隔离 worktree 首次 `check-practice-intake.sh` | 2 | 未初始化 `agent-dev-kit`，暴露环境缺口 |
| 从 GitHub 初始化 `agent-dev-kit` | 1 | 私有远端凭证不可用；未绕过凭证边界 |
| 从本机 Git 对象源初始化精确 gitlink 后复跑 | 0 | practice intake pass；未复制原子仓 dirty 文件 |
| 隔离 worktree 正式 `--apply --materialization local-submodule` | 0 | `mode=apply`，13 项 gate 全部通过 |
| apply 后首次 `check-practice-intake.sh` | 2 | removal pass fixture 的 adoption-matrix 哈希按设计失效 |
| 更新 fixture 为新矩阵 SHA-256 后复跑 | 0 | practice/removal contract 和两项测试全部通过 |
| `rtk scripts/check-all.sh --quick` | 1 | 52/53；仅 `check-reference-dirty-triage.sh` 失败 |
| `rtk scripts/check-reference-dirty-triage.sh .` | 1 | `OpenSpec`、`superpowers`、`vibeflow` 既有 baseline 均在 2026-07-20 到期 |

## 正式登记结果

- `.gitmodules` 新增 `spec-kit`，canonical URL 为 `https://github.com/github/spec-kit`。
- `spec-kit` gitlink 固定为 `ee883a1d4ecee9afe06a81f1bd38a0b745a8d059`；工作树 clean。
- `subrepos/registry.csv`：`P1 / fetch / main / active / observe-first / A`。
- `manifests/subrepo_lifecycle.json`：`active-reference`，`automation_eligible=false`，包含禁止安装、禁止执行外部 runtime 和吸收前复核边界。
- adoption matrix Markdown/JSONL 同步，状态为 `adopt / done`。
- onboarding plan 为 `status=applied / mode=apply`，13 个 gates 全为 `true`。
- 五个准入工件哈希与 dry-run 记录完全一致；candidate 在 `expires_at=2026-10-21` 前有效。

## Verification

- registration plan/fixtures：pass，`checked=3`。
- practice intake：pass。
- reference repository removal：pass，`checked=3`。
- registration/removal tests：pass。
- adoption matrix status/structured：pass。
- authorized subrepos、AGENTS coverage、source integrity、ADK target evidence：pass。
- subrepo state：9 clean、0 dirty、0 uninitialized、0 missing。
- quick aggregate：52 pass、1 fail；失败项是既有 baseline 到期，不影响 spec-kit 登记数据或 gitlink 正确性。

## Open Item

`OpenSpec`、`superpowers`、`vibeflow` 的 known-dirty baseline 续期必须在原工作区基于真实用户变更重新取证；本分支不伪造 fingerprint 或延长过期日期。该事项阻止声明“仓库全量门禁全部通过”，但不回退已经通过独立 registration/apply gate 的 spec-kit 正式登记。

## 长期跟踪边界

- `active-reference` 只允许 fetch/diff/analyze。
- 每周检查 release/tag/security metadata，每月语义 diff，每 90 天复核。
- 只跟踪 integration 生命周期、managed-file/rollback、catalog/preset/extension/bundle 治理、workflow fail-closed、brownfield/spec 演化和 Codex target 变化。
- 不自动吸收，不执行 upstream code，不提供本机 token，不修改 `agent-dev-kit` 或 `~/.codex`。

## Gate Result

`scoped-pass / repository-wide-needs-fix`：`spec-kit active-reference` 已在隔离分支正式登记并通过全部登记范围门禁；仓库级 quick aggregate 仍受三个既有 reference dirty baseline 过期影响，不能声明全仓 53/53。
