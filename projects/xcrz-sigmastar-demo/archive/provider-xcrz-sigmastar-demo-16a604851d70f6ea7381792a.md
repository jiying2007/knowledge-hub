---
id: provider-xcrz-sigmastar-demo-16a604851d70f6ea7381792a
title: v30固定算术组约束负结果
kind: debug-record
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/archive/provider-xcrz-sigmastar-demo-16a604851d70f6ea7381792a.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: provider-candidate-archive
  from: provider-policy-sha256:a295759999c3c3c2594752350565bbde6af74808af32b9272604f53a36f82736;operation:16a604851d70f6ea7381792ab2bbc95a74fc4a88eec67f10d4ac054b98bcb71d
  source_sha256: 4e25d91ec2bc186cff9fbb291e3a76c5db21d7b2ebbb3a8156af3c8714766226
  temporary_source_retained: false
review_after: '2027-01-08'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- provider-archive
- debug-record
validation_refs:
- projects/xcrz-sigmastar-demo/archive/provider-xcrz-sigmastar-demo-16a604851d70f6ea7381792a.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/archive/provider-xcrz-sigmastar-demo-16a604851d70f6ea7381792a.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-10-10'
updated_at: '2026-10-10'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-10-10'
manual_validation_pending: true
summary_zh: 用户本轮授权继续提高预算，按上一轮2亿建议更新Runtime累计Token200M，时间仍36h。 计划PLAN-v30、输入验证DRY-v30；完整102 tests PASS、非仓cwd help/dry-run PASS。
  固定184开发、239保护窗口、九组；独立1996未使用。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
subject_ref: &id001
  id: xcrz-sigmastar-demo
  type: project
created_subject_ref: *id001
principal_id: null
provider_operation_id: 16a604851d70f6ea7381792ab2bbc95a74fc4a88eec67f10d4ac054b98bcb71d
---

# v30固定算术组约束负结果

用户本轮授权继续提高预算，按上一轮2亿建议更新Runtime累计Token200M，时间仍36h。
计划PLAN-v30、输入验证DRY-v30；完整102 tests PASS、非仓cwd help/dry-run PASS。
固定184开发、239保护窗口、九组；独立1996未使用。

一次固定两阶段拟合在Phase I正常收敛：9个barrier阶段全部converged=true，最后6步，
slack=0.0014321505527057883 >0；数值duality gap估计1.185e-7（不是全局证明）。
无法建立去除slack后的严格可行点，所以工具exit1明确拒绝，没有候选模型/头文件输出，
未执行主优化、实际C质量评分或独立集评分。原SI/target/逐例far/范围约束未松弛。
失败阶段为新增算术平均残差充分条件；不能断言原平均dB验收本身不可满足。

下一方向：使用固定v29开发表作为log残差的切线参考，构造逐组平均log残差的凸充分上界。
ln(r)<=ln(r0)+(r-r0)/r0，每组加权二次约束
mean(r/r0)<=1-ln(10)*.5025/10-mean(ln(r0))，可保证组平均dB收益，
相比算术平均更贴近当前残差分布。参考只用已重分类开发，不允许独立数据。
这是新v31设计，需重新冻结plan、身份和控制，不改变v30记录或原质量门槛。
无生产默认/库/上层生命周期改动，无commit/push/deploy/restart。主声学目标仍未完成。
