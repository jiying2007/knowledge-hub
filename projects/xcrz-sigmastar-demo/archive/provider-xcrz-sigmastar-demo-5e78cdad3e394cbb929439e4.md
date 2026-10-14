---
id: provider-xcrz-sigmastar-demo-5e78cdad3e394cbb929439e4
title: v26 固定双讲保护：证明需要重建拟合几何
kind: debug-record
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/archive/provider-xcrz-sigmastar-demo-5e78cdad3e394cbb929439e4.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: provider-candidate-archive
  from: provider-policy-sha256:a295759999c3c3c2594752350565bbde6af74808af32b9272604f53a36f82736;operation:5e78cdad3e394cbb929439e49eb09aa2d194c495d359ab068370d9700b63dbee
  source_sha256: d509ba17f38ecfe5c74a370d5d888ad5d1f67dde3d54dda1f85ecb94af804c63
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
- projects/xcrz-sigmastar-demo/archive/provider-xcrz-sigmastar-demo-5e78cdad3e394cbb929439e4.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/archive/provider-xcrz-sigmastar-demo-5e78cdad3e394cbb929439e4.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-10-10'
updated_at: '2026-10-10'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-10-10'
manual_validation_pending: true
summary_zh: logical_task_open:true; completion_claim:false; shipping_approved:false. 仅Host实验增加 previous-shadow-valid-far-no-candidate-no-active-v26
  保护。 NN callback时shadow属于上一AES帧，与NN一帧FIFO对齐；相位历史继续更新。 保护不改变原生AEC/AES/NN/AGC状态，不改已有shadow阈值，不用clean truth。 冻结v25校正表不重训，对全部已曝光184例做固定配对实验。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
subject_ref: &id001
  id: xcrz-sigmastar-demo
  type: project
created_subject_ref: *id001
principal_id: null
provider_operation_id: 5e78cdad3e394cbb929439e49eb09aa2d194c495d359ab068370d9700b63dbee
---

# v26 固定双讲保护：证明需要重建拟合几何

logical_task_open:true; completion_claim:false; shipping_approved:false.
仅Host实验增加 previous-shadow-valid-far-no-candidate-no-active-v26 保护。
NN callback时shadow属于上一AES帧，与NN一帧FIFO对齐；相位历史继续更新。
保护不改变原生AEC/AES/NN/AGC状态，不改已有shadow阈值，不用clean truth。
冻结v25校正表不重训，对全部已曝光184例做固定配对实验。

184例far平均改善0.323793478 dB，最差DT开发18为-0.144 dB；
新曝光c8f组far平均0.331625/最差DT -0.052 dB。
804原-0.604143 dB退化在旧精度评分中收窄到+0.001 dB，target -0.002 dB。
这是保护归因结果，仍不满足far平均0.5与DT最差-0.1门槛，拒绝采用。
直接给旧表加时域保护会改变整段PCM约束，单个反例恢复不能代替全回归。
下一轮必须按同136开发例重新采集保护后的映射，并绑定新guard身份。
2b9/c8f共48例保留回归，不加到当前136拟合清单；共184例已曝光。

第一次v26和补充完整skip-bin计数的v26-observed之间全部原始评分完全相同。
补充计数未改变算法、保护、模型或音频；记录两版binary身份，旧证据不覆盖。
旧模型与新guard资格器明确拒绝(model or inference contract mismatch)，无资格文件生成。
94 Python tests OK(5.738 s，无跳过)；实际C ASan/UBSan所有DTD flag组合、
真实允许/跳过帧、phase/echo FIFO、无ref、CALL/VOICE/Reset、原生AGC轨迹及负控制PASS。
vendor静态库未整体instrument。九组CLI dry-run从/tmp验证184例，writes=false。
未修改生产默认/业务契约/库/部署。归因评分是旧精度，没有冒称184例高精度通过。

observed candidate binary 40dbecbd3090f6422144133d4bfda8b3a5518314699b01050b0862696e0cbaeb；
native binary 3032e8199d6ea1ddd3a93a81f0b2d4c3ee0a351856160e480045d49587140174；
control binary 58526cf3d18dd96f05f37a07140c2651c11711aeb43065853b9fdcd2a6118db5。
predictor header c051fdd61cd782cb6cbd90784f056edaa3754a0caa21c8e6e335efbffee86418；
adapter header 62ef872e7b360c5164f6c18f3d649c4d847a0c149c75aeba343f33c8415d3cf0；
contract C a2ece25da8374166ecb476c1e73e79de357291730d258ce4686d0c6abe63b231；
boundary Python f262be40e5b33c949de0764d95503cc0bed5f9bd9ac44ae8df015cdbefbb09bb；
qualifier Python 180d8bb12bd5ec0722cfed985619b16884400d34a426590bf09366a80a01f7fb。
实际评分见tail-pcm-*-v26-observed.json；无主回声目标完成或生产最优结论。
