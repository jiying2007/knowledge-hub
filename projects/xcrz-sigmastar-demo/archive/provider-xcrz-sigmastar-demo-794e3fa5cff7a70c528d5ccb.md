---
id: provider-xcrz-sigmastar-demo-794e3fa5cff7a70c528d5ccb
title: v25：160 例回归通过，新的 24 例否决采用
kind: debug-record
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/archive/provider-xcrz-sigmastar-demo-794e3fa5cff7a70c528d5ccb.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: provider-candidate-archive
  from: provider-policy-sha256:a295759999c3c3c2594752350565bbde6af74808af32b9272604f53a36f82736;operation:794e3fa5cff7a70c528d5ccbf0949d94f863493e4d1a7a0afb1937ae03ad9392
  source_sha256: afb1f6fe25ddca9825cfcc9aafbe550b39663b9be486efa4178551511ed12833
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
- projects/xcrz-sigmastar-demo/archive/provider-xcrz-sigmastar-demo-794e3fa5cff7a70c528d5ccb.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/archive/provider-xcrz-sigmastar-demo-794e3fa5cff7a70c528d5ccb.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-10-10'
updated_at: '2026-10-10'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-10-10'
manual_validation_pending: true
summary_zh: logical_task_open:true; completion_claim:false; shipping_approved:false. 同一136例拟合数据，172语音保护约束、七组平均远端残差约束、 原生NN特征/AGC轨迹及实际质量门槛保持原值。冻结v24
  warm量化系数完全重现。 模型SHA256 06f6cdc7e7c188fa2e23cec93d31f918e8d64888a1494f91370e231fca5949c5。 量化原始及新增七组约束通过，拟合预测far平均0.625453325/min
  -0.097494636 dB。 新求解九阶段均达到128步上限而未收敛
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
subject_ref: &id001
  id: xcrz-sigmastar-demo
  type: project
created_subject_ref: *id001
principal_id: null
provider_operation_id: 794e3fa5cff7a70c528d5ccbf0949d94f863493e4d1a7a0afb1937ae03ad9392
---

# v25：160 例回归通过，新的 24 例否决采用

logical_task_open:true; completion_claim:false; shipping_approved:false.
同一136例拟合数据，172语音保护约束、七组平均远端残差约束、
原生NN特征/AGC轨迹及实际质量门槛保持原值。冻结v24 warm量化系数完全重现。
模型SHA256 06f6cdc7e7c188fa2e23cec93d31f918e8d64888a1494f91370e231fca5949c5。
量化原始及新增七组约束通过，拟合预测far平均0.625453325/min -0.097494636 dB。
新求解九阶段均达到128步上限而未收敛；最终decrement约0.0055303，
stationarity约140873；部分未量化二次约束margin接近机器精度。
因此输出仅为可行候选，数值barrier gap估计不得作为最优证书。

实际C及最终整数PCM高精度检查全部160例通过，七开发组加2b9回归组
far平均分别0.651863881/0.974553906/0.710958607/0.520033104/
0.654161350/0.552587362/0.565986243/0.541207354 dB。
160例加权far平均0.612831246，最差DT -0.074110397 dB；
2b9回归组DT最差-0.068940212 dB，907已不再越界。
全部near-only原始指标完全相同，AGC内部饱和及IFFT/OLA/输出/最终clip无增加。

满足上述回归后，首次评分此前未评分的c8f独立24例。
splitSHA c8f943851d6d05a6067a0396bc465bce7956564dacba7ae9926f4b7a57c996d8。
实际整数PCM far平均0.492856281/min0.071831733 dB，
DT最差804为-0.604143322 dB，target最差+0.002767765 dB。
far均值未达到0.5，DT越过-0.1；此版明确拒绝采用。
804原生AES DTD双讲召回1.0，但尾部校正只检查refVad，并未使用双讲状态。
804的far原生DTD误激活率0.91049，shadow far激活0.31714/有效0.75448，
double shadow激活0.75758/有效0.90043。该观察支持做固定运行时双讲保护
归因实验，不能证明它能同时满足远端收益和语音质量。
c8f现已曝光，累计184例；2b9和c8f仍禁止进入当前136例拟合。

92 Python tests OK(5.958s，无跳过)；候选实际C ASan/UBSan整数basis、
echo FIFO、无ref、Reset及负控制PASS；vendor静态库未整体instrument。
源码及主仓diff --check通过。未改变生产默认/业务接口/ARM制品/设备部署。
default v20-bound库及164个生产源码身份仍使用冻结构建回执。
候选binary f2128af48d58c27aea76be308014459f5ff019260bba9507062eaf746f5e39ed；
control binary 932fc2223e5b4cf633ec61d6bd031698c38231368ce34c05284f94f2201a7f77；
contract binary 2f7d28ddf558f7218ffb61768d5d31fea6a107b87efa65c004ced2a8411aba5c。
barrier源码 a31fe104ee5b99ab9e943cef2fe64866224840751cbf6d17493fb123fec1438b；
precision源码 d857ccc02710904f2b3bc36dcbcb94f7d161fe7158df1f672ec3825d6d54bc5e。
全部评分及trace身份见tail-pcm-*-v25.json、pcm-precision-*-v25/precision.json。
主回声目标尚未完成，无设备听感、安全推广或全局最优结论。
