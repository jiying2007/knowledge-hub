---
id: provider-llm-agent-85cdfb6aec9222231a5a7243
title: ADK 主分支同步与验证边界审查候选
kind: audit
domain: projects/llm-agent
path: projects/llm-agent/archive/provider-llm-agent-85cdfb6aec9222231a5a7243.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: provider-candidate-archive
  from: provider-policy-sha256:a295759999c3c3c2594752350565bbde6af74808af32b9272604f53a36f82736;operation:85cdfb6aec9222231a5a7243b5c9bd8d99fecf19139ae1379052f386902d581a
  source_sha256: 110c9d100b9e65d2727f339f8ef6abc63bc18bff318d05b2d1d12131608bee2d
  temporary_source_retained: false
review_after: '2027-01-03'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- provider-archive
- audit
validation_refs:
- projects/llm-agent/archive/provider-llm-agent-85cdfb6aec9222231a5a7243.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/llm-agent/archive/provider-llm-agent-85cdfb6aec9222231a5a7243.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-10-05'
updated_at: '2026-10-05'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-10-05'
manual_validation_pending: true
summary_zh: 状态：reviewing；由 AI 生成，待 owner review。仅保存脱敏结论，不含原始会话、日志或凭证。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
---

# ADK 主分支同步与验证边界审查候选

状态：reviewing；由 AI 生成，待 owner review。仅保存脱敏结论，不含原始会话、日志或凭证。

结论：同步长期开发分支到主分支前，应比较最终 Git tree，不能仅用提交 SHA 判断有效修改是否未合入。此次本地两个提交的最终 tree 与主分支合入提交一致，因此保留旧分支并快进 main，无需重复重放修改。

验证：ADK 当前 canonical main 为 ed688c94d3fb101c77b9f22a6c7b9a1aa90d9c40，匹配 llm_agent gitlink 和 adk.lock。同步后根仓快速门禁由早期基线 34/52 变为 47/52；这属于基线收敛，不可当作本轮代码优化收益。

已实施的可复用修复：全回归 runner 显式绑定自身 cwd，同时保留调用者相对输出路径语义；评测文件拒绝每层重复 JSON 键，包含 Unicode 转义后的相同键；验证路径分级使用目录边界和显式文件族，避免近似文件名误触发布门禁。

负结果：ManifestError 继承 ValueError 时，宽泛的解析异常捕获会重新包装领域错误；应只捕获 JSONDecodeError 和 UnicodeError。运行中的 Bash 脚本被修改会破坏读取位置，此类回归必须以固定源码重新运行。已退役目录中残留的 Python 缓存也可能触发旧权威检测；只处置经过检查的生成物，保留恢复锚点。

证据：agent-dev-kit/src/agent_dev_kit/effect_trials.py；agent-dev-kit/tests/test_effect_trials.py；agent-dev-kit/tests/run_all.sh；tools/codex_assets/validation_plan.py；tests/test_validation_plan.py；docs/changes/20261005-internal-external-iteration.md。validation_plan 定向 19 tests 通过；adoption evidence 206 rows / 602 paths 通过；完整回归仍需以最终报告为准。

风险：合成回归、完整源码回归、签名制品身份、真实 runtime/field 和 owner 决策是独立证据线；本候选不声明发布或效果资格。未提交源码不能作为 clean-commit runtime bundle 证据。

下一步：先固定真实任务集与运行身份测量收益，再调整 harness、上下文加载或拆分热点；外部规范与方法保持设计输入，不自动激活 runtime。长期权威由 Provider 与 owner review 决定。
