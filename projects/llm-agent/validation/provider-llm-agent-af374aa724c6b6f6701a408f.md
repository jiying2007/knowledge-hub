---
id: provider-llm-agent-af374aa724c6b6f6701a408f
title: 资格工具修复与已有签名证据接入
kind: validation
domain: projects/llm-agent
path: projects/llm-agent/validation/provider-llm-agent-af374aa724c6b6f6701a408f.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: provider-candidate-archive
  from: provider-policy-sha256:a295759999c3c3c2594752350565bbde6af74808af32b9272604f53a36f82736;operation:af374aa724c6b6f6701a408f61a9609e2eeddcadde771ee671cf35343b45dac2
  source_sha256: 707418ad1ac40ca6183a318871082742fd5c3dac1b6dd0805e1756f3faca4e95
  temporary_source_retained: false
review_after: '2027-01-07'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- provider-archive
- validation
validation_refs:
- projects/llm-agent/validation/provider-llm-agent-af374aa724c6b6f6701a408f.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/llm-agent/validation/provider-llm-agent-af374aa724c6b6f6701a408f.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-10-09'
updated_at: '2026-10-09'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-10-09'
manual_validation_pending: true
summary_zh: '用户允许累计上限1.05亿、分阶段检查，继续禁止模型调用，仅接入已有真实证据。 实际源码修复：rollover新增显式expected-model（默认gpt-5.5不变），保留外层/嵌套模型一致、候选四身份、quality、时效与摘要校验；JSON复用bounded
  regular strict读取；公开入口保留lexical路径，拒绝链接；诊断新增opt-in pinned cosign/trusted-root crypto验证，默认无外部进程。 17项M5定向测试PASS；非repo help PASS；doc-sync/diff-check
  PASS。 冻结后完整Root74/74 '
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
aliases:
- 资格工具修复与已有签名证据接入
related:
- projects/llm-agent/README.md
- indexes/obsidian-home.md
- indexes/project-readiness.md
---

# 资格工具修复与已有证据接入验证

用户允许累计上限1.05亿、分阶段检查，继续禁止模型调用，仅接入已有真实证据。
实际源码修复：rollover新增显式expected-model（默认gpt-5.5不变），保留外层/嵌套模型一致、候选四身份、quality、时效与摘要校验；JSON复用bounded regular strict读取；公开入口保留lexical路径，拒绝链接；诊断新增opt-in pinned cosign/trusted-root crypto验证，默认无外部进程。
17项M5定向测试PASS；非repo help PASS；doc-sync/diff-check PASS。
冻结后完整Root74/74 PASS；ADK quick56/56 PASS；最终串行Root quick51/52，workspace fingerprint稳定，唯一FAIL为原有历史M5 policy与当前8.0.5发布证据不匹配。整体Root quick仍FAIL，不重写为PASS。
已有8.0.5签名实际验证通过：canonical main CI identity/issuer、cosign3.1.3实体SHA256 4629c757b7618056f8ddd7e2625ae9fdd94c0372a65049520bc7d9df9efc7f71、trusted-root SHA2566494e21ea73fa7ee769f85f57d5a3e6a08725eae1e38c755fc3517c9e6bc0b66。diagnostic promotion_signature PASS，evidence d607402e2e0e5248e0f53a4a525748e218b24bebeed9ef01d1397a49a73fbd02，attestation bb4dd5781c7af2b249721bec2d6aaccc65b0a74aa3bd4cfafe457c91846c9894。
检查的现有实测属于旧candidate/manifest，不能作为当前8.0.5实测；G21两target static、trusted native receipt为空；G22 index0 entries、测量0/86。未重新标注旧报告、未修改policy/qualification/scorecard/历史field，未启动模型或认证campaign。
M5最低门槛为一份measured runtime、一个独立真实仓及一位真人，calendar_days0；30天和第二操作者是运营建议，不加作首次硬门槛。
负结果保留：系统rg无PCRE2；宿主完整PATH下native synthetic test失败，而精简PATH定向PASS，未确定精确宿主因素；缺rtk/cosign的quick46/52为无效环境，补齐既有工具入口后51/52；verifier symlink拒绝，实体binary读取预算问题改为regular streaming hash后真实验签成功。没有削弱断言或信任门禁。
自审由主Agent执行，不声称新增独立人审。源码本地验证阶段完成；本批六路径补丁保留工作区，未自动commit/push/merge/apply。真实M5/G21/G22資格仍blocked，没有伪造owner或外部输入。
