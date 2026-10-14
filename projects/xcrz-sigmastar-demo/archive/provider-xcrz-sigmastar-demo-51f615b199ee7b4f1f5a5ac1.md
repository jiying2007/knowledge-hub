---
id: provider-xcrz-sigmastar-demo-51f615b199ee7b4f1f5a5ac1
title: CALL final PCM projection constraints v17
kind: debug-record
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/archive/provider-xcrz-sigmastar-demo-51f615b199ee7b4f1f5a5ac1.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: provider-candidate-archive
  from: provider-policy-sha256:a295759999c3c3c2594752350565bbde6af74808af32b9272604f53a36f82736;operation:51f615b199ee7b4f1f5a5ac11ba726a99e0a698b7d14df3a48152da09e6dfcf4
  source_sha256: 06260d032cb5ef13c6ec2b70fad8edae933b0da797931ac5757cdc5fbf1da114
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
- projects/xcrz-sigmastar-demo/archive/provider-xcrz-sigmastar-demo-51f615b199ee7b4f1f5a5ac1.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/archive/provider-xcrz-sigmastar-demo-51f615b199ee7b4f1f5a5ac1.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-10-10'
updated_at: '2026-10-10'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-10-10'
manual_validation_pending: true
summary_zh: 'Status: needs-fix. No production adoption, global optimum or acoustic success claim. User approved budget 150000000;
  active goal remains open.'
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
subject_ref: &id001
  id: xcrz-sigmastar-demo
  type: project
created_subject_ref: *id001
principal_id: null
provider_operation_id: 51f615b199ee7b4f1f5a5ac11ba726a99e0a698b7d14df3a48152da09e6dfcf4
---

# CALL final PCM projection constraints v17

Status: needs-fix. No production adoption, global optimum or acoustic success
claim. User approved budget 150000000; active goal remains open.

The label-free 256-cell table retains native NN gain, source/removed-echo power
ratio and causal signed EMA cross-power features. Original NN drives AGC, while
the candidate uses its gain trajectory. IFFT, 512-point sqrt-Hann overlap and
512-sample output delay are matched. On 32 development cases the frozen-control
mapping's worst metric error is 0.00115349 dB, final RMS error <=1.92444 PCM units.
All 64 native/control original metrics exactly match the previous evidence.

Training protects final PCM at the native near-target projection alpha0:
residual ||y-alpha0*n|| squared may not increase, and the target dot may not
decrease. This is a sufficient SI-SDR protection with numerical tolerance for
the observed training windows, not a bound on unobserved callers. All 32 far,
8 near and 32 double-window statistics use only original development data.

The initial 32768-step ADMM did not converge and failed 4/40 protected quantized
constraints. Its raw model SHA is b862068c5550aaf1b2d5f4da0a2fa631ff8b75ea4dfd59c90010320e72c820be;
no header was emitted. A fixed-geometry Dykstra feasibility repair, without
quality feedback or independent data, used 656 cycles and changed any coefficient
by at most 119 Q20 units. All original 1e-6-tolerance constraints then passed.
Finite feasibility still does not establish a global optimum.

Repaired model SHA 507357aab2b5f9180ec4b43ba083192c6424baa65f9305008c151ce949468ee7.
Candidate binary SHA 7047c0430afd7ec9fb54f3ecc801772f209f64a8c6fedbcccf782df20239160e.

| Set | Far mean / worst delta dB | Double mean / worst delta dB | Verdict |
|---|---|---|---|
| Development 24 | +1.434 / +0.487 | +0.420 / 0.000 | all gates pass |
| Development 8 | +1.631 / -0.095 | +0.451 / +0.104 | all gates pass |
| New balanced 24 | +1.196 / -0.164 | +0.500 / -0.081 | far-worst fails |
| New nonlinear 8 | +1.314 / +0.319 | +0.429 / -0.063 | all gates pass |
| Exposed regression 24 | +1.380 / +0.014 | +0.313 / -2.610 | double-worst fails |

Every set keeps explicit near-only metrics exact and has no clipping increase.
The new balanced set's file506 far delta -0.164 violates the -0.1 threshold.
Exposed file202 double delta -2.610 is severe; 215,220,236,263 also violate -0.1.
Average improvement cannot override these failures. The new sets were frozen
before this candidate score and never used in its fit. The balanced24 comes
from the pinned source's train partition; it is independent of this table fit,
not official challenge qualification. Native NN pretraining corpus is unknown.

This experiment supports the final PCM geometry on development data, while
showing that 32 training examples do not cover important device-feature/target
relations. It does not prove that enlarging data alone will solve generalization.
Next: reclassify all now-exposed 88 as development, include every observed
failure in the same final-PCM protection geometry, and freeze a new disjoint
balanced24 before the next candidate. Do not tune on previously scored holdouts
while continuing to call them independent. Production parameters remain intact.

Evidence: pcm-design-statistics-v17.json; FITTING-RECIPE-v17.json;
INDEPENDENT-RECIPE-v17.json; tail-pcm-model-v17[-repaired]/model.json;
tail-pcm-development24/8-v17.json and their qualified receipts;
tail-pcm-independent24/8-v17.json and their qualified receipts;
tail-pcm-exposed-regression24-v17.json and its qualified receipt.
Default Host build: fresh-default-v17-bound/build.json, 69 compiles, default
SO 1f0dbcbda5db2f377d8eba1b0a161c7f6ccdfb4a7513a1def39dd61f892a73fe,
static A cc9561d29c93d00948eb90c1a59b0a0f28f8d59a01ca3895107c798a9a807532.
All 164 production source identities are unchanged from v16.

Testing checkpoint: 74 Python controls before source-partition/repair additions;
six intake controls passed; ASan/UBSan PCM design/sidechain ownership, Reset,
VOICE/no-ref identity and framing controls passed. A final consolidated suite is
still required after current Python additions. No independent code review,
ARM candidate resource proof, final app relink or device acoustic HIL occurred.

Codify: reusable_pattern=matched-final-PCM-convex-protection;
promotion_candidate=false; next_task_friction_reduced=true;
reduced_by=validated native trajectory and isolated data intake;
reduction_evidence=32 matched controls and explicit holdout provenance;
do_not_promote_reason=far and severe double regression;
owner_review=false; rollback_path=retain current native production default;
verification_evidence=paired receipts and fresh-default-v17-bound.

## 中文导读与资格边界

历史 v17 记录：原开发窗口经可行性修复满足约束，但新 balanced 24 的远端最差项及已暴露双讲回归仍失败。有限可行不证明全局最优，也不支持生产采用；当时最终 Python 整合尚未完成。
