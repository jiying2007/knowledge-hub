---
id: provider-xcrz-sigmastar-demo-21757d955c1e22b5a7df9ab9
title: 'Expanded136 strict final-PCM fit v21: rejected'
kind: debug-record
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/archive/provider-xcrz-sigmastar-demo-21757d955c1e22b5a7df9ab9.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: provider-candidate-archive
  from: provider-policy-sha256:a295759999c3c3c2594752350565bbde6af74808af32b9272604f53a36f82736;operation:21757d955c1e22b5a7df9ab92b0b271a0c693b724c27ffceb3339a4a84428861
  source_sha256: e08716cb1157d2385cdd436ae0cfbf1a14d16900e2d84baa8ab0b0d6105bdc43
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
- projects/xcrz-sigmastar-demo/archive/provider-xcrz-sigmastar-demo-21757d955c1e22b5a7df9ab9.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/archive/provider-xcrz-sigmastar-demo-21757d955c1e22b5a7df9ab9.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-10-10'
updated_at: '2026-10-10'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-10-10'
manual_validation_pending: true
summary_zh: logical_task_open:true; completion_claim:false; shipping_approved:false. Native production defaults and upper
  readers/subscriptions/leases/proto unchanged. No commit/push/deployment/new device capture. Budget150m remains active.
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
subject_ref: &id001
  id: xcrz-sigmastar-demo
  type: project
created_subject_ref: *id001
principal_id: null
provider_operation_id: 21757d955c1e22b5a7df9ab92b0b271a0c693b724c27ffceb3339a4a84428861
---

# Expanded136 strict final-PCM fit v21: rejected

logical_task_open:true; completion_claim:false; shipping_approved:false.
Native production defaults and upper readers/subscriptions/leases/proto unchanged.
No commit/push/deployment/new device capture. Budget150m remains active.

Both recent exposed24 cohorts explicitly became development; new reserved24
split2b9d5eb0c37a1db55e95f37c5c766cc4194d55c3a1ecf911f33fd1dba3ef8da4
remains unscored and prohibited from fitting. Expanded statistics contain136
unique examples,136 far and172 near/DT constraints from seven fixed cohorts.
96 new native/frozen-v20 observed runs preserve all original metrics; native
feature/IFFT/AGC gain trajectories exactly match between paired observations.
New mapping worst metric error0.000523516dB; max PCM RMS2.229359.

One fixed Newton fit, unchanged strict residual/native-target protection,
coefficient bounds[0,1], native NN feature floor0.2. All nine stages converge by
decrement; terminal stationarity max0.001022713 and gap estimate9.63e-8 are
numerical diagnostics, not a proof of a global optimum. Quantized predicted far
mean+0.438345dB/min-0.099998dB, below the mean+0.5 gate.171/172 protected
constraints pass;202 DT normalized residual1.00000177287 exceeds1.000001.
No model header generated, no actual candidate evaluation or independent score.
No repair attempted because quantization repair cannot resolve insufficient
far objective improvement. This result supersedes any narrower candidate PASS.

84 Python tests pass without skips; root/module diff --check pass. Default
Host static/shared and164 production source identities remain at v20-bound;
Python tools/schema/tests/docs are the only changes in this phase. No ARM
resource, device-installed identity, subjective cure or product qualification.

Evidence SHA256:
- expanded136 statistics:c9ba1651c5b19f4963502b9ace0d4b580376cb692547416a2b4ca14115a3b8b6
- recent24 statistics:6fc9bf2c43dacee64e7f9a5dacd37537de2e2a5b20f1f735f7503f81499cef7f
- failed24 statistics:64ea627428854c16fe00f1b6381330ea9e36b26dea43ad43ec2cd9b56afa091d
- model:e1831a1f128d03e1c6e12ca3bfebefaccabe74c1608d9f8e8d6a7d8a09fb8034
- dry-run:de93e0f942150c4f6ac1e99b4ee97f1934d4b3ede65b6d107d166fd348254ed1

Replan: use a single analytic sufficient training SI-SDR loss reserve0.08dB,
inside unchanged actual worst-case gate-0.1dB, while retaining native target-dot
nondecrease and native AGC. No change to actual quality acceptance and no
feedback threshold scan. Same features/data/box/objective/fixed Newton schedule;
all seven actual development subsets must pass before reserved24 is opened.

## 中文导读与资格边界

历史 v21 记录：扩大到 136 例后，预测远端均值低于原门槛，且一项量化保护约束失败，因此未生成模型头、未评估实际候选、未评分新独立集合。数值收敛不证明全局最优，源码/Host 检查不代表 ARM、设备或产品资格。
