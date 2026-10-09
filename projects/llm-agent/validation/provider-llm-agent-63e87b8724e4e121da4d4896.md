---
id: provider-llm-agent-63e87b8724e4e121da4d4896
title: ADK 7.14.1 来源升级与运行资产验证
kind: validation
domain: projects/llm-agent
path: projects/llm-agent/validation/provider-llm-agent-63e87b8724e4e121da4d4896.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: provider-candidate-archive
  from: provider-policy-sha256:a295759999c3c3c2594752350565bbde6af74808af32b9272604f53a36f82736;operation:63e87b8724e4e121da4d4896d649c2d91a675c8ffe92715acc2fa1e3c0b9263f
  source_sha256: d6156b28fb8410d89d728a66679d98e8a18678c2bd98bc8dc9dedc5098053f26
  temporary_source_retained: false
review_after: '2027-01-04'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- provider-archive
- validation
validation_refs:
- projects/llm-agent/validation/provider-llm-agent-63e87b8724e4e121da4d4896.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/llm-agent/validation/provider-llm-agent-63e87b8724e4e121da4d4896.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-10-06'
updated_at: '2026-10-06'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-10-06'
manual_validation_pending: true
summary_zh: 本轮采用精确来源和阶段验证：ADK main 19dafa7c61355c04c08e87adcf3eae6946020f92，官方 immutable v7.14.1 制品 SHA256 e32fd405b6cef3698ff8148a79dddac647a7f96f1bc3be727c842bd242f50826，实际签名固定官方
  workflow 和 issuer 校验通过。版本、tree、manifest、制品和签名必须一起核验，不将相同 tree 的不同 commit 或历史签名替换为新的来源证明。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
aliases:
- ADK 7.14.1 来源升级与运行资产验证
related:
- projects/llm-agent/README.md
- indexes/obsidian-home.md
- indexes/project-readiness.md
---

# ADK 7.14.1 来源升级与运行资产验证

本轮采用精确来源和阶段验证：ADK main 19dafa7c61355c04c08e87adcf3eae6946020f92，官方 immutable v7.14.1 制品 SHA256 e32fd405b6cef3698ff8148a79dddac647a7f96f1bc3be727c842bd242f50826，实际签名固定官方 workflow 和 issuer 校验通过。版本、tree、manifest、制品和签名必须一起核验，不将相同 tree 的不同 commit 或历史签名替换为新的来源证明。

ADK 7.14.1 修复非 quick 严格验证的版本身份检查、Git worktree 实际根边界以及测试 fixture symlink/hook 隔离。三 Python 版本本地各97项、routing30项及wheel/audit通过；实际主线CI attempt2和发布run通过。attempt1的临时Git目录清理失败保留，具体写入者尚未证明，不宣称该偶发问题已修复。

Codex重复导入修复已在PR43合并；精确7.14.1来源升级PR44已合并，main 9770140b813a612a2a673b0d3a9c6ddf90c32d38。原本地五文件的增删行完整保留，未跟踪journal保留；备份和命名stash仍在。用户改动没有混入源升级提交。

实际源仓完整执行build、doctor、plan、dry-run、apply、check，保留team-collab。运行资产69个受管变更有原计划和备份；应用后344项测试通过，四profile smoke通过，diff/missing均0，drift changed/stale/unmanaged均0。配置hash不变，计划保留路径和输出身份均匹配。build tree SHA256 092fe31a22bb5b032b49de42969cf89d8fd6bd1c7aa65e9fdd691994e0dd457d；plan SHA256 cdffd08587926fdfcea5d03796c1b3cc4111ee59b242762df9e9ebb504678c57。

根仓最终六路径本地完整回归一次72/72通过，独立审查零blocker/major/minor。评测工具冻结12任务和72计划运行，未调用真实模型，未量化真实收益。

边界：本地runtime conformance、签名来源与源码测试分别成立，不能推导owner/M5/产品资格。历史状态投影fresh_for_current_source=false、release_authorized=false。session-wrap缺少LICENSE的单条警告仍待核实合法来源后处理。没有保存原始会话、日志、凭据或个人主体推断。
