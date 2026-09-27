---
id: adk-four-repo-source-live-validation-20260927
title: ADK 与 Codex 四仓来源和运行资产门禁验证
kind: validation
domain: codex
path: domains/codex/validation/adk-four-repo-source-live-2026-09-27.md
scope: team-general
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: workspace-report
  from: workspace://llm-agent/reports/adk-four-repo-closure-2026-09-27.md
  source_sha256: a99c6dfd6c7f013d31fb98e809b4a096f4e32b3f7b2256102a8511522cecf3c0
review_after: '2026-10-04'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- validation
- capture
- manual-validation-pending
validation_refs:
- domains/codex/validation/adk-four-repo-source-live-2026-09-27.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- domains/codex/validation/adk-four-repo-source-live-2026-09-27.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-09-27'
updated_at: '2026-09-27'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-09-27'
manual_validation_pending: true
summary_zh: 核对四仓来源、双 Python 回归和 Codex 安装预览；本机 live 仍待合规解释器与正式应用。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
aliases:
- ADK 与 Codex 四仓来源和运行资产门禁验证
related:
- indexes/obsidian-home.md
---

# ADK、Codex 与 Knowledge Hub 四仓交付检查点

状态：`source-verified / live-pending`。本记录只绑定本轮本机证据；未完成的门禁不得解释为运行态或发布完成。

## 目标与边界

- 目标：核对 `llm_agent → agent-dev-kit → ~/codex → ~/.codex` 的来源和安装链，并将有证据的结论交给 Knowledge Hub。
- 保留：根仓未跟踪参考目录、Knowledge Hub 已有脏改、Codex 认证/session/memory/`.system` 与当前 live profile。
- 停止条件：ADK 全量回归失败、Codex 来源或计划漂移、本机缺少合规 Python、live 计划触及受保护或未纳入计划的资产。
- 本轮不自动提交、推送、合并、提升 Hub active 或改写已有证据。

## 来源基线

| 层级 | 当前基线 | 本轮观察 |
| --- | --- | --- |
| `llm_agent` | `59967ae39f755fa00fcfffad850359a03e8ec4ad` | gitlink 固定 ADK `86e1306b287b1dbe593865b4fe8cfa667743c548`；参考目录未跟踪状态保留 |
| `agent-dev-kit` | `86e1306b287b1dbe593865b4fe8cfa667743c548`，`v7.8.0` | 仅 5 个测试文件有本轮局部修改，尚未形成新提交身份 |
| `~/codex` | `62047a56e4b5ede2201c325a10ebd9cb46b9d558` | 与 `origin/main` 为 `0/0`，工作区干净；provider lock 固定 ADK `7.0.31` |
| `~/knowledge-hub` | `6aaeaf4477f403af6ffffd7b613d432a6255e185` | registry、索引和项目资料已有用户脏改，本轮未覆盖 |

## 阶段检查点

1. **ADK 源码**：信任测试的模拟脚本改用当前 Python 解释器绝对路径；退役目录检查忽略仅由 `__pycache__` 构成的缓存目录，仍拒绝其他残留。定向验证：native trust `4/4`、Agent Value trust `5/5`、Execution Policy `19/19`、文档命令对齐和模块架构检查通过。同一工作树快照 `b803ec7fb8896fcb8dcffa010a8458c6327b11f0f766930f40ad801055075a41` 的 Python 3.11/3.12 完整门禁及依赖审计通过，各版本测试 `90/90`、路由 `30/30`；回执为 `agent-dev-kit/.cache/local-ci/full-parity-receipt.json`，状态 `pass`。该回执不提供发布权限。
2. **Codex 来源**：只读审计比较现有 42 个启用 ADK Skill 与干净 ADK `7.8.0` 候选，`blocked_skills=0`，目录差异为 0；`v7.0.31..v7.8.0` 的 `skills/`、`agents/`、`execution_policy/` 源码差异也为 0。不得仅为版本变化改标既有来源。
3. **Codex 运行资产预览**：隔离 Python 3.11 的 51 项来源/执行策略/安装测试通过。在临时源副本按当前 live `team-collab` profile 完成 build、repo/build doctor、plan 和 apply dry-run；计划为复制 78、覆盖 57、删除旧受管 80、保留 340。删除项全部位于旧受管 `vendor/`；受保护的认证、session、memory、`.system` 和 `config.toml` 无写动作。预览计划绑定容器路径，不能用于本机 apply。
4. **Knowledge Hub**：`knowledge-check --dry-run` 当前有 3 个与本轮无关的音频资料治理错误及既有 registry/index 脏改；不据此提升 active 或覆盖既有记录。跨仓结论仅形成 reviewing 候选。根仓 `check-doc-sync` 通过、`check-token-budget` 通过但有 warning；`check-agents-coverage` 因缺少 `digital-worker` 路径返回 2，与本轮四仓改动分列。

## 当前阻塞与下一步

- 本机 Codex 入口使用 Python 3.8.10，更新后的 `~/codex` 要求 Python 3.11/3.12；在取得受信任的独立解释器前不得执行正式 build/plan/apply。
- Codex 本机 source-to-live、live doctor/diff/drift/no-op 和 Hub reviewing 候选登记尚未完成；各层结论独立报告。
- 下一步最多三项：准备独立 Python 并重新生成本机计划；完成受管应用与 live 复验；登记 Hub reviewing 记录并核对其状态。
