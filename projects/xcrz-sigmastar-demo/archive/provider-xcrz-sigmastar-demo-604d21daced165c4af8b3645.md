---
id: provider-xcrz-sigmastar-demo-604d21daced165c4af8b3645
title: 'Fixed numerical reserve v23: development pass, independent DT failure'
kind: debug-record
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/archive/provider-xcrz-sigmastar-demo-604d21daced165c4af8b3645.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: provider-candidate-archive
  from: provider-policy-sha256:a295759999c3c3c2594752350565bbde6af74808af32b9272604f53a36f82736;operation:604d21daced165c4af8b3645b03cec69229f8970e7b56635c375089f390d816a
  source_sha256: 4046ae40547de5252f1d1718d3b154187864b19056ebba5360fb9ae144e56811
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
- projects/xcrz-sigmastar-demo/archive/provider-xcrz-sigmastar-demo-604d21daced165c4af8b3645.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/archive/provider-xcrz-sigmastar-demo-604d21daced165c4af8b3645.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-10-10'
updated_at: '2026-10-10'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-10-10'
manual_validation_pending: true
summary_zh: logical_task_open:true; completion_claim:false; shipping_approved:false. Same136 fitted examples/256features/nativeAGC/box0..1,
  protected loss reserve 0.08dB and fixed far training reserve0.0025dB; actual quality gates unchanged. 172 quantized protection
  constraints pass; predictedfar mean0.70736115
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
subject_ref: &id001
  id: xcrz-sigmastar-demo
  type: project
created_subject_ref: *id001
principal_id: null
provider_operation_id: 604d21daced165c4af8b3645b03cec69229f8970e7b56635c375089f390d816a
---

# Fixed numerical reserve v23: development pass, independent DT failure

logical_task_open:true; completion_claim:false; shipping_approved:false.
Same136 fitted examples/256features/nativeAGC/box0..1, protected loss reserve
0.08dB and fixed far training reserve0.0025dB; actual quality gates unchanged.
172 quantized protection constraints pass; predictedfar mean0.707361156/min
-0.097495948dB. ModelSHA f46f7640added7a77b310e8b6f5538f25d4bd8fdf031bcd36a853f311937ee7e.
All9 Newton stages converge by decrement; numerical gap estimate9.63e-8,
stationarity max0.000231925. Not a global optimum proof.

All seven136 development cohorts pass actual C original-metric and new precise
integer-PCM checks. Far means0.750639/1.121110/0.805857/0.569185/0.734192/
0.623423/0.640900dB; overallworstfar-0.097560086dB and DT-0.079866991dB.
Near-only original metrics remain exactly equal; all AGC internal/IFFT/OLA/
output-gain/finalclip counters do not increase. Precision observers preserve all
original native/candidate metrics and native features/IFFT/AGC trajectories.
First precision audit stopped on historic module-relative versus absolute track
path representation; corrected explicit module-root resolution and tested from
nonrepository cwd. Failed directory retained, not counted as evidence.

Then frozen new24 split2b9d5eb0c37a1db55e95f37c5c766cc4194d55c3a1ecf911f33fd1dba3ef8da4
was scored once for this candidate. Far precisionmean0.609947463/min0.083643034,
DTmean0.121547813/min-0.129465111 (file907), targetmin+0.005231557dB.
All near/clip gates pass but DT fails original-0.1 gate, so reject adoption.
Observed907 rawtrace hashes native2a06440473753944c091d1fc42c6d527b7dd5f8d1b2b82b94edf445192131bb0,
candidate50a5ac92987febe0190290a40cb5a4f57f400d6aab4298f6ad0c129e8a9f3827.
No native-reference, input or score window drift. No tolerance added.

Correction surface has neighbor jump maxima1.114286/1/1 and edge MSE
0.196703/0.163794/0.271609 across gain/ratio/phase axes. This is a stability
design clue, not proof that a particular grid jump caused907's loss.
New plan: retain136 fit data and all numeric protection reserves, add one frozen
normalized neighbor-correction Laplacian prior of strength0.01. Original far
curvature normalized to maxeigen1; regularizer maxcurvature0.01. No scan.
Previously independent24 becomes regression-only, not fit; all160 actual cases
must qualify before another fresh balanced24 excluding all160 is opened.

89 Python tests pass5.900s/no skips; actual model ASan/UBSan contracts pass.
Vendor library not entirely sanitizer-instrumented. Production defaults/upper
readers/subscriptions/leases/proto/VOICE unchanged; no commit/push/deployment/
new device capture/ARMresource or subjective cure proof.
Candidatebinary5f5eb97b4579aebae8473838bc361858db04308625f3f61b24b84df4dd1edb56,
sanitizercontractcf1c7ea785910ed47acf061679e8bb4ee7909e3e9a5e6510fa844439aa6b0cb4;
precisiontool95aabc9601db0c1c38aca1645e7b5bfc893703a67268533de1c4d1034146d7d4.
Fresh default-v20-bound static/shared and164 production source identities stay
unchanged. Host qualification is separate from actual device call evidence.

## 中文导读与资格边界

历史 v23 记录：七组 136 例开发门禁通过后，首次冻结独立 24 例仍因双讲最差项低于原门槛而拒绝采用。此前路径审计失败保留，精确重算未加入容差；网格跳变只是后续设计线索，不证明该样本损失的因果或产品资格。
