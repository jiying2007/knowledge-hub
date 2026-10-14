---
id: provider-xcrz-sigmastar-demo-6a4cce1a3723e96391982070
title: 'Analytic0.08dB reserve v22: reject borderline far case'
kind: debug-record
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/archive/provider-xcrz-sigmastar-demo-6a4cce1a3723e96391982070.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: provider-candidate-archive
  from: provider-policy-sha256:a295759999c3c3c2594752350565bbde6af74808af32b9272604f53a36f82736;operation:6a4cce1a3723e963919820709577eb91f8df9d7ef4454e892fe8cd69ad7b572f
  source_sha256: f7a2822db7812f7cddfa3bf7ae3555a9e018c9678e5a98b53991574246c2e728
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
- projects/xcrz-sigmastar-demo/archive/provider-xcrz-sigmastar-demo-6a4cce1a3723e96391982070.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/archive/provider-xcrz-sigmastar-demo-6a4cce1a3723e96391982070.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-10-10'
updated_at: '2026-10-10'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-10-10'
manual_validation_pending: true
summary_zh: logical_task_open:true; completion_claim:false; shipping_approved:false. Same136 statistics and256 features/native
  AGC; one fixed training reserve0.08dB with native target-dot nondecrease. Quantized172 protected constraints pass, far predicted
  mean0.707470983/min-0.099996311dB; all9 Newton stages co
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
subject_ref: &id001
  id: xcrz-sigmastar-demo
  type: project
created_subject_ref: *id001
principal_id: null
provider_operation_id: 6a4cce1a3723e963919820709577eb91f8df9d7ef4454e892fe8cd69ad7b572f
---

# Analytic0.08dB reserve v22: reject borderline far case

logical_task_open:true; completion_claim:false; shipping_approved:false.
Same136 statistics and256 features/native AGC; one fixed training reserve0.08dB
with native target-dot nondecrease. Quantized172 protected constraints pass,
far predicted mean0.707470983/min-0.099996311dB; all9 Newton stages converge
by decrement. No exact global optimum claim. Model SHA256
fbd7591fcce0819059d91a19ce81eb4d3cecd50e5de3a84a7e759e9499d0b107.

Actual C seven cohort far means0.750708/1.121250/0.805958/0.569250/
0.734500/0.623500/0.641125dB. All near-only original metrics exactly unchanged,
DT minima-0.080/-0.051/-0.045/-0.023/-0.034/-0.038/-0.064dB; target minima
nonnegative at published precision. No internal AGC, IFFT, OLA, output-gain or
final clipping increase. Frozen candidate ASan/UBSan contracts pass: integer
basis/FIFO/no-ref/Reset/native AGC state/VOICE and negative controls. Vendor
static library itself is not wholly sanitizer-instrumented.

Six cohort receipts pass; recent24 fails far_worst because published decimal
2.764-2.864 becomes-0.10000000000000009 in binary floating subtraction (file580).
Did NOT add a tolerance or round the failure away. Actual integer-PCM observer
verified all fields except output match native, then matched-window recomputation
gives580 far-0.100002530752dB, DT+0.023665756135dB, target+0.032826938732dB.
Thus actual far narrowly fails too. File506 recomputation far-0.099952519256dB,
DT+0.056027854600dB,target-0.000038517883dB. The new independent24 stays unscored.

85 Python checks pass, no skips. Production defaults/business lifecycle unchanged;
no commit/push/new device capture/deployment or subjective cure. Default static
cc9561d29c93d00948eb90c1a59b0a0f28f8d59a01ca3895107c798a9a807532.
Candidate evaluator SHA abf97f9705c9121cd6f489980dbb82919d269706b6dd7b6af743d7d154e5a0bc;
sanitizer contract caa8422264949928ead10508793aa4eca90f2f62400eb82ba0ff419bc3ad4eca.
Boundary traces580:c93f8c337475c145dfc9a902a622217caf682d717a35fa7babd3de211adb99a2,
506:b12d72f3fa564f782b2849fa69c877a3b827fe05ab9183a378da50fdad0312d7.

Replan one fixed training far reserve0.0025dB, based on twice the maximum already
validated mapping metric error0.001154dB rounded up, inside unchanged actual
worst far gate-0.1dB. Keep0.08dB protected reserve, same data/box/objective/Newton.
Final actual-PCM precision verification must accompany the published3-decimal
metrics before candidate qualification; no tolerance or actual gate relaxation.

## 中文导读与资格边界

历史 v22 记录：多数开发约束通过，但边界远端样本的十进制门禁及精确整数 PCM 重算都略低于原门槛，因此保留拒绝结果，未加容差消除失败。新独立集合未评分，供应商静态库并未完整插桩，生产默认和设备部署未改变。
