---
id: provider-xcrz-sigmastar-demo-2d0fd6fc97ed64db46486648
title: CALL final PCM protected candidate v19
kind: debug-record
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/archive/provider-xcrz-sigmastar-demo-2d0fd6fc97ed64db46486648.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: provider-candidate-archive
  from: provider-policy-sha256:a295759999c3c3c2594752350565bbde6af74808af32b9272604f53a36f82736;operation:2d0fd6fc97ed64db464866482c0be26d262c524737e657a8aa929dae7cd3457e
  source_sha256: f8af69babc002dfe2fd74ce5e6ee5ad90ecd9625c573ebc25b4ad2bae42469ad
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
- projects/xcrz-sigmastar-demo/archive/provider-xcrz-sigmastar-demo-2d0fd6fc97ed64db46486648.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/archive/provider-xcrz-sigmastar-demo-2d0fd6fc97ed64db46486648.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-10-10'
updated_at: '2026-10-10'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-10-10'
manual_validation_pending: true
summary_zh: 'Status: Host development and table-independent quality gates passed. This is the retained conservative candidate,
  not production or acoustic qualification. Budget150000000; upper audio lifecycle and production defaults remain intact.'
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
subject_ref: &id001
  id: xcrz-sigmastar-demo
  type: project
created_subject_ref: *id001
principal_id: null
provider_operation_id: 2d0fd6fc97ed64db464866482c0be26d262c524737e657a8aa929dae7cd3457e
---

# CALL final PCM protected candidate v19

Status: Host development and table-independent quality gates passed. This is
the retained conservative candidate, not production or acoustic qualification.
Budget150000000; upper audio lifecycle and production defaults remain intact.

Same88 statistics and convex protection as v18. Dependency-free damped Newton
barrier produced a quantized feasible256-cell table. Predicted far mean0.626276
dB/worst-0.033481dB, all112 protected constraints pass original1e-6 tolerance.
First barrier stage reached128 steps, later eight stages converged by decrement;
overall converged=false remains recorded. Terminal stationarity max0.0209643,
central-path gap estimate8.03e-8 is numerical only; no rigorous/global optimum
claim. The table does not consume clean labels during inference.

Model SHA2568451849f18cf5f3f2c75184b337607cdf6491dd2e357679a460fb9bd2b59ccc0.
Candidate binary SHA256ab608dc444620d1b7c72f114f6e171da4e2c3eb16d5e59b6ddfaba0abbdaac5b.
Solver source SHA25613ebc98920475790bf1a2c1d7e0e636d53b4d08aa5ff873c6c0625be82d9a0c9.

| Set | Far mean/worst delta dB | Double mean/worst delta dB | Verdict |
|---|---|---|---|
| Original development24 | +0.629375/+0.093 | +0.121083/0.000 | pass |
| Original development8 | +0.932000/+0.054 | +0.127125/+0.051 | pass |
| Exposed old24 | +0.653000/+0.076 | +0.124542/0.000 | pass |
| Expanded balanced24 | +0.503042/-0.034 | +0.117750/0.000 | pass |
| Expanded nonlinear8 | +0.601750/+0.067 | +0.127500/+0.017 | pass |
| New independent24 | +0.527042/-0.076 | +0.103292/-0.029 | pass |

All explicit-near original metrics exact; no tracked clips or AGC internal
saturation increase. Independent target-projection worst-0.149dB remains inside
-0.2dB gate. Native reference evaluator identity and every actual input/binary
hash checked. Independent split c217dfd3ccf7d526216304ac5dace4cc5091c20aac7086861d7d5c21d011350b
was frozen before v18/v19 fitting and scored once after all88 gates passed.
Official train partition is independent of this table fit; native NN pretraining
corpus remains unknown, so this is not official challenge qualification.

file202 double regression improved from v17-2.610 to v19+0.045dB relative to native;
file506 far regression improved from-0.164 to-0.034dB. Do not call this device
echo resolution: average extra attenuation is modest and no new HIL occurred.

82 Python tests passed, analytic optima and independent derivative controls,
actual v19 C ASan/UBSan feature/FIFO/no-ref/Reset/VOICE/native-AGC-state controls.
Fresh default Host static/shared libraries byte-identical to previous version,
164 production sources unchanged. Build receipt remains fresh-default-v18-bound.
Host2000-frame candidate CALL mean237.713us vs native234.384us measured separately;
VOICE PCM hash identical. Timing variance and adapter heap are not ARM resource proof.

Retain this immutable candidate while testing whether the correction's0.2 gain
floor restricts safe residual suppression. Native NN/profile parameters remain
fixed. Any next bounds experiment needs new independent data; this24 is now
exposed regression for future candidates. Current v19 qualification is historical
for its frozen fit, not transferable to a new model. No commit or deployment.

Codify: reusable_pattern=final-PCM-protection-with-native-AGC-trajectory;
promotion_candidate=false; next_task_friction_reduced=true;
reduced_by=first independently passing conservative candidate;
reduction_evidence=all six qualified receipts and label-free compiled binary;
do_not_promote_reason=ARM and acoustic qualification absent;
owner_review=false; rollback_path=preserve current native default and frozen v19;
verification_evidence=tail-pcm-*-qualified-v19 and fresh-default-v18-bound.

## 中文导读与资格边界

历史 v19 记录：当时冻结的首次独立 24 例及开发门禁通过，只对应该候选、数据与评估身份。整体数值收敛仍未成立，Host 耗时不代表 ARM 资源，未知 NN 预训练语料也不支持官方挑战或生产声学资格；后续扩大回归另有失败记录。
