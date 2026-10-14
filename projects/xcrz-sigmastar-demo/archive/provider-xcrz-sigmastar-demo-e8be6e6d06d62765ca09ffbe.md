---
id: provider-xcrz-sigmastar-demo-e8be6e6d06d62765ca09ffbe
title: CALL 残余回声 v57—v59 实际优化结论
kind: debug-record
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/archive/provider-xcrz-sigmastar-demo-e8be6e6d06d62765ca09ffbe.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: provider-candidate-archive
  from: provider-policy-sha256:a295759999c3c3c2594752350565bbde6af74808af32b9272604f53a36f82736;operation:e8be6e6d06d62765ca09ffbe40d1dd77563af1795182f036237a79d73fb74719
  source_sha256: 00906a61c131f9514b4c216fe5a4eab6473752dc8ea901725204127c9e6a3b64
  temporary_source_retained: false
review_after: '2027-01-09'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- provider-archive
- debug-record
validation_refs:
- projects/xcrz-sigmastar-demo/archive/provider-xcrz-sigmastar-demo-e8be6e6d06d62765ca09ffbe.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/archive/provider-xcrz-sigmastar-demo-e8be6e6d06d62765ca09ffbe.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-10-11'
updated_at: '2026-10-11'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-10-11'
manual_validation_pending: true
summary_zh: 持续严重的远端自回声仍未解决，completion_claim=false、logical_task_open=true。v57、v58因逐例双讲退化拒绝；v59在304个已暴露例通过原保护，可列优化候选，但相同304例输出能量收益仅比v52多0.077365个百分点，暂不能证明值得替换已有原生v52方案或称最优。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
subject_ref: &id001
  id: xcrz-sigmastar-demo
  type: project
created_subject_ref: *id001
principal_id: null
provider_operation_id: e8be6e6d06d62765ca09ffbe40d1dd77563af1795182f036237a79d73fb74719
---

# CALL 残余回声 v57—v59 实际优化结论
持续严重的远端自回声仍未解决，completion_claim=false、logical_task_open=true。v57、v58因逐例双讲退化拒绝；v59在304个已暴露例通过原保护，可列优化候选，但相同304例输出能量收益仅比v52多0.077365个百分点，暂不能证明值得替换已有原生v52方案或称最优。

## 实际实现与决策
只新增三组共12个Host测试/审计源码。v57以因果原始播放参考/mic相关confidence限制v56；AEC回调完成前只读取reference_previous，结束后提交，与echo/mic_previous一致。v58进一步在previousDTD veto时清空额外H/raw历史，8次有效学习后才能额外投影。v59再乘1-sqrt(clamp(nn->fVad/Q24_ONE,0,1))；fVad源码上是NN增益平方均值，不是校准的语音概率。固定半强度、v52增益表、AGC原driver、quiet bypass、整数功率floor/ceiling均保持。新H/raw历史仍更新在应用后，无clean truth推理、未来输入或强度扫描。
v57在80例/4组里fileid508双讲-0.10520643275659225dB失败；v58在256例/12组里731双讲-0.1561620694543464dB失败，已启动同批完成，未启动48例停止。不能用它们的局部平均和v59全量排名。
v59实际304例/14组全部保护PASS：far最差-0.06874429775104678dB；double最差-0.07744094363365761dB；target最差-0.16215409801538447dB；near-only原全部指标不变、clips不增、native AGC轨迹相同。每组energy收益5.7878871117273585%—8.331273035121157%，高于原候选1%门槛。全量far均值0.3334583002722195dB，各组仍未达到完整目标>=0.5dB，所有complete_solution/shipping_approved均false。

## 同样本配对比较
重新核验v52两份280+24 registry、各precision/evaluation/source输入及608份原trace绑定；v59与v52完全相同304个fileid和四轨输入。v52 7.003224865004005%，v59 7.080590344073672%，差+0.07736547906966695个百分点；相对v52额外far改善平均+0.0039882346004854454dB、最大+0.1414473401784888dB。相对v52双讲平均-0.000054983560102146885dB、最差-0.02718230250510878dB；target平均-0.0003479098269689596dB、最差-0.006321672675997175dB。不是大幅AEC改善，也未证明统计/听感上的优越性。v59暂保留弱优化候选；v52原生默认关闭的受控接入仍是更完整验证的实现，未替换它。

## 验证与证据边界
3组严格-Werror编译、ASan/UBSan合同exit0（只新wrapper/测试插桩，旧native静态库未整体插桩）；每组20000数值边界、因果warmup、reference对齐负控制、AGC状态、CALL参考消失、VOICE/Reset/owner释放通过。v58/59还核验实际DTD veto清空；v59核验NN幅度约束边界。每组32 identity evaluation原全部指标和旧metadata完全一致，would_apply分别364161/260902/257293，证明实验路径实际工作；逐点PCM identity由实际合成生命周期合同证明，不能把32评价指标一致称所有录音逐点一致。
新增9项负测试，最终178项Python回归/7.629s/exit0无skip，含既有阶段和重放桥。新工具全部从/tmp help/dry-run通过且writes=false。评分使用实际C/整数PCM每帧能量及target dot，原rounded指标仅校验，不以.001舍入决定保护。不是逐点PCM归档或设备ERLE。确认640份evaluation case的1280份trace及2560四轨输入绑定，以及旧v52 608份trace；父仓与AISpeech diff --check exit0。
v55/v56共26处冻结依赖身份不变；v54 Host开启/关闭和ARM三组各185源码头文件及库身份复核不变。无v59设备录音重放、额外CPU/arena实测、ARM接入、安装或持续电话听感。上层reader/订阅/lease/proto和原生默认配置保持。

## 接续与资格
下一阶段v60只验证v59：先冻结排除既有304 fileid/speaker/source-clip的新24例，不把先前数据称blind；NN模型预训练独立性未知，train partition新集只证明相对本项目调参独立。随后新集actualC/精度和与v52配对，再原始16录音两profile重放和资源比较。仅有收益值得保留时才讨论native接入；若保护失败回退v52并基于新反例replan，不弱化门槛。runtime要求compact，checkpoint后接续；累计250M/48h不重置。
制品/方法在本地BUILD-v57-v59.json、candidate-registry-304-v59.json、PAIRED-v59-v52-304.json，raw WAV/trace/bin保留本地不入知识正文。本记录仅Provider reviewing候选，不是owner决定、产品采纳或生产放行。

