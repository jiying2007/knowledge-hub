---
related: []
aliases:
- llm_agent 外部实践吸收候选
- agent-dev-kit 优化候选 2026-07
id: llm-agent-external-practice-absorption-candidates-20260723
title: llm_agent 与 agent-dev-kit 外部实践搜索及吸收候选
kind: external-source-note
domain: projects/llm-agent
path: projects/llm-agent/archive/research/2026-07-23-external-practice-absorption-candidates.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: manual
  from: 'repository-report: workspace://llm-agent/reports/external-practice-search-and-absorption-candidates-2026-07-22.md'
  source_sha256: 5b76d8d0e5296a71b4564756abbdb4ffd50289443019d7da748a7a8191defd2a
  temporary_source_retained: false
review_after: '2026-10-23'
review_status: human-reviewed-accepted
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- llm-agent
- agent-dev-kit
- external-practice
- absorption-governance
- repository-runtime-eval
validation_refs:
- projects/llm-agent/archive/research/2026-07-23-external-practice-absorption-candidates.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/llm-agent/archive/research/2026-07-23-external-practice-absorption-candidates.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-07-23'
updated_at: '2026-07-26'
generated_by_ai: true
ai_role: summarized
ai_model_or_tool: Codex
ai_generated_at: '2026-07-23'
manual_validation_pending: true
summary_zh: 基于 2026-07-22 统一 intake、官方文档和论文定向复核，形成真实仓库 runtime campaign、过程质量、成本分布、安全 canary、MCP 兼容与现场证据候选；全部保持 review-required，不授权
  ADOPT 或运行态变更。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
---

# llm_agent 与 agent-dev-kit 外部实践搜索及吸收候选

## 归档元数据

- captured_at：2026-07-23
- last_verified：2026-07-23
- source_retrieved_at：2026-07-22
- topic：`external-practice-absorption`
- status：`review-required`
- authority：研究候选，不是 owner `ADOPT` 决策，不进入 active authority lane
- source：`workspace://llm-agent/reports/external-practice-search-and-absorption-candidates-2026-07-22.md`
- evidence：`workspace://llm-agent/reports/external-practice-cycle-evidence-2026-07-22.json`

## 摘要

对 `llm_agent` 统一 external-practice intake、现有采纳矩阵、`agent-dev-kit` M5/target/eval 资产，以及官方文档、官方仓库和研究论文进行交叉复核后，未发现继续扩张同义 Skill、Agent 或编排框架的充分理由。

高价值增量集中在真实仓库运行证据、通过后的过程质量、跨 trial 成本分布、安全编码 canary、MCP 新版本兼容和现场试点方法。所有建议均保持 `review-required`；在独立 owner decision、许可证/安全审查和定向验证完成前，不修改 ADK、采纳矩阵或运行时资产。

## 搜索覆盖与健康

2026-07-22 统一 intake 结果：

| Provider | 候选数 | 状态 |
|---|---:|---|
| GitHub | 30 | complete |
| GitLab | 0 | complete |
| Gitee | 0 | degraded-empty |
| OpenAI 官方 | 64 | complete |
| Anthropic 官方 | 5 | complete |
| 微信治理目录 | 20 | complete |

总计 118 条候选，去重 1 条。整体搜索健康为 `degraded`：Gitee 空结果必须保留为负证据，GitLab 0 条不代表该生态没有相关实践。

## 当前能力边界

已验证的 ADK 基线包括 13 个 Agent、55 个 core Skill、10 个 optional Skill、9 个 profile 和 7 个 workflow。三个 direct target 的静态 contract 检查通过，但状态仍为 `experimental`。

Software M5 campaign 已有 `baseline/adk`、双 runtime、三次 trial、预算、重试、成功率、route/safety、P95 latency 和 usage ratio。其 60 条任务字段为 `prompt/category/expected_skill/expected_safe`，本质是路由与安全分类任务，不等价于在真实仓库完成多文件编码、测试和修复。

M5 certification 仍缺独立仓库、第二 operator、30 天 pilot、更多真实仓库/field event 和真实 runtime campaign 证据。因此当前只支持 M5-ready control-plane candidate，不支持 M5 certified 声明。

## 可复用吸收候选

### 1. Repository-runtime campaign

