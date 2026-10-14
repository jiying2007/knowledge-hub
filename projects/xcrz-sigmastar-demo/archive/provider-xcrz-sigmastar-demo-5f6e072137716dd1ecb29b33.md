---
id: provider-xcrz-sigmastar-demo-5f6e072137716dd1ecb29b33
title: 'Fixed smooth prior v24: reject residual907 DT failure'
kind: debug-record
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/archive/provider-xcrz-sigmastar-demo-5f6e072137716dd1ecb29b33.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: provider-candidate-archive
  from: provider-policy-sha256:a295759999c3c3c2594752350565bbde6af74808af32b9272604f53a36f82736;operation:5f6e072137716dd1ecb29b335ee7bf43fd8cea9b3048d6e186c1972708a83de3
  source_sha256: 280dacabc774fb5823ff09c388bb9260f7c8a7afbcd081fd048c7acf02758bb9
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
- projects/xcrz-sigmastar-demo/archive/provider-xcrz-sigmastar-demo-5f6e072137716dd1ecb29b33.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/archive/provider-xcrz-sigmastar-demo-5f6e072137716dd1ecb29b33.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-10-10'
updated_at: '2026-10-10'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-10-10'
manual_validation_pending: true
summary_zh: logical_task_open:true; completion_claim:false; shipping_approved:false. One frozen correction-Laplacian strength0.01
  on unchanged136 fit data/native features/AGC/box, protectedreserve0.08dB/farreserve0.0025dB. All172 quantized protection
  constraints pass, predictedfar mean0.690826461/min-0.09749438
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
subject_ref: &id001
  id: xcrz-sigmastar-demo
  type: project
created_subject_ref: *id001
principal_id: null
provider_operation_id: 5f6e072137716dd1ecb29b335ee7bf43fd8cea9b3048d6e186c1972708a83de3
---

# Fixed smooth prior v24: reject residual907 DT failure

logical_task_open:true; completion_claim:false; shipping_approved:false.
One frozen correction-Laplacian strength0.01 on unchanged136 fit data/native
features/AGC/box, protectedreserve0.08dB/farreserve0.0025dB. All172 quantized
protection constraints pass, predictedfar mean0.690826461/min-0.097494387dB.
All9 Newton stages converge by decrement; stationaritymax0.000751287,
numericalgap9.63e-8. ModelSHA
55e72ae3f884340be5bd165dc985481fc45efd95f49d9b12079a51890a74a935.

Actual C seven136 fitted cohorts pass original gates: farmeans
0.731708/1.108125/0.788917/0.549792/0.724375/0.608542/0.625083dB;
DTminima-0.080/-0.017/-0.062/-0.015/-0.042/-0.021/-0.064dB.
Exposed2b9 regression24(notfit) fails907 DT. Actual integer-PCM precision
farmean0.589351464/min0.083657058; DTmean0.126183656/min-0.104568481;
targetmin+0.009995032dB. All near-only original metrics exactly equal, all
internal AGC/IFFT/OLA/outputgain/finalclip gates pass. No adoption or fresh score.

Correction edge MSE falls from0.196703/0.163794/0.271609(v23) to
0.071830/0.064004/0.138230(v24), reducing roughness approximately63.5/60.9/49.1%.
Worstneighbor jumps remain1.114279/1/1. This demonstrates prior effect and
paired-regression907 improvement but does not establish a causal/general bound.
Candidate C ASan/UBSan lifecycle contracts pass; vendorstaticlibrary not wholly
instrumented.90Python tests pass5.571s/no skips; module diff --check passes.
No production/default/business/deployment/newcapture/ARMresource changes.

New independent balanced24 has already been frozen beforev24fit,96validated
tracks, c8f943851d6d05a6067a0396bc465bce7956564dacba7ae9926f4b7a57c996d8.
Excluded all160 cross-role speakers/source clips; it stays unscored/prohibited
in fit.2b9 remains regression-only, also prohibited from current136 fit.

Training-cohort arithmetic residual ratios at frozenv24 imply sufficient far
means0.683381/0.986574/0.670683/0.530623/0.670656/0.569072/0.611920dB.
All exceed0.5025dB, establishing room for an explicit cohortgain-constrained
minimum-complexity design. Quantizedv24 is not strictly feasible for the barrier
target constraint (minnormalizedtargetdelta-3.819449e-7), so a bounded reexecution
of identicalv24 solver must recover its unquantized feasible point; no model or
existing evidence overwrite. Numerical feasibility does not certify an optimum.

Candidatebinary3972c6a6e6d7a25a20dd760bad7d5f05f26b061a27b403783883816653c0721a;
barriersource0c6d814842e260eb4bb5c0372d634eba8fa69177a088a74f5ac7615646886998.
Defaultv20-bound A/SO/164production identities remain exact. Mainacousticgoal
needs-fix; no exact global optimum, call listening or product qualification.

## 中文导读与资格边界

历史 v24 记录：固定平滑先验改善了表面粗糙度及已暴露样本，但该回归的双讲最差项仍失败，没有采用或新的独立资格。新独立集合保持未评分；量化候选的严格可行性限制、供应商库未完整插桩和无设备/部署变更仍保留。
