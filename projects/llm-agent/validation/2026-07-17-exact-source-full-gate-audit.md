---
related:
- projects/llm-agent/validation/2026-07-15-exact-source-quick-gate-audit.md
- projects/llm-agent/validation/project-readiness.md
- governance/product/validation/project-readiness.md
target_version: llm_agent@1d7730af7afe0217fd387533cd490d64eca51e7e with seven exact gitlinks
test_environment: isolated local clones under /tmp; current host runtime dependencies; no remote network
human_reviewed_by: null
human_reviewed_at: null
review_basis: null
aliases:
- LLM Agent 精确源码 Full 门禁审计 2026-07-17
id: llm-agent-exact-source-full-gate-audit-20260717
title: LLM Agent 精确源码 Full 门禁审计 2026-07-17
kind: validation
domain: projects/llm-agent
path: projects/llm-agent/validation/2026-07-17-exact-source-full-gate-audit.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: manual
  from: llm_agent 根仓与 7 个 gitlink 精确 commit 的隔离全量验证
  source_sha256: 21383d3c228cbf679e64e8ec1ed7ec35de74b1486fd8cf8889b7599425569f30
review_after: '2026-10-17'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- llm-agent
- exact-source
- validation
- full-gate
- portability
validation_refs:
- projects/llm-agent/validation/2026-07-17-exact-source-full-gate-audit.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
- rtk bash scripts/check-all.sh --full
- rtk bash scripts/check-wechat-intake-ledger.sh .
evidence_strength: direct-command
evidence_refs:
- projects/llm-agent/validation/2026-07-17-exact-source-full-gate-audit.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
- projects/llm-agent/validation/2026-07-15-exact-source-quick-gate-audit.md
- projects/llm-agent/validation/project-readiness.md
created_at: '2026-07-17'
updated_at: '2026-07-19'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-07-17'
manual_validation_pending: true
manual_validation_reason: 唯一失败需在源项目修复可移植输入契约并复跑 full；正式 artifact、release、rollback 仍未闭环。
summary_zh: 在根仓与 7 个 gitlink 精确 commit 的隔离克隆中执行 full 聚合门禁，61/62 通过；唯一失败源于 full 无条件依赖被 Git 忽略的 wechat-articles 外部语料目录，当前不能声明全量可移植恢复通过。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: checked
---

# LLM Agent 精确源码 Full 门禁审计 2026-07-17

## 验证目标

验证已登记的 `llm-agent` 根仓 commit 及其 7 个精确 gitlink commit，在不借用原工作区脏状态、未跟踪文件或远端网络的条件下，能否通过仓库定义的 `full` 聚合门禁。

本报告证明的是“精确 Git 源码集合 + 当前本机运行依赖”中的命令结果和唯一失败根因。它不证明正式 artifact、远端 release、生产采用、跨主机复现或 rollback 已完成，也不构成 owner 决策。

## 验证对象

| 仓库路径 | Commit |
| --- | --- |
| 根仓 `llm_agent` | `1d7730af7afe0217fd387533cd490d64eca51e7e` |
| `OpenSpec` | `3c7a05c5dc88b2397c478805890b55ed392b19e8` |
| `agent-dev-kit` | `0d25f3da7ac1f141a5172d62cfc7b6f4bfbd93b1` |
| `scale-engine` | `ace49169c4191db656989b738f31edb19a380a63` |
| `superpowers` | `6efe32c9e2dd002d0c394e861e0529675d1ab32e` |
| `vibeflow` | `0df764eff5e7b034611540da8d9f8367dfae55b2` |
| `oh-my-codex` | `f947e3a41c062c25fd107686862b68ee5d1b66a5` |
| `planning-with-files` | `d71b3be47b62fe49d60fb2ede800e1907ebea3d9` |

根 commit 和 7 个 gitlink 与 2026-07-15 Quick 审计相同。本轮继续使用本机对象库构造隔离克隆，没有从当前子仓 HEAD 推断版本。