建议状态：`CANDIDATE-ENHANCE`，优先级 P0。

建立独立于现有 routing campaign 的真实仓库 eval contract。可选择 Inspect SWE 作为 optional adapter，吸收以下机制：

- sample sandbox 与受控 runtime adapter；
- Codex CLI、Claude Code 等多 runtime 的可比执行；
- transcript、time/message/token/cost limit；
- retry/resume 与失败分类；
- 固定 task、repo revision、container digest、model/runtime version。

不得把 Inspect SWE 变成 core dependency，不默认运行任意外部容器或安装脚本，不沿用宽网络或长期凭证配置。

来源：

- https://inspect.aisi.org.uk/tutorial.html
- https://meridianlabs-ai.github.io/inspect_swe/
- https://github.com/meridianlabs-ai/inspect_swe

### 2. 过程质量与 lucky pass

建议状态：`CANDIDATE-ENHANCE`，优先级 P0。

最终测试通过不能覆盖回归循环、盲目重试、遗漏验证和阶段乱序。建议把以下字段加入 trace/effect eval：

- `regression_cycle_count`
- `blind_retry_count`
- `missing_final_verification`
- `phase_order_violation`
- `pass_with_invalid_process`
- `repeated_tool_call_without_new_evidence`

来源：https://www.microsoft.com/en-us/research/publication/agentlens-revealing-the-lucky-pass-problem-in-swe-agent-evaluation/

### 3. Runtime customization isolation

建议状态：`CANDIDATE-ENHANCE`，优先级 P0。

现有 baseline/adk 比较应记录每个 runtime 实际关闭或启用的 customization surface。Claude target 可参考 `--safe-mode` / `CLAUDE_CODE_SAFE_MODE` 关闭项目指令、plugins、Skills、Hooks 和 MCP。其他 runtime 若不能可靠隔离，应标记 `not-comparable`，不得生成误导性的效果差值。

来源：https://github.com/anthropics/claude-code/releases

### 4. 任务新鲜度与多环境 canary

建议状态：`CANDIDATE-ENHANCE`，优先级 P1。

从 SWE-bench-Live 吸收任务时间、仓库 revision、task/container digest、多语言/多 OS 分层、contamination 标记和 gold patch 重复验证方法。只选择 5–10 条小型冻结 canary，不导入全量高资源 benchmark。

来源：https://github.com/microsoft/SWE-bench-Live

### 5. 安全编码 canary

建议状态：`CANDIDATE-ENHANCE`，优先级 P1。

从 SecCodeBench 和 SecureVibeBench clean-room 派生 3–5 条固定任务。判断顺序必须是功能测试先通过，再执行动态 exploit 或高置信静态 oracle；LLM-as-a-Judge 不得成为唯一安全 oracle。

来源：

- https://github.com/alibaba/sec-code-bench
- https://aclanthology.org/2026.acl-long.1107/

### 6. Token/cost 分布

建议状态：`CANDIDATE-ENHANCE`，优先级 P1。

现有单一 usage ratio 应扩展为 input/output/cached token 的 p50、p95、max，以及 `cost_per_success`、跨 trial 方差、retry、round、timeout 和 tool-call count。预算事实必须来自 runtime/provider 观测，不能以 Agent 自报替代。

来源：https://www.microsoft.com/en-us/research/publication/how-do-ai-agents-spend-your-money-analyzing-and-predicting-token-consumption-in-agentic-coding-tasks/

### 7. Field evidence v2

建议状态：`CANDIDATE-ENHANCE`，优先级 P1。

现场试点增加任务预注册、拒绝/跳过日志、human baseline、wall-clock/human-active/agent-active time 分离、并发 Agent 重叠区间、operator/repo/task family 分层、置信区间和失败案例。

来源：

- https://metr.org/hcast.pdf
- https://metr.org/blog/2026-02-24-uplift-update/
- https://dora.dev/research/2025/dora-report/

### 8. MCP 2026-07-28 compatibility review

建议状态：`CANDIDATE-OBSERVE`，优先级 P0。

截至 source retrieval 日期 2026-07-22，MCP 2026-07-28 仍处 release candidate 窗口。只能先定义 `protocol_version`、`capabilities`、`extension_ids`、`deprecated_features`、`auth_profile`、`compatibility_test` 和 `rollback` 候选字段。

