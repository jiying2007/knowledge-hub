---
aliases:
- M5当前main真实签名CI核验
related:
- projects/llm-agent/README.md
- indexes/obsidian-home.md
- indexes/project-readiness.md
id: provider-llm-agent-3ccf828bb9ab8991bf5f7045
title: M5当前main真实签名CI核验
kind: validation
domain: projects/llm-agent
path: projects/llm-agent/validation/provider-llm-agent-3ccf828bb9ab8991bf5f7045.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: provider-candidate-archive
  from: provider-policy-sha256:a295759999c3c3c2594752350565bbde6af74808af32b9272604f53a36f82736;operation:3ccf828bb9ab8991bf5f7045c7cf6297954bf9a63ec93f3cc1af5e69d7d7b9ac
  source_sha256: 9abcf934f2a549084996e325b8498fc52f775e9bbedb1df8244c4a67f6b27ed8
  temporary_source_retained: false
review_after: '2027-01-09'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- provider-archive
- validation
validation_refs:
- projects/llm-agent/validation/provider-llm-agent-3ccf828bb9ab8991bf5f7045.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/llm-agent/validation/provider-llm-agent-3ccf828bb9ab8991bf5f7045.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-10-11'
updated_at: '2026-10-11'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-10-11'
manual_validation_pending: true
summary_zh: 'verified_at: 2026-10-11 status: reviewing software_m5_certified: false owner_review: 未执行人类资格审批'
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
subject_ref: &id001
  id: llm-agent
  type: project
created_subject_ref: *id001
principal_id: null
provider_operation_id: 3ccf828bb9ab8991bf5f7045c7cf6297954bf9a63ec93f3cc1af5e69d7d7b9ac
---

# M5 当前 main 真实签名 CI 核验

verified_at: 2026-10-11
status: reviewing
software_m5_certified: false
owner_review: 未执行人类资格审批

PR194与PR195已按用户全部授权合并。最终main为af92f63dc91b668dd716e763ffe1f9683de7280a；GitHub CI38148730646 completed/success，完整integration与software-m5-ci-receipt实际执行成功，均非SKIPPED。此基线push已经提供所需完整集成签名回执，无需重复手动运行同基线CI。

下载software-m5-root-ci-receipt后，使用固定实体Cosign3.1.3 SHA4629c757b7618056f8ddd7e2625ae9fdd94c0372a65049520bc7d9df9efc7f71、固定public trusted-root SHA6494e21ea73fa7ee769f85f57d5a3e6a08725eae1e38c755fc3517c9e6bc0b66，调用生产m5_ci_contract.validate_receipt独立离线核验，signature-verified。真实绑定canonical repository/main/ci.yml、eventpush、head af92f63、run38148730646/attempt1以及contract/doc-sync/integration/integration-summary全部success。

回执envelope SHA096ac6b0be4332f69856319f24c32aeeba88ff8702663e91046b2d150d190a31；签名payload SHA420c1d54aa9a1330e817cfb037edd508049d897050ad824a20ade899f19f90ca。不是mock、run编号自报或unsigned报告。此前PR194基线跳过签名CI的记录保留为历史负结果，不能重标成本次。

root签名CI证据缺口已在此最终源码基线补齐；qualification整体、真实signedruntime、independent humanfield与owner资格尚未完成。零模型调用，未注册runner、部署服务或修改live。缺专用机器时本机一次性隔离runner的只读登录/namespace预检和官方包digest核验已通过，执行设施本身尚待实现与验收。

源：GitHub运行38148730646实际API回读、真实下载回执及固定实体Cosign独立验签。只归档脱敏结论与摘要，不存credential、rawsession或二进制。下一步保持本main基线采集签名runtime与真实field，再完整rollover，不能由本签名授予域外放行。
