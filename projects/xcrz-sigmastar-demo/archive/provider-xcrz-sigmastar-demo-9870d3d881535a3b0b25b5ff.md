---
id: provider-xcrz-sigmastar-demo-9870d3d881535a3b0b25b5ff
title: Correction-bound experiment and broader regression v20
kind: debug-record
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/archive/provider-xcrz-sigmastar-demo-9870d3d881535a3b0b25b5ff.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: provider-candidate-archive
  from: provider-policy-sha256:a295759999c3c3c2594752350565bbde6af74808af32b9272604f53a36f82736;operation:9870d3d881535a3b0b25b5ff5410174276e4d2b2e0eaae080a186c5723284b66
  source_sha256: fde405f4fdeb2e449fd18794c0949b4b4932577f3450fa79da2700af62f9c4de
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
- projects/xcrz-sigmastar-demo/archive/provider-xcrz-sigmastar-demo-9870d3d881535a3b0b25b5ff.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/archive/provider-xcrz-sigmastar-demo-9870d3d881535a3b0b25b5ff.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-10-10'
updated_at: '2026-10-10'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-10-10'
manual_validation_pending: true
summary_zh: 'Status: needs-fix. v20 denied promotion; v19 also fails the newly exposed broader regression. Its earlier independent24
  PASS remains historical for that cohort, but must not be treated as qualification over all136 known cases. Keep native production
  default. No deployment, commit or upper audio life'
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
subject_ref: &id001
  id: xcrz-sigmastar-demo
  type: project
created_subject_ref: *id001
principal_id: null
provider_operation_id: 9870d3d881535a3b0b25b5ff5410174276e4d2b2e0eaae080a186c5723284b66
---

# Correction-bound experiment and broader regression v20

Status: needs-fix. v20 denied promotion; v19 also fails the newly exposed broader
regression. Its earlier independent24 PASS remains historical for that cohort,
but must not be treated as qualification over all136 known cases. Keep native
production default. No deployment, commit or upper audio lifecycle changes.

v20 widened only correction coefficients to[0,1]; native feature/NN floor0.2,
AGC driver, features, same88 fit data and quality gates stayed intact. All Newton
stages converged by decrement, predicted far mean0.709879dB, all112 protected
quantized constraints passed. Terminal stationarity0.01033/gap estimate8.03e-8
are numerical, not rigorous global-optimum proof.
Model SHA0610269d7f0f589aecee9debacf4d1e59c855f1aab0ea419ad2a1bf4b979d8f0.
All112 development/exposed regression cases passed actual integer gates.

New frozen independent24 SHA58e9db08227dee887652292c177d4d78f9f694ed72fc41d661bbb83df11897f4,
At freeze exclusions were112 IDs plus cross-role speakers/source clips;
official train partition, NN pretraining unknown. It was scored once after all112
passed. Far mean+0.577958/worst+0.211dB, DT mean+0.130917/worst-0.179dB;
file564-0.179 and605-0.174 violate DT>=-0.1. Near exact, target worst-0.046,
tracked clips decreased1 and AGC saturation did not increase. Average cannot
override these two failures.

The frozen v19 was then scored on this exposed24 as regression: far mean+0.511958,
worst+0.041; DT worst-0.172, including564-0.172 and605-0.146. This is not a new
independent qualification. Both tables need broader protection coverage.

83 Python tests and actual v20 C ASan/UBSan VOICE/native-AGC/FIFO/no-ref/Reset
controls passed. Fresh default69-compile Host build fresh-default-v20-bound:
shared1f0dbcbda5db2f377d8eba1b0a161c7f6ccdfb4a7513a1def39dd61f892a73fe
is unchanged; no production source edits, app relink, ARM candidate or device HIL.

Next: reclassify both recent24 cohorts as development, total136. Observe and
validate48 additional final-PCM native/frozen-v20 controls, merge exactly seven
cohorts, fit the same strict protection and[0,1] bounds once. Freeze a new disjoint
balanced24 before fitting. No weakening of actual quality gates or new feature
search. Numerical feasibility and generalization remain separate questions.

Codify: reusable_pattern=independent-scope-does-not-transfer-to-broader-regression;
promotion_candidate=false; next_task_friction_reduced=true;
reduced_by=identified564/605 generalization failures;
reduction_evidence=tail-pcm-independent24-qualified-v20 and broader-v19 receipt;
do_not_promote_reason=double-talk regression;
owner_review=false; rollback_path=native production default;
verification_evidence=seven actual paired evaluations and fresh-default-v20-bound.

## 中文导读与资格边界

历史 v20 记录：扩大系数范围后的开发回归通过，但新独立 24 例的两项双讲结果低于原门槛；旧 v19 在该暴露集合也失败。旧首次独立 PASS 保留为历史，不能转为全部 136 例资格；保留 native 生产默认，无部署或设备 HIL。