最终规范实际发布、breaking-change diff、负向 fixture 和真实 client/server compatibility smoke 完成前，不修改 core contract，不启用 Tasks、Apps 或 extensions。

来源：

- https://blog.modelcontextprotocol.io/posts/2026-07-28-release-candidate/
- https://modelcontextprotocol.io/specification/2025-11-25/basic/authorization
- https://modelcontextprotocol.io/docs/tutorials/security/security_best_practices

### 9. OWASP Agentic Skills Top 10 crosswalk

建议状态：`CANDIDATE-OBSERVE`，优先级 P1。

把 AST01–AST10 映射到现有 provenance、hash、permission、deny-path、sandbox、scan、retire 和 target conformance。其 Universal Skill Format 与部分风险页面仍处后续路线图，不建立第二套 Skill SSOT，不把候选格式当成稳定行业标准。

来源：https://github.com/OWASP/www-project-agentic-skills-top-10

### 10. Skill 维护证据

建议状态：`CANDIDATE-ENHANCE`，优先级 P2。

增加 `upstream_revision`、`retrieved_at`、`content_digest`、`stable_behavior_diff`、`target_local_binding_diff`、`use_count`、`effect_evidence`、`last_verified_at` 和 `retire_or_refresh_due_at`。目标是提高维护证据质量，不扩大 core Skill 数量。

来源：https://arxiv.org/abs/2607.00911

## 不吸收边界

以下候选默认拒绝或只作 discovery source：

- 与现有 memory、context、verification、parallel、automation 能力重复的 Skill 集合；
- 自带 daemon、后台状态、宽 MCP/文件写权限的新 orchestration runtime；
- awesome list、笔记和目录型仓库；
- 与既有 `AGENTS.md` 约定冲突的单数 `AGENT.md` 方案；
- 第二套 Skill compiler、IR 或 Universal Skill Format；
- 缺少许可证、固定 release、真实 trace 和独立评测的个人项目。

Stars、下载量、作者自报性能和 README 宣称只作排序线索，不作吸收证据。

## 推荐 change 边界

### Change A：`repository-runtime-campaign-v1`

只新增真实仓库 eval contract、optional adapter、隔离 baseline、过程质量、成本分布和少量安全/freshness canary；不改变现有 routing campaign 的语义。

### Change B：`mcp-2026-07-28-compat-review`

最终规范发布后只处理版本、capability、弃用、授权和 rollback compatibility；不默认启用新 extension。

### Change C：`field-evidence-v2`

补第二 operator、独立仓库、30 天 pilot、选择偏差与人工时间证据；不降低现有 M5 门槛。

## 验证记录

2026-07-22/23 已获得以下证据：

- candidate schema：118 条通过；
- cycle evidence schema：通过；
- review queue schema：通过；
- external-practice intake contract、安全、幂等和 terminal boundary：通过；
- llm_agent 文档同步、采纳矩阵状态、token budget：通过；
- quick gate：53 项中 50 项通过，3 项失败来自既有 dirty reference subrepo 和过期 baseline；`agent-dev-kit` 为 clean。

本归档不把工作区整体表述为 pass，也不把研究候选表述为已采纳。

## 风险与刷新条件

- Gitee `degraded-empty` 和 GitLab 0 条必须保留为搜索覆盖限制。
- 外部动态事实在进入 change 前重新检查 release、commit、许可证和安全状态。
- 真实付费模型、外部容器、网络和凭证 campaign 需要独立批准。
- MCP 与 OWASP AST10 在稳定发布前保持 observe。
- 任一候选只有通过 duplicate、legal/security、architecture、owner decision、verification 和 pilot gate 后才可进入 ADK change。

## 版权与脱敏

正文仅保存方法摘要、候选判断和外部 URL，不复制论文、文档或第三方仓库正文；未保存 secrets、auth、Cookie、私有端点、raw session、cache、二进制或完整日志。

## 治理状态

- Archive Candidate：yes
- Memory Candidate：no
- AGENTS Candidate：no
- Promotion：none
- Manual validation pending：yes
- Gate Result：`reviewing`
- 下一次复核：2026-10-23，或 MCP 2026-07-28 最终规范发布后提前复核