## 环境

- 日期：2026-07-17。
- cwd：`/tmp/kh-llm-agent-full-20260717-1052`。
- 根仓与子仓：从本机 Git 对象库构造，checkout 到上表精确 commit；没有访问远端网络。
- 源项目边界：`~/bin/llm_agent` 及其子仓只读；没有修改、清理或借用其中的未提交内容。
- 运行边界：部分门禁仍读取当前本机 `~/codex`、`~/.codex` 或其他已声明 runtime 状态，因此结果不能外推到任意主机。
- 证据保留：Hub 保存 commit、命令、结果摘要和根因链；临时 clone、缓存及长输出不作为正式 artifact。

## 验证命令

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
| --- | --- | --- | --- | --- | --- |
| `rtk git submodule status` | 0 | 7 个子仓均为根 gitlink 指定 commit，无 `+` 漂移。 | 临时隔离目录；commit 已固化于本报告 | Source | 精确源码集合 |
| `rtk bash scripts/check-all.sh --full` | 1 | 62 项中 61 项通过；唯一失败为 `check-wechat-intake-ledger.sh`。 | 临时隔离目录；汇总固化于本报告 | Project / Tool | 无正式 artifact |
| `rtk bash scripts/check-wechat-intake-ledger.sh .` | 1 | 稳定复现：缺少 `./wechat-articles`，在检查 ledger 内容前即退出。 | 临时隔离目录 | Project / Tool | `reports/wechat-article-intake.jsonl` |
| `rtk wc -l reports/wechat-article-intake.jsonl` | 0 | 已跟踪 ledger 为 313 行；该计数不能替代原始语料存在性和 freshness 校验。 | 临时隔离目录 | Source | ledger |
| `rtk git ls-tree -r --name-only HEAD -- wechat-articles hermes_data reports/wechat-article-intake.jsonl scripts/check-wechat-intake-ledger.sh` | 0 | Git 树仅含 ledger 与 checker，不含 `wechat-articles/` 或 `hermes_data/`。 | 精确根 commit | Source | 根 commit |
| `rtk git check-ignore -v --no-index wechat-articles/probe.md` | 0 | `.gitignore:3` 明确忽略 `wechat-articles/`。 | 精确根 commit | Source | 根 commit |

补充说明：

- `check-adk-harden-readiness.sh`、`check-adk-performance-ops.sh`、`check-evidence-bundle.sh`、`check-token-budget.sh` 和 `check-workspace-entrypoints.sh` 均在本次 `full` 聚合中通过。
- 其中 harden、performance 和 workspace entrypoints 为耗时项；本轮完整执行，没有用 2026-07-15 的 Quick 结果代替。
- 聚合命令退出码为 1，因此整体结论必须保持失败/部分通过，不能因 61 项通过而标记为 full pass。

## 结果矩阵

| Case | 期望 | 实际 | 状态 | 证据 |
| --- | --- | --- | --- | --- |
| 精确源码身份 | 根仓与 7 个 gitlink 无漂移 | 全部精确匹配 | 通过 | `git submodule status` |
| Full 聚合 | 62/62 | 61/62 | 失败 | `check-all.sh --full`，退出码 1 |
| Hardening | 通过 | 通过 | 通过 | Full 聚合子项 |
| Performance ops | 通过 | 通过 | 通过 | Full 聚合子项 |
| Evidence bundle | 通过 | 通过 | 通过 | Full 聚合子项 |
| Token budget | 通过 | 通过 | 通过 | Full 聚合子项 |
| Workspace entrypoints | 通过 | 通过 | 通过 | Full 聚合子项 |
| WeChat intake ledger | 在精确源码 checkout 中可执行且可验证 freshness | 输入目录缺失，无法进入 ledger 对比 | 失败 | 单项稳定复现 |
| Artifact / release / rollback | 可校验且可恢复 | 本轮未生成或执行 | 待验证 | `llm-agent` evidence contract 继续 pending |

## 唯一失败的根因链

1. `scripts/check-all.sh --full` 无条件把 `check-wechat-intake-ledger.sh` 纳入 62 项聚合。
2. checker 硬编码读取根目录下的 `wechat-articles/`，要求至少 300 篇 Markdown，并重新生成临时 ledger 与已跟踪 ledger 做精确比较。
3. 同一精确提交的 `.gitignore` 明确忽略 `wechat-articles/`；`git ls-tree` 也证明该目录不在 Git 树中。
4. 精确提交只保存 313 行 ledger、decision overlay、生成器和 checker。因此全新 checkout 没有满足 checker 的原始输入。
5. 原 `llm_agent` 工作区当前存在另一位置的未跟踪参考语料，但它既不是精确 commit 的组成部分，也不是 checker 声明的输入路径；本轮没有复制、链接或静默注入。

由此可直接确认：临时克隆没有丢失已跟踪文件；失败属于“可移植 full 门禁与外部数据输入契约不一致”。它不是 ledger 已被证明过期，也不是其余 61 项失败。

## 结论

本轮结论为“Full 聚合部分通过但整体失败”：精确复合源码在当前本机环境中完成 62 项检查，61 项通过，唯一失败是 WeChat intake gate 依赖 Git checkout 不具备的外部语料目录。

这条负证据收窄了 `llm-agent` 的剩余源码恢复缺口，但不支持把项目标为 full-ready 或 evidence-ready。2026-07-15 的 Smoke 12/12、Quick 56/56 结论仍有效；本报告只补充 Full 模式的真实结果和可移植性阻塞。

## 剩余风险

- 未定义原始语料的受治理 locator、版本、hash/manifest、可用性策略和缺失时语义。
- 直接把本机未跟踪目录做软链接会制造不可审计的主机依赖，不能作为修复或通过证据。
- 只从 `--full` 删除 checker 会降低覆盖面；必须保留显式的 live-corpus 校验入口和负向测试。
- 正式 artifact、release record、远端留存和 rollback drill 仍未闭环。
- 报告由 Codex 起草，保持 `reviewing` 与 `manual_validation_pending`；本次授权不等于 owner 内容签署或 lifecycle promotion。

## 后续动作

源项目后续修复应在单独授权下完成，建议采用双层契约：

1. 可移植层：提交 metadata-only 的 corpus manifest（至少包含稳定 path/id、hash 和期望计数），让默认 `full` 能在纯 Git checkout 中验证 ledger 与 manifest 一致。
2. Live-data 层：checker 接受显式 `--articles-dir` 或同等受治理 locator，校验实际语料、manifest 和 ledger 三者一致；输入缺失、路径错误、计数不足和 ledger stale 均必须 fail closed。
3. 聚合层：`check-all.sh --full` 明确声明运行哪一层；需要真实语料的模式应显式启用，不能从任意本机目录自动猜测。
4. 复验顺序：先定向运行 `rtk bash scripts/check-wechat-intake-ledger.sh .`，再运行 `rtk bash scripts/check-all.sh --full`；目标分别为退出码 0 和 62/62。
5. 修复后再补正式 artifact、release record 与 rollback drill；在此之前 `llm-agent` evidence contract 保持 `pending`。

```yaml
manual_validation_pending: true
manual_validation_reason: 源项目仍需修复 WeChat 外部语料的可移植输入契约并复跑 full；正式 artifact、release、rollback 仍未闭环。
required_followup:
  - 在 llm_agent 源项目中设计并评审 portable manifest 与 explicit live-corpus 两层契约
  - 补 absent/path/count/stale 四类负向测试
  - 定向 gate 通过后复跑 full，目标 62/62
  - 生成并验证正式 artifact、release record 与 rollback drill
owner: leiwenjun
review_after: 2026-10-17
```
